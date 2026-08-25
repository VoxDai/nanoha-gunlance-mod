from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from builders.hm_cm00_epvsp import (
    DONOR_MEDIA_ID as GUARD_DONOR_MEDIA_ID,
    DONOR_RANDOM_ID as GUARD_DONOR_RANDOM_ID,
    DONOR_SOUND_ID as GUARD_DONOR_SOUND_ID,
    DONOR_SWITCH_ID as GUARD_DONOR_SWITCH_ID,
    DONOR_SWITCH_TOPOLOGY as GUARD_DONOR_SWITCH_TOPOLOGY,
    EVENT_ID as GUARD_EVENT_ID,
    EXCLUDED_SWITCH_IDS,
    ORIGINAL_ACTION_ID as GUARD_ORIGINAL_ACTION_ID,
    PLAN as GUARD_PLAN,
    RANDOM_MAX_INSTANCES_OFFSET,
    RANDOM_OVER_LIMIT_BEHAVIOR_OFFSET,
    RANDOM_PARENT_OFFSET,
    SOUND_PARENT_OFFSET,
    VOICE_ACTION_ID as GUARD_ACTION_ID,
    VOICE_MEDIA_IDS as GUARD_MEDIA_IDS,
    VOICE_RANDOM_ID as GUARD_RANDOM_ID,
    VOICE_SOUND_IDS as GUARD_SOUND_IDS,
    VOICE_SWITCH_ID as GUARD_SWITCH_ID,
    VOICE_SWITCH_IDS,
    VOICE_SWITCH_TOPOLOGY,
)
from builders.hm_wp07_snd_ev import PLAN as WWEV_PLAN
from builders.integration import (
    BANK_TARGET,
    LMT_TARGET,
    WWEV_TARGET,
    validate_stationary_draw,
)
from builders.w07_00 import PLAN as LMT_PLAN
from builders.wp07_gun_epvsp_shell import (
    FULL_BURST_ROUTES,
    PLAN as WP07_PLAN,
    POSITIONING_VECTOR_OFFSET as WP07_POSITIONING_OFFSET,
    WYVERNS_FIRE_ROUTES,
)
from builders.wp_cmn_epvsp import (
    DONOR_MEDIA_ID as SHARPEN_DONOR_MEDIA_ID,
    DONOR_SOUND_ID as SHARPEN_DONOR_SOUND_ID,
    EVENT_ID as SHARPEN_EVENT_ID,
    ORIGINAL_ACTION_ID as SHARPEN_ORIGINAL_ACTION_ID,
    PLAN as SHARPEN_PLAN,
    VOICE_ACTION_ID as SHARPEN_ACTION_ID,
    VOICE_MEDIA_ID as SHARPEN_MEDIA_ID,
    VOICE_SOUND_ID as SHARPEN_SOUND_ID,
)
from builders.wp_gun_cmn import (
    DONOR_MEDIA_ID as DRAW_DONOR_MEDIA_ID,
    DONOR_SOUND_ID as DRAW_DONOR_SOUND_ID,
    ORIGINAL_EVENT_ACTION_ID,
    ORIGINAL_EVENT_ID,
    ORIGINAL_ROUTE_ACTION_ID,
    PLAN as DRAW_PLAN,
    POSITIONING_VECTOR_OFFSET as DRAW_POSITIONING_OFFSET,
    VOICE_ACTION_ID as DRAW_ACTION_ID,
    VOICE_EVENT_ID as DRAW_EVENT_ID,
    VOICE_MEDIA_ID as DRAW_MEDIA_ID,
    VOICE_SOUND_ID as DRAW_SOUND_ID,
)
from tools import soundbank_editor

from ._soundbank_fixtures import make_random_container_tail


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def rebuild_bank(plan):
    original = soundbank_editor.SoundBank.from_file(PROJECT_ROOT / plan.source)
    editor = soundbank_editor.SoundBankEditor(original)
    placeholder = original.extract_media(index=1)
    for addition in plan.media_additions:
        editor.append_media(addition.media_id, placeholder)
    for replacement in plan.media_replacements:
        editor.replace_media(
            placeholder,
            index=replacement.index,
            expected_media_id=replacement.expected_media_id,
        )
    plan.apply_edits(editor)
    rebuilt = editor.validate()
    return original, editor, rebuilt


class SoundBankArtifactTestCase(unittest.TestCase):
    def assert_original_content_preserved(self, original, editor, rebuilt) -> None:
        for index, before in enumerate(original.entries, 1):
            after = rebuilt.media_entry(index=index)
            self.assertEqual((after.media_id, after.payload), (before.media_id, before.payload))

        diff = original.diff(rebuilt)
        self.assertEqual(diff.removed_hirc_objects, ())
        self.assertEqual(set(diff.added_hirc_objects), set(editor.summary.added_hirc_objects))
        expected_changed = {
            (object_type, object_id)
            for object_type, object_id, _before, _after in editor.summary.resized_hirc_objects
        }
        self.assertEqual(set(diff.changed_hirc_objects), expected_changed)

        original_hirc = soundbank_editor.HircEditor(
            original.hirc_payload, version=original.version
        )
        rebuilt_hirc = soundbank_editor.HircEditor(
            rebuilt.hirc_payload, version=rebuilt.version
        )
        for item in original_hirc.objects():
            key = (item.object_type, item.object_id)
            if key not in expected_changed:
                self.assertEqual(
                    rebuilt_hirc.object_body(*key),
                    original_hirc.object_body(*key),
                    key,
                )

        for before, after in zip(original.chunks, rebuilt.chunks):
            if before.tag not in (b"DIDX", b"DATA", b"HIRC"):
                self.assertEqual(after.raw, before.raw, before.tag)


class Wp07SoundBankTests(SoundBankArtifactTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original, cls.editor, cls.rebuilt = rebuild_bank(WP07_PLAN)
        cls.original_hirc = soundbank_editor.HircEditor(
            cls.original.hirc_payload, version=cls.original.version
        )
        cls.rebuilt_hirc = soundbank_editor.HircEditor(
            cls.rebuilt.hirc_payload, version=cls.rebuilt.version
        )

    def test_exact_summary_media_order_and_preservation(self) -> None:
        self.assertEqual(self.editor.summary, WP07_PLAN.expected_summary)
        self.assertEqual(
            tuple(entry.media_id for entry in self.rebuilt.entries[-4:]),
            tuple(item.media_id for item in WP07_PLAN.media_additions),
        )
        self.assert_original_content_preserved(
            self.original, self.editor, self.rebuilt
        )

    def test_every_event_action_and_donor_clone_is_exact(self) -> None:
        routes = (*FULL_BURST_ROUTES, *WYVERNS_FIRE_ROUTES)
        final_actions: dict[int, tuple[int, ...]] = {}
        for route in routes:
            final_actions[route.event_id] = route.expected_actions + (route.action_id,)
        for event_id, actions in final_actions.items():
            self.assertEqual(self.rebuilt_hirc.event_actions(event_id), actions)

        positions = {
            (item.object_type, item.object_id): index
            for index, item in enumerate(self.rebuilt_hirc.objects())
        }
        for route in routes:
            self.assertLess(
                positions[(soundbank_editor.HIRC_ACTION, route.action_id)],
                positions[(soundbank_editor.HIRC_EVENT, route.event_id)],
            )
            self.assertEqual(
                self.rebuilt_hirc.object_body(
                    soundbank_editor.HIRC_ACTION, route.action_id
                ),
                self.rebuilt_hirc.create_play_action(
                    route.action_id, route.sound_id, self.rebuilt.bank_id
                ),
            )
            expected_sound = bytearray(
                self.original_hirc.object_body(
                    soundbank_editor.HIRC_SOUND, route.donor_sound_id
                )
            )
            struct.pack_into("<I", expected_sound, 0, route.sound_id)
            struct.pack_into("<I", expected_sound, 9, route.media_id)
            if route.local_2d:
                self.assertEqual(expected_sound[WP07_POSITIONING_OFFSET], 0xC0)
                expected_sound[WP07_POSITIONING_OFFSET] = 0xC1
            self.assertEqual(
                self.rebuilt_hirc.object_body(
                    soundbank_editor.HIRC_SOUND, route.sound_id
                ),
                bytes(expected_sound),
            )


class SharpenSoundBankTests(SoundBankArtifactTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original, cls.editor, cls.rebuilt = rebuild_bank(SHARPEN_PLAN)
        cls.original_hirc = soundbank_editor.HircEditor(
            cls.original.hirc_payload, version=cls.original.version
        )
        cls.rebuilt_hirc = soundbank_editor.HircEditor(
            cls.rebuilt.hirc_payload, version=cls.rebuilt.version
        )

    def test_media_event_action_donor_and_summary_are_exact(self) -> None:
        self.assertEqual(self.editor.summary, SHARPEN_PLAN.expected_summary)
        self.assertEqual(self.rebuilt.media_entry(index=72).media_id, SHARPEN_MEDIA_ID)
        self.assertEqual(
            self.rebuilt_hirc.event_actions(SHARPEN_EVENT_ID),
            (SHARPEN_ORIGINAL_ACTION_ID, SHARPEN_ACTION_ID),
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, SHARPEN_ACTION_ID
            ),
            self.rebuilt_hirc.create_play_action(
                SHARPEN_ACTION_ID, SHARPEN_SOUND_ID, self.rebuilt.bank_id
            ),
        )
        expected_sound = bytearray(
            self.original_hirc.object_body(
                soundbank_editor.HIRC_SOUND, SHARPEN_DONOR_SOUND_ID
            )
        )
        struct.pack_into("<I", expected_sound, 0, SHARPEN_SOUND_ID)
        struct.pack_into("<I", expected_sound, 9, SHARPEN_MEDIA_ID)
        self.assertEqual(
            struct.unpack_from("<I", expected_sound, 9)[0], SHARPEN_MEDIA_ID
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                self.original_hirc.object_body(
                    soundbank_editor.HIRC_SOUND, SHARPEN_DONOR_SOUND_ID
                ),
                9,
            )[0],
            SHARPEN_DONOR_MEDIA_ID,
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_SOUND, SHARPEN_SOUND_ID
            ),
            bytes(expected_sound),
        )
        self.assert_original_content_preserved(
            self.original, self.editor, self.rebuilt
        )


class GunlanceGuardSoundBankTests(SoundBankArtifactTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original, cls.editor, cls.rebuilt = rebuild_bank(GUARD_PLAN)
        cls.original_hirc = soundbank_editor.HircEditor(
            cls.original.hirc_payload, version=cls.original.version
        )
        cls.rebuilt_hirc = soundbank_editor.HircEditor(
            cls.rebuilt.hirc_payload, version=cls.rebuilt.version
        )

    def test_exact_summary_counts_media_order_and_preservation(self) -> None:
        self.assertEqual(self.editor.summary, GUARD_PLAN.expected_summary)
        self.assertEqual(len(self.original.entries), 140)
        self.assertEqual(len(self.rebuilt.entries), 142)
        self.assertEqual(len(self.original_hirc.objects()), 597)
        self.assertEqual(len(self.rebuilt_hirc.objects()), 602)
        self.assertEqual(len(self.original.hirc_payload), 33_313)
        self.assertEqual(len(self.rebuilt.hirc_payload), 33_825)
        self.assertEqual(
            tuple(entry.media_id for entry in self.rebuilt.entries[-2:]),
            GUARD_MEDIA_IDS,
        )
        self.assert_original_content_preserved(
            self.original, self.editor, self.rebuilt
        )

    def test_original_guard_route_and_media_are_byte_exact(self) -> None:
        self.assertEqual(
            self.rebuilt_hirc.event_actions(GUARD_EVENT_ID),
            (GUARD_ORIGINAL_ACTION_ID, GUARD_ACTION_ID),
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, GUARD_ORIGINAL_ACTION_ID
            ),
            self.original_hirc.object_body(
                soundbank_editor.HIRC_ACTION, GUARD_ORIGINAL_ACTION_ID
            ),
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, GUARD_ORIGINAL_ACTION_ID
            ),
            self.rebuilt_hirc.create_play_action(
                GUARD_ORIGINAL_ACTION_ID,
                GUARD_DONOR_SWITCH_ID,
                self.rebuilt.bank_id,
                delay_ms=30,
            ),
        )
        for object_type, object_id in (
                (soundbank_editor.HIRC_SWITCH_CONTAINER, GUARD_DONOR_SWITCH_ID),
                (
                        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
                        GUARD_DONOR_RANDOM_ID,
                ),
                (soundbank_editor.HIRC_SOUND, GUARD_DONOR_SOUND_ID),
        ):
            self.assertEqual(
                self.rebuilt_hirc.object_body(object_type, object_id),
                self.original_hirc.object_body(object_type, object_id),
            )
        self.assertEqual(
            self.rebuilt.media_entry(index=88).media_id,
            GUARD_DONOR_MEDIA_ID,
        )
        self.assertEqual(
            self.rebuilt.media_entry(index=88).payload,
            self.original.media_entry(index=88).payload,
        )

    def test_new_action_and_sounds_are_exact_guarded_clones(self) -> None:
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, GUARD_ACTION_ID
            ),
            self.rebuilt_hirc.create_play_action(
                GUARD_ACTION_ID,
                GUARD_SWITCH_ID,
                self.rebuilt.bank_id,
                delay_ms=30,
            ),
        )
        positions = {
            (item.object_type, item.object_id): index
            for index, item in enumerate(self.rebuilt_hirc.objects())
        }
        self.assertLess(
            positions[(soundbank_editor.HIRC_ACTION, GUARD_ACTION_ID)],
            positions[(soundbank_editor.HIRC_EVENT, GUARD_EVENT_ID)],
        )

        donor = self.original_hirc.object_body(
            soundbank_editor.HIRC_SOUND, GUARD_DONOR_SOUND_ID
        )
        for sound_id, media_id in zip(
                GUARD_SOUND_IDS, GUARD_MEDIA_IDS, strict=True
        ):
            expected = bytearray(donor)
            struct.pack_into("<I", expected, 0, sound_id)
            struct.pack_into("<I", expected, 9, media_id)
            struct.pack_into(
                "<I", expected, SOUND_PARENT_OFFSET, GUARD_RANDOM_ID
            )
            self.assertEqual(
                self.rebuilt_hirc.object_body(
                    soundbank_editor.HIRC_SOUND, sound_id
                ),
                bytes(expected),
            )

    def test_random_is_equal_weight_kill_newest_single_instance(self) -> None:
        donor = self.original_hirc.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            GUARD_DONOR_RANDOM_ID,
        )
        donor_tail = make_random_container_tail((GUARD_DONOR_SOUND_ID, 50_000))
        self.assertTrue(donor.endswith(donor_tail))
        expected_prefix = bytearray(donor[: -len(donor_tail)])
        struct.pack_into("<I", expected_prefix, 0, GUARD_RANDOM_ID)
        struct.pack_into(
            "<I", expected_prefix, RANDOM_PARENT_OFFSET, GUARD_SWITCH_ID
        )
        expected_prefix[RANDOM_OVER_LIMIT_BEHAVIOR_OFFSET] = 1
        struct.pack_into(
            "<H", expected_prefix, RANDOM_MAX_INSTANCES_OFFSET, 1
        )
        struct.pack_into("<H", expected_prefix, len(expected_prefix) - 6, 0)
        expected = bytes(expected_prefix) + make_random_container_tail(
            (GUARD_SOUND_IDS[0], 50_000),
            (GUARD_SOUND_IDS[1], 50_000),
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
                GUARD_RANDOM_ID,
            ),
            expected,
        )

    def test_switch_only_retains_gunlance_guard_packages(self) -> None:
        self.assertEqual(
            self.original_hirc.switch_container_topology(GUARD_DONOR_SWITCH_ID),
            GUARD_DONOR_SWITCH_TOPOLOGY,
        )
        self.assertEqual(
            self.rebuilt_hirc.switch_container_topology(GUARD_SWITCH_ID),
            VOICE_SWITCH_TOPOLOGY,
        )
        package_ids = tuple(
            switch_id
            for switch_id, _node_ids in VOICE_SWITCH_TOPOLOGY.switch_packages
        )
        self.assertEqual(package_ids, VOICE_SWITCH_IDS)
        self.assertTrue(set(EXCLUDED_SWITCH_IDS).isdisjoint(package_ids))

        donor = self.original_hirc.object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER, GUARD_DONOR_SWITCH_ID
        )
        cloned = self.rebuilt_hirc.object_body(
            soundbank_editor.HIRC_SWITCH_CONTAINER, GUARD_SWITCH_ID
        )
        tail_marker = struct.pack(
            "<BIIB",
            GUARD_DONOR_SWITCH_TOPOLOGY.group_type,
            GUARD_DONOR_SWITCH_TOPOLOGY.group_id,
            GUARD_DONOR_SWITCH_TOPOLOGY.default_switch,
            GUARD_DONOR_SWITCH_TOPOLOGY.continuous_validation,
        )
        tail_offset = donor.index(tail_marker)
        self.assertEqual(cloned[4:tail_offset], donor[4:tail_offset])


class StationaryDrawSoundBankTests(SoundBankArtifactTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original, cls.editor, cls.rebuilt = rebuild_bank(DRAW_PLAN)
        cls.original_hirc = soundbank_editor.HircEditor(
            cls.original.hirc_payload, version=cls.original.version
        )
        cls.rebuilt_hirc = soundbank_editor.HircEditor(
            cls.rebuilt.hirc_payload, version=cls.rebuilt.version
        )

    def test_isolated_event_routes_to_original_and_voice_in_order(self) -> None:
        self.assertEqual(self.editor.summary, DRAW_PLAN.expected_summary)
        self.assertEqual(self.rebuilt.media_entry(index=34).media_id, DRAW_MEDIA_ID)
        self.assertEqual(
            self.rebuilt_hirc.event_actions(DRAW_EVENT_ID),
            (ORIGINAL_ROUTE_ACTION_ID, DRAW_ACTION_ID),
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, ORIGINAL_ROUTE_ACTION_ID
            ),
            self.rebuilt_hirc.create_play_event_action(
                ORIGINAL_ROUTE_ACTION_ID, ORIGINAL_EVENT_ID
            ),
        )
        self.assertEqual(
            self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, DRAW_ACTION_ID
            ),
            self.rebuilt_hirc.create_play_action(
                DRAW_ACTION_ID, DRAW_SOUND_ID, self.rebuilt.bank_id
            ),
        )
        self.assertEqual(
            self.rebuilt_hirc.event_actions(ORIGINAL_EVENT_ID),
            (ORIGINAL_EVENT_ACTION_ID,),
        )

    def test_voice_sound_is_guarded_donor_clone_and_originals_are_exact(self) -> None:
        expected_sound = bytearray(
            self.original_hirc.object_body(
                soundbank_editor.HIRC_SOUND, DRAW_DONOR_SOUND_ID
            )
        )
        self.assertEqual(struct.unpack_from("<I", expected_sound, 9)[0], DRAW_DONOR_MEDIA_ID)
        struct.pack_into("<I", expected_sound, 0, DRAW_SOUND_ID)
        struct.pack_into("<I", expected_sound, 9, DRAW_MEDIA_ID)
        self.assertEqual(expected_sound[DRAW_POSITIONING_OFFSET], 0xC0)
        expected_sound[DRAW_POSITIONING_OFFSET] = 0xC1
        self.assertEqual(
            self.rebuilt_hirc.object_body(soundbank_editor.HIRC_SOUND, DRAW_SOUND_ID),
            bytes(expected_sound),
        )
        self.assert_original_content_preserved(
            self.original, self.editor, self.rebuilt
        )


class EventArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original_lmt = soundbank_editor.LmtFile.from_file(
            PROJECT_ROOT / LMT_PLAN.source
        )
        cls.lmt_editor = soundbank_editor.LmtEditor(cls.original_lmt)
        LMT_PLAN.apply_edits(cls.lmt_editor)
        cls.rebuilt_lmt = cls.lmt_editor.validate()

        cls.original_wwev = soundbank_editor.WwevFile.from_file(
            PROJECT_ROOT / WWEV_PLAN.source
        )
        cls.wwev_editor = soundbank_editor.WwevEditor(cls.original_wwev)
        WWEV_PLAN.apply_edits(cls.wwev_editor)
        cls.rebuilt_wwev = cls.wwev_editor.validate()

    def test_lmt_is_one_byte_and_has_fixed_output_hash(self) -> None:
        before = self.original_lmt.to_bytes()
        after = self.lmt_editor.build()
        self.assertEqual(self.lmt_editor.summary, LMT_PLAN.expected_summary)
        self.assertEqual(len(after), len(before))
        self.assertEqual(
            [index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]],
            [0xCC50],
        )
        self.assertEqual(hashlib.sha256(after).hexdigest(), LMT_PLAN.expected_output_sha256)

    def test_wwev_clone_preserves_boundaries_and_has_fixed_output_hash(self) -> None:
        before = self.original_wwev.to_bytes()
        after = self.wwev_editor.build()
        self.assertEqual(self.wwev_editor.summary, WWEV_PLAN.expected_summary)
        self.assertEqual(len(self.original_wwev.records), 43)
        self.assertEqual(len(self.rebuilt_wwev.records), 44)
        self.assertEqual(len(after) - len(before), 129)
        self.assertEqual(after[:8], before[:8])
        self.assertEqual(after[12 : len(before)], before[12:])
        self.assertEqual(
            self.rebuilt_wwev.records[:43], self.original_wwev.records
        )
        donor = self.original_wwev.record(6470)
        appended = self.rebuilt_wwev.record(6592)
        self.assertEqual(appended.size, donor.size)
        self.assertEqual(appended.unknown, donor.unknown)
        self.assertEqual(appended.command_hash, donor.command_hash)
        self.assertEqual(appended.wwpc, donor.wwpc)
        self.assertEqual(
            self.rebuilt_wwev.dependencies, self.original_wwev.dependencies
        )
        self.assertEqual(
            hashlib.sha256(after).hexdigest(), WWEV_PLAN.expected_output_sha256
        )

    def test_real_cross_format_route_is_unique(self) -> None:
        routes = [
            route
            for route in self.rebuilt_lmt.triggered_requests(self.rebuilt_wwev)
            if route.request_no == 6592 or route.event_id == 3_176_129_810
        ]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(
            (
                route.motion_id,
                route.trigger_frame,
                route.slot,
                route.request_no,
                route.wwev_mode,
                route.event_id,
            ),
            (2, 9.0, "B", 6592, 2, 3_176_129_810),
        )

    def test_bundle_validator_connects_route_to_both_audio_branches(self) -> None:
        _original, bank_editor, _rebuilt = rebuild_bank(DRAW_PLAN)
        with tempfile.TemporaryDirectory(prefix="builder-bundle-test.") as directory:
            root = Path(directory)
            paths = {
                LMT_TARGET: root / LMT_TARGET,
                WWEV_TARGET: root / WWEV_TARGET,
                BANK_TARGET: root / BANK_TARGET,
            }
            for path in paths.values():
                path.parent.mkdir(parents=True, exist_ok=True)
            paths[LMT_TARGET].write_bytes(self.lmt_editor.build())
            paths[WWEV_TARGET].write_bytes(self.wwev_editor.build())
            paths[BANK_TARGET].write_bytes(bank_editor.build())
            validate_stationary_draw(paths)


if __name__ == "__main__":
    unittest.main()
