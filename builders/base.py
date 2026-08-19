#!/usr/bin/env python3
"""Shared mapping, NBNK rebuild, HIRC editing, and validation support."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any
from urllib.parse import unquote, urlsplit


EXPECTED_WEM_HEADER = "wem# new(old)"
EXPECTED_AUDIO_HEADER = "audio"
LINK_RE = re.compile(r"\]\((?:<([^>]+)>|([^\s)]+))\)")
BOLD_INDEX_RE = re.compile(r"\*\*(\d+)\*\*")
BANK_NAME_RE = re.compile(r"[a-z0-9_]+")
HIRC_TAG = b"HIRC"


class BuildError(Exception):
    """A user-actionable build failure."""


@dataclass
class Replacement:
    """One mapping row that replaces a 1-based DIDX entry."""

    index: int
    source_audio: Path
    line_number: int
    media_id: int | None = None
    wem_path: Path | None = None


@dataclass
class MappingInfo:
    """Parsed mapping table for one SoundBank."""

    path: Path
    bank_name: str
    data_rows: int
    replacements: list[Replacement]
    unresolved_rows: list[str]


@dataclass
class HircObject:
    """One mutable object body from a HIRC chunk."""

    index: int
    object_type: int
    object_id: int
    body: bytearray


class HircEditor:
    """Edit HIRC object bodies by type and ID using guarded relative offsets.

    The editor deliberately supports only length-preserving field patches. This
    keeps every HIRC object size and the enclosing chunk size stable while still
    allowing the node properties currently required by this project.
    """

    def __init__(self, payload: bytes):
        if len(payload) < 4:
            raise BuildError("HIRC payload is missing its object count")

        self._count = struct.unpack_from("<I", payload, 0)[0]
        self._objects: list[HircObject] = []
        self._by_key: dict[tuple[int, int], HircObject] = {}
        self._patched_ranges: dict[tuple[int, int], list[tuple[int, int]]] = {}
        self._changed_byte_count = 0

        position = 4
        for index in range(self._count):
            if position + 5 > len(payload):
                raise BuildError(f"HIRC object #{index} is missing its header")
            object_type = payload[position]
            size = struct.unpack_from("<I", payload, position + 1)[0]
            body_start = position + 5
            body_end = body_start + size
            if body_end > len(payload):
                raise BuildError(f"HIRC object #{index} extends beyond the chunk")
            if size < 4:
                raise BuildError(f"HIRC object #{index} is too small to contain an ID")

            body = bytearray(payload[body_start:body_end])
            object_id = struct.unpack_from("<I", body, 0)[0]
            key = (object_type, object_id)
            if key in self._by_key:
                raise BuildError(
                    f"HIRC contains duplicate type 0x{object_type:02X} "
                    f"object ID {object_id}"
                )
            item = HircObject(index, object_type, object_id, body)
            self._objects.append(item)
            self._by_key[key] = item
            position = body_end

        if position != len(payload):
            raise BuildError(
                f"HIRC has {len(payload) - position} trailing bytes after its objects"
            )

    @property
    def changed_byte_count(self) -> int:
        """Number of byte positions whose values were changed."""

        return self._changed_byte_count

    def object_body(self, object_type: int, object_id: int) -> bytes:
        """Return a read-only copy of one HIRC object body."""

        return bytes(self._get_object(object_type, object_id).body)

    def _get_object(self, object_type: int, object_id: int) -> HircObject:
        try:
            return self._by_key[(object_type, object_id)]
        except KeyError as error:
            raise BuildError(
                f"HIRC object not found: type 0x{object_type:02X}, ID {object_id}"
            ) from error

    def patch_bytes(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: bytes,
        replacement: bytes,
        *,
        label: str,
    ) -> None:
        """Replace bytes inside one object after checking the exact old value."""

        if len(expected) != len(replacement):
            raise BuildError(f"{label}: HIRC patches must preserve field length")
        if not expected:
            raise BuildError(f"{label}: HIRC patch may not be empty")
        if offset < 4:
            raise BuildError(f"{label}: patch may not alter the HIRC object ID")

        item = self._get_object(object_type, object_id)
        end = offset + len(expected)
        if end > len(item.body):
            raise BuildError(
                f"{label}: object ID {object_id} range 0x{offset:X}..0x{end:X} "
                f"exceeds its {len(item.body)}-byte body"
            )

        key = (object_type, object_id)
        for prior_start, prior_end in self._patched_ranges.get(key, []):
            if offset < prior_end and prior_start < end:
                raise BuildError(
                    f"{label}: patch overlaps an earlier edit to object ID {object_id}"
                )

        actual = bytes(item.body[offset:end])
        if actual != expected:
            raise BuildError(
                f"{label}: object type 0x{object_type:02X} ID {object_id} "
                f"at body+0x{offset:X} expected {expected.hex()} but found {actual.hex()}"
            )

        item.body[offset:end] = replacement
        self._patched_ranges.setdefault(key, []).append((offset, end))
        self._changed_byte_count += sum(
            before != after for before, after in zip(expected, replacement)
        )

    def patch_u8(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: int,
        replacement: int,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<B", expected),
            struct.pack("<B", replacement),
            label=label,
        )

    def patch_u32(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: int,
        replacement: int,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<I", expected),
            struct.pack("<I", replacement),
            label=label,
        )

    def patch_float(
        self,
        object_type: int,
        object_id: int,
        offset: int,
        expected: float,
        replacement: float,
        *,
        label: str,
    ) -> None:
        self.patch_bytes(
            object_type,
            object_id,
            offset,
            struct.pack("<f", expected),
            struct.pack("<f", replacement),
            label=label,
        )

    def build(self) -> bytes:
        """Serialize the edited HIRC payload without reordering objects."""

        output = bytearray(struct.pack("<I", self._count))
        for item in self._objects:
            output += struct.pack("<BI", item.object_type, len(item.body))
            output += item.body
        return bytes(output)


SettingsHook = Callable[[HircEditor], None]


@dataclass(frozen=True)
class BankSpec:
    """Declarative identity and bank-specific HIRC settings for one builder."""

    name: str
    apply_settings: SettingsHook

    def __post_init__(self) -> None:
        if not BANK_NAME_RE.fullmatch(self.name):
            raise ValueError(f"Invalid Bank builder name: {self.name}")
        if not callable(self.apply_settings):
            raise TypeError("apply_settings must be callable")


@dataclass
class BankPlan:
    """A source Bank and all expected media/HIRC changes."""

    spec: BankSpec
    source: Path
    mapping: MappingInfo
    original_bank: Any
    expected_hirc: bytes
    hirc_changed_bytes: int
    staged: Path | None = None


@dataclass(frozen=True)
class ToolPaths:
    """Project tools used by the build and validation pipeline."""

    media: Path
    converter: Path
    pyvgmstream: Path
    wwiser: Path


@dataclass(frozen=True)
class BuildResult:
    """One published Bank and its observable build metadata."""

    path: Path
    sha256: str
    replacements: tuple[tuple[int, int], ...]
    hirc_changed_bytes: int


def normalize_header(value: str) -> str:
    return " ".join(value.split()).casefold()


def split_table_cells(line: str) -> list[str]:
    if not line.lstrip().startswith("|"):
        return []
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|"):
        content = content[:-1]
    return [cell.strip() for cell in content.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in cells)


def markdown_links(cell: str) -> list[str]:
    return [match.group(1) or match.group(2) for match in LINK_RE.finditer(cell)]


def resolve_local_link(target: str, base_dir: Path) -> Path:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        raise BuildError(f"External links are not supported in local audio cells: {target}")
    path_text = unquote(parsed.path)
    if not path_text:
        raise BuildError(f"Audio link has no file path: {target}")
    return (base_dir / path_text).resolve()


def find_original_reference(
    wem_cell: str, mapping_path: Path, project_root: Path
) -> tuple[Path, str, int] | None:
    original_root = (project_root / "original" / "audio_files").resolve()
    candidates: list[tuple[Path, str, int]] = []
    for target in markdown_links(wem_cell):
        candidate = resolve_local_link(target, mapping_path.parent)
        try:
            relative = candidate.relative_to(original_root)
        except ValueError:
            continue
        if len(relative.parts) != 3 or relative.parts[1] != "wav":
            continue
        filename = Path(relative.parts[2])
        if filename.suffix.casefold() != ".wav" or not filename.stem.isdigit():
            continue
        candidates.append((candidate, relative.parts[0], int(filename.stem)))

    if len(candidates) > 1:
        raise BuildError(
            f"{mapping_path}: Wem# New(Old) cell contains multiple original audio links"
        )
    return candidates[0] if candidates else None


def parse_mapping(path: Path, project_root: Path) -> MappingInfo:
    """Parse and preflight one project mapping Markdown table."""

    headers: dict[str, int] | None = None
    saw_header = False
    data_rows = 0
    replacements: list[Replacement] = []
    unresolved_rows: list[str] = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        cells = split_table_cells(line)
        if not cells:
            continue

        normalized = [normalize_header(cell) for cell in cells]
        if normalized and normalized[0] == EXPECTED_WEM_HEADER:
            if EXPECTED_AUDIO_HEADER not in normalized:
                raise BuildError(f"{path}:{line_number}: missing Audio column")
            if normalized.count(EXPECTED_WEM_HEADER) != 1:
                raise BuildError(f"{path}:{line_number}: duplicate Wem# New(Old) column")
            if normalized.count(EXPECTED_AUDIO_HEADER) != 1:
                raise BuildError(f"{path}:{line_number}: duplicate Audio column")
            headers = {
                EXPECTED_WEM_HEADER: normalized.index(EXPECTED_WEM_HEADER),
                EXPECTED_AUDIO_HEADER: normalized.index(EXPECTED_AUDIO_HEADER),
            }
            saw_header = True
            continue

        if headers is None or is_separator_row(cells):
            continue

        required_index = max(headers.values())
        if len(cells) <= required_index:
            raise BuildError(
                f"{path}:{line_number}: table row has fewer cells than its header"
            )
        if not any(cells):
            continue

        data_rows += 1
        wem_cell = cells[headers[EXPECTED_WEM_HEADER]]
        audio_cell = cells[headers[EXPECTED_AUDIO_HEADER]].strip()
        original = find_original_reference(wem_cell, path, project_root)

        if original is None:
            message = f"{path}:{line_number}: no original audio link"
            if audio_cell:
                raise BuildError(
                    f"{message}; Audio is non-empty and cannot identify a DIDX target"
                )
            unresolved_rows.append(message)
            continue

        original_path, bank_name, index = original
        if bank_name != path.stem:
            raise BuildError(
                f"{path}:{line_number}: original link belongs to {bank_name}, "
                f"but mapping filename is {path.stem}"
            )
        if not original_path.is_file():
            raise BuildError(
                f"{path}:{line_number}: original audio does not exist: {original_path}"
            )

        bold_index = BOLD_INDEX_RE.search(wem_cell)
        if bold_index and int(bold_index.group(1)) != index:
            raise BuildError(
                f"{path}:{line_number}: bold Wem index {bold_index.group(1)} "
                f"does not match original audio index {index}"
            )

        if not audio_cell:
            continue

        audio_links = markdown_links(audio_cell)
        if len(audio_links) != 1:
            raise BuildError(
                f"{path}:{line_number}: Audio must contain exactly one local Markdown link"
            )
        source_audio = resolve_local_link(audio_links[0], path.parent)
        if not source_audio.is_relative_to(project_root):
            raise BuildError(
                f"{path}:{line_number}: Audio path must remain inside the project: "
                f"{source_audio}"
            )
        if not source_audio.is_file():
            raise BuildError(
                f"{path}:{line_number}: Audio file does not exist: {source_audio}"
            )

        replacements.append(
            Replacement(index=index, source_audio=source_audio, line_number=line_number)
        )

    if not saw_header:
        raise BuildError(
            f"{path}: no table with Wem# New(Old) and Audio columns was found"
        )

    seen: dict[int, int] = {}
    for replacement in replacements:
        previous = seen.get(replacement.index)
        if previous is not None:
            raise BuildError(
                f"{path}:{replacement.line_number}: DIDX index {replacement.index} "
                f"already appears at line {previous}"
            )
        seen[replacement.index] = replacement.line_number

    return MappingInfo(
        path=path,
        bank_name=path.stem,
        data_rows=data_rows,
        replacements=replacements,
        unresolved_rows=unresolved_rows,
    )


def find_project_root(explicit_root: Path | None) -> Path:
    if explicit_root is not None:
        root = explicit_root.expanduser().resolve()
        if not root.is_dir():
            raise BuildError(f"Project root does not exist: {root}")
        return root

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / ".agents").is_dir():
            return candidate
    raise BuildError("Could not find the project root; pass --root explicitly")


def resolve_project_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def load_media_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("project_nbnk_media", path)
    if spec is None or spec.loader is None:
        raise BuildError(f"Could not load NBNK helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_tool(
    command: list[str], label: str, working_directory: Path
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise BuildError(f"{label} could not start: {error}") from error
    if completed.returncode != 0:
        details = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
        )
        raise BuildError(
            f"{label} failed with exit code {completed.returncode}"
            + (f":\n{details}" if details else "")
        )
    return completed


def make_tool_paths(project_root: Path) -> ToolPaths:
    tools_root = project_root / "tools"
    utils_root = tools_root / "utils"
    paths = ToolPaths(
        media=utils_root / "nbnk_media.py",
        converter=utils_root / "wav_to_wem.py",
        pyvgmstream=utils_root / "pyvgmstream.py",
        wwiser=tools_root / "wwiser" / "wwiser.py",
    )
    missing = [
        str(path)
        for path in (paths.media, paths.converter, paths.pyvgmstream, paths.wwiser)
        if not path.is_file()
    ]
    if missing:
        raise BuildError("Required project tools are missing:\n" + "\n".join(missing))
    if shutil.which("ffmpeg") is None:
        raise BuildError(
            "ffmpeg was not found on PATH; run the builder in the project conda environment"
        )
    return paths


def _iter_raw_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    chunks: list[tuple[bytes, bytes]] = []
    position = 0
    while position < len(data):
        if position + 8 > len(data):
            raise BuildError(f"NBNK is missing a chunk header at 0x{position:X}")
        tag = data[position : position + 4]
        size = struct.unpack_from("<I", data, position + 4)[0]
        end = position + 8 + size
        if end > len(data):
            raise BuildError(f"NBNK chunk {tag!r} extends beyond the file boundary")
        chunks.append((tag, data[position + 8 : end]))
        position = end
    return chunks


def get_chunk_payload(data: bytes, tag: bytes) -> bytes:
    """Return the payload of the one chunk matching ``tag``."""

    matches = [payload for chunk_tag, payload in _iter_raw_chunks(data) if chunk_tag == tag]
    if len(matches) != 1:
        raise BuildError(f"Expected exactly one {tag!r} chunk, found {len(matches)}")
    return matches[0]


def replace_chunk_payload(data: bytes, tag: bytes, replacement: bytes) -> bytes:
    """Replace exactly one chunk payload while preserving order and other bytes."""

    output = bytearray()
    matches = 0
    for chunk_tag, payload in _iter_raw_chunks(data):
        if chunk_tag == tag:
            payload = replacement
            matches += 1
        output += chunk_tag + struct.pack("<I", len(payload)) + payload
    if matches != 1:
        raise BuildError(f"Expected exactly one {tag!r} chunk, found {matches}")
    return bytes(output)


def load_bank(media_module: ModuleType, path: Path) -> Any:
    try:
        return media_module.read_bank(path)
    except Exception as error:
        raise BuildError(f"Could not read Bank {path}: {error}") from error


def prepare_plan(
    spec: BankSpec,
    project_root: Path,
    mapping_dir: Path,
    soundbank_dir: Path,
    media_module: ModuleType,
) -> BankPlan:
    mapping_path = mapping_dir / f"{spec.name}.md"
    source = soundbank_dir / f"{spec.name}.nbnk"
    if not mapping_path.is_file():
        raise BuildError(f"Mapping table does not exist for {spec.name}: {mapping_path}")
    if not source.is_file():
        raise BuildError(f"Source Bank does not exist for {spec.name}: {source}")

    mapping = parse_mapping(mapping_path, project_root)
    original_bank = load_bank(media_module, source)
    for replacement in mapping.replacements:
        if not 1 <= replacement.index <= len(original_bank.entries):
            raise BuildError(
                f"{mapping.path}:{replacement.line_number}: DIDX index "
                f"{replacement.index} is outside {source.name}'s range "
                f"1..{len(original_bank.entries)}"
            )
        replacement.media_id = original_bank.entries[replacement.index - 1].media_id

    original_hirc = get_chunk_payload(source.read_bytes(), HIRC_TAG)
    editor = HircEditor(original_hirc)
    spec.apply_settings(editor)
    expected_hirc = editor.build()
    if len(expected_hirc) != len(original_hirc):
        raise BuildError(f"{spec.name}: bank-specific HIRC settings changed chunk length")

    return BankPlan(
        spec=spec,
        source=source,
        mapping=mapping,
        original_bank=original_bank,
        expected_hirc=expected_hirc,
        hirc_changed_bytes=editor.changed_byte_count,
    )


def validate_registry(
    specs: Sequence[BankSpec], mapping_dir: Path, soundbank_dir: Path
) -> None:
    names = [spec.name for spec in specs]
    if len(names) != len(set(names)):
        duplicate = next(name for name in names if names.count(name) > 1)
        raise BuildError(f"Duplicate builder registration: {duplicate}")
    expected = set(names)

    if not mapping_dir.is_dir():
        raise BuildError(f"Mapping directory does not exist: {mapping_dir}")
    if not soundbank_dir.is_dir():
        raise BuildError(f"SoundBank directory does not exist: {soundbank_dir}")
    actual_mappings = {path.stem for path in mapping_dir.glob("*.md")}
    actual_banks = {path.stem for path in soundbank_dir.glob("*.nbnk")}

    for label, actual in (("mapping", actual_mappings), ("SoundBank", actual_banks)):
        missing = sorted(actual - expected)
        extra = sorted(expected - actual)
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing builders: {', '.join(missing)}")
            if extra:
                details.append(f"builders without {label} files: {', '.join(extra)}")
            raise BuildError(f"Builder/{label} registry mismatch: {'; '.join(details)}")


def prepare_all_plans(
    specs: Sequence[BankSpec],
    project_root: Path,
    mapping_dir: Path,
    soundbank_dir: Path,
    media_module: ModuleType,
) -> list[BankPlan]:
    validate_registry(specs, mapping_dir, soundbank_dir)
    return [
        prepare_plan(spec, project_root, mapping_dir, soundbank_dir, media_module)
        for spec in sorted(specs, key=lambda item: item.name)
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def convert_replacements(
    plan: BankPlan,
    converted_dir: Path,
    project_root: Path,
    tools: ToolPaths,
    media_module: ModuleType,
) -> dict[int, bytes]:
    converted_dir.mkdir(parents=True, exist_ok=True)
    payloads: dict[int, bytes] = {}
    for replacement in plan.mapping.replacements:
        wem_path = converted_dir / f"{plan.source.stem}_{replacement.index:03d}.wem"
        run_tool(
            [
                sys.executable,
                str(tools.converter),
                str(replacement.source_audio),
                str(wem_path),
                "--force",
            ],
            f"convert {replacement.source_audio}",
            project_root,
        )
        try:
            payload = media_module.validate_wem(wem_path)
        except Exception as error:
            raise BuildError(f"Converted WEM is invalid: {wem_path}: {error}") from error
        replacement.wem_path = wem_path
        payloads[replacement.index - 1] = payload
    return payloads


def validate_stage(
    plan: BankPlan,
    stage: Path,
    replacement_payloads: dict[int, bytes],
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths,
    media_module: ModuleType,
) -> None:
    validation_dir.mkdir(parents=True, exist_ok=True)
    staged_bank = load_bank(media_module, stage)
    original_bank = plan.original_bank

    if len(original_bank.entries) != len(staged_bank.entries):
        raise BuildError(f"{stage.name}: media count changed")
    if [entry.media_id for entry in original_bank.entries] != [
        entry.media_id for entry in staged_bank.entries
    ]:
        raise BuildError(f"{stage.name}: Media IDs or DIDX order changed")
    for index, (before, after) in enumerate(
        zip(original_bank.entries, staged_bank.entries)
    ):
        expected = replacement_payloads.get(index, before.payload)
        if after.payload != expected:
            raise BuildError(
                f"{stage.name}: DIDX #{index + 1} payload is not the expected media"
            )
        if after.offset % media_module.ALIGNMENT:
            raise BuildError(f"{stage.name}: DIDX #{index + 1} is not 16-byte aligned")

    if len(original_bank.chunks) != len(staged_bank.chunks):
        raise BuildError(f"{stage.name}: chunk count changed")
    for before, after in zip(original_bank.chunks, staged_bank.chunks):
        if before.tag != after.tag:
            raise BuildError(f"{stage.name}: chunk order changed")
        if before.tag in {b"DIDX", b"DATA"}:
            continue
        expected = plan.expected_hirc if before.tag == HIRC_TAG else before.payload
        if after.payload != expected:
            raise BuildError(
                f"{stage.name}: unexpected change in {before.tag.decode(errors='replace')} chunk"
            )

    if not replacement_payloads and plan.hirc_changed_bytes == 0:
        if stage.read_bytes() != plan.source.read_bytes():
            raise BuildError(f"{stage.name}: unchanged Bank was not copied byte-for-byte")

    # Parsing the expected result catches malformed object sizes before wwiser.
    HircEditor(plan.expected_hirc)
    run_tool(
        [sys.executable, str(tools.media), "inspect", str(stage)],
        f"inspect {stage.name}",
        project_root,
    )
    run_tool(
        [sys.executable, str(tools.wwiser), "-d", "none", str(stage)],
        f"wwiser {stage.name}",
        validation_dir,
    )

    extract_dir = validation_dir / "extracted"
    decode_dir = validation_dir / "decoded"
    extract_dir.mkdir(parents=True, exist_ok=True)
    decode_dir.mkdir(parents=True, exist_ok=True)
    for replacement in plan.mapping.replacements:
        extracted = extract_dir / f"{plan.source.stem}_{replacement.index:03d}.wem"
        decoded = decode_dir / f"{plan.source.stem}_{replacement.index:03d}.wav"
        run_tool(
            [
                sys.executable,
                str(tools.media),
                "extract",
                str(stage),
                "--index",
                str(replacement.index),
                "-o",
                str(extracted),
                "--force",
            ],
            f"extract {stage.name} DIDX #{replacement.index}",
            project_root,
        )
        run_tool(
            [sys.executable, str(tools.pyvgmstream), "inspect", str(extracted)],
            f"inspect extracted DIDX #{replacement.index}",
            project_root,
        )
        run_tool(
            [
                sys.executable,
                str(tools.pyvgmstream),
                "decode",
                str(extracted),
                str(decoded),
                "--force",
            ],
            f"decode extracted DIDX #{replacement.index}",
            project_root,
        )
        if not decoded.is_file() or decoded.stat().st_size == 0:
            raise BuildError(f"Decoded validation WAV is empty: {decoded}")


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


def build_plan(
    plan: BankPlan,
    stage_dir: Path,
    converted_dir: Path,
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths,
    media_module: ModuleType,
) -> None:
    stage = stage_dir / plan.source.name
    stage_dir.mkdir(parents=True, exist_ok=True)
    replacement_payloads = convert_replacements(
        plan, converted_dir, project_root, tools, media_module
    )

    if replacement_payloads:
        try:
            payload = media_module.rebuild(plan.original_bank, replacement_payloads)
        except Exception as error:
            raise BuildError(f"Could not rebuild media in {plan.source}: {error}") from error
    else:
        payload = plan.source.read_bytes()

    original_hirc = get_chunk_payload(payload, HIRC_TAG)
    if original_hirc != plan.expected_hirc:
        payload = replace_chunk_payload(payload, HIRC_TAG, plan.expected_hirc)
    atomic_write(stage, payload)

    validate_stage(
        plan,
        stage,
        replacement_payloads,
        validation_dir,
        project_root,
        tools,
        media_module,
    )
    plan.staged = stage


def atomic_publish(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        with source.open("rb") as source_handle, temporary.open("wb") as target_handle:
            shutil.copyfileobj(source_handle, target_handle)
            target_handle.flush()
            os.fsync(target_handle.fileno())
        shutil.copymode(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def print_preflight(plans: Sequence[BankPlan]) -> None:
    print(f"Builders: {len(plans)}")
    for plan in plans:
        replacements = ", ".join(
            f"#{item.index} (Media ID {item.media_id})"
            for item in plan.mapping.replacements
        ) or "none"
        print(
            f"  {plan.mapping.path.name}: {plan.mapping.data_rows} rows, "
            f"replacements={replacements}, "
            f"HIRC changed bytes={plan.hirc_changed_bytes}"
        )
        for unresolved in plan.mapping.unresolved_rows:
            print(f"  warning: {unresolved}")


def _ensure_safe_target(plan: BankPlan, target: Path, *, allow_existing: bool) -> None:
    if target.resolve() == plan.source.resolve():
        raise BuildError(f"Refusing to overwrite original Bank: {target}")
    if target.exists() and not allow_existing:
        raise BuildError(
            f"Output already exists; add --force after confirming overwrite: {target}"
        )


def _make_result(plan: BankPlan, target: Path) -> BuildResult:
    replacements: list[tuple[int, int]] = []
    for item in plan.mapping.replacements:
        if item.media_id is None:
            raise BuildError(f"Missing Media ID for DIDX #{item.index}")
        replacements.append((item.index, item.media_id))
    return BuildResult(
        path=target,
        sha256=sha256(target),
        replacements=tuple(replacements),
        hirc_changed_bytes=plan.hirc_changed_bytes,
    )


def _print_result(result: BuildResult) -> None:
    replacements = ", ".join(
        f"#{index}/Media ID {media_id}" for index, media_id in result.replacements
    ) or "none"
    print(
        f"Published {result.path} | SHA-256 {result.sha256} | "
        f"replacements: {replacements} | "
        f"HIRC changed bytes: {result.hirc_changed_bytes}"
    )


def build_one(
    spec: BankSpec,
    *,
    root: Path | None = None,
    mapping_dir: str | Path = "mapping",
    soundbank_dir: str | Path = "original/soundbank",
    output_dir: str | Path = "output",
    dry_run: bool = False,
    force: bool = False,
) -> BuildResult | None:
    """Build, validate, and publish one Bank, defaulting to ``output/``."""

    project_root = find_project_root(root)
    resolved_mapping = resolve_project_path(project_root, mapping_dir)
    resolved_soundbank = resolve_project_path(project_root, soundbank_dir)
    resolved_output = resolve_project_path(project_root, output_dir)
    tools = make_tool_paths(project_root)
    media_module = load_media_module(tools.media)
    plan = prepare_plan(
        spec, project_root, resolved_mapping, resolved_soundbank, media_module
    )
    print_preflight([plan])
    target = resolved_output / plan.source.name
    _ensure_safe_target(plan, target, allow_existing=force or dry_run)

    if dry_run:
        print("Dry run complete; no output files were written.")
        return None

    with tempfile.TemporaryDirectory(prefix="nbnk-builder.", dir="/tmp") as directory:
        task_dir = Path(directory)
        build_plan(
            plan,
            task_dir / "banks",
            task_dir / "converted",
            task_dir / "validation" / plan.spec.name,
            project_root,
            tools,
            media_module,
        )
        if plan.staged is None:
            raise BuildError(f"Bank was not staged: {plan.source}")
        atomic_publish(plan.staged, target)

    result = _make_result(plan, target)
    _print_result(result)
    return result


def build_all(
    specs: Sequence[BankSpec],
    *,
    root: Path | None = None,
    mapping_dir: str | Path = "mapping",
    soundbank_dir: str | Path = "original/soundbank",
    release_dir: str | Path = "release",
    dry_run: bool = False,
) -> list[BuildResult]:
    """Build all registered Banks and publish only after every validation passes."""

    project_root = find_project_root(root)
    resolved_mapping = resolve_project_path(project_root, mapping_dir)
    resolved_soundbank = resolve_project_path(project_root, soundbank_dir)
    resolved_release = resolve_project_path(project_root, release_dir)
    tools = make_tool_paths(project_root)
    media_module = load_media_module(tools.media)
    plans = prepare_all_plans(
        specs,
        project_root,
        resolved_mapping,
        resolved_soundbank,
        media_module,
    )
    print_preflight(plans)
    for plan in plans:
        _ensure_safe_target(
            plan, resolved_release / plan.source.name, allow_existing=True
        )

    if dry_run:
        print("Dry run complete; no output files were written.")
        return []

    results: list[BuildResult] = []
    with tempfile.TemporaryDirectory(prefix="nbnk-build-all.", dir="/tmp") as directory:
        task_dir = Path(directory)
        for plan in plans:
            build_plan(
                plan,
                task_dir / "banks",
                task_dir / "converted" / plan.spec.name,
                task_dir / "validation" / plan.spec.name,
                project_root,
                tools,
                media_module,
            )

        for plan in plans:
            if plan.staged is None:
                raise BuildError(f"Bank was not staged: {plan.source}")
            target = resolved_release / plan.source.name
            atomic_publish(plan.staged, target)
            result = _make_result(plan, target)
            results.append(result)
            _print_result(result)

    print(f"Build complete: {len(results)} Banks published to {resolved_release}")
    return results


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, help="Project root; auto-detected by default")
    parser.add_argument(
        "--mapping-dir", default="mapping", help="Mapping directory relative to root"
    )
    parser.add_argument(
        "--soundbank-dir",
        default="original/soundbank",
        help="Original SoundBank directory relative to root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run table, path, index, and HIRC setting checks without building",
    )


def run_single_cli(spec: BankSpec, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"Build and validate {spec.name}.nbnk from its mapping table."
    )
    _add_common_arguments(parser)
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory relative to root unless absolute",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing output")
    args = parser.parse_args(argv)
    try:
        build_one(
            spec,
            root=args.root,
            mapping_dir=args.mapping_dir,
            soundbank_dir=args.soundbank_dir,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            force=args.force,
        )
        return 0
    except (BuildError, OSError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


def run_all_cli(specs: Sequence[BankSpec], argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and validate every registered project NBNK mod Bank."
    )
    _add_common_arguments(parser)
    parser.add_argument(
        "--release-dir",
        default="release",
        help="Release directory relative to root unless absolute",
    )
    args = parser.parse_args(argv)
    try:
        build_all(
            specs,
            root=args.root,
            mapping_dir=args.mapping_dir,
            soundbank_dir=args.soundbank_dir,
            release_dir=args.release_dir,
            dry_run=args.dry_run,
        )
        return 0
    except (BuildError, OSError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
