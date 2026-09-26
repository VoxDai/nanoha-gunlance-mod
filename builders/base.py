#!/usr/bin/env python3
"""Explicit artifact plans, guarded builds, validation, and publication."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import difflib
import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import uuid
import wave

from tools import soundbank_editor


NAME_RE = re.compile(r"[a-z0-9_]+")
DESIGN_ID_RE = re.compile(r"[a-z0-9_]+(?:\.[a-z0-9_]+)+")
SHA256_RE = re.compile(r"[0-9a-fA-F]{64}")

__all__ = (
    "ArtifactBuildPlan",
    "BuildError",
    "BuildResult",
    "BundleValidator",
    "HircBankBuildPlan",
    "HircBankEditSummary",
    "LmtBuildPlan",
    "MediaAddition",
    "MediaReplacement",
    "ModBuildPlan",
    "ReferenceInput",
    "SoundBankBuildPlan",
    "WwevBuildPlan",
    "build_all",
    "build_one",
    "prepare_all_plans",
    "prepare_plan",
    "publish_release_tree",
    "run_all_cli",
    "run_single_cli",
    "validate_registry",
)


class BuildError(Exception):
    """A user-actionable build failure."""


def _u32(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"{label} must be an unsigned 32-bit integer: {value!r}")
    return value


def _positive_index(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive integer: {value!r}")
    return value


def _declared_path(
    value: Path | str,
    label: str,
    *,
    suffix: str,
    target: bool = False,
) -> Path:
    if not isinstance(value, (Path, str)):
        raise TypeError(f"{label} must be a path")
    raw = str(value)
    path = Path(raw)
    if (
        not raw
        or raw != raw.strip()
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in path.parts)
        or "\\" in raw
    ):
        raise ValueError(f"{label} must be a safe project-relative path: {value!r}")
    if target and path.parts[0].casefold() == "nativepc":
        raise ValueError(f"{label} is relative to nativePC and must not include it")
    if path.suffix.casefold() != suffix:
        raise ValueError(f"{label} must end in {suffix}: {path}")
    return path


def _sha256_guard(value: str, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be a 64-character hexadecimal SHA-256")
    return value.casefold()


def _plan_identity(
    name: str,
    design_ids: tuple[str, ...],
    apply_edits: object,
) -> None:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid artifact builder name: {name!r}")
    if not isinstance(design_ids, tuple) or not design_ids:
        raise TypeError("design_ids must be a non-empty tuple")
    if any(not isinstance(item, str) or not DESIGN_ID_RE.fullmatch(item) for item in design_ids):
        raise ValueError(f"Invalid design ID in {design_ids!r}")
    if len(design_ids) != len(set(design_ids)):
        raise ValueError(f"Duplicate design ID in {name}: {design_ids!r}")
    if not callable(apply_edits):
        raise TypeError("apply_edits must be callable")


@dataclass(frozen=True)
class MediaReplacement:
    """Replace one existing 1-based DIDX entry with converted project audio."""

    index: int
    expected_media_id: int
    source_audio: Path
    wem_channels: int = 2

    def __post_init__(self) -> None:
        _positive_index(self.index, "media replacement index")
        _u32(self.expected_media_id, "expected Media ID")
        object.__setattr__(
            self,
            "source_audio",
            _declared_path(self.source_audio, "source audio", suffix=".wav"),
        )
        if (
            not isinstance(self.wem_channels, int)
            or isinstance(self.wem_channels, bool)
            or self.wem_channels not in (1, 2)
        ):
            raise ValueError("wem_channels must be 1 or 2")


@dataclass(frozen=True)
class MediaAddition:
    """Append one media entry at an explicitly guarded 1-based DIDX index."""

    expected_index: int
    media_id: int
    source_audio: Path
    wem_channels: int = 2

    def __post_init__(self) -> None:
        _positive_index(self.expected_index, "expected added media index")
        _u32(self.media_id, "added Media ID")
        object.__setattr__(
            self,
            "source_audio",
            _declared_path(self.source_audio, "source audio", suffix=".wav"),
        )
        if (
            not isinstance(self.wem_channels, int)
            or isinstance(self.wem_channels, bool)
            or self.wem_channels not in (1, 2)
        ):
            raise ValueError("wem_channels must be 1 or 2")


@dataclass(frozen=True)
class ReferenceInput:
    """One immutable project input used to guard a cross-Bank build contract."""

    path: Path
    expected_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, (Path, str)):
            raise TypeError("reference input must be a path")
        raw = str(self.path)
        path = Path(raw)
        if (
            not raw
            or raw != raw.strip()
            or path.is_absolute()
            or any(part in ("", ".", "..") for part in path.parts)
            or "\\" in raw
            or not path.parts
            or path.parts[0] != "original"
        ):
            raise ValueError(
                f"reference input must be a safe path below original/: {self.path!r}"
            )
        object.__setattr__(self, "path", path)
        object.__setattr__(
            self,
            "expected_sha256",
            _sha256_guard(self.expected_sha256, "reference input SHA-256"),
        )


SoundBankEditHook = Callable[[soundbank_editor.SoundBankEditor], None]
LmtEditHook = Callable[[soundbank_editor.LmtEditor], None]
WwevEditHook = Callable[[soundbank_editor.WwevEditor], None]


@dataclass(frozen=True)
class SoundBankBuildPlan:
    """Complete build contract for one NBNK artifact."""

    name: str
    design_ids: tuple[str, ...]
    source: Path
    target: Path
    expected_source_sha256: str
    expected_bank_id: int
    apply_edits: SoundBankEditHook
    expected_summary: soundbank_editor.SoundBankEditSummary
    media_replacements: tuple[MediaReplacement, ...] = ()
    media_additions: tuple[MediaAddition, ...] = ()
    reference_inputs: tuple[ReferenceInput, ...] = ()
    external_stop_references: tuple[soundbank_editor.ExternalStopReference, ...] = ()

    def __post_init__(self) -> None:
        _plan_identity(self.name, self.design_ids, self.apply_edits)
        object.__setattr__(
            self, "source", _declared_path(self.source, "source Bank", suffix=".nbnk")
        )
        object.__setattr__(
            self,
            "target",
            _declared_path(self.target, "target Bank", suffix=".nbnk", target=True),
        )
        object.__setattr__(
            self,
            "expected_source_sha256",
            _sha256_guard(self.expected_source_sha256, "source Bank SHA-256"),
        )
        _u32(self.expected_bank_id, "expected Bank ID")
        if not isinstance(self.expected_summary, soundbank_editor.SoundBankEditSummary):
            raise TypeError("expected_summary must be SoundBankEditSummary")
        if not isinstance(self.media_replacements, tuple) or any(
            not isinstance(item, MediaReplacement) for item in self.media_replacements
        ):
            raise TypeError("media_replacements must be a tuple of MediaReplacement")
        if not isinstance(self.media_additions, tuple) or any(
            not isinstance(item, MediaAddition) for item in self.media_additions
        ):
            raise TypeError("media_additions must be a tuple of MediaAddition")
        if not isinstance(self.reference_inputs, tuple) or any(
            not isinstance(item, ReferenceInput) for item in self.reference_inputs
        ):
            raise TypeError("reference_inputs must be a tuple of ReferenceInput")
        if not isinstance(self.external_stop_references, tuple) or any(
            not isinstance(item, soundbank_editor.ExternalStopReference)
            for item in self.external_stop_references
        ):
            raise TypeError("external_stop_references must be a tuple of ExternalStopReference")
        external_ids = [ref.action_id for ref in self.external_stop_references]
        if len(external_ids) != len(set(external_ids)):
            raise ValueError(f"{self.name}: duplicate external Stop Action declaration")
        if any(ref.target_bank_id == self.expected_bank_id for ref in self.external_stop_references):
            raise ValueError(f"{self.name}: external Stop target Bank must differ")
        replacement_indices = [item.index for item in self.media_replacements]
        addition_indices = [item.expected_index for item in self.media_additions]
        media_ids = [item.media_id for item in self.media_additions]
        if len(replacement_indices) != len(set(replacement_indices)):
            raise ValueError(f"{self.name}: duplicate media replacement index")
        if len(addition_indices) != len(set(addition_indices)):
            raise ValueError(f"{self.name}: duplicate media addition index")
        if set(replacement_indices) & set(addition_indices):
            raise ValueError(f"{self.name}: replacement and addition indices overlap")
        if len(media_ids) != len(set(media_ids)):
            raise ValueError(f"{self.name}: duplicate added Media ID")
        reference_paths = [item.path for item in self.reference_inputs]
        if len(reference_paths) != len(set(reference_paths)):
            raise ValueError(f"{self.name}: duplicate reference input")


@dataclass(frozen=True)
class HircBankEditSummary:
    """Exact edit report for a media-less v120 event Bank."""

    added_hirc_objects: tuple[tuple[int, int], ...]
    changed_byte_count: int
    resized_hirc_objects: tuple[tuple[int, int, int, int], ...]
    hirc_size_delta: int


@dataclass(frozen=True)
class HircBankBuildPlan:
    """Build a BKHD/HIRC-only Bank while retaining every original chunk."""

    name: str
    design_ids: tuple[str, ...]
    source: Path
    target: Path
    expected_source_sha256: str
    expected_bank_id: int
    apply_edits: Callable[[soundbank_editor.HircEditor], None]
    expected_summary: HircBankEditSummary

    def __post_init__(self) -> None:
        _plan_identity(self.name, self.design_ids, self.apply_edits)
        object.__setattr__(self, "source", _declared_path(self.source, "source Bank", suffix=".nbnk"))
        object.__setattr__(self, "target", _declared_path(self.target, "target Bank", suffix=".nbnk", target=True))
        object.__setattr__(self, "expected_source_sha256",
                           _sha256_guard(self.expected_source_sha256, "source Bank SHA-256"))
        _u32(self.expected_bank_id, "expected Bank ID")
        if not isinstance(self.expected_summary, HircBankEditSummary):
            raise TypeError("expected_summary must be HircBankEditSummary")


@dataclass(frozen=True)
class HircBank:
    """Losslessly parsed media-less Bank; only its HIRC chunk may change."""

    chunks: tuple[soundbank_editor.Chunk, ...]
    version: int
    bank_id: int

    @classmethod
    def from_bytes(cls, data: bytes) -> HircBank:
        chunks = []
        position = 0
        while position < len(data):
            if position + 8 > len(data):
                raise BuildError("media-less Bank has a truncated chunk header")
            tag, size = struct.unpack_from("<4sI", data, position)
            end = position + 8 + size
            if end > len(data):
                raise BuildError(f"media-less Bank chunk {tag!r} exceeds file length")
            chunks.append(soundbank_editor.Chunk(tag, position, data[position + 8:end], data[position:end]))
            position = end
        if tuple(chunk.tag for chunk in chunks) != (b"BKHD", b"HIRC"):
            raise BuildError("media-less Bank must contain exactly BKHD and HIRC chunks")
        if len(chunks[0].payload) < 8:
            raise BuildError("media-less Bank BKHD is too short")
        version, bank_id = struct.unpack_from("<II", chunks[0].payload)
        if version != soundbank_editor.SUPPORTED_EDIT_VERSION:
            raise BuildError(f"media-less Bank requires Wwise v120, found v{version}")
        soundbank_editor.HircEditor(chunks[1].payload, version=version)
        return cls(tuple(chunks), version, bank_id)

    @property
    def hirc_payload(self) -> bytes:
        return self.chunks[1].payload

    def with_hirc(self, payload: bytes) -> bytes:
        return self.chunks[0].raw + b"HIRC" + struct.pack("<I", len(payload)) + payload


def _edit_hirc_bank(
        plan: HircBankBuildPlan, original: HircBank,
) -> tuple[bytes, HircBankEditSummary]:
    editor = soundbank_editor.HircEditor(original.hirc_payload, version=original.version)
    original_objects = tuple((o.object_type, o.object_id, o.body) for o in editor.objects())
    plan.apply_edits(editor)
    payload = editor.build()
    rebuilt = HircBank.from_bytes(original.with_hirc(payload))
    reread = soundbank_editor.HircEditor(rebuilt.hirc_payload, version=rebuilt.version)
    added = set(editor.added_objects)
    retained = tuple((o.object_type, o.object_id, o.body) for o in reread.objects()
                     if (o.object_type, o.object_id) not in added)
    if retained != original_objects:
        raise BuildError(f"{plan.name}: original HIRC objects changed or reordered")
    if rebuilt.chunks[0].raw != original.chunks[0].raw:
        raise BuildError(f"{plan.name}: original BKHD changed")
    if tuple((o.object_type, o.object_id, o.body) for o in reread.objects()) != tuple(
            (o.object_type, o.object_id, o.body) for o in editor.objects()
    ):
        raise BuildError(f"{plan.name}: HIRC read-back differs")
    summary = HircBankEditSummary(editor.added_objects, editor.changed_byte_count,
                                  editor.resized_objects, len(payload) - len(original.hirc_payload))
    if summary != plan.expected_summary:
        raise _summary_mismatch(plan.name, plan.expected_summary, summary)
    return original.with_hirc(payload), summary


@dataclass(frozen=True)
class LmtBuildPlan:
    """Complete build contract for one MHW LMT v95 artifact."""

    name: str
    design_ids: tuple[str, ...]
    source: Path
    target: Path
    expected_source_sha256: str
    apply_edits: LmtEditHook
    expected_summary: soundbank_editor.LmtEditSummary

    def __post_init__(self) -> None:
        _plan_identity(self.name, self.design_ids, self.apply_edits)
        object.__setattr__(
            self, "source", _declared_path(self.source, "source LMT", suffix=".lmt")
        )
        object.__setattr__(
            self,
            "target",
            _declared_path(self.target, "target LMT", suffix=".lmt", target=True),
        )
        object.__setattr__(
            self,
            "expected_source_sha256",
            _sha256_guard(self.expected_source_sha256, "source LMT SHA-256"),
        )
        if not isinstance(self.expected_summary, soundbank_editor.LmtEditSummary):
            raise TypeError("expected_summary must be LmtEditSummary")


@dataclass(frozen=True)
class WwevBuildPlan:
    """Complete build contract for one MHW WWEV v19 artifact."""

    name: str
    design_ids: tuple[str, ...]
    source: Path
    target: Path
    expected_source_sha256: str
    apply_edits: WwevEditHook
    expected_summary: soundbank_editor.WwevEditSummary

    def __post_init__(self) -> None:
        _plan_identity(self.name, self.design_ids, self.apply_edits)
        object.__setattr__(
            self, "source", _declared_path(self.source, "source WWEV", suffix=".wwev")
        )
        object.__setattr__(
            self,
            "target",
            _declared_path(self.target, "target WWEV", suffix=".wwev", target=True),
        )
        object.__setattr__(
            self,
            "expected_source_sha256",
            _sha256_guard(self.expected_source_sha256, "source WWEV SHA-256"),
        )
        if not isinstance(self.expected_summary, soundbank_editor.WwevEditSummary):
            raise TypeError("expected_summary must be WwevEditSummary")


ArtifactBuildPlan = SoundBankBuildPlan | HircBankBuildPlan | LmtBuildPlan | WwevBuildPlan
ArtifactSummary = (
    soundbank_editor.SoundBankEditSummary
    | HircBankEditSummary
    | soundbank_editor.LmtEditSummary
    | soundbank_editor.WwevEditSummary
)
BundleValidationHook = Callable[[Mapping[Path, Path]], None]


@dataclass(frozen=True)
class BundleValidator:
    """One cross-artifact invariant evaluated against the staged nativePC tree."""

    name: str
    design_id: str
    validate: BundleValidationHook

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not NAME_RE.fullmatch(self.name):
            raise ValueError(f"Invalid bundle validator name: {self.name!r}")
        if not isinstance(self.design_id, str) or not DESIGN_ID_RE.fullmatch(self.design_id):
            raise ValueError(f"Invalid bundle validator design ID: {self.design_id!r}")
        if not callable(self.validate):
            raise TypeError("bundle validator validate must be callable")


@dataclass(frozen=True)
class ModBuildPlan:
    """The complete, transactionally published mod artifact set."""

    artifacts: tuple[ArtifactBuildPlan, ...]
    validators: tuple[BundleValidator, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.artifacts, tuple) or not self.artifacts:
            raise TypeError("artifacts must be a non-empty tuple")
        if any(
                not isinstance(item, (SoundBankBuildPlan, HircBankBuildPlan, LmtBuildPlan, WwevBuildPlan))
            for item in self.artifacts
        ):
            raise TypeError("artifacts contains an unsupported plan")
        if not isinstance(self.validators, tuple) or any(
            not isinstance(item, BundleValidator) for item in self.validators
        ):
            raise TypeError("validators must be a tuple of BundleValidator")


@dataclass(frozen=True)
class ToolPaths:
    """Project tools used by NBNK conversion and deep validation."""

    converter: Path
    pyvgmstream: Path
    wwiser: Path


@dataclass
class PreparedArtifact:
    """One source-verified artifact ready to build in a task directory."""

    plan: ArtifactBuildPlan
    source: Path
    original: (
        soundbank_editor.SoundBank
        | HircBank
        | soundbank_editor.LmtFile
        | soundbank_editor.WwevFile
    )
    preview_summary: ArtifactSummary
    staged: Path | None = None


@dataclass(frozen=True)
class BuildResult:
    """One published artifact and its verified observable metadata."""

    name: str
    target: Path
    path: Path
    sha256: str
    summary: ArtifactSummary


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


def resolve_project_path(project_root: Path, value: Path | str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def _resolve_declared(project_root: Path, path: Path, label: str) -> Path:
    resolved = (project_root / path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise BuildError(f"{label} resolves outside the project root: {path}") from error
    return resolved


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    paths = ToolPaths(
        converter=tools_root / "utils" / "wav_to_wem.py",
        pyvgmstream=tools_root / "utils" / "pyvgmstream.py",
        wwiser=tools_root / "wwiser" / "wwiser.py",
    )
    missing = [str(path) for path in paths.__dict__.values() if not path.is_file()]
    if missing:
        raise BuildError("Required project tools are missing:\n" + "\n".join(missing))
    if shutil.which("ffmpeg") is None:
        raise BuildError(
            "ffmpeg was not found on PATH; run the builder in the project conda environment"
        )
    return paths


def _verify_source(plan: ArtifactBuildPlan, project_root: Path) -> Path:
    source = _resolve_declared(project_root, plan.source, f"{plan.name} source")
    if not source.is_file():
        raise BuildError(f"{plan.name}: source artifact does not exist: {source}")
    actual = sha256(source)
    if actual != plan.expected_source_sha256:
        raise BuildError(
            f"{plan.name}: source SHA-256 expected {plan.expected_source_sha256} "
            f"but found {actual}: {source}"
        )
    return source


def _verify_audio_sources(plan: SoundBankBuildPlan, project_root: Path) -> None:
    for edit in (*plan.media_replacements, *plan.media_additions):
        source = _resolve_declared(
            project_root, edit.source_audio, f"{plan.name} source audio"
        )
        if not source.is_file():
            raise BuildError(f"{plan.name}: source audio does not exist: {source}")
        try:
            with wave.open(str(source), "rb") as wav:
                channels = wav.getnchannels()
                sample_rate = wav.getframerate()
                sample_width = wav.getsampwidth()
                compression = wav.getcomptype()
        except (OSError, EOFError, wave.Error) as error:
            raise BuildError(
                f"{plan.name}: source audio is not a readable PCM WAV: {source}"
            ) from error
        if (
            channels != 2
            or sample_rate != 48_000
            or sample_width not in (2, 3)
            or compression != "NONE"
        ):
            raise BuildError(
                f"{plan.name}: source audio must be 48 kHz stereo PCM at 16/24-bit; "
                f"found {sample_rate} Hz, {channels} channel(s), "
                f"{sample_width * 8}-bit, compression={compression}: {source}"
            )


def _verify_reference_inputs(plan: SoundBankBuildPlan, project_root: Path) -> None:
    for reference in plan.reference_inputs:
        source = _resolve_declared(
            project_root, reference.path, f"{plan.name} reference input"
        )
        if not source.is_file():
            raise BuildError(f"{plan.name}: reference input does not exist: {source}")
        actual = sha256(source)
        if actual != reference.expected_sha256:
            raise BuildError(
                f"{plan.name}: reference input SHA-256 expected "
                f"{reference.expected_sha256} but found {actual}: {source}"
            )


def _summary_mismatch(name: str, expected: ArtifactSummary, actual: ArtifactSummary) -> BuildError:
    return BuildError(
        f"{name}: edit summary differs from the reviewed build plan\n"
        f"expected: {expected!r}\nactual:   {actual!r}"
    )


def _verify_declared_soundbank_media(
    plan: SoundBankBuildPlan,
    summary: soundbank_editor.SoundBankEditSummary,
) -> None:
    declared_replacements = tuple(
        (item.index, item.expected_media_id) for item in plan.media_replacements
    )
    declared_additions = tuple(
        (item.expected_index, item.media_id) for item in plan.media_additions
    )
    if summary.replaced_media != declared_replacements:
        raise BuildError(
            f"{plan.name}: apply_edits must not add undeclared media replacements; "
            f"declared {declared_replacements}, found {summary.replaced_media}"
        )
    if summary.added_media != declared_additions:
        raise BuildError(
            f"{plan.name}: apply_edits must not add undeclared media additions; "
            f"declared {declared_additions}, found {summary.added_media}"
        )


def _preview_soundbank(
    plan: SoundBankBuildPlan, bank: soundbank_editor.SoundBank
) -> soundbank_editor.SoundBankEditSummary:
    editor = soundbank_editor.SoundBankEditor(
        bank, external_stop_references=plan.external_stop_references,
    )
    try:
        for replacement in plan.media_replacements:
            editor.replace_media(
                bank.extract_media(index=replacement.index),
                index=replacement.index,
                expected_media_id=replacement.expected_media_id,
            )
        if plan.media_additions and not bank.entries:
            raise BuildError(f"{plan.name}: cannot preview additions for an empty Bank")
        placeholder = bank.extract_media(index=1) if plan.media_additions else b""
        for addition in plan.media_additions:
            editor.append_media(addition.media_id, placeholder)
        plan.apply_edits(editor)
        editor.validate()
    except soundbank_editor.EditorError as error:
        raise BuildError(f"{plan.name}: invalid SoundBank edit plan: {error}") from error
    _verify_declared_soundbank_media(plan, editor.summary)
    if editor.summary != plan.expected_summary:
        raise _summary_mismatch(plan.name, plan.expected_summary, editor.summary)
    return editor.summary


def prepare_plan(plan: ArtifactBuildPlan, project_root: Path) -> PreparedArtifact:
    """Verify one explicit plan, all immutable guards, and its exact edit summary."""

    source = _verify_source(plan, project_root)
    try:
        if isinstance(plan, SoundBankBuildPlan):
            _verify_reference_inputs(plan, project_root)
            _verify_audio_sources(plan, project_root)
            original = soundbank_editor.SoundBank.from_file(source)
            if original.bank_id != plan.expected_bank_id:
                raise BuildError(
                    f"{plan.name}: expected Bank ID {plan.expected_bank_id} "
                    f"but found {original.bank_id}"
                )
            for edit in plan.media_replacements:
                if edit.index > len(original.entries):
                    raise BuildError(
                        f"{plan.name}: replacement DIDX #{edit.index} is outside "
                        f"1..{len(original.entries)}"
                    )
                actual_id = original.entries[edit.index - 1].media_id
                if actual_id != edit.expected_media_id:
                    raise BuildError(
                        f"{plan.name}: DIDX #{edit.index} expected Media ID "
                        f"{edit.expected_media_id} but found {actual_id}"
                    )
            expected_indices = tuple(
                range(
                    len(original.entries) + 1,
                    len(original.entries) + len(plan.media_additions) + 1,
                )
            )
            actual_indices = tuple(item.expected_index for item in plan.media_additions)
            if actual_indices != expected_indices:
                raise BuildError(
                    f"{plan.name}: added media indices expected {expected_indices} "
                    f"but plan declares {actual_indices}"
                )
            existing_ids = {item.media_id for item in original.entries}
            collisions = sorted(
                item.media_id for item in plan.media_additions if item.media_id in existing_ids
            )
            if collisions:
                raise BuildError(
                    f"{plan.name}: added Media ID already exists: {collisions[0]}"
                )
            summary = _preview_soundbank(plan, original)
        elif isinstance(plan, HircBankBuildPlan):
            original = HircBank.from_bytes(source.read_bytes())
            if original.bank_id != plan.expected_bank_id:
                raise BuildError(f"{plan.name}: expected Bank ID {plan.expected_bank_id} but found {original.bank_id}")
            _, summary = _edit_hirc_bank(plan, original)
        elif isinstance(plan, LmtBuildPlan):
            original = soundbank_editor.LmtFile.from_file(source)
            editor = soundbank_editor.LmtEditor(original)
            plan.apply_edits(editor)
            editor.validate()
            summary = editor.summary
            if summary != plan.expected_summary:
                raise _summary_mismatch(plan.name, plan.expected_summary, summary)
        else:
            original = soundbank_editor.WwevFile.from_file(source)
            editor = soundbank_editor.WwevEditor(original)
            plan.apply_edits(editor)
            editor.validate()
            summary = editor.summary
            if summary != plan.expected_summary:
                raise _summary_mismatch(plan.name, plan.expected_summary, summary)
    except soundbank_editor.EditorError as error:
        raise BuildError(f"{plan.name}: invalid artifact edit plan: {error}") from error
    return PreparedArtifact(plan, source, original, summary)


def validate_registry(mod_plan: ModBuildPlan) -> None:
    """Validate global uniqueness without consulting mapping documentation."""

    artifacts = mod_plan.artifacts
    for label, values in (
        ("builder name", [item.name for item in artifacts]),
        ("source artifact", [item.source for item in artifacts]),
        ("target artifact", [item.target for item in artifacts]),
    ):
        if len(values) != len(set(values)):
            duplicate = next(value for value in values if values.count(value) > 1)
            raise BuildError(f"Duplicate {label}: {duplicate}")
    validator_names = [item.name for item in mod_plan.validators]
    bank_owners: dict[int, list[SoundBankBuildPlan]] = {}
    for plan in artifacts:
        if isinstance(plan, SoundBankBuildPlan):
            bank_owners.setdefault(plan.expected_bank_id, []).append(plan)
    for plan in artifacts:
        if isinstance(plan, SoundBankBuildPlan):
            for ref in plan.external_stop_references:
                if len(bank_owners.get(ref.target_bank_id, ())) != 1:
                    raise BuildError(
                        f"{plan.name}: external Stop target Bank {ref.target_bank_id} "
                        "must have exactly one registered artifact owner"
                    )
    if len(validator_names) != len(set(validator_names)):
        duplicate = next(name for name in validator_names if validator_names.count(name) > 1)
        raise BuildError(f"Duplicate bundle validator: {duplicate}")
    design_ids = {design for artifact in artifacts for design in artifact.design_ids}
    for validator in mod_plan.validators:
        if validator.design_id not in design_ids:
            raise BuildError(
                f"Bundle validator {validator.name} references unregistered design "
                f"{validator.design_id}"
            )


def prepare_all_plans(mod_plan: ModBuildPlan, project_root: Path) -> list[PreparedArtifact]:
    validate_registry(mod_plan)
    return [prepare_plan(plan, project_root) for plan in mod_plan.artifacts]


def _convert_media(
    prepared: PreparedArtifact,
    converted_dir: Path,
    project_root: Path,
    tools: ToolPaths,
) -> dict[tuple[Path, int], bytes]:
    plan = prepared.plan
    if not isinstance(plan, SoundBankBuildPlan):
        return {}
    converted_dir.mkdir(parents=True, exist_ok=True)
    payloads: dict[tuple[Path, int], bytes] = {}
    edits = (*plan.media_replacements, *plan.media_additions)
    for ordinal, edit in enumerate(edits, 1):
        source = _resolve_declared(project_root, edit.source_audio, "source audio")
        key = (source, edit.wem_channels)
        if key in payloads:
            continue
        wem_path = converted_dir / f"{plan.name}_{ordinal:02d}.wem"
        run_tool(
            [
                sys.executable,
                str(tools.converter),
                str(source),
                str(wem_path),
                "--force",
                "--channels",
                str(edit.wem_channels),
            ],
            f"convert {source}",
            project_root,
        )
        try:
            payload = soundbank_editor.validate_wem(wem_path)
        except soundbank_editor.SoundBankError as error:
            raise BuildError(f"Converted WEM is invalid: {wem_path}: {error}") from error
        fmt_offset = payload.find(b"fmt ")
        if fmt_offset < 0 or fmt_offset + 18 > len(payload):
            raise BuildError(f"Converted WEM has no readable fmt chunk: {wem_path}")
        channels = int.from_bytes(payload[fmt_offset + 10 : fmt_offset + 12], "little")
        if channels != edit.wem_channels:
            raise BuildError(
                f"Converted WEM expected {edit.wem_channels} channel(s) but found "
                f"{channels}: {wem_path}"
            )
        payloads[key] = payload
    return payloads


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


def _validate_soundbank_stage(
    prepared: PreparedArtifact,
    editor: soundbank_editor.SoundBankEditor,
    stage: Path,
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths,
) -> None:
    validation_dir.mkdir(parents=True, exist_ok=True)
    try:
        staged_bank = soundbank_editor.SoundBank.from_file(stage)
        expected_bank = editor.validate()
    except soundbank_editor.SoundBankError as error:
        raise BuildError(f"{stage.name}: SoundBank read-back failed: {error}") from error
    if stage.read_bytes() != editor.build() or staged_bank.to_bytes() != expected_bank.to_bytes():
        raise BuildError(f"{stage.name}: staged bytes do not match the editor result")

    summary = editor.summary
    diff = editor.diff()
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

    run_tool(
        [sys.executable, str(tools.wwiser), "-d", "none", str(stage)],
        f"wwiser {stage.name}",
        validation_dir,
    )
    if b"HIRC" in allowed_chunks:
        _write_wwiser_hirc_diff(
            prepared.source, stage, validation_dir, tools, project_root
        )

    extract_dir = validation_dir / "extracted"
    decode_dir = validation_dir / "decoded"
    extract_dir.mkdir(parents=True, exist_ok=True)
    decode_dir.mkdir(parents=True, exist_ok=True)
    for index, media_id in (*summary.replaced_media, *summary.added_media):
        extracted = extract_dir / f"{prepared.plan.name}_{index:03d}_{media_id}.wem"
        decoded = decode_dir / f"{prepared.plan.name}_{index:03d}_{media_id}.wav"
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


def build_plan(
    prepared: PreparedArtifact,
    nativepc_dir: Path,
    converted_dir: Path,
    validation_dir: Path,
    project_root: Path,
    tools: ToolPaths | None,
) -> Path:
    """Build and read back one artifact below a temporary nativePC tree."""

    plan = prepared.plan
    stage = nativepc_dir / plan.target
    stage.parent.mkdir(parents=True, exist_ok=True)
    try:
        if isinstance(plan, SoundBankBuildPlan):
            if tools is None:
                raise BuildError(f"{plan.name}: NBNK build tools were not initialized")
            if not isinstance(prepared.original, soundbank_editor.SoundBank):
                raise BuildError(f"{plan.name}: prepared source is not a SoundBank")
            payloads = _convert_media(
                prepared, converted_dir, project_root, tools
            )
            editor = soundbank_editor.SoundBankEditor(
                prepared.original, external_stop_references=plan.external_stop_references,
            )
            for replacement in plan.media_replacements:
                source = _resolve_declared(project_root, replacement.source_audio, "source audio")
                editor.replace_media(
                    payloads[(source, replacement.wem_channels)],
                    index=replacement.index,
                    expected_media_id=replacement.expected_media_id,
                )
            for addition in plan.media_additions:
                source = _resolve_declared(project_root, addition.source_audio, "source audio")
                editor.append_media(
                    addition.media_id,
                    payloads[(source, addition.wem_channels)],
                )
            plan.apply_edits(editor)
            editor.validate()
            _verify_declared_soundbank_media(plan, editor.summary)
            if editor.summary != plan.expected_summary:
                raise _summary_mismatch(plan.name, plan.expected_summary, editor.summary)
            atomic_write(stage, editor.build())
            _validate_soundbank_stage(
                prepared, editor, stage, validation_dir, project_root, tools
            )
        elif isinstance(plan, HircBankBuildPlan):
            if not isinstance(prepared.original, HircBank):
                raise BuildError(f"{plan.name}: prepared source is not a media-less Bank")
            payload, summary = _edit_hirc_bank(plan, prepared.original)
            if summary != prepared.preview_summary:
                raise _summary_mismatch(plan.name, prepared.preview_summary, summary)
            atomic_write(stage, payload)
            if stage.read_bytes() != payload:
                raise BuildError(f"{plan.name}: staged Bank failed byte-exact read-back")
            if tools is not None:
                validation_dir.mkdir(parents=True, exist_ok=True)
                run_tool([sys.executable, str(tools.wwiser), "-d", "none", str(stage)],
                         f"wwiser {stage.name}", validation_dir)
        elif isinstance(plan, LmtBuildPlan):
            if not isinstance(prepared.original, soundbank_editor.LmtFile):
                raise BuildError(f"{plan.name}: prepared source is not an LMT")
            editor = soundbank_editor.LmtEditor(prepared.original)
            plan.apply_edits(editor)
            editor.write_atomic(stage)
            if editor.summary != plan.expected_summary:
                raise _summary_mismatch(plan.name, plan.expected_summary, editor.summary)
            if soundbank_editor.LmtFile.from_file(stage).to_bytes() != editor.build():
                raise BuildError(f"{plan.name}: staged LMT failed byte-exact read-back")
        else:
            if not isinstance(prepared.original, soundbank_editor.WwevFile):
                raise BuildError(f"{plan.name}: prepared source is not a WWEV")
            editor = soundbank_editor.WwevEditor(prepared.original)
            plan.apply_edits(editor)
            editor.write_atomic(stage)
            if editor.summary != plan.expected_summary:
                raise _summary_mismatch(plan.name, plan.expected_summary, editor.summary)
            if soundbank_editor.WwevFile.from_file(stage).to_bytes() != editor.build():
                raise BuildError(f"{plan.name}: staged WWEV failed byte-exact read-back")
    except soundbank_editor.EditorError as error:
        raise BuildError(f"{plan.name}: artifact build failed: {error}") from error
    prepared.staged = stage
    return stage


def _safe_publish_root(project_root: Path, target: Path) -> None:
    resolved = target.resolve()
    if resolved == Path(resolved.anchor) or resolved == project_root.resolve():
        raise BuildError(f"Refusing broad publication target: {target}")
    protected = (
        project_root / "original",
        project_root / "audio",
        project_root / "assets",
        project_root / "designs",
        project_root / "docs",
    )
    for path in protected:
        try:
            resolved.relative_to(path.resolve())
        except ValueError:
            continue
        raise BuildError(f"Refusing publication inside protected source tree: {target}")


def atomic_publish(source: Path, target: Path, *, force: bool = False) -> None:
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise BuildError(f"Output target is not a regular file: {target}")
    if target.exists() and not force:
        raise BuildError(
            f"Output already exists; add --force after confirming overwrite: {target}"
        )
    atomic_write(target, source.read_bytes())


def publish_release_tree(
    staged_release: Path,
    target_release: Path,
    *,
    project_root: Path,
    force: bool = False,
) -> None:
    """Replace the complete release tree with sibling staging and rollback backup."""

    _safe_publish_root(project_root, target_release)
    if not staged_release.is_dir() or staged_release.is_symlink():
        raise BuildError(f"Staged release tree is invalid: {staged_release}")
    if target_release.is_symlink() or (target_release.exists() and not target_release.is_dir()):
        raise BuildError(f"Release target is not a regular directory: {target_release}")
    if target_release.exists() and not force:
        raise BuildError(
            f"Release already exists; add --force for transactional replacement: "
            f"{target_release}"
        )

    target_release.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    sibling_stage = target_release.parent / f".{target_release.name}.staging-{token}"
    backup = target_release.parent / f".{target_release.name}.backup-{token}"
    try:
        shutil.copytree(staged_release, sibling_stage)
        if target_release.exists():
            os.replace(target_release, backup)
            try:
                os.replace(sibling_stage, target_release)
            except BaseException:
                try:
                    os.replace(backup, target_release)
                except OSError as rollback_error:
                    raise BuildError(
                        f"Release replacement failed and rollback is at {backup}: "
                        f"{rollback_error}"
                    ) from rollback_error
                raise
            shutil.rmtree(backup, ignore_errors=True)
        else:
            os.replace(sibling_stage, target_release)
    finally:
        if sibling_stage.exists() and not sibling_stage.is_symlink():
            shutil.rmtree(sibling_stage, ignore_errors=True)


def _make_result(prepared: PreparedArtifact, path: Path) -> BuildResult:
    return BuildResult(
        name=prepared.plan.name,
        target=prepared.plan.target,
        path=path,
        sha256=sha256(path),
        summary=prepared.preview_summary,
    )


def _print_preflight(prepared: Sequence[PreparedArtifact]) -> None:
    print(f"Artifacts: {len(prepared)}")
    for item in prepared:
        print(
            f"  {item.plan.name}: {item.plan.source} -> nativePC/{item.plan.target} | "
            f"designs={','.join(item.plan.design_ids)} | summary={item.preview_summary!r}"
        )


def _print_result(result: BuildResult) -> None:
    print(
        f"Published {result.path} | SHA-256 {result.sha256} | "
        f"summary={result.summary!r}"
    )


def build_one(
    plan: ArtifactBuildPlan,
    *,
    root: Path | None = None,
    output_dir: Path | str = "output",
    dry_run: bool = False,
    force: bool = False,
) -> BuildResult | None:
    """Fully build and validate one artifact, publishing below output/nativePC."""

    project_root = find_project_root(root)
    prepared = prepare_plan(plan, project_root)
    _print_preflight([prepared])
    output_root = resolve_project_path(project_root, output_dir)
    _safe_publish_root(project_root, output_root)
    target = output_root / "nativePC" / plan.target
    if target.resolve() == prepared.source.resolve():
        raise BuildError(f"Refusing to overwrite source artifact: {target}")
    if not dry_run and target.exists() and not force:
        raise BuildError(
            f"Output already exists; add --force after confirming overwrite: {target}"
        )
    tools = make_tool_paths(project_root) if isinstance(plan, (SoundBankBuildPlan, HircBankBuildPlan)) else None

    with tempfile.TemporaryDirectory(prefix=f"builder-{plan.name}.") as directory:
        task_dir = Path(directory)
        staged = build_plan(
            prepared,
            task_dir / "nativePC",
            task_dir / "converted",
            task_dir / "validation",
            project_root,
            tools,
        )
        if isinstance(plan, SoundBankBuildPlan) and plan.external_stop_references:
            print(
                "External Stop declarations checked locally; companion targets "
                "require the complete Mod build's joint reference validation."
            )
        if dry_run:
            print("Dry run complete; full temporary build passed and no output was published.")
            return None
        atomic_publish(staged, target, force=force)

    result = _make_result(prepared, target)
    _print_result(result)
    return result


def build_all(
    mod_plan: ModBuildPlan,
    *,
    root: Path | None = None,
    release_dir: Path | str = "release",
    dry_run: bool = False,
    force: bool = False,
) -> list[BuildResult]:
    """Build the complete mod and publish one transactionally replaced release tree."""

    project_root = find_project_root(root)
    prepared = prepare_all_plans(mod_plan, project_root)
    _print_preflight(prepared)
    target_release = resolve_project_path(project_root, release_dir)
    _safe_publish_root(project_root, target_release)
    if not dry_run and target_release.exists() and not force:
        raise BuildError(
            f"Release already exists; add --force for transactional replacement: "
            f"{target_release}"
        )
    tools = (
        make_tool_paths(project_root)
        if any(isinstance(item.plan, (SoundBankBuildPlan, HircBankBuildPlan)) for item in prepared)
        else None
    )

    results: list[BuildResult] = []
    with tempfile.TemporaryDirectory(prefix="mod-build.") as directory:
        task_dir = Path(directory)
        staged_release = task_dir / "release"
        nativepc = staged_release / "nativePC"
        staged_paths: dict[Path, Path] = {}
        for item in prepared:
            staged_paths[item.plan.target] = build_plan(
                item,
                nativepc,
                task_dir / "converted" / item.plan.name,
                task_dir / "validation" / item.plan.name,
                project_root,
                tools,
            )
        try:
            soundbank_editor.validate_external_stop_references(
                tuple(
                    soundbank_editor.SoundBank.from_file(staged_paths[item.plan.target])
                    for item in prepared if isinstance(item.plan, SoundBankBuildPlan)
                ),
                {
                    item.plan.expected_bank_id: item.plan.external_stop_references
                    for item in prepared if isinstance(item.plan, SoundBankBuildPlan)
                },
            )
        except soundbank_editor.EditorError as error:
            raise BuildError(f"External Stop reference validation failed: {error}") from error
        for validator in mod_plan.validators:
            try:
                validator.validate(staged_paths)
            except soundbank_editor.EditorError as error:
                raise BuildError(
                    f"Bundle validator {validator.name} failed: {error}"
                ) from error
        if dry_run:
            print(
                "Dry run complete; all artifacts and bundle validators passed in a "
                "temporary release tree."
            )
            return []
        publish_release_tree(
            staged_release,
            target_release,
            project_root=project_root,
            force=force,
        )
        for item in prepared:
            result = _make_result(
                item, target_release / "nativePC" / item.plan.target
            )
            results.append(result)
            _print_result(result)

    print(f"Build complete: {len(results)} artifacts published to {target_release}")
    return results


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, help="Project root; auto-detected by default")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform conversion, editing, and full validation without publication",
    )


def run_single_cli(plan: ArtifactBuildPlan, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"Build and validate the explicit {plan.name} artifact plan."
    )
    _add_common_arguments(parser)
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output root containing nativePC; relative to project root by default",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing output")
    args = parser.parse_args(argv)
    try:
        build_one(
            plan,
            root=args.root,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            force=args.force,
        )
        return 0
    except (BuildError, OSError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


def run_all_cli(mod_plan: ModBuildPlan, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and validate the complete design-driven mod release."
    )
    _add_common_arguments(parser)
    parser.add_argument(
        "--release-dir",
        default="release",
        help="Complete release tree; relative to project root by default",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Transactionally replace an existing complete release tree",
    )
    args = parser.parse_args(argv)
    try:
        build_all(
            mod_plan,
            root=args.root,
            release_dir=args.release_dir,
            dry_run=args.dry_run,
            force=args.force,
        )
        return 0
    except (BuildError, OSError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
