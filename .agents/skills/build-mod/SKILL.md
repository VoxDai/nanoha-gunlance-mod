---
name: build-mod
description: "Build and validate the complete design-driven Monster Hunter: World mod artifact set, including NBNK, LMT, and WWEV routes, then transactionally publish release/nativePC."
---

# Build Mod

Use the registered `ModBuildPlan` in `builders.__main__` as the sole executable
build contract. `designs/` explains intent and `docs/mapping/` records research;
neither directory is parsed at build time.

## Commands

From the project root, perform the complete build and every validator without
publishing:

```sh
conda run -n nanoha-gunlance-mod python -m builders --dry-run
```

Publish the complete tree to `release/nativePC/`:

```sh
conda run -n nanoha-gunlance-mod python -m builders
```

An existing release is intentionally rejected. After confirming that the
complete old tree may be replaced, add `--force`; the builder stages a sibling
tree, moves the old release to a rollback backup, swaps the complete tree, and
restores the backup if the swap fails. `--release-dir` selects a different
release root and `--root` selects the project root.

For one artifact, run its module, for example:

```sh
conda run -n nanoha-gunlance-mod python -m builders.w07_00 --dry-run
conda run -n nanoha-gunlance-mod python -m builders.wp_gun_cmn
```

Single-artifact output is `output/nativePC/<declared-target>` by default. Use
`--output-dir` to change its root and `--force` to replace an existing file.
Single-artifact execution is for focused debugging; only `python -m builders`
produces an official complete release.

## Executable Contract

- `SoundBankBuildPlan`, `LmtBuildPlan`, and `WwevBuildPlan` explicitly declare
  design IDs, project-relative source and nativePC target paths, original binary
  SHA-256, guarded editor callback, and exact expected summary.
- SoundBank plans declare every `MediaReplacement(index, expected_media_id,
  source_audio)` and `MediaAddition(expected_index, media_id, source_audio)`.
  WAV content is intentionally not hash-pinned, allowing a reviewed mix to be
  updated at the same path without changing routing code. The callback owns
  HIRC edits only; undeclared callback media edits are rejected.
- LMT and WWEV plans additionally pin their output SHA-256. Target paths must be
  safe nativePC-relative paths and globally unique.
- `ModBuildPlan` owns the complete artifact registry and cross-file validators.
  Do not infer release membership from files under `original/` or documentation.

## Build and Validation

Every normal and dry-run build performs the same work in a task-specific
temporary directory:

1. Validate registry uniqueness, safe paths, source hashes, Bank IDs, DIDX
   indices and Media IDs, editor guards, exact summaries, and source audio.
2. Convert declared WAVs to the project Wwise PCM WEM layout. Apply media edits
   in declared order, then run the artifact's guarded callback.
3. Reparse every NBNK and run wwiser. Generate normalized HIRC semantic diffs
   when applicable, re-extract every changed media entry, and inspect/decode it
   with pyvgmstream.
4. Reparse LMT/WWEV outputs, require their exact summaries and output hashes,
   and run all bundle validators against the staged nativePC paths.
5. Publish only after the complete staging tree succeeds. `--dry-run` stops here
   without creating an output or release tree.

Use [soundbank-workflow](../soundbank-workflow/SKILL.md) for format analysis and
guarded route authoring. Structural validation does not replace in-game trigger,
mix, spatialization, and mod-conflict tests.

## Protection Boundaries

- Never modify `designs/`, `docs/mapping/`, `original/`, or `audio/` while building.
- Keep converted WEMs, decoded WAVs, wwiser dumps, and semantic diffs out of
  `output/` and `release/`.
- Never publish a subset after any artifact or bundle validator fails.
