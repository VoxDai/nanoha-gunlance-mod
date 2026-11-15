# <Move and test question>

## How to Test

<Briefly describe the goal, which marker maps to each candidate, the positive
load control, the minimum test order, and when to stop. Pause candidate testing
if the load control fails. Record overlapping or unclear cues as “Uncertain”.>

Exit the game. Back up the target files and note which targets were originally
absent. Install one complete `nativePC` variant from `packages/` at a time,
disable conflicting mods, and fully restart between variants. Restore the
original backup afterward and remove only newly installed targets that were
originally absent. Keep your backup even when testing `00_baseline`.

<List target files or link the exact list in `src/README.md`.>

Example: `Trigger two; 2/2; after insertion, before the explosion; original
audio normal`. Record what you observed. Use “Not tested” for untried cases,
“0/N” for silence across N valid attempts, and “Uncertain” for unclear cues.

## Test Results

Relevant equipment/shelling type, monster/body part, and game version: Not tested

| Package | Actual action or conditions | Markers heard | Hits / valid attempts | Observed phase | Original audio or other anomalies |
|---|---|---|---|---|---|
| <Load-control package> | <Easy control action> | Not tested | Not tested | Not tested | Not tested |
| <Candidate package> | <Target action> | Not tested | Not tested | Not tested | Not tested |

Video or additional observations (optional): Not tested
