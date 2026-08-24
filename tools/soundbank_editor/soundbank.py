"""Lossless NBNK parsing and guarded Wwise v120 editing."""

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
    HIRC_ACTION,
    HIRC_EVENT,
    HIRC_RANDOM_SEQUENCE_CONTAINER,
    HIRC_SOUND,
    SUPPORTED_EDIT_VERSION,
    HircEditor,
    _parse_random_sequence_container_tail,
)


ALIGNMENT = 16


@dataclass(frozen=True)
class Chunk:
    """One SoundBank chunk, including its original serialized bytes."""

    tag: bytes
    offset: int
    payload: bytes
    raw: bytes


@dataclass(frozen=True)
class MediaEntry:
    """One embedded DIDX/DATA media record."""

    media_id: int
    offset: int
    size: int
    payload: bytes


@dataclass(frozen=True)
class SoundBankEditSummary:
    """Observable changes made by a SoundBankEditor."""

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
    """Object-level differences between two parsed SoundBanks."""

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
    """Return Wwise's lowercase 32-bit FNV-1 object-name hash."""

    if not isinstance(name, str) or not name:
        raise SoundBankError("Wwise hash name must be a non-empty string")
    value = 2166136261
    for byte in name.lower().encode("utf-8"):
        value = ((value * 16777619) ^ byte) & 0xFFFFFFFF
    return value


def validate_wem(value: Payload) -> bytes:
    """Read and validate a Wwise RIFF/WAVE media payload."""

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
    """An immutable, losslessly parsed SoundBank."""

    chunks: tuple[Chunk, ...]
    entries: tuple[MediaEntry, ...]
    version: int
    bank_id: int
    source_path: Path | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> SoundBank:
        source = Path(path)
        if not source.is_file():
            raise SoundBankError(f"SoundBank does not exist: {source}")
        parsed = cls.from_bytes(source.read_bytes())
        return cls(parsed.chunks, parsed.entries, parsed.version, parsed.bank_id, source.resolve())

    @classmethod
    def from_bytes(cls, data: bytes) -> SoundBank:
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
        return b"".join(chunk.raw for chunk in self.chunks)

    def chunk(self, tag: bytes) -> Chunk:
        matches = [chunk for chunk in self.chunks if chunk.tag == tag]
        if len(matches) != 1:
            raise SoundBankError(f"expected exactly one {tag!r} chunk, found {len(matches)}")
        return matches[0]

    @property
    def hirc_payload(self) -> bytes:
        return self.chunk(b"HIRC").payload

    def media_entry(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> MediaEntry:
        selected = _resolve_media_index(self.entries, index=index, media_id=media_id)
        return self.entries[selected]

    def extract_media(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> bytes:
        return self.media_entry(index=index, media_id=media_id).payload

    def extract_all_media(self) -> dict[int, bytes]:
        return {index: entry.payload for index, entry in enumerate(self.entries, 1)}

    def diff(self, other: SoundBank) -> SoundBankDiff:
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
    """A transactional editor for one parsed SoundBank."""

    def __init__(self, bank: SoundBank):
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
        return cls(SoundBank.from_file(path))

    @classmethod
    def from_bytes(cls, data: bytes) -> SoundBankEditor:
        return cls(SoundBank.from_bytes(data))

    @property
    def version(self) -> int:
        return self.original.version

    @property
    def bank_id(self) -> int:
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
        selected = _resolve_media_index(self._media, index=index, media_id=media_id)
        return self._media[selected]

    def extract_media(
        self, *, index: int | None = None, media_id: int | None = None
    ) -> bytes:
        return self.media_entry(index=index, media_id=media_id).payload

    def extract_all_media(self) -> dict[int, bytes]:
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
                elif object_type == HIRC_RANDOM_SEQUENCE_CONTAINER:
                    layout = _parse_random_sequence_container_tail(
                        body, f"new Container {object_id}"
                    )
                    missing_children = [
                        child_id
                        for child_id in layout.children
                        if child_id not in object_ids
                    ]
                    if missing_children:
                        raise SoundBankError(
                            f"new Container {object_id} references missing child "
                            f"objects: {missing_children}"
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
        return self.original.diff(self.validate())

    def write_atomic(self, output: Path | str, *, overwrite: bool = False) -> Path:
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
