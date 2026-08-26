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
STANDARD_DONOR_BANK_ID = 1_149_256_632
STANDARD_DONOR_SOUND_ID = 890_667_980
STANDARD_DONOR_MEDIA_ID = 838_569_492
STANDARD_DONOR_SOUND_BODY_SHA256 = (
    "b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e"
)

STANDARD_ACTOR_BANK_PATH = Path("original/nbnk/pl_act_vo_event.nbnk")
STANDARD_ACTOR_BANK_SHA256 = (
    "4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582"
)
STANDARD_ACTOR_BANK_ID = 3_755_575_407
STANDARD_VOICE_PARENT_ID = 209_038_110
STANDARD_VOICE_PARENT_BODY_SHA256 = (
    "3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80"
)

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


def validate_standard_reference_binaries(
    donor_bank_path: Path,
    actor_bank_path: Path,
) -> None:
    """Validate semantic facts behind the two byte-exact reference inputs."""

    validate_standard_template()
    donor = soundbank_editor.SoundBank.from_file(donor_bank_path)
    if donor.bank_id != STANDARD_DONOR_BANK_ID:
        raise soundbank_editor.SoundBankError(
            f"standard donor Bank ID expected {STANDARD_DONOR_BANK_ID} but found {donor.bank_id}"
        )
    donor_hirc = soundbank_editor.HircEditor(donor.hirc_payload, version=donor.version)
    donor_body = donor_hirc.object_body(
        soundbank_editor.HIRC_SOUND, STANDARD_DONOR_SOUND_ID
    )
    if donor_body != STANDARD_DONOR_SOUND_BODY:
        raise soundbank_editor.SoundBankError(
            "standard donor Sound body differs from the reviewed 46-byte source"
        )

    data = actor_bank_path.read_bytes()
    chunks: dict[bytes, bytes] = {}
    position = 0
    while position < len(data):
        if position + 8 > len(data):
            raise soundbank_editor.SoundBankError("actor Bank has a truncated chunk header")
        tag = data[position : position + 4]
        size = struct.unpack_from("<I", data, position + 4)[0]
        end = position + 8 + size
        if end > len(data):
            raise soundbank_editor.SoundBankError("actor Bank has an out-of-bounds chunk")
        if tag in chunks:
            raise soundbank_editor.SoundBankError(f"actor Bank repeats chunk {tag!r}")
        chunks[tag] = data[position + 8 : end]
        position = end
    try:
        bkhd = chunks[b"BKHD"]
        hirc_payload = chunks[b"HIRC"]
    except KeyError as error:
        raise soundbank_editor.SoundBankError("actor Bank is missing BKHD or HIRC") from error
    if len(bkhd) < 8:
        raise soundbank_editor.SoundBankError("actor Bank BKHD is too short")
    version, bank_id = struct.unpack_from("<II", bkhd, 0)
    if version != 120 or bank_id != STANDARD_ACTOR_BANK_ID:
        raise soundbank_editor.SoundBankError(
            f"actor Bank expected v120 / ID {STANDARD_ACTOR_BANK_ID}, found v{version} / ID {bank_id}"
        )
    actor_hirc = soundbank_editor.HircEditor(hirc_payload, version=version)
    actor_body = actor_hirc.object_body(0x07, STANDARD_VOICE_PARENT_ID)
    actual_hash = hashlib.sha256(actor_body).hexdigest()
    if actual_hash != STANDARD_VOICE_PARENT_BODY_SHA256:
        raise soundbank_editor.SoundBankError(
            f"Actor-Mixer {STANDARD_VOICE_PARENT_ID} body SHA-256 expected "
            f"{STANDARD_VOICE_PARENT_BODY_SHA256} but found {actual_hash}"
        )
