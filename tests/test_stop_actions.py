"""Synthetic regression coverage for v120 Stop authoring and cross-Bank edges."""
from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

from tools import soundbank_editor as se
from builders.base import (
    BuildError, ModBuildPlan, SoundBankBuildPlan, build_all, prepare_plan, validate_registry,
)
from ._soundbank_fixtures import make_test_soundbank


def sound_bank(bank_id: int, sound_id: int, *, kind: int = se.HIRC_SOUND) -> se.SoundBank:
    editor = se.SoundBankEditor.from_bytes(make_test_soundbank(bank_id=bank_id, media_id=99))
    # Minimal synthetic source-bearing body; no original game identity or audio.
    editor.hirc.insert_object(kind, sound_id, bytes(5) + struct.pack("<I", 99))
    return editor.validate()


def source_bank(*, action_type: int = se.ACTION_STOP, target: int = 20) -> se.SoundBank:
    editor = se.SoundBankEditor.from_bytes(make_test_soundbank(bank_id=1))
    body = editor.hirc.create_stop_action(30, target, transition_ms=50)
    body = body[:4] + struct.pack("<H", action_type) + body[6:]
    editor.hirc.insert_object(3, 30, body[4:])
    editor.hirc.insert_object(4, 40, struct.pack("<II", 1, 30))
    return se.SoundBank.from_bytes(editor.build())


def reference(target: se.SoundBank) -> se.ExternalStopReference:
    h = se.HircEditor(target.hirc_payload)
    return se.ExternalStopReference(30, target.bank_id, 20, hashlib.sha256(h.object_body(2, 20)).hexdigest())


class StopConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hirc = se.HircEditor(struct.pack("<I", 0))

    def test_default_explicit_transition_delay_and_curve(self) -> None:
        prefix = struct.pack("<IHI", 30, se.ACTION_STOP, 20)
        self.assertEqual(self.hirc.create_stop_action(30, 20), prefix + bytes.fromhex("0000000400000000"))
        for duration in (0, 50, 200, 0xFFFFFFFF):
            expected = prefix + bytes.fromhex("000110") + struct.pack("<I", duration) + bytes.fromhex("000400000000")
            self.assertEqual(self.hirc.create_stop_action(30, 20, transition_ms=duration), expected)
        expected = prefix + bytes.fromhex("00020f10") + struct.pack("<II", 10, 50) + bytes.fromhex("000800000000")
        self.assertEqual(self.hirc.create_stop_action(30, 20, delay_ms=10, transition_ms=50, fade_curve=8), expected)
        self.assertEqual(self.hirc.object_ids, frozenset())

    def test_numeric_and_version_guards(self) -> None:
        for field in ("delay_ms", "transition_ms"):
            for value in (-1, 1 << 32, True, 0.5):
                with self.subTest(field=field, value=value), self.assertRaises(se.SoundBankError):
                    self.hirc.create_stop_action(30, 20, **{field: value})
        for value in (-1, 9, 256, True):
            with self.assertRaises(se.SoundBankError):
                self.hirc.create_stop_action(30, 20, fade_curve=value)
        for action, target in ((-1, 20), (30, 1 << 32), (True, 20)):
            with self.assertRaises(se.SoundBankError):
                self.hirc.create_stop_action(action, target)
        with self.assertRaises(se.SoundBankError):
            se.HircEditor(struct.pack("<I", 0), version=119).create_stop_action(30, 20)

    def test_append_rejects_shared_action_without_mutating(self) -> None:
        h = se.HircEditor(source_bank().hirc_payload)
        h.insert_object(4, 41, struct.pack("<I", 0))
        before = h.build()
        with self.assertRaisesRegex(se.SoundBankError, "already belongs"):
            h.append_event_action(41, 30, expected_actions=())
        self.assertEqual(h.build(), before)

    def test_final_validation_rejects_low_level_shared_and_duplicate_references(self) -> None:
        target = sound_bank(2, 20)
        for other_event in (True, False):
            e = se.SoundBankEditor(source_bank(), external_stop_references=(reference(target),))
            if other_event:
                e.hirc.insert_object(4, 41, struct.pack("<II", 1, 30))
            else:
                e.hirc.replace_object_body(4, 40, expected=e.hirc.object_body(4, 40), replacement=struct.pack("<IIII", 40, 2, 30, 30), label="synthetic duplicate reference")
            # Inspection remains available even for a runtime-invalid graph.
            self.assertEqual(se.SoundBank.from_bytes(e.build()).to_bytes(), e.build())
            with self.assertRaisesRegex(se.SoundBankError, "already belongs"):
                e.validate()


class ExternalStopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target = sound_bank(2, 20)
        self.source = source_bank()
        self.ref = reference(self.target)

    def test_local_default_is_strict_and_explicit_declaration_is_preserved(self) -> None:
        with self.assertRaisesRegex(se.SoundBankError, "missing object"):
            se.SoundBankEditor(self.source).validate()
        e = se.SoundBankEditor.from_bytes(self.source.to_bytes(), external_stop_references=(self.ref,))
        self.assertEqual(e.external_stop_references, (self.ref,))
        self.assertEqual(e.validate().to_bytes(), self.source.to_bytes())
        self.assertEqual(e.diff().changed_hirc_objects, ())
        with tempfile.TemporaryDirectory() as directory:
            p = e.write_atomic(Path(directory) / "local.nbnk")
            self.assertEqual(se.SoundBankEditor.from_file(p, external_stop_references=(self.ref,)).validate().to_bytes(), self.source.to_bytes())
        se.validate_external_stop_references((self.source, self.target), {1: (self.ref,)})

    def test_declarations_do_not_authorize_other_action_types_or_targets(self) -> None:
        for kind in (se.ACTION_PLAY, se.ACTION_PLAY_EVENT, 0x102):
            with self.subTest(kind=kind), self.assertRaisesRegex(se.SoundBankError, "does not match"):
                se.SoundBankEditor(source_bank(action_type=kind), external_stop_references=(self.ref,)).validate()
        with self.assertRaisesRegex(se.SoundBankError, "does not match"):
            se.SoundBankEditor(source_bank(target=21), external_stop_references=(self.ref,)).validate()
        local = se.SoundBankEditor(self.source, external_stop_references=(self.ref,))
        local.hirc.insert_object(2, 20, bytes(5) + struct.pack("<I", 987654321), before=(3, 30))
        with self.assertRaisesRegex(se.SoundBankError, "does not match"):
            local.validate()
        short = se.SoundBankEditor(self.source, external_stop_references=(self.ref,))
        short.hirc.replace_object_body(3, 30, expected=short.hirc.object_body(3, 30), replacement=struct.pack("<I", 30), label="synthetic short Action")
        with self.assertRaisesRegex(se.SoundBankError, "too short"):
            short.validate()

    def test_declaration_guards_and_unused_edges(self) -> None:
        for digest in ("", "g" * 64, "A" * 64, None):
            with self.assertRaises(se.SoundBankError):
                replace(self.ref, expected_body_sha256=digest)
        with self.assertRaises(se.SoundBankError):
            replace(self.ref, action_id=True)
        with self.assertRaisesRegex(se.SoundBankError, "duplicate"):
            se.SoundBankEditor(self.source, external_stop_references=(self.ref, self.ref))
        with self.assertRaisesRegex(se.SoundBankError, "must differ"):
            se.SoundBankEditor(self.source, external_stop_references=(replace(self.ref, target_bank_id=1),))
        with self.assertRaisesRegex(se.SoundBankError, "Event-owned"):
            se.SoundBankEditor(self.source, external_stop_references=(self.ref, replace(self.ref, action_id=31))).validate()

    def test_joint_rejects_missing_wrong_or_ambiguous_targets(self) -> None:
        cases = [
            ((self.source,), {1: (self.ref,)}, "target Bank.*missing"),
            ((self.target,), {1: (self.ref,)}, "declaring Bank.*missing"),
            ((self.source, self.target, self.target), {1: (self.ref,)}, "duplicate Bank"),
            ((self.source, sound_bank(2, 21)), {1: (self.ref,)}, "unique Sound"),
            ((self.source, sound_bank(2, 20, kind=7)), {1: (self.ref,)}, "unique Sound"),
            ((self.source, self.target, sound_bank(3, 20)), {1: (self.ref,)}, "unique Sound"),
            ((self.source, self.target), {1: (replace(self.ref, expected_body_sha256="0" * 64),)}, "SHA-256"),
            ((self.source, self.target), {}, "missing object"),
        ]
        for banks, refs, error in cases:
            with self.subTest(error=error), self.assertRaisesRegex(se.SoundBankError, error):
                se.validate_external_stop_references(banks, refs)

    def test_joint_checks_target_media_and_accepts_bidirectional_edges(self) -> None:
        missing = se.SoundBankEditor(self.target)
        missing.hirc.patch_u32(2, 20, 9, 99, 100, label="synthetic missing media")
        bank = se.SoundBank.from_bytes(missing.build())
        ref = reference(bank)
        with self.assertRaises(se.SoundBankError):
            se.validate_external_stop_references((self.source, bank), {1: (ref,)})
        a = se.SoundBankEditor(self.source, external_stop_references=(self.ref,))
        a.hirc.insert_object(2, 10, bytes(5) + struct.pack("<I", 987654321), before=(3, 30))
        a_bank = a.validate()
        b = se.SoundBankEditor(self.target)
        stop = b.hirc.create_stop_action(31, 10, transition_ms=50)
        b.hirc.insert_object(3, 31, stop[4:])
        b.hirc.insert_object(4, 41, struct.pack("<II", 1, 31))
        b_ref = se.ExternalStopReference(31, 1, 10, hashlib.sha256(a.hirc.object_body(2, 10)).hexdigest())
        se.validate_external_stop_references((a_bank, se.SoundBank.from_bytes(b.build())), {1: (self.ref,), 2: (b_ref,)})


class StopBuildIntegrationTests(unittest.TestCase):
    def test_registry_and_joint_failure_preserve_existing_release(self) -> None:
        source, target = source_bank(), sound_bank(2, 20)
        bad_ref = replace(reference(target), expected_body_sha256="0" * 64)
        empty = se.SoundBankEditSummary((), (), 0, (), (), 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plans = []
            for i, bank in enumerate((source, target), 1):
                path = root / f"original/nbnk/b{i}.nbnk"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bank.to_bytes())
                plans.append(SoundBankBuildPlan(
                    name=f"b{i}", design_ids=("test.synthetic",), source=path.relative_to(root),
                    target=f"sound/b{i}.nbnk", expected_source_sha256=hashlib.sha256(bank.to_bytes()).hexdigest(),
                    expected_bank_id=bank.bank_id, apply_edits=lambda _e: None, expected_summary=empty,
                    external_stop_references=(bad_ref,) if i == 1 else (),
                ))
            with self.assertRaisesRegex(BuildError, "registered artifact owner"):
                validate_registry(ModBuildPlan((plans[0],)))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                replace(plans[0], external_stop_references=(bad_ref, bad_ref))
            with self.assertRaisesRegex(ValueError, "must differ"):
                replace(plans[0], external_stop_references=(replace(bad_ref, target_bank_id=1),))
            self.assertEqual(prepare_plan(plans[0], root).preview_summary, empty)
            release = root / "release/nativePC"
            release.mkdir(parents=True)
            marker = release / "existing.bin"
            marker.write_bytes(b"existing release")
            with (
                mock.patch("builders.base.make_tool_paths", return_value=object()),
                mock.patch("builders.base._validate_soundbank_stage"),
                mock.patch("builders.base.publish_release_tree") as publish,
                self.assertRaisesRegex(BuildError, "External Stop reference validation.*SHA-256"),
            ):
                build_all(ModBuildPlan(tuple(plans)), root=root, force=True)
            publish.assert_not_called()
            self.assertEqual(marker.read_bytes(), b"existing release")
            self.assertEqual(list(release.iterdir()), [marker])
