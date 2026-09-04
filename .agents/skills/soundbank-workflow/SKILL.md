---
name: soundbank-workflow
description: "Understand, inspect, and perform guarded standalone edits on Monster Hunter: World NBNK, LMT v95/TIML, and WWEV v19 files. Use for format structure, WEM extraction, HIRC and request routing, and verified single-artifact workflows; do not author project designs or builders or publish releases."
---

# SoundBank Workflow

This skill owns format principles, route analysis, and the workflow for reading
and making supported additions, changes, or deletions. Concrete Python calls,
API navigation, and examples belong in the
[Library README](../../../tools/soundbank_editor/README.md); exact parameters,
returns, guards, exceptions, and side effects belong in public API docstrings.
Use `tools.soundbank_editor` for format-level work.

## Format and Route Model

| Format | Responsibility | Main structures |
|---|---|---|
| NBNK | Media storage and Wwise playback graph | BKHD identity; DIDX media directory; DATA payloads; HIRC Events, Actions, Sounds, and Containers |
| LMT v95 / TIML | Animation-time request assignments and triggers | Motion headers; shared or unshared TIML; EventGroup00–10; ReqNo slots A–H; trigger masks and keyframes |
| WWEV v19 | Request-to-Event expansion | Header; four dependencies; variable-length ReqNo/mode/Event records, command data, unknown bytes, and WWPC |

For animation-driven audio, trace the complete chain:

```text
Motion / TIML assignment + trigger
  → ReqNo in an active A–H slot
  → every matching WWEV record and its mode / Event ID
  → HIRC Event → Action → Sound or Container → Sound source
  → DIDX Media ID → DATA WEM
```

Not every Event originates in an LMT. Requests can expand to multiple WWEV
records, several Motions can share TIML, and one Media ID can serve multiple
playback paths. Determine the actual affected routes before choosing an edit.

Read [format-and-troubleshooting.md](references/format-and-troubleshooting.md)
for binary layouts, preservation rules, WEM encoding, or LMT/WWEV analysis.
Read [hirc-routing-and-settings.md](references/hirc-routing-and-settings.md)
for HIRC topology, inherited node settings, custom routes, or interruption.

## Choose the Operation

| Operation | NBNK | LMT / TIML | WWEV |
|---|---|---|---|
| Query | Inspect chunks, media identities, WEMs, and HIRC routes | Inspect Motion/TIML, assignments, masks, frames, and shared timelines | Inspect dependencies and expand every record for a ReqNo |
| Add | Append media; construct or clone supported HIRC structures | Timeline or Motion insertion is not provided | Append a complete guarded donor clone with a new ReqNo and Event |
| Modify | Replace media; edit reviewed fields or supported node structures | Substitute one guarded request assignment in an unshared Motion TIML | Existing-record modification is not provided |
| Delete | General original media/object deletion is not provided | Original timeline/keyframe deletion is not provided | Original-record deletion is not provided |

Filtering children from a cloned Switch changes the new route; it does not
delete the donor, original children, or their media. A diff can report removed
objects without providing a deletion operation. Do not simulate unsupported
deletion with raw file patches. If removal is the audible intent, first clarify
the intended trigger behavior and identify a supported route change, if any.

MHW Wwise v120 is the structural authoring target. The Library has some
version-independent byte-preserving operations; their exact version checks
are documented per API. This is not evidence of compatibility with another
game/version. LMT and WWEV readers require v95 and v19 respectively. Unknown
structures are preserved or rejected instead of being guessed.

## Work from Evidence to a Verified Artifact

1. **Confirm the input.** Read the documented `original/` artifact and record
   its path and format identity. Never modify it, `assets/chunk/`, or
   reference Mod samples. Keep diagnostics and prototypes in one task-specific
   temporary directory.
2. **Query the affected graph.** Pair every 1-based DIDX index with its Media
   ID. Inspect all paths to shared media, all Motions sharing TIML, and all WWEV
   expansions. Record assignment frames separately from trigger frames, plus
   node inheritance and object serialization order.
3. **Fix the intended change and guards.** Record reviewed old values,
   complete donor bodies/records where required, affected references, and
   explicit collision-checked new IDs. Persistent guards come from reviewed
   original evidence, not from an unreviewed live target during a build.
4. **Apply the supported operation in memory.** Consult the README for
   [media APIs](../../../tools/soundbank_editor/README.md#nbnk-and-media),
   [HIRC APIs](../../../tools/soundbank_editor/README.md#hirc), or
   [LMT/WWEV APIs](../../../tools/soundbank_editor/README.md#lmt-and-wwev).
   Use object-relative guarded HIRC edits and high-level LMT/WWEV edits;
   never patch absolute file offsets. Preserve all undeclared data and create
   dependencies before attaching their new users.
5. **Verify the result and preservation.** Compare the edit summary and diff
   with the reviewed intent; build, reparse, and validate. For NBNK, also run
   wwiser and re-extract, inspect, and decode every changed WEM. For a rebuilt
   LMT/WWEV pair, resolve the routes again and compare the intended rows and
   unaffected routes. Structural checks do not verify loudness or runtime
   behavior.
6. **Write and report only the requested artifact.** Prefer in-memory results.
   Write a single artifact only when requested, to a new authorized output path
   that cannot overwrite its input. See
   [validation and writing](../../../tools/soundbank_editor/README.md#validation-and-writing)
   for the I/O contract. Report path, SHA-256, summary, and preservation checks;
   keep diagnostics in the temporary directory.
7. **Validate in a recoverable game environment.** Check positive and negative
   trigger cases, timing, loudness, channels, positioning, Stop/interruption,
   and conflicting Mods. Record what was structurally verified and what was
   actually tested in game.

## Temporary Workspace and External Tools

Run these commands from the project root, in the same shell so the temporary
directory variable remains available:

```sh
temp_dir="$(mktemp -d /tmp/soundbank-workflow.XXXXXX)"
trap 'rm -rf -- "$temp_dir"' EXIT INT TERM

conda run -n nanoha-gunlance-mod ffmpeg -version
conda run -n nanoha-gunlance-mod python -c "import pyvgmstream; print('pyvgmstream available')"
test -f tools/wwiser/wwiser.py
```

Create a HIRC dump for the selected input and inspect stable IDs:

```sh
conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py \
  -d txt -dn "$temp_dir/bank-hirc" original/nbnk/wp_gun_cmn.nbnk
rg -n -C 8 'sourceID|ulID|DirectParentID|ulChildID|idExt' \
  "$temp_dir/bank-hirc.txt"
```

After extracting the selected WEM into the temporary directory using the
README's media API, inspect and decode it. Here `22.wem` denotes the previously
verified DIDX entry, not Media ID 22:

```sh
conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py inspect \
  "$temp_dir/22.wem"
conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py decode \
  "$temp_dir/22.wem" "$temp_dir/22.wav"
```

Convert a reviewed project WAV before embedding it; `replacement.wav` is the
chosen input WAV:

```sh
conda run -n nanoha-gunlance-mod python tools/utils/wav_to_wem.py \
  replacement.wav "$temp_dir/replacement.wem"
```

## Project Handoff

- Use `audio-design` to turn verified audible behavior, final audio, original
  artifacts, routes, guards, and acceptance cases into a design contract.
- Use `design-implement` to implement a specified design in artifact builders,
  integration validators, and tests.
- Use `build-mod` to execute the registered complete Mod plan and publish
  `release/nativePC/`.

Binary analysis does not implicitly authorize editing these project layers.
