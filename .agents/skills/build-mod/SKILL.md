---
name: build-mod
description: "Build and validate every Monster Hunter: World .nbnk mod Bank through the project's per-Bank builders. Use for a complete mapping-driven release build, including registered HIRC node settings and atomic publication to release/."
---

# Build Mod

## Quick start

Run from the project root:

    conda run -n nanoha-gunlance-mod python \
      -m builders

Run only registry, table, path, tool, index, and HIRC setting checks:

    conda run -n nanoha-gunlance-mod python \
      -m builders --dry-run

The batch entry point requires one registered builder for every matching file in
`mapping/` and `original/soundbank/`. It stages and validates all Banks before
atomically replacing same-named files under `release/`. Use `--root`,
`--mapping-dir`, `--soundbank-dir`, or `--release-dir` to override paths.

For one Bank, run `python -m builders.<bank-name>`. A single builder writes to
`output/` by default and requires `--force` before replacing an existing output.

## Input contract

- Every mapping Markdown file must have a same-stem source Bank and builder.
- Each mapping table must contain `Wem# New(Old)` and `Audio` columns.
- Use the link in Wem# New(Old) that points to original/audio_files/Bank/wav/index.wav to resolve the current 1-based DIDX index. Ignore the parenthesized Old index for replacement.
- Treat an Audio cell containing only whitespace as unchanged media. A non-empty Audio cell must contain exactly one local Markdown link to an existing file inside the project.
- Ignore Source Audio for building; it is research metadata only.
- Report rows without an original-audio link when Audio is empty and skip them. Fail before publishing when such a row has a non-empty Audio cell.
- Reject missing Banks, missing audio files, malformed headers, duplicate DIDX targets, and out-of-range indices.

## Build and validation workflow

1. Preflight the builder registry, mappings, source Banks, paths, DIDX indices,
   bank-specific HIRC guards, and required tools.
2. Convert mapped audio to the verified 48 kHz, 16-bit, stereo Wwise PCM WEM
   layout in one task-specific `/tmp` workspace.
3. Create `tools.soundbank_editor.SoundBankEditor` from the original Bank,
   apply mapped media replacements, then execute only the Python edits declared
   by its `BankBuildPlan`. Banks with neither change remain byte-for-byte identical.
4. Reparse every staged Bank with `SoundBank.from_file()` and run
   `wwiser.py -d none`; for HIRC edits, also generate a normalized semantic diff.
5. Re-extract every replaced or appended DIDX entry through the Library, then
   inspect and decode it with `tools/utils/pyvgmstream.py`; require a non-empty WAV.
6. Publish only after all staged Banks pass. Report each path, SHA-256,
   replacement DIDX/Media ID, and HIRC changed-byte count.

The builders reuse the NBNK and WEM tools documented by
[soundbank-workflow](../soundbank-workflow/SKILL.md). Structural validation does
not replace in-game trigger, volume, channel, spatialization, and conflict tests.

## Protection boundaries

- Never modify `mapping/`, `original/`, or `audio/` while building.
- Do not write intermediate WEM, decoded WAV, or logs into release/.
- Do not publish partial results when parsing, conversion, rebuilding, or validation fails.
