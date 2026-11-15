---
design_id: wp_gun_cmn.stationary_draw
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# Stationary Draw

## Description

The stationary draw with a normal attack keeps its original mechanical sound. At frame 9, it plays one of six equally weighted Raising Heart “Standby Ready” clips. Consecutive draws can select the same clip. A dedicated Container applies a fresh ±50 cents random pitch offset each time.

| Name             | Action or State                       | Expected Behavior                                              |
|------------------|----------------------------------|-------------------------------------------------------|
| Stationary Normal Attack Draw | Sheathed state, no direction input, press normal attack button | At frame 9, keep the original sound and add one randomly selected “Standby Ready” line. |
| Continuous Stationary Draw | Same character performs another stationary normal attack draw | Choose one of the six clips with equal probability and draw a fresh pitch offset. Repeats are allowed. |
| Moving Draw Attack | Press the normal attack button with directional input while the weapon is sheathed | No additional voice lines played |
| Guard Draw | Enter guard with the weapon sheathed | No additional voice lines played |
| Other Gunlance Actions | Sheathing, reloading, sharpening, or other non-target actions | No additional voice lines played |

## Audio

| Name | Audio | Loudness (LUFS-I) | Playback |
|------|------|----------------|----------|
| Standby Ready 01 (Set Up) | [raising_heart_standby_ready_01](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_01(movie_1st.raising_heart.standby_ready_set_up.1).wav>) | -24 LUFS-I | Independent media, weight 50000; six files share one random Container, only one plays each time |
| Standby Ready 02 | [raising_heart_standby_ready_02](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_02(movie_1st.raising_heart.standby_ready_01.1).wav>) | -24 LUFS-I | Independent media, weight 50000; allows continuous repetition |
| Standby Ready 03 | [raising_heart_standby_ready_03](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_03(movie_1st.raising_heart.standby_ready_02.1).wav>) | -24 LUFS-I | Independent media, weight 50000; continuous repetition allowed |
| Standby Ready 04 | [raising_heart_standby_ready_04](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_04(movie_1st.raising_heart.standby_ready_03.1).wav>) | -24 LUFS-I | Independent media, weight 50000; allows continuous repetition |
| Standby Ready 05 | [raising_heart_standby_ready_05](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_05(movie_1st.raising_heart.standby_ready_04.1).wav>) | -24 LUFS-I | Independent media, weight 50000; allows continuous repetition |
| Standby Ready 06 | [raising_heart_standby_ready_06](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_06(movie_1st.raising_heart.standby_ready_05.1).wav>) | -24 LUFS-I | Independent media, weight 50000; allows continuous repetition |

All six final WAVs have been normalized to -24 ±0.05 LUFS-I using constant linear gain, maintaining 48 kHz, stereo, 24-bit PCM, and original duration.
Measured loudness for 01–06 is `-24.01, -24.03, -23.98, -24.02, -23.99, -23.99` LUFS-I, and true peak is
`-13.02, -13.72, -13.08, -13.72, -13.50, -13.74` dBTP, with sample frame counts of `99000, 60000, 72000, 78000, 78000, 78000`.
Play starts simultaneously with the original Draw Event, with no delay; Random Container `avoid-repeat=0` selects independently each time and allows continuous repetition.
Build-only-no-gain downmix to 48 kHz, 16-bit mono Wwise PCM WEM, channel config `000001410000`, without loudness correction during build.

## Implementation Contract

- Original Bank: `original/nbnk/wp_gun_cmn.nbnk`, Wwise v120
- Bank ID: `939294496`

| Name                 | Event ID   | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|----------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| Stationary Draw (Retain Original Sound) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 267255962 | — |
| Stationary Draw (Voice 01) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 708529406 | 700212875 |
| Draw Blade in Place (Voice 02) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 708529406 | 776774097 |
| Draw Blade in Place (Voice 03) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 708529406 | 3655378684 |
| Draw Blade in Place (Voice 04) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 708529406 | 3336805367 |
| Draw Blade in Place (Voice 05) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 708529406 | 1609904242 |
| Draw Blade in Place (Voice 06) | 3567942167 | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 708529406 | 3412709805 |

| Voice | DIDX / New Media ID |
|------|--------------------|
| 01 | #34 / 863865614 |
| 02 | #39 / 3899958096 |
| 03 | #40 / 1917220401 |
| 04 | #41 / 2922118034 |
| 05 | #42 / 3798249131 |
| 06 | #43 / 3222869860 |

- The Action list of the original Event `3567942167` is fixed to `(1061269777,)`, and the full body SHA-256 of the original Action is
  `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a`; it must remain a Play without delay, targeting the original Container `522283251`.
  Original Sound `233981936` body SHA-256 is `708699420d9237c644f13919834d5f4374d67e29a94762dc1bc0b0b98e133186`.
- The Action list of the new Event `3176129810` is fixed to `(267255962, 708529406)`: the first is a PlayEvent, targeting the original full Event
  `3567942167`; the second is a Play without delay, targeting the new Random Container `847783544`. Following the sequence of six Sounds (01–06) → Random → two
  Actions → new Event → original Event, serialized to maintain the Wwise v120 loading order.
- Random clones the original Container `522283251`; the 83-byte donor body SHA-256 is
  `e47758895339f8a1e74a65b122921135b97edf7ee01ad69f5d2a388f66e1955d`; the original playlist is `((233981936, 50000),)`,
  avoid-repeat=`1`. New children and playlist are sorted by Sound ID 01–06, with weights `50000` and `avoid-repeat=0` respectively.
  The parent of body `+0x0B` is changed from `768813060` to `209038110`; retain the donor's Random/Normal, Step, one-shot, disabled transition,
  playlist reset every play, global, no local Volume, no instance limit, and other unmodeled fields;
  Local Pitch base value defaults to (0 cents), with a fixed random range of `(-50.0, 50.0)`. The final 143-byte body SHA-256 is
  `db3a22c71a5c29ad75d077c95b70a2b7f65f98b7c3940b4ba4c8fab2707a6644`.
- The identity and media payload of the original DIDX #1–#33 remain byte-exact; retain the existing voice 01's #34 and ID, and the five new media are appended as #39–#43 via 02–06.
  Overhead Smash, Shelling, and Wide Sweep occupy #35–#38; their audio and routes remain unchanged.
- Six Sounds using 46-byte standard voice body, sourced from `original/nbnk/wp_cmn_epvsp.nbnk` (Bank ID `1149256632`) Sound `890667980` /
  Media `838569492`, original body SHA-256 is `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`.
  Uses standard templates (SHA-256 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`), only replacing Sound/Media ID
  and `DirectParentID=847783544`, maintaining body `+0x20`'s `PositioningParams.uByVector=0xC1`; sub-Sounds do not set local Pitch.
  This Container → standard voice Sound hierarchy follows the voice routing confirmed by Wide.
- External parent is locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; its parent `694534885`
  body SHA-256 is `e55d7200a7e2df6833bc634f2b9f8518958cd882da9f18eb5f102f3a6c884bcb`. Both levels have no local Pitch, and the two reference Banks are not included in the Mod.
- Native playback root and parent chain are `522283251 → 768813060 → 972300144 → 694534885`; no matching Stop Action for native Event references was found in the original Bank,
  no new Stop is added, and the interruption behavior of the original sound is unchanged.
- This design independently adds 6 Sounds, 1 Random, 2 Actions, 1 Event, HIRC objects `123→133`, payload `7250→7766`,
  increment `+516`, changed-byte count `4` (parent of new Randoms). After merging with all existing designs, media totals 43 items, HIRC objects
  `123→146`, payload `7250→8234`, total increment `+984`, changed-byte count `9`. This design does not resize, delete, or modify any original HIRC
  objects; the only original object expansion after merging is still the reload Event `3476627122`'s body `12→16`. Other Bank chunks remain byte-exact.
- Event `3176129810`, Action `267255962` / `708529406`, Sound `700212875`, and Media `863865614` maintain existing stable IDs.
  New IDs use `wwise_fnv1("nanoha_wp_gun_cmn_stationary_draw_" + suffix)`: Container suffix is `random_container`,
  Sound/Media suffixes for 02–06 are `standby_ready_<NN>_sound` / `standby_ready_<NN>_media` respectively. All new IDs have passed collision checks with all original Bank
  Media/HIRC and registered custom IDs.

| Name             | LMT                                         | Motion | EventGroup   | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|------------------|---------------------------------------------|--------|--------------|------|--------|----------|----------|------------|
| In-place normal attack draw sword | `original/lmt/w07_00.lmt` | 2 | EventGroup06 | B | 0 | 6470 | 6592 | 9 |

| Name             | WWEV                                    | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | New ReqNo | New Event ID |
|------------------|-----------------------------------------|-------------|----------------|------|--------------------------------------------------------------------|----------|-------------|
| In-place normal attack draw sword | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6592 | 3176129810 |

- `original/lmt/w07_00.lmt` is fixed to v95. Motion 2 total 91
  frames, TIML `0xC6E0` is used only by this Motion; trigger slot B with trigger mask `0x02` at frame 9. Only allows changing assignment frame 0, offset
  `0xCC50` of ReqNo `6470` to `6592`, file length remains unchanged and changed-byte count is `1`.
- `original/wwev/hm_wp07_snd_ev.wwev` is fixed to v19. Full clone of the 17th
  donor record and only replace ReqNo and Event ID; append as the 44th record, increasing by `129` bytes, original 43 records, dependent strings, and order remain byte-exact.
- ReqNo `6592` maintains existing value. End-to-end readback must only produce Motion 2 / 9th frame / EventGroup06 / slot B / ReqNo `6592` / mode `2` /
  Event `3176129810` a new route, and verify full original sound delegation, one-of-six Container, Pitch, parent and media of each Sound, and loading order.
  LMT/WWEV build contract remains as-is, after merging with existing design LMT changed-byte count is `6`, WWEV total 45 records, total append `258` bytes.
