#!/usr/bin/env python3
"""Shared mapping, conversion, validation, and publication support."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import difflib
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

from tools import soundbank_editor


EXPECTED_WEM_HEADER = "wem# new(old)"
EXPECTED_AUDIO_HEADER = "audio"
LINK_RE = re.compile(r"\]\((?:<([^>]+)>|([^\s)]+))\)")
BOLD_INDEX_RE = re.compile(r"\*\*(\d+)\*\*")
BANK_NAME_RE = re.compile(r"[a-z0-9_]+")


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


EditHook = Callable[[soundbank_editor.SoundBankEditor], None]


@dataclass(frozen=True)
class MappingMediaOverlay:
    """Mapping rows consumed as one appended media payload, not replacements."""

    indices: tuple[int, ...]
    media_id: int

    def __post_init__(self) -> None:
        if not self.indices:
            raise ValueError("Mapping media overlay must contain at least one DIDX index")
        if any(
            not isinstance(index, int) or isinstance(index, bool) or index < 1
            for index in self.indices
        ):
            raise ValueError("Mapping media overlay indices must be positive integers")
        if len(self.indices) != len(set(self.indices)):
            raise ValueError("Mapping media overlay indices must be unique")
        if (
            not isinstance(self.media_id, int)
            or isinstance(self.media_id, bool)
            or not 0 <= self.media_id <= 0xFFFFFFFF
        ):
            raise ValueError("Mapping media overlay Media ID must be a u32")


@dataclass(frozen=True)
class BankBuildPlan:
    """Declarative identity and bank-specific edits for one builder."""

    name: str
    apply_edits: EditHook
    media_overlays: tuple[MappingMediaOverlay, ...] = ()

    def __post_init__(self) -> None:
        if not BANK_NAME_RE.fullmatch(self.name):
            raise ValueError(f"Invalid Bank builder name: {self.name}")
        if not callable(self.apply_edits):
            raise TypeError("apply_edits must be callable")
        if not isinstance(self.media_overlays, tuple) or any(
            not isinstance(overlay, MappingMediaOverlay)
            for overlay in self.media_overlays
        ):
            raise TypeError("media_overlays must be a tuple of MappingMediaOverlay")


@dataclass(frozen=True)
class PreparedMappingMediaOverlay:
    """One validated overlay and its representative mapping row."""

    config: MappingMediaOverlay
    source_audio: Path
    representative: Replacement


@dataclass
class PreparedBank:
    """One preflighted project Bank build."""

    plan: BankBuildPlan
    source: Path
    mapping: MappingInfo
    original_bank: soundbank_editor.SoundBank
    preview_summary: soundbank_editor.EditSummary
    replacements: tuple[Replacement, ...]
    media_overlays: tuple[PreparedMappingMediaOverlay, ...]
    editor: soundbank_editor.SoundBankEditor | None = None
    staged: Path | None = None


@dataclass(frozen=True)
class ToolPaths:
    """Project tools used by the build and validation pipeline."""

    converter: Path
    pyvgmstream: Path
    wwiser: Path


@dataclass(frozen=True)
class BuildResult:
    """One published Bank and its observable build metadata."""

    path: Path
    sha256: str
    replacements: tuple[tuple[int, int], ...]
    added_media: tuple[tuple[int, int], ...]
    hirc_changed_bytes: int
    added_hirc_objects: tuple[tuple[int, int], ...]
    resized_hirc_objects: tuple[tuple[int, int, int, int], ...]
    hirc_size_delta: int


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
        converter=utils_root / "wav_to_wem.py",
        pyvgmstream=utils_root / "pyvgmstream.py",
        wwiser=tools_root / "wwiser" / "wwiser.py",
    )
    missing = [
        str(path)
        for path in (paths.converter, paths.pyvgmstream, paths.wwiser)
        if not path.is_file()
    ]
    if missing:
        raise BuildError("Required project tools are missing:\n" + "\n".join(missing))
    if shutil.which("ffmpeg") is None:
        raise BuildError(
            "ffmpeg was not found on PATH; run the builder in the project conda environment"
        )
    return paths


def partition_mapping_edits(
    build_plan: BankBuildPlan, mapping: MappingInfo
) -> tuple[tuple[Replacement, ...], tuple[PreparedMappingMediaOverlay, ...]]:
    """Separate ordinary replacements from plan-declared appended overlays."""

    by_index = {replacement.index: replacement for replacement in mapping.replacements}
    claimed: dict[int, int] = {}
    prepared_overlays: list[PreparedMappingMediaOverlay] = []
    for overlay_number, overlay in enumerate(build_plan.media_overlays, start=1):
        for index in overlay.indices:
            previous = claimed.get(index)
            if previous is not None:
                raise BuildError(
                    f"{build_plan.name}: DIDX #{index} is claimed by mapping media "
                    f"overlays {previous} and {overlay_number}"
                )
            claimed[index] = overlay_number
        missing = [index for index in overlay.indices if index not in by_index]
        if missing:
            raise BuildError(
                f"{build_plan.name}: mapping media overlay {overlay_number} references "
                "rows without Audio replacements: "
                + ", ".join(f"#{index}" for index in missing)
            )
        rows = [by_index[index] for index in overlay.indices]
        sources = {row.source_audio.resolve() for row in rows}
        if len(sources) != 1:
            details = ", ".join(
                f"#{row.index}={row.source_audio}" for row in rows
            )
            raise BuildError(
                f"{build_plan.name}: mapping media overlay {overlay_number} rows must "
                f"use one source audio file: {details}"
            )
        prepared_overlays.append(
            PreparedMappingMediaOverlay(
                config=overlay,
                source_audio=next(iter(sources)),
                representative=rows[0],
            )
        )
    replacements = tuple(
        replacement
        for replacement in mapping.replacements
        if replacement.index not in claimed
    )
    return replacements, tuple(prepared_overlays)


def prepare_plan(
    build_plan: BankBuildPlan,
    project_root: Path,
    mapping_dir: Path,
    soundbank_dir: Path,
) -> PreparedBank:
    mapping_path = mapping_dir / f"{build_plan.name}.md"
    source = soundbank_dir / f"{build_plan.name}.nbnk"
    if not mapping_path.is_file():
        raise BuildError(
            f"Mapping table does not exist for {build_plan.name}: {mapping_path}"
        )
    if not source.is_file():
        raise BuildError(f"Source Bank does not exist for {build_plan.name}: {source}")

    mapping = parse_mapping(mapping_path, project_root)
    try:
        original_bank = soundbank_editor.SoundBank.from_file(source)
    except soundbank_editor.SoundBankError as error:
        raise BuildError(f"Could not read Bank {source}: {error}") from error
    for replacement in mapping.replacements:
        if not 1 <= replacement.index <= len(original_bank.entries):
            raise BuildError(
                f"{mapping.path}:{replacement.line_number}: DIDX index "
                f"{replacement.index} is outside {source.name}'s range "
                f"1..{len(original_bank.entries)}"
            )
        replacement.media_id = original_bank.entries[replacement.index - 1].media_id

    replacements, media_overlays = partition_mapping_edits(build_plan, mapping)

    preview = soundbank_editor.SoundBankEditor(original_bank)
    try:
        for overlay in media_overlays:
            preview.append_media(
                overlay.config.media_id,
                original_bank.extract_media(index=overlay.representative.index),
            )
        build_plan.apply_edits(preview)
        preview.validate()
    except soundbank_editor.SoundBankError as error:
        raise BuildError(f"{build_plan.name}: invalid Bank edit plan: {error}") from error
    mapped_indices = {replacement.index for replacement in mapping.replacements}
    callback_indices = {index for index, _ in preview.summary.replaced_media}
    overlap = sorted(mapped_indices & callback_indices)
    if overlap:
        raise BuildError(
            f"{build_plan.name}: mapped media and apply_edits both replace DIDX "
            + ", ".join(f"#{index}" for index in overlap)
        )

    return PreparedBank(
        plan=build_plan,
        source=source,
        mapping=mapping,
        original_bank=original_bank,
        preview_summary=preview.summary,
        replacements=replacements,
        media_overlays=media_overlays,
    )


def validate_registry(
    plans: Sequence[BankBuildPlan], mapping_dir: Path, soundbank_dir: Path
) -> None:
    names = [plan.name for plan in plans]
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
    plans: Sequence[BankBuildPlan],
    project_root: Path,
    mapping_dir: Path,
    soundbank_dir: Path,
) -> list[PreparedBank]:
    validate_registry(plans, mapping_dir, soundbank_dir)
    return [
        prepare_plan(plan, project_root, mapping_dir, soundbank_dir)
        for plan in sorted(plans, key=lambda item: item.name)
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def convert_replacements(
    plan: PreparedBank,
    converted_dir: Path,
    project_root: Path,
    tools: ToolPaths,
) -> dict[int, bytes]:
    converted_dir.mkdir(parents=True, exist_ok=True)
    payloads: dict[int, bytes] = {}
    converted_sources: dict[Path, tuple[bytes, Path]] = {}
    conversion_rows = (
        *plan.replacements,
        *(overlay.representative for overlay in plan.media_overlays),
    )
    for replacement in conversion_rows:
        source_audio = replacement.source_audio.resolve()
        cached = converted_sources.get(source_audio)
        if cached is not None:
            payload, wem_path = cached
            replacement.wem_path = wem_path
            payloads[replacement.index - 1] = payload
            continue
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
            payload = soundbank_editor.validate_wem(wem_path)
        except soundbank_editor.SoundBankError as error:
            raise BuildError(f"Converted WEM is invalid: {wem_path}: {error}") from error
        replacement.wem_path = wem_path
        converted_sources[source_audio] = (payload, wem_path)
        payloads[replacement.index - 1] = payload
    return payloads


def validate_stage(
    plan: PreparedBank,
    stage: Path,
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths,
) -> None:
    validation_dir.mkdir(parents=True, exist_ok=True)
    if plan.editor is None:
        raise BuildError(f"{stage.name}: editor was not initialized")
    try:
        staged_bank = soundbank_editor.SoundBank.from_file(stage)
        expected_bank = plan.editor.validate()
    except soundbank_editor.SoundBankError as error:
        raise BuildError(f"{stage.name}: SoundBank read-back failed: {error}") from error
    if stage.read_bytes() != plan.editor.build() or staged_bank.to_bytes() != expected_bank.to_bytes():
        raise BuildError(f"{stage.name}: staged bytes do not match the editor result")
    summary = plan.editor.summary
    diff = plan.editor.diff()
    allowed_chunks: set[bytes] = set()
    if summary.replaced_media or summary.added_media:
        allowed_chunks.update((b"DIDX", b"DATA"))
    if summary.hirc_changed_bytes or summary.added_hirc_objects or summary.hirc_size_delta:
        allowed_chunks.add(b"HIRC")
    unexpected_chunks = set(diff.changed_chunks) - allowed_chunks
    if unexpected_chunks:
        raise BuildError(
            f"{stage.name}: unexpected changed chunks: {sorted(unexpected_chunks)}"
        )
    if not allowed_chunks and stage.read_bytes() != plan.source.read_bytes():
        raise BuildError(f"{stage.name}: unchanged Bank was not copied byte-for-byte")

    run_tool(
        [sys.executable, str(tools.wwiser), "-d", "none", str(stage)],
        f"wwiser {stage.name}",
        validation_dir,
    )

    if b"HIRC" in allowed_chunks:
        _write_wwiser_hirc_diff(plan.source, stage, validation_dir, tools, project_root)

    extract_dir = validation_dir / "extracted"
    decode_dir = validation_dir / "decoded"
    extract_dir.mkdir(parents=True, exist_ok=True)
    decode_dir.mkdir(parents=True, exist_ok=True)
    changed_media = (*summary.replaced_media, *summary.added_media)
    for index, media_id in changed_media:
        extracted = extract_dir / f"{plan.source.stem}_{index:03d}_{media_id}.wem"
        decoded = decode_dir / f"{plan.source.stem}_{index:03d}_{media_id}.wav"
        atomic_write(extracted, staged_bank.extract_media(index=index))
        run_tool(
            [sys.executable, str(tools.pyvgmstream), "inspect", str(extracted)],
            f"inspect extracted DIDX #{index}",
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
            f"decode extracted DIDX #{index}",
            project_root,
        )
        if not decoded.is_file() or decoded.stat().st_size == 0:
            raise BuildError(f"Decoded validation WAV is empty: {decoded}")


def _normalize_wwiser_hirc_dump(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == "obj  HircChunk"),
        None,
    )
    if start is None:
        raise BuildError(f"wwiser dump does not contain a HircChunk: {path}")
    section: list[str] = []
    for index, line in enumerate(lines[start:], start):
        if index > start and line.startswith("             obj  "):
            break
        section.append(re.sub(r"^[0-9a-fA-F]{8}", "OFFSET__", line).rstrip())
    return section


def _write_wwiser_hirc_diff(
    original: Path,
    staged: Path,
    validation_dir: Path,
    tools: ToolPaths,
    project_root: Path,
) -> None:
    original_prefix = validation_dir / "original-hirc"
    staged_prefix = validation_dir / "staged-hirc"
    for source, prefix, label in (
        (original, original_prefix, "original"),
        (staged, staged_prefix, "staged"),
    ):
        run_tool(
            [
                sys.executable,
                str(tools.wwiser),
                "-d",
                "txt",
                "-dn",
                str(prefix),
                str(source),
            ],
            f"wwiser {label} HIRC dump {source.name}",
            project_root,
        )
    before = _normalize_wwiser_hirc_dump(original_prefix.with_suffix(".txt"))
    after = _normalize_wwiser_hirc_dump(staged_prefix.with_suffix(".txt"))
    semantic_diff = "\n".join(
        difflib.unified_diff(
            before,
            after,
            fromfile=f"{original.name}:HIRC",
            tofile=f"{staged.name}:HIRC",
            lineterm="",
        )
    )
    atomic_write(validation_dir / "hirc-semantic.diff", semantic_diff.encode("utf-8"))


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
    plan: PreparedBank,
    stage_dir: Path,
    converted_dir: Path,
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths,
) -> None:
    stage = stage_dir / plan.source.name
    stage_dir.mkdir(parents=True, exist_ok=True)
    replacement_payloads = convert_replacements(plan, converted_dir, project_root, tools)
    editor = soundbank_editor.SoundBankEditor(plan.original_bank)
    try:
        for replacement in plan.replacements:
            if replacement.media_id is None:
                raise BuildError(f"Missing Media ID for DIDX #{replacement.index}")
            editor.replace_media(
                replacement_payloads[replacement.index - 1],
                index=replacement.index,
                expected_media_id=replacement.media_id,
            )
        for overlay in plan.media_overlays:
            editor.append_media(
                overlay.config.media_id,
                replacement_payloads[overlay.representative.index - 1],
            )
        plan.plan.apply_edits(editor)
        editor.validate()
    except soundbank_editor.SoundBankError as error:
        raise BuildError(f"Could not edit {plan.source}: {error}") from error
    plan.editor = editor
    payload = editor.build()
    atomic_write(stage, payload)

    validate_stage(
        plan,
        stage,
        validation_dir,
        project_root,
        tools,
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


def print_preflight(plans: Sequence[PreparedBank]) -> None:
    print(f"Builders: {len(plans)}")
    for plan in plans:
        replacements = ", ".join(
            f"#{item.index} (Media ID {item.media_id})"
            for item in plan.replacements
        ) or "none"
        overlays = ", ".join(
            "/".join(f"#{index}" for index in overlay.config.indices)
            + f" -> added Media ID {overlay.config.media_id}"
            for overlay in plan.media_overlays
        ) or "none"
        print(
            f"  {plan.mapping.path.name}: {plan.mapping.data_rows} rows, "
            f"replacements={replacements}, "
            f"overlays={overlays}, "
            f"HIRC changed bytes={plan.preview_summary.hirc_changed_bytes}, "
            f"HIRC added objects={len(plan.preview_summary.added_hirc_objects)}, "
            f"HIRC size delta={plan.preview_summary.hirc_size_delta:+d}"
        )
        for unresolved in plan.mapping.unresolved_rows:
            print(f"  warning: {unresolved}")


def _ensure_safe_target(
    plan: PreparedBank, target: Path, *, allow_existing: bool
) -> None:
    if target.resolve() == plan.source.resolve():
        raise BuildError(f"Refusing to overwrite original Bank: {target}")
    if target.exists() and not allow_existing:
        raise BuildError(
            f"Output already exists; add --force after confirming overwrite: {target}"
        )


def _make_result(plan: PreparedBank, target: Path) -> BuildResult:
    if plan.editor is None:
        raise BuildError(f"Bank editor is missing for {plan.source}")
    summary = plan.editor.summary
    return BuildResult(
        path=target,
        sha256=sha256(target),
        replacements=summary.replaced_media,
        added_media=summary.added_media,
        hirc_changed_bytes=summary.hirc_changed_bytes,
        added_hirc_objects=summary.added_hirc_objects,
        resized_hirc_objects=summary.resized_hirc_objects,
        hirc_size_delta=summary.hirc_size_delta,
    )


def _print_result(result: BuildResult) -> None:
    replacements = ", ".join(
        f"#{index}/Media ID {media_id}" for index, media_id in result.replacements
    ) or "none"
    added_media = ", ".join(
        f"#{index}/Media ID {media_id}" for index, media_id in result.added_media
    ) or "none"
    print(
        f"Published {result.path} | SHA-256 {result.sha256} | "
        f"replacements: {replacements} | "
        f"added media: {added_media} | "
        f"HIRC changed bytes: {result.hirc_changed_bytes} | "
        f"HIRC added objects: {len(result.added_hirc_objects)} | "
        f"HIRC resized objects: {len(result.resized_hirc_objects)} | "
        f"HIRC size delta: {result.hirc_size_delta:+d}"
    )


def build_one(
    build_plan_config: BankBuildPlan,
    *,
    root: Path | None = None,
    mapping_dir: str | Path = "mapping",
    soundbank_dir: str | Path = "original/nbnk",
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
    prepared = prepare_plan(
        build_plan_config, project_root, resolved_mapping, resolved_soundbank
    )
    print_preflight([prepared])
    target = resolved_output / prepared.source.name
    _ensure_safe_target(prepared, target, allow_existing=force or dry_run)

    if dry_run:
        print("Dry run complete; no output files were written.")
        return None

    with tempfile.TemporaryDirectory(prefix="nbnk-builder.", dir="/tmp") as directory:
        task_dir = Path(directory)
        build_plan(
            prepared,
            task_dir / "banks",
            task_dir / "converted",
            task_dir / "validation" / prepared.plan.name,
            project_root,
            tools,
        )
        if prepared.staged is None:
            raise BuildError(f"Bank was not staged: {prepared.source}")
        atomic_publish(prepared.staged, target)

    result = _make_result(prepared, target)
    _print_result(result)
    return result


def build_all(
    build_plan_configs: Sequence[BankBuildPlan],
    *,
    root: Path | None = None,
    mapping_dir: str | Path = "mapping",
    soundbank_dir: str | Path = "original/nbnk",
    release_dir: str | Path = "release",
    dry_run: bool = False,
) -> list[BuildResult]:
    """Build all registered Banks and publish only after every validation passes."""

    project_root = find_project_root(root)
    resolved_mapping = resolve_project_path(project_root, mapping_dir)
    resolved_soundbank = resolve_project_path(project_root, soundbank_dir)
    resolved_release = resolve_project_path(project_root, release_dir)
    tools = make_tool_paths(project_root)
    plans = prepare_all_plans(
        build_plan_configs,
        project_root,
        resolved_mapping,
        resolved_soundbank,
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
                task_dir / "converted" / plan.plan.name,
                task_dir / "validation" / plan.plan.name,
                project_root,
                tools,
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
        default="original/nbnk",
        help="Original SoundBank directory relative to root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run table, path, index, and HIRC setting checks without building",
    )


def run_single_cli(plan: BankBuildPlan, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"Build and validate {plan.name}.nbnk from its mapping table."
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
            plan,
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


def run_all_cli(plans: Sequence[BankBuildPlan], argv: list[str] | None = None) -> int:
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
            plans,
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
