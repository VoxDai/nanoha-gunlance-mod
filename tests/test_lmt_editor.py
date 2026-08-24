from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest

from tools import soundbank_editor

from ._event_format_fixtures import make_test_lmt, make_test_wwev


class LmtFileTests(unittest.TestCase):
    def test_round_trip_and_wwev_resolution(self) -> None:
        payload = make_test_lmt()
        lmt = soundbank_editor.LmtFile.from_bytes(payload)
        wwev = soundbank_editor.WwevFile.from_bytes(make_test_wwev())
        self.assertEqual(lmt.version, 95)
        self.assertEqual(lmt.entry_count, 1)
        self.assertEqual(lmt.to_bytes(), payload)
        self.assertEqual(lmt.action(0).frame_count, 60)
        self.assertEqual(lmt.timl_for_motion(0), lmt.action(0).timl)
        rows = lmt.triggered_requests(wwev)
        self.assertEqual(
            [(row.slot, row.request_no, row.event_id) for row in rows],
            [
                ("A", 6485, 1_352_901_803),
                ("B", 6489, 2_467_230_203),
            ],
        )
        self.assertTrue(all(row.trigger_frame == 12.0 for row in rows))

    def test_shared_timl_motions_are_reported(self) -> None:
        lmt = soundbank_editor.LmtFile.from_bytes(
            make_test_lmt(duplicate_action=True)
        )
        rows = lmt.triggered_requests()
        self.assertEqual(len(rows), 4)
        self.assertTrue(
            all(row.shared_timl_motions == (0, 1) for row in rows)
        )

    def test_magic_version_and_keyframe_type_are_guarded(self) -> None:
        invalid_magic = bytearray(make_test_lmt())
        invalid_magic[:4] = b"BAD!"
        with self.assertRaisesRegex(soundbank_editor.LmtError, "magic"):
            soundbank_editor.LmtFile.from_bytes(bytes(invalid_magic))

        invalid_version = bytearray(make_test_lmt())
        struct.pack_into("<H", invalid_version, 4, 94)
        with self.assertRaisesRegex(soundbank_editor.LmtError, "version"):
            soundbank_editor.LmtFile.from_bytes(bytes(invalid_version))

        invalid_type = bytearray(make_test_lmt())
        first = soundbank_editor.LmtFile.from_bytes(bytes(invalid_type)).action(0)
        keyframe = first.timl[0].transforms[0].keyframes[0]
        struct.pack_into("<h", invalid_type, keyframe.offset + 18, 2)
        with self.assertRaisesRegex(soundbank_editor.LmtError, "stores data type"):
            soundbank_editor.LmtFile.from_bytes(bytes(invalid_type))


class LmtEditorTests(unittest.TestCase):
    def test_guarded_request_replacement_and_multiple_edits(self) -> None:
        original = make_test_lmt()
        editor = soundbank_editor.LmtEditor.from_bytes(original)
        first = editor.replace_request(
            motion_id=0,
            event_group="EventGroup06",
            slot="A",
            request_keyframe_frame=0.0,
            expected_request=6485,
            replacement_request=6500,
            expected_trigger_frames=(12.0,),
        )
        self.assertEqual(first.changed_byte_count, 1)
        second = editor.replace_request(
            motion_id=0,
            event_group="EventGroup06",
            slot="B",
            request_keyframe_frame=0.0,
            expected_request=6489,
            replacement_request=6501,
            expected_trigger_frames=(12.0,),
        )
        rebuilt = editor.validate()
        self.assertEqual(len(rebuilt.to_bytes()), len(original))
        self.assertEqual(editor.summary.changed_byte_count, 2)
        self.assertEqual(editor.summary.edits, (first, second))
        self.assertEqual(
            [(row.slot, row.request_no) for row in rebuilt.triggered_requests()],
            [("A", 6500), ("B", 6501)],
        )

    def test_shared_timeline_frame_request_and_overlap_guards(self) -> None:
        shared = soundbank_editor.LmtEditor.from_bytes(
            make_test_lmt(duplicate_action=True)
        )
        with self.assertRaisesRegex(soundbank_editor.LmtError, "shares TIML"):
            shared.replace_request(
                motion_id=0,
                event_group="EventGroup06",
                slot="A",
                request_keyframe_frame=0.0,
                expected_request=6485,
                replacement_request=6500,
                expected_trigger_frames=(12.0,),
            )

        editor = soundbank_editor.LmtEditor.from_bytes(make_test_lmt())
        with self.assertRaisesRegex(soundbank_editor.LmtError, "keyframe at frame"):
            editor.replace_request(
                motion_id=0,
                event_group="EventGroup06",
                slot="A",
                request_keyframe_frame=1.0,
                expected_request=6485,
                replacement_request=6500,
                expected_trigger_frames=(12.0,),
            )
        with self.assertRaisesRegex(soundbank_editor.LmtError, "trigger frames"):
            editor.replace_request(
                motion_id=0,
                event_group="EventGroup06",
                slot="A",
                request_keyframe_frame=0.0,
                expected_request=6485,
                replacement_request=6500,
                expected_trigger_frames=(11.0,),
            )

        editor.replace_request(
            motion_id=0,
            event_group="EventGroup06",
            slot="A",
            request_keyframe_frame=0.0,
            expected_request=6485,
            replacement_request=6500,
            expected_trigger_frames=(12.0,),
        )
        with self.assertRaisesRegex(soundbank_editor.LmtError, "overlaps"):
            editor.replace_request(
                motion_id=0,
                event_group="EventGroup06",
                slot="A",
                request_keyframe_frame=0.0,
                expected_request=6500,
                replacement_request=6501,
                expected_trigger_frames=(12.0,),
            )

    def test_request_range_and_atomic_write_guards(self) -> None:
        editor = soundbank_editor.LmtEditor.from_bytes(make_test_lmt())
        with self.assertRaisesRegex(soundbank_editor.LmtError, "signed 16-bit"):
            editor.replace_request(
                motion_id=0,
                event_group="EventGroup06",
                slot="A",
                request_keyframe_frame=0.0,
                expected_request=6485,
                replacement_request=0x8000,
                expected_trigger_frames=(12.0,),
            )

        with tempfile.TemporaryDirectory(prefix="lmt-editor-test.", dir="/tmp") as root:
            source = Path(root) / "input.lmt"
            source.write_bytes(make_test_lmt())
            from_file = soundbank_editor.LmtEditor.from_file(source)
            with self.assertRaisesRegex(soundbank_editor.LmtError, "overwriting"):
                from_file.write_atomic(source)
            output = Path(root) / "output.lmt"
            from_file.write_atomic(output)
            self.assertEqual(output.read_bytes(), source.read_bytes())
            with self.assertRaisesRegex(soundbank_editor.LmtError, "already exists"):
                from_file.write_atomic(output)


class EventRouteIntegrationTests(unittest.TestCase):
    def test_edited_lmt_resolves_through_edited_wwev(self) -> None:
        lmt_editor = soundbank_editor.LmtEditor.from_bytes(make_test_lmt())
        lmt_editor.replace_request(
            motion_id=0,
            event_group="EventGroup06",
            slot="A",
            request_keyframe_frame=0.0,
            expected_request=6485,
            replacement_request=6500,
            expected_trigger_frames=(12.0,),
        )
        wwev_editor = soundbank_editor.WwevEditor.from_bytes(make_test_wwev())
        donor = wwev_editor.records_for_request(6485)[0]
        wwev_editor.append_cloned_record(
            donor_request=6485,
            expected_donor_event_id=donor.event_id,
            expected_donor_mode=donor.mode,
            expected_donor_sha256=donor.sha256,
            new_request=6500,
            new_event_id=3_000_000_001,
        )
        rows = lmt_editor.validate().triggered_requests(wwev_editor.validate())
        target = [row for row in rows if row.request_no == 6500]
        self.assertEqual(len(target), 1)
        self.assertEqual(target[0].event_id, 3_000_000_001)
        self.assertEqual(target[0].trigger_frame, 12.0)


if __name__ == "__main__":
    unittest.main()
