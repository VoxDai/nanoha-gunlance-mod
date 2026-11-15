---
design_id: wp_gun_cmn.clutch_weapon_attack
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# Clutch Claw Weapon Attack

## Description

When the hunter is attached to a monster, the Gunlance weapon attack plays a Nanoha line once as the hunter pulls out the gunlance. Mute the two vanilla character lines after the draw and before insertion. Keep the original weapon sounds for the draw, insertion, and shot. The shot uses the shared Buster pool from the [Charged Shelling design](../wp07_gun_epvsp_shell/charged_shelling.md).

| Name | Action or State | Expected Behavior |
|------|------------|----------|
| Weapon Attack Startup | With the weapon initially drawn or sheathed, latch onto the monster and start the weapon attack | Play "Excellion" once, retain original gun draw sound, mute original character "Hmph" |
| Gun Insertion | Gun inserted into monster, before explosion | Retain two original weapon sound branches, mute original character "Hmph" before gun insertion |
| Shelling | The gunlance fires after insertion | Select and play "Buster" once from shared container with equal weight, retain original explosion sound |
| Interruption Before the Shot | The shot never triggers | Do not trigger "Buster" |
| Other Actions | Clutch Claw launch, Wyrmstake Cannon, Mounted Finisher, normal attacks, and landing | Maintain existing sound behavior |

## Audio

| Name | Audio | Loudness (LUFS-I) | Playback |
|------|------|---------------|----------|
| Nanoha "Excellion" | [nanoha_excellion_01](<../../audio/wp_gun_cmn/clutch_weapon_attack/nanoha_excellion_01(movie_reflection.nanoha.excellion_buster.1).wav>) | −24 | Add once at start, no delay, independent random Pitch ±50 cents |

## Implementation Contract

Both Banks are Wwise v120. Original inputs are `original/nbnk/wp_gun_cmn.nbnk` (Bank ID `939294496`) and `original/nbnk/pl_wp_par_op_event_structure.nbnk` (Bank ID `2944223826`).

| Name | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|------|----------|-------------|--------------|------------------------|--------------------|-------------|-----------|
| Start Original Sound Delegation | 146964709 → 3567942167 | 1061269777 | 522283251 | — | — | 1984195518 | — |
| Excellion | 146964709 → 2405966492 | — | — | 890667980 / 838569492 | #49 / — | 1423603563 → 1277608954 | 507956785 |

- The Action list for the gun draw wrapper Event `146964709` is `[1984195518,1423603563]`. Two zero-delay PlayEvents call the full original sound first, then call the voice Event `2405966492`, and are serialized before the wrapper Event. The voice Event contains only Play Action `1277608954`, serialized after Sound and Action. The two original Events for gun insertion maintain original Actions and the body object.
- Original Event / Action full body SHA-256, listed by start, gun insertion first branch, and gun insertion second branch.

| Event ID | Event SHA-256 | Action SHA-256 |
|----------|---------------|----------------|
| 3567942167 | `cdf654b3ef9e93d51971da97cc9479fcfd85ad8baaa6923f1a94bb6784844f15` | `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a` |
| 1024101668 | `9e0727fd4f80e2a0410e6b26cb44565a62194e49011716232d2e07a68c460876` | `b5a74054bd5d85178c6129c3668a6ec8f211f897e40477b17d02a7a7901ad5c8` |
| 1080565533 | `27390d1f2a5a2a3356cd5eee0cdbafe1d9fa9f4d734a6f8fba0f469e5a8f193b` | `b156ed03e9878e9474778f313489e1f7c9d3ac905ba4cd8d30655e94ee780ebb` |

- Original Play targets and parents are `522283251 → 768813060`, `186074123 → 468342192`, `9236354 → 460803750` respectively, each continuing to point to `972300144 → 694534885`. There are no Stop Actions pointing to these targets or parents in the original Bank; this design adds no new Stop. The original Wyrmstake Cannon stop chain and EPVSP branching are retained independently.
- Standard voice donor from `original/nbnk/wp_cmn_epvsp.nbnk` (Bank ID `1149256632`), original body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`. Retain template C1 positioning and Aux, DirectParentID is `209038110` (`original/nbnk/pl_act_vo_event.nbnk`, Bank ID `3755575407`, Actor-Mixer body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`). After template standardization SHA-256 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`. Only replace Sound/Media ID and add random Pitch `(-50.0, 50.0)`, no base Pitch offset. Final Sound body SHA-256 is `0b8d9f6f3c01e0f9f91234fc65954a1ec1db9f4f0c502577bd5f97dc28dfef8c`.
- Only append Media `3631037616` to #49. 48 kHz, dual-channel, 24-bit PCM WAV downmixed without gain to 48 kHz, 16-bit, mono Wwise PCM WEM, channel config `000001410000`. Original media remains byte-exact; only-append and reconstruction-required-alignment-changes for DIDX/DATA. New IDs derived from `wwise_fnv1("wp_gun_cmn_clutch_weapon_attack_" + suffix)`; checked occupancy of 4550 original NBNK and 1300 original WWEV.
- This design adds 1 Sound, 1 Action, 1 Event to the common Bank, HIRC increment `+100`, merged `+1900`, random Pitch increases changed-byte count by `8`, merged to `49`. Adds 2 Action, 1 Event to the structure Bank, HIRC increment `+57`, merged `+228`, changed-byte count is `0`. BKHD of the structure Bank is byte-exact with all original HIRC objects.

| Name | LMT | Motion | EventGroup | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| Start | `original/lmt/w07_00.lmt` | 335 | EventGroup06 | F | 0 | 6470 | 6613 | 5 |
| Character Voice after Gun Draw | `original/lmt/w07_00.lmt` | 335 | EventGroup02 | B | 0 | 1409 | 6750 | 16 |
| Character Voice before Gun Insertion | `original/lmt/w07_00.lmt` | 335 | EventGroup02 | A | 0 | 1309 | 6750 | 107 |
| Gun Insertion | `original/lmt/w07_00.lmt` | 335 | EventGroup06 | H | 0 | 6460 | Retain original value | 110 |

| Name | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | New ReqNo | New Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| Start | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6613 | 146964709 |
| First Insertion Branch | Same as above | 6460 | 1024101668 | 2 | `ee5b6bfa669cd61e9828e3dc88db75219ec5a55babe87548eabd65c159c0a52e` | — | Keep original Event |
| Second Insertion Branch | Same as above | 6460 | 1080565533 | 2 | `641f251490902f7b5e322be89c5bd4b72bfe3b5100f3a85d1ccc26563d7e8f32` | — | Keep original Event |

- LMT v95, Motion 335 total 359 frames, TIML `2913472` exclusive. F/H assignment offsets are `2915840`/`2915904`, trigger masks are `0x20`/`0x80`. Use `replace_request()` to modify F assignment, changing 1 byte. Character voice B/A assignment offsets are `2915504`/`2915472`, trigger masks are `0x02`/`0x01`, each changing 2 bytes. Clutch Claw changes 5 bytes total, 51 bytes after merging, file size remains unchanged.
- WWEV v19, original #17 fully cloned to #50 (129 bytes), only changing ReqNo and Event ID. Original #14/#15 maintain original order and byte content. 50 entries after merging, cumulative addition of 903 bytes.
- Original character voice table is `original/wwev/pl_voice.wwev` v19. Original Req1409 only has #20/mode 4/Event `967571325`, record SHA-256 is `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507`. Original Req1309 only has #18/mode 4/Event `3262711103`, record SHA-256 is `505d806915b6b08b37add31895e56e4e45faf84cc0e85883a4414873927390f9`. Both original records are preserved.
- Reuse Req6750 from [Wyrmstake Design](../wp07_gun_epvsp_shell/wyrmstake_cannon.md). Character voice table maintains 103 records after merging, with an addition of 387 bytes. #103 is the unique Req6750/mode 4/Event `2846173097`, record SHA-256 is `c44060757af7fe2b1ba1c5bc505e738d20342f68cd5754d7184283bca6432f00`. Common Bank follows the serialization order of empty Event `3938800881` → PlayEvent Action `1604422970` → wrapped Event `2846173097`, with the wrapper calling an empty Event. This mute modification only edits LMT.
- Register this design under five existing artifact owners. Cross-file verification of the two character voice reroutes and empty Event, Excellion playback, the two mode 2 original branches for insertion, as well as the absence of Buster media for the old Req6614, dedicated wrapper, voice Event, and common Bank.
- [Mute Probe](../../assets/analyses/clutch_weapon_attack/clutch_weapon_attack_11_grunt_mute/recordings.md) covers two attempts each with the weapon initially drawn and sheathed. Both "hmph" sounds are 0/2, Excellion, insertion original sounds, and Buster are normal; baseline columns were not tested. Final package acceptance covers both start states, insertion original sounds, three shell types where actual shelling only sounds once via shared Buster, interruption before shelling, and comparisons with Wyrmstake Cannon, Mounted Finisher, and Normal shelling.
