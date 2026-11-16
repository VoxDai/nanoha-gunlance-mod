# Probe Technical Workflow

Read this when building or validating binary packages. Use it alongside
`soundbank-workflow`. Follow the current Library README and API docstrings
and verify IDs, offsets, and guards against current inputs.

## Inputs and Route Evidence

In `src`, pin each source path, nativePC target, format version, Bank ID,
and complete input SHA-256. Identify the audio and route data used. Label
vanilla and existing Mod baselines explicitly. Use only pinned, selected
inputs for an existing Mod diagnosis.

For animation routes, trace Motion → TIML assignment and trigger frames and
slot → ReqNo → all WWEV modes, records, and Events → Action → Container or
Sound → DIDX index and Media ID → WEM. Record shared TIML, shared media,
and all WWEV expansions. Attribute a Motion only when the Event has an LMT
route.

## Choose Edits

- Media replacement affects every consumer. Verify and document the scope.
  A positive shared-media result alone cannot identify a specific Motion.
- For Motion isolation, use `LmtEditor.replace_request()` with guards for
  Motion, EventGroup, slot, assignment frame, old ReqNo, and every trigger
  frame. Respect shared TIML protections and use guarded APIs throughout.
- Use `WwevEditor.append_cloned_request()` or the current equivalent guarded
  API to clone every donor record. Pin count, order, mode, and complete record
  hashes. Preserve each original Event in its wrapper. Attach a single
  logical cue to one wrapper by default to avoid repeated playback.
- Use public guarded HIRC APIs. Pin donor bodies, old values, and every
  reference. Serialize dependencies before their users. Each Action has one
  owning Event per Bank. A shared Sound can have multiple Actions. Check new
  IDs and ReqNos for collisions in affected Banks, request tables, and
  Motions, and record the search scope.
- For cross-Bank PlayEvent, verify target uniqueness and type, Action
  ownership, and serialization across the final set of companion Banks. Use
  the Library-supported handling for structural Banks without media.
- For an explicit interruption test, use a long marker and check native Stop
  routes, scope, GameObject, fades, and inherited properties. A short marker
  cannot establish the interruption behavior of a longer line.

## Build and Validate

Each `src/build_probe.py --output <new-directory>` invocation must rebuild
complete packages from pinned inputs and reject existing output. Build and
validate in temporary storage before delivering. Deliver only complete
variants and leave game installation to the user.

- Save input guards, collision checks, declared edit summaries, target paths,
  and output hashes.
- Read back every artifact. Trace the full target route and compare
  undeclared LMT routes, original WWEV records, original objects and media,
  and unrelated chunks. List intentional changes separately.
- Run wwiser parsing on every modified Bank. Extract every new or replaced
  WEM and inspect and decode it with the project's pyvgmstream tooling.
  Verify sample rate, channels, duration, and agreement with the source PCM
  used for conversion.
- Check all required variant files and cross-file references. Include only
  immutable build inputs and outputs in hashed manifests.
- Compare package contents from an independent rebuild to detect dependencies
  on prior variants, temporary paths, or the game installation.

Put concise install and restore instructions in the recording document.
Have the tester quit the game, back up targets, record absent targets, switch
one complete variant at a time, disable conflicting mods, and restart. Restore
the original backup after testing and remove only targets newly added by the
probe. Preserve the rest of nativePC.

## Examples

- Mounted finisher candidates. Use separate spoken cues for candidate
  Motions in one package and a distinct load-control cue. Observe actual
  head, back, or tail placement and phase before mapping any body part.
  Test other branches after a positive when needed.
- Wyrmstake opener. With the same preceding action, compare when the cue is
  heard relative to lifting the gunlance, insertion, and release. Distinguish
  direction, hit or miss, and resource state. Report the earliest route
  verified under those conditions.
- Failed control. Pause phase scanning and retry the previous complete
  positive package. Then vary one file set based on the results. A working
  load control establishes loading only. If the previous positive also
  fails, keep the cause open until evidence identifies the affected file.

## External Reference

[Player Weapon Action IDs](https://github.com/AniBullet/MonsterHunterWorldModding/wiki/Player-Weapon-Action-IDs)
helps identify weapon actions when tracing move events or reading FSM data.
Verify candidate Motion IDs and sound requests against the vanilla files.
