from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from tools import soundbank_editor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOUNDBANK_ROOT = PROJECT_ROOT / "original" / "soundbank"


def make_hirc(*records: tuple[int, int, bytes]) -> bytes:
    payload = bytearray(struct.pack("<I", len(records)))
    for object_type, object_id, body_tail in records:
        body = struct.pack("<I", object_id) + body_tail
        payload += struct.pack("<BI", object_type, len(body)) + body
    return bytes(payload)


def make_random_container_tail(*playlist: tuple[int, int]) -> bytes:
    payload = bytearray(struct.pack("<I", len(playlist)))
    payload += struct.pack(
        f"<{len(playlist)}I", *(child_id for child_id, _ in playlist)
    )
    payload += struct.pack("<H", len(playlist))
    for child_id, weight in playlist:
        payload += struct.pack("<Ii", child_id, weight)
    return bytes(payload)


class SoundBankRoundTripTests(unittest.TestCase):
    def test_every_original_bank_round_trips_byte_exactly(self) -> None:
        for path in sorted(SOUNDBANK_ROOT.glob("*.nbnk")):
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

    def test_atomic_write_refuses_input_and_reads_back(self) -> None:
        editor = soundbank_editor.SoundBankEditor(self.bank)
        with self.assertRaisesRegex(soundbank_editor.SoundBankError, "overwriting"):
            editor.write_atomic(self.path)
        with tempfile.TemporaryDirectory(prefix="soundbank-editor-test.", dir="/tmp") as directory:
            output = Path(directory) / self.path.name
            editor.write_atomic(output)
            self.assertEqual(output.read_bytes(), self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
