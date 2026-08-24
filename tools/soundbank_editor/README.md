# soundbank_editor

`tools.soundbank_editor` is the project-local Python Library for lossless NBNK,
LMT v95/TIML, and WWEV v19 parsing. It provides embedded WEM extraction,
DIDX/DATA rebuilding, guarded HIRC edits, Motion-scoped request substitution,
and guarded WWEV record cloning. It has no command-line or JSON-plan interface.
Import its public API with `from tools import soundbank_editor`; the internal
modules are split by binary format.

## Parse and extract

```python
from pathlib import Path
from tools import soundbank_editor

bank = soundbank_editor.SoundBank.from_file(
    Path("original/nbnk/wp_gun_cmn.nbnk")
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

## Clone a random Container

Create every child object first, then clone a reviewed v120 Random/Sequence
Container with a guarded replacement playlist:

```python
editor.hirc.clone_random_sequence_container(
    donor_container_id=145848034,
    new_container_id=1771233315,
    playlist=((3336168856, 50000), (173193142, 50000)),
    expected_playlist=((535190438, 50000),),
    expected_avoid_repeat_count=1,
    avoid_repeat_count=0,
)
```

The operation locates the donor's terminal `Children` and `CAkPlayList`
structures, requires an exact expected playlist and avoid-repeat value, and
rebuilds only that tail. The donor's node, output, positioning, Aux, loop, and
other unmodeled fields remain byte-exact. Child IDs must already exist and be
unique; weights must be positive signed 32-bit values. The donor must be in
Random mode. Setting `avoid_repeat_count=0` allows independent selections;
omitting it preserves the donor value.

When cloned Sounds become children of the new Container, separately patch each
reviewed `DirectParentID` field with `patch_u32()`. Any positioning override
must likewise use its inspected object-relative offset and expected old byte.
`SoundBankEditor.validate()` reparses added Containers and rejects missing child
references or malformed child/playlist topology.

For persistent work, call these APIs from `apply_edits()` in the same-name Bank
module under `builders/`. During the current transition, builders parse tables
under `docs/mapping/` when invoked with `--mapping-dir docs/mapping`; they also own WAV-to-WEM conversion,
wwiser comparison, pyvgmstream decoding, and atomic output publication.
When mapped Audio should be layered over unchanged original media, the plan may
declare `MappingMediaOverlay(indices=(...), media_id=...)`. This builder-only
configuration validates one shared source, converts it once, appends it, and
then calls `apply_edits()`; it is not a JSON plan or Library CLI feature.

## Trace LMT requests through WWEV

```python
from pathlib import Path
from tools import soundbank_editor

lmt = soundbank_editor.LmtFile.from_file(Path("input.lmt"))
wwev = soundbank_editor.WwevFile.from_file(Path("input.wwev"))

for route in lmt.triggered_requests(wwev):
    print(
        route.motion_id,
        route.trigger_frame,
        route.event_group,
        route.slot,
        route.request_no,
        route.event_id,
    )
```

`LmtFile` preserves the complete input and exposes populated Motion headers and
embedded TIML types, transforms, and keyframes. Request reports map the low
eight `mTrigger` bits to ReqNo slots A through H. Repeated WWEV records are
expanded rather than silently collapsed, and shared TIML offsets list every
affected Motion.

## Guarded LMT request substitution

```python
editor = soundbank_editor.LmtEditor(lmt)
edit = editor.replace_request(
    motion_id=2,
    event_group="EventGroup06",
    slot="B",
    request_keyframe_frame=0.0,
    expected_request=100,
    replacement_request=101,
    expected_trigger_frames=(9.0,),
)
rebuilt_lmt = editor.validate()
```

The editor requires one unshared Motion TIML, one typed request transform, one
matching assignment keyframe, and the exact trigger-frame set. It changes only
the keyframe's four-byte value and rejects overlapping edits. ReqNo values use
the positive signed-16 range shared with WWEV.

## Guarded WWEV record cloning

```python
donor = wwev.record(100)
editor = soundbank_editor.WwevEditor(wwev)
editor.append_cloned_record(
    donor_request=100,
    expected_donor_event_id=123456,
    expected_donor_mode=2,
    expected_donor_sha256="0123456789abcdef" * 4,
    new_request=101,
    new_event_id=654321,
)
rebuilt_wwev = editor.validate()
```

Record SHA-256 covers the entire variable-length donor, including mode,
command hash, the 116-byte unknown region, WWPC, and its terminator. The editor
preserves dependencies and every original record byte-for-byte, updates only
the record count, and appends verified clones. Inspect and record the donor hash
before writing a persistent edit plan; do not derive a guard from an unreviewed
input at edit time.

`SoundBankEditor`, `LmtEditor`, and `WwevEditor` all provide `build()`,
`validate()`, summaries, and `write_atomic()`. Atomic writes reject input-path
overwrites and existing outputs unless `overwrite=True` is explicit. Catch
`EditorError` for every format or the format-specific `SoundBankError`,
`LmtError`, and `WwevError` subclasses.

## Boundaries

- Structural authoring supports MHW Wwise v120. Other versions are read-only.
- LMT/TIML parsing and editing supports MHW LMT v95 only.
- WWEV parsing and append-only editing supports MHW WWEV v19 only.
- Unknown HIRC types are preserved, not semantically decoded.
- Unknown WWEV record bytes are retained and included in donor guards.
- Arbitrary HIRC object deletion is intentionally unsupported.
- A successful parse is not proof of game-runtime acceptance; complete trigger,
  mix, spatial, loop/Stop, and mod-conflict testing in game.
