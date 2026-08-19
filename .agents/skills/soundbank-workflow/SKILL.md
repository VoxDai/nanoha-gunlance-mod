---
name: soundbank-workflow
description: "Analyze and rebuild Monster Hunter: World/Iceborne Wwise NBNK SoundBanks. Use for DIDX/WEM media work, HIRC Event-to-Sound routing, guarded node or mix settings, structural validation, and verified single-Bank output."
---

# SoundBank Workflow

## Safety Rules

- Use an original Bank from `original/` as the rebuild input. Never modify `original/` or `mod_samples/`.
- Treat DIDX indices as 1-based. Inspect the Bank and report the matching Media ID before replacement.
- Put all extracted media, converted WEM files, logs, and validation artifacts in one task-specific `/tmp` directory.
- Write only the verified final NBNK to `output/`. Never overwrite an existing output without explicit authorization.
- Treat `nbnk_media.py replace` as media-only: it must preserve HIRC byte-for-byte.
- Put persistent project HIRC changes in the matching module under `builders/`, using guarded object-relative edits. Never patch absolute file offsets.
- Treat structural validation as necessary but insufficient. Complete final trigger, volume, channel, and conflict checks in a recoverable game environment.

## Prepare the Workspace

Create a temporary workspace and register cleanup before producing intermediates:

```sh
temp_dir="$(mktemp -d /tmp/soundbank-workflow.XXXXXX)"
trap 'rm -rf -- "$temp_dir"' EXIT INT TERM
```

Check the required tools:

```sh
conda run -n nanoha-gunlance-mod ffmpeg -version
conda run -n nanoha-gunlance-mod python -c "import pyvgmstream; print('pyvgmstream available')"
test -f tools/wwiser/wwiser.py
```

## Inspect and Analyze

Inspect chunk order, sizes, DIDX indices, Media IDs, offsets, and alignment:

```sh
conda run -n nanoha-gunlance-mod python \
  tools/utils/nbnk_media.py inspect input.nbnk
```

Use wwiser for a structural check:

```sh
conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py -d none input.nbnk
```

When tracing HIRC routes or node settings, write a text dump inside the temporary
workspace and search it by Media ID or HIRC object ID:

```sh
conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py \
  -d txt -dn "$temp_dir/input-hirc" input.nbnk
rg -n -C 8 'sourceID|ulID|DirectParentID|ulChildID|idExt' \
  "$temp_dir/input-hirc.txt"
```

Read [hirc-routing-and-settings.md](references/hirc-routing-and-settings.md)
before changing Event routes, Sound/Container properties, positioning, or Aux
sends.

## Extract and Decode Media

Extract one entry by DIDX index or Media ID:

```sh
conda run -n nanoha-gunlance-mod python \
  tools/utils/nbnk_media.py extract \
  input.nbnk --index 22 -o "$temp_dir/22.wem"
```

Use `--media-id ID` instead of `--index`, or extract every entry with:

```sh
conda run -n nanoha-gunlance-mod python \
  tools/utils/nbnk_media.py extract \
  input.nbnk --all -o "$temp_dir/wem"
```

Inspect or decode extracted media with the project CLI:

```sh
conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py inspect "$temp_dir/22.wem"
conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py decode \
  "$temp_dir/22.wem" "$temp_dir/22.wav"
```

## Convert and Replace

Convert replacement audio to the verified 48 kHz, 16-bit, stereo Wwise PCM layout:

```sh
conda run -n nanoha-gunlance-mod python \
  tools/utils/wav_to_wem.py \
  replacement.wav "$temp_dir/replacement.wem"
```

Inspect the converted WEM, then rebuild the Bank. Omit the output argument to write the final Bank to `output/<input filename>`:

```sh
conda run -n nanoha-gunlance-mod python \
  tools/utils/nbnk_media.py replace \
  original/soundbank/input.nbnk \
  --replace 22="$temp_dir/replacement.wem"
```

Use `--replace id:468604124=...` to target a Media ID, and repeat `--replace` for distinct targets.

The media-only rebuild must preserve Media ID order and every chunk other than
DIDX/DATA byte-for-byte. It must also align media offsets to 16 bytes and pass
read-back verification.

## Change HIRC Settings

First trace the complete route in a wwiser text dump. The same Media ID may be
referenced by multiple Sound objects or spatial paths, so changing only the
first match can cause level or channel imbalance.

For a project Bank, implement the reviewed settings in
`builders/<bank-name>.py`. Use `HircEditor` to locate an object by HIRC type and
ID, then patch a body-relative field with its exact expected old value. The
builder must fail if the object or old bytes differ. Keep paired playback paths
symmetric unless the intended mix explicitly requires otherwise.

Run the single builder with `--dry-run`, then build to `output/` and inspect the
resulting HIRC diff. Do not use `nbnk_media.py replace` to express HIRC changes;
its strict HIRC-preservation rule is an intentional safety boundary.

## Validate the Final Bank

Run the NBNK inspector and wwiser against the final file. Re-extract each
replaced entry and inspect or decode it with pyvgmstream. For a HIRC edit,
compare original and rebuilt dumps after removing file-offset-only differences
and require that all semantic changes match the declared builder settings.
Report the output path, SHA-256, replaced DIDX indices, Media IDs, and HIRC
changed-byte count.

Read [format-and-troubleshooting.md](references/format-and-troubleshooting.md) when a Bank is rejected, an index is ambiguous, a WEM is unrecognized, or the game is silent.
