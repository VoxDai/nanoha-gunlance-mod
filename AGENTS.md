# Nanoha Gunlance Mod

This Monster Hunter: World voice mod replaces or layers Gunlance sound effects
with combat voice lines from Nanoha and Raising Heart in Magical Girl Lyrical
Nanoha. Development includes analyzing game audio events, preparing source
audio, designing sound effects, implementing builders, and validating and
publishing the complete mod.

## Workflow

1. Use `soundbank-workflow` to inspect vanilla NBNK, LMT, and WWEV files
   read-only and document events, actions, media, and routing evidence.
2. Collect and prepare the final voice assets.
3. Use `mod-design` to verify playback behavior, final audio, original
   artifacts, routes, and guards. Update the contract in `designs/` and its
   implementation in `builders/` in the same task. Verify affected artifacts
   and cross-file routes.
4. Use `build-release` to run a full dry run and publish `release/nativePC/`
   transactionally after all validation passes.
5. In a recoverable game setup, verify trigger coverage, playback timing,
   levels, spatialization, interruption behavior, and mod conflicts.

## Repository Layout

- `assets/` contains source material, extracted game data, and read-only
  test references.
    - `assets/chunk/` contains the complete vanilla data extracted from
      Monster Hunter: World. Keep it unchanged.
    - `assets/mod_samples/` contains reference mods for reverse engineering.
      Keep them unchanged.
    - `assets/source_audio/` contains voice assets from Nanoha games and
      animation. Its `testing/` directory is reserved for probes and test audio.
    - `assets/testing_mod_files/` contains historical and temporary packages
      for recoverable testing outside the official release.
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
  contracts, and acceptance criteria by player-observable move. Builders do
  not load these documents as configuration.
- `docs/` contains research and reference material.
    - `docs/mapping/` documents vanilla audio, events, and moves for research.
    - `docs/reference/` contains move and voice references.
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

## Local Development Environment

The project uses the `nanoha-gunlance-mod` Conda environment with Python 3.12.
See `environment.yml` for the full dependency list, including `ffmpeg`,
`pyvgmstream`, and testing and analysis libraries.

```sh
# Run a single command
conda run -n nanoha-gunlance-mod mycommand

# Run multiline Python
conda run -n nanoha-gunlance-mod python <<'PY'
...
PY
```

Git LFS tracks binary files such as `.nbnk`, `.wav`, `.wem`, `.lmt`, and
`.wwev`. When the sandbox makes `.git` read-only, use
`git -c filter.lfs.process= -c filter.lfs.required=false diff --check -- <paths>`
to check text files without the LFS filter. A full check requires write access.

## Project Tools

- Import the format Library with `from tools import soundbank_editor`. It
  supports lossless parsing, guarded edits, structural rebuilds, and
  read-back verification for NBNK/DIDX/DATA/HIRC, LMT v95/TIML, and WWEV v19.
- Run `conda run -n nanoha-gunlance-mod ffmpeg ...` to convert, trim, or
  extract audio and video.
- Use `tools/utils/pyvgmstream.py` to inspect WEM files and decode them to WAV.
  Pass `-h` for options.
- Use `tools/utils/wav_to_wem.py` to convert final audio to the project's
  verified 48 kHz, 16-bit, stereo Wwise PCM WEM format.
- The [wwiser](https://github.com/bnnm/wwiser) Git submodule at `tools/wwiser/`
  parses NBNK files and HIRC routes and exports structures and TXTP. Run
  `conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py <file.nbnk>`.

## References

- The community audio spreadsheet lists NBNK and NPCK uses, WEM IDs, Bank
  indices, character voice presets, and some audition notes. Verify entries
  marked `?` and IDs from older versions. [MHW:IB Labelled Audio](https://docs.google.com/spreadsheets/d/10A_YEfm7KV0ATw7uD-3_o_ZOGSlGXtzWWMGXKs_neYM/edit)
- The wwiseutil wiki describes MHW NBNK, NPCK, and WEM structures and replacement
  workflows. Use the project's wwiser for parsing. [Modding MH:W — wwiseutil Wiki](https://github.com/hpxro7/wwiseutil/wiki/Modding-MH%3AW)
- The weapon Action ID list supports move-event analysis and FSM editing.
  [Player Weapon Action IDs](https://github.com/AniBullet/MonsterHunterWorldModding/wiki/Player-Weapon-Action-IDs)
