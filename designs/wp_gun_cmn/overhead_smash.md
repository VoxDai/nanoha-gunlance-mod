---
design_id: wp_gun_cmn.overhead_smash
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# Overhead Smash

## Description

The ordinary Overhead Smash and Quick Reload Overhead Smash keep all their original mechanical, metal, and swing sounds. One of two equally likely Nanoha “Accel” clips replaces the vanilla grunt in Motion 131 and
Motion 128. Repeats are allowed. A dedicated Container applies a fresh ±50 cents random pitch offset each time. The original frame 32
gets no additional voice trigger. The separate jumping variant and other character voices are outside this change.

| Name         | Action or State                                     | Expected Behavior                                                                                                  |
|--------------|------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| Normal Overhead Smash | Via Motion 131 into `WP_07::STRIKE` / Action 83 | At frame 14, replace the original grunt with one of the equally likely “Accel” clips at a ±50 cents random pitch offset. Keep the original mechanical sounds. |
| Quick Reload Overhead Smash | Motion 128's `WP_07::STRIKE_QR` / Action 84 | At frame 18, replace the original grunt with one of the equally likely “Accel” clips at a ±50 cents random pitch offset. Frame 32 still triggers only the original mechanical sounds. |
| Continuous Overhead Smash | Re-enter any target-trigger frame | Each time, a new voice and pitch offset are selected, allowing the same one to be selected consecutively; no new cooldown or instance limits |
| Original Mechanical Sounds | Motion 128 Frame 32 and subsequent normal smash route | Original Event, Container, Sound, media, and playback timing remain unchanged, with no early or duplicate trigger |
| Separate Jumping Variants | Jump Overhead Smash and Jump Quick Reload Overhead Smash | Maintains original, does not add "Accel" due to this design |
| Other Character Voices | Attacks, hits, dodges, or other actions not involving Motion 128/131 | Maintains original character voices, no global muting or replacement occurs |

## Audio

| Name     | Audio                                                                                                                                                          | Loudness (LUFS-I) | Playback                                                                                   |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------------------------|
| Accel 01 | [nanoha_accel_01](<../../audio/wp_gun_cmn/overhead_smash/nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav>) | -21 LUFS-I | Added independent media, weight `50000` (50%); the two overhead smash routes share one Random Container, only one is selected per trigger |
| Accel 02 | [nanoha_accel_02](<../../audio/wp_gun_cmn/overhead_smash/nanoha_accel_02(gears_of_destiny.attack_voice.attack_03.1+movie_2nd_as.nanoha.accel_shooter.1).wav>) | -21 LUFS-I | Added independent media, weight `50000` (50%); shares Container with 01, allows continuous repetition |

Two final WAV files unified to `-21 ±0.05 LUFS-I`, maintaining 48 kHz, stereo, 24-bit PCM, at 34000/48000 frames (0.708333/1 second) respectively. 01 retains the original files, measured.
`-21.01 LUFS-I`, `-14.65 dBTP`; after 02 is standardized via constant `-0.76 dB` linear gain, measured at `-21.02 LUFS-I`, `-12.44 dBTP`. The two routes respectively
play once without delay at Motion 131 Frame 14 and Motion 128 Frame 18, replacing original character grunts. Each time the Container generates a `[-50, +50] cents`
offset, the two sub-Sounds inherit this offset, with no local Pitch set. During build, no gain, normalization, or loudness correction is applied; only un-gained downmixing to 48 kHz, 16-bit mono Wwise
PCM WEM, channel config `000001410000`.

## Implementation Contract

- Original Bank: `original/nbnk/wp_gun_cmn.nbnk`, Wwise v120, Bank ID `939294496`.

| Name                   | Event ID   | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID            | New Sound ID             |
|------------------------|------------|--------------|--------------|------------------------|--------------------|-------------------------|-------------------------|
| Overhead Smash Mechanical Sounds (Keep Original) | 1129041389 | 948030399 | 968655714 | 959908164 / 554875117 | #13 / 554875117 | — | — |
| Character Grunts Replaced by Accel | 2866569635 | — | 1487507844 | 890667980 / 838569492 | Added #35, #44 / — | 2176868439 / 3750542142 | 1643477631 / 3476329532 |
| Mute PlayEvent Target | 971912882 | — | — | — | — | — | — |

| Name | LMT | Motion | EventGroup | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| Quick Reload Overhead Smash Character Voices | `original/lmt/w07_00.lmt` | 128 | EventGroup02 | B | 0 | 1409 | 6595 | 18 |
| Normal Overhead Smash Character Voices | `original/lmt/w07_00.lmt` | 131 | EventGroup02 | A | 0 | 1409 | 6595 | 14 |

| Name | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | New ReqNo | New Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| Both Overhead Smash Types Share Character Voice Replacement | `original/wwev/pl_voice.wwev` | 1409 | 967571325 | 4 | `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507` | 6595 | 2866569635 |

- `original/lmt/w07_00.lmt` is fixed to v95. Motion 128
  Total 199 frames, TIML `0xEF7C0` is used only by this Motion; only allows assigning ReqNo with frame 0 and offset `0xF03C0` to EventGroup02 slot B
  `1409` to `6595`, and triggering with trigger mask `0x02` at frame 18. Motion 131 total 23 frames, TIML `0xFC040` is used only by this Motion
  ; only allows assigning ReqNo `1409` with frame 0 and offset `0xFC5A0` to EventGroup02 slot A to `6595`, and triggering with trigger mask
  `0x01` at frame 14. Replacing the two ReqNo changes 2 bytes each; after merging the modifications of Motion 2 with `stationary_draw`, the file length remains unchanged, and the cumulative
  `LmtEditSummary.changed_byte_count` becomes `5`; after including the existing `wide_sweep` Motion 143 modification, it becomes `6`, and this does not increase LMT modifications.
- EventGroup06 slot F of Motion 128 must maintain its original assignment frame 0 / ReqNo `6505`, and trigger with trigger mask `0x20` at frame 32; it must not be changed to
  ReqNo `6593`. EventGroup02 slot B / frame 18 / ReqNo `1409` of Motion 151 shall also remain as-is, serving as an undiffused control route.
- `original/wwev/pl_voice.wwev` is fixed to v19. Fully clone the 20-th entry, size `129` bytes, donor
  record, replacing only ReqNo and Event ID, and appending it as the 101-th entry; the new record SHA-256 is
  `c430e117fad198b99f94187fc7ff7c3ca1140c1ae618ad306037c16d9f4a7ed6`. The original 100 entries, four dependency strings, order, and
  record boundaries must remain byte-exact. The donor ReqNo `1409` parses uniquely to mode `4` / Event `967571325`; ReqNo `6595` has been confirmed to have zero occupancy in the
  1300 WWEV and 52816 entries of `assets/chunk/`, and is locked by the collision guard of `append_cloned_record()`.
- `original/wwev/hm_wp07_snd_ev.wwev` is fixed to v19. The original record #28 / ReqNo `6505` / mode `100` /
  Event `1129041389` / full record SHA-256
  `716e10c4bb841822f8d5b178580980d654f4367e5753403474bc8b50cfb7f2c8` must remain byte-exact; this artifact only allows
  appending `stationary_draw` with ReqNo `6592` as record #44, and `wide_sweep` appending ReqNo `6596` as record #45, both remaining unchanged; this design does not append
  ReqNo `6593` or any records. After merging, it remains 45 entries, with a total append of `258` bytes.
- The Action list of the original Event `1129041389` remains `(948030399,)`, and the original routing remains Action `948030399` → Container
  `968655714` → Sound `959908164` / Media `554875117`, with DIDX #13 identity and all objects remaining byte-exact. New Event
  `2866569635`'s Action list is fixed to `(2176868439, 3750542142)`: the first Action is `PlayEvent`, target zero Action Event
  `971912882`; the second Action is a Play with no delay, target a new Random Container `1487507844`. The Action list of a silent Event must be `()`
  , and must not contain
  Media, Sound, Container, Play, or Stop routing. It has been confirmed in-game that this silent lead allows the mode `4` of `pl_voice.wwev` to route Accel, while not producing
  premature or repeated mechanical sounds; an isolated `(3750542142,)` Event will simultaneously swallow both the original character grunts and the Accel, therefore it must not be reverted to a single Action structure.
- The 13-byte body SHA-256 of the silent lead Action `2176868439` is fixed to
  `cae38dfc9dcbfac1472669624ad21db1b2354d3043423e58c5f6cb6fa72c7138`; the 8-byte body SHA-256 of the silent Event `971912882` is fixed to
  `7b80a7d5a9de0359f31a89f18cd167d2c4b8863a0b631f21a6207b3ee0e08b20`; the final Event
  `2866569635`'s 16-byte body SHA-256 is fixed to
  `c48f67dfffd2c4da82f8c01b499831978d9affcf65d83b69abfb60b2c88cdd03`. The Accel Play Action pointing to Random
  `3750542142` has an 18-byte body, and SHA-256 is `e8e1110f9c4918a32b395f1d0857e854c730816c9d4f8a511c4d597336251d82`.
  The serialization order is fixed as standard voice Sound `1643477631` → Sound `3476329532` → Random `1487507844` → Accel Play Action
  `3750542142` → silent lead Action `2176868439` → silent Event `971912882` → character voice Event
  `2866569635` → original mechanical Event `1129041389`. The old original mechanical Event's delegated Action `2557911997` must not be created; the silent lead must not reference the original mechanical sound
  Event.
- The identity and media payload of the original DIDX #1–#33 remain byte-exact; Accel 01 uses DIDX #35 / Media ID `1280643898`, and Accel 02 appends after all existing media as
  DIDX #44 / Media ID `1779645041`. The #34 of `stationary_draw`, #39–#43,
  #36 of `reload`, #37–#38 of `wide_sweep`, and their media order all remain unchanged; the two Overhead Smash routes share these two media sets.
- Random `1487507844` clones the original Container `570218704`, the 83-byte donor body SHA-256 is
  `be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427`. The original playlist is `((647150707, 50000),)`,
  avoid-repeat=`1`; the new children order is `(1643477631, 3476329532)`, and the playlist is fixed to
  `((1643477631, 50000), (3476329532, 50000))`, avoid-repeat=`0`. The parent of body `+0x0B` changed from `768813060` to
  `209038110`. Retain donor's Random/Normal, Step, one-shot, disabled transition, reset playlist every play, global, no local
  Volume, no instance limit, and other unmodeled fields; use `HircPitchSettings(None, (-50.0, 50.0))` as guard to retain its Pitch, base Pitch
  default, random range is `(-50.0, 50.0)`. Final 95-byte body SHA-256 is
  `14d8a2b8bc85006842ce55cc6be9a29941d92baee5047b3ce049baedabada0f8`.
- Both new Sounds use 46-byte standard voice body, sourced from
  `original/nbnk/wp_cmn_epvsp.nbnk`'s Sound `890667980` / Media
  `838569492` (original body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`), only replacing Sound ID, Media
  ID and parent, fixed `DirectParentID=1487507844`, body `+0x20` `PositioningParams.uByVector=0xC1`; standard template body SHA-256 is
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`. Sound / Media mappings are as follows:
  `1643477631 / 1280643898`, `3476329532 / 1779645041`; final body SHA-256 is
  `6306b71c6ddbb1d3623c0eb203d5a8cc7d9fe0a9ae3554c42c78d44ea07d1d9a`,
  `b2d63396a981e857c8a5338700a95a251a84d9b9795cab4b48fc617ce59b77ea`. Neither has local Pitch, does not stack a second random offset, and does not add to the original mechanical
  Container; follows the verified Wide Sweep Container → standard voice Sound hierarchy.
- External parent is locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; its parent `694534885`
  body SHA-256 is `e55d7200a7e2df6833bc634f2b9f8518958cd882da9f18eb5f102f3a6c884bcb`, both levels have no local Pitch. Two reference Banks
  are not included in the Mod. The two Play roots and parent chains of the original character voice Event `967571325` are
  `123580933 → 390816861 → 694534885`, `1030793858 → 753306426 → 402681221 → 694534885`; along with the standard external parent chain
  `209038110 → 694534885`, no matching Stop Action referenced by native Events was found in the original character voice Bank, target Bank, or standard Sound donor Bank,
  therefore this design does not add new Stop Actions and does not change the interruption behavior of the original sound.
- In the memory prototype, this design adds 2 Sounds, 1 Random, 2 Actions, and 2 Events to HIRC, with object `123→130` and payload `7250→7527`.
  , increment `+277`, changed-byte count is `4` (new Random parent modification), all original HIRC objects remain byte-exact. After replacing the currently registered single voice Overhead Smash contract, this net increase
  1 Sound, 1 Random, 1 media, HIRC increment `+151`; merged with current
  `stationary_draw`, `reload`, `wide_sweep`, the DIDX total is 44 items, HIRC objects `123→148`, payload `7250→8394`, cumulative
  changed-byte count is `21`, payload increment is `+1144`. This merged value uses the currently registered HIRC increment `+993`, changed-byte count `17`
  as a baseline, plus the difference of this independent prototype; Event `3476627122` is still designed to expand from 12 bytes to
  16 bytes via reload. Except for the declared DIDX/DATA, new objects, and reload Event expansion, other Bank contents remain byte-exact.
- Media `1280643898`, Sound `1643477631`, Accel Action `3750542142` and Event `2866569635` respectively reuse
  `nanoha_wp_gun_cmn_overhead_smash_accel_media`,`nanoha_wp_gun_cmn_overhead_smash_accel_sound`,
  `nanoha_wp_gun_cmn_overhead_smash_voice_action` and `nanoha_wp_gun_cmn_overhead_smash_event` stable
  `wwise_fnv1()` values. Muted leading Action `2176868439` reuses
  `nanoha_wp_gun_cmn_overhead_smash_silent_prime_action`, muted Event `971912882` reuses the
  `nanoha_pl_act_vo_event_motion131_silent_event` already verified by-game probes. New Sound `3476329532`, Media `1779645041`, Random `1487507844`
  are derived from `wwise_fnv1("nanoha_wp_gun_cmn_overhead_smash_" + suffix)`'s `accel_02_sound`, `accel_02_media`,
  `random_container` respectively; checked all `original/nbnk/` Bank, Media, HIRC IDs and currently registered custom IDs; the three are non-repetitive and have no collisions.
  End-to-end readback must
  exactly produce Motion 128 / frame 18
  and Motion 131 / frame 14 two ReqNo `6595` / mode `4` / Event `2866569635` routes, while preserving the original mechanical path of Motion 128 / frame 32 /
  ReqNo `6505` / mode `100` / Event `1129041389` and the existing Motion 2 / frame 9 / ReqNo `6592`, Motion 143 / frame
  11 / ReqNo `6596` routes, and verify both media identities, equal-weight playlists, avoid-repeat=`0`, Pitch, parents, and loading order.
- Acceptance on-device according to description table: both types of Overhead Smash only replace character grunts once at the specified frames; multiple triggers can hear two Accel sets and slight pitch changes, and the same one is allowed to appear consecutively;
  Original mechanical sounds, separate jumping variants, and other character voices remain unchanged. The new dual-voice combination has completed structural verification; playback and loading still need in-game verification after implementation.
