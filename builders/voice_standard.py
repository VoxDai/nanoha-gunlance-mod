"""Canonical custom-voice Sound template and immutable provenance guards."""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct

from tools import soundbank_editor

from .base import ReferenceInput


STANDARD_DONOR_BANK_PATH = Path("original/nbnk/wp_cmn_epvsp.nbnk")
STANDARD_DONOR_BANK_SHA256 = (
    "76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8"
)
STANDARD_DONOR_SOUND_ID = 890_667_980
STANDARD_DONOR_MEDIA_ID = 838_569_492
STANDARD_DONOR_SOUND_BODY_SHA256 = (
    "b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e"
)

STANDARD_ACTOR_BANK_PATH = Path("original/nbnk/pl_act_vo_event.nbnk")
STANDARD_ACTOR_BANK_SHA256 = (
    "4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582"
)
STANDARD_VOICE_PARENT_ID = 209_038_110

STANDARD_SOUND_BODY_LENGTH = 46
STANDARD_SOUND_MEDIA_OFFSET = 0x09
STANDARD_SOUND_PARENT_OFFSET = 0x19
STANDARD_SOUND_POSITIONING_VECTOR_OFFSET = 0x20
STANDARD_SOUND_POSITIONING_VECTOR = 0xC1
STANDARD_SOUND_BODY_SHA256 = (
    "54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64"
)

STANDARD_DONOR_SOUND_BODY = bytes.fromhex(
    "cc8316350100040000148efb31d65e0000000000000000000071cc4812000000"
    "c000000100000000000000000000"
)
STANDARD_SOUND_BODY = bytes.fromhex(
    "cc8316350100040000148efb31d65e000000000000000000001eab750c000000"
    "c100000100000000000000000000"
)

STANDARD_VOICE_REFERENCE_INPUTS = (
    ReferenceInput(STANDARD_DONOR_BANK_PATH, STANDARD_DONOR_BANK_SHA256),
    ReferenceInput(STANDARD_ACTOR_BANK_PATH, STANDARD_ACTOR_BANK_SHA256),
)


def _u32(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFFFFFF:
        raise soundbank_editor.SoundBankError(
            f"{label} must be an unsigned 32-bit integer: {value!r}"
        )
    return value


def validate_standard_template() -> None:
    """Reject accidental changes to the reviewed donor and standardized body."""

    checks = (
        (
            STANDARD_DONOR_SOUND_BODY,
            STANDARD_DONOR_SOUND_BODY_SHA256,
            "standard donor Sound body",
        ),
        (STANDARD_SOUND_BODY, STANDARD_SOUND_BODY_SHA256, "standard Sound body"),
    )
    for body, expected_hash, label in checks:
        if len(body) != STANDARD_SOUND_BODY_LENGTH:
            raise soundbank_editor.SoundBankError(
                f"{label} must be {STANDARD_SOUND_BODY_LENGTH} bytes"
            )
        actual_hash = hashlib.sha256(body).hexdigest()
        if actual_hash != expected_hash:
            raise soundbank_editor.SoundBankError(
                f"{label} SHA-256 expected {expected_hash} but found {actual_hash}"
            )
    if (
        struct.unpack_from("<I", STANDARD_SOUND_BODY, 0)[0]
        != STANDARD_DONOR_SOUND_ID
        or struct.unpack_from("<I", STANDARD_SOUND_BODY, STANDARD_SOUND_MEDIA_OFFSET)[0]
        != STANDARD_DONOR_MEDIA_ID
        or struct.unpack_from("<I", STANDARD_SOUND_BODY, STANDARD_SOUND_PARENT_OFFSET)[0]
        != STANDARD_VOICE_PARENT_ID
        or STANDARD_SOUND_BODY[STANDARD_SOUND_POSITIONING_VECTOR_OFFSET]
        != STANDARD_SOUND_POSITIONING_VECTOR
    ):
        raise soundbank_editor.SoundBankError(
            "standard Sound body no longer contains the reviewed donor IDs, parent, and C1 positioning"
        )


def standard_voice_sound_body(
    sound_id: int,
    media_id: int,
    *,
    direct_parent_id: int = STANDARD_VOICE_PARENT_ID,
) -> bytes:
    """Return the exact 46-byte standard body with only IDs substituted."""

    validate_standard_template()
    body = bytearray(STANDARD_SOUND_BODY)
    struct.pack_into("<I", body, 0, _u32(sound_id, "Sound ID"))
    struct.pack_into(
        "<I", body, STANDARD_SOUND_MEDIA_OFFSET, _u32(media_id, "Media ID")
    )
    struct.pack_into(
        "<I",
        body,
        STANDARD_SOUND_PARENT_OFFSET,
        _u32(direct_parent_id, "DirectParentID"),
    )
    return bytes(body)


def insert_standard_voice_sound(
    editor: soundbank_editor.HircEditor,
    sound_id: int,
    media_id: int,
    *,
    direct_parent_id: int = STANDARD_VOICE_PARENT_ID,
    label: str = "insert standard custom-voice Sound",
) -> None:
    """Insert one canonical custom-voice Sound into a v120 HIRC payload."""

    body = standard_voice_sound_body(
        sound_id,
        media_id,
        direct_parent_id=direct_parent_id,
    )
    editor.insert_object(
        soundbank_editor.HIRC_SOUND,
        sound_id,
        body[4:],
        label=label,
    )
