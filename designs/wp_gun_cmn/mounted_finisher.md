---
design_id: wp_gun_cmn.mounted_finisher
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# Mounted Finisher

## Description

The Gunlance mounted finisher keeps its original sounds and plays Nanoha’s “Accelerator” once before the explosion. The back, head, and tail variants share the same voice clip, with a fresh random pitch offset.

| Name | Action or State | Expected Behavior |
| --- | --- | --- |
| Accelerator | Back, Head, Tail finisher | Plays once before explosion, pitch randomized by ±50 cents |
| Other Actions | Mounting, mid-thrust, Clutch Claw Weapon Attack, Wyrmstake Cannon | Maintain existing sound behavior |

## Audio

| Name | Audio | Loudness (LUFS-I) | Playback |
| --- | --- | ---: | --- |
| Accelerator | [Final WAV](../../audio/wp_gun_cmn/mounted_finisher/nanoha_accelerator_01%28source_audio.movie_detonation.nanoha.accelerator.1%29.wav) | −20 | Shared by three parts, appended immediately upon trigger, no extra delay |

## Implementation Contract

LMT v95 uses `original/lmt/w07_00.lmt`. Three TIML locations are at 1788784, 1863696, and 1937840, each referenced only by its corresponding Motion, with trigger masks all being 16. Request field offsets are 1792672, 1867552, and 1941728. Only one byte is modified per location, file length remains unchanged.

| Name | LMT | Motion | EventGroup | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| Back | w07_00 | 170 | EventGroup06 | E | 0 | 6550 | 6615 | 82 |
| Head | w07_00 | 171 | EventGroup06 | E | 0 | 6550 | 6615 | 82 |
| Tail | w07_00 | 172 | EventGroup06 | E | 0 | 6550 | 6615 | 82 |

WWEV v19 uses `original/wwev/hm_wp07_snd_ev.wwev`. Use `append_cloned_request()` to atomically clone records 33 and 34, each 129 bytes. Only modify the cloned ReqNo and Event ID; the original records and dependencies remain byte-for-byte consistent. When applied independently, records increase from 43 to 45; after merging, the new record sequence numbers are 51, 52.

| Name | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | New ReqNo | New Event ID |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| First Branch | hm_wp07_snd_ev | 6550 | 2925880017 | 2 | `b501ecd9ebb0baaf4ae7432ef8c25e161f372c7b298791664ad4567c1851736e` | 6615 | 496401681 |
| Second Branch | hm_wp07_snd_ev | 6550 | 1080565533 | 2 | `0ce801814a4ba5382e311df66e9611d56c9972dad36aab2690ceb5a7ad1944fb` | 6615 | 3994593461 |

NBNK v120 uses `original/nbnk/pl_wp_par_op_event_structure.nbnk` (Bank 2944223826) and `original/nbnk/wp_gun_cmn.nbnk` (Bank 939294496).

| Name | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| First Native Branch | 2925880017 | 1012787452 | 987082006 | — | — | 2248472451 | — |
| Second Native Branch | 1080565533 | 29680933 | 9236354 | — | — | 2208167511 | — |
| Accelerator | 4197115840 | — | — | 890667980 / 838569492 | Added 50 / — | 831225203 | 2739514054 |

- Original Events 2925880017 and 1080565533 each possess only one original Action from the table. Event body SHA-256 are `c9adec59ce59bd1cf3c407f2d8efa9afa051668b423459b852ffe730cface5ca`, `27390d1f2a5a2a3356cd5eee0cdbafe1d9fa9f4d734a6f8fba0f469e5a8f193b` respectively. Original Action body SHA-256 are `273437fb964544b5333f281a91f87099fdb7e6e0671e5ad786ca3c17f2a5b0b2`, `b156ed03e9878e9474778f313489e1f7c9d3ac905ba4cd8d30655e94ee780ebb` respectively.
- The Action list for the wrapped Event 496401681 is `[2248472451, 2095821896]`, calling the original first branch and voice Event in sequence. The Action list for the wrapped Event 3994593461 is `[2208167511]`, calling the original second branch. Each PlayEvent Action is serialized prior to its belonging Event. The structure Bank adds five objects, HIRC increases by 92 bytes, and original objects and BKHD are preserved as-is.
- The unique Action 831225203 of voice Event 4197115840 plays Sound 2739514054, Media ID 3650218823, and is appended to the registered build's DIDX index 50. Converted to 48 kHz, 16-bit mono Wwise PCM, with no additional gain.
- Standard voice donor comes from `original/nbnk/wp_cmn_epvsp.nbnk`, body SHA-256 is `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`. Uses C1 positioning and `original/nbnk/pl_act_vo_event.nbnk` Actor-Mixer 209038110; its body SHA-256 is `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`. Only applies Pitch random range `[-50, 50]` to the newly added Sound; Sound body is 55 bytes, SHA-256 is `5533fb6a951b52f8d554559b62ba2b564d0d9c3ba290362be40d407c591ecb91`. Appended in the order of Sound, Action, Event; HIRC increases by 100 bytes; Pitch editing counts as 8 change bytes. Retains existing DIDX order, media content, and other HIRC objects.
- Checked the Play targets and their parent chains of the original branches (987082006 → 468342192 → 972300144 → 694534885; 9236354 → 460803750 → 972300144 → 694534885); the original Bank's native Events in the project contain no Stop Actions targeting these nodes.

Game acceptance requires performing a finisher once each on the back, head, and tail, confirming that "Accelerator" plays once before each explosion with normal original sound. Compare this against mounted, mid-air thrusts, Clutch Claw Weapon Attack, and Wyrmstake Cannon to confirm that none of these play this voice line. For trigger criteria, see [Joint Probe Test Results](../../assets/analyses/mounted_finisher/mounted_finisher_11_five_routes_spoken/recordings.md).
