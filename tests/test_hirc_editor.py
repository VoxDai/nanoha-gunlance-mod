from __future__ import annotations

import hashlib
import struct
import unittest

from tools import soundbank_editor

from ._soundbank_fixtures import (
    SOUNDBANK_ROOT,
    make_hirc,
    make_random_container_tail,
)


DONOR_SWITCH_TOPOLOGY = soundbank_editor.SwitchContainerTopology(
    group_type=0,
    group_id=3_251_135_135,
    default_switch=3_396_333_570,
    continuous_validation=0,
    children=(101_900_622, 125_400_496, 127_521_149, 133_098_601, 438_972_177),
    switch_packages=(
        (3_396_333_570, (127_521_149,)),
        (1_341_411_413, (438_972_177,)),
        (3_366_211_890, (125_400_496,)),
        (1_382_012_724, (127_521_149,)),
        (345_916_037, (127_521_149,)),
        (1_839_555_973, (127_521_149,)),
        (3_165_334_324, (127_521_149,)),
        (3_893_559_432, (133_098_601,)),
        (3_529_994_682, (127_521_149,)),
        (3_846_765_152, (127_521_149,)),
        (3_818_705_907, (101_900_622,)),
        (1_876_434_011, (127_521_149,)),
        (835_669_289, (127_521_149,)),
        (3_295_588_651, (127_521_149,)),
        (208_142_906, (127_521_149,)),
    ),
    node_params=(
        soundbank_editor.SwitchNodeParams(125_400_496, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(438_972_177, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(133_098_601, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(101_900_622, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(127_521_149, 0, 1, 0, 0),
    ),
)
DONOR_SWITCH_BODY_SHA256 = (
    "a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde1358c02ab99043bb"
)


class HircEditorTests(unittest.TestCase):
    def test_noop_round_trip_is_byte_exact(self) -> None:
        payload = make_hirc((0x02, 10, b"\x01\x02"), (0x05, 20, b"\x03"))
        self.assertEqual(soundbank_editor.HircEditor(payload).build(), payload)

    def test_typed_patch_uses_object_relative_offset(self) -> None:
        payload = make_hirc((0x02, 10, b"\x01\x02\x03\x04"))
        editor = soundbank_editor.HircEditor(payload)
        editor.patch_u8(0x02, 10, 5, 0x02, 0x09, label="test field")
        self.assertEqual(editor.object_body(0x02, 10)[4:], b"\x01\x09\x03\x04")
        self.assertEqual(editor.changed_byte_count, 1)

    def test_missing_duplicate_and_old_value_guards(self) -> None:
        editor = soundbank_editor.HircEditor(make_hirc((0x02, 10, b"\0")))
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "object not found"):
            editor.object_body(0x02, 99)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "expected 02"):
            editor.patch_u8(0x02, 10, 4, 0x02, 0x03, label="test field")
        duplicate = make_hirc((0x02, 10, b"\0"), (0x02, 10, b"\1"))
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "duplicate"):
            soundbank_editor.HircEditor(duplicate)

    def test_insert_object_uses_stable_type_group_placement(self) -> None:
        payload = make_hirc(
            (soundbank_editor.HIRC_SOUND, 10, b"a"),
            (soundbank_editor.HIRC_ACTION, 20, b"b"),
            (soundbank_editor.HIRC_EVENT, 30, struct.pack("<I", 0)),
        )
        editor = soundbank_editor.HircEditor(payload)
        editor.insert_object(soundbank_editor.HIRC_ACTION, 21, b"new")
        self.assertEqual(
            [(item.object_type, item.object_id) for item in editor.objects()],
            [(0x02, 10), (0x03, 20), (0x03, 21), (0x04, 30)],
        )
        reparsed = soundbank_editor.HircEditor(editor.build())
        self.assertEqual(len(reparsed.objects()), 4)

    def test_insert_object_can_be_anchored_before_an_event(self) -> None:
        payload = make_hirc(
            (soundbank_editor.HIRC_ACTION, 20, b"old"),
            (soundbank_editor.HIRC_EVENT, 30, struct.pack("<II", 1, 20)),
            (soundbank_editor.HIRC_ACTION, 21, b"later"),
        )
        editor = soundbank_editor.HircEditor(payload)
        editor.insert_object(
            soundbank_editor.HIRC_ACTION,
            22,
            b"new",
            before=(soundbank_editor.HIRC_EVENT, 30),
        )
        self.assertEqual(
            [(item.object_type, item.object_id) for item in editor.objects()],
            [(0x03, 20), (0x03, 22), (0x04, 30), (0x03, 21)],
        )

    def test_play_action_golden_bodies(self) -> None:
        editor = soundbank_editor.HircEditor(struct.pack("<I", 0))
        play_event = editor.create_play_event_action(189166630, 14956425)
        self.assertEqual(play_event.hex(), "2674460b03218937e400000000")
        play = editor.create_play_action(101454437, 1004943696, 4182706408)
        self.assertEqual(play.hex(), "65120c0603045039e63b00000004e8084ff9")

    def test_event_can_be_rebuilt_more_than_once(self) -> None:
        event_id = 30
        payload = make_hirc(
            (0x03, 20, b"x"),
            (0x03, 21, b"y"),
            (0x04, event_id, struct.pack("<II", 1, 20)),
        )
        editor = soundbank_editor.HircEditor(payload)
        editor.append_event_action(event_id, 21, expected_actions=(20,))
        self.assertEqual(editor.event_actions(event_id), (20, 21))

    def test_same_length_object_rebuild_is_declared(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        sound_id = 330_120_372
        body = editor.hirc.object_body(soundbank_editor.HIRC_SOUND, sound_id)
        replacement = bytearray(body)
        replacement[-1] ^= 1
        editor.hirc.replace_object_body(
            soundbank_editor.HIRC_SOUND,
            sound_id,
            body,
            bytes(replacement),
            label="test same-size rebuild",
        )
        self.assertIn(
            (soundbank_editor.HIRC_SOUND, sound_id), editor.hirc.rebuilt_objects
        )
        editor.validate()

    def test_clone_random_sequence_container_rebuilds_reviewed_tail(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        donor_container_id = 145_848_034
        donor_sound_id = 535_190_438
        second_sound_id = 220_939_954
        new_container_id = 4_294_967_000
        old_playlist = ((donor_sound_id, 50_000),)
        new_playlist = (
            (donor_sound_id, 50_000),
            (second_sound_id, 25_000),
        )

        donor = editor.hirc.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            donor_container_id,
        )
        old_tail = make_random_container_tail(*old_playlist)
        self.assertTrue(donor.endswith(old_tail))
        prefix = bytearray(donor[: -len(old_tail)])
        struct.pack_into("<I", prefix, 0, new_container_id)
        self.assertEqual(struct.unpack_from("<H", prefix, len(prefix) - 6)[0], 1)
        struct.pack_into("<H", prefix, len(prefix) - 6, 0)

        editor.hirc.clone_random_sequence_container(
            donor_container_id,
            new_container_id,
            new_playlist,
            expected_playlist=old_playlist,
            expected_avoid_repeat_count=1,
            avoid_repeat_count=0,
        )

        actual = editor.hirc.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            new_container_id,
        )
        self.assertEqual(actual, bytes(prefix) + make_random_container_tail(*new_playlist))
        rebuilt = editor.validate()
        self.assertEqual(
            soundbank_editor.HircEditor(rebuilt.hirc_payload).object_body(
                soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
                new_container_id,
            ),
            actual,
        )
        self.assertEqual(
            editor.summary.added_hirc_objects,
            ((soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, new_container_id),),
        )
        self.assertEqual(editor.summary.hirc_size_delta, 105)

    def test_cloned_random_is_serialized_after_its_latest_child(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        donor_container_id = 145_848_034
        donor_sound_id = 535_190_438
        new_sound_id = 4_294_966_999
        new_container_id = 4_294_967_000
        donor_sound = editor.hirc.object_body(
            soundbank_editor.HIRC_SOUND, donor_sound_id
        )
        donor_media_id = struct.unpack_from("<I", donor_sound, 9)[0]
        editor.hirc.clone_sound(
            donor_sound_id,
            new_sound_id,
            donor_media_id,
            expected_source_id=donor_media_id,
        )
        editor.hirc.clone_random_sequence_container(
            donor_container_id,
            new_container_id,
            ((new_sound_id, 50_000),),
            expected_playlist=((donor_sound_id, 50_000),),
            expected_avoid_repeat_count=1,
        )

        positions = {item.object_id: item.index for item in editor.hirc.objects()}
        self.assertLess(positions[new_sound_id], positions[new_container_id])
        editor.validate()

    def test_clone_random_sequence_container_guards_inputs(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        donor_container_id = 145_848_034
        donor_sound_id = 535_190_438
        expected_playlist = ((donor_sound_id, 50_000),)
        arguments = {
            "donor_container_id": donor_container_id,
            "new_container_id": 4_294_967_000,
            "playlist": expected_playlist,
            "expected_playlist": expected_playlist,
            "expected_avoid_repeat_count": 1,
        }

        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "expected playlist"):
            editor.hirc.clone_random_sequence_container(
                **(arguments | {"expected_playlist": ((donor_sound_id, 40_000),)})
            )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "avoid-repeat count"):
            editor.hirc.clone_random_sequence_container(
                **(arguments | {"expected_avoid_repeat_count": 0})
            )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "must be unique"):
            editor.hirc.clone_random_sequence_container(
                **(
                    arguments
                    | {
                        "playlist": (
                            (donor_sound_id, 50_000),
                            (donor_sound_id, 50_000),
                        )
                    }
                )
            )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "does not exist"):
            editor.hirc.clone_random_sequence_container(
                **(arguments | {"playlist": ((4_294_966_999, 50_000),)})
            )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "positive signed"):
            editor.hirc.clone_random_sequence_container(
                **(arguments | {"playlist": ((donor_sound_id, 0),)})
            )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "ID already exists"):
            editor.hirc.clone_random_sequence_container(
                **(arguments | {"new_container_id": donor_container_id})
            )

    def test_clone_random_sequence_container_rejects_bad_donor_and_version(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        expected_playlist = ((535_190_438, 50_000),)
        unsupported = soundbank_editor.HircEditor(bank.hirc_payload, version=121)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "requires Wwise v120"):
            unsupported.clone_random_sequence_container(
                145_848_034,
                4_294_967_000,
                expected_playlist,
                expected_playlist=expected_playlist,
                expected_avoid_repeat_count=1,
            )

        editor = soundbank_editor.SoundBankEditor(bank)
        donor = editor.hirc.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 145_848_034
        )
        tail = make_random_container_tail(*expected_playlist)
        sequence_donor_id = 4_294_966_998
        sequence = bytearray(donor)
        struct.pack_into("<I", sequence, 0, sequence_donor_id)
        sequence[len(donor) - len(tail) - 2] = 1
        editor.hirc.insert_object(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            sequence_donor_id,
            bytes(sequence[4:]),
        )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "not in Random mode"):
            editor.hirc.clone_random_sequence_container(
                sequence_donor_id,
                4_294_967_000,
                expected_playlist,
                expected_playlist=expected_playlist,
                expected_avoid_repeat_count=1,
            )

        malformed = soundbank_editor.HircEditor(
            make_hirc(
                (soundbank_editor.HIRC_SOUND, 10, b"sound"),
                (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 20, b"bad"),
            )
        )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "unambiguous"):
            malformed.clone_random_sequence_container(
                20,
                21,
                ((10, 50_000),),
                expected_playlist=((10, 50_000),),
                expected_avoid_repeat_count=1,
            )

    def test_switch_container_topology_and_filtered_clone(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        donor_container_id = 368_774_789
        new_container_id = 4_294_967_000
        replacement_child_id = 925_721_864
        child_map = {
            child_id: replacement_child_id if child_id == 127_521_149 else None
            for child_id in DONOR_SWITCH_TOPOLOGY.children
        }

        self.assertEqual(
            editor.hirc.switch_container_topology(donor_container_id),
            DONOR_SWITCH_TOPOLOGY,
        )
        donor = editor.hirc.object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER, donor_container_id
        )
        editor.hirc.clone_switch_container(
            donor_container_id,
            new_container_id,
            child_map,
            expected_topology=DONOR_SWITCH_TOPOLOGY,
            expected_body_sha256=DONOR_SWITCH_BODY_SHA256,
        )

        cloned = editor.hirc.object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER, new_container_id
        )
        tail_marker = struct.pack(
            "<BIIB",
            DONOR_SWITCH_TOPOLOGY.group_type,
            DONOR_SWITCH_TOPOLOGY.group_id,
            DONOR_SWITCH_TOPOLOGY.default_switch,
            DONOR_SWITCH_TOPOLOGY.continuous_validation,
        )
        tail_offset = donor.index(tail_marker)
        self.assertEqual(cloned[4:tail_offset], donor[4:tail_offset])
        retained_switch_ids = tuple(
            switch_id
            for switch_id, node_ids in DONOR_SWITCH_TOPOLOGY.switch_packages
            if 127_521_149 in node_ids
        )
        expected = soundbank_editor.SwitchContainerTopology(
            group_type=0,
            group_id=3_251_135_135,
            default_switch=3_396_333_570,
            continuous_validation=0,
            children=(replacement_child_id,),
            switch_packages=tuple(
                (switch_id, (replacement_child_id,))
                for switch_id in retained_switch_ids
            ),
            node_params=(
                soundbank_editor.SwitchNodeParams(
                    replacement_child_id, 0, 1, 0, 0
                ),
            ),
        )
        self.assertEqual(
            editor.hirc.switch_container_topology(new_container_id), expected
        )
        rebuilt = editor.validate()
        self.assertEqual(
            soundbank_editor.HircEditor(
                rebuilt.hirc_payload, version=rebuilt.version
            ).switch_container_topology(new_container_id),
            expected,
        )

    def test_cloned_switch_is_serialized_after_its_latest_child(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        )
        editor = soundbank_editor.SoundBankEditor(bank)
        new_child_id = 4_294_966_999
        new_container_id = 4_294_967_000
        donor_sound_id = 925_721_864
        donor_sound = editor.hirc.object_body(
            soundbank_editor.HIRC_SOUND, donor_sound_id
        )
        donor_media_id = struct.unpack_from("<I", donor_sound, 9)[0]
        editor.hirc.clone_sound(
            donor_sound_id,
            new_child_id,
            donor_media_id,
            expected_source_id=donor_media_id,
        )
        editor.hirc.clone_switch_container(
            368_774_789,
            new_container_id,
            {
                child_id: new_child_id if child_id == 127_521_149 else None
                for child_id in DONOR_SWITCH_TOPOLOGY.children
            },
            expected_topology=DONOR_SWITCH_TOPOLOGY,
            expected_body_sha256=DONOR_SWITCH_BODY_SHA256,
        )

        positions = {item.object_id: item.index for item in editor.hirc.objects()}
        self.assertLess(positions[new_child_id], positions[new_container_id])
        editor.validate()

    def test_clone_switch_container_guards_inputs(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        )
        donor_container_id = 368_774_789
        child_map = {
            child_id: 925_721_864 if child_id == 127_521_149 else None
            for child_id in DONOR_SWITCH_TOPOLOGY.children
        }
        arguments = {
            "donor_container_id": donor_container_id,
            "new_container_id": 4_294_967_000,
            "child_map": child_map,
            "expected_topology": DONOR_SWITCH_TOPOLOGY,
            "expected_body_sha256": DONOR_SWITCH_BODY_SHA256,
        }

        editor = soundbank_editor.SoundBankEditor(bank)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "body SHA-256"):
            editor.hirc.clone_switch_container(
                **(arguments | {"expected_body_sha256": "00" * 32})
            )

        changed_topology = soundbank_editor.SwitchContainerTopology(
            **(
                DONOR_SWITCH_TOPOLOGY.__dict__
                | {"continuous_validation": 1}
            )
        )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "topology changed"):
            editor.hirc.clone_switch_container(
                **(arguments | {"expected_topology": changed_topology})
            )

        incomplete_map = dict(child_map)
        incomplete_map.pop(101_900_622)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "cover every donor"):
            editor.hirc.clone_switch_container(
                **(arguments | {"child_map": incomplete_map})
            )

        missing_child_map = dict(child_map)
        missing_child_map[127_521_149] = 4_294_966_999
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "does not exist"):
            editor.hirc.clone_switch_container(
                **(arguments | {"child_map": missing_child_map})
            )

        duplicate_map = {child_id: None for child_id in child_map}
        duplicate_map[127_521_149] = 925_721_864
        duplicate_map[125_400_496] = 925_721_864
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "must be unique"):
            editor.hirc.clone_switch_container(
                **(arguments | {"child_map": duplicate_map})
            )

        removed_default_map = {child_id: None for child_id in child_map}
        removed_default_map[125_400_496] = 925_721_864
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "default switch"):
            editor.hirc.clone_switch_container(
                **(arguments | {"child_map": removed_default_map})
            )

    def test_clone_switch_container_rejects_version_and_malformed_body(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "hm_cm00_epvsp.nbnk"
        )
        unsupported = soundbank_editor.HircEditor(
            bank.hirc_payload, version=121
        )
        child_map = {
            child_id: 925_721_864 if child_id == 127_521_149 else None
            for child_id in DONOR_SWITCH_TOPOLOGY.children
        }
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "requires Wwise v120"):
            unsupported.clone_switch_container(
                368_774_789,
                4_294_967_000,
                child_map,
                expected_topology=DONOR_SWITCH_TOPOLOGY,
                expected_body_sha256=DONOR_SWITCH_BODY_SHA256,
            )

        malformed_body = struct.pack("<I", 20) + b"bad"
        malformed = soundbank_editor.HircEditor(
            make_hirc(
                (soundbank_editor.HIRC_SOUND, 10, b"sound"),
                (soundbank_editor.HIRC_SWITCH_CONTAINER, 20, b"bad"),
            )
        )
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "unambiguous"):
            malformed.clone_switch_container(
                20,
                21,
                {child_id: None for child_id in DONOR_SWITCH_TOPOLOGY.children},
                expected_topology=DONOR_SWITCH_TOPOLOGY,
                expected_body_sha256=hashlib.sha256(malformed_body).hexdigest(),
            )

if __name__ == "__main__":
    unittest.main()
