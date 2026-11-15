---
name: mod-design
description: "Create or update Nanoha Gunlance Mod sound effects by changing the design contract and guarded artifact builders together. Also use to implement or repair builders for an existing complete design."
---

# Mod Design

Deliver the selected playback behavior through a contract in `designs/` and
its executable implementation in `builders/` in the same task. Builders
declare their plans explicitly and never parse design Markdown at runtime.

## Scope

- Work on the selected action, behavior, design path, or `design_id`. Ask
  which design to use if a repair request has several plausible matches.
  Preserve existing design IDs and the playback requirements.
- For a request limited to implementing or repairing a builder against a
  complete existing design, edit the affected builders. If the contract
  conflicts with verified inputs or lacks required values, report the exact
  discrepancy so the design and implementation can be corrected together.
- Use existing final audio and immutable originals. Missing originals may be
  promoted from a uniquely resolved `assets/chunk/` source by byte-exact copy.
  Leave `assets/chunk/`, existing `original/` files, and `docs/mapping/`
  untouched. Keep generated test artifacts in temporary storage.
- Leave final WAVs unchanged unless the user explicitly confirms the files and
  loudness target for a separate standardization step described in the design
  reference. Report all loudness, format, and naming failures before editing.
- `build-release` owns release publication. Use dry-runs here and keep
  `output/` and `release/` untouched.

## Workflow

1. Read the selected design if it exists and the [design contract](references/design-contract.md).
   Read the two examples listed there and the relevant research. For custom
   character voice, read [custom voice sound](references/custom-voice-sound.md)
   before selecting the Sound route or documenting conversion.
2. Inventory original NBNK, LMT, and WWEV inputs and verify every final WAV.
   Resolve missing originals uniquely and verify byte equality on promotion.
   Report missing or ambiguous sources, or an existing original that differs
   from the resolved source. Inspect binaries directly with
   `tools.soundbank_editor`. Use `soundbank-workflow` and temporary wwiser
   dumps for deeper topology checks. For animation-driven routes, resolve
   `LmtFile.triggered_requests()` through the matching `WwevFile`.
3. Establish complete positive and negative playback behavior, native Stop
   behavior, full routes, collision-checked IDs, and editor guards. Use an
   in-memory guarded prototype when needed to establish exact structural
   hashes or summaries. Report blockers before editing when evidence is
   insufficient. Keep a requested non-final draft explicitly provisional and
   out of the registered build.
4. Update the design and the affected artifact owners together using the
   [builder contract](references/builder-contract.md). Preserve the other
   designs sharing each owner. Add or update the bundle validator for a
   multi-artifact design. If the paired update cannot be finished, leave the
   affected design and its builders at their pre-task state and report the
   blocker. Preserve any pre-existing user edits.
5. Verify the design front matter, unique `design_id`, safe target paths,
   local links, table column counts, and original-artifact paths. Reconcile
   the design with the builder declarations, guarded callbacks, exact
   summaries, and staged route validators.

## Verification

Update tests only for changed shared builder or editor behavior, using
synthetic fixtures. Artifact summaries, callback guards, bundle validators,
and dry-runs cover specific designs.

Run the following in order. Run the first command for every affected artifact
owner.

```sh
conda run -n nanoha-gunlance-mod python -m builders.<affected-artifact> --dry-run
conda run -n nanoha-gunlance-mod python -m unittest
conda run -n nanoha-gunlance-mod python -m builders --dry-run
git diff --check
```

Report the design IDs and paths, artifact owners, any promoted originals,
verified routes and guards, media changes, exact summaries, validators,
verification results, and remaining in-game acceptance work.
