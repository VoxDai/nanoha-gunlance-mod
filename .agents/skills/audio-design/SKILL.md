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
- Never edit `builders/`, `audio/`, `docs/mapping/`, existing
  `original/` files, `output/`, or `release/`. Existing builders may be
  inspected only to find and report design-to-implementation drift.
- Never modify, move, or delete a source under `assets/chunk/`. Never
  overwrite an `original/` destination. If an existing destination differs
  from the resolved source, stop and report the conflict.
- Use mapping and research documents only as evidence. Inspect the original
  binaries before fixing IDs, guards, hashes, versions, byte counts, or routes.
- Never invent Event, Action, Container, Sound, Media, DIDX, ReqNo, frame,
  offset, record, or summary values. Preserve an existing `design_id`.
- Use only final project WAVs. Probes, placeholders, and unprocessed source
  clips do not satisfy a complete design.

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
| 名称 | 音频 | 播放方式 |
```

Record replacement versus independent append, sharing, synchronization, delay,
and distinct spatial paths. Final project WAVs may be 48 kHz stereo PCM at
16-bit or 24-bit depth. Inspect and report other formats, but do not convert
audio during this task.

### 实现契约

For every target, record its project-relative source under `original/`,
supported version, source SHA-256, and the exact editor guards. For NBNK, record
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
2. Inventory every NBNK, LMT, WWEV, and final WAV dependency. Each game binary
   must exist in its documented `original/nbnk/`, `original/lmt/`, or
   `original/wwev/` directory.
3. If a dependency is missing, locate exactly one source under
   `assets/chunk/`, copy it byte-for-byte to the correct new `original/`
   path, and verify matching SHA-256 values. Stop on absence, ambiguity, or a
   differing existing destination.
4. Inspect every original through `tools.soundbank_editor`; use
   `soundbank-workflow` and a task-specific wwiser dump under `/tmp` when
   topology needs deeper proof. Resolve LMT routes with
   `LmtFile.triggered_requests()` and the matching `WwevFile`.
5. Verify every final audio link and its metadata. Build an in-memory guarded
   prototype when exact summaries, output hashes, or collision checks cannot be
   established by inspection alone; do not publish it.
6. Create or update the design, keeping behavior, audio, and implementation
   facts in their respective sections.
7. Reparse the front matter, require a unique `design_id`, validate every
   local link and table column count, and ensure all game-artifact contract
   paths point into `original/`, never `assets/chunk/`.
8. Run `git diff --check` and report the design, promoted artifacts and
   hashes, verified route facts, unresolved blockers, and any disagreement with
   existing builders or mapping.

When the contract is complete, hand off its path or `design_id` to
`design-implement`. Do not implement or repair the builder in the same task
unless the user explicitly requests that separate stage.
