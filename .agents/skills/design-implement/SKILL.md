---
name: design-implement
description: "Implement specified project sound-effect designs as explicit guarded NBNK, LMT, and WWEV artifact builders, bundle validators, registry entries, and tests. Use after a designs/ contract is complete; do not author designs or publish releases."
---

# Design Implement

Translate one or more user-specified documents under `designs/` into the sole
executable contracts under `builders/`. A design fixes intent; its Python plans
fix implementation. Builders never parse design documents at build time.

## Scope and Boundaries

- Require an explicit design path or `design_id`. When the request does not
  identify one unambiguously, ask for it instead of implementing every design.
- Modify only `builders/` and builder-related tests unless the user explicitly
  expands the task. Do not edit `designs/`, `audio/`, `original/`,
  `docs/mapping/`, `assets/chunk/`, `output/`, or `release/`.
- Treat the selected design as authoritative. If it lacks final audio, source
  artifacts, IDs, hashes, editor guards, target paths, or an exact behavioral
  contract, stop and report what `audio-design` must resolve.
- Never invent or silently repair a design value. Values derived by executing
  its complete guarded edit in memory, such as a combined summary or LMT/WWEV
  output SHA-256, may be calculated and fixed in the plan.
- Use `tools.soundbank_editor` guarded APIs. Never patch an absolute binary
  offset or mutate an original artifact.
- Do not run a publishing build. `build-mod` owns complete release execution.

## Inspect the Contract and Existing Owners

1. Read the selected design, `builders/base.py`, `builders/__main__.py`, the
   current plan for every `target_artifacts` entry, and the relevant builder
   tests. Read other designs only when they share a target or ID domain.
2. Parse the design front matter and require one valid, repository-unique
   `design_id` plus a non-empty list of safe nativePC-relative targets.
3. Resolve every linked final WAV and every `original/` input. Verify the
   recorded format version, source SHA-256, Bank ID, DIDX/Media identities,
   route topology, record hash, frame/slot guards, and expected preservation
   rules against the original artifacts. Use `soundbank-workflow` when deeper
   binary inspection is needed.
4. Match each target against `ModBuildPlan`. A target has exactly one artifact
   owner. Merge into that owner when it exists; create one same-artifact module
   only when it does not. Never register two plans for one target.
5. Check the selected design against every design already implemented by a
   shared owner. Preserve their IDs, media order, callback behavior, HIRC load
   order, summaries, and bundle invariants.

## Implement Artifact Plans

For every affected plan, add the design ID and keep its complete contract
explicit: project-relative source and target, source identity, ordered edits,
guarded callback, and the exact combined summary for all implemented designs.

### SoundBank

- Declare WAV-backed changes only through
  `MediaReplacement(index, expected_media_id, source_audio)` or
  `MediaAddition(expected_index, media_id, source_audio)`.
- Keep media replacement and addition out of `apply_edits()`. The callback owns
  only reviewed HIRC work and must guard object IDs, old values, donor topology,
  Event Action ordering, paired routes, positioning, delay, parents, and Aux
  behavior required by the design.
- Recompute the whole artifact's `SoundBankEditSummary` after merging a design.
  Require undeclared media and HIRC changes to remain impossible.

### LMT and WWEV

- Implement LMT requests with `LmtEditor.replace_request()` using the exact
  Motion, EventGroup, slot, assignment frame, old/new ReqNo, and trigger frames.
- Implement WWEV additions with `WwevEditor.append_cloned_record()` using the
  exact donor ReqNo, Event, mode, full record SHA-256, and new ReqNo/Event.
- Fix the exact combined edit summary and output SHA-256 after applying every
  design owned by that artifact. Do not bypass shared-TIML, collision,
  variable-record, or byte-preservation checks.

### Registry and Cross-Artifact Routes

- Register each new artifact exactly once in `builders.__main__.MOD_PLAN` and
  retain deterministic artifact order.
- A design spanning more than one target must add or update a
  `BundleValidator`. Validate the staged files and prove the intended route end
  to end, including Motion, ReqNo, Event, Action, Sound, Media, original-path
  preservation, uniqueness, and required serialization order.
- Keep validators keyed by the selected `design_id`; do not infer release
  membership from `designs/`, `original/`, or directory contents.

## Tests and Verification

Add or update tests that cover:

- plan identity, source/target guards, declared media, exact summaries, output
  hashes, registry membership, and duplicate-target rejection;
- byte-exact preservation of original media, HIRC objects, LMT fields, WWEV
  dependencies and records outside the declared edits;
- positive routing plus important negative or paired-route behavior from the
  design;
- complete bundle validation for every cross-artifact route.

Run, in order:

```sh
conda run -n nanoha-gunlance-mod python -m builders.<affected-artifact> --dry-run
conda run -n nanoha-gunlance-mod python -m unittest
conda run -n nanoha-gunlance-mod python -m builders --dry-run
git diff --check
```

Run every affected single-artifact dry-run when there is more than one. These
commands may use temporary files but must not create or replace `output/` or
`release/`.

Report the implemented design IDs, artifact owners, media declarations,
summaries and hashes, added validators, tests run, and any remaining in-game
acceptance work. If the design cannot be implemented exactly, leave it and its
builders unchanged and report the blocking contract discrepancy.
