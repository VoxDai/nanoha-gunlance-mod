"""Synthetic LMT/TIML and WWEV fixtures for format editor tests."""

import struct

from tools.soundbank_editor import lmt as lmt_format
from tools.soundbank_editor import wwev as wwev_format


def make_test_lmt(*, duplicate_action: bool = False) -> bytes:
    entry_count = 2 if duplicate_action else 1
    action_offsets = (32, 128) if duplicate_action else (32,)
    timl_offset = 224 if duplicate_action else 128
    type_offset = timl_offset + lmt_format.TIML_DATA.size
    transform_offset = type_offset + lmt_format.TIML_TYPE.size
    keyframe_offset = (
        transform_offset + 3 * lmt_format.TIML_TRANSFORM.size
    )
    payload = bytearray(
        keyframe_offset + 3 * lmt_format.TIML_KEYFRAME_SIZE
    )

    lmt_format.LMT_HEADER.pack_into(
        payload,
        0,
        b"LMT\0",
        lmt_format.SUPPORTED_LMT_VERSION,
        entry_count,
        bytes((0, 8, 2, 24, 0, 0, 0, 0)),
    )
    struct.pack_into(f"<{entry_count}Q", payload, 16, *action_offsets)
    for motion_id, action_offset in enumerate(action_offsets):
        struct.pack_into("<Q", payload, action_offset, 0)
        struct.pack_into("<II", payload, action_offset + 8, 0, 60 + motion_id)
        struct.pack_into("<i", payload, action_offset + 16, -1)
        struct.pack_into("<Q", payload, action_offset + 88, timl_offset)

    lmt_format.TIML_DATA.pack_into(
        payload, timl_offset, type_offset, 1, 0, 0, 60.0, 0.0, 0, 0
    )
    lmt_format.TIML_TYPE.pack_into(
        payload,
        type_offset,
        transform_offset,
        3,
        816_017_303,
        0,
    )
    transforms = (
        (lmt_format.REQUEST_SLOT_HASHES[0], 6485, 0.0),
        (lmt_format.REQUEST_SLOT_HASHES[1], 6489, 0.0),
        (lmt_format.TRIGGER_HASH, 3, 12.0),
    )
    for index, (datatype_hash, value, frame) in enumerate(transforms):
        current_keyframe = keyframe_offset + index * lmt_format.TIML_KEYFRAME_SIZE
        lmt_format.TIML_TRANSFORM.pack_into(
            payload,
            transform_offset + index * lmt_format.TIML_TRANSFORM.size,
            current_keyframe,
            1,
            datatype_hash,
            1,
        )
        struct.pack_into(
            "<III f hh", payload, current_keyframe, value, 0, 0, frame, 0, 1
        )
    return bytes(payload)


def make_test_wwev() -> bytes:
    payload = bytearray(
        wwev_format.WWEV_HEADER.pack(
            b"WWEV", wwev_format.SUPPORTED_WWEV_VERSION, 2, 0x11223344
        )
    )
    for dependency in ("motion", "weapon", "player", "common"):
        payload += dependency.encode("utf-8") + b"\0"
    records = (
        (6485, 100, 1_352_901_803, 0x01020304, bytes((0x11,)) * 116, ""),
        (6489, 2, 2_467_230_203, 0x05060708, bytes((0x22,)) * 116, "wp07"),
    )
    for request_no, mode, event_id, command_hash, unknown, wwpc in records:
        payload += wwev_format.WWEV_RECORD_FIXED.pack(
            request_no, mode, event_id, command_hash, unknown
        )
        payload += wwpc.encode("utf-8") + b"\0"
    return bytes(payload)
