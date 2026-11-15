# Builder Contract

## Inspect the Contract and Existing Owners

1. Read the selected design, `builders/base.py`, `builders/__main__.py`, and the
   current plan for every `target_artifacts` entry. Read generic builder tests
   only when shared infrastructure changes, and read other designs only when
   they share a target or ID domain.
2. Parse the design front matter and require one valid, repository-unique
   `design_id` plus a non-empty list of safe nativePC-relative targets.
3. Resolve every linked final WAV and every `original/` input by its recorded
   path. Verify the recorded format version, Bank ID, DIDX/Media identities,
   route topology, structural body or record hashes, frame/slot guards, and
   expected preservation rules against the original artifacts. Do not require
   or add whole-file hashes for audio or `original/` files in the design. Use
   `soundbank-workflow` when deeper binary inspection is needed.
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
When the executable plan requires a runtime source-hash guard, derive it from
the file resolved by the design path and keep it in the builder; do not write
it back into the design.

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
- Fix the exact combined edit summary after applying every design owned by that
  artifact. Do not bypass shared-TIML, collision,
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
