---
name: soundbank-workflow
description: "Inspect, query, and perform guarded standalone edits on Monster Hunter: World NBNK, LMT v95/TIML, and WWEV v19 files. Use for binary-format analysis, WEM extraction, HIRC and request routing, safe prototypes, and verified single-artifact output; do not author project designs or builders or publish releases."
---

# SoundBank Workflow

Use `tools.soundbank_editor` as the format-level Library for NBNK audio and
LMT/WWEV event routes. This skill explains binary inspection and guarded
single-artifact work. It does not decide audible behavior, implement persistent
project plans, or publish a Mod release.

## Capabilities and Limits

| Format | Read and query | Guarded changes |
|---|---|---|
| NBNK / Wwise v120 | Bank/chunk identity, 1-based DIDX, Media IDs, WEM extraction, HIRC routes and objects | replace or append media; patch, insert, append, or clone supported HIRC structures |
| LMT v95 / TIML | Motions, embedded TIML, EventGroup00–10, ReqNo A–H, low-eight-bit triggers, shared TIML | replace one guarded request assignment |
| WWEV v19 | header, dependencies, complete records, ReqNo/mode/Event routes, WWPC | append a full guarded donor clone with new ReqNo/Event |

The Library does not provide high-level deletion of original media, HIRC
objects, TIML data, or WWEV records. Do not simulate unsupported deletion with
raw byte patches. Unsupported versions and unknown structures are preserved or
rejected rather than guessed.

## Safety Rules

- Read project inputs from the documented `original/` directories. Never
  modify them, `assets/chunk/`, or reference Mod samples.
- Treat DIDX indices as 1-based and always pair an index with its inspected
  Media ID.
- Put extracted WEMs, converted media, prototypes, wwiser dumps, logs, and
  validation files in one task-specific `/tmp` directory.
- Never patch an absolute file offset. HIRC fields use object-relative offsets;
  LMT and WWEV changes use their high-level guarded APIs.
- Prefer in-memory build and validation. Write a single artifact only when the
  user requests it, to a new output path that cannot overwrite its input.
- A successful structural validation is not game acceptance. Trigger, timing,
  loudness, channel, positioning, interruption, and Mod conflicts require
  recoverable in-game testing.

## Prepare a Temporary Workspace

```sh
temp_dir="$(mktemp -d /tmp/soundbank-workflow.XXXXXX)"
trap 'rm -rf -- "$temp_dir"' EXIT INT TERM
```

Check project tools when the task needs WEM or HIRC validation:

```sh
conda run -n nanoha-gunlance-mod ffmpeg -version
conda run -n nanoha-gunlance-mod python -c "import pyvgmstream; print('pyvgmstream available')"
test -f tools/wwiser/wwiser.py
```

## Read and Query

Inspect one Bank and its embedded media:

```python
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(
    Path("original/nbnk/wp_gun_cmn.nbnk")
)
print(bank.version, bank.bank_id, len(bank.entries))
for index, entry in enumerate(bank.entries, 1):
    print(index, entry.media_id, entry.offset, entry.size, entry.offset % 16)
```

Resolve an animation request through WWEV:

```python
lmt = soundbank_editor.LmtFile.from_file(Path("original/lmt/w07_00.lmt"))
wwev = soundbank_editor.WwevFile.from_file(
    Path("original/wwev/hm_wp07_snd_ev.wwev")
)
for route in lmt.triggered_requests(wwev):
    print(route)
```

`triggered_requests()` preserves repeated WWEV expansions, shared-TIML Motion
lists, trigger frames and masks, slot, mode, and Event ID. Inspect the complete
route before selecting an edit guard.

For HIRC topology, first parse with wwiser and write the dump under the
temporary directory:

```sh
conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py \
  -d txt -dn "$temp_dir/bank-hirc" original/nbnk/wp_gun_cmn.nbnk
rg -n -C 8 'sourceID|ulID|DirectParentID|ulChildID|idExt' \
  "$temp_dir/bank-hirc.txt"
```

Read
[hirc-routing-and-settings.md](references/hirc-routing-and-settings.md) before
changing an Event route, Sound or Container topology, positioning, volume,
pitch, or Aux settings.

## Extract and Inspect WEM

```sh
conda run -n nanoha-gunlance-mod python <<PY
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(
    Path("original/nbnk/wp_gun_cmn.nbnk")
)
entry = bank.media_entry(index=22)
Path("$temp_dir/22.wem").write_bytes(bank.extract_media(index=22))
print(entry.media_id)
PY
```

```sh
conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py inspect \
  "$temp_dir/22.wem"
conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py decode \
  "$temp_dir/22.wem" "$temp_dir/22.wav"
```

Convert a reviewed WAV to the verified 48 kHz, 16-bit, stereo Wwise PCM WEM
layout before using it as a replacement:

```sh
conda run -n nanoha-gunlance-mod python tools/utils/wav_to_wem.py \
  replacement.wav "$temp_dir/replacement.wem"
```

## Guarded Standalone Edits

For NBNK, guard media identity and every HIRC old value:

```python
editor = soundbank_editor.SoundBankEditor(bank)
editor.replace_media(
    replacement_wem,  # Path inside the task-specific temporary directory
    index=22,
    expected_media_id=entry.media_id,
)
editor.hirc.patch_float(
    soundbank_editor.HIRC_SOUND,
    123456,
    0x20,
    -5.0,
    -6.5,
    label="reviewed Sound volume",
)
rebuilt_bank = editor.validate()
```

Use `append_media()`, `clone_sound()`, `insert_object()`,
`append_event_action()`, and
`clone_random_sequence_container()` only after inspecting the donor and every
reference. New IDs must be explicit and collision checked.

For LMT, supply the complete Motion-level guard:

```python
lmt_editor = soundbank_editor.LmtEditor(lmt)
lmt_editor.replace_request(
    motion_id=2,
    event_group="EventGroup06",
    slot="B",
    request_keyframe_frame=0.0,
    expected_request=6470,
    replacement_request=6592,
    expected_trigger_frames=(9.0,),
)
rebuilt_lmt = lmt_editor.validate()
```

For WWEV, hash and guard the entire variable-length donor record:

```python
wwev_editor = soundbank_editor.WwevEditor(wwev)
wwev_editor.append_cloned_record(
    donor_request=6470,
    expected_donor_event_id=3567942167,
    expected_donor_mode=2,
    expected_donor_sha256="1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f",
    new_request=6592,
    new_event_id=3176129810,
)
rebuilt_wwev = wwev_editor.validate()
```

The donor hash covers mode, command data, the unknown region, WWPC, and record
terminators. Do not derive a guard from an unreviewed or already modified input.

## Validate and Write

Before writing, compare the editor summary with the reviewed intent, call
`validate()`, and reparse `build()`. For NBNK also run wwiser, re-extract
every changed WEM, and inspect/decode it with pyvgmstream. For an LMT/WWEV pair,
resolve the rebuilt request route again and require only the intended rows.

`SoundBankEditor`, `LmtEditor`, and `WwevEditor` provide
`write_atomic()`. They reject input-path overwrites and existing outputs
unless overwrite is explicitly authorized. Keep diagnostics in `/tmp`; report
the final path, SHA-256, summary, and preservation checks.

Read
[format-and-troubleshooting.md](references/format-and-troubleshooting.md) when
parsing fails, WEM is silent, an index or route is ambiguous, or the game does
not trigger the expected sound.

## Project Handoff

- Use `audio-design` to turn verified behavior, audio, artifacts, and guards
  into a design contract.
- Use `design-implement` to encode a specified design in persistent artifact
  builders, integration validators, and tests.
- Use `build-mod` to execute the registered complete Mod plan and publish
  `release/nativePC/`.

Do not edit those project layers as an implicit side effect of binary analysis.
