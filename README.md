# Nanoha Gunlance Mod

A Monster Hunter: World Gunlance mod features voice lines from *Magical Girl Lyrical NANOHA*. Watch [demo video](https://www.bilibili.com/zh-Hans/video/BV1qWsm6bEPZ/).

## Install

Download and extract the [latest release](https://github.com/VoxDai/nanoha-gunlance-mod/releases), then copy the
`nativePC/` folder into your Monster Hunter: World installation directory (usually
`Steam\steamapps\common\Monster Hunter World\`). If a `nativePC/` folder already exists, merge the folders.

To uninstall, remove the files added by this mod from `nativePC/`.

## Build from Source

Install Git LFS and Conda. After cloning the repository, run these commands to build the mod in `release/`:

```sh
git lfs install
git lfs pull
git submodule update --init --recursive
conda env create -f environment.yml
conda run -n nanoha-gunlance-mod python -m builders
```

## Developer Guide

Set up Git LFS, the Git submodule, and the Conda environment using the commands
above.

Use [WorldChunkTool](https://github.com/mhvuze/WorldChunkTool) to unpack the `chunk/*.bin` archives from your
Monster Hunter: World installation into `assets/chunk/`. Preserve the extracted
directory structure so the agent can find the vanilla NBNK sound banks, LMT
motion files, WWEV sound request tables, and EPVSP effect sound tables.

1. Choose a Gunlance move and prepare the WAV sound effect files. Tell the agent which
   actions should trigger each sound, when it should play, and whether it
   should replace or play alongside the original audio.
2. If the trigger or timing is uncertain, the agent can use `create-probe` skill
   to build a test package. Follow the in-game test instructions and send
   your observations to the agent for analysis.
3. Ask the agent to use `mod-design` skill to implement the effect by updating the
   design contract in `designs/` and the corresponding `builders/`.
4. Use `build-release` skill to validate and build the mod. Install the generated
   `release/nativePC/` and verify the triggers, timing, and mix in game.

See [AGENTS.md](AGENTS.md) and [project skills](.agents/skills) for more information.

## Credits

This is an unofficial fan mod based on Capcom's *Monster Hunter: World* and *Magical Girl Lyrical NANOHA* anime & games.

- [WorldChunkTool](https://github.com/mhvuze/WorldChunkTool) extracts vanilla
  game files from the chunk archives.
- [wwiser](https://github.com/bnnm/wwiser) inspects Wwise sound banks and
  traces HIRC playback routes.
- [MHW:IB Labelled Audio](https://docs.google.com/spreadsheets/d/10A_YEfm7KV0ATw7uD-3_o_ZOGSlGXtzWWMGXKs_neYM/edit)
  catalogs sound banks, WEM IDs, and character voice presets.
- [Modding MH:W — wwiseutil Wiki](https://github.com/hpxro7/wwiseutil/wiki/Modding-MH%3AW)
  documents NBNK, NPCK, and WEM structures and audio replacement workflows.
- [Player Weapon Action IDs](https://github.com/AniBullet/MonsterHunterWorldModding/wiki/Player-Weapon-Action-IDs)
  helps identify weapon actions when tracing game events.
