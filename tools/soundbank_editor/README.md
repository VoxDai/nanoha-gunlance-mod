# soundbank_editor

`tools.soundbank_editor` is the project-local Python Library for lossless NBNK
parsing, embedded WEM extraction, DIDX/DATA rebuilding, and guarded HIRC edits.
It has no command-line or JSON-plan interface. Project changes belong in the
matching Python module under `builders/`.

## Parse and extract

```python
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(
    Path("original/soundbank/wp_gun_cmn.nbnk")
)
print(bank.version, bank.bank_id, len(bank.entries))

entry = bank.media_entry(index=22)  # DIDX indices are 1-based
Path("/tmp/22.wem").write_bytes(bank.extract_media(index=22))
```

`SoundBank.to_bytes()` is lossless. A parsed Bank with no edits must serialize
byte-for-byte identically, including unknown chunks and HIRC object bodies.

## Guarded media and HIRC edits

```python
editor = soundbank_editor.SoundBankEditor(bank)
editor.replace_media(
    Path("/tmp/replacement.wem"),
    index=22,
    expected_media_id=entry.media_id,
)
editor.hirc.patch_float(
    soundbank_editor.HIRC_SOUND,
    123456,
    0x20,
    -5.0,
    -6.5,
    label="lower reviewed Sound route",
)
rebuilt = editor.validate()
payload = editor.build()
```

Field patches are object-relative and require the exact old value. Media edits
rebuild DIDX/DATA with 16-byte alignment. `validate()` reparses the result and
rejects undeclared HIRC changes, broken Event/Action references, and invalid new
Sound-to-Media references. For Wwise v120, every Action referenced by an Event
must be serialized before that Event; the high-level Action APIs preserve this
load-order requirement automatically.

## Add a custom one-shot Sound

```python
editor.add_custom_sound_action(
    event_id=1665664746,
    action_id=4294967003,
    sound_id=4294967002,
    media_id=4294967001,
    donor_sound_id=330120372,
    wem=Path("/tmp/custom.wem"),
    expected_actions=(325918653, 744297877),
    expected_donor_source_id=321677221,
)
```

This v120-only operation appends the WEM, clones a reviewed embedded Sound,
creates a Play Action, and appends it to the guarded Event action list. The
donor Sound's node, output, positioning, Aux, and memory-size data are retained.
The new Action is inserted immediately before its owning Event rather than at
the end of the Action objects, matching the ordering used by the original Banks.
Use distinct explicit IDs; `wwise_fnv1(name)` is available when a deterministic
Wwise-style ID is wanted.

For persistent work, call these APIs from `apply_edits()` in the same-name Bank
module under `builders/`. Builders own mapping parsing, WAV-to-WEM conversion,
wwiser comparison, pyvgmstream decoding, and atomic output publication.
When mapped Audio should be layered over unchanged original media, the plan may
declare `MappingMediaOverlay(indices=(...), media_id=...)`. This builder-only
configuration validates one shared source, converts it once, appends it, and
then calls `apply_edits()`; it is not a JSON plan or Library CLI feature.

## Boundaries

- Structural authoring supports MHW Wwise v120. Other versions are read-only.
- Unknown HIRC types are preserved, not semantically decoded.
- Arbitrary HIRC object deletion is intentionally unsupported.
- A successful parse is not proof of game-runtime acceptance; complete trigger,
  mix, spatial, loop/Stop, and mod-conflict testing in game.
