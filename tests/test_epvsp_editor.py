"""Synthetic coverage of the request-only EPVSP editor."""

from dataclasses import replace
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from builders.base import BuildError, EpvspBuildPlan, build_plan, prepare_plan
from tools import soundbank_editor as se


def esp_bytes(*rows):
    return (
        struct.pack("<I4sII", 0x18091001, b"ESP\0", 8, 0x45185BED)
        + b"test\\sound\\context\0"
        + struct.pack("<I", len(rows))
        + b"".join(struct.pack("<iiiII", *row) for row in rows)
        + bytes(4)
    )


class EpvspEditorTests(unittest.TestCase):
    def test_round_trip_and_start_only_replacement(self):
        old = (0, 17, 18, 100, 0)
        sibling = (0, 17, 18, 101, 0)
        payload = esp_bytes(old, sibling)
        original = se.EpvspFile.from_bytes(payload)
        self.assertEqual(original.to_bytes(), payload)
        editor = se.EpvspEditor(original)
        editor.replace_start_request(0, expected=old, new_request=19)
        self.assertEqual(editor.validate().to_bytes(), esp_bytes((0, 19, 18, 100, 0), sibling))
        self.assertEqual(editor.summary, (se.EpvspStartEdit(0, old, (0, 19, 18, 100, 0)),))
        self.assertEqual(original.to_bytes(), payload)

    def test_guard_failures_do_not_edit(self):
        old = (0, 17, 18, 100, 0)
        original = se.EpvspFile.from_bytes(esp_bytes(old, (0, 20, 21, 101, 0)))
        for row, expected, request in (
            (0, (0, 16, 18, 100, 0), 19),
            (2, old, 19),
            (0, old, 21),
            (0, old, 32768),
        ):
            with self.subTest(row=row, expected=expected, request=request):
                editor = se.EpvspEditor(original)
                with self.assertRaises(se.EditorError):
                    editor.replace_start_request(row, expected=expected, new_request=request)
                self.assertEqual(editor.validate(), original)
                self.assertEqual(editor.summary, ())

    def test_unsupported_layout_and_duplicate_row(self):
        old = (0, 17, 18, 100, 0)
        valid = esp_bytes(old)
        for malformed in (valid[:-1], valid[:-4] + struct.pack("<I", 1), valid + b"x"):
            with self.assertRaises(se.EditorError):
                se.EpvspFile.from_bytes(malformed)
        duplicate = se.EpvspEditor(se.EpvspFile.from_bytes(esp_bytes(old, old)))
        with self.assertRaises(se.EditorError):
            duplicate.replace_start_request(0, expected=old, new_request=19)


    def test_plan_preflight_and_staged_readback(self):
        old = (0, 17, 18, 100, 0)
        new = (0, 19, 18, 100, 0)
        payload = esp_bytes(old)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "original/epvsp/test.epvsp"
            source.parent.mkdir(parents=True)
            source.write_bytes(payload)

            def apply(editor):
                editor.replace_start_request(0, expected=old, new_request=19)

            plan = EpvspBuildPlan(
                name="test_epvsp", design_ids=("test.synthetic",),
                source=source.relative_to(root), target="sound/test.epvsp",
                expected_source_sha256=hashlib.sha256(payload).hexdigest(),
                apply_edits=apply, expected_summary=(se.EpvspStartEdit(0, old, new),),
            )
            with self.assertRaises(BuildError):
                prepare_plan(replace(plan, expected_summary=()), root)
            prepared = prepare_plan(plan, root)
            target = build_plan(prepared, root / "stage", root / "converted",
                                root / "validation", root, tools=None)
            self.assertEqual(target.read_bytes(), esp_bytes(new))
            self.assertEqual(source.read_bytes(), payload)
