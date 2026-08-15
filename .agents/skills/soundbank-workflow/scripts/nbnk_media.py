#!/usr/bin/env python3
"""Inspect, extract, and replace embedded WEM media in MHW NBNK files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import struct
import sys
import tempfile


ALIGNMENT = 16


class BankError(Exception):
    """A user-actionable SoundBank failure."""


@dataclass(frozen=True)
class Chunk:
    tag: bytes
    offset: int
    payload: bytes
    raw: bytes


@dataclass(frozen=True)
class MediaEntry:
    media_id: int
    offset: int
    size: int
    payload: bytes


@dataclass(frozen=True)
class Bank:
    chunks: tuple[Chunk, ...]
    entries: tuple[MediaEntry, ...]


def find_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "AGENTS.md").is_file() and (parent / ".agents").is_dir():
            return parent
    return Path.cwd()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect, extract, or replace embedded media in MHW NBNK files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect", help="Show chunk structure and DIDX media"
    )
    inspect_parser.add_argument("bank", type=Path)

    extract_parser = subparsers.add_parser(
        "extract", help="Extract one or all embedded WEM files"
    )
    extract_parser.add_argument("bank", type=Path)
    selector = extract_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--index", type=int, help="1-based DIDX index")
    selector.add_argument("--media-id", type=int, help="Media ID")
    selector.add_argument("--all", action="store_true", help="Extract every DIDX entry")
    extract_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output WEM for one entry, or output directory with --all",
    )
    extract_parser.add_argument("--force", action="store_true")

    replace_parser = subparsers.add_parser(
        "replace", help="Replace WEM files and rebuild the NBNK"
    )
    replace_parser.add_argument("input", type=Path)
    replace_parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output NBNK (default: <project>/output/<input filename>)",
    )
    replace_parser.add_argument(
        "--replace",
        action="append",
        required=True,
        metavar="TARGET=WEM",
        help="TARGET is a 1-based index or id:MEDIA_ID; may be repeated",
    )
    replace_parser.add_argument("--force", action="store_true")
    return parser


def read_bank(path: Path) -> Bank:
    if not path.is_file():
        raise BankError(f"Bank file does not exist: {path}")
    data = path.read_bytes()
    chunks: list[Chunk] = []
    position = 0
    while position < len(data):
        if len(data) - position < 8:
            raise BankError(f"{path} is missing a chunk header at 0x{position:X}")
        tag = data[position : position + 4]
        size = struct.unpack_from("<I", data, position + 4)[0]
        end = position + 8 + size
        if end > len(data):
            raise BankError(f"Chunk {tag!r} extends beyond the file boundary")
        chunks.append(
            Chunk(
                tag=tag,
                offset=position,
                payload=data[position + 8 : end],
                raw=data[position:end],
            )
        )
        position = end

    didx_chunks = [chunk for chunk in chunks if chunk.tag == b"DIDX"]
    data_chunks = [chunk for chunk in chunks if chunk.tag == b"DATA"]
    if len(didx_chunks) != 1 or len(data_chunks) != 1:
        raise BankError("Only Banks containing exactly one DIDX and one DATA chunk are supported")
    didx = didx_chunks[0].payload
    media_data = data_chunks[0].payload
    if len(didx) % 12:
        raise BankError("DIDX size is not a whole number of 12-byte entries")

    entries: list[MediaEntry] = []
    for position in range(0, len(didx), 12):
        media_id, offset, size = struct.unpack_from("<III", didx, position)
        end = offset + size
        if end > len(media_data):
            raise BankError(f"Media ID {media_id} range extends beyond DATA")
        entries.append(MediaEntry(media_id, offset, size, media_data[offset:end]))
    if not entries:
        raise BankError("DIDX contains no media entries")
    return Bank(tuple(chunks), tuple(entries))


def resolve_index(bank: Bank, index: int | None, media_id: int | None) -> int:
    if index is not None:
        if index < 1 or index > len(bank.entries):
            raise BankError(f"DIDX index must be between 1 and {len(bank.entries)}: {index}")
        return index - 1
    matches = [i for i, entry in enumerate(bank.entries) if entry.media_id == media_id]
    if not matches:
        raise BankError(f"Media ID not found: {media_id}")
    if len(matches) > 1:
        raise BankError(f"Media ID {media_id} is not unique; use a DIDX index instead")
    return matches[0]


def find_format_tag(payload: bytes) -> int:
    if len(payload) < 12 or payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
        raise BankError("Replacement file is not a RIFF/WAVE WEM")
    position = 12
    while position + 8 <= len(payload):
        tag = payload[position : position + 4]
        size = struct.unpack_from("<I", payload, position + 4)[0]
        start = position + 8
        end = start + size
        if end > len(payload):
            raise BankError("Replacement WEM contains an out-of-bounds RIFF chunk")
        if tag == b"fmt ":
            if size < 2:
                raise BankError("Replacement WEM has a fmt chunk that is too short")
            return struct.unpack_from("<H", payload, start)[0]
        position = end + (size & 1)
    raise BankError("Replacement WEM is missing a fmt chunk")


def validate_wem(path: Path) -> bytes:
    if not path.is_file():
        raise BankError(f"Replacement WEM does not exist: {path}")
    payload = path.read_bytes()
    format_tag = find_format_tag(payload)
    if format_tag == 0x0001:
        raise BankError(
            f"{path} is an ordinary PCM WAV (format tag 0x0001), which may produce silence "
            "in-game; convert it with wav_to_wem.py first"
        )
    return payload


def ensure_output(
    input_path: Path, output_path: Path, force: bool, expected_suffix: str | None = None
) -> None:
    if input_path.resolve() == output_path.resolve():
        raise BankError("Overwriting the input Bank in place is not allowed")
    if expected_suffix and output_path.suffix.lower() != expected_suffix:
        raise BankError(f"Output file must use the {expected_suffix} extension")
    if output_path.exists() and not force:
        raise BankError(
            f"Output already exists; add --force after confirming overwrite: {output_path}"
        )


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


def command_inspect(path: Path) -> None:
    bank = read_bank(path)
    print(f"Bank: {path}")
    print(f"Chunks: {len(bank.chunks)}")
    print(f"{'Index':>5} {'Tag':<4} {'File offset':>12} {'Payload size':>12}")
    for index, chunk in enumerate(bank.chunks, 1):
        print(
            f"{index:5d} {chunk.tag.decode('ascii', errors='replace'):<4} "
            f"0x{chunk.offset:08X} {len(chunk.payload):12d}"
        )

    print(f"Media entries: {len(bank.entries)}")
    print(f"{'Index':>5} {'Media ID':>10} {'DATA offset':>12} {'Size':>10} {'Aligned':>7}")
    for index, entry in enumerate(bank.entries, 1):
        aligned = "yes" if entry.offset % ALIGNMENT == 0 else "no"
        print(
            f"{index:5d} {entry.media_id:10d} "
            f"0x{entry.offset:08X} {entry.size:10d} {aligned:>7}"
        )


def command_extract(args: argparse.Namespace) -> None:
    bank = read_bank(args.bank)
    if args.all:
        if args.output.exists() and not args.output.is_dir():
            raise BankError(f"Batch extraction output is not a directory: {args.output}")
        targets = [
            (args.output / f"{index}_{entry.media_id}.wem", entry)
            for index, entry in enumerate(bank.entries, 1)
        ]
        collisions = [path for path, _ in targets if path.exists()]
        if collisions and not args.force:
            raise BankError(
                f"Output already exists; add --force after confirming overwrite: {collisions[0]}"
            )
        args.output.mkdir(parents=True, exist_ok=True)
        for path, entry in targets:
            atomic_write(path, entry.payload)
        print(f"Extracted {len(targets)} WEM files to {args.output}")
        return

    selected = resolve_index(bank, args.index, args.media_id)
    entry = bank.entries[selected]
    ensure_output(args.bank, args.output, args.force, ".wem")
    atomic_write(args.output, entry.payload)
    print(
        f"Extracted DIDX #{selected + 1} / Media ID {entry.media_id} "
        f"to {args.output} ({entry.size} bytes)"
    )


def parse_replacements(bank: Bank, specs: list[str]) -> dict[int, bytes]:
    replacements: dict[int, bytes] = {}
    for spec in specs:
        if "=" not in spec:
            raise BankError(f"Replacement argument must be TARGET=WEM: {spec}")
        target, path_text = spec.split("=", 1)
        if not target or not path_text:
            raise BankError(f"Replacement argument is missing a target or WEM path: {spec}")
        if target.startswith("id:"):
            try:
                media_id = int(target[3:], 10)
            except ValueError as error:
                raise BankError(f"Invalid Media ID: {target}") from error
            index = resolve_index(bank, None, media_id)
        else:
            try:
                didx_index = int(target, 10)
            except ValueError as error:
                raise BankError(f"Invalid DIDX index: {target}") from error
            index = resolve_index(bank, didx_index, None)
        if index in replacements:
            raise BankError(f"DIDX #{index + 1} was specified more than once")
        replacements[index] = validate_wem(Path(path_text))
    return replacements


def rebuild(bank: Bank, replacements: dict[int, bytes]) -> bytes:
    new_data = bytearray()
    new_entries: list[tuple[int, int, int]] = []
    for index, entry in enumerate(bank.entries):
        if new_data:
            new_data.extend(b"\0" * ((-len(new_data)) % ALIGNMENT))
        payload = replacements.get(index, entry.payload)
        new_entries.append((entry.media_id, len(new_data), len(payload)))
        new_data.extend(payload)
    new_didx = b"".join(struct.pack("<III", *entry) for entry in new_entries)

    output = bytearray()
    for chunk in bank.chunks:
        if chunk.tag == b"DIDX":
            output += b"DIDX" + struct.pack("<I", len(new_didx)) + new_didx
        elif chunk.tag == b"DATA":
            output += b"DATA" + struct.pack("<I", len(new_data)) + new_data
        else:
            output += chunk.raw
    return bytes(output)


def verify_rebuild(original: Bank, modified: Bank, replacements: dict[int, bytes]) -> None:
    if len(original.entries) != len(modified.entries):
        raise BankError("Read-back verification failed: the media count changed")
    if [entry.media_id for entry in original.entries] != [
        entry.media_id for entry in modified.entries
    ]:
        raise BankError("Read-back verification failed: Media IDs or order changed")
    for index, (before, after) in enumerate(zip(original.entries, modified.entries)):
        expected = replacements.get(index, before.payload)
        if after.payload != expected:
            raise BankError(f"Read-back verification failed: DIDX #{index + 1} content is unexpected")
        if after.offset % ALIGNMENT:
            raise BankError(f"Read-back verification failed: DIDX #{index + 1} is not 16-byte aligned")
    original_other = [
        (chunk.tag, chunk.payload)
        for chunk in original.chunks
        if chunk.tag not in {b"DIDX", b"DATA"}
    ]
    modified_other = [
        (chunk.tag, chunk.payload)
        for chunk in modified.chunks
        if chunk.tag not in {b"DIDX", b"DATA"}
    ]
    if original_other != modified_other:
        raise BankError("Read-back verification failed: a chunk other than DIDX/DATA changed")


def command_replace(args: argparse.Namespace) -> None:
    bank = read_bank(args.input)
    output = args.output or (find_project_root() / "output" / args.input.name)
    ensure_output(args.input, output, args.force, ".nbnk")
    replacements = parse_replacements(bank, args.replace)
    payload = rebuild(bank, replacements)
    output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb", dir=output.parent, prefix=f".{output.name}.", delete=False
    )
    staged = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        modified = read_bank(staged)
        verify_rebuild(bank, modified, replacements)
        os.replace(staged, output)
    finally:
        staged.unlink(missing_ok=True)

    print(f"Wrote and read back for verification: {output}")
    for index in sorted(replacements):
        entry = bank.entries[index]
        print(
            f"DIDX #{index + 1}: Media ID {entry.media_id}, "
            f"{entry.size} -> {len(replacements[index])} bytes"
        )
    print(f"SHA-256: {hashlib.sha256(payload).hexdigest()}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            command_inspect(args.bank)
        elif args.command == "extract":
            command_extract(args)
        elif args.command == "replace":
            command_replace(args)
        else:
            raise BankError(f"Unknown command: {args.command}")
        return 0
    except (BankError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
