"""Guarded parsing and structural editing for Wwise HIRC objects."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import struct

from ._binary import check_unsigned
from ._pitch import (
    HircPitchSettings,
    _encode_pitch_settings,
    _pack_cents,
    _pack_pitch_range,
    _parse_pitch_layout,
)
from .errors import SoundBankError


SUPPORTED_EDIT_VERSION = 120
HIRC_SOUND = 0x02
HIRC_ACTION = 0x03
HIRC_EVENT = 0x04
HIRC_RANDOM_SEQUENCE_CONTAINER = 0x05
HIRC_SWITCH_CONTAINER = 0x06
HIRC_ACTOR_MIXER = 0x07
ACTION_STOP = 0x0103
ACTION_PLAY = 0x0403
ACTION_PLAY_EVENT = 0x2103


@dataclass
class HircObject:
    """One mutable HIRC object body."""

    index: int
    object_type: int
    object_id: int
    body: bytearray


@dataclass(frozen=True)
class _RandomSequenceContainerTail:
    """Parsed terminal child and playlist fields from one v120 Container."""

    children_offset: int
    children: tuple[int, ...]
    playlist: tuple[tuple[int, int], ...]
    avoid_repeat_count: int
    mode: int


@dataclass(frozen=True)
class SwitchNodeParams:
    """One v120 Switch Container child behavior record."""

    node_id: int
    behavior_flags: int
    transition_flags: int
    fade_out_ms: int
    fade_in_ms: int


@dataclass(frozen=True)
class SwitchContainerTopology:
    """Guardable terminal routing topology for one v120 Switch Container."""

    group_type: int
    group_id: int
    default_switch: int
    continuous_validation: int
    children: tuple[int, ...]
    switch_packages: tuple[tuple[int, tuple[int, ...]], ...]
    node_params: tuple[SwitchNodeParams, ...]


@dataclass(frozen=True)
class _SwitchContainerTail:
    """Parsed v120 Switch Container tail and its object-relative offset."""

    offset: int
    topology: SwitchContainerTopology


def _check_u32(value: int, label: str) -> int:
    return check_unsigned(value, 32, label, SoundBankError)


def _check_u8(value: int, label: str) -> int:
    return check_unsigned(value, 8, label, SoundBankError)


def _check_u16(value: int, label: str) -> int:
    return check_unsigned(value, 16, label, SoundBankError)


def _check_i32(value: int, label: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not -(1 << 31) <= value < (1 << 31)
    ):
        raise SoundBankError(f"{label} must be a signed 32-bit integer: {value!r}")
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

        children = struct.unpack_from(f"<{count}I", body, children_offset + 4)
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


def _normalize_switch_container_topology(
    value: SwitchContainerTopology,
    label: str,
) -> SwitchContainerTopology:
    if not isinstance(value, SwitchContainerTopology):
        raise SoundBankError(f"{label} must be a SwitchContainerTopology")

    group_type = _check_u8(value.group_type, f"{label} group type")
    if group_type not in (0, 1):
        raise SoundBankError(f"{label} group type must be Switch or State")
    group_id = _check_u32(value.group_id, f"{label} group ID")
    default_switch = _check_u32(value.default_switch, f"{label} default switch")
    continuous_validation = _check_u8(
        value.continuous_validation, f"{label} continuous-validation flag"
    )
    if continuous_validation not in (0, 1):
        raise SoundBankError(
            f"{label} continuous-validation flag must be zero or one"
        )

    children = tuple(
        _check_u32(child_id, f"{label} child #{index} ID")
        for index, child_id in enumerate(value.children, 1)
    )
    if not children:
        raise SoundBankError(f"{label} must contain at least one child")
    if len(children) != len(set(children)):
        raise SoundBankError(f"{label} child IDs must be unique")

    packages: list[tuple[int, tuple[int, ...]]] = []
    for index, package in enumerate(value.switch_packages, 1):
        if not isinstance(package, (tuple, list)) or len(package) != 2:
            raise SoundBankError(
                f"{label} package #{index} must be a (switch ID, node IDs) pair"
            )
        switch_id = _check_u32(package[0], f"{label} package #{index} switch ID")
        node_ids = tuple(
            _check_u32(node_id, f"{label} package #{index} node #{node_index} ID")
            for node_index, node_id in enumerate(package[1], 1)
        )
        if not node_ids:
            raise SoundBankError(f"{label} package #{index} may not be empty")
        if len(node_ids) != len(set(node_ids)):
            raise SoundBankError(f"{label} package #{index} node IDs must be unique")
        packages.append((switch_id, node_ids))
    if not packages:
        raise SoundBankError(f"{label} must contain at least one switch package")
    switch_ids = tuple(switch_id for switch_id, _ in packages)
    if len(switch_ids) != len(set(switch_ids)):
        raise SoundBankError(f"{label} switch IDs must be unique")
    if default_switch not in switch_ids:
        raise SoundBankError(
            f"{label} default switch {default_switch} has no switch package"
        )

    child_ids = set(children)
    package_node_ids = {
        node_id for _, node_ids in packages for node_id in node_ids
    }
    unknown_package_nodes = package_node_ids - child_ids
    if unknown_package_nodes:
        raise SoundBankError(
            f"{label} packages reference non-child nodes: "
            f"{sorted(unknown_package_nodes)}"
        )
    if package_node_ids != child_ids:
        raise SoundBankError(
            f"{label} children without a switch package: "
            f"{sorted(child_ids - package_node_ids)}"
        )

    node_params: list[SwitchNodeParams] = []
    for index, params in enumerate(value.node_params, 1):
        if not isinstance(params, SwitchNodeParams):
            raise SoundBankError(
                f"{label} node params #{index} must be a SwitchNodeParams"
            )
        node_params.append(
            SwitchNodeParams(
                node_id=_check_u32(
                    params.node_id, f"{label} node params #{index} node ID"
                ),
                behavior_flags=_check_u8(
                    params.behavior_flags,
                    f"{label} node params #{index} behavior flags",
                ),
                transition_flags=_check_u8(
                    params.transition_flags,
                    f"{label} node params #{index} transition flags",
                ),
                fade_out_ms=_check_i32(
                    params.fade_out_ms, f"{label} node params #{index} fade-out"
                ),
                fade_in_ms=_check_i32(
                    params.fade_in_ms, f"{label} node params #{index} fade-in"
                ),
            )
        )
    param_node_ids = tuple(params.node_id for params in node_params)
    if len(param_node_ids) != len(set(param_node_ids)):
        raise SoundBankError(f"{label} node-param IDs must be unique")
    if set(param_node_ids) != child_ids:
        raise SoundBankError(
            f"{label} node params must cover every child exactly once"
        )

    return SwitchContainerTopology(
        group_type=group_type,
        group_id=group_id,
        default_switch=default_switch,
        continuous_validation=continuous_validation,
        children=children,
        switch_packages=tuple(packages),
        node_params=tuple(node_params),
    )


def _parse_switch_container_tail(
    body: bytes | bytearray,
    label: str,
) -> _SwitchContainerTail:
    """Locate the terminal v120 Switch routing structures unambiguously."""

    candidates: list[_SwitchContainerTail] = []
    for offset in range(4, max(4, len(body) - 13)):
        if body[offset] not in (0, 1):
            continue
        position = offset
        try:
            group_type = body[position]
            position += 1
            group_id, default_switch = struct.unpack_from("<II", body, position)
            position += 8
            continuous_validation = body[position]
            position += 1

            child_count = struct.unpack_from("<I", body, position)[0]
            position += 4
            if not child_count or position + 4 * child_count > len(body):
                continue
            children = struct.unpack_from(f"<{child_count}I", body, position)
            position += 4 * child_count

            package_count = struct.unpack_from("<I", body, position)[0]
            position += 4
            if not package_count or package_count > (len(body) - position) // 8:
                continue
            packages: list[tuple[int, tuple[int, ...]]] = []
            for _ in range(package_count):
                if position + 8 > len(body):
                    raise struct.error
                switch_id, node_count = struct.unpack_from("<II", body, position)
                position += 8
                if not node_count or position + 4 * node_count > len(body):
                    raise struct.error
                node_ids = struct.unpack_from(f"<{node_count}I", body, position)
                position += 4 * node_count
                packages.append((switch_id, node_ids))

            if position + 4 > len(body):
                continue
            params_count = struct.unpack_from("<I", body, position)[0]
            position += 4
            if not params_count or position + 14 * params_count != len(body):
                continue
            node_params: list[SwitchNodeParams] = []
            for _ in range(params_count):
                node_id, behavior_flags, transition_flags, fade_out, fade_in = (
                    struct.unpack_from("<IBBii", body, position)
                )
                position += 14
                node_params.append(
                    SwitchNodeParams(
                        node_id=node_id,
                        behavior_flags=behavior_flags,
                        transition_flags=transition_flags,
                        fade_out_ms=fade_out,
                        fade_in_ms=fade_in,
                    )
                )

            topology = _normalize_switch_container_topology(
                SwitchContainerTopology(
                    group_type=group_type,
                    group_id=group_id,
                    default_switch=default_switch,
                    continuous_validation=continuous_validation,
                    children=children,
                    switch_packages=tuple(packages),
                    node_params=tuple(node_params),
                ),
                label,
            )
        except (IndexError, struct.error, SoundBankError):
            continue
        candidates.append(_SwitchContainerTail(offset=offset, topology=topology))

    if len(candidates) != 1:
        raise SoundBankError(
            f"{label}: expected one unambiguous v120 Switch Container tail, "
            f"found {len(candidates)}"
        )
    return candidates[0]


def _build_switch_container_tail(topology: SwitchContainerTopology) -> bytes:
    payload = bytearray(
        struct.pack(
            "<BIIB",
            topology.group_type,
            topology.group_id,
            topology.default_switch,
            topology.continuous_validation,
        )
    )
    payload += struct.pack("<I", len(topology.children))
    payload += struct.pack(f"<{len(topology.children)}I", *topology.children)
    payload += struct.pack("<I", len(topology.switch_packages))
    for switch_id, node_ids in topology.switch_packages:
        payload += struct.pack("<II", switch_id, len(node_ids))
        payload += struct.pack(f"<{len(node_ids)}I", *node_ids)
    payload += struct.pack("<I", len(topology.node_params))
    for params in topology.node_params:
        payload += struct.pack(
            "<IBBii",
            params.node_id,
            params.behavior_flags,
            params.transition_flags,
            params.fade_out_ms,
            params.fade_in_ms,
        )
    return bytes(payload)


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
        self._reserved_ids = {
            _check_u32(value, "reserved ID") for value in reserved_ids
        }
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
                raise SoundBankError(
                    f"HIRC object #{index} is too small to contain an ID"
                )
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
            raise SoundBankError(
                f"HIRC object ID conflicts with a Media ID: {item.object_id}"
            )
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
            HircObject(
                item.index,
                item.object_type,
                item.object_id,
                bytearray(item.body),
            )
            for item in self._objects
        )

    def object_body(self, object_type: int, object_id: int) -> bytes:
        return bytes(self._get_object(object_type, object_id).body)

    def object(self, object_type: int, object_id: int) -> HircObject:
        item = self._get_object(object_type, object_id)
        return HircObject(
            item.index, item.object_type, item.object_id, bytearray(item.body)
        )

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
            raise SoundBankError(
                f"Media ID conflicts with a HIRC object ID: {object_id}"
            )
        self._reserved_ids.add(object_id)

    def pitch_settings(self, object_type: int, object_id: int) -> HircPitchSettings:
        """Read local v120 Pitch properties, distinguishing absence from zero."""

        self._require_v120("read node pitch")
        object_type = _check_u8(object_type, "HIRC object type")
        object_id = _check_u32(object_id, "HIRC object ID")
        label = f"read pitch for object {object_id}"
        body = self.object_body(object_type, object_id)
        return _parse_pitch_layout(body, object_type, label).settings(label)

    def set_pitch(
            self,
            object_type: int,
            object_id: int,
            *,
            expected: HircPitchSettings,
            base_cents: float | None = None,
            random_range_cents: tuple[float, float] | None = None,
            label: str = "set node pitch",
    ) -> HircPitchSettings:
        """Guard and upsert local Pitch properties; omitted values are retained.

        Values are cents encoded as float32. None in ``expected`` guards an
        absent property; None in a replacement leaves that property alone.
        Parent contributions are not changed. All fields are preflighted
        before any mutation, including existing patch/rebuild conflicts.
        """

        self._require_v120(label)
        object_type = _check_u8(object_type, "HIRC object type")
        object_id = _check_u32(object_id, "HIRC object ID")
        if base_cents is None and random_range_cents is None:
            raise SoundBankError(f"{label}: specify at least one Pitch setting")
        body = self.object_body(object_type, object_id)
        layout = _parse_pitch_layout(body, object_type, label)
        current = layout.settings(label)
        if layout.encoded != _encode_pitch_settings(expected, f"{label} expected"):
            raise SoundBankError(
                f"{label}: object {object_id} expected pitch {expected} "
                f"but found {current}"
            )
        base = layout.base.pitch if base_cents is None else _pack_cents(base_cents, label)
        random = (
            layout.random.pitch
            if random_range_cents is None
            else _pack_pitch_range(random_range_cents, label)
        )
        candidate = layout.replace(body, base, random, label)
        read_back = _parse_pitch_layout(candidate, object_type, label)
        result = read_back.settings(label)
        if read_back.encoded != (base, random):
            raise SoundBankError(f"{label}: Pitch read-back verification failed")
        if candidate == body:
            return result

        if len(candidate) != len(body):
            self.replace_object_body(object_type, object_id, body, candidate, label=label)
        else:
            patches = []
            for bundle, value in ((layout.base, base), (layout.random, random)):
                if bundle.pitch != value:
                    patches.append((bundle.pitch_offset, bundle.pitch, value))
            # A later conflict must not leave an earlier field partially edited.
            for offset, old, new in patches:
                self._check_patch(object_type, object_id, offset, old, new, label=label)
            for offset, old, new in patches:
                self.patch_bytes(object_type, object_id, offset, old, new, label=label)
        return result

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
        item = self._check_patch(
            object_type, object_id, offset, expected, replacement, label=label
        )
        end = offset + len(expected)
        item.body[offset:end] = replacement
        self._patched_ranges.setdefault((object_type, object_id), []).append((offset, end))
        self._changed_byte_count += sum(
            before != after for before, after in zip(expected, replacement)
        )

    def _check_patch(
            self,
            object_type: int,
            object_id: int,
            offset: int,
            expected: bytes,
            replacement: bytes,
            *,
            label: str,
    ) -> HircObject:
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
        return item

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
        if (
            len(replacement) < 4
            or struct.unpack_from("<I", replacement, 0)[0] != object_id
        ):
            raise SoundBankError(
                f"{label}: replacement must preserve object ID {object_id}"
            )
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
                index
                for index, item in enumerate(self._objects)
                if item.object_type == object_type
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

    def _container_insertion_anchor(
        self,
        object_type: int,
        child_ids: Iterable[int],
    ) -> tuple[int, int]:
        """Keep type grouping while placing a Container after every child."""

        candidates = [
            item for item in self._objects if item.object_type == object_type
        ]
        candidates.extend(self._by_id[child_id] for child_id in child_ids)
        latest = max(candidates, key=lambda item: item.index)
        return latest.object_type, latest.object_id

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
            raise SoundBankError(
                f"{label}: Event {event_id} already contains Action {action_id}"
            )
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

    def clone_stop_action(
        self,
        donor_action_id: int,
        new_action_id: int,
        new_target_id: int,
        *,
        expected_target_id: int,
        expected_body_sha256: str,
        before_event_id: int,
        label: str = "clone Stop Action",
    ) -> HircObject:
        """Clone a reviewed v120 Stop Action and retarget its playback object."""

        self._require_v120(label)
        donor = self.object_body(HIRC_ACTION, donor_action_id)
        if len(donor) < 10:
            raise SoundBankError(
                f"{label}: donor Action {donor_action_id} is too short"
            )
        action_type = struct.unpack_from("<H", donor, 4)[0]
        if action_type != ACTION_STOP:
            raise SoundBankError(
                f"{label}: donor Action {donor_action_id} is not a Stop Action"
            )
        if (
            not isinstance(expected_body_sha256, str)
            or len(expected_body_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in expected_body_sha256
            )
        ):
            raise SoundBankError(
                f"{label}: expected body SHA-256 must be 64 lowercase hex characters"
            )
        actual_sha256 = hashlib.sha256(donor).hexdigest()
        if actual_sha256 != expected_body_sha256:
            raise SoundBankError(
                f"{label}: donor Action {donor_action_id} expected body SHA-256 "
                f"{expected_body_sha256} but found {actual_sha256}"
            )
        expected_target_id = _check_u32(
            expected_target_id, "expected target object ID"
        )
        actual_target_id = struct.unpack_from("<I", donor, 6)[0]
        if actual_target_id != expected_target_id:
            raise SoundBankError(
                f"{label}: donor Action {donor_action_id} expected target object "
                f"ID {expected_target_id} but found {actual_target_id}"
            )
        new_target_id = _check_u32(new_target_id, "new target object ID")
        if new_target_id not in self._by_id:
            raise SoundBankError(
                f"{label}: target object does not exist: {new_target_id}"
            )
        before_event_id = _check_u32(before_event_id, "before Event ID")
        self._get_object(HIRC_EVENT, before_event_id)

        cloned = bytearray(donor)
        struct.pack_into("<I", cloned, 0, _check_u32(new_action_id, "new Action ID"))
        struct.pack_into("<I", cloned, 6, new_target_id)
        return self.insert_object(
            HIRC_ACTION,
            new_action_id,
            bytes(cloned[4:]),
            before=(HIRC_EVENT, before_event_id),
            label=label,
        )

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
            raise SoundBankError(
                f"{label}: donor Sound {donor_sound_id} is too short"
            )
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
        struct.pack_into(
            "<I", cloned, 9, _check_u32(new_source_id, "new source ID")
        )
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
                raise SoundBankError(
                    f"{label}: child object does not exist: {child_id}"
                )

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
            after=self._container_insertion_anchor(
                HIRC_RANDOM_SEQUENCE_CONTAINER, child_ids
            ),
            label=label,
        )

    def switch_container_topology(
        self,
        container_id: int,
    ) -> SwitchContainerTopology:
        """Return the parsed terminal topology of one v120 Switch Container."""

        self._require_v120("parse Switch Container topology")
        body = self.object_body(HIRC_SWITCH_CONTAINER, container_id)
        return _parse_switch_container_tail(
            body, f"Switch Container {container_id}"
        ).topology

    def clone_switch_container(
        self,
        donor_container_id: int,
        new_container_id: int,
        child_map: Mapping[int, int | None],
        *,
        expected_topology: SwitchContainerTopology,
        expected_body_sha256: str,
        label: str = "clone Switch Container",
    ) -> HircObject:
        """Clone a reviewed v120 Switch Container and filter/remap its children."""

        self._require_v120(label)
        donor = self.object_body(HIRC_SWITCH_CONTAINER, donor_container_id)
        if (
            not isinstance(expected_body_sha256, str)
            or len(expected_body_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in expected_body_sha256
            )
        ):
            raise SoundBankError(
                f"{label}: expected body SHA-256 must be 64 lowercase hex characters"
            )
        actual_sha256 = hashlib.sha256(donor).hexdigest()
        if actual_sha256 != expected_body_sha256:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} expected body "
                f"SHA-256 {expected_body_sha256} but found {actual_sha256}"
            )

        layout = _parse_switch_container_tail(donor, label)
        guarded_topology = _normalize_switch_container_topology(
            expected_topology, f"{label} expected topology"
        )
        if layout.topology != guarded_topology:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} topology changed"
            )

        if not isinstance(child_map, Mapping):
            raise SoundBankError(f"{label}: child_map must be a mapping")
        normalized_map: dict[int, int | None] = {}
        for old_child_id, new_child_id in child_map.items():
            old_child_id = _check_u32(old_child_id, f"{label} old child ID")
            if new_child_id is not None:
                new_child_id = _check_u32(new_child_id, f"{label} new child ID")
            normalized_map[old_child_id] = new_child_id

        expected_children = set(layout.topology.children)
        actual_children = set(normalized_map)
        if actual_children != expected_children:
            raise SoundBankError(
                f"{label}: child_map must cover every donor child exactly once; "
                f"missing={sorted(expected_children - actual_children)}, "
                f"extra={sorted(actual_children - expected_children)}"
            )
        retained_children = tuple(
            normalized_map[child_id]
            for child_id in layout.topology.children
            if normalized_map[child_id] is not None
        )
        if not retained_children:
            raise SoundBankError(f"{label}: child_map may not remove every child")
        if len(retained_children) != len(set(retained_children)):
            raise SoundBankError(
                f"{label}: retained replacement child IDs must be unique"
            )
        for child_id in retained_children:
            if child_id not in self._by_id:
                raise SoundBankError(
                    f"{label}: replacement child object does not exist: {child_id}"
                )

        remapped_packages: list[tuple[int, tuple[int, ...]]] = []
        for switch_id, node_ids in layout.topology.switch_packages:
            remapped_nodes = tuple(
                normalized_map[node_id]
                for node_id in node_ids
                if normalized_map[node_id] is not None
            )
            if remapped_nodes:
                remapped_packages.append((switch_id, remapped_nodes))

        remapped_params = tuple(
            SwitchNodeParams(
                node_id=normalized_map[params.node_id],
                behavior_flags=params.behavior_flags,
                transition_flags=params.transition_flags,
                fade_out_ms=params.fade_out_ms,
                fade_in_ms=params.fade_in_ms,
            )
            for params in layout.topology.node_params
            if normalized_map[params.node_id] is not None
        )
        remapped_topology = _normalize_switch_container_topology(
            SwitchContainerTopology(
                group_type=layout.topology.group_type,
                group_id=layout.topology.group_id,
                default_switch=layout.topology.default_switch,
                continuous_validation=layout.topology.continuous_validation,
                children=retained_children,
                switch_packages=tuple(remapped_packages),
                node_params=remapped_params,
            ),
            f"{label} remapped topology",
        )

        cloned = bytearray(donor[: layout.offset])
        struct.pack_into(
            "<I", cloned, 0, _check_u32(new_container_id, "new Container ID")
        )
        cloned += _build_switch_container_tail(remapped_topology)
        return self.insert_object(
            HIRC_SWITCH_CONTAINER,
            new_container_id,
            bytes(cloned[4:]),
            after=self._container_insertion_anchor(
                HIRC_SWITCH_CONTAINER, retained_children
            ),
            label=label,
        )

    def clone_switch_container_with_topology(
            self,
            donor_container_id: int,
            new_container_id: int,
            replacement_topology: SwitchContainerTopology,
            *,
            expected_topology: SwitchContainerTopology,
            expected_body_sha256: str,
            label: str = "clone Switch Container with explicit topology",
    ) -> HircObject:
        """Clone a reviewed v120 Switch Container with an explicit new tail."""

        self._require_v120(label)
        donor = self.object_body(HIRC_SWITCH_CONTAINER, donor_container_id)
        if (
                not isinstance(expected_body_sha256, str)
                or len(expected_body_sha256) != 64
                or any(
            character not in "0123456789abcdef"
            for character in expected_body_sha256
        )
        ):
            raise SoundBankError(
                f"{label}: expected body SHA-256 must be 64 lowercase hex characters"
            )
        actual_sha256 = hashlib.sha256(donor).hexdigest()
        if actual_sha256 != expected_body_sha256:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} expected body "
                f"SHA-256 {expected_body_sha256} but found {actual_sha256}"
            )

        layout = _parse_switch_container_tail(donor, label)
        guarded_topology = _normalize_switch_container_topology(
            expected_topology, f"{label} expected topology"
        )
        if layout.topology != guarded_topology:
            raise SoundBankError(
                f"{label}: donor Container {donor_container_id} topology changed"
            )

        replacement = _normalize_switch_container_topology(
            replacement_topology, f"{label} replacement topology"
        )
        for child_id in replacement.children:
            if child_id not in self._by_id:
                raise SoundBankError(
                    f"{label}: replacement child object does not exist: {child_id}"
                )

        cloned = bytearray(donor[: layout.offset])
        struct.pack_into(
            "<I", cloned, 0, _check_u32(new_container_id, "new Container ID")
        )
        cloned += _build_switch_container_tail(replacement)
        return self.insert_object(
            HIRC_SWITCH_CONTAINER,
            new_container_id,
            bytes(cloned[4:]),
            after=self._container_insertion_anchor(
                HIRC_SWITCH_CONTAINER, replacement.children
            ),
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
