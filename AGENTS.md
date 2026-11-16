# Nanoha Gunlance Mod

This Monster Hunter: World voice mod replaces or layers Gunlance sound effects
with combat voice lines from Nanoha and Raising Heart in Magical Girl Lyrical
Nanoha. Development includes analyzing game audio events, preparing source
audio, designing sound effects, implementing builders, and validating and
publishing the complete mod.

## Workflow

1. Map the user's request and WAV files to the affected Gunlance move,
   triggers, playback timing, and sounds to replace or layer. Read the
   relevant designs and builders. Use `soundbank-workflow` to trace the
   playback route without modifying vanilla files.
2. Use `create-probe` when the trigger or timing requires in-game evidence.
   Build a focused test package and specify what the user should test and
   record. Analyze their observations against the route evidence and carry
   the findings into the design.
3. Use `mod-design` to verify the WAVs, pinned originals, routes, and guards.
   Update the contract in `designs/` and its implementation in `builders/`
   together, including any affected cross-file validators. Run the affected
   artifact dry runs, unit tests, and full mod dry run.
4. Use `build-release` to validate and publish `release/nativePC/` when
   requested. Report the build results and give the user specific triggers,
   timing, and sound mix checks to verify in game.

## Repository Layout

- `assets/` contains source material, extracted game data, and read-only
  test references.
    - `assets/chunk/` contains the complete vanilla data extracted from
      Monster Hunter: World. Keep it unchanged.
    - `assets/source_audio/` contains voice assets from Nanoha games and
      animation. Its `testing/` directory is reserved for probes and test audio.
- `audio/` contains final project WAVs used by designs, organized by target
  artifact and move.
- `builders/` contains the executable build contracts.
    - `SoundBankBuildPlan`, `LmtBuildPlan`, and `WwevBuildPlan` explicitly
      declare design IDs, sources, nativePC targets, original hashes, media
      indices and IDs, guarded callbacks, and exact summaries.
    - `ModBuildPlan` explicitly registers all release artifacts and cross-file
      validators. It does not infer membership from directories or documents.
    - `builders/base.py` handles temporary builds, deep validation, and
      transactional publication of the entire tree with rollback.
- `designs/` documents trigger coverage, sound layers, implementation
  contracts, and acceptance criteria by player-observable move.
- `docs/` contains research and reference material.
- `original/` contains verified, pinned vanilla inputs for designs and
  builders. Keep these files immutable.
    - `original/nbnk/` contains vanilla NBNK SoundBanks.
    - `original/lmt/` contains vanilla LMT Motion files.
    - `original/wwev/` contains vanilla WWEV request tables.
    - `original/audio_files/<SoundBank>/{wav,wem}/` contains extracted vanilla
      media organized by SoundBank.
- `output/` contains explicitly requested single-artifact diagnostic output.
- `release/` contains the complete mod tree published transactionally by
  `build-release`. Publish the whole tree through the builder.
- `tools/` contains the format Library, audio converters, and third-party
  analysis tools.

## Environment and Tools

- Use the `nanoha-gunlance-mod` Conda environment with `ffmpeg`,
  `pyvgmstream`, and testing and analysis libraries.
- Git LFS tracks binary files such as `.nbnk`, `.wav`, `.wem`, `.lmt`, and
  `.wwev`.
