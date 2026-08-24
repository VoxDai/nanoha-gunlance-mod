from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

import builders.base as builder_base
from builders.__main__ import MOD_PLAN
from builders.base import (
    BuildError,
    MediaAddition,
    MediaReplacement,
    ModBuildPlan,
    prepare_all_plans,
    prepare_plan,
    validate_registry,
)
from builders.w07_00 import PLAN as LMT_PLAN
from builders.wp07_gun_epvsp_shell import PLAN as WP07_PLAN
from builders.wp_cmn_epvsp import PLAN as SHARPEN_PLAN
from tools import soundbank_editor


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def append_undeclared_media(editor: soundbank_editor.SoundBankEditor) -> None:
    editor.append_media(242_768_048, editor.original.extract_media(index=1))


class ExplicitPlanTests(unittest.TestCase):
    def test_public_plan_api_has_no_mapping_parser_types(self) -> None:
        for name in (
            "MediaReplacement",
            "MediaAddition",
            "SoundBankBuildPlan",
            "LmtBuildPlan",
            "WwevBuildPlan",
            "ModBuildPlan",
        ):
            self.assertIn(name, builder_base.__all__)
            self.assertTrue(hasattr(builder_base, name))
        for removed in ("MappingInfo", "MappingMediaOverlay", "parse_mapping"):
            self.assertFalse(hasattr(builder_base, removed))

    def test_registry_is_exactly_the_five_design_artifacts(self) -> None:
        validate_registry(MOD_PLAN)
        self.assertEqual(len(MOD_PLAN.artifacts), 5)
        self.assertEqual(
            {plan.name for plan in MOD_PLAN.artifacts},
            {
                "wp07_gun_epvsp_shell",
                "wp_cmn_epvsp",
                "wp_gun_cmn",
                "w07_00",
                "hm_wp07_snd_ev",
            },
        )
        self.assertEqual(
            {str(plan.target) for plan in MOD_PLAN.artifacts},
            {
                "sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk",
                "sound/wwise/Windows/wp_cmn_epvsp.nbnk",
                "sound/wwise/Windows/wp_gun_cmn.nbnk",
                "hm/wp/wp07/mot/w07_00/w07_00.lmt",
                "sound/pl/hm_wp07_snd_ev.wwev",
            },
        )
        self.assertEqual(
            {design for plan in MOD_PLAN.artifacts for design in plan.design_ids},
            {
                "wp07_gun_epvsp_shell.full_burst",
                "wp07_gun_epvsp_shell.wyverns_fire",
                "wp_cmn_epvsp.sharpen",
                "wp_gun_cmn.stationary_draw",
            },
        )
        for removed in (
            "cm_hitmark_epvsp.py",
            "hm_cm00_epvsp.py",
            "pl_prop_cmn.py",
        ):
            self.assertFalse((PROJECT_ROOT / "builders" / removed).exists())

    def test_all_sources_hashes_and_summaries_preflight(self) -> None:
        prepared = prepare_all_plans(MOD_PLAN, PROJECT_ROOT)
        self.assertEqual(
            [item.plan.name for item in prepared],
            [item.name for item in MOD_PLAN.artifacts],
        )
        for item in prepared:
            self.assertEqual(item.preview_summary, item.plan.expected_summary)

    def test_declared_paths_reject_escape_and_nativepc_prefix(self) -> None:
        with self.assertRaisesRegex(ValueError, "safe project-relative"):
            MediaAddition(1, 1, "../voice.wav")
        with self.assertRaisesRegex(ValueError, "must not include"):
            replace(
                WP07_PLAN,
                target="nativePC/sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk",
            )
        with self.assertRaisesRegex(ValueError, "safe project-relative"):
            replace(WP07_PLAN, target="../outside.nbnk")

    def test_source_sha_guard_fails_before_editing(self) -> None:
        bad = replace(LMT_PLAN, expected_source_sha256="00" * 32)
        with self.assertRaisesRegex(BuildError, "source SHA-256"):
            prepare_plan(bad, PROJECT_ROOT)

    def test_media_index_and_identity_guards(self) -> None:
        addition = SHARPEN_PLAN.media_additions[0]
        wrong_index = replace(
            SHARPEN_PLAN,
            media_additions=(replace(addition, expected_index=73),),
        )
        with self.assertRaisesRegex(BuildError, "added media indices"):
            prepare_plan(wrong_index, PROJECT_ROOT)

        original = soundbank_editor.SoundBank.from_file(
            PROJECT_ROOT / SHARPEN_PLAN.source
        )
        collision = replace(
            SHARPEN_PLAN,
            media_additions=(replace(addition, media_id=original.entries[0].media_id),),
        )
        with self.assertRaisesRegex(BuildError, "Media ID already exists"):
            prepare_plan(collision, PROJECT_ROOT)

        replacement = replace(
            SHARPEN_PLAN,
            media_additions=(),
            media_replacements=(
                MediaReplacement(
                    1,
                    original.entries[0].media_id + 1,
                    addition.source_audio,
                ),
            ),
        )
        with self.assertRaisesRegex(BuildError, "expected Media ID"):
            prepare_plan(replacement, PROJECT_ROOT)

    def test_duplicate_target_and_summary_mismatch_are_rejected(self) -> None:
        duplicate = replace(
            LMT_PLAN,
            name="w07_00_duplicate",
            source="original/lmt/w07_00_duplicate.lmt",
        )
        with self.assertRaisesRegex(BuildError, "Duplicate target artifact"):
            validate_registry(ModBuildPlan((LMT_PLAN, duplicate)))

        wrong_summary = replace(
            LMT_PLAN,
            expected_summary=soundbank_editor.LmtEditSummary(0, ()),
        )
        with self.assertRaisesRegex(BuildError, "edit summary differs"):
            prepare_plan(wrong_summary, PROJECT_ROOT)

    def test_hirc_callback_cannot_hide_undeclared_media_edits(self) -> None:
        undeclared = replace(
            WP07_PLAN,
            media_additions=(),
            apply_edits=append_undeclared_media,
            expected_summary=soundbank_editor.SoundBankEditSummary(
                replaced_media=(),
                added_media=((43, 242_768_048),),
                hirc_changed_bytes=0,
                added_hirc_objects=(),
                resized_hirc_objects=(),
                hirc_size_delta=0,
            ),
        )
        with self.assertRaisesRegex(BuildError, "undeclared media additions"):
            prepare_plan(undeclared, PROJECT_ROOT)


if __name__ == "__main__":
    unittest.main()
