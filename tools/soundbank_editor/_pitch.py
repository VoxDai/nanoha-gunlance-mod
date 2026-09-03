"""Wwise v120 node property tables, preserving unmodeled values as bytes."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from ._binary import require_range
from .errors import SoundBankError

_PITCH_ID = 0x02


@dataclass(frozen=True)
class HircPitchSettings:
    """Local pitch contributions in cents; None means an absent property."""

    base_cents: float | None
    random_range_cents: tuple[float, float] | None


def _pack_cents(value: float, label: str) -> bytes:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SoundBankError(f"{label}: cents must be a finite float32 number")
    try:
        packed = struct.pack("<f", value)
    except (OverflowError, struct.error) as error:
        raise SoundBankError(f"{label}: cents must fit finite float32") from error
    if not math.isfinite(struct.unpack("<f", packed)[0]):
        raise SoundBankError(f"{label}: cents must be a finite float32 number")
    return packed


def _pack_pitch_range(value: tuple[float, float], label: str) -> bytes:
    if not isinstance(value, tuple) or len(value) != 2:
        raise SoundBankError(f"{label}: random range must be a (min, max) tuple")
    low = _pack_cents(value[0], f"{label} min")
    high = _pack_cents(value[1], f"{label} max")
    if value[0] > value[1]:
        raise SoundBankError(f"{label}: random range requires min <= max")
    return low + high


def _encode_pitch_settings(
        value: HircPitchSettings, label: str
) -> tuple[bytes | None, bytes | None]:
    if not isinstance(value, HircPitchSettings):
        raise SoundBankError(f"{label}: expected HircPitchSettings")
    return (
        None if value.base_cents is None else _pack_cents(value.base_cents, label),
        None
        if value.random_range_cents is None
        else _pack_pitch_range(value.random_range_cents, label),
    )


class _Reader:
    def __init__(self, body: bytes, label: str):
        self.body = body
        self.label = label
        self.offset = 0

    def take(self, size: int, field: str) -> bytes:
        require_range(
            self.body, self.offset, size, f"{self.label}: {field}", SoundBankError
        )
        value = self.body[self.offset: self.offset + size]
        self.offset += size
        return value


@dataclass(frozen=True)
class _PropertyBundle:
    start: int
    end: int
    ids: tuple[int, ...]
    values: tuple[bytes, ...]
    value_size: int

    @property
    def pitch(self) -> bytes | None:
        if _PITCH_ID not in self.ids:
            return None
        return self.values[self.ids.index(_PITCH_ID)]

    @property
    def pitch_offset(self) -> int:
        return self.start + 1 + len(self.ids) + self.ids.index(_PITCH_ID) * self.value_size

    def with_pitch(self, value: bytes | None, label: str) -> bytes:
        items = dict(zip(self.ids, self.values))
        if value is not None:
            if _PITCH_ID not in items and len(items) == 0xFF:
                raise SoundBankError(f"{label}: property count would exceed 255")
            items[_PITCH_ID] = value
        ids = sorted(items)
        return bytes([len(ids), *ids]) + b"".join(items[key] for key in ids)


def _read_bundle(reader: _Reader, value_size: int, name: str) -> _PropertyBundle:
    start = reader.offset
    count = reader.take(1, f"{name} count")[0]
    ids = tuple(reader.take(count, f"{name} IDs"))
    if any(left >= right for left, right in zip(ids, ids[1:])):
        raise SoundBankError(f"{reader.label}: {name} has duplicate or unordered IDs")
    values = tuple(reader.take(value_size, f"{name} value") for _ in ids)
    return _PropertyBundle(start, reader.offset, ids, values, value_size)


@dataclass(frozen=True)
class _PitchLayout:
    base: _PropertyBundle
    random: _PropertyBundle

    @property
    def encoded(self) -> tuple[bytes | None, bytes | None]:
        return self.base.pitch, self.random.pitch

    def settings(self, label: str) -> HircPitchSettings:
        base, random = self.encoded
        result = HircPitchSettings(
            None if base is None else struct.unpack("<f", base)[0],
            None if random is None else struct.unpack("<ff", random),
        )
        # Reject malformed Pitch values without interpreting other properties.
        _encode_pitch_settings(result, label)
        return result

    def replace(
            self, body: bytes, base: bytes | None, random: bytes | None, label: str
    ) -> bytes:
        return (
                body[: self.base.start]
                + self.base.with_pitch(base, label)
                + self.random.with_pitch(random, label)
                + body[self.random.end:]
        )


def _parse_pitch_layout(body: bytes, object_type: int, label: str) -> _PitchLayout:
    # Sound, Random/Sequence, Switch and Actor-Mixer all use NodeBaseParams.
    if isinstance(object_type, bool) or object_type not in (0x02, 0x05, 0x06, 0x07):
        raise SoundBankError(f"{label}: unsupported Pitch object type {object_type!r}")
    reader = _Reader(body, label)
    reader.take(4, "object ID")
    if object_type == 0x02:
        # v120 AkBankSourceData: plugin, stream type, source ID, size and bits.
        source = reader.take(14, "Sound source")
        plugin_id = struct.unpack_from("<I", source)[0]
        if (plugin_id & 0x0F) in (2, 5):
            size = struct.unpack("<I", reader.take(4, "source parameter size"))[0]
            reader.take(size, "source parameters")

    # v120 NodeInitialFxParams: override, count, optional bypass and FX records.
    fx_count = reader.take(2, "FX header")[1]
    if fx_count:
        reader.take(1 + 7 * fx_count, "FX bypass and records")
    # Attachment override, output bus, parent ID and priority/MIDI bits.
    reader.take(10, "node routing and flags")
    base = _read_bundle(reader, 4, "base properties")
    random = _read_bundle(reader, 8, "random properties")
    return _PitchLayout(base, random)
