from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from tools import soundbank_editor
from tools.soundbank_editor import editor as compatibility_editor

from ._soundbank_fixtures import SOUNDBANK_ROOT, make_random_container_tail


class SoundBankRoundTripTests(unittest.TestCase):
    def test_every_original_bank_round_trips_byte_exactly(self) -> None:
        for path in sorted(SOUNDBANK_ROOT.glob("*.nbnk")):
            if path.name == "pl_act_vo_event.nbnk":
                continue
            bank = soundbank_editor.SoundBank.from_file(path)
            self.assertEqual(bank.to_bytes(), path.read_bytes(), path.name)
            editor = soundbank_editor.SoundBankEditor(bank)
            self.assertEqual(editor.build(), path.read_bytes(), path.name)
            self.assertEqual(editor.validate().to_bytes(), path.read_bytes(), path.name)

    def test_media_selection_and_extraction_are_one_based(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp_gun_cmn.nbnk"
        )
        first = bank.media_entry(index=1)
        self.assertEqual(bank.media_entry(media_id=first.media_id), first)
        self.assertEqual(bank.extract_media(index=1), first.payload)
        self.assertEqual(bank.extract_all_media()[1], first.payload)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "exactly one"):
            bank.media_entry()

    def test_wwise_hash_matches_bank_header(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        )
        self.assertEqual(soundbank_editor.wwise_fnv1("hm_cm00_epvsp"), bank.bank_id)


class SoundBankEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        cls.bank = soundbank_editor.SoundBank.from_file(cls.path)
        cls.donor_sound_id = 330120372
        cls.donor_media_id = 321677221
        cls.wem = cls.bank.extract_media(media_id=cls.donor_media_id)

    def test_media_replace_and_append(self) -> None:
        editor = soundbank_editor.SoundBankEditor(self.bank)
        original = self.bank.media_entry(index=1)
        editor.replace_media(
            self.wem,
            index=1,
            expected_media_id=original.media_id,
            expected_sha256=hashlib.sha256(original.payload).hexdigest(),
        )
        editor.append_media(4_294_967_001, self.wem)
        rebuilt = editor.validate()
        self.assertEqual(rebuilt.media_entry(index=1).payload, self.wem)
        self.assertEqual(rebuilt.media_entry(media_id=4_294_967_001).payload, self.wem)
        self.assertEqual(rebuilt.media_entry(media_id=4_294_967_001).offset % 16, 0)
        self.assertEqual(editor.summary.added_media, ((len(self.bank.entries) + 1, 4_294_967_001),))

    def test_media_guards_and_collisions(self) -> None:
        editor = soundbank_editor.SoundBankEditor(self.bank)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "expected Media ID"):
            editor.replace_media(self.wem, index=1, expected_media_id=0)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "expected SHA-256"):
            editor.replace_media(
                self.wem,
                index=1,
                expected_sha256="00" * 32,
            )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "already exists"):
            editor.append_media(self.bank.entries[0].media_id, self.wem)

    def test_ordinary_pcm_wav_is_rejected(self) -> None:
        payload = (
            b"RIFF"
            + struct.pack("<I", 28)
            + b"WAVEfmt "
            + struct.pack("<IHHIIHH", 16, 1, 1, 48000, 96000, 2, 16)
        )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "ordinary PCM"):
            soundbank_editor.validate_wem(payload)

    def test_complete_custom_sound_chain(self) -> None:
        event_id = 1_665_664_746
        expected_actions = (325_918_653, 744_297_877)
        media_id = 4_294_967_001
        sound_id = 4_294_967_002
        action_id = 4_294_967_003
        editor = soundbank_editor.SoundBankEditor(self.bank)
        editor.add_custom_sound_action(
            event_id,
            action_id,
            sound_id,
            media_id,
            self.donor_sound_id,
            self.wem,
            expected_actions=expected_actions,
            expected_donor_source_id=self.donor_media_id,
        )
        rebuilt = editor.validate()
        hirc = soundbank_editor.HircEditor(rebuilt.hirc_payload)
        self.assertEqual(hirc.event_actions(event_id), expected_actions + (action_id,))
        self.assertEqual(struct.unpack_from("<I", hirc.object_body(0x02, sound_id), 9)[0], media_id)
        action = hirc.object_body(0x03, action_id)
        self.assertEqual(struct.unpack_from("<H", action, 4)[0], 0x0403)
        self.assertEqual(struct.unpack_from("<I", action, 6)[0], sound_id)
        positions = {
            (item.object_type, item.object_id): position
            for position, item in enumerate(hirc.objects())
        }
        self.assertLess(positions[(0x03, action_id)], positions[(0x04, event_id)])
        self.assertEqual(rebuilt.extract_media(media_id=media_id), self.wem)
        self.assertEqual(editor.summary.added_hirc_objects, ((0x02, sound_id), (0x03, action_id)))
        self.assertEqual(editor.summary.hirc_size_delta, 104)

    def test_play_event_action_and_version_gate(self) -> None:
        editor = soundbank_editor.SoundBankEditor(self.bank)
        editor.add_play_event_action(
            1_665_664_746,
            4_294_967_003,
            4283649192,
            expected_actions=(325_918_653, 744_297_877),
        )
        rebuilt = editor.validate()
        hirc = soundbank_editor.HircEditor(rebuilt.hirc_payload)
        positions = {
            (item.object_type, item.object_id): position
            for position, item in enumerate(hirc.objects())
        }
        self.assertEqual(
            positions[(soundbank_editor.HIRC_ACTION, 4_294_967_003)] + 1,
            positions[(soundbank_editor.HIRC_EVENT, 1_665_664_746)],
        )

        invalid_order = soundbank_editor.SoundBankEditor(self.bank)
        action = invalid_order.hirc.create_play_event_action(
            4_294_967_004, 4283649192
        )
        invalid_order.hirc.insert_object(
            soundbank_editor.HIRC_ACTION,
            4_294_967_004,
            action[4:],
        )
        invalid_order.hirc.append_event_action(
            1_665_664_746,
            4_294_967_004,
            expected_actions=(325_918_653, 744_297_877),
        )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "serialized before"):
            invalid_order.validate()

        data = bytearray(self.bank.to_bytes())
        struct.pack_into("<I", data, 8, 121)
        unsupported = soundbank_editor.SoundBankEditor.from_bytes(bytes(data))
        self.assertEqual(unsupported.validate().version, 121)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "requires Wwise v120"):
            unsupported.add_play_event_action(
                1_665_664_746,
                4_294_967_003,
                4283649192,
                expected_actions=(325_918_653, 744_297_877),
            )

    def test_validate_rejects_new_container_with_missing_child(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        donor_container_id = 145_848_034
        donor_sound_id = 535_190_438
        new_container_id = 4_294_967_000
        missing_child_id = 4_294_966_999
        donor = editor.hirc.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            donor_container_id,
        )
        old_tail = make_random_container_tail((donor_sound_id, 50_000))
        cloned = bytearray(donor[: -len(old_tail)])
        struct.pack_into("<I", cloned, 0, new_container_id)
        cloned += make_random_container_tail((missing_child_id, 50_000))
        editor.hirc.insert_object(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            new_container_id,
            bytes(cloned[4:]),
        )

        with self.assertRaisesRegex(
            soundbank_editor.SoundBankError, "references missing child"
        ):
            editor.validate()

    def test_validate_rejects_stop_action_with_missing_target(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        donor_action_id = 743_936_681
        stop_event_id = 461_444_626
        new_action_id = 4_294_966_999
        missing_target_id = 4_294_966_998
        cloned = bytearray(
            editor.hirc.object_body(
                soundbank_editor.HIRC_ACTION, donor_action_id
            )
        )
        struct.pack_into("<I", cloned, 0, new_action_id)
        struct.pack_into("<I", cloned, 6, missing_target_id)
        editor.hirc.insert_object(
            soundbank_editor.HIRC_ACTION,
            new_action_id,
            bytes(cloned[4:]),
            before=(soundbank_editor.HIRC_EVENT, stop_event_id),
        )
        editor.hirc.append_event_action(
            stop_event_id,
            new_action_id,
            expected_actions=(donor_action_id,),
        )

        with self.assertRaisesRegex(
            soundbank_editor.SoundBankError, "Stop Action.*missing object"
        ):
            editor.validate()

    def test_validate_rejects_new_switch_with_missing_child(self) -> None:
        editor = soundbank_editor.SoundBankEditor(self.bank)
        donor_container_id = 368_774_789
        new_container_id = 4_294_967_000
        original_child_id = 127_521_149
        missing_child_id = 4_294_966_999
        topology = editor.hirc.switch_container_topology(donor_container_id)
        editor.hirc.clone_switch_container(
            donor_container_id,
            new_container_id,
            {
                child_id: original_child_id
                if child_id == original_child_id
                else None
                for child_id in topology.children
            },
            expected_topology=topology,
            expected_body_sha256=(
                "a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde"
                "1358c02ab99043bb"
            ),
        )
        body = editor.hirc.object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER, new_container_id
        )
        old_id = struct.pack("<I", original_child_id)
        new_id = struct.pack("<I", missing_child_id)
        self.assertEqual(body.count(old_id), 13)
        editor.hirc.replace_object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER,
            new_container_id,
            body,
            body.replace(old_id, new_id),
            label="inject missing Switch child",
        )

        with self.assertRaisesRegex(
            soundbank_editor.SoundBankError, "references missing child"
        ):
            editor.validate()

    def test_validate_rejects_new_switch_serialized_before_child(self) -> None:
        source = soundbank_editor.SoundBankEditor(self.bank)
        donor_container_id = 368_774_789
        new_container_id = 4_294_967_000
        child_id = 127_521_149
        topology = source.hirc.switch_container_topology(donor_container_id)
        source.hirc.clone_switch_container(
            donor_container_id,
            new_container_id,
            {
                item: child_id if item == child_id else None
                for item in topology.children
            },
            expected_topology=topology,
            expected_body_sha256=(
                "a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde"
                "1358c02ab99043bb"
            ),
        )
        cloned = source.hirc.object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER, new_container_id
        )

        invalid = soundbank_editor.SoundBankEditor(self.bank)
        invalid.hirc.insert_object(
            soundbank_editor.HIRC_SWITCH_CONTAINER,
            new_container_id,
            cloned[4:],
            before=(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, child_id),
        )
        with self.assertRaisesRegex(
            soundbank_editor.SoundBankError, "serialized before their parent"
        ):
            invalid.validate()

    def test_atomic_write_refuses_input_and_reads_back(self) -> None:
        editor = soundbank_editor.SoundBankEditor(self.bank)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "overwriting"):
            editor.write_atomic(self.path)
        with tempfile.TemporaryDirectory(prefix="soundbank-editor-test.", dir="/tmp") as directory:
            output = Path(directory) / self.path.name
            editor.write_atomic(output)
            self.assertEqual(output.read_bytes(), self.path.read_bytes())


class PublicApiCompatibilityTests(unittest.TestCase):
    def test_package_and_legacy_editor_exports_share_implementations(self) -> None:
        self.assertIs(compatibility_editor.SoundBank, soundbank_editor.SoundBank)
        self.assertIs(
            compatibility_editor.SoundBankEditor, soundbank_editor.SoundBankEditor
        )
        self.assertIs(compatibility_editor.HircEditor, soundbank_editor.HircEditor)
        self.assertIs(
            compatibility_editor.SwitchContainerTopology,
            soundbank_editor.SwitchContainerTopology,
        )
        self.assertIs(
            compatibility_editor.SwitchNodeParams,
            soundbank_editor.SwitchNodeParams,
        )
        self.assertEqual(soundbank_editor.HIRC_SWITCH_CONTAINER, 0x06)
        self.assertEqual(soundbank_editor.ACTION_STOP, 0x0103)
        self.assertIs(
            soundbank_editor.EditSummary, soundbank_editor.SoundBankEditSummary
        )
        self.assertTrue(
            issubclass(soundbank_editor.SoundBankError, soundbank_editor.EditorError)
        )
        self.assertTrue(
            issubclass(soundbank_editor.LmtError, soundbank_editor.EditorError)
        )
        self.assertTrue(
            issubclass(soundbank_editor.WwevError, soundbank_editor.EditorError)
        )


if __name__ == "__main__":
    unittest.main()
