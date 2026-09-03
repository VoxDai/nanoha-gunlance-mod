"""Lossless NBNK parsing, media operations, and guarded Bank-level editing.

Notes:
    Public names are re-exported by tools.soundbank_editor. ALIGNMENT is the
    16-byte DATA alignment used when rebuilding media. EditSummary is a
    compatibility alias for SoundBankEditSummary. README.md contains usage;
    format structure and external verification belong to soundbank-workflow.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct

from ._binary import Payload, check_unsigned, coerce_payload, write_atomic as _write_atomic
from .errors import SoundBankError
from .hirc import (
    ACTION_PLAY,
    ACTION_PLAY_EVENT,
    ACTION_STOP,
    HIRC_ACTION,
    HIRC_EVENT,
    HIRC_RANDOM_SEQUENCE_CONTAINER,
    HIRC_SOUND,
    HIRC_SWITCH_CONTAINER,
    SUPPORTED_EDIT_VERSION,
    HircEditor,
    _parse_random_sequence_container_tail,
    _parse_switch_container_tail,
)


ALIGNMENT = 16


@dataclass(frozen=True)
class Chunk:
    """Immutable parsed chunk, retaining its original serialization.

    Attributes:
        tag: Four-byte chunk tag.
        offset: Absolute byte offset of the chunk header in the input Bank.
        payload: Chunk bytes after its eight-byte header.
        raw: Complete original header and payload, used for lossless output.
    """

    tag: bytes
    offset: int
    payload: bytes
    raw: bytes


@dataclass(frozen=True)
class MediaEntry:
    """Immutable DIDX media record with its extracted DATA payload.

    Attributes:
        media_id: Unsigned 32-bit Wwise media identity, independent of index.
        offset: Byte offset relative to DATA. Pending editor replacements and
            additions use zero until the Bank is rebuilt and reparsed.
        size: Payload length in bytes.
        payload: Embedded WEM bytes.
    """

    media_id: int
    offset: int
    size: int
    payload: bytes


@dataclass(frozen=True)
class SoundBankEditSummary:
    """Immutable report of edits declared through a SoundBankEditor.

    Attributes:
        replaced_media: Sorted (1-based DIDX index, Media ID) replacement pairs.
        added_media: Appended (1-based DIDX index, Media ID) pairs in edit order.
        hirc_changed_bytes: Cumulative changed-byte count reported by HircEditor;
            excludes inserted objects and size-only differences.
        added_hirc_objects: Added (object type, object ID) pairs in edit order.
        resized_hirc_objects: Original (type, ID, old body size, new body size)
            records whose current size differs; sizes include object ID bytes.
        hirc_size_delta: Current minus original serialized HIRC payload length.

    Notes:
        This is bookkeeping, not proof of validation or net semantic equality.
        EditSummary is an alias of this type.
    """

    replaced_media: tuple[tuple[int, int], ...]
    added_media: tuple[tuple[int, int], ...]
    hirc_changed_bytes: int
    added_hirc_objects: tuple[tuple[int, int], ...]
    resized_hirc_objects: tuple[tuple[int, int, int, int], ...]
    hirc_size_delta: int


# Backward-compatible public name used by existing builders.
EditSummary = SoundBankEditSummary


@dataclass(frozen=True)
class SoundBankDiff:
    """Immutable directional comparison from an original Bank to another Bank.

    Attributes:
        changed_chunks: Distinct changed tags in encounter order; chunk position,
            tag, and payload participate in comparison.
        replaced_media: (1-based index, new Media ID) pairs where corresponding
            DIDX positions differ in media identity or payload.
        added_media: (1-based index, Media ID) pairs beyond the original length.
        removed_media: Original (1-based index, Media ID) trailing pairs beyond
            the new length. This report does not provide a deletion operation.
        changed_hirc_objects: Sorted (type, ID) pairs present in both Banks with
            different body bytes.
        added_hirc_objects: Sorted (type, ID) pairs only in the new Bank.
        removed_hirc_objects: Sorted (type, ID) pairs only in the original Bank.

    Notes:
        Media comparison is positional, not an ID-based sequence alignment.
        Object order changes are visible at chunk level, not as body changes.
    """

    changed_chunks: tuple[bytes, ...]
    replaced_media: tuple[tuple[int, int], ...]
    added_media: tuple[tuple[int, int], ...]
    removed_media: tuple[tuple[int, int], ...]
    changed_hirc_objects: tuple[tuple[int, int], ...]
    added_hirc_objects: tuple[tuple[int, int], ...]
    removed_hirc_objects: tuple[tuple[int, int], ...]


def _check_u32(value: int, label: str) -> int:
    return check_unsigned(value, 32, label, SoundBankError)


def wwise_fnv1(name: str) -> int:
    """Compute the lowercase UTF-8, unsigned 32-bit Wwise FNV-1 name hash.

    Args:
        name: Nonempty name; lowercased with Python's Unicode lower operation.

    Returns:
        Deterministic unsigned object-name hash.

    Raises:
        SoundBankError: The name is not a nonempty string.

    Notes:
        This neither reserves the result nor checks collisions in any Bank.
    """

    if not isinstance(name, str) or not name:
        raise SoundBankError("Wwise hash name must be a non-empty string")
    value = 2166136261
    for byte in name.lower().encode("utf-8"):
        value = ((value * 16777619) ^ byte) & 0xFFFFFFFF
    return value


def validate_wem(value: Payload) -> bytes:
    """Read a payload and perform the Library's limited RIFF/WAVE format check.

    Args:
        value: Bytes, bytearray, memoryview, or a Path/string naming a WEM file.

    Returns:
        Immutable input bytes after finding a non-ordinary-PCM fmt chunk.

    Raises:
        SoundBankError: The payload/path is invalid, the RIFF/WAVE header is
            missing, an inspected chunk exceeds bounds, fmt is missing/short,
            or the fmt tag is ordinary PCM WAV (0x0001).
        OSError: Reading the file fails.

    Notes:
        Checking stops at the first accepted fmt chunk. This does not decode
        audio, validate the RIFF declared total length or remaining chunks, or
        certify sample rate, channel count, codec support, or the project's
        exact PCM WEM layout. Use external inspection/decoding for those checks.
    """

    payload = coerce_payload(value, "WEM", SoundBankError)
    if len(payload) < 12 or payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
        raise SoundBankError("WEM is not a RIFF/WAVE file")
    position = 12
    while position + 8 <= len(payload):
        tag = payload[position : position + 4]
        size = struct.unpack_from("<I", payload, position + 4)[0]
        start = position + 8
        end = start + size
        if end > len(payload):
            raise SoundBankError("WEM contains an out-of-bounds RIFF chunk")
        if tag == b"fmt ":
            if size < 2:
                raise SoundBankError("WEM fmt chunk is too short")
            format_tag = struct.unpack_from("<H", payload, start)[0]
            if format_tag == 0x0001:
                raise SoundBankError(
                    "ordinary PCM WAV files are not accepted; convert with wav_to_wem.py"
                )
            return payload
        position = end + (size & 1)
    raise SoundBankError("WEM is missing a fmt chunk")


@dataclass(frozen=True)
class SoundBank:
    """Immutable parsed NBNK; construct with from_file() or from_bytes().

    Attributes:
        chunks: Chunks in input serialization order, including unknown tags.
        entries: Embedded media in DIDX order; public selectors use 1-based indices.
        version: Wwise version from BKHD; parsing is not restricted to v120.
        bank_id: Unsigned Bank identity from BKHD.
        source_path: Resolved input path for from_file(), otherwise None.

    Notes:
        Factories validate chunk boundaries, required chunks, DIDX ranges, and
        HIRC framing/identities, not every HIRC body's semantics. Direct dataclass
        construction bypasses these checks. to_bytes() retains original bytes.
    """

    chunks: tuple[Chunk, ...]
    entries: tuple[MediaEntry, ...]
    version: int
    bank_id: int
    source_path: Path | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> SoundBank:
        """Read and parse a file, retaining its resolved path for output protection.

        Args:
            path: Path or string filename of the input artifact.

        Returns:
            Parsed SoundBank.

        Raises:
            SoundBankError: The path is not a file or format parsing fails.
            OSError: Reading the file or resolving its path fails.

        Notes:
            Does not modify the input. Editors reject writing to this resolved
            source_path even when output overwrite is enabled.
        """

        source = Path(path)
        if not source.is_file():
            raise SoundBankError(f"SoundBank does not exist: {source}")
        parsed = cls.from_bytes(source.read_bytes())
        return cls(parsed.chunks, parsed.entries, parsed.version, parsed.bank_id, source.resolve())

    @classmethod
    def from_bytes(cls, data: bytes) -> SoundBank:
        """Parse immutable input bytes without recording a source filename.

        Args:
            data: Complete file as bytes; bytearray/memoryview are not accepted
                by the underlying parsed-file factory.

        Returns:
            Parsed SoundBank; source_path is None.

        Raises:
            SoundBankError: The input is not bytes or parsing checks fail.

        Notes:
            Checks required BKHD/DIDX/DATA/HIRC chunks, chunk bounds, DIDX ranges, and HIRC framing/IDs.
            No file I/O occurs; source-path overwrite protection is unavailable.
        """

        if not isinstance(data, bytes):
            raise SoundBankError("SoundBank input must be bytes")
        chunks: list[Chunk] = []
        position = 0
        while position < len(data):
            if position + 8 > len(data):
                raise SoundBankError(f"SoundBank is missing a chunk header at 0x{position:X}")
            tag = data[position : position + 4]
            size = struct.unpack_from("<I", data, position + 4)[0]
            end = position + 8 + size
            if end > len(data):
                raise SoundBankError(f"chunk {tag!r} extends beyond the file boundary")
            chunks.append(Chunk(tag, position, data[position + 8 : end], data[position:end]))
            position = end
        required = {}
        for tag in (b"BKHD", b"DIDX", b"DATA", b"HIRC"):
            matches = [chunk for chunk in chunks if chunk.tag == tag]
            if len(matches) != 1:
                raise SoundBankError(f"expected exactly one {tag!r} chunk, found {len(matches)}")
            required[tag] = matches[0]
        bkhd = required[b"BKHD"].payload
        if len(bkhd) < 8:
            raise SoundBankError("BKHD is too short to contain version and Bank ID")
        version, bank_id = struct.unpack_from("<II", bkhd, 0)
        didx = required[b"DIDX"].payload
        media_data = required[b"DATA"].payload
        if len(didx) % 12:
            raise SoundBankError("DIDX size is not a whole number of 12-byte entries")
        entries: list[MediaEntry] = []
        for offset in range(0, len(didx), 12):
            media_id, data_offset, size = struct.unpack_from("<III", didx, offset)
            end = data_offset + size
            if end > len(media_data):
                raise SoundBankError(f"Media ID {media_id} range extends beyond DATA")
            entries.append(
                MediaEntry(media_id, data_offset, size, media_data[data_offset:end])
            )
        HircEditor(
            required[b"HIRC"].payload,
            version=version,
            reserved_ids=(entry.media_id for entry in entries),
        )
        return cls(tuple(chunks), tuple(entries), version, bank_id)

    def to_bytes(self) -> bytes:
        """Return the original chunk serializations byte-for-byte without validation.

        Returns:
            Complete NBNK bytes; no disk I/O or rebuilding of media offsets occurs.
        """

        return b"".join(chunk.raw for chunk in self.chunks)

    def chunk(self, tag: bytes) -> Chunk:
        """Select exactly one chunk by its byte tag.

        Args:
            tag: Chunk tag such as b"BKHD".

        Returns:
            The immutable parsed Chunk.

        Raises:
            SoundBankError: No chunk or more than one chunk has that tag.
        """

        matches = [chunk for chunk in self.chunks if chunk.tag == tag]
        if len(matches) != 1:
            raise SoundBankError(f"expected exactly one {tag!r} chunk, found {len(matches)}")
        return matches[0]

    @property
    def hirc_payload(self) -> bytes:
        """Return immutable HIRC payload bytes, excluding the chunk header.

        Raises:
            SoundBankError: There is not exactly one HIRC chunk.
        """

        return self.chunk(b"HIRC").payload

    def media_entry(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> MediaEntry:
        """Select one original parsed media entry without extracting to disk.

        Args:
            index: 1-based DIDX position; mutually exclusive with media_id.
            media_id: Media identity that must resolve to exactly one entry.

        Returns:
            Immutable MediaEntry. Specify exactly one selector.

        Raises:
            SoundBankError: Both/neither selectors are supplied, the index is
                out of range, or the Media ID does not resolve uniquely.
        """

        selected = _resolve_media_index(self.entries, index=index, media_id=media_id)
        return self.entries[selected]

    def extract_media(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> bytes:
        """Return the original parsed WEM bytes selected by index or Media ID.

        Args:
            index: 1-based DIDX position; mutually exclusive with media_id.
            media_id: Unique media identity, as for media_entry().

        Returns:
            Immutable embedded payload; no decoding or disk write occurs.

        Raises:
            SoundBankError: The selector is missing, conflicting, or not unique/in range.
        """

        return self.media_entry(index=index, media_id=media_id).payload

    def extract_all_media(self) -> dict[int, bytes]:
        """Return a new mapping of 1-based DIDX indices to original parsed WEM bytes.

        Returns:
            dict keyed by entry position, not Media ID. No files are written.
        """

        return {index: entry.payload for index, entry in enumerate(self.entries, 1)}

    def diff(self, other: SoundBank) -> SoundBankDiff:
        """Compare this Bank to another without mutating either input.

        Args:
            other: The new Bank to compare against this original Bank.

        Returns:
            SoundBankDiff with positional media differences and HIRC identity/body
            differences. Offset-only media movement is not a media replacement.

        Raises:
            SoundBankError: Either HIRC payload cannot be parsed.

        Notes:
            This does not enforce an edit declaration or validate the resulting
            graph. HIRC order changes affect changed_chunks, not object body lists.
        """

        changed_chunk_tags: list[bytes] = []
        for before, after in zip(self.chunks, other.chunks):
            if before.tag != after.tag or before.payload != after.payload:
                changed_chunk_tags.extend((before.tag, after.tag))
        for chunk in self.chunks[len(other.chunks) :]:
            changed_chunk_tags.append(chunk.tag)
        for chunk in other.chunks[len(self.chunks) :]:
            changed_chunk_tags.append(chunk.tag)
        changed_chunks = tuple(dict.fromkeys(changed_chunk_tags))
        replaced_media: list[tuple[int, int]] = []
        for index, (before, after) in enumerate(zip(self.entries, other.entries), 1):
            if before.media_id != after.media_id or before.payload != after.payload:
                replaced_media.append((index, after.media_id))
        added_media = tuple(
            (index, entry.media_id)
            for index, entry in enumerate(other.entries[len(self.entries) :], len(self.entries) + 1)
        )
        removed_media = tuple(
            (index, entry.media_id)
            for index, entry in enumerate(self.entries[len(other.entries) :], len(other.entries) + 1)
        )
        before_hirc = HircEditor(self.hirc_payload, version=self.version)
        after_hirc = HircEditor(other.hirc_payload, version=other.version)
        before_objects = {
            (item.object_type, item.object_id): bytes(item.body) for item in before_hirc.objects()
        }
        after_objects = {
            (item.object_type, item.object_id): bytes(item.body) for item in after_hirc.objects()
        }
        common = before_objects.keys() & after_objects.keys()
        changed_hirc = tuple(sorted(key for key in common if before_objects[key] != after_objects[key]))
        return SoundBankDiff(
            changed_chunks=changed_chunks,
            replaced_media=tuple(replaced_media),
            added_media=added_media,
            removed_media=removed_media,
            changed_hirc_objects=changed_hirc,
            added_hirc_objects=tuple(sorted(after_objects.keys() - before_objects.keys())),
            removed_hirc_objects=tuple(sorted(before_objects.keys() - after_objects.keys())),
        )


def _resolve_media_index(
    entries: Sequence[MediaEntry], *, index: int | None, media_id: int | None
) -> int:
    if (index is None) == (media_id is None):
        raise SoundBankError("select media with exactly one of index or media_id")
    if index is not None:
        if not isinstance(index, int) or isinstance(index, bool) or not 1 <= index <= len(entries):
            raise SoundBankError(f"DIDX index must be between 1 and {len(entries)}: {index}")
        return index - 1
    matches = [position for position, entry in enumerate(entries) if entry.media_id == media_id]
    if not matches:
        raise SoundBankError(f"Media ID not found: {media_id}")
    if len(matches) > 1:
        raise SoundBankError(f"Media ID {media_id} is not unique; use a DIDX index")
    return matches[0]


class SoundBankEditor:
    """In-memory editor for one parsed Bank, leaving its original unchanged.

    Attributes:
        original: Immutable Bank supplied at construction.
        hirc: HircEditor for the working HIRC payload, with media IDs reserved.

    Notes:
        build() serializes; validate() checks the rebuilt Bank; write_atomic()
        validates and writes one file. A sequence of editing calls is not a
        general rollback transaction. Individual methods document their checks.
    """

    def __init__(self, bank: SoundBank):
        """Create independent working media and HIRC state from a parsed Bank.

        Args:
            bank: Original SoundBank whose source_path is retained for write protection.

        Raises:
            SoundBankError: HIRC framing or reserved media identities are invalid.
        """

        self.original = bank
        self._media = list(bank.entries)
        self._original_media_count = len(bank.entries)
        self._replaced_media: dict[int, bytes] = {}
        self._added_media: list[tuple[int, int]] = []
        self.hirc = HircEditor(
            bank.hirc_payload,
            version=bank.version,
            reserved_ids=(entry.media_id for entry in bank.entries),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> SoundBankEditor:
        """Read and parse a file, retaining its resolved path for output protection.

        Args:
            path: Path or string filename of the input artifact.

        Returns:
            New SoundBankEditor containing a parsed original and independent working state.

        Raises:
            SoundBankError: The path is not a file or format parsing fails.
            OSError: Reading the file or resolving its path fails.

        Notes:
            Does not modify the input. Editors reject writing to this resolved
            source_path even when output overwrite is enabled.
        """

        return cls(SoundBank.from_file(path))

    @classmethod
    def from_bytes(cls, data: bytes) -> SoundBankEditor:
        """Parse immutable input bytes without recording a source filename.

        Args:
            data: Complete file as bytes; bytearray/memoryview are not accepted
                by the underlying parsed-file factory.

        Returns:
            New SoundBankEditor containing a parsed original and independent working state; source_path is None.

        Raises:
            SoundBankError: The input is not bytes or parsing checks fail.

        Notes:
            Checks required BKHD/DIDX/DATA/HIRC chunks, chunk bounds, DIDX ranges, and HIRC framing/IDs.
            No file I/O occurs; source-path overwrite protection is unavailable.
        """

        return cls(SoundBank.from_bytes(data))

    @property
    def version(self) -> int:
        """Return the original Bank's Wwise version, without modifying it."""

        return self.original.version

    @property
    def bank_id(self) -> int:
        """Return the original Bank's unsigned Bank ID."""

        return self.original.bank_id

    def _require_v120(self, operation: str) -> None:
        if self.version != SUPPORTED_EDIT_VERSION:
            raise SoundBankError(
                f"{operation} requires Wwise v{SUPPORTED_EDIT_VERSION}; "
                f"this Bank is v{self.version}"
            )

    def media_entry(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> MediaEntry:
        """Select one current working media entry without extracting to disk.

        Args:
            index: 1-based DIDX position; mutually exclusive with media_id.
            media_id: Media identity that must resolve to exactly one entry.

        Returns:
            Immutable MediaEntry. Specify exactly one selector.

        Raises:
            SoundBankError: Both/neither selectors are supplied, the index is
                out of range, or the Media ID does not resolve uniquely.
        """

        selected = _resolve_media_index(self._media, index=index, media_id=media_id)
        return self._media[selected]

    def extract_media(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> bytes:
        """Return the current working WEM bytes selected by index or Media ID.

        Args:
            index: 1-based DIDX position; mutually exclusive with media_id.
            media_id: Unique media identity, as for media_entry().

        Returns:
            Immutable embedded payload; no decoding or disk write occurs.

        Raises:
            SoundBankError: The selector is missing, conflicting, or not unique/in range.
        """

        return self.media_entry(index=index, media_id=media_id).payload

    def extract_all_media(self) -> dict[int, bytes]:
        """Return a new mapping of 1-based DIDX indices to current working WEM bytes.

        Returns:
            dict keyed by entry position, not Media ID. No files are written.
        """

        return {index: entry.payload for index, entry in enumerate(self._media, 1)}

    def replace_media(
        self,
        wem: bytes | bytearray | memoryview | Path | str,
        *,
        index: int | None = None,
        media_id: int | None = None,
        expected_media_id: int | None = None,
        expected_sha256: str | None = None,
    ) -> None:
        """Replace one working media payload while retaining its Media ID.

        Args:
            wem: WEM bytes, bytearray, memoryview, or Path/string filename; checked
                with validate_wem(), which does not decode audio.
            index: 1-based DIDX position; supply exactly one of index or media_id.
            media_id: Unique working Media ID selector.
            expected_media_id: Optional exact identity guard; None disables it.
            expected_sha256: Optional case-insensitive SHA-256 guard over the current
                WEM payload; None disables it.

        Raises:
            SoundBankError: Selection fails, this entry was already replaced, a
                supplied guard fails, or the WEM check fails.
            OSError: Reading the replacement file fails.

        Notes:
            Returns None. After checks, records the replacement in memory with
            offset zero; build() recalculates DIDX offsets and DATA alignment. May
            select an appended entry. This method has no v120 version restriction.
            Project workflow guards can be stricter than these optional parameters.
        """

        selected = _resolve_media_index(self._media, index=index, media_id=media_id)
        current = self._media[selected]
        if selected in self._replaced_media:
            raise SoundBankError(f"DIDX #{selected + 1} was already replaced")
        if expected_media_id is not None and current.media_id != expected_media_id:
            raise SoundBankError(
                f"DIDX #{selected + 1} expected Media ID {expected_media_id} "
                f"but found {current.media_id}"
            )
        if expected_sha256 is not None:
            actual_hash = hashlib.sha256(current.payload).hexdigest()
            if actual_hash.casefold() != expected_sha256.casefold():
                raise SoundBankError(
                    f"DIDX #{selected + 1} expected SHA-256 {expected_sha256} "
                    f"but found {actual_hash}"
                )
        payload = validate_wem(wem)
        self._media[selected] = MediaEntry(current.media_id, 0, len(payload), payload)
        self._replaced_media[selected] = payload

    def append_media(
        self, media_id: int, wem: bytes | bytearray | memoryview | Path | str
    ) -> MediaEntry:
        """Append a WEM with an explicit unused media identity in a v120 Bank.

        Args:
            media_id: Unsigned 32-bit ID unused by working media and HIRC objects.
            wem: WEM bytes, bytearray, memoryview, or Path/string filename.

        Returns:
            New immutable MediaEntry with provisional offset zero. Its DIDX index
            is the new working media count.

        Raises:
            SoundBankError: The Bank is not v120, the ID is invalid/colliding,
                or validate_wem() rejects the payload.
            OSError: Reading the WEM file fails.

        Notes:
            Reserves the ID in HIRC and appends bookkeeping; does not add a Sound
            or playback route. Original entries and payloads remain unchanged.
        """

        self._require_v120("append media")
        media_id = _check_u32(media_id, "Media ID")
        if any(entry.media_id == media_id for entry in self._media):
            raise SoundBankError(f"Media ID already exists: {media_id}")
        payload = validate_wem(wem)
        self.hirc.reserve_id(media_id)
        entry = MediaEntry(media_id, 0, len(payload), payload)
        self._media.append(entry)
        self._added_media.append((len(self._media), media_id))
        return entry

    def add_play_event_action(
        self,
        event_id: int,
        action_id: int,
        target_event_id: int,
        *,
        expected_actions: Sequence[int],
    ) -> None:
        """Add and attach a new PlayEvent Action to an existing v120 Event.

        Args:
            event_id: Existing Event to receive the new Action.
            action_id: New unsigned 32-bit Action ID, unused by HIRC/media.
            target_event_id: Existing Event the new Action will invoke.
            expected_actions: Exact current ordered Action IDs of event_id.

        Raises:
            SoundBankError: Version, target/owner lookup, ordered guard, ID,
                insertion, or Event body replacement checks fail.

        Notes:
            Returns None. Inserts the Action immediately before its owning Event,
            then appends its ID to that Event's list. Does not create either Event.
            This composition has no general rollback if a later operation fails.
        """

        self._require_v120("add PlayEvent Action")
        self.hirc._get_object(HIRC_EVENT, target_event_id)
        actual_actions = self.hirc.event_actions(event_id)
        if actual_actions != tuple(expected_actions):
            raise SoundBankError(
                f"Event {event_id} expected actions {tuple(expected_actions)} "
                f"but found {actual_actions}"
            )
        body = self.hirc.create_play_event_action(action_id, target_event_id)
        self.hirc.insert_object(
            HIRC_ACTION,
            action_id,
            body[4:],
            before=(HIRC_EVENT, event_id),
            label=f"add PlayEvent Action {action_id}",
        )
        self.hirc.append_event_action(
            event_id,
            action_id,
            expected_actions=expected_actions,
            label=f"append PlayEvent Action {action_id} to Event {event_id}",
        )

    def add_custom_sound_action(
        self,
        event_id: int,
        action_id: int,
        sound_id: int,
        media_id: int,
        donor_sound_id: int,
        wem: bytes | bytearray | memoryview | Path | str,
        *,
        expected_actions: Sequence[int],
        expected_donor_source_id: int,
        delay_ms: int = 0,
        transition_ms: int | None = None,
    ) -> None:
        """Append media, clone an embedded Sound, and attach a Play Action in v120.

        Args:
            event_id: Existing Event that will receive the Action.
            action_id: New Action ID.
            sound_id: New Sound ID.
            media_id: New Media ID; all three new IDs must be distinct unsigned-32
                identities unused by existing working HIRC objects and media.
            donor_sound_id: Existing embedded v120 Sound to clone.
            wem: WEM bytes, bytearray, memoryview, or Path/string filename.
            expected_actions: Exact current ordered Action list of event_id.
            expected_donor_source_id: Exact donor's embedded source Media ID.
            delay_ms: Delay property passed to create_play_action(); zero omits it.
            transition_ms: Optional transition property in milliseconds; None omits it.

        Raises:
            SoundBankError: Version, guards, media, identities, donor layout,
                Action construction, or constituent edit checks fail.
            OSError: Reading the WEM file fails.

        Notes:
            Returns None. Prechecks the listed IDs, Event guard, donor source, WEM,
            and Action encoding before composing edits. It is not a general rollback
            transaction for subsequent edit conflicts. Other donor Sound bytes,
            including parent and memory-size data, are retained. The Play Action is
            serialized immediately before its Event; validate() checks the result.
        """

        self._require_v120("add custom Sound Action")
        new_ids = tuple(
            _check_u32(value, label)
            for value, label in (
                (action_id, "Action ID"),
                (sound_id, "Sound ID"),
                (media_id, "Media ID"),
            )
        )
        if len(set(new_ids)) != len(new_ids):
            raise SoundBankError("Action, Sound, and Media IDs must be distinct")
        existing_ids = self.hirc.object_ids | frozenset(entry.media_id for entry in self._media)
        collision = next((value for value in new_ids if value in existing_ids), None)
        if collision is not None:
            raise SoundBankError(f"new custom Sound ID already exists: {collision}")
        if self.hirc.event_actions(event_id) != tuple(expected_actions):
            raise SoundBankError(
                f"Event {event_id} expected actions {tuple(expected_actions)} but found "
                f"{self.hirc.event_actions(event_id)}"
            )
        self.hirc._get_object(HIRC_EVENT, event_id)
        donor = self.hirc.object_body(HIRC_SOUND, donor_sound_id)
        if len(donor) < 18 or donor[8] != 0:
            raise SoundBankError(
                f"donor Sound {donor_sound_id} is not an embedded v120 DATA source"
            )
        if struct.unpack_from("<I", donor, 9)[0] != expected_donor_source_id:
            actual = struct.unpack_from("<I", donor, 9)[0] if len(donor) >= 13 else None
            raise SoundBankError(
                f"donor Sound {donor_sound_id} expected source ID "
                f"{expected_donor_source_id} but found {actual}"
            )
        payload = validate_wem(wem)
        action = self.hirc.create_play_action(
            action_id,
            sound_id,
            self.bank_id,
            delay_ms=delay_ms,
            transition_ms=transition_ms,
        )
        self.append_media(media_id, payload)
        self.hirc.clone_sound(
            donor_sound_id,
            sound_id,
            media_id,
            expected_source_id=expected_donor_source_id,
            label=f"clone donor Sound {donor_sound_id} as {sound_id}",
        )
        self.hirc.insert_object(
            HIRC_ACTION,
            action_id,
            action[4:],
            before=(HIRC_EVENT, event_id),
            label=f"add Play Action {action_id}",
        )
        self.hirc.append_event_action(
            event_id,
            action_id,
            expected_actions=expected_actions,
            label=f"append Play Action {action_id} to Event {event_id}",
        )

    @property
    def summary(self) -> SoundBankEditSummary:
        """Return immutable current edit bookkeeping without validation or disk I/O.

        Returns:
            SoundBankEditSummary; media pairs use 1-based indices, object pairs use
            (type, ID). Computing HIRC size delta serializes the working HIRC.
        """

        return SoundBankEditSummary(
            replaced_media=tuple(
                (index + 1, self._media[index].media_id)
                for index in sorted(self._replaced_media)
            ),
            added_media=tuple(self._added_media),
            hirc_changed_bytes=self.hirc.changed_byte_count,
            added_hirc_objects=self.hirc.added_objects,
            resized_hirc_objects=self.hirc.resized_objects,
            hirc_size_delta=len(self.hirc.build()) - len(self.original.hirc_payload),
        )

    def _build_media_chunks(self) -> tuple[bytes, bytes]:
        data = bytearray()
        records: list[tuple[int, int, int]] = []
        for entry in self._media:
            if data:
                data += b"\0" * ((-len(data)) % ALIGNMENT)
            records.append((entry.media_id, len(data), len(entry.payload)))
            data += entry.payload
        didx = b"".join(struct.pack("<III", *record) for record in records)
        return didx, bytes(data)

    def build(self) -> bytes:
        """Serialize the working Bank to bytes without a full validation pass.

        Returns:
            Complete NBNK bytes. Media edits rebuild DIDX/DATA with 16-byte starts;
            HIRC edits rebuild that chunk. Unchanged chunks retain their raw bytes.

        Notes:
            Does not write files, update the original Bank, or replace provisional
            MediaEntry offsets with rebuilt offsets. Use validate() to obtain the
            reparsed entries and verify the declared changes.
        """

        media_changed = bool(self._replaced_media or self._added_media)
        hirc_payload = self.hirc.build()
        hirc_changed = hirc_payload != self.original.hirc_payload
        didx_payload, data_payload = self._build_media_chunks() if media_changed else (b"", b"")
        output = bytearray()
        for chunk in self.original.chunks:
            if media_changed and chunk.tag == b"DIDX":
                payload = didx_payload
            elif media_changed and chunk.tag == b"DATA":
                payload = data_payload
            elif hirc_changed and chunk.tag == b"HIRC":
                payload = hirc_payload
            else:
                output += chunk.raw
                continue
            output += chunk.tag + struct.pack("<I", len(payload)) + payload
        return bytes(output)

    def validate(self) -> SoundBank:
        """Build, reparse, and verify the Bank against working state and declarations.

        Returns:
            New parsed SoundBank with resolved media offsets and no source_path.

        Raises:
            SoundBankError: Reparse, identity, media bytes/alignment, or declared
                HIRC change checks fail. For v120, also rejects missing Action/Event
                targets, Actions serialized after their Events, or missing/misordered
                children and media references of newly added Containers/Sounds.

        Notes:
            No disk writes or editor mutation. Unknown HIRC semantics and all
            existing Container internals are not comprehensively validated. External
            decoding and game acceptance remain separate checks.
        """

        rebuilt = SoundBank.from_bytes(self.build())
        if rebuilt.version != self.version or rebuilt.bank_id != self.bank_id:
            raise SoundBankError("read-back verification changed BKHD identity")
        if len(rebuilt.entries) != len(self._media):
            raise SoundBankError("read-back verification changed the expected media count")
        for index, (expected, actual) in enumerate(zip(self._media, rebuilt.entries), 1):
            if expected.media_id != actual.media_id or expected.payload != actual.payload:
                raise SoundBankError(f"read-back verification failed for DIDX #{index}")
            if (self._replaced_media or self._added_media) and actual.offset % ALIGNMENT:
                raise SoundBankError(f"read-back DIDX #{index} is not 16-byte aligned")
        rebuilt_hirc = HircEditor(rebuilt.hirc_payload, version=rebuilt.version)
        if rebuilt.version == SUPPORTED_EDIT_VERSION:
            hirc_objects = rebuilt_hirc.objects()
            object_positions = {
                (item.object_type, item.object_id): position
                for position, item in enumerate(hirc_objects)
            }
            object_positions_by_id = {
                item.object_id: position
                for position, item in enumerate(hirc_objects)
            }
            action_ids = {
                item.object_id
                for item in hirc_objects
                if item.object_type == HIRC_ACTION
            }
            event_ids = {
                item.object_id
                for item in hirc_objects
                if item.object_type == HIRC_EVENT
            }
            object_ids = rebuilt_hirc.object_ids
            for item in hirc_objects:
                if item.object_type == HIRC_EVENT:
                    for action_id in rebuilt_hirc.event_actions(item.object_id):
                        if action_id not in action_ids:
                            raise SoundBankError(
                                f"Event {item.object_id} references missing Action {action_id}"
                            )
                        if object_positions[(HIRC_ACTION, action_id)] >= object_positions[
                            (HIRC_EVENT, item.object_id)
                        ]:
                            raise SoundBankError(
                                f"Action {action_id} must be serialized before Event "
                                f"{item.object_id} for Wwise v120"
                            )
                elif item.object_type == HIRC_ACTION and len(item.body) >= 10:
                    action_type = struct.unpack_from("<H", item.body, 4)[0]
                    target_id = struct.unpack_from("<I", item.body, 6)[0]
                    if action_type == ACTION_PLAY_EVENT and target_id not in event_ids:
                        raise SoundBankError(
                            f"PlayEvent Action {item.object_id} references missing Event "
                            f"{target_id}"
                        )
                    if action_type == ACTION_PLAY and target_id not in object_ids:
                        raise SoundBankError(
                            f"Play Action {item.object_id} references missing object "
                            f"{target_id}"
                        )
                    if action_type == ACTION_STOP and target_id not in object_ids:
                        raise SoundBankError(
                            f"Stop Action {item.object_id} references missing object "
                            f"{target_id}"
                        )
            media_ids = {entry.media_id for entry in rebuilt.entries}
            for object_type, object_id in self.hirc.added_objects:
                body = rebuilt_hirc.object_body(object_type, object_id)
                if object_type == HIRC_SOUND:
                    source_id = struct.unpack_from("<I", body, 9)[0]
                    if source_id not in media_ids:
                        raise SoundBankError(
                            f"new Sound {object_id} references missing Media ID "
                            f"{source_id}"
                        )
                elif object_type in (
                    HIRC_RANDOM_SEQUENCE_CONTAINER,
                    HIRC_SWITCH_CONTAINER,
                ):
                    if object_type == HIRC_RANDOM_SEQUENCE_CONTAINER:
                        container_kind = "Container"
                        children = _parse_random_sequence_container_tail(
                            body, f"new Container {object_id}"
                        ).children
                    else:
                        container_kind = "Switch Container"
                        children = _parse_switch_container_tail(
                            body, f"new Switch Container {object_id}"
                        ).topology.children
                    missing_children = [
                        child_id
                        for child_id in children
                        if child_id not in object_ids
                    ]
                    if missing_children:
                        raise SoundBankError(
                            f"new {container_kind} {object_id} references missing child "
                            f"objects: {missing_children}"
                        )
                    late_children = [
                        child_id
                        for child_id in children
                        if object_positions_by_id[child_id]
                        >= object_positions[(object_type, object_id)]
                    ]
                    if late_children:
                        raise SoundBankError(
                            f"new {container_kind} {object_id} child objects must be "
                            "serialized before their parent for Wwise v120: "
                            f"{late_children}"
                        )
        diff = self.original.diff(rebuilt)
        declared_hirc = set(self.hirc.added_objects)
        declared_hirc.update((item[0], item[1]) for item in self.hirc.resized_objects)
        declared_hirc.update(self.hirc.patched_objects)
        declared_hirc.update(self.hirc.rebuilt_objects)
        unexpected_hirc = set(diff.changed_hirc_objects) - declared_hirc
        unexpected_added = set(diff.added_hirc_objects) - set(self.hirc.added_objects)
        if unexpected_hirc or unexpected_added or diff.removed_hirc_objects:
            raise SoundBankError(
                "read-back verification found undeclared HIRC object changes: "
                f"changed={sorted(unexpected_hirc)}, added={sorted(unexpected_added)}, "
                f"removed={list(diff.removed_hirc_objects)}"
            )
        return rebuilt

    def diff(self) -> SoundBankDiff:
        """Validate the working Bank and compare it to the original.

        Returns:
            Directional SoundBankDiff from original to validated working Bank.

        Raises:
            SoundBankError: validate() or the HIRC comparison fails.
        """

        return self.original.diff(self.validate())

    def write_atomic(self, output: Path | str, *, overwrite: bool = False) -> Path:
        """Validate and write one artifact using a temporary file beside the output.

        Args:
            output: Path or string filename; missing parent directories are created.
            overwrite: Permit replacing an existing output when True. Never permits
                replacing the original's recorded resolved source_path.

        Returns:
            Path of the written output, retaining the caller's relative/absolute form.

        Raises:
            SoundBankError: Validation fails, output resolves to the recorded input, or
                output already exists and overwrite is False.
            OSError: Directory creation, staging, fsync, or replacement fails.

        Notes:
            Calls build() and validate(), stages/fsyncs bytes, then uses os.replace().
            Cleans up the staged file and leaves editor state unchanged. from_bytes()
            has no source path to protect. The preflight existence check is not
            concurrency-safe exclusive creation; this is not a multi-file transaction
            or an on-disk read-back verification pass.
        """

        payload = self.build()
        self.validate()
        return _write_atomic(
            output,
            payload,
            source_path=self.original.source_path,
            overwrite=overwrite,
            kind="SoundBank",
            error_type=SoundBankError,
        )
