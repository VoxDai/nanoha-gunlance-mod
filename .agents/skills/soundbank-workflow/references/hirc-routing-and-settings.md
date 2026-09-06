# HIRC Routing and Node Settings

Use this reference for Event analysis, shared media paths, node inheritance,
Container topology, and interruption. Concrete Python operations are in the
[HIRC API guide](../../../../tools/soundbank_editor/README.md#hirc); parameter
and return-value contracts are in public docstrings.

## Object and Route Model

The HIRC payload begins with an unsigned object count. Each record contains a
one-byte type, a little-endian body size, and a body starting with a four-byte
object ID. Object-relative offsets include those ID bytes at offset zero.

| Type | Role |
|---|---|
| `0x02` Sound | Source media and local playback settings |
| `0x03` Action | Play, PlayEvent, Stop, and other Event commands |
| `0x04` Event | Ordered Action references |
| `0x05` Random/Sequence Container | Children, weighted playlist, and selection behavior |
| `0x06` Switch Container | Switch/State group, value-to-child packages, and child behavior |
| `0x07` Actor-Mixer | Shared parent settings inherited by descendants |

```text
Event ulActionID
  → Action idExt
  → Sound or Container (possibly nested)
  → Sound sourceID
  → DIDX Media ID
```

PlayEvent invokes another Event, while Stop targets a playback object. A
Media ID is not a unique playback route: multiple Sounds, Events, or Containers
can use the same media with different inherited settings. Trace all users
before selecting a donor or target.

For MHW v120 authoring, each Action must belong to one Event at most within a
Bank. Multiple Events may use distinct Actions that target the same Sound; do
not reuse an Action ID across Events. In the charged-shelling runtime test,
sharing one Stop among three Events caused a loading crash; using independent
Actions removed the crash while retaining cross-Bank targets and zero
transition. This establishes the project constraint, not the engine-internal
crash mechanism or a rule for other Wwise versions.

## Trace and Bound the Change

Create a wwiser dump in the task's temporary directory using the main skill's
commands. Start from a known Event, HIRC object, or Media ID and record:

- Every Event Action and its order; Action type, target, and Bank when relevant.
- Container children, playlist weights, Random/Sequence mode, avoid-repeat
  behavior, Switch packages, default value, and child transition parameters.
- Sound source, DirectParentID, output, positioning, Aux, and inherited settings.
- Sibling or paired spatial paths and all descendants of a shared parent.
- Original serialized positions, which are distinct from parent references.

Object IDs are stable anchors; file offsets move when DATA or HIRC is rebuilt.
Preserve undeclared fields and compare the intended graph with both the rebuilt
graph and its serialization order.

## Node Properties and Inheritance

`NodeInitialParams` stores property IDs and corresponding values, including
Volume (`0x00`, float dB), Pitch (`0x02`, float cents), CenterPCT (`0x0E`, float
percentage), and GameAuxSendVolume (`0x17`, float dB). Random property ranges
contribute alongside base values. Optional fields change later offsets, so
never reuse an offset or flag pattern across nodes without inspecting it.

Pitch uses 100 cents per semitone. Node-local base Pitch and random offsets
accumulate with parent contributions; RTPC, State, and Action changes can also
affect playback. A Sound with no local random property may inherit a range
from a Container or Actor-Mixer. An explicit local zero does not cancel an
ancestor's contribution. Changing a shared Actor-Mixer can affect all of its
inheriting descendants. Identify the owner of each contribution before editing.

`AuxParams` contains a version-specific bit vector and optional Aux Bus IDs.
Interpret output, positioning, and Aux with wwiser on the exact target. Paired
or layered paths generally need corresponding changes unless asymmetry is the
reviewed intent. See the [Pitch API](../../../../tools/soundbank_editor/README.md#pitch)
for absence/zero semantics and guarded property insertion.

## Guarded Changes and New Routes

For a field change, identify the type and object ID, inspect its object-relative
location, and preserve its exact old value as a guard. For a structural change,
inspect the entire donor and every incoming/outgoing reference, then record
the required donor topology or body guard. Unknown object types can be retained
as bytes without being safe semantic authoring targets.

Clone Sounds from reviewed embedded donors. Preserve all fields other than the
explicit new identities and reviewed property changes; verify parent, output,
positioning, Aux, and memory-size fields. Add the media before validating its
new Sound. Parenting and inserting a Container child are separate operations:
confirm DirectParentID as well as the Container's child list.

Create children before their parent Container and Actions before their Event.
For v120, preserve this same order in the serialized HIRC. Matching IDs alone
does not establish a usable graph. Low-level insertion requires choosing an
appropriate anchor; high-level clones handle their documented placement rules.

For Random routes, review the playlist, positive weights, selection mode, and
avoid-repeat count. Equal weights with no avoid-repeat restriction yield
independent uniform choices; two children with an avoid-repeat count of one
alternate after the initial choice. Preserve unmodeled donor settings, and
verify the new child/playlist tail and parent links.

For Switch routes, review the Switch/State group, default value, ordered
packages, and per-child transition/fade data. Filtering a clone removes branches
only from that new topology, retains a valid default package, and leaves
original objects intact. An explicitly rebuilt topology can assign packages
independently of the donor's shared children. Validate child coverage and load
order for either approach; no general original-object deletion is provided.

When preserving original playback behind a new Event, route to the complete
original Event rather than accidentally selecting one descendant Sound. For
interruption, trace the native Stop route and clone its reviewed behavior to
the new playback object, preserving scope, transitions, and unknown fields.
Verify the new Action is attached to the correct Event and exercise the
interruption in game. If the user explicitly requests a Stop with no matching
native route, construct the reviewed scope, delay, transition and exceptions
through the Stop API instead. A transition is the old voice’s fade duration,
not a delay before another Action: a 50 ms Stop with no delay can overlap a
new Play for that fade window. Preserve native donor behavior when no change
was requested.

For a Stop targeting another Bank, declare the exact Action → Bank/Sound edge
and the reviewed target Sound body hash. Keep media and Sound ownership in
their intended Bank. Local validation checks the declaration against the
Action; joint validation of the actual final Banks must resolve the target,
its unique ownership, body hash, and media. Do not treat a declaration as
proof that the target exists, and do not turn an external-target error into
a generic missing-reference exemption. Bidirectional edges do not imply a
build-order dependency.

Keep parsing, joint structural validation, and runtime evidence distinct.
wwiser may parse a Bank that crashes during MHW loading. Confirm loading
before playback tests, then verify the intended Game Object, both Stop
directions, transition timing, negative triggers, and multiplayer scope.
Record only the cases actually exercised; successful zero-transition testing
does not establish a later 50 ms transition’s in-game result.

## Validation and Handoff Evidence

Compare exact summaries, semantic differences, references, and preservation;
reparse with the Library and wwiser, then re-extract changed media. These checks
do not replace game acceptance. For a persistent feature, provide `audio-design`
with:

- Original Bank path, version, Bank ID, DIDX index, and Media ID.
- Original and proposed routes, serialization order, donors, parents, paired
  paths, collision checks, and Stop/interruption behavior.
- Reviewed old/new fields and body/topology guards, allowed changes, and
  expected summary.
- Positive and negative game acceptance cases.

`design-implement` handles the resulting design's builders and tests. HIRC
analysis does not implicitly include implementation or release publication.
