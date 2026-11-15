---
name: create-probe
description: "Create reproducible Monster Hunter: World gameplay probes under assets/analyses and analyze recordings.md to identify moves, sound triggers, timing, and routes. Use for probe packages and follow-up experiments."
---

# Create Probe

Turn a specific question into a reversible in-game experiment. Combine the
user's observations with binary evidence for the design and implementation
workflow in `mod-design`.

## Scope

- Work on the specified move, question, or feedback. Read relevant past
  packages and recordings first. Reuse an existing package when it can answer
  the question.
- Write deliverables under the matching `assets/analyses/<move>/` directory.
  Prefer inputs from `original/`. If an input is missing there, use a
  uniquely identified file from `assets/chunk/` and pin its identity. Leave
  both input trees untouched.
- Preserve delivered packages and user recordings. Use a new sequence number
  for each new round and write analysis to the matching `findings.md`.
  Leave `audio/`, `designs/`, `builders/`, `tools/`, `output/`, and
  `release/` untouched.
- The user installs the probe and records in-game observations. Report
  structural verification separately from gameplay results.

## Package Layout

```text
assets/analyses/<move>/<move>_<NN>[_description]/
├── packages/
│   ├── 00_baseline/nativePC/...
│   └── 01_motions160_163/nativePC/...
├── src/
│   ├── README.md
│   ├── build_probe.py
│   └── route evidence, input guards, markers, and verification results
├── recordings.md
└── findings.md
```

Use snake_case for the move and optional description. Number probes in
ascending order within each move directory, with at least two digits, as in
`mounted_finisher_01_control_diagnostic`. Each variant includes all companion
files required for that experiment and can be installed independently. Pin
the baseline input set explicitly. Deliver directories without ZIP archives.

## Build the Probe

1. Define the hypotheses, candidate range, and stopping condition. Inspect
   original routes with `soundbank-workflow`, the current
   `tools/soundbank_editor/README.md`, and API docstrings. Read the
   [technical workflow](references/probe-workflow.md) before editing or
   validating binaries. Verify IDs and guards against current inputs.
2. Choose the smallest useful experiment. Use media replacement to verify
   sound identity or known sharing. Isolate requests for specific Motion
   candidates when actions share an Event. Preserve unrelated audio and
   controls.
3. Use distinct spoken markers for candidates in the same package. Group
   candidates when they are numerous or may overlap. Narrow the route before
   testing phases, sharing, and negative cases. Include an easy positive load
   control in each candidate variant when feasible.
4. For one marker, use `assets/source_audio/testing/trigger.wav` if suitable.
   Generate distinct spoken Mandarin markers for multiple candidates, with a
   separate load-success phrase. Use spoken phrases throughout.

   ```sh
   conda run -n nanoha-gunlance-mod python .agents/skills/create-probe/scripts/generate_markers.py --output-dir <probe>/src/markers --count 3
   ```

   The script uses the local macOS `say` voice `Tingting` by default. Use
   `--voice` to select another installed Mandarin voice. Report missing voices
   without downloading a voice or substituting counted beeps. The script saves
   the phrases, synthesis settings, original synthesis audio, 48 kHz stereo
   16-bit WAVs, WEMs, and decode verification. Check markers for nonempty
   audio, clipping, and audibility, and link the WAV previews. Probe markers
   are exempt from final WAV naming and loudness rules. Phrase duration,
   leading silence, and inherited mixing can affect perceived timing.
5. Save the reproducible build script and route evidence under `src/`. Require
   an explicit `--output` and reject existing outputs. Build in temporary
   storage and deliver complete packages after validation. Put the file list,
   rebuild command, and verification results in `src/README.md`.
6. Fill the [recordings template](assets/recordings.md) and the
   [findings template](assets/findings.md) for this round. Keep only relevant
   rows and columns. Use the two recording sections for test instructions and
   results. Include an example, install and restore steps, and a stopping
   condition. Initialize results as “Not tested” and select only conditions
   needed to distinguish the hypotheses.
7. Link `recordings.md`, the variant packages, and marker previews. State
   which structural checks passed and which observations require a game test.

## Analyze Results and Choose the Next Round

Read the specified recordings beside the package routes, input identities,
and validation results. Cite the exact rows, packages, and original evidence
in `findings.md`. Read legacy `feedback.md` or `recording.md` when supplied.
Use `recordings.md` for new packages.

- Distinguish “Not tested”, “0/N”, and “Uncertain”. Record valid attempts,
  every marker heard, and the observed phase. Leave unspecified conditions
  unknown.
- If the load control fails or a prior positive stops reproducing, diagnose
  loading, Mod conflicts, the actual Motion branch, and package differences.
  Keep references valid during comparisons. Treat silence as inconclusive in
  these cases and avoid inferring an engine record limit.
- Limit conclusions to tested conditions. Action IDs and Motion IDs refer
  to different entities. Frame numbers from different Motions cannot establish
  absolute order. Use video timestamps to quantify timing intervals. Different
  body parts, directions, or preceding actions can select different Motions.
- Continue with the existing package, build another round, or stop and
  summarize. Choose the lowest-cost test that would change the conclusion.
- Summarize verified conditions, IDs, complete routes, timing, sharing,
  negative cases, guard evidence, and open questions. Link original evidence
  and recordings. Pass verified findings to `mod-design` for the final audio
  and behavior contract. Keep temporary probe IDs and markers within probes.
