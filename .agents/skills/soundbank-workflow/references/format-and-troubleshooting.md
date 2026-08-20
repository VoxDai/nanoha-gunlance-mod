# NBNK Format and Troubleshooting

## WEM

- A `.wem` is Wwise media; changing a WAV filename extension does not create a valid replacement.
- The PCM WEM layout verified by this project uses RIFF/WAVE, format tag `0xFFFE`, 48 kHz, 16-bit stereo audio, a 6-byte Wwise channel extension, and a 4-byte `JUNK` chunk.
- An ordinary PCM WAV normally uses format tag `0x0001`. The rebuild script rejects it because the MHW runtime may play silence.
- Original media often uses Wwise Custom Vorbis. Use the verified PCM wrapper when a matching Wwise encoder is unavailable, accepting the larger file size.

## NBNK Structure

- `BKHD` stores the Bank header and identifier.
- `DIDX` stores one little-endian `(Media ID, DATA offset, size)` triple per embedded file.
- `DATA` stores embedded WEM payloads. This workflow aligns rebuilt media starts to 16 bytes.
- `HIRC` stores Sound objects, events, and Media ID references.

DIDX order is independent of Media ID order. Community labels such as “WEM #22” normally mean the 22nd DIDX entry, so always inspect the Bank before replacement.

When rebuilding:

1. Preserve DIDX order and Media IDs.
2. Replace only explicitly selected payloads.
3. Rebuild DATA with 16-byte media alignment.
4. Rewrite DIDX offsets and sizes.
5. Preserve BKHD, HIRC, and unknown chunks byte-for-byte for a media-only rebuild.

`SoundBankEditor.append_media()` appends a new DIDX record and WEM payload while
preserving existing order. It requires a new explicit Media ID, rejects HIRC or
media ID collisions, and applies the same 16-byte alignment during rebuilding.

An explicitly configured `BankBuildPlan` may change HIRC after mapped media edits.
In that case it must identify objects by HIRC type and ID, assert every old
field value, preserve all undeclared fields and chunks, and report the exact
HIRC changed-byte count. Absolute Bank offsets are not stable because rebuilding
DATA moves the HIRC chunk.

Known working MHW replacement Banks retain original HIRC Source and memory-size fields when embedding PCM WEMs. Do not generalize this rule to other games or Wwise versions.

A Media ID is not a playback path. Multiple Sound objects can reference the same
media through different Events, containers, parent properties, or positioning
paths. Trace every route before changing volume, pitch, or Aux settings.

## Silence Troubleshooting

1. Inspect the Bank and confirm both the 1-based DIDX index and Media ID.
2. Extract the rebuilt entry and inspect it with `tools/utils/pyvgmstream.py`.
3. Decode the entry to WAV and confirm that it contains audible audio with the intended duration and channels.
4. Parse the rebuilt Bank with `tools/wwiser/wwiser.py -d none`.
5. If the symptom is reverb, spatialization, or channel imbalance, inspect every
   Sound path for inherited Aux sends, positioning, parent pitch, and asymmetric
   volume settings.
6. Confirm the installed Bank filename and path match the original game Bank.
7. Remove conflicting mods that provide the same Bank.
8. Restore the original Bank to verify the game environment, then compare with a known-working reference.

## Validation Boundaries

- pyvgmstream verifies individual media decoding, not event references or Wwise mixing.
- wwiser verifies Bank and HIRC parsing, not acceptance by the MHW runtime.
- Byte and hash comparisons verify preservation, not loudness or subjective quality.
- In-game trigger testing remains the final acceptance step.
