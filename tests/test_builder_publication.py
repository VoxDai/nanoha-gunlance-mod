from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from builders.base import (
    BuildError,
    BundleValidator,
    ModBuildPlan,
    build_all,
    build_one,
    publish_release_tree,
)
from builders.hm_cm00_epvsp import PLAN as GUARD_PLAN
from builders.hm_wp07_snd_ev import PLAN as WWEV_PLAN
from builders.w07_00 import PLAN as LMT_PLAN


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def reject_bundle(_staged) -> None:
    raise BuildError("synthetic bundle rejection")


EVENT_ONLY_PLAN = ModBuildPlan(
    artifacts=(LMT_PLAN, WWEV_PLAN),
    validators=(
        BundleValidator(
            name="synthetic_rejection",
            design_id="wp_gun_cmn.stationary_draw",
            validate=reject_bundle,
        ),
    ),
)


class BuilderPublicationTests(unittest.TestCase):
    def test_dry_run_fully_builds_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="builder-dry-run-test.") as directory:
            output = Path(directory) / "output"
            self.assertIsNone(
                build_one(
                    LMT_PLAN,
                    root=PROJECT_ROOT,
                    output_dir=output,
                    dry_run=True,
                )
            )
            self.assertFalse(output.exists())

    def test_single_artifact_refuses_overwrite_unless_forced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="builder-single-test.") as directory:
            output = Path(directory) / "output"
            first = build_one(LMT_PLAN, root=PROJECT_ROOT, output_dir=output)
            self.assertIsNotNone(first)
            target = output / "nativePC" / LMT_PLAN.target
            self.assertTrue(target.is_file())
            with self.assertRaisesRegex(BuildError, "already exists"):
                build_one(LMT_PLAN, root=PROJECT_ROOT, output_dir=output)
            forced = build_one(
                LMT_PLAN,
                root=PROJECT_ROOT,
                output_dir=output,
                force=True,
            )
            self.assertEqual(forced.sha256, LMT_PLAN.expected_output_sha256)

    def test_guard_build_matches_the_accepted_candidate_04(self) -> None:
        with tempfile.TemporaryDirectory(prefix="guard-candidate-04-test.") as directory:
            output = Path(directory) / "output"
            result = build_one(GUARD_PLAN, root=PROJECT_ROOT, output_dir=output)
            self.assertIsNotNone(result)
            self.assertEqual(
                result.sha256,
                "e61c7bccccd630d903ac36245a4d135374fd8fb6bdbcfd5c536929d8f63e283e",
            )

    def test_bundle_validator_failure_publishes_nothing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="builder-failure-test.") as directory:
            release = Path(directory) / "release"
            with self.assertRaisesRegex(BuildError, "synthetic bundle rejection"):
                build_all(
                    EVENT_ONLY_PLAN,
                    root=PROJECT_ROOT,
                    release_dir=release,
                )
            self.assertFalse(release.exists())

    def test_existing_release_requires_force_and_force_replaces_whole_tree(self) -> None:
        mod_plan = ModBuildPlan((LMT_PLAN, WWEV_PLAN))
        with tempfile.TemporaryDirectory(prefix="builder-release-test.") as directory:
            release = Path(directory) / "release"
            release.mkdir()
            (release / "legacy.txt").write_text("old", encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "Release already exists"):
                build_all(mod_plan, root=PROJECT_ROOT, release_dir=release)

            results = build_all(
                mod_plan,
                root=PROJECT_ROOT,
                release_dir=release,
                force=True,
            )
            self.assertEqual(len(results), 2)
            self.assertFalse((release / "legacy.txt").exists())
            self.assertTrue((release / "nativePC" / LMT_PLAN.target).is_file())
            self.assertTrue((release / "nativePC" / WWEV_PLAN.target).is_file())

    def test_force_tree_replacement_rolls_back_on_swap_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="builder-rollback-test.") as directory:
            root = Path(directory)
            staged = root / "staged"
            release = root / "release"
            (staged / "nativePC").mkdir(parents=True)
            (staged / "nativePC" / "new.txt").write_text("new", encoding="utf-8")
            release.mkdir()
            (release / "old.txt").write_text("old", encoding="utf-8")

            real_replace = os.replace

            def fail_staging_swap(source, target):
                if Path(source).name.startswith(".release.staging-"):
                    raise OSError("synthetic staging swap failure")
                return real_replace(source, target)

            with mock.patch("builders.base.os.replace", side_effect=fail_staging_swap):
                with self.assertRaisesRegex(OSError, "synthetic staging swap failure"):
                    publish_release_tree(
                        staged,
                        release,
                        project_root=PROJECT_ROOT,
                        force=True,
                    )

            self.assertEqual(
                (release / "old.txt").read_text(encoding="utf-8"), "old"
            )
            self.assertFalse((release / "nativePC").exists())


if __name__ == "__main__":
    unittest.main()
