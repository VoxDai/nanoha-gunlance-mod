---
name: audio-design
description: "Create or update this project's sound-effect design documents under designs/ from intended playback behavior, with verified audio references, original artifacts, routes, and guarded implementation contracts. Use for design documentation and byte-exact promotion of required game artifacts from assets/chunk to original/; do not use to implement builders or modify game assets."
---

# Audio Design

Turn the user's audible-behavior requirements into a concise, auditable design under `designs/`. The document fixes what
a later builder must implement; it is not runtime configuration and does not authorize implementation.

## Boundaries

- Treat the user's requested playback behavior as authoritative. Do not reshape it to match an existing builder or
  `docs/mapping/` entry.
- Unless the user explicitly expands the task, edit only the requested design document and add any missing dependent
  game artifacts to `original/` as byte-exact copies from `assets/chunk/`. Do not edit `builders/`, `docs/mapping/`,
  `audio/`, existing `original/` files, `output/`, or release artifacts.
- Never move, delete, or modify a source under `assets/chunk/`. Do not overwrite an `original/` destination; if an
  existing file differs from the resolved source, stop and report the conflict.
- Use `docs/mapping/` and other research notes as evidence only. Inspect the original artifacts before recording IDs or
  guards.
- Never invent Event, Action, Container, Sound, Media, DIDX, ReqNo, frame, version, hash, offset, or byte-count values.
  Resolve them from the original files, an already reviewed design, or an existing guarded builder.
- Preserve an existing `design_id`. Report disagreement between a design and a builder or mapping; do not silently
  change the design to make them agree.

## Standard Format

Use the current
`designs/wp07_gun_epvsp_shell/wyverns_fire.md` and
`designs/wp07_gun_epvsp_shell/full_burst.md` as visual references. All designs use the same three-section structure and
the following front matter:

```yaml
---
design_id: <bank>.<snake_case_design>
target_artifacts:
  - sound/wwise/Windows/<artifact>
---
```

Create the file as `designs/<bank>/<snake_case_design>.md`. Keep the title short. Do not add a status field, research
diary, approval workflow, evidence section, or generic implementation instructions.

### 描述

State in one compact paragraph what original sounds are preserved or replaced and what is added. Follow it with exactly
this behavior table header:

```markdown
| 名称 | 动作或状态 | 预期行为 |
```

Include positive and important negative trigger behavior without repeating the Event mechanics already fixed in the
contract.

### 音频

List only final project audio used by the design. Use repository-relative links from the design file and exactly this
table header:

```markdown
| 名称 | 音频 | 播放方式 |
```

Record whether each file replaces media, is appended independently, is shared by routes, starts synchronously, has a
delay, or uses distinct spatial paths. Do not substitute source clips, probes, or placeholders for final audio.

Final project WAV files may use 48 kHz, stereo PCM at either 16-bit or 24-bit depth. Treat both bit depths as accepted;
do not report 24-bit PCM as a format mismatch or convert it during a design-document task.

### 实现契约

For an NBNK design, first record the original Bank path and parsed Bank ID, then use exactly this core route table
header:

```markdown
| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
```

Each row represents one route a builder must guard. After the table, fix in a few bullets:

- media replacement or append behavior, including new DIDX and Media IDs;
- expected Event Action lists and ordering;
- donor cloning, positioning, delay, channel, sharing, and paired-route rules;
- exact allowed DIDX/DATA/HIRC changes and all byte-exact invariants;
- expected object counts, changed-byte counts, and payload deltas when they have been verified by an existing
  implementation or an in-memory prototype.

Use explicit collision-checked unsigned 32-bit IDs for new Wwise objects and media. Preserve reviewed IDs. If new IDs
are needed, derive stable candidates with `tools.soundbank_editor.wwise_fnv1()` from descriptive project-local names,
verify them against all Media and HIRC IDs in the target Bank, and record the numbers. Leave `待分配` only when the user
explicitly asks for a non-final draft; otherwise an unresolved ID blocks fixing the contract.

When the audible behavior also requires an LMT/WWEV route change, keep the same three top-level sections and add the
relevant compact tables inside
`实现契约` after the NBNK route table:

```markdown
| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
```

Record the supported file versions and every guard required by
`LmtEditor.replace_request()` or `WwevEditor.append_cloned_record()`. Include shared-TIML behavior and duplicate request
expansion when relevant. Do not reduce an animation route to only its final Event ID.

## Verification Workflow

1. Read the user's request, the existing target design if present, both standard design documents, and only the mapping
   or research files relevant to the affected action.
2. Inventory every game artifact the design depends on, including `.nbnk`, `.lmt`, `.wwev`, and any other binary that
   must be parsed or changed by the eventual implementation. Each dependency must exist under the project-documented
   type directory in `original/` (`original/nbnk/`, `original/lmt/`, or `original/wwev/` for those three formats). If a
   dependency is missing, locate one unambiguous source under `assets/chunk/`, create the required subdirectory, copy
   it byte-for-byte, and verify matching SHA-256 digests. Stop if the source is missing or ambiguous, or if the
   destination exists with different bytes. Keep `assets/chunk/` unchanged and record only `original/` paths in the
   design contract.
3. Resolve and inspect every target artifact from `original/`. Use
   `tools.soundbank_editor` for lossless, read-only parsing; use a wwiser text dump in a task-specific `/tmp` directory
   when HIRC topology cannot be proven from the library alone. For LMT/WWEV, use `LmtFile.triggered_requests()` and
   `WwevFile` to verify the full route.
4. Check final audio links exist. Inspect audio metadata and report any mismatch from the project's accepted 48 kHz,
   stereo, 16-bit or 24-bit PCM WAV formats; do not convert the audio during a design-document task.
5. Create or update the document. Keep prose compact and place implementation facts in the contract rather than
   duplicating them across sections.
6. Reparse the front matter, ensure `design_id` is unique, verify every local Markdown link and table column count,
   confirm that every recorded game-artifact path exists under `original/` and no contract path points into
   `assets/chunk/`, then run `git diff --check`.
7. Report the changed design, any artifacts copied into `original/` with their SHA-256 digests, verified route facts,
   unresolved blockers, and any known design-to-builder or design-to-mapping disagreement.

If the repository evidence cannot identify a route or guard unambiguously, stop and ask for the missing design decision
instead of publishing a false contract.
