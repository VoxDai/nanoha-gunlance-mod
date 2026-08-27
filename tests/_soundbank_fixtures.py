"""Shared fixtures for SoundBank and HIRC unit tests."""

from pathlib import Path
import struct


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOUNDBANK_ROOT = PROJECT_ROOT / "original" / "nbnk"


def make_hirc(*records: tuple[int, int, bytes]) -> bytes:
    payload = bytearray(struct.pack("<I", len(records)))
    for object_type, object_id, body_tail in records:
        body = struct.pack("<I", object_id) + body_tail
        payload += struct.pack("<BI", object_type, len(body)) + body
    return bytes(payload)


def make_random_container_tail(*playlist: tuple[int, int]) -> bytes:
    payload = bytearray(struct.pack("<I", len(playlist)))
    payload += struct.pack(
        f"<{len(playlist)}I", *(child_id for child_id, _ in playlist)
    )
    payload += struct.pack("<H", len(playlist))
    for child_id, weight in playlist:
        payload += struct.pack("<Ii", child_id, weight)
    return bytes(payload)


def make_test_wem(*, frames: int = 4) -> bytes:
    """Return a small valid mono Wwise PCM WEM for synthetic tests."""

    pcm = bytes(frames * 2)
    channel_extra = bytes.fromhex("000001410000")
    fmt = struct.pack(
        "<HHIIHHH",
        0xFFFE,
        1,
        48_000,
        96_000,
        2,
        16,
        len(channel_extra),
    ) + channel_extra
    body = b"WAVE"
    body += b"fmt " + struct.pack("<I", len(fmt)) + fmt
    body += b"JUNK" + struct.pack("<I", 4) + bytes(4)
    body += b"data" + struct.pack("<I", len(pcm)) + pcm
    return b"RIFF" + struct.pack("<I", len(body)) + body


def make_test_soundbank(
    *,
    bank_id: int = 123_456_789,
    media_id: int = 987_654_321,
    version: int = 120,
) -> bytes:
    """Return a minimal editable SoundBank with one embedded media entry."""

    wem = make_test_wem()

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return tag + struct.pack("<I", len(payload)) + payload

    return b"".join(
        (
            chunk(b"BKHD", struct.pack("<II", version, bank_id)),
            chunk(b"DIDX", struct.pack("<III", media_id, 0, len(wem))),
            chunk(b"DATA", wem),
            chunk(b"HIRC", struct.pack("<I", 0)),
        )
    )
