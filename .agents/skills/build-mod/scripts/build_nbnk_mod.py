#!/usr/bin/env python3
"""Build every project NBNK mod Bank from Markdown mapping tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
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


class BuildError(Exception):
    """A user-actionable build failure."""


@dataclass
class Replacement:
    """One mapping row that replaces a DIDX entry."""

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
class BankPlan:
    """A source Bank and its parsed replacement plan."""

    source: Path
    mapping: MappingInfo | None
    original_bank: Any
    staged: Path | None = None


@dataclass(frozen=True)
class ToolPaths:
    """Project tools used by the build and validation pipeline."""

    media: Path
    converter: Path
    pyvgmstream: Path
    wwiser: Path


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
            raise BuildError(f"{path}:{line_number}: original audio does not exist: {original_path}")

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
            raise BuildError(f"{path}:{line_number}: Audio file does not exist: {source_audio}")

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


def resolve_project_path(project_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def load_media_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_mod_media", path)
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
    tools_root = project_root / ".agents" / "skills" / "soundbank-workflow"
    paths = ToolPaths(
        media=tools_root / "scripts" / "nbnk_media.py",
        converter=tools_root / "scripts" / "wav_to_wem.py",
        pyvgmstream=project_root / "tools" / "pyvgmstream" / "pyvgmstream.py",
        wwiser=project_root / "tools" / "wwiser" / "wwiser.py",
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
            "ffmpeg was not found on PATH; run the skill in the project conda environment"
        )
    return paths


def load_bank(media_module: ModuleType, path: Path) -> Any:
    try:
        return media_module.read_bank(path)
    except Exception as error:
        raise BuildError(f"Could not read Bank {path}: {error}") from error


def prepare_plans(
    project_root: Path,
    mapping_dir: Path,
    soundbank_dir: Path,
    media_module: ModuleType,
) -> tuple[list[MappingInfo], list[BankPlan]]:
    mapping_paths = sorted(mapping_dir.glob("*.md"))
    if not mapping_paths:
        raise BuildError(f"No Markdown mapping tables found in {mapping_dir}")
    bank_paths = sorted(soundbank_dir.glob("*.nbnk"))
    if not bank_paths:
        raise BuildError(f"No .nbnk source Banks found in {soundbank_dir}")

    mappings = [parse_mapping(path, project_root) for path in mapping_paths]
    mapping_by_name: dict[str, MappingInfo] = {}
    for mapping in mappings:
        if mapping.bank_name in mapping_by_name:
            raise BuildError(f"Duplicate mapping for Bank {mapping.bank_name}")
        mapping_by_name[mapping.bank_name] = mapping

    plans: list[BankPlan] = []
    for mapping in mappings:
        source = soundbank_dir / f"{mapping.bank_name}.nbnk"
        if not source.is_file():
            raise BuildError(
                f"{mapping.path}: matching source Bank does not exist: {source}"
            )

    for source in bank_paths:
        original_bank = load_bank(media_module, source)
        mapping = mapping_by_name.get(source.stem)
        if mapping:
            for replacement in mapping.replacements:
                if not 1 <= replacement.index <= len(original_bank.entries):
                    raise BuildError(
                        f"{mapping.path}:{replacement.line_number}: DIDX index "
                        f"{replacement.index} is outside {source.name}'s range "
                        f"1..{len(original_bank.entries)}"
                    )
                replacement.media_id = original_bank.entries[replacement.index - 1].media_id
        plans.append(BankPlan(source=source, mapping=mapping, original_bank=original_bank))

    return mappings, plans


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
) -> None:
    if plan.mapping is None:
        return
    converted_dir.mkdir(parents=True, exist_ok=True)
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
            media_module.validate_wem(wem_path)
        except Exception as error:
            raise BuildError(f"Converted WEM is invalid: {wem_path}: {error}") from error
        replacement.wem_path = wem_path


def validate_stage(
    plan: BankPlan,
    stage: Path,
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths,
    media_module: ModuleType,
) -> None:
    validation_dir.mkdir(parents=True, exist_ok=True)
    staged_bank = load_bank(media_module, stage)
    if plan.mapping is None or not plan.mapping.replacements:
        if stage.read_bytes() != plan.source.read_bytes():
            raise BuildError(f"Unmapped Bank was changed unexpectedly: {stage}")
        for entry in staged_bank.entries:
            if entry.offset % media_module.ALIGNMENT:
                raise BuildError(f"Bank contains an unaligned DIDX entry: {stage}")
    else:
        replacement_payloads: dict[int, bytes] = {}
        for replacement in plan.mapping.replacements:
            if replacement.wem_path is None:
                raise BuildError(f"Missing converted WEM for DIDX #{replacement.index}")
            replacement_payloads[replacement.index - 1] = replacement.wem_path.read_bytes()
        try:
            media_module.verify_rebuild(plan.original_bank, staged_bank, replacement_payloads)
        except Exception as error:
            raise BuildError(
                f"NBNK read-back verification failed for {stage}: {error}"
            ) from error

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

    if plan.mapping is None:
        return
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


def build_bank(
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
    if plan.mapping is not None and plan.mapping.replacements:
        convert_replacements(plan, converted_dir, project_root, tools, media_module)
        command = [
            sys.executable,
            str(tools.media),
            "replace",
            str(plan.source),
            str(stage),
            "--force",
        ]
        for replacement in plan.mapping.replacements:
            if replacement.wem_path is None:
                raise BuildError(f"Missing converted WEM for DIDX #{replacement.index}")
            command.extend(
                ["--replace", f"{replacement.index}={replacement.wem_path}"]
            )
        run_tool(command, f"rebuild {plan.source.name}", project_root)
    else:
        shutil.copy2(plan.source, stage)

    validate_stage(plan, stage, validation_dir, project_root, tools, media_module)
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


def print_preflight(mappings: list[MappingInfo], plans: list[BankPlan]) -> None:
    print(f"Mapping tables: {len(mappings)}")
    print(f"Source Banks: {len(plans)}")
    for mapping in mappings:
        replacements = ", ".join(
            f"#{item.index} (Media ID {item.media_id})"
            for item in mapping.replacements
        ) or "none"
        print(
            f"  {mapping.path.name}: {mapping.data_rows} rows, "
            f"replacements={replacements}"
        )
        for unresolved in mapping.unresolved_rows:
            print(f"  warning: {unresolved}")
    for plan in plans:
        if plan.mapping is None:
            print(f"  {plan.source.name}: no mapping table; copy unchanged")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and validate all project NBNK mod Banks."
    )
    parser.add_argument("--root", type=Path, help="Project root; auto-detected by default")
    parser.add_argument(
        "--mapping-dir",
        default="mapping",
        help="Mapping directory relative to root",
    )
    parser.add_argument(
        "--soundbank-dir",
        default="original/soundbank",
        help="Original SoundBank directory relative to root",
    )
    parser.add_argument(
        "--release-dir",
        default="release",
        help="Release directory; relative to root unless absolute",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run preflight checks without converting, rebuilding, or publishing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        project_root = find_project_root(args.root)
        mapping_dir = resolve_project_path(project_root, args.mapping_dir)
        soundbank_dir = resolve_project_path(project_root, args.soundbank_dir)
        release_dir = resolve_project_path(project_root, args.release_dir)
        tools = make_tool_paths(project_root)
        media_module = load_media_module(tools.media)
        mappings, plans = prepare_plans(
            project_root, mapping_dir, soundbank_dir, media_module
        )
        print_preflight(mappings, plans)

        if args.dry_run:
            print("Dry run complete; no output files were written.")
            return 0

        with tempfile.TemporaryDirectory(prefix="build-nbnk-mod.") as temporary:
            task_dir = Path(temporary)
            stage_dir = task_dir / "banks"
            converted_dir = task_dir / "converted"
            validation_dir = task_dir / "validation"
            for plan in plans:
                build_bank(
                    plan,
                    stage_dir,
                    converted_dir,
                    validation_dir,
                    project_root,
                    tools,
                    media_module,
                )

            for plan in plans:
                if plan.staged is None:
                    raise BuildError(f"Bank was not staged: {plan.source}")
                target = release_dir / plan.source.name
                atomic_publish(plan.staged, target)
                replacement_summary = "none"
                if plan.mapping and plan.mapping.replacements:
                    replacement_summary = ", ".join(
                        f"#{item.index}/Media ID {item.media_id}"
                        for item in plan.mapping.replacements
                    )
                print(
                    f"Published {target} | SHA-256 {sha256(plan.staged)} | "
                    f"replacements: {replacement_summary}"
                )
        print(f"Build complete: {len(plans)} Banks published to {release_dir}")
        return 0
    except BuildError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
