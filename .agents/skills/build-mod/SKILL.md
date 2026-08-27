---
name: build-mod
description: "Run and validate the registered design-driven Monster Hunter: World Mod artifact plan, then transactionally publish the complete release/nativePC tree. Use for dry-runs, focused artifact diagnostics, and official release builds; do not author designs or builders."
---

# Build Mods

Execute the registered `ModBuildPlan` in `builders.__main__`. It is the sole
release membership and implementation contract. `designs/` explains intent
and `docs/mapping/` records research; neither is parsed while building.

## Complete Build

Run the full conversion, edit, read-back, format, and bundle validation pipeline
without publishing:

```sh
conda run -n nanoha-gunlance-mod python -m builders --dry-run
```

Publish the complete staged tree to `release/nativePC/` only after every
artifact and bundle validator succeeds:

```sh
conda run -n nanoha-gunlance-mod python -m builders
```

An existing release is rejected. After the user explicitly authorizes replacing
the complete old tree, use:

```sh
conda run -n nanoha-gunlance-mod python -m builders --force
```

The publisher creates a sibling staging tree, moves the old release to a
rollback backup, swaps the complete tree, and restores the backup if the swap
fails. `--release-dir` selects another complete release root and `--root`
selects the project root.

## Focused Artifact Diagnostics

Run a registered artifact module when diagnosing one plan:

```sh
conda run -n nanoha-gunlance-mod python -m builders.w07_00 --dry-run
conda run -n nanoha-gunlance-mod python -m builders.wp_gun_cmn --dry-run
```

A non-dry single-artifact run writes
`output/nativePC/<declared-target>`; it requires `--force` to replace an
existing file and never constitutes an official release. Prefer dry-run unless
the user explicitly requests the diagnostic artifact.

## What the Runner Verifies

Every full dry-run and release build uses a task-specific temporary tree and:

1. validates unique registered targets, design IDs, safe source/target paths,
   original hashes, Bank IDs, media identities, audio inputs, callbacks, exact
   summaries, and editor guards;
2. converts declared WAVs, applies declared media edits and guarded callbacks,
   then reparses every artifact;
3. runs wwiser and pyvgmstream validation for changed SoundBanks and media;
4. runs every `BundleValidator` against the staged nativePC files;
5. publishes only after the complete set succeeds.

Report artifact names, design IDs, target paths, summaries, observed output
hashes when artifacts are published, and the validator that failed. Output
hashes are diagnostic metadata, not fixed acceptance guards. Structural success
does not replace in-game trigger, mix, spatialization, interruption, and
Mod-conflict testing.

## Failure and Ownership Boundaries

- Do not modify `builders/`, `designs/`, `audio/`, `original/`,
  `docs/mapping/`, or `assets/chunk/` to make a failing build pass.
- Do not publish a subset after another artifact or validator fails.
- Keep converted WEMs, decoded WAVs, wwiser dumps, and semantic diffs out of
  `output/` and `release/`.
- Route incomplete or incorrect design contracts to `audio-design`. Route
  implementation, registry, summary, or validator drift to `design-implement`.
