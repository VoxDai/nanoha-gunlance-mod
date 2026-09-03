# soundbank_editor

`tools.soundbank_editor` is the project-local Python Library for lossless NBNK,
LMT v95/TIML, and WWEV v19 parsing. It provides embedded WEM extraction,
DIDX/DATA rebuilding, guarded HIRC edits and Container cloning, Motion-scoped
request substitution, and guarded WWEV record cloning. It has no command-line
or JSON-plan interface.
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
Sound-to-Media references. For Wwise v120, Container children must be serialized
before their parent Container, and every Action referenced by an Event must be
serialized before that Event. The high-level Container and Action APIs preserve
these load-order requirements automatically.

## Read and set node pitch

`HircEditor.pitch_settings()` and `set_pitch()` support Wwise v120 Sounds, Random/Sequence Containers, Switch
Containers, and Actor-Mixers (`HIRC_ACTOR_MIXER`). Both base Pitch and its random offsets are in **cents**
(100 cents = one semitone). The API locates the property tables structurally; callers do not supply byte offsets.

```python
bank = soundbank_editor.SoundBank.from_file(
    Path("original/nbnk/wp07_gun_epvsp_shell.nbnk")
)
editor = soundbank_editor.SoundBankEditor(bank)

settings = editor.hirc.pitch_settings(
    soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 145848034
)
# HircPitchSettings(base_cents=None, random_range_cents=(-50.0, 50.0))

# Add a fixed offset and change the existing random range in one guarded edit.
updated = editor.hirc.set_pitch(
    soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
    145848034,
    expected=soundbank_editor.HircPitchSettings(
        base_cents=None, random_range_cents=(-50.0, 50.0)
    ),
    base_cents=-100.0,
    random_range_cents=(-25.0, 25.0),
)
# This container now contributes between -125 and -75 cents.
rebuilt = editor.validate()
```

`HircPitchSettings` is frozen. A `None` field in the inspected/expected settings means that the property **does not
exist**, which differs from an explicit zero. `expected` must match both fields, including absence; numerical guards
compare float32 encodings, including the sign of zero. Persistent builders should supply reviewed literal settings
rather than deriving the guard from the live target during a build.

In `set_pitch()` replacement arguments, omitted values or `None` retain the current setting. At least one setting is
required. Missing properties are inserted in ID order, even when the requested value is zero. The returned settings
contain the stored float32 values. Same-value requests are no-ops after guard validation and leave the body and edit
summary unchanged.

For example, on a fresh editor for the same original Bank, disable just the container's random contribution while
retaining its absent base Pitch:

```python
editor = soundbank_editor.SoundBankEditor(bank)
editor.hirc.set_pitch(
    soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
    145848034,
    expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
    random_range_cents=(0.0, 0.0),
)
```

To add a fixed local offset directly to its Sound, whose own Pitch properties are absent:

```python
editor.hirc.set_pitch(
    soundbank_editor.HIRC_SOUND,
    535190438,
    expected=soundbank_editor.HircPitchSettings(None, None),
    base_cents=100.0,
)
```

These methods read/edit **local node contributions**. Parent Pitch settings still accumulate, and RTPC/State/Action
changes may also affect playback. A Sound with no local random property can inherit a random range from its Container or
Actor-Mixer. Setting a child's local base or range to zero does not cancel an ancestor's contribution. Editing a shared
Actor-Mixer affects all descendants that inherit its settings.

Base values and range endpoints must be Python `int`/`float` numbers encodable as finite float32, excluding booleans,
NaN, infinity and overflow. Random ranges are two-element `(min, max)` tuples with `min <= max`; asymmetric ranges are
allowed. Property removal is not provided; `(0.0, 0.0)` leaves an explicit zero range. Unsupported object types/versions
and malformed property tables raise `SoundBankError`.

Edits are preflighted as a unit: a bad guard, invalid input, count overflow or edit conflict leaves the object and edit
bookkeeping unchanged. Existing Pitch values use the normal field-patch bookkeeping, while insertion rebuilds the object
and updates its size. Other property bytes, node routing, FX/source parameters, and the remaining object body are
preserved.

The existing composition rules still apply:

- Equal-length Pitch edits can coexist with non-overlapping field patches; rewriting an already patched Pitch field is
  rejected, except for a no-op.
- Inserting a property cannot follow any field patch on that same object. After an object rebuild, field patches
  (including equal-length Pitch edits)
  are rejected. Combine required base/range changes in one call when inserting properties, and use the existing guarded
  whole-body replacement workflow when combining a structural change with other edits on the same object.

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

## Clone a native Stop Action

When a custom playback object must follow an existing Event's interruption
behavior, clone the reviewed native Stop Action instead of reconstructing its
version-specific fields:

```python
editor.hirc.clone_stop_action(
    donor_action_id=743936681,
    new_action_id=2987046856,
    new_target_id=4149261730,
    expected_target_id=60034062,
    expected_body_sha256=(
        "137f38d973a5e3b84d35d84146d2b562e21e575abbfee532"
        "b8531d3583ae0ebd"
    ),
    before_event_id=461444626,
)
editor.hirc.append_event_action(
    461444626,
    2987046856,
    expected_actions=(743936681,),
)
```

This v120-only API requires an exact donor target and full body hash, verifies
that the new target and serialization anchor exist, and rejects ID collisions.
It preserves every donor field except the Action ID and target ID, including
scope, properties, transition, fade curve, exception data, and unknown bytes.
The clone is serialized before the selected Event; attach it separately with
the guarded `append_event_action()` API. `SoundBankEditor.validate()` reparses
Stop Action targets and rejects missing references.

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
Random mode. The clone retains stable type-group placement while ensuring that
it is serialized after every playlist child. Setting `avoid_repeat_count=0`
allows independent selections; omitting it preserves the donor value.

When cloned Sounds become children of the new Container, separately patch each
reviewed `DirectParentID` field with `patch_u32()`. Any positioning override
must likewise use its inspected object-relative offset and expected old byte.
`SoundBankEditor.validate()` reparses added Containers and rejects missing child
references or malformed child/playlist topology.

## Clone and filter a Switch Container

Inspect a Wwise v120 donor once, persist the reviewed topology and body hash as
guards, create the replacement child objects, then clone the Switch Container
with an explicit mapping for every donor child:

```python
reviewed = soundbank_editor.SwitchContainerTopology(
    group_type=0,
    group_id=3251135135,
    default_switch=3396333570,
    continuous_validation=0,
    children=(101900622, 125400496, 127521149, 133098601, 438972177),
    switch_packages=reviewed_packages,
    node_params=reviewed_node_params,
)

editor.hirc.clone_switch_container(
    donor_container_id=368774789,
    new_container_id=4010844647,
    child_map={
        101900622: None,
        125400496: None,
        127521149: 3163089818,
        133098601: None,
        438972177: None,
    },
    expected_topology=reviewed,
    expected_body_sha256=(
        "a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde"
        "1358c02ab99043bb"
    ),
)
```

`switch_container_topology()` returns the parsed Group, default value,
Children, ordered Switch packages, and ordered `SwitchNodeParams` records for
inspection. Persistent edits must use a reviewed literal rather than deriving
their guard from the live donor during the build.

The clone preserves the donor prefix and property bytes, package order, and
per-child behavior/transition/fade parameters. Each donor child must map
exactly once to an existing unique HIRC object or `None`; packages emptied by
deletion are omitted. The default Switch package must survive. Ambiguous or
malformed tails, internal package/parameter references that do not exactly
cover the retained Children, body-hash/topology drift, ID collisions, and
non-v120 Banks are rejected. The clone retains stable type-group placement
unless a retained child is later, in which case it is placed after that child.
`SoundBankEditor.validate()` repeats the topology parse after serialization and
also rejects missing or parent-before-child references.

When a reviewed route must assign packages independently of the donor's shared children, use
`clone_switch_container_with_topology()`. It accepts a complete replacement `SwitchContainerTopology`, while retaining
the donor prefix and requiring the same exact donor topology and body SHA-256 guards. Every replacement child must
already exist; default-package coverage, unique IDs, package-to-child coverage, serialization order, and v120
compatibility are validated identically to the filtered clone API.

For persistent project work, call these APIs from the guarded `apply_edits()`
callback of an explicit plan under `builders/`. `SoundBankBuildPlan` declares
each `MediaReplacement` or `MediaAddition` directly, including its 1-based DIDX
index, Media ID, project WAV path, original Bank identity and exact expected
`SoundBankEditSummary`. The builder converts WAVs, runs wwiser and pyvgmstream
validation, rejects callback media edits not declared in the plan, and publishes
only after read-back succeeds. `docs/mapping/` is
research documentation and is never parsed at build time.

LMT and WWEV routes use the same pattern through `LmtBuildPlan` and
`WwevBuildPlan`, with fixed source hashes, exact editor summaries and fixed
output hashes. `ModBuildPlan` groups every target and runs cross-file validators
before replacing the complete `release/nativePC/` tree. These project plan
types are orchestration around the Library; the Library itself remains free of
CLI and project-specific route data.

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
- Project builders fix original NBNK/LMT/WWEV SHA-256 values, but intentionally
  do not fix WAV hashes so a reviewed mix can be adjusted at the same declared
  path and rebuilt without changing routing code.
- A successful parse is not proof of game-runtime acceptance; complete trigger,
  mix, spatial, loop/Stop, and mod-conflict testing in game.
