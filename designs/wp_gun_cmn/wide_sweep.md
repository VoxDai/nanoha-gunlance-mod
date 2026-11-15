---
design_id: wp_gun_cmn.wide_sweep
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# Wide Sweep

## Description

The ordinary grounded Wide Sweep keeps all its original sounds and independently plays Nanoha’s “Smasher” once at frame 11. The two clips have 70% and 30% selection probabilities. Repeats are allowed. A dedicated Container applies a fresh ±50 cents random pitch offset each time.

| Name | Action or State | Expected Behavior |
|------|------------|----------|
| Normal Wide Sweep | Enters normal ground wide sweep after an Overhead Smash or Full Burst | Synchronized with the earlier metallic sound at frame 11, randomly plays one Smasher |
| Subsequent Original Sound | Frame 27/49 of the same wide sweep | Retains metallic sounds, swing sounds, and the two conditional routes, without playing an extra Smasher |
| Original Character Voice | Motion 143's EventGroup02 | Attack voice at frame 27 remains untriggered, character voice at frame 166 remains as-is |
| Other Actions | Sheathing, drawing, reloading, Overhead Smash, aerial Wide Sweep, and wall-clinging Wide Sweep | Does not add new Smasher due to this design; existing Mod voices remain as-is |
| Continuous Wide Sweep | Re-entering the target trigger frame | Selects one voice each time, without setting new cooldowns or instance limits |

## Audio

| Name | Audio | Loudness (LUFS-I) | Playback |
|------|------|----------------|----------|
| Smasher 01 | [nanoha_smasher_01](<../../audio/wp_gun_cmn/wide_sweep/nanoha_smasher_01(gears_of_destiny.attack_voice.attack_05.1).wav>) | -21 LUFS-I | Appends independent media, weight 70000 (70%); only one selected per wide sweep |
| Smasher 02 | [nanoha_smasher_02](<../../audio/wp_gun_cmn/wide_sweep/nanoha_smasher_02(movie_2nd_as.nanoha.smasher.1).wav>) | -21 LUFS-I | Appends independent media, weight 30000 (30%); shares Container with 01 |

Both final WAVs are 48 kHz, stereo, 24-bit PCM, at 54000/72000 frames (1.125/1.5 seconds), measured at -20.99 LUFS-I, with true peak at -16.52/-14.30 dBTP. Build-only downmix to 48 kHz, 16-bit mono Wwise PCM, channel config `000001410000`; no loudness correction during build.

## Implementation Contract

- Original Bank: `original/nbnk/wp_gun_cmn.nbnk`, Wwise v120, Bank ID `939294496`.

| Name | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 11 Frame Original Sound Delegate | 2467230206 | 281299658 | 5732403 | 402899610 / 367086010 | #6 / 367086010 | 2768755612 / 3181937101 | 102041635 / 3822519236 |

- The original Event's Action list is fixed to `(281299658,)`; this Action is a Play with no delay, pointing to the original Container `5732403`. This design does not modify original sound objects. The new Event `4096779774` is fixed to Action list `(2768755612, 3181937101)`: the first is a PlayEvent delegating the full original Event `2467230206`, the second is a Play with no delay, targeting Random `3645186695`.
- The two media files are appended after the existing DIDX #34–#36 as #37 / Media `1484106982`, #38 / Media `2274559001`. The identity and media payload of the original DIDX #1–#33 remain unchanged; the existing three appended media and routes remain unchanged. Only DIDX/DATA appending to the above HIRC new objects is allowed, preserving other chunks.
- Random `3645186695` clones the original Container `570218704`, with a complete donor body SHA-256 `be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427`. The original playlist is `((647150707, 50000),)`, avoid-repeat=1; the new playlist is `((102041635, 70000), (3822519236, 30000))`, avoid-repeat=0. The parent of body `+0x0B` changes from `768813060` to `209038110`. Retains the donor's Random/Normal, one-shot, disabled transition, and no local Volume or instance limit settings; local Pitch base defaults (0 cents), random range fixed to `(-50.0, 50.0)`. Final 95-byte body SHA-256 `369e0b6264741e600b9e87a2a05034365fcaafa6ae82a19ed178d66357fc0efd`.
- The two Sounds use standard 46-byte voice templates, sourced from Sound `890667980` / Media `838569492` of `original/nbnk/wp_cmn_epvsp.nbnk`, with the original body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`. Only the Sound/Media ID, `DirectParentID=3645186695`, and the positioning vector of body `+0x20` to `0xC1` are changed; follows the confirmed 11 frame test-version Container voice hierarchy.
- Voice parent is fixed by `original/nbnk/pl_act_vo_event.nbnk` (Bank ID `3755575407`, Actor-Mixer `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`). This parent and the upper-level `694534885` have no local Pitch; the two new Sounds also have no local Pitch, and do not stack a second random offset. No matching Stop referenced by the original playback root or its parent chain was found; no new Stop is added. The two reference Banks are not included in the Mod.
- Serialization order: two Sounds → Random → Original Sound Delegate Action → Voice Play Action → New Event. This design adds 2 Sounds, 1 Random, 2 Actions, and 1 Event; HIRC increments are `+264`, changed-byte count is `4` (due to modification of the new Random's parent). Merges with all current existing Bank designs, media 38 items, HIRC objects `123→140`, payload `7250→7831`, total increment `+581`, changed-byte count `5`; the existing reload Event `3476627122` remains the only extended original object, body `12→16`.

| Name | LMT | Motion | EventGroup | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| Wide Sweep | `original/lmt/w07_00.lmt` | 143 | EventGroup06 | A | 0 | 6486 | 6596 | 11 |

| Name | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | New ReqNo | New Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| Wide Sweep | `original/wwev/hm_wp07_snd_ev.wwev` | 6486 | 2467230206 | 100 | `7acef10768c67f1bd791873f65a0c345e00c9e24c50428e4c5ad2cae4bbabbfb` | 6596 | 4096779774 |

- `original/lmt/w07_00.lmt` is v95. Motion 143 has 187 frames; TIML `0x124BE0` is used only by this Motion. Only replaces the request assignment for slot A at frame 0: recorded position `1202416`, expected trigger frame `(11.0,)`, trigger mask `0x01`, and an additional change of 1 byte. After merging with existing Motion 2, 128, and 131, the changed-byte count is `6`, with file length unchanged. All other TIML data remains as-is, including EventGroup02's ReqNo 1129 for slot A at frame 0, trigger=0 at frame 27, and ReqNo 1009 for slot B at frame 166.
- `original/wwev/hm_wp07_snd_ev.wwev` is v19. ReqNo 6486 must only parse the original record #22, mode 100, the aforementioned Event, and the full raw hash; new ReqNo/Event must be unoccupied. Use `append_cloned_record()` to fully clone as #45, only changing ReqNo and Event, retaining command, unknown, WWPC, and appending 129 bytes. The original 43 records and four dependency strings are byte-exact, so existing #44 remains unchanged, total record count 45, total appended `258` bytes. New record raw SHA-256 is `d4a45c5e6c512f1b9688decbe9ad966e606a5674b7307ad469e6a8c60a9b8637`.
- Subsequent original audio follows the original route: EventGroup06's 27 frame slot F is ReqNo 6488 → Event `2467230204`; the 49 frame slot E is ReqNo 6410, expanding in original order to mode 200's Event `252365729`/`3350794741`, with both conditional records retained. The original raw hash of ReqNo 6488 is `f1ad3a74af5e568cbf058b9fa10b4df01459042fd40e7b62989b51b0e3e957d9`; the two original raw hashes of ReqNo 6410 are `e7fd989c59feb3d3543d02dd77ac79113f435212f795ed371cafc59a042d218c` and `9f39b9a7d1443461da8e5e75d6b9d7a62b54badd488494714312df74fd2553f2` respectively. Do not append ReqNo 6597/6598 and Event `1359210849`/`2281439929`.
- All new IDs are `wwise_fnv1("nanoha_wp_gun_cmn_wide_sweep_" + suffix)`: Media and Sound use `smasher_01_media`/`smasher_02_media`/`smasher_01_sound`/`smasher_02_sound`, Container uses `random_container`, Event/Action uses `frame11_event`/`frame11_original_action`/`frame11_voice_action`. These IDs and ReqNo 6596 have passed the occupancy check of 4550 NBNK and 1300 WWEV from the original version; simultaneously, they must reject conflicts with currently registered custom IDs.
- All three existing artifact owners are registered to this design ID, with the formal seven-piece set maintaining unique ownership. Cross-file validation must parse exactly once Motion 143/EventGroup06/Slot A/11 frame/ReqNo 6596/Record #45/mode 100/Event `4096779774` within the full animation trigger table, and verify full audio delegation, Random weights and Pitch, Sound parent, media, and serialization order; retain all existing bundle validators.
