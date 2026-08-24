# HIRC Routing and Node Settings

Read this reference when a task requires more than replacing embedded media:
tracing a game Event, identifying every Sound path that uses a Media ID, or
changing volume, pitch, positioning, or Aux behavior.

## Object and Route Model

The HIRC chunk begins with an object count. Each record contains a one-byte type,
a little-endian body size, and a body whose first four bytes are the object ID.
Common object types in these MHW Banks are:

- `0x02`: Sound
- `0x03`: Action
- `0x04`: Event
- `0x05`: Random/Sequence Container

A typical playback route is:

```text
Event ulActionID
  -> Action idExt
  -> Sound or Container
  -> Container child IDs, possibly through more parents
  -> Sound sourceID
  -> DIDX Media ID
```

Do not stop after finding one `sourceID`. The same media can appear in multiple
Sound objects, and separate Events or containers may apply different pitch,
volume, positioning, or Aux settings. Also inspect `DirectParentID`, every
container child, and inherited parent properties.

## Trace a Route

Create the dump in the task's `/tmp` workspace:

```sh
conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py \
  -d txt -dn "$temp_dir/bank-hirc" input.nbnk
```

Start from the known DIDX Media ID or Event ID and search the dump. Record the
complete Event -> Action -> Container -> Sound route, including sibling paths
that reach the same media. Use object IDs as stable anchors; displayed file
offsets are diagnostic only and change when DATA is rebuilt.

## Common Node Properties

`NodeInitialParams` contains a property count, an array of property IDs, and a
corresponding array of values. Relevant IDs observed in this project include:

- `0x00` Volume, stored as a float in dB.
- `0x02` Pitch, stored as a float in cents.
- `0x0E` CenterPCT, stored as a float percentage.
- `0x17` GameAuxSendVolume, stored as a float in dB.

`AuxParams` contains a version-specific bit vector and, when present, Aux Bus
IDs. Use wwiser to interpret the exact node layout. Do not reuse a flag offset or
bit pattern across Banks without checking the target object, because optional
fields change later body offsets.

## Implement a Project Setting

1. Start from `original/nbnk/<bank>.nbnk` and trace all affected routes in
   a wwiser text dump.
2. Add the setting to `apply_edits()` in `builders/<bank>.py`; keep the route,
   audible intent, units, and reason in comments.
3. Use `editor.hirc` to locate each target by HIRC type and ID. Patch only an
   object-relative field and supply the exact expected old value.
4. Adjust every paired or layered path symmetrically unless asymmetry is the
   intended result. A pitch-shifted duplicate or one-sided volume edit can sound
   like surround processing or a channel imbalance.
5. Use `insert_object()`, `append_event_action()`, `add_play_event_action()`,
   `add_custom_sound_action()`, or `clone_random_sequence_container()` for
   reviewed Wwise v120 structural changes. These APIs rebuild object and chunk
   sizes and reject ID collisions. In the original v120 Banks every Event Action
   is serialized before the Event that references it; use the high-level APIs,
   which insert a new Action immediately before its owning Event, and treat
   forward Action references as invalid. Unknown object types remain raw bodies
   and must not be structurally authored.
6. Run the builder `--dry-run`, build to a temporary output, parse it with
   wwiser, and compare semantic dumps. Only declared fields may differ.
7. Re-extract and decode all replaced media, then perform in-game trigger,
   loudness, channel, camera-position, and conflict tests.

`tools.soundbank_editor` is a Python Library, not a CLI. Use a per-Bank
`BankBuildPlan` for persistent media and HIRC changes. The builder's mapping
replacement phase remains media-only; bank-specific structural changes belong
only in its Python `apply_edits()` callback. If mapping Audio rows feed an
additional route while their original media must remain intact, declare them as
a `MappingMediaOverlay` on that plan. The shared WEM is appended before the
callback runs; the callback must guard its Media ID, clone the reviewed Sound,
insert each Action before its Event, and preserve the Event's existing Action as
the first list entry.

For a random route, create and parent every child first, then use
`clone_random_sequence_container()` with the donor's exact expected playlist
and avoid-repeat count. The API preserves the donor's node and unmodeled fields,
rebuilds only `Children` and `CAkPlayList`, and requires existing unique child
IDs with positive weights. Guard any child `DirectParentID` and positioning
changes separately. Use equal weights plus `avoid_repeat_count=0` for independent
uniform selection; with two children, an avoid-repeat value of `1` becomes
alternation after the initial choice.
