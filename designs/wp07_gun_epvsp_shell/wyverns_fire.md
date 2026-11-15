---
design_id: wp07_gun_epvsp_shell.wyverns_fire
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
  - sound/pl/hm_wp07_epvsp_snd_ev.wwev
  - wp/gun/sound/hm_wp07.epvsp
---

# Wyvern's Fire

## Description

Wyvern’s Fire keeps its original charge and blast sounds. Charging adds one line each from the Nanoha and Raising Heart pools. Firing adds one line from Nanoha’s Breaker pool. Each pool selects with equal probability and allows repeats, with a fresh ±50 cents random pitch offset per playback.

| Name | Action or State | Expected Behavior |
|---|---|---|
| Container 1 | Wyvern's Fire starts charging | Choose one of three equally weighted Nanoha “Starlight” clips. Play it after a 0 ms delay. |
| Container 2 | Wyvern's Fire starts charging | Choose one of two equally weighted Raising Heart “Starlight Breaker” clips. Draw a fresh delay of 0–50 ms. |
| Container 3 | Wyvern's Fire firing | Choose one of three equally weighted Nanoha “Breaker” clips. Play it once on the right-side firing path. |
| Charging stops | Normal firing, cancellation, or interruption by hit | Two sets of charging voice lines fade out with the original Stop; no Breaker when not fired, and voice lines waiting for delay should not play after interruption |
| Other actions | Clutch Claw Weapon Attack, Mounted Finisher, ordinary shelling, etc. | Retain original sounds, do not play the additional voice lines of this design |

## Audio

| Name | Audio | Loudness (LUFS-I) | Playback |
|---|---|---:|---|
| Nanoha Starlight 01 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav>) | −21 | Additional, Container 1 |
| Nanoha Starlight 02 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_02(battle_of_aces.attack_voice.attack_01.1).wav>) | −21 | Additional, Container 1 |
| Nanoha Starlight 03 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_03(movie_1st.nanoha.starlight_breaker.1).wav>) | −23 | Additional, Container 1 |
| Raising Heart Starlight Breaker 01 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_01(movie_1st.raising_heart.starlight_breaker.1).wav>) | −24 | Additional, Container 2 |
| Raising Heart Starlight Breaker 02 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_02(movie_2nd_as.raising_heart.starlight_breaker.1).wav>) | −24 | Additional, Container 2 |
| Nanoha Breaker 01 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav>) | −21 | Additional, Container 3 |
| Nanoha Breaker 02 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_02(battle_of_aces.attack_voice.attack_01.2).wav>) | −21 | Additional, Container 3 |
| Nanoha Breaker 03 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_03(movie_1st.nanoha.starlight_breaker.2).wav>) | −23 | Additional, Container 3 |

Re-measure in order according to the table as −21.00, −21.00, −23.17, −23.98, −24.00, −20.98, −21.02, −22.69 LUFS-I. The three materials approved for adjustment only apply fixed gains (Starlight 02 −3.03 dB, Breaker 02 −3.92 dB, Raising Heart 02 +1.22 dB). Sources are all 48 kHz, stereo, 24-bit PCM; build-down without gain is 48 kHz, mono, 16-bit Wwise PCM WEM, channel config `000001410000`.

## Implementation Contract

- `original/epvsp/hm_wp07.epvsp`: ESP v8, Iceborne mark `0x18091001`, WWCT path hash type `0x45185BED`, path `wp\gun\sound\hm_wp07_epvsp_snd_ct`, 101 requests, 0 TriggerData. Only modify line 0 `(0,26501,26502,2000,0)` → `(0,26690,26502,2000,0)`, other records, stop requests, file sizes, and headers remain unchanged. Element 2020 line `(0,26501,26502,2020,0)` remains as is.
- `original/wwev/hm_wp07_epvsp_snd_ev.wwev`: v19, full clone of the 1-th Req26501 with 129 bytes (mode −1, Event302768804, record SHA-256 `9fea5c28772ab6bc99423844a29926803733ac708639e15eb16d0de280c1da89`), as the 27-th Req26690 → Event281273126. Only replace ReqNo and Event ID; original 26 records and dependencies are preserved. Req26502 → Event461444626 remains unchanged.
- `original/nbnk/wp07_gun_epvsp_shell.nbnk`: Wwise v120, Bank ID `3273965928`. Original charging Event and left-side shelling Event bytes remain unchanged; right-side retains original Action and appends Container 3.

| Name | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|---|---:|---:|---:|---|---|---:|---|
| Original charging | 302768804 | 51759545 | 60034062 | 990545535 / 477887770 | #23 / 477887770 | — | — |
| Original sound call for private charging wrapper | 281273126 | — | — | — | — | 3388979775 | — |
| Container 1 | 281273126 | — | 3610379736 | Standard Voice Body | Added #44, 54, 55 | 4011774951 | 4149261730, 2849114849, 1620588112 |
| Container 2 | 281273126 | — | 3391377780 | Standard Voice Body | Added #45, 56 | 254514827 | 36215958, 1229173909 |
| Container 3 | 3655102100 | 648832766 | 362366644 | 269350169 / 401136332 (Original Shell) | #19 / 401136332 Retained; Added #46, 57, 58 | 1866468495 | 2472459210, 3984040149, 3346634804 |

| Added DIDX | Media ID | Sound |
|---:|---:|---|
| 44 | 322318543 | Starlight 01 |
| 45 | 3332910283 | Raising Heart 01 |
| 46 | 2217266443 | Breaker 01 |
| 54 | 2014220448 | Starlight 02 |
| 55 | 3735305437 | Starlight 03 |
| 56 | 941385580 | Raising Heart 02 |
| 57 | 3696251564 | Breaker 02 |
| 58 | 631532425 | Breaker 03 |

- Actions for Event281273126 are `3388979775, 4011774951, 254514827`; the first item PlayEvent calls the full original Event302768804. The original Event302768804 still only has `51759545`, so 2020 does not trigger the newly added voice. The right-side Event3655102100 is `648832766, 1866468495`; the left-side Event3253425110 still only has `120830402`. Each new Action belongs to only one Event, with a serialization order of sub-Sound, Container, Play Action, and its parent Event.
- Three container clones `58172267`: original SHA-256 `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`, original playlist `[(46149961,50000)]`, original avoid-repeat=1. Retain Normal Random, single-play selection, non-continuous mode, replace sub-lists by table order, weights all 50000, avoid-repeat changed to 0. Direct parent changed from 717111903 to 209038110; container Pitch base default, random range `[-50.0,50.0]` cents. The three final container bodies SHA-256 in order are:
  - `1e448d3da356472e8305b9247cb8518aa7292ce67b40150bdcae96cfe7f69c8c`
  - `4e837dd3701b18dd8d4113ada5535974e0a6e9ca60a09605f451ef652df8b610`
  - `1a6016233c7c433dba061964d783e44889891ff67394984189773a35cdc0e263`
- Sub-Sounds use 46 byte standard voice bodies: Sound890667980 / Media838569492 of `original/nbnk/wp_cmn_epvsp.nbnk`, original body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`. Retain standard voice positioning `0xC1` and mixing settings; each Sound only changes its own ID, Media ID, and the corresponding container's DirectParentID. The container's external parent is locked to Actor-Mixer209038110 in `original/nbnk/pl_act_vo_event.nbnk` (Bank3755575407, body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`); this reference Bank is not included in the Mod.
- Container 1 and 3 do not write delay properties. Container 2's Play Action254514827 writes DelayTime (0x0F) with a base of 0 ms and a range offset of `[0,50]` ms. Sound selection, container pitch, and Action delay are configured separately; no delay is added in the WAV files.

| Name | Stop Event ID | donor Stop Action ID / target | scope | transition / fade | exceptions | New Stop Action ID | New Stop Target |
|---|---:|---|---|---|---|---:|---:|
| Container 1 Stop | 461444626 | 743936681 / 60034062 | Game Object | 200 ms / Linear | Empty | 2987046856 | 3610379736 |
| Container 2 Stop | 461444626 | 743936681 / 60034062 | Game Object | 200 ms / Linear | Empty | 3645807405 | 3391377780 |

Stop donor body SHA-256 to `137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd`. Only modify the cloned Action ID and target, retaining all other properties; the two clones are serialized before the Stop Event; Event461444626 is expanded from `743936681` to `743936681, 2987046856, 3645807405`. Do not add new Motion107 start points or Motion108 stop sounds.

This design adds 8 Sounds, 3 Containers, 6 Actions, and 1 Event. Original objects only adjust the native Stop Event and the right-side Shelling Event's Action lists (12→20, 12→16 bytes); a single design's HIRC changed-byte count is 15, with a payload increment of +926. After merging the full shell Bank, media #43–58 is added; original media and other designs keep their existing indices; HIRC changed-byte count is 42, with a payload increment of +2093. All other chunk bytes remain unchanged except for the declared DIDX, DATA, and HIRC changes.

Test with official assets for normal firing, interrupted firing, and Clutch Claw negative cases. Specifically check interruptions when Container 2 has not yet started playing: no sound should be filled in after an interruption. The probe's native stop results do not replace runtime verification of actual containers and random delays.
