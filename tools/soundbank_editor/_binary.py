"""Shared guarded binary and atomic I/O helpers."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import TypeVar

from .errors import EditorError


ErrorT = TypeVar("ErrorT", bound=EditorError)
Payload = bytes | bytearray | memoryview | Path | str


def coerce_payload(
    value: Payload,
    label: str,
    error_type: type[ErrorT],
) -> bytes:
    if isinstance(value, (Path, str)):
        path = Path(value)
        if not path.is_file():
            raise error_type(f"{label} does not exist: {path}")
        return path.read_bytes()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    raise error_type(f"{label} must be bytes or a filesystem path")


def require_range(
    payload: bytes,
    offset: int,
    size: int,
    label: str,
    error_type: type[ErrorT],
) -> None:
    if offset < 0 or size < 0 or offset + size > len(payload):
        raise error_type(
            f"{label} range 0x{offset:X}+0x{size:X} exceeds file size "
            f"0x{len(payload):X}"
        )


def read_cstring(
    payload: bytes,
    offset: int,
    label: str,
    error_type: type[ErrorT],
) -> tuple[str, int]:
    if offset < 0 or offset >= len(payload):
        raise error_type(f"{label} starts beyond end of file")
    end = payload.find(b"\0", offset)
    if end < 0:
        raise error_type(f"{label} is not NUL-terminated")
    try:
        value = payload[offset:end].decode("utf-8")
    except UnicodeDecodeError as error:
        raise error_type(f"{label} is not valid UTF-8: {error}") from error
    return value, end + 1


def check_unsigned(
    value: int,
    bits: int,
    label: str,
    error_type: type[ErrorT],
) -> int:
    maximum = (1 << bits) - 1
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= maximum
    ):
        description = "byte" if bits == 8 else f"{bits}-bit integer"
        raise error_type(f"{label} must be an unsigned {description}: {value!r}")
    return value


def check_positive_i16(value: int, label: str, error_type: type[ErrorT]) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 1 <= value <= 0x7FFF
    ):
        raise error_type(
            f"{label} must be a positive signed 16-bit integer: {value!r}"
        )
    return value


def count_changed_bytes(before: bytes, after: bytes) -> int:
    return sum(left != right for left, right in zip(before, after)) + abs(
        len(before) - len(after)
    )


def write_atomic(
    output: Path | str,
    payload: bytes,
    *,
    source_path: Path | None,
    overwrite: bool,
    kind: str,
    error_type: type[ErrorT],
) -> Path:
    """Atomically write a verified payload without silently replacing inputs."""

    target = Path(output)
    if source_path is not None and target.resolve() == source_path.resolve():
        raise error_type(f"overwriting the input {kind} in place is not allowed")
    if target.exists() and not overwrite:
        raise error_type(f"output already exists: {target}")
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
