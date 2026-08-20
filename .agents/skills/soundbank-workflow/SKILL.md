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
- Treat ordinary mapped media replacement as media-only: it must preserve HIRC byte-for-byte. A reviewed `MappingMediaOverlay` is different: it consumes declared Audio rows without replacing their original payloads, appends shared media, and relies on the Bank callback for its HIRC route.
- Put persistent project media and HIRC changes in the matching `BankBuildPlan`
  under `builders/`, using `tools.soundbank_editor` guarded APIs. Never patch absolute file offsets.
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

Inspect chunk order, sizes, DIDX indices, Media IDs, offsets, and alignment with
the Python Library:

```sh
conda run -n nanoha-gunlance-mod python <<'PY'
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(Path("input.nbnk"))
print("version", bank.version, "bank_id", bank.bank_id)
for index, entry in enumerate(bank.entries, 1):
    print(index, entry.media_id, entry.offset, entry.size, entry.offset % 16 == 0)
PY
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
conda run -n nanoha-gunlance-mod python <<PY
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(Path("input.nbnk"))
Path("$temp_dir/22.wem").write_bytes(bank.extract_media(index=22))
PY
```

Use `extract_media(media_id=ID)` instead of `index=`, or extract every entry with:

```sh
conda run -n nanoha-gunlance-mod python <<PY
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(Path("input.nbnk"))
output = Path("$temp_dir/wem")
output.mkdir(parents=True, exist_ok=True)
for index, entry in enumerate(bank.entries, 1):
    (output / f"{index}_{entry.media_id}.wem").write_bytes(entry.payload)
PY
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

Inspect the converted WEM, then register the replacement in the matching mapping
table and run its Python `BankBuildPlan`:

```sh
conda run -n nanoha-gunlance-mod python -m builders.wp07_gun_epvsp_shell --dry-run
conda run -n nanoha-gunlance-mod python -m builders.wp07_gun_epvsp_shell
```

The builder resolves every 1-based mapping index to its original Media ID,
converts the mapped audio, and calls `SoundBankEditor.replace_media()` with that
exact guard.

When several mapping rows describe one sound that must be layered over the
original effects, declare `MappingMediaOverlay(indices=(...), media_id=...)` on
the `BankBuildPlan`. Every declared row must exist and resolve to the same source
file. The builder excludes those indices from ordinary replacement, converts
the shared source once, appends it under the explicit Media ID, and then invokes
`apply_edits()` to create the reviewed Event -> Action -> Sound route. A missing
row, split source path, duplicate claimed index, or ID collision is fatal.

The media-only rebuild must preserve Media ID order and every chunk other than
DIDX/DATA byte-for-byte. It must also align media offsets to 16 bytes and pass
read-back verification.

## Change HIRC Settings

First trace the complete route in a wwiser text dump. The same Media ID may be
referenced by multiple Sound objects or spatial paths, so changing only the
first match can cause level or channel imbalance.

For a project Bank, implement the reviewed settings in
`builders/<bank-name>.py`. Import `soundbank_editor`, define the Bank's
`apply_edits(editor)` callback, and use `editor.hirc` to locate an object by HIRC
type and ID. Patch a body-relative field with its exact expected old value. Use
the v120 structural APIs only for reviewed Event/Action/Sound additions. The
builder must fail if an object, ID, route, or old value differs. Keep paired
playback paths symmetric unless the intended mix explicitly requires otherwise.
For an overlay, clone only a reviewed donor Sound, preserve all donor fields
except the explicit new Sound and Source IDs, and guard any additional
positioning override byte before changing it.

Run the single builder with `--dry-run`, then build to `output/` and inspect the
resulting normalized wwiser HIRC diff. Do not express persistent HIRC changes in
ad-hoc scripts; the same-name Python builder is the auditable edit plan.

## Validate the Final Bank

Reparse the final file with `SoundBank.from_file()` and run wwiser against it.
Re-extract each replaced or appended entry and inspect or decode it with
pyvgmstream. For a HIRC edit,
compare original and rebuilt dumps after removing file-offset-only differences
and require that all semantic changes match the declared builder settings.
Report the output path, SHA-256, replaced DIDX indices, Media IDs, and HIRC
changed-byte count.

Read [format-and-troubleshooting.md](references/format-and-troubleshooting.md) when a Bank is rejected, an index is ambiguous, a WEM is unrecognized, or the game is silent.
