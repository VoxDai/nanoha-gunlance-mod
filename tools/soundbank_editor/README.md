# soundbank_editor

`tools.soundbank_editor` is the project-local Python Library for lossless NBNK,
LMT v95/TIML, and WWEV v19 parsing and guarded editing. It has no CLI or
JSON-plan interface.

This README owns **API navigation and examples**. Public docstrings own exact
parameters, return values, guards, exceptions, and side effects. For binary
structure, route analysis, editing workflow, external validation tools, and
project handoff, read the
[soundbank-workflow skill](../../.agents/skills/soundbank-workflow/SKILL.md).

## Public entry point

```python
from pathlib import Path
from tools import soundbank_editor as se
```

Import public names from this package. Its `__all__` is the public API list;
`editor.py` retains legacy imports, and `EditSummary` aliases
`SoundBankEditSummary`. Neither introduces a separate implementation. Use
`help(se.SoundBankEditor.replace_media)`, for example, to inspect a contract.

| API family | Public entry points and source docstrings |
|---|---|
| NBNK | [SoundBank, SoundBankEditor, ExternalStopReference, validate_external_stop_references, Chunk, MediaEntry, SoundBankEditSummary, SoundBankDiff, validate_wem, wwise_fnv1](soundbank.py) |
| HIRC | [HircEditor, HircObject, SwitchContainerTopology, SwitchNodeParams](hirc.py); [HircPitchSettings](_pitch.py) |
| LMT/TIML | [LmtFile, LmtEditor, LmtAction, TimlType, TimlTransform, TimlKeyframe, TriggeredRequest, LmtRequestEdit, LmtEditSummary](lmt.py) |
| WWEV | [WwevFile, WwevEditor, WwevRecord, WwevRecordEdit, WwevEditSummary](wwev.py) |
| Errors | [EditorError, SoundBankError, LmtError, WwevError](errors.py) |
| Constants and compatibility | [Package docstring and exports](__init__.py); [legacy imports](editor.py) |

`from_file()` records the resolved input path; `from_bytes()` has no source-path
identity. Parsed files serialize losslessly with `to_bytes()`. Editors keep
changes in memory until explicitly written. The examples below run from the
project root and share the imports above; no example writes into `original/`.

## NBNK and media

| Task | API |
|---|---|
| Parse, inspect, serialize | `SoundBank.from_file()`, `from_bytes()`, `chunk()`, `hirc_payload`, `to_bytes()` |
| Select or extract media | `media_entry()`, `extract_media()`, `extract_all_media()` on parsed Bank or editor |
| Compare parsed Banks | `SoundBank.diff(other)` → `SoundBankDiff` |
| Replace or append | `SoundBankEditor.replace_media()`, `append_media()` |
| Add a route | `add_custom_sound_action()`, `add_play_event_action()` |
| Check a WEM or derive an ID | `validate_wem()`, `wwise_fnv1()` |

Select media by exactly one of the 1-based DIDX `index` or the unique
`media_id`. `extract_all_media()` maps **DIDX indices**, not Media IDs, to bytes.
Editor queries include pending replacements and additions; parsed Bank queries
remain unchanged.

```python
bank = se.SoundBank.from_file("original/nbnk/wp_gun_cmn.nbnk")
entry = bank.media_entry(index=22)
assert entry.media_id == 723639573
wem_bytes = bank.extract_media(index=22)
assert bank.to_bytes() == Path("original/nbnk/wp_gun_cmn.nbnk").read_bytes()
```

To save an extracted WEM for inspection, write the returned bytes inside the
task's temporary directory. Conversion, pyvgmstream, and wwiser commands are
in the skill. `validate_wem()` only checks enough RIFF/fmt structure to reject
obvious invalid input and ordinary PCM WAV; it does not decode audio or certify
the project's complete Wwise PCM layout.

This callable recipe accepts a converted WEM, guards the reviewed original
media identity, and returns a validated editor without writing a file:

```python
def replace_reviewed_media(wem: bytes | Path) -> se.SoundBankEditor:
    editor = se.SoundBankEditor.from_file("original/nbnk/wp_gun_cmn.nbnk")
    editor.replace_media(wem, index=22, expected_media_id=723639573)
    editor.validate()
    return editor
```

`expected_media_id` and `expected_sha256` are optional in the API. The project
workflow requires reviewed identity guards; persistent guards should be fixed
from original evidence. Replacing media is not restricted to v120 by the method,
whereas adding media and high-level structural authoring require v120. Exact
support and checks are documented per method, not implied for all versions.

## HIRC

Access the Bank editor's `hirc` attribute; a standalone `HircEditor` instead
accepts a HIRC chunk payload and explicit version/reserved IDs.

| Task | API |
|---|---|
| Inspect | `objects()`, `object()`, `object_body()`, `object_ids`, `event_actions()`, `switch_container_topology()` |
| Reserve new media IDs | `reserve_id()`; normally coordinated by `SoundBankEditor.append_media()` |
| Patch a field | `patch_bytes()`, `patch_u8()`, `patch_u16()`, `patch_u32()`, `patch_float()` |
| Replace/insert a body | `replace_object_body()`, `insert_object()` |
| Assemble Actions | `create_play_action()`, `create_play_event_action()`, `create_stop_action()`, `append_event_action()` |
| Clone | `clone_sound()`, `clone_stop_action()`, `clone_random_sequence_container()`, `clone_switch_container()`, `clone_switch_container_with_topology()` |
| Inspect changes | `changed_byte_count`, `added_objects`, `patched_objects`, `rebuilt_objects`, `resized_objects`, `build()` |

`objects()` and `object()` return detached copies, and `object_body()` returns
immutable bytes. Editing these results does not edit the Bank. HIRC indices are
zero-based serialized positions. Field offsets are relative to the body,
including the leading four-byte object ID; field patches cannot alter that ID.
Use inspected offsets and expected old bytes, not offsets copied from a different
node. Exact patch/rebuild composition rules are in the method docstrings.

`create_play_action()`, `create_play_event_action()`, and `create_stop_action()` return complete bodies,
including the ID, without inserting or reserving anything. `insert_object()`
accepts the body **after** those four ID bytes. Attaching an Action to an Event
is another operation. The Bank-level convenience methods compose these steps.

### Pitch

Pitch methods support v120 Sound, Random/Sequence Container, Switch Container,
and Actor-Mixer nodes. This example uses reviewed literal settings from the
original shell Bank:

```python
pitch_editor = se.SoundBankEditor.from_file(
    "original/nbnk/wp07_gun_epvsp_shell.nbnk"
)
updated = pitch_editor.hirc.set_pitch(
    se.HIRC_RANDOM_SEQUENCE_CONTAINER,
    145848034,
    expected=se.HircPitchSettings(None, (-50.0, 50.0)),
    base_cents=-100.0,
    random_range_cents=(-25.0, 25.0),
)
assert updated == se.HircPitchSettings(-100.0, (-25.0, 25.0))
pitch_editor.validate()
```

`pitch_settings()` reads local settings. In `expected`, `None` means the
property is absent; replacement `None` retains the existing property. Expected
values compare float32 encodings, including signed zero. Values must be finite
float32 numbers; ranges are ordered `(min, max)` tuples. Zero inserts or retains
an explicit property rather than removing it. Same-value updates validate the
guard but do not add edit bookkeeping. See `set_pitch()` for insertion and
patch conflicts, and the
[HIRC reference](../../.agents/skills/soundbank-workflow/references/hirc-routing-and-settings.md#node-properties-and-inheritance)
for inheritance and audible interpretation.

### Clone and compose routes

The following recipe is parameterized: all IDs and guards must come from the
reviewed route. It adds media, clones an embedded Sound, and attaches a new Play
Action to an existing Event. It does not choose a donor or output path:

```python
def add_reviewed_one_shot(
    editor, *, wem, event_id, action_id, sound_id, media_id,
    donor_sound_id, expected_actions, expected_donor_source_id,
):
    editor.add_custom_sound_action(
        event_id=event_id,
        action_id=action_id,
        sound_id=sound_id,
        media_id=media_id,
        donor_sound_id=donor_sound_id,
        wem=wem,
        expected_actions=expected_actions,
        expected_donor_source_id=expected_donor_source_id,
    )
    return editor.validate()
```

For other compositions, use the following entry points and their docstrings:

- `add_play_event_action()` attaches a new PlayEvent Action to an existing
  Event. Each Action may belong to only one Event in a v120 Bank; create a
  distinct Action per Event even when their target Sound is shared.
  `clone_stop_action()` inserts a guarded Stop clone before the selected
  Event; attach it separately with `append_event_action()`.
- `clone_random_sequence_container()` requires an exact donor playlist and
  avoid-repeat guard, existing unique replacement children, and a Random-mode
  donor. It does not update the children's DirectParentID.
- `clone_switch_container()` accepts a complete donor-child map: replacement
  IDs or `None` to omit that branch from the clone. It requires the reviewed
  `SwitchContainerTopology` and full donor-body SHA-256. The default package
  must survive. Original objects are not deleted.
- `clone_switch_container_with_topology()` takes a complete replacement
  topology instead of a child map, with the same donor guards. It supports
  independent package assignment while preserving the donor prefix.

Inspect topology and body hashes during review, then persist those values for
reproducible edits. Do not compute a persistent expected guard from the live
donor during the build. New IDs must be explicit; `wwise_fnv1(name)` computes a
deterministic ID but does not reserve it or guarantee collision freedom.

### Explicit Stop and companion Banks

Use `clone_stop_action()` to preserve a native donor's scope, transitions,
exceptions, and unknown fields. For an explicitly requested new Stop,
`create_stop_action(action_id, target_id, delay_ms=0, transition_ms=None,
fade_curve=4)` constructs v120 `Stop_E_O`: Game Object scope, a non-bus target,
and an empty exception list. `None` omits TransitionTime; `0` writes zero;
`50` writes a 50 ms fade. Delay and fade are separate: a zero-delay Stop can
begin fading an old voice while a Play in the same Event starts a new voice.
Insertion, guarded Event-list editing, and reference validation remain separate.

An external target must be a Sound with a reviewed complete body hash. Declare
each exact edge with `ExternalStopReference(action_id, target_bank_id,
target_sound_id, expected_body_sha256)`. Pass the declarations through the
`external_stop_references=` keyword on `SoundBankEditor`, `from_file()`, or
`from_bytes()`. Declarations are immutable and must name Event-owned Stop
Actions targeting a different Bank. They cannot authorize Play/PlayEvent,
local targets, missing Actions, or a generic set of unresolved IDs.

`validate()`, `diff()`, and `write_atomic()` check the declaring Bank and its
exact declarations; they do **not** establish that companion targets exist.
Before publishing a set containing external Stops, call:

```python
def validate_stop_bundle(final_banks, declarations_by_bank_id):
    se.validate_external_stop_references(final_banks, declarations_by_bank_id)
```

Pass parsed **final** `SoundBank` values and a mapping from declaring Bank ID
to its reviewed declaration tuple. The joint check repeats local validation,
requires unique Bank identities and target Sound ownership, checks the target
body hash and embedded media, and rejects undeclared external Stops. Both
directions may refer to each other; this does not impose a build order or prove
runtime loading and Game Object identity. Single-artifact diagnostics with
declarations must report that joint resolution is still outstanding.

## LMT and WWEV

| Task | API |
|---|---|
| Inspect a Motion/TIML | `LmtFile.action()`, `timl_for_motion()`, `actions`, `entry_count` |
| Expand trigger routes | `LmtFile.triggered_requests(wwev=None)` → tuple of `TriggeredRequest` |
| Replace one assignment | `LmtEditor.replace_request()` → `LmtRequestEdit` |
| Query every matching record | `WwevFile.records_for_request()`, `WwevEditor.records_for_request()` |
| Require one matching record | `WwevFile.record()` → `WwevRecord` |
| Inspect a record guard | `WwevRecord.raw`, `size`, `sha256` |
| Append a full donor clone | `WwevEditor.append_cloned_record()` → appended `WwevRecord` |
| Clone a complete multi-record request | `WwevEditor.append_cloned_request()` → ordered appended `WwevRecord` tuple; full-record hash guards for every donor, one unused Event per record, one unused shared ReqNo; atomic commit |

```python
lmt = se.LmtFile.from_file("original/lmt/w07_00.lmt")
wwev = se.WwevFile.from_file("original/wwev/hm_wp07_snd_ev.wwev")
rows = lmt.triggered_requests(wwev)
selected = [row for row in rows if row.motion_id == 2 and row.slot == "B"]
assert len(selected) == 1
assert (selected[0].request_no, selected[0].event_id) == (6470, 3567942167)
```

Repeated WWEV records produce separate rows; unresolved requests retain a row
with `None` WWEV fields. Shared TIML reports all affected Motion IDs. Motion IDs
are zero-based; WWEV record indices are one-based. `record()` rejects both zero
matches and ambiguous matches, whereas `records_for_request()` returns all
matches, including an empty tuple.

The following continues the example in memory using guards verified against
these original artifacts. The new Event ID must separately exist in the target
Bank for a playable combined Mod; LMT/WWEV validation does not check the Bank.

```python
lmt_editor = se.LmtEditor(lmt)
lmt_editor.replace_request(
    motion_id=2,
    event_group="EventGroup06",
    slot="B",
    request_keyframe_frame=0.0,
    expected_request=6470,
    replacement_request=6592,
    expected_trigger_frames=(9.0,),
)
wwev_editor = se.WwevEditor(wwev)
wwev_editor.append_cloned_record(
    donor_request=6470,
    expected_donor_event_id=3567942167,
    expected_donor_mode=2,
    expected_donor_sha256=(
        "1c6fd120501ce70925b00d8ab0166a38b132"
        "934e220a1095506424024a33e53f"
    ),
    new_request=6592,
    new_event_id=3176129810,
)
rebuilt_lmt = lmt_editor.validate()
rebuilt_wwev = wwev_editor.validate()
changed = [
    row for row in rebuilt_lmt.triggered_requests(rebuilt_wwev)
    if row.motion_id == 2 and row.slot == "B"
]
assert len(changed) == 1
assert (changed[0].trigger_frame, changed[0].request_no, changed[0].event_id) == (
    9.0, 6592, 3176129810,
)
```

Request edits require positive signed-16 ReqNo values, an unshared Motion TIML,
one matching typed assignment, and the exact trigger-frame set. Frame guards
use an absolute tolerance of `1e-5`. WWEV additions reject existing new ReqNo
or Event IDs within that editor. The donor hash covers the complete record;
original records and dependencies are preserved.

## Validation and writing

All three file editors expose the following; `summary` is a property:

| Member | Contract |
|---|---|
| `build()` | Return current bytes; no disk write and no full validation pass |
| `validate()` | Build and reparse, check format-specific invariants, return a parsed file |
| `summary` | Return an immutable change report without validating |
| `write_atomic(output, overwrite=False)` | Validate, stage beside the output, then replace that output path |

`SoundBankEditor.diff()` validates and returns a `SoundBankDiff`; the other
editors expose summaries and byte-preservation checks instead. A standalone
`HircEditor.build()` returns only the HIRC payload and does not perform Bank-level
validation. SoundBank validation checks declared HIRC changes, v120 Event/Action
references, single-Event Action ownership and order, and newly added
Sound/Container references. External Stops require the separate joint check
described above. It does not
semantically validate every unknown field or every existing Container.

Here is an optional temporary-file round trip using the `lmt_editor` above:

```python
from tempfile import TemporaryDirectory

with TemporaryDirectory(prefix="soundbank-api.", dir="/tmp") as temp_dir:
    output = lmt_editor.write_atomic(Path(temp_dir) / "edited.lmt")
    assert se.LmtFile.from_file(output).to_bytes() == lmt_editor.build()
```

`overwrite=True` permits replacing an existing output. It never permits
replacing a recorded input path, compared after path resolution. An editor
created from bytes has no input path to protect. The existence check is not
concurrency-safe exclusive creation; coordinate competing writers externally.
The atomic file replacement is not a multi-file release transaction.

Catch `EditorError` for Library parsing/editing failures or use its
format-specific subclasses. Ordinary filesystem failures may propagate as
`OSError`; this hierarchy does not wrap every Python exception. No generic
media, object, timeline, or record deletion API is provided. See the
[workflow](../../.agents/skills/soundbank-workflow/SKILL.md#work-from-evidence-to-a-verified-artifact)
for external decoding, preservation evidence, and game acceptance, and its
[project handoff](../../.agents/skills/soundbank-workflow/SKILL.md#project-handoff)
for design, builder, and complete-release work.
