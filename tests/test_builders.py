from __future__ import annotations

import struct
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from builders.__main__ import PLANS
from builders.base import (
    BankBuildPlan,
    BuildError,
    MappingInfo,
    MappingMediaOverlay,
    Replacement,
    ToolPaths,
    convert_replacements,
    parse_mapping,
    partition_mapping_edits,
    prepare_plan,
    validate_registry,
)
from builders.wp07_gun_epvsp_shell import (
    FULL_BURST_MAPPING_INDICES,
    FULL_BURST_OVERLAY_MEDIA_ID,
    FULL_BURST_OVERLAY_ROUTES,
    PLAN as WP07_PLAN,
    POSITIONING_VECTOR_OFFSET,
    apply_edits as apply_wp07_edits,
)
from tools import soundbank_editor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAPPING_ROOT = PROJECT_ROOT / "docs" / "mapping"
SOUNDBANK_ROOT = PROJECT_ROOT / "original" / "nbnk"


def noop_edits(_editor: soundbank_editor.SoundBankEditor) -> None:
    """Use a named no-op callback in synthetic build plans."""


def synthetic_mapping(*sources: str) -> MappingInfo:
    return MappingInfo(
        path=Path("synthetic.md"),
        bank_name="synthetic",
        data_rows=len(sources),
        replacements=[
            Replacement(index, Path(source), index)
            for index, source in enumerate(sources, 1)
        ],
        unresolved_rows=[],
    )


class MappingTests(unittest.TestCase):
    def test_registry_matches_every_mapping_and_soundbank(self) -> None:
        validate_registry(PLANS, MAPPING_ROOT, SOUNDBANK_ROOT)
        self.assertEqual(
            {plan.name for plan in PLANS},
            {
                "cm_hitmark_epvsp",
                "hm_cm00_epvsp",
                "pl_prop_cmn",
                "wp07_gun_epvsp_shell",
                "wp_cmn_epvsp",
                "wp_gun_cmn",
            },
        )

    def test_current_mapping_replacements_and_unresolved_rows(self) -> None:
        parsed = {
            path.stem: parse_mapping(path, PROJECT_ROOT)
            for path in sorted(MAPPING_ROOT.glob("*.md"))
        }
        self.assertEqual(
            [item.index for item in parsed["wp07_gun_epvsp_shell"].replacements],
            [2, 4, 9, 15, 19, 23, 27, 29, 30, 33, 34, 37],
        )
        self.assertEqual(
            [item.index for item in parsed["wp_cmn_epvsp"].replacements], [52]
        )
        for name in (
            "cm_hitmark_epvsp",
            "hm_cm00_epvsp",
            "pl_prop_cmn",
            "wp_gun_cmn",
        ):
            self.assertEqual(parsed[name].replacements, [])
        self.assertEqual(len(parsed["cm_hitmark_epvsp"].unresolved_rows), 1)
        self.assertEqual(len(parsed["wp_gun_cmn"].unresolved_rows), 0)

    def test_wp07_overlay_rows_are_removed_from_replacements(self) -> None:
        prepared = prepare_plan(
            WP07_PLAN,
            PROJECT_ROOT,
            MAPPING_ROOT,
            SOUNDBANK_ROOT,
        )
        self.assertEqual(
            tuple(item.index for item in prepared.replacements),
            (4, 19, 23, 27, 29, 33, 37),
        )
        self.assertEqual(len(prepared.media_overlays), 1)
        overlay = prepared.media_overlays[0]
        self.assertEqual(overlay.config.indices, FULL_BURST_MAPPING_INDICES)
        self.assertEqual(overlay.config.media_id, FULL_BURST_OVERLAY_MEDIA_ID)
        self.assertEqual(
            overlay.source_audio,
            PROJECT_ROOT / "audio" / "wp07_gun_epvsp_shell" / "shoot.wav",
        )
        self.assertEqual(prepared.preview_summary.replaced_media, ())
        self.assertEqual(
            prepared.preview_summary.added_media,
            ((43, FULL_BURST_OVERLAY_MEDIA_ID),),
        )
        self.assertEqual(prepared.preview_summary.hirc_changed_bytes, 10)
        self.assertEqual(len(prepared.preview_summary.added_hirc_objects), 10)
        self.assertEqual(len(prepared.preview_summary.resized_hirc_objects), 5)
        self.assertEqual(prepared.preview_summary.hirc_size_delta, 520)

    def test_overlay_requires_mapped_rows_with_one_source(self) -> None:
        missing = BankBuildPlan(
            "synthetic",
            noop_edits,
            (MappingMediaOverlay((1, 3), 100),),
        )
        with self.assertRaisesRegex(BuildError, "rows without Audio replacements"):
            partition_mapping_edits(missing, synthetic_mapping("same.wav", "same.wav"))

        split = BankBuildPlan(
            "synthetic",
            noop_edits,
            (MappingMediaOverlay((1, 2), 100),),
        )
        with self.assertRaisesRegex(BuildError, "one source audio file"):
            partition_mapping_edits(split, synthetic_mapping("one.wav", "two.wav"))

    def test_overlay_indices_cannot_be_claimed_twice(self) -> None:
        plan = BankBuildPlan(
            "synthetic",
            noop_edits,
            (
                MappingMediaOverlay((1, 2), 100),
                MappingMediaOverlay((2,), 101),
            ),
        )
        with self.assertRaisesRegex(BuildError, "claimed by mapping media overlays"):
            partition_mapping_edits(plan, synthetic_mapping("same.wav", "same.wav"))

    def test_overlay_media_id_collision_fails_preflight(self) -> None:
        bank = soundbank_editor.SoundBank.from_file(
            SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        )
        plan = BankBuildPlan(
            "wp07_gun_epvsp_shell",
            noop_edits,
            (
                MappingMediaOverlay(
                    FULL_BURST_MAPPING_INDICES,
                    bank.entries[0].media_id,
                ),
            ),
        )
        with self.assertRaisesRegex(BuildError, "Media ID already exists"):
            prepare_plan(plan, PROJECT_ROOT, MAPPING_ROOT, SOUNDBANK_ROOT)

    def test_overlay_shared_source_is_converted_once(self) -> None:
        prepared = prepare_plan(
            WP07_PLAN,
            PROJECT_ROOT,
            MAPPING_ROOT,
            SOUNDBANK_ROOT,
        )
        placeholder_wem = prepared.original_bank.extract_media(index=2)
        commands: list[list[str]] = []

        def fake_run_tool(
            command: list[str], _label: str, _working_directory: Path
        ) -> None:
            commands.append(command)
            Path(command[3]).write_bytes(placeholder_wem)

        fake_tools = ToolPaths(
            Path("converter.py"), Path("pyvgmstream.py"), Path("wwiser.py")
        )
        with tempfile.TemporaryDirectory(
            prefix="mapping-overlay-test.", dir="/tmp"
        ) as directory, mock.patch(
            "builders.base.run_tool", side_effect=fake_run_tool
        ):
            payloads = convert_replacements(
                prepared,
                Path(directory),
                PROJECT_ROOT,
                fake_tools,
            )

        overlay_source = prepared.media_overlays[0].source_audio
        overlay_commands = [
            command
            for command in commands
            if Path(command[2]).resolve() == overlay_source
        ]
        self.assertEqual(len(overlay_commands), 1)
        self.assertEqual(payloads[1], placeholder_wem)
        self.assertFalse(
            {index - 1 for index in FULL_BURST_MAPPING_INDICES[1:]} & payloads.keys()
        )


class Wp07OverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = SOUNDBANK_ROOT / "wp07_gun_epvsp_shell.nbnk"
        cls.original = soundbank_editor.SoundBank.from_file(source)
        cls.original_hirc = soundbank_editor.HircEditor(cls.original.hirc_payload)
        cls.editor = soundbank_editor.SoundBankEditor(cls.original)
        cls.editor.append_media(
            FULL_BURST_OVERLAY_MEDIA_ID,
            cls.original.extract_media(index=FULL_BURST_MAPPING_INDICES[0]),
        )
        apply_wp07_edits(cls.editor)
        cls.rebuilt = cls.editor.validate()
        cls.rebuilt_hirc = soundbank_editor.HircEditor(cls.rebuilt.hirc_payload)

    def test_exact_structural_summary(self) -> None:
        summary = self.editor.summary
        expected_added = tuple(
            item
            for route in FULL_BURST_OVERLAY_ROUTES
            for item in (
                (soundbank_editor.HIRC_SOUND, route.sound_id),
                (soundbank_editor.HIRC_ACTION, route.action_id),
            )
        )
        expected_resized = {
            (soundbank_editor.HIRC_EVENT, route.event_id, 12, 16)
            for route in FULL_BURST_OVERLAY_ROUTES
        }
        self.assertEqual(summary.replaced_media, ())
        self.assertEqual(summary.added_media, ((43, FULL_BURST_OVERLAY_MEDIA_ID),))
        self.assertEqual(summary.hirc_changed_bytes, 10)
        self.assertEqual(summary.added_hirc_objects, expected_added)
        self.assertEqual(set(summary.resized_hirc_objects), expected_resized)
        self.assertEqual(summary.hirc_size_delta, 520)

    def test_overlay_mapping_media_remains_byte_exact(self) -> None:
        for index in FULL_BURST_MAPPING_INDICES:
            before = self.original.media_entry(index=index)
            after = self.rebuilt.media_entry(index=index)
            self.assertEqual(after.media_id, before.media_id, index)
            self.assertEqual(after.payload, before.payload, index)
        added = self.rebuilt.media_entry(index=43)
        self.assertEqual(added.media_id, FULL_BURST_OVERLAY_MEDIA_ID)
        self.assertEqual(added.offset % soundbank_editor.ALIGNMENT, 0)

    def test_five_event_action_sound_media_routes(self) -> None:
        positions = {
            (item.object_type, item.object_id): position
            for position, item in enumerate(self.rebuilt_hirc.objects())
        }
        for route in FULL_BURST_OVERLAY_ROUTES:
            self.assertEqual(
                self.rebuilt_hirc.event_actions(route.event_id),
                (route.expected_action_id, route.action_id),
            )
            self.assertEqual(
                positions[(soundbank_editor.HIRC_ACTION, route.action_id)] + 1,
                positions[(soundbank_editor.HIRC_EVENT, route.event_id)],
            )
            action = self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_ACTION, route.action_id
            )
            expected_action = self.rebuilt_hirc.create_play_action(
                route.action_id, route.sound_id, self.rebuilt.bank_id
            )
            self.assertEqual(action, expected_action)

            donor = self.original_hirc.object_body(
                soundbank_editor.HIRC_SOUND, route.donor_sound_id
            )
            expected_sound = bytearray(donor)
            struct.pack_into("<I", expected_sound, 0, route.sound_id)
            struct.pack_into("<I", expected_sound, 9, FULL_BURST_OVERLAY_MEDIA_ID)
            expected_sound[POSITIONING_VECTOR_OFFSET] = 0xC1
            actual_sound = self.rebuilt_hirc.object_body(
                soundbank_editor.HIRC_SOUND, route.sound_id
            )
            self.assertEqual(actual_sound, bytes(expected_sound))

    def test_only_five_original_events_change(self) -> None:
        diff = self.original.diff(self.rebuilt)
        expected_events = {
            (soundbank_editor.HIRC_EVENT, route.event_id)
            for route in FULL_BURST_OVERLAY_ROUTES
        }
        expected_added = {
            item
            for route in FULL_BURST_OVERLAY_ROUTES
            for item in (
                (soundbank_editor.HIRC_SOUND, route.sound_id),
                (soundbank_editor.HIRC_ACTION, route.action_id),
            )
        }
        self.assertEqual(set(diff.changed_hirc_objects), expected_events)
        self.assertEqual(set(diff.added_hirc_objects), expected_added)
        self.assertEqual(diff.removed_hirc_objects, ())

    def test_paired_events_remain_unchanged(self) -> None:
        for event_id in (719268880, 678619471, 2432475814):
            self.assertEqual(
                self.rebuilt_hirc.object_body(soundbank_editor.HIRC_EVENT, event_id),
                self.original_hirc.object_body(soundbank_editor.HIRC_EVENT, event_id),
            )

    def test_other_builders_are_hirc_noops(self) -> None:
        for plan in PLANS:
            if plan.name == "wp07_gun_epvsp_shell":
                continue
            bank = soundbank_editor.SoundBank.from_file(
                SOUNDBANK_ROOT / f"{plan.name}.nbnk"
            )
            editor = soundbank_editor.SoundBankEditor(bank)
            plan.apply_edits(editor)
            self.assertEqual(editor.build(), bank.to_bytes(), plan.name)
            self.assertEqual(editor.hirc.changed_byte_count, 0, plan.name)


if __name__ == "__main__":
    unittest.main()
