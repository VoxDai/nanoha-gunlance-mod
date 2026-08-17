---
name: build-mod
description: "Build and validate every Monster Hunter: World .nbnk mod Bank from the project's mapping Markdown tables. Resolve 1-based DIDX indices from Wem# New(Old) original-audio links, replace media from local Audio links, preserve rows with empty Audio cells, and publish verified Banks to release/."
---

# Build Mod

## Quick start

Run from the project root:

    conda run -n nanoha-gunlance-mod python \
      .agents/skills/build-mod/scripts/build_nbnk_mod.py

Run only table, path, tool, and index checks:

    conda run -n nanoha-gunlance-mod python \
      .agents/skills/build-mod/scripts/build_nbnk_mod.py --dry-run

The script scans mapping/ and original/soundbank/ by default and publishes every source Bank with the same filename under release/. Use --root, --mapping-dir, --soundbank-dir, or --release-dir to override paths.

## Input contract

- Scan every mapping Markdown file. Each file must contain Wem# New(Old) and Audio columns.
- Use the link in Wem# New(Old) that points to original/audio_files/Bank/wav/index.wav to resolve the current 1-based DIDX index. Ignore the parenthesized Old index for replacement.
- Treat an Audio cell containing only whitespace as unchanged media. A non-empty Audio cell must contain exactly one local Markdown link to an existing file inside the project.
- Ignore Source Audio for building; it is research metadata only.
- Report rows without an original-audio link when Audio is empty and skip them. Fail before publishing when such a row has a non-empty Audio cell.
- Reject missing Banks, missing audio files, malformed headers, duplicate DIDX targets, and out-of-range indices.

## Build and validation workflow

1. Parse every mapping table and preflight all source Banks, paths, indices, and required project tools.
2. Create a task-specific temporary workspace. Use the existing soundbank-workflow wav_to_wem.py to convert each replacement into the verified 48 kHz, 16-bit, stereo Wwise PCM WEM layout.
3. Use nbnk_media.py replace for Banks with replacements. Copy Banks with no replacements byte-for-byte. Never modify original/.
4. Run nbnk_media.py inspect and tools/wwiser/wwiser.py -d none for every staged Bank.
5. Re-extract each replaced DIDX entry, run tools/pyvgmstream/pyvgmstream.py inspect and decode, and require a non-empty decoded WAV.
6. Publish Banks only after every staged Bank passes validation. Atomically create or replace same-named .nbnk files in release/; leave unrelated release files untouched.
7. Report each published path, SHA-256, replacement DIDX index, and Media ID. Remove temporary WEM, WAV, logs, and validation artifacts when the task ends.

This skill reuses the NBNK and WEM rules in [soundbank-workflow](../soundbank-workflow/SKILL.md). Structural validation does not replace in-game acceptance testing; check triggers, volume, channels, and conflicting Mods in a recoverable game environment.

## Protection boundaries

- Do not modify mapping/, original/, audio/, or the existing soundbank-workflow skill.
- Do not write intermediate WEM, decoded WAV, or logs into release/.
- Do not publish partial results when parsing, conversion, rebuilding, or validation fails.
