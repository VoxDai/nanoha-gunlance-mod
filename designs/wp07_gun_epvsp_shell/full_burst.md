---
design_id: wp07_gun_epvsp_shell.full_burst
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# Full Burst

## Description

Full Bursts of 1–5 shells keep the original ignition sounds, explosions, and spatial routes. Each valid trigger adds one of four equally likely “Shoot” clips. Repeats are allowed, with a fresh ±50 cents random pitch offset.

| Name | Action or State | Expected Behavior |
|------|------------|----------|
| Full Burst with 1–5 shells | Actually consumes 1–5 shells | Keep the original sound and add one randomly selected “Shoot” clip. |
| Continuous Full Burst | Complete another Full Burst of any shell count | Choose a fresh clip with equal probability. The previous clip can play again. |
| Paired Spatial Path | Another spatial Event for a Full Burst with 3–5 shells | Keep the original sound on this path without duplicating the voice. |
| Other Gunlance Actions | Non-Full Burst actions | Does not play this design's "Shoot" |

## Audio

| Name | Audio | Loudness (LUFS-I) | Playback |
|------|------|----------------|----------|
| Shoot 01 | [nanoha_shoot_01](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_01(battle_of_aces.attack_voice.attack_03.1).wav>) | -21 LUFS-I | Append independent media, weight `25000` (25%); one trigger selects only one |
| Shoot 02 | [nanoha_shoot_02](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_02(gears_of_destiny.attack_voice.attack_03.1).wav>) | -21 LUFS-I | Append independent media, weight `25000` (25%); shares Container with the other three |
| Shoot 03 | [nanoha_shoot_03](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_03(movie_1st.nanoha.shoot_02.1).wav>) | -21 LUFS-I | Append independent media, weight `25000` (25%); shares Container with the other three |
| Shoot 04 | [nanoha_shoot_04](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_04(movie_1st.nanoha.shoot_03.1).wav>) | -21 LUFS-I | Append independent media, weight `25000` (25%); shares Container with the other three |

All four final WAVs are 48 kHz, stereo, 24-bit PCM, sequentially 58000/30000/54000/42000 frames
(1.208333/0.625/1.125/0.875 seconds), measured loudness is -20.99/-20.98/-21.00/-21.00 LUFS-I, true peak is
-15.76/-15.09/-13.56/-12.26 dBTP. Build-only downmix without gain to 48 kHz, 16-bit mono
Wwise PCM WEM, channel config `000001410000`; do not correct loudness during build.

## Implementation Contract

- Original Bank: `original/nbnk/wp07_gun_epvsp_shell.nbnk`, Wwise v120, Bank ID `3273965928`.

| Name | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 1 firing Full Burst | 2727643338 | 449657149 | 108007348 → 853759195 | 219848096 / 768048455 | #34 / 768048455 | 3386055930 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 2 firing Full Burst | 2727643337 | 646158903 | 58172267 → 853759195 | 46149961 / 669932693 | #30 / 669932693 | 4199321359 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 3 firing Full Burst | 1124197610 | 19077629 | 246916390 → 853759195 | 641882349 / 31902971 | #2 / 31902971 | 4100049135 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 4 firing Full Burst | 680296805 | 223369281 | 505597934 → 853759195 | 68448090 / 385933384 | #15 / 385933384 | 4272498343 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 5 firing Full Burst | 1765608260 | 403102539 | 885313651 → 853759195 | 994484287 / 272642002 | #9 / 272642002 | 3047212046 | 960803121 / 479969098 / 2544331946 / 4251385954 |

- Original media and original playback objects remain byte-exact. Shoot 01 appended as DIDX #43 / Media `242768048`; retain Wyrmstake Blast media with the same artifact owner
  DIDX #44–#46 and its order, then append Shoot 02–04 as DIDX #47 / Media `954495929`, #48 / Media `2170495128`, #49 /
  Media `2062876979`.
- Action lists for the five Events are fixed to `(449657149, 3386055930)`, `(646158903, 4199321359)`,
  `(19077629, 4100049135)`, `(223369281, 4272498343)`, `(403102539, 3047212046)`; original Actions are always the first item,
  new Actions are all Play with no delay pointing to Random `853759195`.
- Random `853759195` clones original Container `58172267`; donor is 83-byte body, SHA-256
  `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`, original playlist was
  `((46149961, 50000),)`, `avoid-repeat=1`. New playlist is fixed to
  `((960803121, 25000), (479969098, 25000), (2544331946, 25000), (4251385954, 25000))`,
  `avoid-repeat=0`; retains Random/Normal, one-shot, disables transition, resets every playback, no local Volume or instance limit settings.
- New Random body `+0x0B` parent changed from `717111903` to standard voice Actor-Mixer `209038110`; local Pitch base defaults, random range fixed to
  `(-50.0, 50.0)`. Final body is 119 bytes, SHA-256
  `6ed503ce5f4b061e412c7221932068fb105c4cb11b72e68fa4125d76ab879895`.
- Four Sounds use standard 46-byte voice templates, Sound / Media mapping is `960803121 / 242768048`,
  `479969098 / 954495929`, `2544331946 / 2170495128`, `4251385954 / 2062876979` respectively; DirectParentID are all
  `853759195`, body `+0x20` `PositioningParams.uByVector=0xC1`, no local Pitch, no second random offset overlay. Template source is
  `original/nbnk/wp_cmn_epvsp.nbnk`'s Sound `890667980` / Media
  `838569492`, original body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`; follows the project-verified
  Container voice hierarchy.
- External parent locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; this reference Bank is not included in the Mod.
- Original Bank's Stop Action only targets `60034062`, `662442083`, `1054468797`, `956375262`, `599243561`, and does not target any of the five
  Full Burst original playback roots or their parent chains; new Random does not add new Stop Actions. The paired spatial paths sent by 3–5 only append voice to the Event in the table, while the other paired Event and its
  Action list remain byte-exact.
- Serialization order is fixed as four Sounds → Random; every new Action is serialized before its corresponding Event. This design adds 4 Sounds, 1 Random, and
  5 Actions, extending 5 original Events, changed-byte count is `9`, HIRC increment is `+463`. After merging with `wyverns_fire`, media totals 49 items,
  HIRC objects `181→199`, payload `11090→11851`, changed-byte count is `14`, HIRC increment is `+761`; except for DIDX, DATA, and the aforementioned
  HIRC changes, other Bank contents remain byte-exact.
- New Media `954495929`, `2170495128`, `2062876979` and Random `853759195` are derived from
  `wwise_fnv1("nanoha_wp07_gun_epvsp_shell_full_burst_" + suffix)`'s `shoot_02_media`, `shoot_03_media`,
  `shoot_04_media`, `random_container` respectively; existing Shoot 01 Media, four Sounds, and five Action IDs remain unchanged. All IDs have completed collision checks against the original Bank's
  42 Media, 181 HIRC objects, and the Wyrmstake Cannon custom IDs with the same owner.
