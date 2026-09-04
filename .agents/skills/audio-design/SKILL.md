---
name: audio-design
description: "Create or update specified project sound-effect designs under designs/ from intended playback behavior, verified final audio, original artifacts, routes, and guarded implementation contracts. Use before builder implementation; do not implement builders or publish releases."
---

# Audio Design

Turn the user's audible-behavior requirements into a concise, auditable
contract under `designs/`. The design is the complete input for
`design-implement`; it is documentation, not runtime configuration.

## Scope and Boundaries

- Work only on the design path or behavior selected by the user. Do not reshape
  the requested playback behavior to fit an existing builder or
  `docs/mapping/` entry.
- Unless the user explicitly expands the task, modify only the selected design
  and promote any missing dependent game artifacts from `assets/chunk/` to
  `original/` as byte-exact copies.
- Never edit `builders/`, `docs/mapping/`, existing `original/` files,
  `output/`, or `release/`. Do not edit `audio/` unless a loudness validation has failed and the user explicitly
  confirms the exact files and target LUFS-I for a separately reviewed standardization task. Existing builders may be
  inspected only to find and report design-to-implementation drift.
- Never modify, move, or delete a source under `assets/chunk/`. Never
  overwrite an `original/` destination. If an existing destination differs
  from the resolved source, stop and report the conflict.
- Use mapping and research documents only as evidence. Inspect the original
  binaries before fixing IDs, guards, structural body or record hashes,
  versions, byte counts, or routes.
- Never invent Event, Action, Container, Sound, Media, DIDX, ReqNo, frame,
  offset, record, or summary values. Preserve an existing `design_id`.
- Use only final project WAVs. Probes, placeholders, and unprocessed source
  clips do not satisfy a complete design.
- For custom character voice, read
  `references/custom-voice-sound.md` before selecting the Sound route or
  documenting media conversion.

## Standard Design Contract

Use the current
`designs/wp07_gun_epvsp_shell/wyverns_fire.md` and
`designs/wp07_gun_epvsp_shell/full_burst.md` as visual references. Designs
have exactly the following front matter and three top-level sections:

```yaml
---
design_id: <bank>.<snake_case_design>
target_artifacts:
  - sound/wwise/Windows/<artifact>
---
```

Create a new design as
`designs/<bank>/<snake_case_design>.md`. Keep the title short. Do not add a
status field, research diary, approval workflow, evidence section, or generic
builder instructions.

### 描述

State in one compact paragraph which original sounds are preserved or replaced
and which sounds are added. Follow it with exactly:

```markdown
| 名称 | 动作或状态 | 预期行为 |
```

Include every positive trigger and important negative or paired-path behavior.
Describe what the player must hear, not the implementation mechanics.

### 音频

List only final repository audio with links relative to the design file:

```markdown
| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
```

Identify each final WAV by its repository-relative link only. Do not record a
whole-file hash for an audio file in the design.

Record replacement versus independent append, sharing, synchronization, delay, and distinct spatial paths. Measure
integrated loudness read-only with FFmpeg
`loudnorm` and use its unrounded `input_i` to validate the inclusive
`[-25.00, -20.00]` LUFS-I range. Record the measured value rounded to the nearest integer in the table.

Ordinary final project WAVs must be 48 kHz, stereo, 24-bit PCM and use
`<character>_<content>_<NN>(<audio_source>).wav`: character and content are lowercase snake case, `NN` is a zero-padded
two-digit number, and the source is non-empty. A functionally necessary special audio file may violate loudness, format,
or naming requirements only when the audio section identifies it as an exception and records its purpose, actual
loudness, and actual format.

Report every loudness, format, or naming failure before changing anything. Do not rename, re-encode, or adjust a failing
file on your own. For an otherwise compliant WAV outside the loudness range, offer `-21` and `-24` LUFS-I as the
recommended targets. After the user explicitly confirms the files and target, standardize with a constant linear FFmpeg
`volume=<target-minus-input_i>dB:precision=double` gain, re-export as 48 kHz stereo `pcm_s24le`, and remeasure before
replacing the final WAV. Do not use dynamic compression, limiting, or `loudnorm` as a write filter, and do not encode
the correction in a design or builder.

### 实现契约

For every target, record its project-relative source under `original/`,
supported version, and the exact editor guards. Identify each `original/` file
by path only; do not record its whole-file hash in the design. For NBNK, record
the parsed Bank ID and use this core table:

```markdown
| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
```

Each row fixes one route. After the table, specify:

- media replacement or append behavior, ordered DIDX indices, and Media IDs;
- exact Event Action lists, original-route preservation, and serialization
  order;
- donor cloning, parent, positioning, delay, channel, Aux, sharing, random
  selection, and paired-route rules;
- allowed DIDX/DATA/HIRC changes and every byte-exact invariant;
- exact object counts, changed-byte counts, size deltas, and summary values
  proven by an existing implementation or in-memory prototype.

For every custom playback route, inspect the native Play target and its parent
Container chain for Stop Actions referenced by native Events. When a matching
native Stop route exists and the user has not explicitly requested that the
custom sound finish uninterrupted, clone each matching native Stop Action for
each custom playback root. Retarget only the clone; preserve its scope,
properties, transition, fade curve, exceptions, and unknown bytes. Add this
table inside `实现契约` only when at least one matching Stop route exists:

```markdown
| 名称 | Stop Event ID | donor Stop Action ID / target | scope | transition / fade | exceptions | 新 Stop Action ID | 新 Stop target |
```

Record the donor Action's complete body SHA-256, the Stop Event's original and
final Action lists, collision-checked clone IDs, custom root targets, and the
requirement that every cloned Action serialize before its Stop Event. If no
matching native Stop route exists, do not create a Stop Action.

New Wwise and media IDs must be explicit collision-checked unsigned 32-bit
values. Derive stable candidates with
`tools.soundbank_editor.wwise_fnv1()`, verify them against all target Media
and HIRC IDs, and record the numbers. An unresolved ID or guard blocks a final
contract unless the user explicitly asks for a non-final draft.

For animation-driven routes, add these tables inside `实现契约`:

```markdown
| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
```

Record every guard required by `LmtEditor.replace_request()` and
`WwevEditor.append_cloned_record()`, including versions, shared TIML,
duplicate request expansion, record boundaries, and byte-preservation rules.
Do not reduce a cross-format route to its final Event ID.

## Verification Workflow

1. Read the request, the selected design if it exists, both standard design
   examples, and only the mapping or research material relevant to the action.
   For custom character voice, also read
   `references/custom-voice-sound.md` before route analysis.
2. Inventory every NBNK, LMT, WWEV, and final WAV dependency. Each game binary
   must exist in its documented `original/nbnk/`, `original/lmt/`, or
   `original/wwev/` directory.
3. If a dependency is missing, locate exactly one source under
   `assets/chunk/`, copy it byte-for-byte to the correct new `original/`
   path, and verify the source and destination are byte-exact. Stop on absence,
   ambiguity, or a differing existing destination.
4. Inspect every original through `tools.soundbank_editor`; use
   `soundbank-workflow` and a task-specific wwiser dump under `/tmp` when
   topology needs deeper proof. For each custom playback route, complete the
   native Stop Action audit described above before fixing its HIRC contract.
   Resolve LMT routes with
   `LmtFile.triggered_requests()` and the matching `WwevFile`.
5. Verify every final audio link, measure its unrounded LUFS-I, and validate its format and filename. Stop and report
   ordinary WAVs outside the loudness range or media contract; document any justified special-audio exception. Build an
   in-memory guarded prototype when exact summaries, structural body or record
   hashes, or collision checks cannot be established by inspection alone; do
   not publish it.
6. Create or update the design, keeping behavior, audio, and implementation
   facts in their respective sections.
7. Reparse the front matter, require a unique `design_id`, validate every
   local link and table column count, and ensure all game-artifact contract
   paths point into `original/`, never `assets/chunk/`.
8. Run `git diff --check` and report the design, promoted artifact paths,
   verified route facts, unresolved blockers, and any disagreement with
   existing builders or mapping.

When the contract is complete, hand off its path or `design_id` to
`design-implement`. Do not implement or repair the builder in the same task
unless the user explicitly requests that separate stage.
