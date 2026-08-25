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
from builders.hm_cm00_epvsp import PLAN as GUARD_PLAN
from builders.hm_wp07_snd_ev import PLAN as WWEV_PLAN
from builders.w07_00 import PLAN as LMT_PLAN
from builders.wp07_gun_epvsp_shell import PLAN as WP07_PLAN
from builders.wp_cmn_epvsp import PLAN as SHARPEN_PLAN
from builders.wp_gun_cmn import PLAN as WP_GUN_PLAN
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

    def test_registry_is_exactly_the_six_design_artifacts(self) -> None:
        validate_registry(MOD_PLAN)
        self.assertEqual(len(MOD_PLAN.artifacts), 6)
        self.assertEqual(
            {plan.name for plan in MOD_PLAN.artifacts},
            {
                "wp07_gun_epvsp_shell",
                "wp_cmn_epvsp",
                "wp_gun_cmn",
                "hm_cm00_epvsp",
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
                "sound/wwise/Windows/hm_cm00_epvsp.nbnk",
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
                "wp_gun_cmn.overhead_smash",
                "hm_cm00_epvsp.gunlance_guard",
            },
        )
        self.assertEqual(
            tuple(validator.design_id for validator in MOD_PLAN.validators),
            (
                "wp_gun_cmn.stationary_draw",
                "wp_gun_cmn.overhead_smash",
            ),
        )
        for removed in (
            "cm_hitmark_epvsp.py",
            "pl_prop_cmn.py",
        ):
            self.assertFalse((PROJECT_ROOT / "builders" / removed).exists())

    def test_gunlance_guard_plan_identity_and_media_are_explicit(self) -> None:
        self.assertEqual(
            GUARD_PLAN.design_ids,
            ("hm_cm00_epvsp.gunlance_guard",),
        )
        self.assertEqual(
            str(GUARD_PLAN.source),
            "original/nbnk/hm_cm00_epvsp.nbnk",
        )
        self.assertEqual(
            str(GUARD_PLAN.target),
            "sound/wwise/Windows/hm_cm00_epvsp.nbnk",
        )
        self.assertEqual(GUARD_PLAN.expected_bank_id, 707_566_772)
        self.assertEqual(
            GUARD_PLAN.expected_source_sha256,
            "73b52c1a69532f0a84ab6dfa2e95bd804bf8affc5af77450786d700c177a9977",
        )
        self.assertEqual(
            tuple(
                (item.expected_index, item.media_id, str(item.source_audio))
                for item in GUARD_PLAN.media_additions
            ),
            (
                (
                    141,
                    141_209_263,
                    "audio/hm_cm00_epvsp/"
                    "raising_heart_protection_01(movie_1st.raising_heart."
                    "protection_01.1).wav",
                ),
                (
                    142,
                    440_767_416,
                    "audio/hm_cm00_epvsp/"
                    "raising_heart_protection_02(movie_1st.raising_heart."
                    "protection_02.1).wav",
                ),
            ),
        )

    def test_overhead_smash_shared_plans_and_media_are_explicit(self) -> None:
        expected_designs = (
            "wp_gun_cmn.stationary_draw",
            "wp_gun_cmn.overhead_smash",
        )
        for plan in (WP_GUN_PLAN, LMT_PLAN, WWEV_PLAN):
            self.assertEqual(plan.design_ids, expected_designs)
        self.assertEqual(
            (
                str(WP_GUN_PLAN.source),
                str(WP_GUN_PLAN.target),
                WP_GUN_PLAN.expected_bank_id,
                WP_GUN_PLAN.expected_source_sha256,
            ),
            (
                "original/nbnk/wp_gun_cmn.nbnk",
                "sound/wwise/Windows/wp_gun_cmn.nbnk",
                939_294_496,
                "bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1",
            ),
        )
        self.assertEqual(
            (str(LMT_PLAN.source), str(LMT_PLAN.target)),
            (
                "original/lmt/w07_00.lmt",
                "hm/wp/wp07/mot/w07_00/w07_00.lmt",
            ),
        )
        self.assertEqual(
            (str(WWEV_PLAN.source), str(WWEV_PLAN.target)),
            (
                "original/wwev/hm_wp07_snd_ev.wwev",
                "sound/pl/hm_wp07_snd_ev.wwev",
            ),
        )
        self.assertEqual(
            tuple(
                (item.expected_index, item.media_id, str(item.source_audio))
                for item in WP_GUN_PLAN.media_additions
            ),
            (
                (
                    34,
                    863_865_614,
                    "audio/wp_gun_cmn/stationary_draw/"
                    "raising_heart_standby_ready_01(movie_1st.raising_heart."
                    "standby_ready_set_up.1).wav",
                ),
                (
                    35,
                    1_280_643_898,
                    "audio/wp_gun_cmn/overhead_smash/"
                    "nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav",
                ),
            ),
        )
        self.assertEqual(
            LMT_PLAN.expected_output_sha256,
            "e75b48eb9bb61e2595311b6a026d195f2178bc61729968bd2da3078fbce957d1",
        )
        self.assertEqual(
            WWEV_PLAN.expected_output_sha256,
            "1818d0547237ef6bed7900ad3fa2bbecda2e040910b88760800c6fdc9b7a6222",
        )

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
