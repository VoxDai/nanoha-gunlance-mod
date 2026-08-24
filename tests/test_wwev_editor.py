from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest

from tools import soundbank_editor

from ._event_format_fixtures import make_test_wwev


class WwevFileTests(unittest.TestCase):
    def test_round_trip_preserves_complete_variable_records(self) -> None:
        payload = make_test_wwev()
        wwev = soundbank_editor.WwevFile.from_bytes(payload)
        self.assertEqual(wwev.to_bytes(), payload)
        self.assertEqual(wwev.version, 19)
        self.assertEqual(wwev.unknown, 0x11223344)
        self.assertEqual(wwev.dependencies, ("motion", "weapon", "player", "common"))
        self.assertEqual(wwev.record(6485).size, 129)
        self.assertEqual(wwev.record(6485).unknown, bytes((0x11,)) * 116)
        self.assertEqual(wwev.record(6489).wwpc, "wp07")
        self.assertGreater(wwev.record(6489).size, wwev.record(6485).size)

    def test_magic_version_trailing_data_and_lookup_are_guarded(self) -> None:
        invalid_magic = bytearray(make_test_wwev())
        invalid_magic[:4] = b"BAD!"
        with self.assertRaisesRegex(soundbank_editor.WwevError, "magic"):
            soundbank_editor.WwevFile.from_bytes(bytes(invalid_magic))

        invalid_version = bytearray(make_test_wwev())
        struct.pack_into("<I", invalid_version, 4, 18)
        with self.assertRaisesRegex(soundbank_editor.WwevError, "version"):
            soundbank_editor.WwevFile.from_bytes(bytes(invalid_version))

        with self.assertRaisesRegex(soundbank_editor.WwevError, "trailing bytes"):
            soundbank_editor.WwevFile.from_bytes(make_test_wwev() + b"x")
        with self.assertRaisesRegex(soundbank_editor.WwevError, "exactly one"):
            soundbank_editor.WwevFile.from_bytes(make_test_wwev()).record(9999)


class WwevEditorTests(unittest.TestCase):
    def test_clones_complete_records_and_supports_multiple_appends(self) -> None:
        editor = soundbank_editor.WwevEditor.from_bytes(make_test_wwev())
        first_donor = editor.records_for_request(6485)[0]
        first = editor.append_cloned_record(
            donor_request=6485,
            expected_donor_event_id=first_donor.event_id,
            expected_donor_mode=first_donor.mode,
            expected_donor_sha256=first_donor.sha256,
            new_request=6500,
            new_event_id=3_000_000_001,
        )
        second_donor = editor.records_for_request(6489)[0]
        second = editor.append_cloned_record(
            donor_request=6489,
            expected_donor_event_id=second_donor.event_id,
            expected_donor_mode=second_donor.mode,
            expected_donor_sha256=second_donor.sha256,
            new_request=6501,
            new_event_id=3_000_000_002,
        )
        rebuilt = editor.validate()
        self.assertEqual(len(rebuilt.records), 4)
        self.assertEqual(first.unknown, first_donor.unknown)
        self.assertEqual(first.command_hash, first_donor.command_hash)
        self.assertEqual(first.wwpc, first_donor.wwpc)
        self.assertEqual(second.unknown, second_donor.unknown)
        self.assertEqual(second.wwpc, "wp07")
        self.assertEqual(editor.summary.record_count_before, 2)
        self.assertEqual(editor.summary.record_count_after, 4)
        self.assertEqual(
            editor.summary.appended_size, first.size + second.size
        )

    def test_donor_and_collision_guards_are_transactional(self) -> None:
        original = make_test_wwev()
        donor = soundbank_editor.WwevFile.from_bytes(original).record(6485)
        cases = (
            ("expected Event", {"expected_donor_event_id": donor.event_id + 1}),
            ("expected mode", {"expected_donor_mode": donor.mode + 1}),
            ("SHA-256", {"expected_donor_sha256": "00" * 32}),
            ("request already exists", {"new_request": 6489}),
            ("Event ID already exists", {"new_event_id": 2_467_230_203}),
        )
        base = {
            "donor_request": 6485,
            "expected_donor_event_id": donor.event_id,
            "expected_donor_mode": donor.mode,
            "expected_donor_sha256": donor.sha256,
            "new_request": 6500,
            "new_event_id": 3_000_000_001,
        }
        for message, override in cases:
            editor = soundbank_editor.WwevEditor.from_bytes(original)
            with self.subTest(message=message):
                with self.assertRaisesRegex(soundbank_editor.WwevError, message):
                    editor.append_cloned_record(**(base | override))
                self.assertEqual(editor.build(), original)
                self.assertEqual(editor.summary.record_count_after, 2)

    def test_request_range_and_atomic_write_guards(self) -> None:
        donor = soundbank_editor.WwevFile.from_bytes(make_test_wwev()).record(6485)
        editor = soundbank_editor.WwevEditor.from_bytes(make_test_wwev())
        with self.assertRaisesRegex(soundbank_editor.WwevError, "signed 16-bit"):
            editor.append_cloned_record(
                donor_request=6485,
                expected_donor_event_id=donor.event_id,
                expected_donor_mode=donor.mode,
                expected_donor_sha256=donor.sha256,
                new_request=0x8000,
                new_event_id=3_000_000_001,
            )

        with tempfile.TemporaryDirectory(prefix="wwev-editor-test.", dir="/tmp") as root:
            source = Path(root) / "input.wwev"
            source.write_bytes(make_test_wwev())
            from_file = soundbank_editor.WwevEditor.from_file(source)
            with self.assertRaisesRegex(soundbank_editor.WwevError, "overwriting"):
                from_file.write_atomic(source)
            output = Path(root) / "output.wwev"
            from_file.write_atomic(output)
            self.assertEqual(output.read_bytes(), source.read_bytes())
            with self.assertRaisesRegex(soundbank_editor.WwevError, "already exists"):
                from_file.write_atomic(output)


if __name__ == "__main__":
    unittest.main()
