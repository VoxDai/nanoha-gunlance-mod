from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import wave

import builders.base as builder_base
from builders.base import (
    BuildError,
    BundleValidator,
    MediaAddition,
    MediaReplacement,
    ModBuildPlan,
    ReferenceInput,
    prepare_all_plans,
    prepare_plan,
    validate_registry,
)
from tools import soundbank_editor

from ._builder_fixtures import (
    ADDED_MEDIA_ID,
    TEST_DESIGN_ID,
    TEST_MEDIA_ID,
    SyntheticBuilderProject,
)


def append_undeclared_media(editor: soundbank_editor.SoundBankEditor) -> None:
    editor.append_media(
        ADDED_MEDIA_ID,
        editor.original.extract_media(index=1),
    )


class GenericPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="builder-plan-test.")
        self.root = Path(self.temporary.name).resolve()
        self.project = SyntheticBuilderProject.create(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_public_plan_api_is_generic(self) -> None:
        for name in (
            "MediaReplacement",
            "MediaAddition",
            "ReferenceInput",
            "SoundBankBuildPlan",
            "LmtBuildPlan",
            "WwevBuildPlan",
            "ModBuildPlan",
        ):
            self.assertIn(name, builder_base.__all__)
            self.assertTrue(hasattr(builder_base, name))
        for removed in ("MappingInfo", "MappingMediaOverlay", "parse_mapping"):
            self.assertFalse(hasattr(builder_base, removed))

    def test_declared_paths_channels_and_collection_invariants(self) -> None:
        bank = self.project.soundbank_plan()
        lmt = self.project.lmt_plan()
        addition = bank.media_additions[0]

        with self.assertRaisesRegex(ValueError, "safe project-relative"):
            MediaAddition(1, 1, "../voice.wav")
        with self.assertRaisesRegex(ValueError, "must not include"):
            replace(lmt, target="nativePC/motion/test.lmt")
        with self.assertRaisesRegex(ValueError, "safe project-relative"):
            replace(lmt, source="../outside.lmt")
        with self.assertRaisesRegex(ValueError, "below original"):
            ReferenceInput("assets/chunk/unsafe.nbnk", "00" * 32)
        with self.assertRaisesRegex(ValueError, "below original"):
            ReferenceInput("original/../unsafe.nbnk", "00" * 32)
        for invalid_channels in (3, True):
            with self.subTest(wem_channels=invalid_channels):
                with self.assertRaisesRegex(ValueError, "wem_channels"):
                    replace(addition, wem_channels=invalid_channels)

        with self.assertRaisesRegex(ValueError, "duplicate media addition index"):
            replace(
                bank,
                media_additions=(
                    addition,
                    MediaAddition(
                        addition.expected_index,
                        addition.media_id + 1,
                        addition.source_audio,
                    ),
                ),
            )
        with self.assertRaisesRegex(ValueError, "duplicate added Media ID"):
            replace(
                bank,
                media_additions=(
                    addition,
                    MediaAddition(
                        addition.expected_index + 1,
                        addition.media_id,
                        addition.source_audio,
                    ),
                ),
            )
        with self.assertRaisesRegex(ValueError, "indices overlap"):
            replace(
                bank,
                media_replacements=(
                    MediaReplacement(
                        addition.expected_index,
                        TEST_MEDIA_ID,
                        addition.source_audio,
                    ),
                ),
            )
        with self.assertRaisesRegex(ValueError, "duplicate reference input"):
            replace(
                bank,
                reference_inputs=(
                    bank.reference_inputs[0],
                    bank.reference_inputs[0],
                ),
            )

    def test_registry_rejects_generic_identity_and_validator_conflicts(self) -> None:
        plan = self.project.lmt_plan()
        validate_registry(
            ModBuildPlan(
                (plan,),
                (
                    BundleValidator(
                        "route",
                        TEST_DESIGN_ID,
                        lambda _staged: None,
                    ),
                ),
            )
        )

        duplicate_name = replace(
            plan,
            source="original/lmt/other-name.lmt",
            target="motion/other-name.lmt",
        )
        with self.assertRaisesRegex(BuildError, "Duplicate builder name"):
            validate_registry(ModBuildPlan((plan, duplicate_name)))

        duplicate_source = replace(
            plan,
            name="other_source_owner",
            target="motion/other-source.lmt",
        )
        with self.assertRaisesRegex(BuildError, "Duplicate source artifact"):
            validate_registry(ModBuildPlan((plan, duplicate_source)))

        duplicate_target = replace(
            plan,
            name="other_target_owner",
            source="original/lmt/other-target.lmt",
        )
        with self.assertRaisesRegex(BuildError, "Duplicate target artifact"):
            validate_registry(ModBuildPlan((plan, duplicate_target)))

        validator = BundleValidator("route", TEST_DESIGN_ID, lambda _staged: None)
        with self.assertRaisesRegex(BuildError, "Duplicate bundle validator"):
            validate_registry(ModBuildPlan((plan,), (validator, validator)))
        with self.assertRaisesRegex(BuildError, "unregistered design"):
            validate_registry(
                ModBuildPlan(
                    (plan,),
                    (
                        BundleValidator(
                            "orphan_route",
                            "test.unregistered",
                            lambda _staged: None,
                        ),
                    ),
                )
            )

    def test_all_synthetic_plan_types_preflight_in_registry_order(self) -> None:
        plans = (
            self.project.soundbank_plan(),
            self.project.lmt_plan(),
            self.project.wwev_plan(),
        )
        prepared = prepare_all_plans(ModBuildPlan(plans), self.root)
        self.assertEqual(
            [item.plan.name for item in prepared],
            [plan.name for plan in plans],
        )
        self.assertEqual(
            [item.preview_summary for item in prepared],
            [plan.expected_summary for plan in plans],
        )

    def test_source_reference_bank_and_audio_guards_run_before_editing(self) -> None:
        edit = mock.Mock()
        bad_source = replace(
            self.project.lmt_plan(),
            expected_source_sha256="00" * 32,
            apply_edits=edit,
        )
        with self.assertRaisesRegex(BuildError, "source SHA-256"):
            prepare_plan(bad_source, self.root)
        edit.assert_not_called()

        bank = self.project.soundbank_plan()
        bad_reference = replace(
            bank.reference_inputs[0],
            expected_sha256="00" * 32,
        )
        with self.assertRaisesRegex(BuildError, "reference input SHA-256"):
            prepare_plan(
                replace(bank, reference_inputs=(bad_reference,)),
                self.root,
            )
        with self.assertRaisesRegex(BuildError, "expected Bank ID"):
            prepare_plan(
                replace(bank, expected_bank_id=bank.expected_bank_id + 1),
                self.root,
            )

        audio = self.root / bank.media_additions[0].source_audio
        with wave.open(str(audio), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48_000)
            wav.writeframes(bytes(8))
        with self.assertRaisesRegex(BuildError, "source audio must be"):
            prepare_plan(bank, self.root)

    def test_media_identity_and_declaration_guards(self) -> None:
        plan = self.project.soundbank_plan()
        addition = plan.media_additions[0]

        with self.assertRaisesRegex(BuildError, "added media indices"):
            prepare_plan(
                replace(
                    plan,
                    media_additions=(replace(addition, expected_index=3),),
                ),
                self.root,
            )
        with self.assertRaisesRegex(BuildError, "Media ID already exists"):
            prepare_plan(
                replace(
                    plan,
                    media_additions=(replace(addition, media_id=TEST_MEDIA_ID),),
                ),
                self.root,
            )

        replacement = MediaReplacement(
            1,
            TEST_MEDIA_ID + 1,
            addition.source_audio,
            wem_channels=1,
        )
        with self.assertRaisesRegex(BuildError, "expected Media ID"):
            prepare_plan(
                replace(
                    plan,
                    media_additions=(),
                    media_replacements=(replacement,),
                ),
                self.root,
            )

        with self.assertRaisesRegex(BuildError, "undeclared media additions"):
            prepare_plan(
                replace(
                    plan,
                    media_additions=(),
                    apply_edits=append_undeclared_media,
                    expected_summary=soundbank_editor.SoundBankEditSummary(
                        replaced_media=(),
                        added_media=((2, ADDED_MEDIA_ID),),
                        hirc_changed_bytes=0,
                        added_hirc_objects=(),
                        resized_hirc_objects=(),
                        hirc_size_delta=0,
                    ),
                ),
                self.root,
            )

    def test_summary_mismatch_is_rejected_without_an_output_hash(self) -> None:
        wrong_summary = soundbank_editor.LmtEditSummary(0, ())
        with self.assertRaisesRegex(BuildError, "edit summary differs"):
            prepare_plan(
                replace(
                    self.project.lmt_plan(),
                    expected_summary=wrong_summary,
                ),
                self.root,
            )


if __name__ == "__main__":
    unittest.main()
