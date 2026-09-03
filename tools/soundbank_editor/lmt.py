"""Lossless MHW LMT v95/TIML parsing and guarded request substitution.

Notes:
    Public names are re-exported by tools.soundbank_editor. Offsets in
    parsed records are absolute LMT byte positions; public Motion IDs are
    zero-based offset-table positions. EventGroup/slot hash constants are
    documented in the package docstring. README.md provides API examples.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
import math
from pathlib import Path
import struct

from ._binary import (
    check_positive_i16,
    require_range,
    write_atomic as _write_atomic,
)
from .errors import LmtError
from .wwev import WwevFile, WwevRecord


SUPPORTED_LMT_VERSION = 95
LMT_HEADER = struct.Struct("<4sHH8s")
LMT_ACTION_HEADER_SIZE = 96
TIML_DATA = struct.Struct("<QQiiffiI")
TIML_TYPE = struct.Struct("<QQIi")
TIML_TRANSFORM = struct.Struct("<QQIi")
TIML_KEYFRAME_SIZE = 20

EVENT_GROUP_HASHES = {
    1_505_807_010: "EventGroup00",
    784_857_652: "EventGroup01",
    936_291_214: "EventGroup02",
    1_086_954_264: "EventGroup03",
    1_588_399_803: "EventGroup04",
    699_022_893: "EventGroup05",
    816_017_303: "EventGroup06",
    1_201_954_561: "EventGroup07",
    1_461_404_304: "EventGroup08",
    538_735_110: "EventGroup09",
    1_088_158_691: "EventGroup10",
}
REQUEST_SLOT_HASHES = (
    3_863_836_990,
    2_135_173_252,
    138_614_802,
    2_519_174_577,
    3_777_019_175,
    2_016_013_469,
    254_729_227,
    2_677_129_626,
)
TRIGGER_HASH = 2_575_924_291
SLOT_NAMES = "ABCDEFGH"
FRAME_TOLERANCE = 1e-5


def _check_frame(value: float, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise LmtError(f"{label} must be a finite frame number: {value!r}")
    return float(value)


def _same_frame(left: float, right: float) -> bool:
    return abs(left - right) <= FRAME_TOLERANCE


def _normalize_trigger_frames(value: Sequence[float]) -> tuple[float, ...]:
    if isinstance(value, (str, bytes, bytearray)):
        raise LmtError("expected trigger frames must be a sequence of frame numbers")
    try:
        frames = tuple(
            _check_frame(frame, "expected trigger frame") for frame in value
        )
    except TypeError as error:
        raise LmtError(
            "expected trigger frames must be a sequence of frame numbers"
        ) from error
    if not frames:
        raise LmtError("expected trigger frames must contain at least one frame")
    return tuple(sorted(set(frames)))


@dataclass(frozen=True)
class TimlKeyframe:
    """Immutable typed keyframe from an embedded TIML transform.

    Attributes:
        offset: Absolute LMT byte offset of the 20-byte keyframe.
        value: Parsed scalar or four-component value according to data_type.
        frame: Finite frame position stored as float32.
        transition: Signed 16-bit transition field.
        data_type: Keyframe type, checked against the enclosing transform.
    """

    offset: int
    value: int | float | tuple[int, int, int, int]
    frame: float
    transition: int
    data_type: int


@dataclass(frozen=True)
class TimlTransform:
    """Immutable TIML property transform and its ordered keyframes.

    Attributes:
        datatype_hash: Unsigned property hash; may identify ReqNo A-H or mTrigger.
        data_type: Type used to parse each keyframe's value.
        keyframes: Keyframes in their original serialized order.
    """

    datatype_hash: int
    data_type: int
    keyframes: tuple[TimlKeyframe, ...]


@dataclass(frozen=True)
class TimlType:
    """Immutable TIML timeline type and its ordered transforms.

    Attributes:
        timeline_hash: Unsigned type hash, mapped to EventGroup names when known.
        transforms: Property transforms in their original serialized order.
    """

    timeline_hash: int
    transforms: tuple[TimlTransform, ...]


@dataclass(frozen=True)
class LmtAction:
    """Immutable populated Motion header and its embedded TIML.

    Attributes:
        motion_id: Zero-based position in the LMT offset table, including holes.
        header_offset: Absolute byte offset of the Motion header.
        fcurve_offset: Absolute stored animation-curve offset; curves are not decoded.
        fcurve_count: Stored animation-curve count.
        frame_count: Stored Motion length in frames.
        loop_frame: Signed loop-frame field, preserved without reinterpretation.
        timl_offset: Absolute embedded TIML offset, or zero when absent.
        timl: Parsed timeline types; empty if TIML is absent.
    """

    motion_id: int
    header_offset: int
    fcurve_offset: int
    fcurve_count: int
    frame_count: int
    loop_frame: int
    timl_offset: int
    timl: tuple[TimlType, ...]

    @property
    def header_identity(self) -> tuple[int, ...]:
        """Return header fields used for preservation checks as an ordered tuple.

        Returns:
            (motion_id, header_offset, fcurve_offset, fcurve_count, frame_count,
            loop_frame, timl_offset); embedded TIML contents are excluded.
        """

        return (
            self.motion_id,
            self.header_offset,
            self.fcurve_offset,
            self.fcurve_count,
            self.frame_count,
            self.loop_frame,
            self.timl_offset,
        )


@dataclass(frozen=True)
class TriggeredRequest:
    """Immutable trigger-to-request row with an optional WWEV record expansion.

    Attributes:
        motion_id: Zero-based Motion ID.
        frame_count: Stored length of that Motion.
        timl_offset: Absolute LMT byte offset of the shared/unshared TIML.
        shared_timl_motions: All Motion IDs using this TIML, including this Motion.
        event_group: Recognized EventGroup00-10 name.
        trigger_frame: Frame at which the slot is activated.
        trigger_mask: Complete stored trigger mask; route selection uses low eight bits.
        slot: Activated ReqNo slot name, A-H.
        request_no: Positive request assignment active at trigger_frame.
        wwev_record: 1-based WWEV record index, or None if unresolved/not supplied.
        wwev_mode: Matched record's signed mode, or None.
        event_id: Matched record's unsigned Event ID, or None.

    Notes:
        Repeated WWEV matches generate separate rows, not a collapsed Event.
    """

    motion_id: int
    frame_count: int
    timl_offset: int
    shared_timl_motions: tuple[int, ...]
    event_group: str
    trigger_frame: float
    trigger_mask: int
    slot: str
    request_no: int
    wwev_record: int | None
    wwev_mode: int | None
    event_id: int | None


def _parse_keyframe(payload: bytes, offset: int, data_type: int) -> TimlKeyframe:
    require_range(payload, offset, TIML_KEYFRAME_SIZE, "TIML keyframe", LmtError)
    if data_type == 0:
        value: int | float | tuple[int, int, int, int] = struct.unpack_from(
            "<i", payload, offset
        )[0]
    elif data_type in (1, 4):
        value = struct.unpack_from("<I", payload, offset)[0]
    elif data_type == 2:
        value = struct.unpack_from("<f", payload, offset)[0]
    elif data_type == 3:
        value = tuple(payload[offset : offset + 4])
    else:
        raise LmtError(f"unsupported TIML keyframe data type: {data_type}")
    frame = struct.unpack_from("<f", payload, offset + 12)[0]
    if not math.isfinite(frame):
        raise LmtError(f"TIML keyframe at 0x{offset:X} has a non-finite frame")
    transition, stored_data_type = struct.unpack_from("<hh", payload, offset + 16)
    if stored_data_type != data_type:
        raise LmtError(
            f"TIML keyframe at 0x{offset:X} stores data type {stored_data_type}, "
            f"but its transform declares {data_type}"
        )
    return TimlKeyframe(offset, value, frame, transition, data_type)


def _parse_embedded_timl(payload: bytes, offset: int) -> tuple[TimlType, ...]:
    if not offset:
        return ()
    require_range(payload, offset, TIML_DATA.size, "embedded TIML data", LmtError)
    type_offset, type_count, _ix0, _ix1, _length, _loop, _control, _label = (
        TIML_DATA.unpack_from(payload, offset)
    )
    if type_count > 10_000:
        raise LmtError(f"implausible TIML type count {type_count} at 0x{offset:X}")
    require_range(
        payload,
        type_offset,
        type_count * TIML_TYPE.size,
        "TIML type list",
        LmtError,
    )

    types: list[TimlType] = []
    for type_index in range(type_count):
        transform_offset, transform_count, timeline_hash, _unknown = (
            TIML_TYPE.unpack_from(payload, type_offset + type_index * TIML_TYPE.size)
        )
        if transform_count > 100_000:
            raise LmtError(
                f"implausible TIML transform count {transform_count} at "
                f"0x{transform_offset:X}"
            )
        require_range(
            payload,
            transform_offset,
            transform_count * TIML_TRANSFORM.size,
            "TIML transform list",
            LmtError,
        )
        transforms: list[TimlTransform] = []
        for transform_index in range(transform_count):
            keyframe_offset, keyframe_count, datatype_hash, data_type = (
                TIML_TRANSFORM.unpack_from(
                    payload,
                    transform_offset + transform_index * TIML_TRANSFORM.size,
                )
            )
            if keyframe_count > 1_000_000:
                raise LmtError(
                    f"implausible TIML keyframe count {keyframe_count} at "
                    f"0x{keyframe_offset:X}"
                )
            require_range(
                payload,
                keyframe_offset,
                keyframe_count * TIML_KEYFRAME_SIZE,
                "TIML keyframes",
                LmtError,
            )
            keyframes = tuple(
                _parse_keyframe(
                    payload,
                    keyframe_offset + index * TIML_KEYFRAME_SIZE,
                    data_type,
                )
                for index in range(keyframe_count)
            )
            transforms.append(TimlTransform(datatype_hash, data_type, keyframes))
        types.append(TimlType(timeline_hash, tuple(transforms)))
    return tuple(types)


def _value_at(keyframes: Sequence[TimlKeyframe], frame: float) -> int | None:
    current: int | None = None
    for keyframe in sorted(keyframes, key=lambda item: item.frame):
        if keyframe.frame > frame + FRAME_TOLERANCE:
            break
        if isinstance(keyframe.value, int):
            current = keyframe.value
    return current


@dataclass(frozen=True)
class LmtFile:
    """Immutable LMT v95 file; construct with from_file() or from_bytes().

    Attributes:
        version: Accepted LMT version, 95.
        entry_count: Total Motion offset-table slots, including empty entries.
        actions: Populated Motion headers in table order, with parsed TIML.
        source_path: Resolved input filename for from_file(), otherwise None.

    Notes:
        The complete original payload is retained, including unmodeled data.
        Factories validate supported headers, pointers, and typed TIML records;
        direct dataclass construction bypasses parsing checks.
    """

    version: int
    entry_count: int
    actions: tuple[LmtAction, ...]
    _payload: bytes = field(repr=False)
    source_path: Path | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> LmtFile:
        """Read and parse a file, retaining its resolved path for output protection.

        Args:
            path: Path or string filename of the input artifact.

        Returns:
            Parsed LmtFile.

        Raises:
            LmtError: The path is not a file or format parsing fails.
            OSError: Reading the file or resolving its path fails.

        Notes:
            Does not modify the input. Editors reject writing to this resolved
            source_path even when output overwrite is enabled.
        """

        source = Path(path)
        if not source.is_file():
            raise LmtError(f"LMT does not exist: {source}")
        parsed = cls.from_bytes(source.read_bytes())
        return cls(
            parsed.version,
            parsed.entry_count,
            parsed.actions,
            parsed._payload,
            source.resolve(),
        )

    @classmethod
    def from_bytes(cls, payload: bytes) -> LmtFile:
        """Parse immutable input bytes without recording a source filename.

        Args:
            payload: Complete file as bytes; bytearray/memoryview are not accepted
                by the underlying parsed-file factory.

        Returns:
            Parsed LmtFile; source_path is None.

        Raises:
            LmtError: The input is not bytes or parsing checks fail.

        Notes:
            Checks LMT v95 header, offset table, populated Motion headers, and typed TIML pointers/keyframes.
            No file I/O occurs; source-path overwrite protection is unavailable.
        """

        if not isinstance(payload, bytes):
            raise LmtError("LMT input must be bytes")
        require_range(payload, 0, LMT_HEADER.size, "LMT header", LmtError)
        magic, version, entry_count, _unknown = LMT_HEADER.unpack_from(payload)
        if magic != b"LMT\0":
            raise LmtError(f"invalid LMT magic: {magic!r}")
        if version != SUPPORTED_LMT_VERSION:
            raise LmtError(
                f"unsupported LMT version: {version}; "
                f"expected {SUPPORTED_LMT_VERSION}"
            )
        offset_table_size = entry_count * 8
        require_range(
            payload,
            LMT_HEADER.size,
            offset_table_size,
            "LMT offset table",
            LmtError,
        )
        offsets = struct.unpack_from(f"<{entry_count}Q", payload, LMT_HEADER.size)

        actions: list[LmtAction] = []
        timl_cache: dict[int, tuple[TimlType, ...]] = {}
        for motion_id, header_offset in enumerate(offsets):
            if not header_offset:
                continue
            require_range(
                payload,
                header_offset,
                LMT_ACTION_HEADER_SIZE,
                f"LMT motion {motion_id} header",
                LmtError,
            )
            fcurve_offset = struct.unpack_from("<Q", payload, header_offset)[0]
            fcurve_count, frame_count = struct.unpack_from(
                "<II", payload, header_offset + 8
            )
            loop_frame = struct.unpack_from("<i", payload, header_offset + 16)[0]
            timl_offset = struct.unpack_from("<Q", payload, header_offset + 88)[0]
            if timl_offset not in timl_cache:
                timl_cache[timl_offset] = _parse_embedded_timl(payload, timl_offset)
            actions.append(
                LmtAction(
                    motion_id=motion_id,
                    header_offset=header_offset,
                    fcurve_offset=fcurve_offset,
                    fcurve_count=fcurve_count,
                    frame_count=frame_count,
                    loop_frame=loop_frame,
                    timl_offset=timl_offset,
                    timl=timl_cache[timl_offset],
                )
            )
        return cls(version, entry_count, tuple(actions), payload)

    def to_bytes(self) -> bytes:
        """Return the complete retained LMT payload byte-for-byte.

        Notes:
            No rebuilding, validation, or disk I/O occurs.
        """

        return self._payload

    def action(self, motion_id: int) -> LmtAction:
        """Look up exactly one populated Motion by its offset-table ID.

        Args:
            motion_id: Zero-based table position, not index into the actions tuple.

        Returns:
            Immutable LmtAction for that Motion.

        Raises:
            LmtError: There is not exactly one populated matching Motion.
        """

        matches = [action for action in self.actions if action.motion_id == motion_id]
        if len(matches) != 1:
            raise LmtError(
                f"expected one populated Motion {motion_id}, found {len(matches)}"
            )
        return matches[0]

    def timl_for_motion(self, motion_id: int) -> tuple[TimlType, ...]:
        """Return the parsed timeline types for a populated Motion.

        Args:
            motion_id: Zero-based Motion offset-table position.

        Returns:
            Tuple of TimlType, empty when the Motion has no TIML.

        Raises:
            LmtError: action() cannot resolve the Motion uniquely.
        """

        return self.action(motion_id).timl

    def triggered_requests(
        self, wwev: WwevFile | None = None
    ) -> tuple[TriggeredRequest, ...]:
        """Expand recognized EventGroup triggers into request and optional WWEV rows.

        Args:
            wwev: Parsed WwevFile to resolve each positive ReqNo, or None.

        Returns:
            Immutable rows sorted by Motion, trigger frame, EventGroup, slot, and
            WWEV record index. Each matching WWEV record gets a separate row; missing
            matches or omitted wwev retain one row with None WWEV fields. Shared TIML
            lists every Motion using it, including the current Motion.

        Raises:
            LmtError: wwev is neither WwevFile nor None.

        Notes:
            Uses EventGroup00-10 and low-eight mTrigger bits A-H. The active request
            is the latest integer assignment at/before the trigger (frame tolerance
            1e-5). Unknown groups, missing transforms, inactive slots, and absent or
            nonpositive assignments produce no row. This is a route report, not a
            full ambiguity/type validator or a lookup into an NBNK.
        """

        if wwev is not None and not isinstance(wwev, WwevFile):
            raise LmtError("wwev must be a WwevFile or None")
        shared_by_offset: dict[int, list[int]] = defaultdict(list)
        for action in self.actions:
            if action.timl_offset:
                shared_by_offset[action.timl_offset].append(action.motion_id)

        records_by_request: dict[int, list[WwevRecord]] = defaultdict(list)
        if wwev is not None:
            for record in wwev.records:
                records_by_request[record.request_no].append(record)

        output: list[TriggeredRequest] = []
        for action in self.actions:
            for typing in action.timl:
                event_group = EVENT_GROUP_HASHES.get(typing.timeline_hash)
                if event_group is None:
                    continue
                transforms = {item.datatype_hash: item for item in typing.transforms}
                trigger = transforms.get(TRIGGER_HASH)
                if trigger is None:
                    continue
                for trigger_keyframe in trigger.keyframes:
                    if (
                        not isinstance(trigger_keyframe.value, int)
                        or not trigger_keyframe.value
                    ):
                        continue
                    trigger_mask = trigger_keyframe.value
                    for slot_index, request_hash in enumerate(REQUEST_SLOT_HASHES):
                        if not trigger_mask & (1 << slot_index):
                            continue
                        request_transform = transforms.get(request_hash)
                        if request_transform is None:
                            continue
                        request_no = _value_at(
                            request_transform.keyframes, trigger_keyframe.frame
                        )
                        if request_no is None or request_no <= 0:
                            continue
                        matching_records: Sequence[WwevRecord | None] = (
                            records_by_request.get(request_no) or (None,)
                        )
                        for record in matching_records:
                            output.append(
                                TriggeredRequest(
                                    motion_id=action.motion_id,
                                    frame_count=action.frame_count,
                                    timl_offset=action.timl_offset,
                                    shared_timl_motions=tuple(
                                        shared_by_offset[action.timl_offset]
                                    ),
                                    event_group=event_group,
                                    trigger_frame=trigger_keyframe.frame,
                                    trigger_mask=trigger_mask,
                                    slot=SLOT_NAMES[slot_index],
                                    request_no=request_no,
                                    wwev_record=record.index if record else None,
                                    wwev_mode=record.mode if record else None,
                                    event_id=record.event_id if record else None,
                                )
                            )
        return tuple(
            sorted(
                output,
                key=lambda item: (
                    item.motion_id,
                    item.trigger_frame,
                    item.event_group,
                    item.slot,
                    item.wwev_record or 0,
                ),
            )
        )


@dataclass(frozen=True)
class LmtRequestEdit:
    """Immutable record of one guarded request-keyframe substitution.

    Attributes:
        motion_id: Zero-based Motion ID.
        event_group: EventGroup00-10 name.
        slot: Normalized uppercase ReqNo slot A-H.
        request_keyframe_frame: Actual matched assignment frame.
        trigger_frames: Sorted unique verified trigger frames after replacement.
        offset: Absolute LMT byte offset of the four-byte assignment value.
        old_request: Previous positive signed-16 request number.
        new_request: Replacement positive signed-16 request number.
        changed_byte_count: Differing bytes within the four-byte value, not always four.
    """

    motion_id: int
    event_group: str
    slot: str
    request_keyframe_frame: float
    trigger_frames: tuple[float, ...]
    offset: int
    old_request: int
    new_request: int
    changed_byte_count: int


@dataclass(frozen=True)
class LmtEditSummary:
    """Immutable current LMT edit report, without running validation.

    Attributes:
        changed_byte_count: Net differing bytes between original and working LMT.
        edits: Declared LmtRequestEdit records in edit order.
    """

    changed_byte_count: int
    edits: tuple[LmtRequestEdit, ...]


class LmtEditor:
    """In-memory editor for guarded substitutions in unshared Motion TIML.

    Attributes:
        original: Immutable source LmtFile; retained for byte preservation and
            source-path checks. New/removed timelines are not supported.
    """

    def __init__(self, lmt: LmtFile):
        """Copy the retained LMT payload into independent working memory.

        Args:
            lmt: Parsed original LmtFile; its source_path is retained for write protection.
        """

        self.original = lmt
        self._payload = bytearray(lmt.to_bytes())
        self._edits: list[LmtRequestEdit] = []

    @classmethod
    def from_file(cls, path: Path | str) -> LmtEditor:
        """Read and parse a file, retaining its resolved path for output protection.

        Args:
            path: Path or string filename of the input artifact.

        Returns:
            New LmtEditor containing a parsed original and independent working state.

        Raises:
            LmtError: The path is not a file or format parsing fails.
            OSError: Reading the file or resolving its path fails.

        Notes:
            Does not modify the input. Editors reject writing to this resolved
            source_path even when output overwrite is enabled.
        """

        return cls(LmtFile.from_file(path))

    @classmethod
    def from_bytes(cls, payload: bytes) -> LmtEditor:
        """Parse immutable input bytes without recording a source filename.

        Args:
            payload: Complete file as bytes; bytearray/memoryview are not accepted
                by the underlying parsed-file factory.

        Returns:
            New LmtEditor containing a parsed original and independent working state; source_path is None.

        Raises:
            LmtError: The input is not bytes or parsing checks fail.

        Notes:
            Checks LMT v95 header, offset table, populated Motion headers, and typed TIML pointers/keyframes.
            No file I/O occurs; source-path overwrite protection is unavailable.
        """

        return cls(LmtFile.from_bytes(payload))

    def replace_request(
        self,
        *,
        motion_id: int,
        event_group: str,
        slot: str,
        request_keyframe_frame: float,
        expected_request: int,
        replacement_request: int,
        expected_trigger_frames: Sequence[float],
    ) -> LmtRequestEdit:
        """Replace one four-byte request assignment guarded by its Motion route.

        Args:
            motion_id: Zero-based populated Motion ID with unshared embedded TIML.
            event_group: Exact EventGroup00-10 name.
            slot: ReqNo slot A-H, normalized to uppercase.
            request_keyframe_frame: Finite assignment frame, matched within 1e-5.
            expected_request: Exact old ReqNo in 1..32767.
            replacement_request: Different replacement ReqNo in 1..32767.
            expected_trigger_frames: Nonempty sequence of finite frames; sorted and
                deduplicated, then compared within 1e-5 to all triggers for the old
                request in this transform. Also checked against the replacement route.

        Returns:
            LmtRequestEdit containing actual assignment/trigger frames, offset, and
            changed-byte count. The working payload and edit list are then updated.

        Raises:
            LmtError: Motion/range/group/slot/frame guards fail; TIML is absent/shared;
                the request transform is not uniquely typed as data type 1; assignment
                selection is ambiguous; edits overlap; or candidate read-back and
                replacement-trigger checks fail.

        Notes:
            Candidate checks run before committing this edit. Other bytes and Motion
            headers remain unchanged. No WWEV lookup, new-request collision check
            across files, or game trigger verification is performed here.
        """

        if (
            not isinstance(motion_id, int)
            or isinstance(motion_id, bool)
            or not 0 <= motion_id < self.original.entry_count
        ):
            raise LmtError(
                f"motion ID must be between 0 and {self.original.entry_count - 1}: "
                f"{motion_id!r}"
            )
        if event_group not in EVENT_GROUP_HASHES.values():
            raise LmtError(f"unknown event group: {event_group}")
        if not isinstance(slot, str):
            raise LmtError(f"slot must be A through H, found {slot!r}")
        slot = slot.upper()
        if slot not in SLOT_NAMES:
            raise LmtError(f"slot must be A through H, found {slot!r}")
        request_keyframe_frame = _check_frame(
            request_keyframe_frame, "request keyframe frame"
        )
        trigger_guard = _normalize_trigger_frames(expected_trigger_frames)
        expected_request = check_positive_i16(
            expected_request, "expected request", LmtError
        )
        replacement_request = check_positive_i16(
            replacement_request, "replacement request", LmtError
        )
        if expected_request == replacement_request:
            raise LmtError("replacement request must differ from the expected request")

        current = LmtFile.from_bytes(bytes(self._payload))
        action = current.action(motion_id)
        if not action.timl_offset:
            raise LmtError(f"Motion {motion_id} has no embedded TIML")
        shared = tuple(
            candidate.motion_id
            for candidate in current.actions
            if candidate.timl_offset == action.timl_offset
        )
        if shared != (motion_id,):
            raise LmtError(
                f"Motion {motion_id} shares TIML 0x{action.timl_offset:X} "
                f"with {list(shared)}"
            )

        timeline_hash = next(
            key for key, value in EVENT_GROUP_HASHES.items() if value == event_group
        )
        slot_index = SLOT_NAMES.index(slot)
        datatype_hash = REQUEST_SLOT_HASHES[slot_index]
        matching_keyframes: list[TimlKeyframe] = []
        matching_transforms: list[tuple[TimlType, TimlTransform]] = []
        for typing in action.timl:
            if typing.timeline_hash != timeline_hash:
                continue
            for transform in typing.transforms:
                if transform.datatype_hash != datatype_hash:
                    continue
                matching_transforms.append((typing, transform))
                if transform.data_type != 1:
                    raise LmtError(
                        f"Motion {motion_id} {event_group} slot {slot} uses "
                        f"unsupported request data type {transform.data_type}"
                    )
                matching_keyframes.extend(
                    keyframe
                    for keyframe in transform.keyframes
                    if keyframe.value == expected_request
                    and _same_frame(keyframe.frame, request_keyframe_frame)
                )
        if len(matching_transforms) != 1:
            raise LmtError(
                f"Motion {motion_id} {event_group} slot {slot}: expected one "
                f"request transform, found {len(matching_transforms)}"
            )
        if len(matching_keyframes) != 1:
            raise LmtError(
                f"Motion {motion_id} {event_group} slot {slot}: expected one ReqNo "
                f"{expected_request} keyframe at frame {request_keyframe_frame:g}, "
                f"found {len(matching_keyframes)}"
            )
        typing, request_transform = matching_transforms[0]
        keyframe = matching_keyframes[0]
        edit_end = keyframe.offset + 4
        for prior in self._edits:
            if keyframe.offset < prior.offset + 4 and prior.offset < edit_end:
                raise LmtError(
                    f"request edit at 0x{keyframe.offset:X} overlaps an earlier edit"
                )
        if struct.unpack_from("<I", self._payload, keyframe.offset)[0] != expected_request:
            raise LmtError(f"request guard failed at 0x{keyframe.offset:X}")

        trigger_frames = self._trigger_frames_for_request(
            typing, request_transform, slot_index, expected_request
        )
        if len(trigger_frames) != len(trigger_guard) or any(
            not _same_frame(actual, expected)
            for actual, expected in zip(trigger_frames, trigger_guard)
        ):
            raise LmtError(
                f"Motion {motion_id} {event_group} slot {slot} expected trigger "
                f"frames {trigger_guard} but found {trigger_frames}"
            )

        candidate_payload = bytearray(self._payload)
        struct.pack_into("<I", candidate_payload, keyframe.offset, replacement_request)
        candidate = LmtFile.from_bytes(bytes(candidate_payload))
        if tuple(item.header_identity for item in candidate.actions) != tuple(
            item.header_identity for item in current.actions
        ):
            raise LmtError(
                "request substitution unexpectedly changed an LMT action header"
            )
        changed_byte_count = sum(
            before != after
            for before, after in zip(
                self._payload[keyframe.offset:edit_end],
                candidate_payload[keyframe.offset:edit_end],
            )
        )
        if not changed_byte_count:
            raise LmtError("request substitution did not change the LMT")
        changed_rows = [
            row
            for row in candidate.triggered_requests()
            if row.motion_id == motion_id
            and row.event_group == event_group
            and row.slot == slot
            and row.request_no == replacement_request
        ]
        changed_trigger_frames = tuple(
            sorted({row.trigger_frame for row in changed_rows})
        )
        if len(changed_trigger_frames) != len(trigger_guard) or any(
            not _same_frame(actual, expected)
            for actual, expected in zip(changed_trigger_frames, trigger_guard)
        ):
            raise LmtError(
                "replacement request is not reached at the guarded trigger frames"
            )

        edit = LmtRequestEdit(
            motion_id=motion_id,
            event_group=event_group,
            slot=slot,
            request_keyframe_frame=keyframe.frame,
            trigger_frames=changed_trigger_frames,
            offset=keyframe.offset,
            old_request=expected_request,
            new_request=replacement_request,
            changed_byte_count=changed_byte_count,
        )
        self._payload[:] = candidate_payload
        self._edits.append(edit)
        return edit

    @staticmethod
    def _trigger_frames_for_request(
        typing: TimlType,
        request_transform: TimlTransform,
        slot_index: int,
        request_no: int,
    ) -> tuple[float, ...]:
        frames: set[float] = set()
        for trigger in (
            transform
            for transform in typing.transforms
            if transform.datatype_hash == TRIGGER_HASH
        ):
            for keyframe in trigger.keyframes:
                if (
                    isinstance(keyframe.value, int)
                    and keyframe.value & (1 << slot_index)
                    and _value_at(request_transform.keyframes, keyframe.frame)
                    == request_no
                ):
                    frames.add(keyframe.frame)
        return tuple(sorted(frames))

    def build(self) -> bytes:
        """Return immutable current LMT bytes without reparsing or writing a file."""

        return bytes(self._payload)

    def validate(self) -> LmtFile:
        """Reparse and verify working LMT bytes against the original and declared edits.

        Returns:
            Parsed LmtFile of the current payload, with no source_path.

        Raises:
            LmtError: Reparse fails, size/header metadata changes, undeclared bytes
                differ, or an edited request value/trigger-frame set fails read-back.

        Notes:
            Does not mutate the editor, write a file, or resolve requests through WWEV.
        """

        payload = self.build()
        if len(payload) != len(self.original.to_bytes()):
            raise LmtError("read-back verification changed LMT file size")
        rebuilt = LmtFile.from_bytes(payload)
        if (
            rebuilt.version != self.original.version
            or rebuilt.entry_count != self.original.entry_count
            or tuple(item.header_identity for item in rebuilt.actions)
            != tuple(item.header_identity for item in self.original.actions)
        ):
            raise LmtError("read-back verification changed LMT action metadata")

        allowed_offsets = {
            offset
            for edit in self._edits
            for offset in range(edit.offset, edit.offset + 4)
        }
        unexpected = [
            offset
            for offset, (before, after) in enumerate(
                zip(self.original.to_bytes(), payload)
            )
            if before != after and offset not in allowed_offsets
        ]
        if unexpected:
            raise LmtError(
                "read-back verification found undeclared LMT byte changes at "
                + ", ".join(f"0x{offset:X}" for offset in unexpected[:8])
            )
        for edit in self._edits:
            if struct.unpack_from("<I", payload, edit.offset)[0] != edit.new_request:
                raise LmtError(
                    f"read-back verification failed at request offset 0x{edit.offset:X}"
                )
            rows = [
                row
                for row in rebuilt.triggered_requests()
                if row.motion_id == edit.motion_id
                and row.event_group == edit.event_group
                and row.slot == edit.slot
                and row.request_no == edit.new_request
            ]
            frames = tuple(sorted({row.trigger_frame for row in rows}))
            if len(frames) != len(edit.trigger_frames) or any(
                not _same_frame(actual, expected)
                for actual, expected in zip(frames, edit.trigger_frames)
            ):
                raise LmtError(
                    f"read-back verification changed trigger frames for Motion "
                    f"{edit.motion_id} {edit.event_group} slot {edit.slot}"
                )
        return rebuilt

    @property
    def summary(self) -> LmtEditSummary:
        """Return net byte differences and declared edits as an immutable LmtEditSummary.

        Notes:
            This compares current bytes to the original without running validate().
        """

        changed = sum(
            before != after
            for before, after in zip(self.original.to_bytes(), self.build())
        )
        return LmtEditSummary(changed_byte_count=changed, edits=tuple(self._edits))

    def write_atomic(self, output: Path | str, *, overwrite: bool = False) -> Path:
        """Validate and write one artifact using a temporary file beside the output.

        Args:
            output: Path or string filename; missing parent directories are created.
            overwrite: Permit replacing an existing output when True. Never permits
                replacing the original's recorded resolved source_path.

        Returns:
            Path of the written output, retaining the caller's relative/absolute form.

        Raises:
            LmtError: Validation fails, output resolves to the recorded input, or
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
            kind="LMT",
            error_type=LmtError,
        )
