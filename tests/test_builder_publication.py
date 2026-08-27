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
    sha256,
)

from ._builder_fixtures import TEST_DESIGN_ID, SyntheticBuilderProject


def reject_bundle(_staged) -> None:
    raise BuildError("synthetic bundle rejection")


class BuilderPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="builder-publication-test.")
        self.root = Path(self.temporary.name).resolve()
        self.project = SyntheticBuilderProject.create(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_dry_run_fully_builds_without_creating_output(self) -> None:
        output = self.root / "output"
        self.assertIsNone(
            build_one(
                self.project.lmt_plan(),
                root=self.root,
                output_dir=output,
                dry_run=True,
            )
        )
        self.assertFalse(output.exists())

    def test_single_artifact_overwrite_and_dynamic_result_digest(self) -> None:
        plan = self.project.lmt_plan()
        output = self.root / "output"
        first = build_one(plan, root=self.root, output_dir=output)
        self.assertIsNotNone(first)
        target = output / "nativePC" / plan.target
        self.assertTrue(target.is_file())
        self.assertEqual(first.sha256, sha256(target))

        with self.assertRaisesRegex(BuildError, "already exists"):
            build_one(plan, root=self.root, output_dir=output)
        forced = build_one(
            plan,
            root=self.root,
            output_dir=output,
            force=True,
        )
        self.assertIsNotNone(forced)
        self.assertEqual(forced.sha256, sha256(target))

    def test_publication_inside_protected_assets_tree_is_rejected(self) -> None:
        with self.assertRaisesRegex(BuildError, "protected source tree"):
            build_one(
                self.project.lmt_plan(),
                root=self.root,
                output_dir="assets/generated",
                dry_run=True,
            )
        self.assertFalse((self.root / "assets").exists())

    def test_bundle_validator_failure_publishes_nothing(self) -> None:
        mod_plan = ModBuildPlan(
            (self.project.lmt_plan(), self.project.wwev_plan()),
            (
                BundleValidator(
                    name="synthetic_rejection",
                    design_id=TEST_DESIGN_ID,
                    validate=reject_bundle,
                ),
            ),
        )
        release = self.root / "release"
        with self.assertRaisesRegex(BuildError, "synthetic bundle rejection"):
            build_all(mod_plan, root=self.root, release_dir=release)
        self.assertFalse(release.exists())

    def test_force_replaces_the_complete_tree_after_bundle_validation(self) -> None:
        plans = (self.project.lmt_plan(), self.project.wwev_plan())
        observed: list[set[Path]] = []

        def validate_staged(staged) -> None:
            observed.append(set(staged))
            self.assertEqual(set(staged), {plan.target for plan in plans})
            self.assertTrue(all(path.is_file() for path in staged.values()))

        mod_plan = ModBuildPlan(
            plans,
            (
                BundleValidator(
                    name="synthetic_route",
                    design_id=TEST_DESIGN_ID,
                    validate=validate_staged,
                ),
            ),
        )
        release = self.root / "release"
        release.mkdir()
        (release / "legacy.txt").write_text("old", encoding="utf-8")
        with self.assertRaisesRegex(BuildError, "already exists"):
            build_all(mod_plan, root=self.root, release_dir=release)

        results = build_all(
            mod_plan,
            root=self.root,
            release_dir=release,
            force=True,
        )
        self.assertEqual(len(results), len(plans))
        self.assertEqual(len(observed), 1)
        self.assertFalse((release / "legacy.txt").exists())
        for plan, result in zip(plans, results, strict=True):
            target = release / "nativePC" / plan.target
            self.assertTrue(target.is_file())
            self.assertEqual(result.sha256, sha256(target))

    def test_force_tree_replacement_rolls_back_on_swap_failure(self) -> None:
        staged = self.root / "staged"
        release = self.root / "release"
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
                    project_root=self.root,
                    force=True,
                )

        self.assertEqual((release / "old.txt").read_text(encoding="utf-8"), "old")
        self.assertFalse((release / "nativePC").exists())


if __name__ == "__main__":
    unittest.main()
