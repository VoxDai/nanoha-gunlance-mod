---
design_id: hm_cm00_epvsp.gunlance_guard
target_artifacts:
  - sound/wwise/Windows/hm_cm00_epvsp.nbnk
---

# Gunlance Guard

## Description

The shared guard Event keeps its original sounds and routes. When `pl_weapon_type` is Gunlance, it also plays one Raising
Heart “Protection” line chosen with equal probability, with a fresh `[-50, +50] cents` pitch offset. Other weapons that trigger this Event use the 10 ms
silent fallback and play no custom voice.

| Name             | Action or State                           | Expected Behavior                                    |
|------------------|--------------------------------------|---------------------------------------------|
| Gunlance Guard | A successful Gunlance block triggers the shared guard Event | Keep the original sound and choose one “Protection” clip, each with a 50% chance, at a ±50 cents random pitch offset. |
| Repeated Guard | Block again while “Protection” is playing | The active line continues without interruption or overlap. |
| Guard After Playback | Block again after the line finishes | Re-randomizes voice and pitch, allowing the same one to be selected consecutively |
| Guard With Another Weapon | Another weapon triggers the shared guard Event | Retains respective original sounds, only plays an inaudible 10 ms silence fallback |
| Non-Guard Action | The shared guard Event does not trigger | Does not play “Protection” or silence fallback |

## Audio

| Name                           | Audio                                                                                                                                | Loudness (LUFS-I)        | Playback                                            |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------|-----------------------------------------------------|
| Raising Heart “Protection 01” | [raising_heart_protection_01](<../../audio/hm_cm00_epvsp/gunlance_guard/raising_heart_protection_01(movie_1st.raising_heart.protection_01.1).wav>) | -24 LUFS-I | Independent media; weight `50000`, random with Protection 02 with equal probability; inherits Container's ±50 cents random pitch |
| Raising Heart “Protection 02” | [raising_heart_protection_02](<../../audio/hm_cm00_epvsp/gunlance_guard/raising_heart_protection_02(movie_1st.raising_heart.protection_02.1).wav>) | -24 LUFS-I | Independent media; weight `50000`, random with Protection 01 with equal probability; inherits Container's ±50 cents random pitch |
| 10 ms Silence Fallback | [silence_10ms](../../audio/silence_10ms.wav) | -∞ LUFS-I (Special Silence) | Independent media; only for the default branch of non-Gunlance or non-matching weapon values |

Both Protection clips are 48 kHz, stereo, 24-bit PCM, last 5 seconds, and measure -24 LUFS-I as listed above. The silence fallback is a functional exception to the usual
24-bit and filename requirements. It is 48 kHz, stereo, 16-bit PCM with 480 frames of zero samples and measures -∞ LUFS-I. The build downmixes all three WAVs without gain, normalization, or loudness correction to
48 kHz, 16-bit mono Wwise PCM WEM. Random Container `avoid-repeat=0`, each of the two voices has a 50% probability, allowing the same one to be selected consecutively.
Each valid playback generates a random `[-50, +50] cents` pitch offset on the Container; the two Protection Sounds inherit this offset and do not add local
Pitch attributes. Instance limit is 1, and when the limit is exceeded, Kill Newest is used. Asset file duration is kept at 5 seconds, and playback duration during runtime may vary with pitch; continuous defense
suppression is based on the actual end of the current voice playback.

## Implementation Contract

- Original Bank: `original/nbnk/hm_cm00_epvsp.nbnk`, Wwise v120
- Bank ID: `707566772`

| Name          | Event ID   | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|---------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| Protection 01 | 4072881687 | 601196071    | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 2154199438  |
| Protection 02 | 4072881687 | 601196071    | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 640829561   |
| Silence Fallback | 4072881687 | 601196071 | 368774789 | 925721864 / 676385730 | #88 / 676385730 | 4197300369 | 3060148569 |

- Original media count is 140, HIRC object count is 597, HIRC payload is 33313 bytes. The original routing remains byte-exact: Event `4072881687` → Action
  `601196071` → Switch `368774789` → Random `127521149` → Sound `925721864` → DIDX #88 / Media `676385730`. The Event only appends an
  Action `4197300369` at the end, and the Action list is fixed at `601196071, 4197300369`; the new Action delay is `30 ms`, targeting Switch `4010844647`.
- Native Play target Switch `368774789` and its parent Actor-Mixer chain `422956649` → `694534885` found no matching
  Stop Action referenced by the native Event; this routing does not add a Stop Action.
- Full body SHA-256 of donor Switch `368774789` is `a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde1358c02ab99043bb`
  , Group `3251135135` to `pl_weapon_type`, default value `3396333570`. New Switch `4010844647` contains only two children: default value
  `3396333570` → Mute Sound `3060148569`, Gunlance value `3529994682` → Protection Random `3163089818`; both node params are
  behavior flags `0`, transition flags `1`, fade-out/in `0 ms`. Other Switch packages do not enter the new route. Retain donor prefix and unmodeled attributes, only
  change the parent of body `+0x0B` from `422956649` to Actor-Mixer `209038110`, and explicitly rebuild the above topology tail.
- Protection Random `3163089818` clones donor `127521149`, the donor's full 79-byte body SHA-256 is
  `dd0dfececc9d361c76f00553fe4179e4558f9adf909199c64c0fd28e9997237f`. The original playlist guard is fixed to
  `((925721864, 50000),)`, `expected_avoid_repeat_count=1`; the new playlist is fixed to Sound `2154199438` / weight `50000` and
  Sound `640829561` / weight `50000`, Random mode remains unchanged, `avoid-repeat=0`. Dual-entry clone body is 91 bytes.
- The new Random's parent, instance limit, and Pitch must be applied together via a single guarded full body replacement: in an independent memory HircEditor,
  first change the parent of the 91-byte cloned body `+0x0B` from donor Switch `368774789` to new Switch `4010844647`, `+0x19` from `0x00`
  to `0x01` (Kill Newest), `+0x1B` from `0` to `1` (instance limit); serialize and re-parse this temporary HIRC, then call `set_pitch()`,
  using `HircPitchSettings(None, None)` as the initial guard, setting only `random_range_cents=(-50, 50)`, with base Pitch attribute remaining default.
  Replace the 91-byte cloned body in the main editor with the resulting full body via `replace_object_body()`, expected must be the full clone
  body prior to the above modifications; do not apply field patches to the same Random in the main editor before inserting the Pitch attribute.
- Random Pitch attribute `0x02` insertion results in new Random body `91→100` bytes; final read-back must be `HircPitchSettings(None, (-50, 50))`.
  Parent field remains at `+0x0B`, Kill Newest and instance limit fields moved to `+0x22` and `+0x24` respectively. Final body SHA-256 is fixed to
  `396592e4835d0108b6049e3f40c2d1e6fb66c628c52fb59da3506f49c0c4756f`; except for explicitly declared ID, parent, playlist, avoid-repeat,
  instance limit, and random Pitch, retain the donor's other attributes and unknown bytes.
- All three new Sounds use 46-byte standard voice bodies: source is Sound `original/nbnk/wp_cmn_epvsp.nbnk`
  `890667980` / Media `838569492`, original body
  SHA-256 is `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`, standard C1 body SHA-256 is
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`. Protection's two Sounds'
  `DirectParentID=3163089818`, Mute Sound's `DirectParentID=4010844647`, all three bodies' `+0x20`
  `PositioningParams.uByVector=0xC1`.
- External parent is locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer `209038110` body
  SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; this reference Bank is not included in the Mod.
- Append sequentially DIDX #141 / Media `141209263`, #142 / Media `440767416`, #143 / Media `2901559960`. All three runtime media are
  48 kHz, 16-bit mono Wwise PCM, and verified via build readback format.
- New IDs `4197300369`, `4010844647`, `3163089818`, `2154199438`, `640829561`, `3060148569`, `141209263`, `440767416`,
  `2901559960` has passed all HIRC and Media ID collision checks from the original Bank. The readback summary records Media `140→143`, HIRC object `597→603`, HIRC
  payload `33313→33743`, Event body `12→16`, changed-byte count `51`, HIRC increment `+430`. Among these, a full body
  replacement for new Random counts as 46 changed bytes, new Switch parent patch counts as 4, and Event extension counts as 1; resized objects summary still only contains
  Event `4072881687`'s `12→16`. Newly added HIRC objects are three Sounds, Random `3163089818`, Switch `4010844647`, Action
  `4197300369`; the three Sounds must be serialized before their parent Container, Random before Switch, Switch before the new Action, and the new Action before
  Event `4072881687`. All other content remains byte-exact except for DIDX, DATA, and HIRC; original HIRC objects other than the original media and the aforementioned Event remain byte-exact.
- In-game acceptance based on description table: two Protection sounds can be heard with interval triggering and random pitch variations, allowing the same one to appear consecutively; guarding again during playback does not interrupt or stack,
  random triggering resumes after actual playback ends; other weapons' guarding and non-guarding actions do not play custom voice lines.
