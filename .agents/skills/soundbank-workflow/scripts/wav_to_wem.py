#!/usr/bin/env python3
"""Convert audio to the Wwise PCM WEM layout known to work in MHW."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile


SAMPLE_RATE = 48_000
CHANNELS = 2
BITS_PER_SAMPLE = 16
BLOCK_ALIGN = CHANNELS * (BITS_PER_SAMPLE // 8)
WWISE_CHANNEL_EXTRA = bytes.fromhex("000002310000")


class ConversionError(Exception):
    """A user-actionable conversion failure."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert audio to an MHW-compatible 48 kHz stereo Wwise PCM WEM."
    )
    parser.add_argument("input", type=Path, help="Input audio (usually WAV)")
    parser.add_argument("output", type=Path, help="Output .wem file")
    parser.add_argument("--force", action="store_true", help="Allow overwriting an existing output")
    return parser


def ensure_output(input_path: Path, output_path: Path, force: bool) -> None:
    if not input_path.is_file():
        raise ConversionError(f"Input file does not exist: {input_path}")
    if input_path.resolve() == output_path.resolve():
        raise ConversionError("Input and output must be different files")
    if output_path.exists() and not force:
        raise ConversionError(
            f"Output already exists; add --force after confirming overwrite: {output_path}"
        )
    if output_path.suffix.lower() != ".wem":
        raise ConversionError("Output file must use the .wem extension")


def convert_to_raw(input_path: Path, raw_path: Path) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ConversionError("ffmpeg was not found; install it and ensure it is on PATH")
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-sn",
        "-dn",
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        str(CHANNELS),
        "-c:a",
        "pcm_s16le",
        "-f",
        "s16le",
        str(raw_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "ffmpeg did not provide an error message"
        raise ConversionError(f"ffmpeg conversion failed: {detail}")
    pcm = raw_path.read_bytes() if raw_path.is_file() else b""
    if not pcm:
        raise ConversionError("Conversion produced no data; the input may not contain an audio track")
    if len(pcm) % BLOCK_ALIGN:
        raise ConversionError("PCM data size is not a whole number of stereo 16-bit frames")
    return pcm


def build_wem(pcm: bytes) -> bytes:
    byte_rate = SAMPLE_RATE * BLOCK_ALIGN
    fmt = struct.pack(
        "<HHIIHHH",
        0xFFFE,
        CHANNELS,
        SAMPLE_RATE,
        byte_rate,
        BLOCK_ALIGN,
        BITS_PER_SAMPLE,
        len(WWISE_CHANNEL_EXTRA),
    ) + WWISE_CHANNEL_EXTRA
    body = b"WAVE"
    body += b"fmt " + struct.pack("<I", len(fmt)) + fmt
    body += b"JUNK" + struct.pack("<I", 4) + b"\0" * 4
    body += b"data" + struct.pack("<I", len(pcm)) + pcm
    return b"RIFF" + struct.pack("<I", len(body)) + body


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ensure_output(args.input, args.output, args.force)
        with tempfile.TemporaryDirectory(prefix="mhw-wem-") as directory:
            pcm = convert_to_raw(args.input, Path(directory) / "audio.pcm")
        wem = build_wem(pcm)
        atomic_write(args.output, wem)
        frames = len(pcm) // BLOCK_ALIGN
        duration = frames / SAMPLE_RATE
        print(f"Wrote {args.output}")
        print(
            f"Wwise PCM: {SAMPLE_RATE} Hz, {CHANNELS} channels, "
            f"{BITS_PER_SAMPLE}-bit, {duration:.3f} s, {len(wem)} bytes"
        )
        return 0
    except (ConversionError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
