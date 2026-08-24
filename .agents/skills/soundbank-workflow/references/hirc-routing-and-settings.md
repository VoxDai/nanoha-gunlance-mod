# HIRC Routing and Node Settings

Read this reference when a task requires more than extracting or replacing
embedded media: tracing a game Event, identifying every Sound path that uses a
Media ID, or changing volume, pitch, positioning, parent, Container, or Aux
behavior.

## Object and Route Model

The HIRC chunk begins with an object count. Each record contains a one-byte
type, a little-endian body size, and a body whose first four bytes are the
object ID. Common object types in these MHW Wwise v120 Banks are:

- `0x02`: Sound
- `0x03`: Action
- `0x04`: Event
- `0x05`: Random/Sequence Container

A typical route is:

```text
Event ulActionID
  -> Action idExt
  -> Sound or Container
  -> Container children, possibly through more parents
  -> Sound sourceID
  -> DIDX Media ID
```

A Media ID is not a unique playback route. The same media may appear in several
Sounds, Events, or Containers with different inherited pitch, volume,
positioning, Aux, or parent settings. Trace every path before selecting a
donor or edit target.

## Trace a Route

Create the dump in the task's `/tmp` workspace:

```sh
conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py \
  -d txt -dn "$temp_dir/bank-hirc" input.nbnk
```

Start from a known Event ID, HIRC object ID, or DIDX Media ID. Record the full
Event → Action → Container → Sound → Media route, including:

- every Event Action and its order;
- Action type, target ID, and Bank ID when relevant;
- Container children, playlist weights, random/sequence mode, and
  avoid-repeat count;
- Sound source ID, DirectParentID, output, positioning, and Aux inheritance;
- sibling or paired spatial paths that reach the same audible event;
- original object serialization positions.

Use object IDs as stable anchors. File offsets are diagnostic only and move
when DATA or HIRC is rebuilt.

## Common Node Properties

`NodeInitialParams` contains a property count, property IDs, and corresponding
values. Properties observed in this project include:

- `0x00` Volume, stored as a float in dB.
- `0x02` Pitch, stored as a float in cents.
- `0x0E` CenterPCT, stored as a float percentage.
- `0x17` GameAuxSendVolume, stored as a float in dB.

`AuxParams` contains a version-specific bit vector and optional Aux Bus IDs.
Use wwiser to interpret the exact object. Optional fields change later body
offsets, so never reuse an offset or flag pattern across objects or Banks
without inspecting and guarding the target.

## Guarded Prototype Changes

1. Parse the original through `SoundBank.from_file()` and create a
   `SoundBankEditor`; never edit the source file.
2. Locate every target by HIRC type and object ID.
3. Patch object-relative fields only, supplying the exact expected old value.
   Use `patch_u8()`, `patch_u16()`, `patch_u32()`,
   `patch_float()`, or `patch_bytes()` as appropriate.
4. For structural changes, use `clone_sound()`, `insert_object()`,
   `append_event_action()`, `create_play_action()`,
   `create_play_event_action()`, or
   `clone_random_sequence_container()`. These APIs rebuild sizes and reject
   collisions.
5. In the original v120 Banks, every Action referenced by an Event is
   serialized before that Event. Preserve this order and validate references
   after rebuilding.
6. Adjust paired or layered paths symmetrically unless the intended behavior is
   explicitly asymmetric.
7. Call `validate()`, compare the exact summary and HIRC semantic diff,
   re-extract changed media, and write only to a new temporary or
   user-authorized output path.

Unknown HIRC types remain raw bodies and are not safe structural authoring
targets. Arbitrary object deletion is unsupported.

## Cloned Sounds and Custom Routes

Clone only a reviewed donor Sound. Preserve all donor fields except explicitly
reviewed new object/source IDs and guarded property changes. Confirm the new
Sound's parent, output, positioning, Aux, and memory-size fields are correct.

Create and insert each new Action before its Event, then append or construct the
guarded Event Action list. When preserving an original sound through a new
Event, verify the PlayEvent Action targets the complete original Event rather
than only one descendant Sound.

For a random route, create and parent every child first, then use
`clone_random_sequence_container()` with the donor's exact playlist and
avoid-repeat count. The API preserves unmodeled donor fields and rebuilds only
`Children` and `CAkPlayList`. Child IDs must already exist and be unique;
weights must be positive signed 32-bit values. Equal weights with
`avoid_repeat_count=0` give independent uniform selection; with two children,
an avoid-repeat value of `1` alternates after the initial choice.

## Project Handoff Facts

For a persistent feature, supply `audio-design` with the audible behavior and
all verified implementation facts:

- original Bank path, SHA-256, version, Bank ID, DIDX index, and Media ID;
- complete original and proposed routes, Action ordering, donor IDs, parents,
  paired paths, and collision checks;
- object-relative offsets with exact old/new values;
- allowed media/HIRC changes and expected summary;
- positive and negative in-game acceptance cases.

`design-implement` encodes the resulting design in artifact builders and
tests. Do not edit those layers as an implicit part of HIRC analysis.
