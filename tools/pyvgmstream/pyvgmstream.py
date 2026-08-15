#!/usr/bin/env python3
"""Inspect and decode game audio with the installed pyvgmstream package."""

from __future__ import annotations

import argparse
import ctypes
import importlib
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType


class CLIError(Exception):
    """A user-actionable pyvgmstream CLI failure."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect, decode, or batch-convert game audio with pyvgmstream."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Print stream metadata")
    inspect_parser.add_argument("input", type=Path, help="Input audio file")

    decode_parser = subparsers.add_parser("decode", help="Decode one file to WAV")
    decode_parser.add_argument("input", type=Path, help="Input audio file")
    decode_parser.add_argument("output", type=Path, help="Output .wav file")
    decode_parser.add_argument(
        "--force", action="store_true", help="Allow overwriting an existing output"
    )

    batch_parser = subparsers.add_parser(
        "batch", help="Recursively decode .wem files to WAV"
    )
    batch_parser.add_argument("input", type=Path, help="Input directory")
    batch_parser.add_argument("output", type=Path, help="Output directory")
    batch_parser.add_argument(
        "--workers", type=int, default=1, help="Worker processes (default: 1)"
    )
    return parser


def load_macos_vorbis_runtime() -> None:
    """Expose Conda's Vorbisfile symbols to the extension on macOS."""
    if sys.platform != "darwin":
        return
    library = Path(sys.prefix) / "lib" / "libvorbisfile.3.dylib"
    if library.is_file():
        ctypes.CDLL(str(library), mode=ctypes.RTLD_GLOBAL)


_VORBIS_RUNTIME_ERROR: OSError | None = None
try:
    # multiprocessing spawn imports this module in each worker before it
    # unpickles pyvgmstream tasks, so the native extension can resolve Vorbis.
    load_macos_vorbis_runtime()
except OSError as error:
    _VORBIS_RUNTIME_ERROR = error


def _resolved_sys_path(entry: str) -> Path:
    return Path(entry or os.curdir).resolve()


def load_backend() -> ModuleType:
    """Import the installed package without importing this same-named script."""
    if _VORBIS_RUNTIME_ERROR is not None:
        raise CLIError(f"Could not load the macOS Vorbis runtime: {_VORBIS_RUNTIME_ERROR}")
    script_directory = Path(__file__).resolve().parent
    # Keep this directory excluded for the rest of the process. On platforms
    # using multiprocessing spawn, transcode workers inherit sys.path and must
    # also resolve ``pyvgmstream`` to the installed package rather than this CLI.
    sys.path[:] = [
        entry for entry in sys.path if _resolved_sys_path(entry) != script_directory
    ]
    try:
        backend = importlib.import_module("pyvgmstream")
    except (ImportError, OSError) as error:
        raise CLIError(f"Could not load pyvgmstream: {error}") from error

    backend_path = getattr(backend, "__file__", None)
    if backend_path and Path(backend_path).resolve() == Path(__file__).resolve():
        raise CLIError("Imported the CLI script instead of the installed pyvgmstream package")
    return backend


def ensure_input_file(path: Path) -> None:
    if not path.is_file():
        raise CLIError(f"Input file does not exist: {path}")


def inspect_audio(path: Path) -> None:
    ensure_input_file(path)
    backend = load_backend()
    try:
        info = backend.probe(str(path))
    except Exception as error:
        raise CLIError(f"pyvgmstream could not inspect {path}: {error}") from error

    print(f"Path: {path}")
    for label, attribute in (
        ("Codec", "codec_name"),
        ("Sample rate", "sample_rate"),
        ("Channels", "channels"),
        ("Sample format", "sample_format"),
        ("Sample size", "sample_size"),
        ("Duration", "duration_seconds"),
        ("Stream samples", "stream_samples"),
        ("Playable samples", "play_samples"),
        ("Loop enabled", "loop_flag"),
        ("Loop start", "loop_start"),
        ("Loop end", "loop_end"),
    ):
        value = getattr(info, attribute, None)
        if value is not None:
            print(f"{label}: {value}")


def validate_decode_paths(input_path: Path, output_path: Path, force: bool) -> None:
    ensure_input_file(input_path)
    if input_path.resolve() == output_path.resolve():
        raise CLIError("Input and output must be different files")
    if output_path.suffix.lower() != ".wav":
        raise CLIError("Output file must use the .wav extension")
    if output_path.exists() and not force:
        raise CLIError(
            f"Output already exists; add --force after confirming overwrite: {output_path}"
        )


def decode_audio(input_path: Path, output_path: Path, force: bool) -> None:
    validate_decode_paths(input_path, output_path, force)
    backend = load_backend()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.stem}.",
        suffix=".wav",
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        result = backend.decode_to_wav_file(str(input_path), str(temporary))
        os.replace(temporary, output_path)
    except Exception as error:
        raise CLIError(f"pyvgmstream could not decode {input_path}: {error}") from error
    finally:
        temporary.unlink(missing_ok=True)

    print(f"Wrote {output_path}")
    print(f"Frames: {result.frame_count}")
    print(f"Bytes: {output_path.stat().st_size}")


def batch_decode(input_path: Path, output_path: Path, workers: int) -> int:
    if not input_path.is_dir():
        raise CLIError(f"Input directory does not exist: {input_path}")
    if workers < 1:
        raise CLIError("--workers must be at least 1")

    backend = load_backend()
    output_path.mkdir(parents=True, exist_ok=True)
    try:
        summary = backend.transcode_tree(
            str(input_path),
            str(output_path),
            workers=workers,
            pattern="*.wem",
        )
    except Exception as error:
        raise CLIError(f"pyvgmstream batch conversion failed: {error}") from error

    print(f"Processed: {summary.processed_count}")
    print(f"Succeeded: {summary.processed_count - summary.failed_count}")
    print(f"Failed: {summary.failed_count}")
    for result in summary.results:
        if result.error:
            print(f"Failed: {result.source_path}: {result.error}", file=sys.stderr)
    return 1 if summary.failed_count else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            inspect_audio(args.input)
            return 0
        if args.command == "decode":
            decode_audio(args.input, args.output, args.force)
            return 0
        if args.command == "batch":
            return batch_decode(args.input, args.output, args.workers)
        raise CLIError(f"Unknown command: {args.command}")
    except (CLIError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
