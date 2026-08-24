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
