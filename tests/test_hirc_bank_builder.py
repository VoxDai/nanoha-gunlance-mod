"""Generic media-less Bank plan validation with synthetic v120 chunks."""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from builders.base import (
    BuildError, HircBank, HircBankBuildPlan, HircBankEditSummary,
    _edit_hirc_bank, prepare_plan,
)
from tools import soundbank_editor


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return tag + struct.pack("<I", len(payload)) + payload


def _source_bank() -> bytes:
    old_event = struct.pack("<II", 1, 0)
    hirc = struct.pack("<I", 1) + struct.pack("<BI", 4, len(old_event)) + old_event
    return _chunk(b"BKHD", struct.pack("<II", 120, 123) + b"\xAA\xBB") + _chunk(b"HIRC", hirc)


def _append_route(hirc: soundbank_editor.HircEditor) -> None:
    hirc.insert_object(soundbank_editor.HIRC_ACTION, 2,
                       hirc.create_play_event_action(2, 1)[4:])
    hirc.insert_object(soundbank_editor.HIRC_EVENT, 3, struct.pack("<II", 1, 2))


class HircBankBuilderTests(unittest.TestCase):
    def test_preserves_all_original_chunks_and_objects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "original/nbnk/event.nbnk"
            source.parent.mkdir(parents=True)
            raw = _source_bank()
            source.write_bytes(raw)
            plan = HircBankBuildPlan(
                name="event", design_ids=("test.event",),
                source="original/nbnk/event.nbnk",
                target="sound/wwise/Windows/event.nbnk",
                expected_source_sha256=hashlib.sha256(raw).hexdigest(),
                expected_bank_id=123, apply_edits=_append_route,
                expected_summary=HircBankEditSummary(((3, 2), (4, 3)), 0, (), 35),
            )
            prepared = prepare_plan(plan, root)
            rebuilt, summary = _edit_hirc_bank(plan, prepared.original)
            self.assertEqual(summary, plan.expected_summary)
            self.assertEqual(rebuilt[:18], raw[:18])  # Complete BKHD chunk.
            parsed = HircBank.from_bytes(rebuilt)
            hirc = soundbank_editor.HircEditor(parsed.hirc_payload)
            self.assertEqual(hirc.event_actions(1), ())
            self.assertEqual(hirc.event_actions(3), (2,))

    def test_rejects_missing_chunks_and_original_object_changes(self) -> None:
        raw = _source_bank()
        with self.assertRaisesRegex(BuildError, "exactly BKHD and HIRC"):
            HircBank.from_bytes(raw + _chunk(b"DATA", b""))

        def modify_original(hirc: soundbank_editor.HircEditor) -> None:
            hirc.replace_object_body(
                soundbank_editor.HIRC_EVENT, 1, struct.pack("<II", 1, 0),
                struct.pack("<II", 1, 1), label="synthetic original mutation",
            )

        plan = HircBankBuildPlan(
            name="event", design_ids=("test.event",),
            source="original/nbnk/event.nbnk", target="sound/wwise/Windows/event.nbnk",
            expected_source_sha256=hashlib.sha256(raw).hexdigest(),
            expected_bank_id=123, apply_edits=modify_original,
            expected_summary=HircBankEditSummary((), 1, (), 0),
        )
        with self.assertRaisesRegex(BuildError, "original HIRC objects changed"):
            _edit_hirc_bank(plan, HircBank.from_bytes(raw))


if __name__ == "__main__":
    unittest.main()
