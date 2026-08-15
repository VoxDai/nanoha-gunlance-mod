---
name: soundbank-workflow
description: "Analyze and rebuild Monster Hunter: World/Iceborne Wwise NBNK SoundBanks. Use when Codex needs to inspect NBNK chunks or DIDX media, extract embedded WEM files, convert replacement audio, replace media by DIDX index or Media ID, validate rebuilt Banks with pyvgmstream and wwiser, or produce a verified NBNK in output/."
---

# SoundBank Workflow

## Safety Rules

- Use an original Bank from `original/` as the rebuild input. Never modify `original/` or `mod_samples/`.
- Treat DIDX indices as 1-based. Inspect the Bank and report the matching Media ID before replacement.
- Put all extracted media, converted WEM files, logs, and validation artifacts in one task-specific `/tmp` directory.
- Write only the verified final NBNK to `output/`. Never overwrite an existing output without explicit authorization.
- Treat structural validation as necessary but insufficient. Complete final trigger, volume, channel, and conflict checks in a recoverable game environment.

## Prepare the Workspace

Create a temporary workspace and register cleanup before producing intermediates:

```sh
temp_dir="$(mktemp -d /tmp/soundbank-workflow.XXXXXX)"
trap 'rm -rf -- "$temp_dir"' EXIT INT TERM
```

Check the required tools:

```sh
mamba run -n nanoha-gunlance-mod ffmpeg -version
mamba run -n nanoha-gunlance-mod python -c "import pyvgmstream; print('pyvgmstream available')"
test -f tools/wwiser/wwiser.py
```

## Inspect and Analyze

Inspect chunk order, sizes, DIDX indices, Media IDs, offsets, and alignment:

```sh
mamba run -n nanoha-gunlance-mod python \
  .agents/skills/soundbank-workflow/scripts/nbnk_media.py inspect input.nbnk
```

Use wwiser for HIRC objects, events, and media relationships:

```sh
mamba run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py -d none input.nbnk
```

## Extract and Decode Media

Extract one entry by DIDX index or Media ID:

```sh
mamba run -n nanoha-gunlance-mod python \
  .agents/skills/soundbank-workflow/scripts/nbnk_media.py extract \
  input.nbnk --index 22 -o "$temp_dir/22.wem"
```

Use `--media-id ID` instead of `--index`, or extract every entry with:

```sh
mamba run -n nanoha-gunlance-mod python \
  .agents/skills/soundbank-workflow/scripts/nbnk_media.py extract \
  input.nbnk --all -o "$temp_dir/wem"
```

Inspect or decode extracted media with the project CLI:

```sh
mamba run -n nanoha-gunlance-mod python tools/pyvgmstream/pyvgmstream.py inspect "$temp_dir/22.wem"
mamba run -n nanoha-gunlance-mod python tools/pyvgmstream/pyvgmstream.py decode \
  "$temp_dir/22.wem" "$temp_dir/22.wav"
```

## Convert and Replace

Convert replacement audio to the verified 48 kHz, 16-bit, stereo Wwise PCM layout:

```sh
mamba run -n nanoha-gunlance-mod python \
  .agents/skills/soundbank-workflow/scripts/wav_to_wem.py \
  replacement.wav "$temp_dir/replacement.wem"
```

Inspect the converted WEM, then rebuild the Bank. Omit the output argument to write the final Bank to `output/<input filename>`:

```sh
mamba run -n nanoha-gunlance-mod python \
  .agents/skills/soundbank-workflow/scripts/nbnk_media.py replace \
  original/soundbank/input.nbnk \
  --replace 22="$temp_dir/replacement.wem"
```

Use `--replace id:468604124=...` to target a Media ID, and repeat `--replace` for distinct targets.

The rebuild must preserve Media ID order and every chunk other than DIDX/DATA byte-for-byte. It must also align media offsets to 16 bytes and pass read-back verification.

## Validate the Final Bank

Run the NBNK inspector and wwiser against the final file. Re-extract each replaced entry and inspect or decode it with `tools/pyvgmstream/pyvgmstream.py`. Report the output path, SHA-256, replaced DIDX indices, and Media IDs.

Read [format-and-troubleshooting.md](references/format-and-troubleshooting.md) when a Bank is rejected, an index is ambiguous, a WEM is unrecognized, or the game is silent.
