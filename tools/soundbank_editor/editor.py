"""Lossless NBNK parsing and guarded Wwise v120 editing."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import struct
import tempfile


ALIGNMENT = 16
SUPPORTED_EDIT_VERSION = 120
HIRC_SOUND = 0x02
HIRC_ACTION = 0x03
HIRC_EVENT = 0x04
HIRC_RANDOM_SEQUENCE_CONTAINER = 0x05
ACTION_PLAY = 0x0403
ACTION_PLAY_EVENT = 0x2103


class SoundBankError(Exception):
    """A user-actionable SoundBank parsing or editing failure."""


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


@dataclass
class HircObject:
    """One mutable HIRC object body."""

    index: int
    object_type: int
    object_id: int
    body: bytearray


@dataclass(frozen=True)
class EditSummary:
    """Observable changes made by a SoundBankEditor."""

    replaced_media: tuple[tuple[int, int], ...]
    added_media: tuple[tuple[int, int], ...]
    hirc_changed_bytes: int
    added_hirc_objects: tuple[tuple[int, int], ...]
    resized_hirc_objects: tuple[tuple[int, int, int, int], ...]
    hirc_size_delta: int


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


@dataclass(frozen=True)
class _RandomSequenceContainerTail:
    """Parsed terminal child and playlist fields from one v120 Container."""

    children_offset: int
    children: tuple[int, ...]
    playlist: tuple[tuple[int, int], ...]
    avoid_repeat_count: int
    mode: int


def _check_u32(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFFFFFF:
        raise SoundBankError(f"{label} must be an unsigned 32-bit integer: {value!r}")
    return value


def _check_u8(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFF:
        raise SoundBankError(f"{label} must be an unsigned byte: {value!r}")
    return value


def _check_u16(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFF:
        raise SoundBankError(f"{label} must be an unsigned 16-bit integer: {value!r}")
    return value


def _normalize_random_playlist(
    value: Sequence[tuple[int, int]], label: str
) -> tuple[tuple[int, int], ...]:
    if isinstance(value, (str, bytes, bytearray)):
        raise SoundBankError(f"{label} must be a sequence of (child ID, weight) pairs")
    try:
        items = tuple(value)
    except TypeError as error:
        raise SoundBankError(
            f"{label} must be a sequence of (child ID, weight) pairs"
        ) from error
    if not items:
        raise SoundBankError(f"{label} must contain at least one child")
    if len(items) > 0xFFFF:
        raise SoundBankError(f"{label} cannot contain more than 65535 children")

    normalized: list[tuple[int, int]] = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise SoundBankError(
                f"{label} item #{index} must be a (child ID, weight) pair"
            )
        child_id = _check_u32(item[0], f"{label} item #{index} child ID")
        weight = item[1]
        if (
            not isinstance(weight, int)
            or isinstance(weight, bool)
            or not 1 <= weight <= 0x7FFFFFFF
        ):
            raise SoundBankError(
                f"{label} item #{index} weight must be a positive signed 32-bit "
                f"integer: {weight!r}"
            )
        normalized.append((child_id, weight))

    child_ids = [child_id for child_id, _ in normalized]
    if len(child_ids) != len(set(child_ids)):
        raise SoundBankError(f"{label} child IDs must be unique")
    return tuple(normalized)


def _parse_random_sequence_container_tail(
    body: bytes | bytearray, label: str
) -> _RandomSequenceContainerTail:
    """Locate the terminal Children/CAkPlayList layout used by Wwise v120."""

    candidates: list[_RandomSequenceContainerTail] = []
    for count in range(1, max(1, (len(body) - 6) // 12 + 1)):
        playlist_offset = len(body) - 2 - 8 * count
        children_offset = playlist_offset - 4 - 4 * count
        if children_offset < 10:
            continue
        if struct.unpack_from("<H", body, playlist_offset)[0] != count:
            continue
        if struct.unpack_from("<I", body, children_offset)[0] != count:
            continue

        children = struct.unpack_from(
            f"<{count}I", body, children_offset + 4
        )
        playlist = tuple(
            struct.unpack_from("<Ii", body, playlist_offset + 2 + 8 * index)
            for index in range(count)
        )
        if len(set(children)) != count:
            continue
        if sorted(children) != sorted(child_id for child_id, _ in playlist):
            continue
        candidates.append(
            _RandomSequenceContainerTail(
                children_offset=children_offset,
                children=children,
                playlist=playlist,
                avoid_repeat_count=struct.unpack_from(
                    "<H", body, children_offset - 6
                )[0],
                mode=body[children_offset - 2],
            )
        )

    if len(candidates) != 1:
        raise SoundBankError(
            f"{label}: expected one unambiguous v120 Children/playlist tail, "
            f"found {len(candidates)}"
        )
    return candidates[0]


def wwise_fnv1(name: str) -> int:
    """Return Wwise's lowercase 32-bit FNV-1 object-name hash."""

    if not isinstance(name, str) or not name:
        raise SoundBankError("Wwise hash name must be a non-empty string")
    value = 2166136261
    for byte in name.lower().encode("utf-8"):
        value = ((value * 16777619) ^ byte) & 0xFFFFFFFF
    return value


def _coerce_payload(value: bytes | bytearray | memoryview | Path | str, label: str) -> bytes:
    if isinstance(value, (Path, str)):
        path = Path(value)
        if not path.is_file():
            raise SoundBankError(f"{label} does not exist: {path}")
        return path.read_bytes()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    raise SoundBankError(f"{label} must be bytes or a filesystem path")


def validate_wem(value: bytes | bytearray | memoryview | Path | str) -> bytes:
    """Read and validate a Wwise RIFF/WAVE media payload."""

    payload = _coerce_payload(value, "WEM")
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


class HircEditor:
    """Parse and edit HIRC objects using guarded object-relative operations."""

    def __init__(
        self,
        payload: bytes,
        *,
        version: int = SUPPORTED_EDIT_VERSION,
        reserved_ids: Iterable[int] = (),
    ):
        if len(payload) < 4:
            raise SoundBankError("HIRC payload is missing its object count")
        self.version = version
        self._original_payload = bytes(payload)
        self._objects: list[HircObject] = []
        self._by_key: dict[tuple[int, int], HircObject] = {}
        self._by_id: dict[int, HircObject] = {}
        self._reserved_ids = {_check_u32(value, "reserved ID") for value in reserved_ids}
        self._patched_ranges: dict[tuple[int, int], list[tuple[int, int]]] = {}
        self._replaced_keys: set[tuple[int, int]] = set()
        self._changed_byte_count = 0
        self._added_keys: list[tuple[int, int]] = []
        self._original_sizes: dict[tuple[int, int], int] = {}

        count = struct.unpack_from("<I", payload, 0)[0]
        position = 4
        for index in range(count):
            if position + 5 > len(payload):
                raise SoundBankError(f"HIRC object #{index} is missing its header")
            object_type = payload[position]
            size = struct.unpack_from("<I", payload, position + 1)[0]
            body_start = position + 5
            body_end = body_start + size
            if body_end > len(payload):
                raise SoundBankError(f"HIRC object #{index} extends beyond the chunk")
            if size < 4:
                raise SoundBankError(f"HIRC object #{index} is too small to contain an ID")
            body = bytearray(payload[body_start:body_end])
            object_id = struct.unpack_from("<I", body, 0)[0]
            item = HircObject(index, object_type, object_id, body)
            self._objects.append(item)
            self._register(item, new=False)
            position = body_end
        if position != len(payload):
            raise SoundBankError(
                f"HIRC has {len(payload) - position} trailing bytes after its objects"
            )

    def _register(self, item: HircObject, *, new: bool) -> None:
        key = (item.object_type, item.object_id)
        if key in self._by_key:
            raise SoundBankError(
                f"HIRC contains duplicate type 0x{item.object_type:02X} object ID "
                f"{item.object_id}"
            )
        if item.object_id in self._by_id:
            previous = self._by_id[item.object_id]
            raise SoundBankError(
                f"HIRC object ID {item.object_id} is also used by type "
                f"0x{previous.object_type:02X}"
            )
        if new and item.object_id in self._reserved_ids:
            raise SoundBankError(f"HIRC object ID conflicts with a Media ID: {item.object_id}")
        self._by_key[key] = item
        self._by_id[item.object_id] = item
        if new:
            self._added_keys.append(key)
        else:
            self._original_sizes[key] = len(item.body)

    def _require_v120(self, operation: str) -> None:
        if self.version != SUPPORTED_EDIT_VERSION:
            raise SoundBankError(
                f"{operation} requires Wwise v{SUPPORTED_EDIT_VERSION}; "
                f"this Bank is v{self.version}"
            )

    @property
    def changed_byte_count(self) -> int:
        return self._changed_byte_count

    @property
    def added_objects(self) -> tuple[tuple[int, int], ...]:
        return tuple(self._added_keys)

    @property
    def object_ids(self) -> frozenset[int]:
        return frozenset(self._by_id)

    @property
    def patched_objects(self) -> tuple[tuple[int, int], ...]:
        return tuple(self._patched_ranges)

    @property
    def rebuilt_objects(self) -> tuple[tuple[int, int], ...]:
        return tuple(self._replaced_keys)

    def objects(self) -> tuple[HircObject, ...]:
        """Return copies of all objects in serialized order."""

        return tuple(
            HircObject(item.index, item.object_type, item.object_id, bytearray(item.body))
            for item in self._objects
        )

    def object_body(self, object_type: int, object_id: int) -> bytes:
        return bytes(self._get_object(object_type, object_id).body)

    def object(self, object_type: int, object_id: int) -> HircObject:
        item = self._get_object(object_type, object_id)
        return HircObject(item.index, item.object_type, item.object_id, bytearray(item.body))

    def _get_object(self, object_type: int, object_id: int) -> HircObject:
        try:
            return self._by_key[(object_type, object_id)]
        except KeyError as error:
            raise SoundBankError(
                f"HIRC object not found: type 0x{object_type:02X}, ID {object_id}"
            ) from error

    def reserve_id(self, object_id: int) -> None:
        object_id = _check_u32(object_id, "reserved ID")
        if object_id in self._by_id:
            raise SoundBankError(f"Media ID conflicts with a HIRC object ID: {object_id}")
        self._reserved_ids.add(object_id)

    def patch_bytes(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: bytes,
        replacement: bytes,
        *,
        label: str,
    ) -> None:
        if len(expected) != len(replacement):
            raise SoundBankError(f"{label}: HIRC field patches must preserve length")
        if not expected:
            raise SoundBankError(f"{label}: HIRC patch may not be empty")
        if offset < 4:
            raise SoundBankError(f"{label}: patch may not alter the HIRC object ID")
        item = self._get_object(object_type, object_id)
        end = offset + len(expected)
        if end > len(item.body):
            raise SoundBankError(
                f"{label}: object ID {object_id} range 0x{offset:X}..0x{end:X} "
                f"exceeds its {len(item.body)}-byte body"
            )
        key = (object_type, object_id)
        if key in self._replaced_keys:
            raise SoundBankError(f"{label}: object ID {object_id} was already rebuilt")
        for prior_start, prior_end in self._patched_ranges.get(key, []):
            if offset < prior_end and prior_start < end:
                raise SoundBankError(
                    f"{label}: patch overlaps an earlier edit to object ID {object_id}"
                )
        actual = bytes(item.body[offset:end])
        if actual != expected:
            raise SoundBankError(
                f"{label}: object type 0x{object_type:02X} ID {object_id} "
                f"at body+0x{offset:X} expected {expected.hex()} but found {actual.hex()}"
            )
        item.body[offset:end] = replacement
        self._patched_ranges.setdefault(key, []).append((offset, end))
        self._changed_byte_count += sum(
            before != after for before, after in zip(expected, replacement)
        )

    def patch_u8(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: int,
        replacement: int,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<B", _check_u8(expected, "expected value")),
            struct.pack("<B", _check_u8(replacement, "replacement value")),
            label=label,
        )

    def patch_u16(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: int,
        replacement: int,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<H", _check_u16(expected, "expected value")),
            struct.pack("<H", _check_u16(replacement, "replacement value")),
            label=label,
        )

    def patch_u32(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: int,
        replacement: int,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<I", _check_u32(expected, "expected value")),
            struct.pack("<I", _check_u32(replacement, "replacement value")),
            label=label,
        )

    def patch_float(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: float,
        replacement: float,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<f", expected),
            struct.pack("<f", replacement),
            label=label,
        )

    def replace_object_body(
        self,
        object_type: int,
        object_id: int,
        expected: bytes,
        replacement: bytes,
        *,
        label: str,
    ) -> None:
        item = self._get_object(object_type, object_id)
        key = (object_type, object_id)
        if self._patched_ranges.get(key):
            raise SoundBankError(f"{label}: object ID {object_id} was already edited")
        actual = bytes(item.body)
        if actual != expected:
            raise SoundBankError(
                f"{label}: object type 0x{object_type:02X} ID {object_id} body changed"
            )
        if len(replacement) < 4 or struct.unpack_from("<I", replacement, 0)[0] != object_id:
            raise SoundBankError(f"{label}: replacement must preserve object ID {object_id}")
        if len(replacement) != len(actual):
            self._require_v120(label)
        item.body[:] = replacement
        self._replaced_keys.add(key)
        self._changed_byte_count += sum(
            before != after for before, after in zip(actual, replacement)
        )

    def insert_object(
        self,
        object_type: int,
        object_id: int,
        body_tail: bytes,
        *,
        after: tuple[int, int] | None = None,
        before: tuple[int, int] | None = None,
        label: str = "insert HIRC object",
    ) -> HircObject:
        self._require_v120(label)
        object_type = _check_u8(object_type, "HIRC object type")
        object_id = _check_u32(object_id, "HIRC object ID")
        if not isinstance(body_tail, bytes):
            raise SoundBankError(f"{label}: body_tail must be bytes")
        if object_id in self._by_id or object_id in self._reserved_ids:
            raise SoundBankError(f"{label}: ID already exists: {object_id}")
        if after is not None and before is not None:
            raise SoundBankError(f"{label}: select at most one insertion anchor")
        if before is not None:
            anchor = self._get_object(*before)
            position = self._objects.index(anchor)
        elif after is not None:
            anchor = self._get_object(*after)
            position = self._objects.index(anchor) + 1
        else:
            same_type = [
                index for index, item in enumerate(self._objects) if item.object_type == object_type
            ]
            position = same_type[-1] + 1 if same_type else len(self._objects)
        body = bytearray(struct.pack("<I", object_id) + body_tail)
        item = HircObject(position, object_type, object_id, body)
        self._objects.insert(position, item)
        self._register(item, new=True)
        self._reindex()
        return self.object(object_type, object_id)

    def _reindex(self) -> None:
        for index, item in enumerate(self._objects):
            item.index = index

    def event_actions(self, event_id: int) -> tuple[int, ...]:
        self._require_v120("parse Event actions")
        body = self.object_body(HIRC_EVENT, event_id)
        if len(body) < 8:
            raise SoundBankError(f"Event {event_id} body is too short")
        count = struct.unpack_from("<I", body, 4)[0]
        expected_size = 8 + 4 * count
        if len(body) != expected_size:
            raise SoundBankError(
                f"Event {event_id} body size {len(body)} does not match {count} actions"
            )
        if not count:
            return ()
        return struct.unpack_from(f"<{count}I", body, 8)

    def append_event_action(
        self,
        event_id: int,
        action_id: int,
        *,
        expected_actions: Sequence[int],
        label: str = "append Event Action",
    ) -> None:
        self._require_v120(label)
        action_id = _check_u32(action_id, "Action ID")
        self._get_object(HIRC_ACTION, action_id)
        actual_actions = self.event_actions(event_id)
        guarded_actions = tuple(expected_actions)
        if actual_actions != guarded_actions:
            raise SoundBankError(
                f"{label}: Event {event_id} expected actions {guarded_actions} "
                f"but found {actual_actions}"
            )
        if action_id in actual_actions:
            raise SoundBankError(f"{label}: Event {event_id} already contains Action {action_id}")
        expected_body = self.object_body(HIRC_EVENT, event_id)
        new_actions = actual_actions + (action_id,)
        replacement = struct.pack("<II", event_id, len(new_actions)) + struct.pack(
            f"<{len(new_actions)}I", *new_actions
        )
        self.replace_object_body(
            HIRC_EVENT,
            event_id,
            expected_body,
            replacement,
            label=label,
        )

    def create_play_event_action(self, action_id: int, target_event_id: int) -> bytes:
        self._require_v120("create PlayEvent Action")
        return struct.pack(
            "<IHI3B",
            _check_u32(action_id, "Action ID"),
            ACTION_PLAY_EVENT,
            _check_u32(target_event_id, "target Event ID"),
            0,
            0,
            0,
        )

    def create_play_action(
        self,
        action_id: int,
        target_id: int,
        bank_id: int,
        *,
        delay_ms: int = 0,
        transition_ms: int | None = None,
        fade_curve: int = 0x04,
    ) -> bytes:
        self._require_v120("create Play Action")
        properties: list[tuple[int, int]] = []
        if delay_ms:
            properties.append((0x0F, _check_u32(delay_ms, "delay_ms")))
        if transition_ms is not None:
            properties.append((0x10, _check_u32(transition_ms, "transition_ms")))
        body = bytearray(
            struct.pack(
                "<IHI",
                _check_u32(action_id, "Action ID"),
                ACTION_PLAY,
                _check_u32(target_id, "target object ID"),
            )
        )
        body += b"\0"
        body += struct.pack("<B", len(properties))
        body += bytes(prop_id for prop_id, _ in properties)
        for _, value in properties:
            body += struct.pack("<I", value)
        body += b"\0"
        body += struct.pack("<B", _check_u8(fade_curve, "fade_curve"))
        body += struct.pack("<I", _check_u32(bank_id, "Bank ID"))
        return bytes(body)

    def clone_sound(
        self,
        donor_sound_id: int,
        new_sound_id: int,
        new_source_id: int,
        *,
        expected_source_id: int,
        label: str = "clone Sound",
    ) -> HircObject:
        self._require_v120(label)
        donor = self.object_body(HIRC_SOUND, donor_sound_id)
        if len(donor) < 18:
            raise SoundBankError(f"{label}: donor Sound {donor_sound_id} is too short")
        if donor[8] != 0:
            raise SoundBankError(
                f"{label}: donor Sound {donor_sound_id} is not an embedded DATA source"
            )
        actual_source_id = struct.unpack_from("<I", donor, 9)[0]
        if actual_source_id != expected_source_id:
            raise SoundBankError(
                f"{label}: donor Sound {donor_sound_id} expected source ID "
                f"{expected_source_id} but found {actual_source_id}"
            )
        cloned = bytearray(donor)
        struct.pack_into("<I", cloned, 0, _check_u32(new_sound_id, "new Sound ID"))
        struct.pack_into("<I", cloned, 9, _check_u32(new_source_id, "new source ID"))
        return self.insert_object(
            HIRC_SOUND,
            new_sound_id,
            bytes(cloned[4:]),
            label=label,
        )

    def clone_random_sequence_container(
        self,
        donor_container_id: int,
        new_container_id: int,
        playlist: Sequence[tuple[int, int]],
        *,
        expected_playlist: Sequence[tuple[int, int]],
        expected_avoid_repeat_count: int,
        avoid_repeat_count: int | None = None,
        label: str = "clone Random/Sequence Container",
    ) -> HircObject:
        """Clone a reviewed v120 Random Container with a rebuilt playlist."""

        self._require_v120(label)
        donor = self.object_body(
            HIRC_RANDOM_SEQUENCE_CONTAINER, donor_container_id
        )
        layout = _parse_random_sequence_container_tail(donor, label)
        if layout.mode != 0:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} is not in Random mode"
            )

        guarded_playlist = _normalize_random_playlist(
            expected_playlist, f"{label} expected playlist"
        )
        if layout.playlist != guarded_playlist:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} expected playlist "
                f"{guarded_playlist} but found {layout.playlist}"
            )
        expected_avoid_repeat_count = _check_u16(
            expected_avoid_repeat_count, "expected avoid-repeat count"
        )
        if layout.avoid_repeat_count != expected_avoid_repeat_count:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} expected "
                f"avoid-repeat count {expected_avoid_repeat_count} but found "
                f"{layout.avoid_repeat_count}"
            )

        new_playlist = _normalize_random_playlist(playlist, f"{label} playlist")
        for child_id, _ in new_playlist:
            if child_id not in self._by_id:
                raise SoundBankError(f"{label}: child object does not exist: {child_id}")

        if avoid_repeat_count is None:
            new_avoid_repeat_count = layout.avoid_repeat_count
        else:
            new_avoid_repeat_count = _check_u16(
                avoid_repeat_count, "avoid-repeat count"
            )

        cloned = bytearray(donor[: layout.children_offset])
        struct.pack_into(
            "<I", cloned, 0, _check_u32(new_container_id, "new Container ID")
        )
        struct.pack_into(
            "<H", cloned, layout.children_offset - 6, new_avoid_repeat_count
        )
        child_ids = tuple(child_id for child_id, _ in new_playlist)
        cloned += struct.pack("<I", len(child_ids))
        cloned += struct.pack(f"<{len(child_ids)}I", *child_ids)
        cloned += struct.pack("<H", len(new_playlist))
        for child_id, weight in new_playlist:
            cloned += struct.pack("<Ii", child_id, weight)

        return self.insert_object(
            HIRC_RANDOM_SEQUENCE_CONTAINER,
            new_container_id,
            bytes(cloned[4:]),
            label=label,
        )

    @property
    def resized_objects(self) -> tuple[tuple[int, int, int, int], ...]:
        resized: list[tuple[int, int, int, int]] = []
        for key, original_size in self._original_sizes.items():
            current_size = len(self._by_key[key].body)
            if current_size != original_size:
                resized.append((*key, original_size, current_size))
        return tuple(resized)

    def build(self) -> bytes:
        output = bytearray(struct.pack("<I", len(self._objects)))
        for item in self._objects:
            output += struct.pack("<BI", item.object_type, len(item.body))
            output += item.body
        return bytes(output)


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
    def summary(self) -> EditSummary:
        return EditSummary(
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
        target = Path(output)
        if self.original.source_path is not None and target.resolve() == self.original.source_path:
            raise SoundBankError("overwriting the input SoundBank in place is not allowed")
        if target.exists() and not overwrite:
            raise SoundBankError(f"output already exists: {target}")
        payload = self.build()
        self.validate()
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
        )
        staged = Path(handle.name)
        try:
            with handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staged, target)
        finally:
            staged.unlink(missing_ok=True)
        return target
