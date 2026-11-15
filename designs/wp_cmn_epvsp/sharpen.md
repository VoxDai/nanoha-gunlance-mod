---
design_id: wp_cmn_epvsp.sharpen
target_artifacts:
  - sound/wwise/Windows/wp_cmn_epvsp.nbnk
---

# Sharpening Completion

## Description

Sharpening completion keeps its original sound and adds one Raising Heart line in sync. “Charging Completed” and “Condition Green” are equally likely, with a fresh ±50 cents random pitch offset per playback.

| Name         | Action or State             | Expected Behavior                                                       |
|--------------|------------------------|----------------------------------------------------------------|
| Sharpening Complete | Complete the entire sharpening action | Keep the original sound and play one randomly selected Raising Heart line in sync. |
| Continuous Sharpening Complete | Complete the entire sharpening action again | Re-randomize voice and pitch, allowing the same one to be selected consecutively |
| Sharpening Interrupted | Sharpening canceled or interrupted | Play neither added voice line. |
| Other General Actions | Actions other than completing sharpening | Play neither added voice line. |

## Audio

| Name                                | Audio                                                                                                                                                              | Loudness (LUFS-I) | Playback                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------|
| Raising Heart “Charging Completed” | [raising_heart_charging_completed_01](<../../audio/wp_cmn_epvsp/sharpen/raising_heart_charging_completed_01(movie_1st.raising_heart.charging_completed.1).wav>) | -24 LUFS-I | Additional independent media, weight `50000`; randomly selected with the same probability as Condition Green, etc., and inherits Container Pitch |
| Raising Heart “Condition Green” | [raising_heart_condition_green_01](<../../audio/wp_cmn_epvsp/sharpen/raising_heart_condition_green_01(movie_1st.raising_heart.condition_green.1).wav>) | -24 LUFS-I | Additional independent media, weight `50000`; randomly selected with the same probability as Charging Completed, etc., and inherits Container Pitch |

Both final WAVs are 48 kHz, stereo, 24-bit PCM, 72000 frames (1.5 seconds). Charging Completed measured at `-24.01 LUFS-I`, `-11.32 dBTP`;
Condition Green measured at `-23.99 LUFS-I`, `-13.78 dBTP` after normalization with constant `-0.67 dB` linear gain.
Play starts simultaneously with the original sharpening completion sound, no delay; Random Container's `avoid-repeat=0`, independently randomized every time and allows continuous repetition. Container's local
Pitch base value is default, random range is `[-50, +50] cents`; the two Sounds do not set local Pitch. No gain, normalization, or loudness correction during build, only downmix without gain to
48 kHz, 16-bit mono Wwise PCM WEM, channel config `000001410000`.

## Implementation Contract

- Original Bank: `original/nbnk/wp_cmn_epvsp.nbnk`, Wwise v120
- Bank ID: `1149256632`

| Name                                | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|-------------------------------------|----------|----------------|--------------|------------------------|--------------------|--------------|-------------|
| Sharpening Complete (Charging Completed) | 166276485 | 579012432 | 306760817 | 890667980 / 838569492 | #52 / 838569492 | 487645987 | 84645870 |
| Sharpening Complete (Condition Green) | 166276485 | 579012432 | 306760817 | 890667980 / 838569492 | #52 / 838569492 | 487645987 | 2168824776 |

- Existing 71 media files and payloads remain byte-exact; sequentially append Charging Completed as DIDX #72 / Media ID `2791080207`, and Condition Green as
  DIDX #73 / Media ID `2163208725`. Both runtime media must be read back as 48 kHz, 16-bit mono Wwise PCM, 72000 samples.
- Original sound playback path remains byte-exact: Action `579012432` → Random `306760817` → Sound `890667980` → DIDX #52 /
  Media `838569492`. Event's Action list is fixed to `579012432, 487645987`, original Action remains the first item; new Action `487645987` is a Play with no delay,
  target new Random Container `3800640078`, final 18-byte body SHA-256 is
  `21ca6e777442d1b1f1f0e0a57ae207aaa599e428113b4dcb50fbe45b02228f5d`.
- New Random `3800640078` clones original Container `306760817`; donor is 109-byte body, SHA-256
  `5f4b68b79ee8809c2c1f6bc8ed3dfde2e247e7c42a25e2b97b31cd58feb7fca0`, original playlist was `((890667980, 50000),)`,
  `avoid-repeat=1`, local Pitch was `HircPitchSettings(None, (-25, 25))`. New playlist is fixed to Sound `84645870` / weight `50000` and
  Sound `2168824776` / weight `50000`, `avoid-repeat=0`; retain donor's Random/Normal, one-shot, disabled transition, reset playlist
  every play, global, and other unmodeled fields.
- New Random body `+0x0B`'s parent changed from `914939451` to standard voice Actor-Mixer `209038110`; using
  `HircPitchSettings(None, (-25, 25))` as guard, only changing the random range to `(-50, 50)`, with base Pitch kept at default. Final body is 121 bytes,
  SHA-256 `30dac3ea0e65598e2b1aa56e6cdca67ad72a016908dfdec627a8f744851fcec9`.
- Both new Sounds use donor `890667980` / Media `838569492`'s 46-byte standard voice body; original body SHA-256 was
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`, standard C1 donor-ID body SHA-256 is
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`. Only replace respective Sound / Media IDs,
  `DirectParentID=3800640078`, and fix body `+0x20`'s `PositioningParams.uByVector` to `0xC1`; Charging Completed and
  Condition Green's final body SHA-256 are `5052b089e940f8b99e5b4f8091ebfa54f5e6de51fa09e4a1854a8c2f1598518e` and
  `25b4895802884802a7955c98a9357d8b9de7e29d196c40f2da2753b38fca268d`.
- External parent locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; this reference Bank is not included in the Mod.
- Native playback root and parent chain is `306760817 → 914939451 → 972300144 → 694534885`; no Stop Action was found that is referenced by a native Event and targets any object in this chain,
  therefore no new Stop routing is added.
- New IDs use `wwise_fnv1("nanoha_wp_cmn_epvsp_sharpen_" + suffix)`: Container suffix is `random_container`, Condition Green
  Media / Sound suffix are `condition_green_01_media` / `condition_green_01_sound` respectively; resulting IDs are `3800640078`,
  `2163208725`, `2168824776`. Action `487645987`, Charging Completed Sound `84645870` / Media `2791080207` maintain existing stable IDs;
  All IDs have passed collision checks against all Media and HIRC of the original Bank and currently registered custom IDs.
- Serialization order is fixed as Charging Completed Sound → Condition Green Sound → Random `3800640078` → Action `487645987` → Event
  `166276485`. Memory prototype readback summary is fixed as: media `71→73`, HIRC object `299→303`, HIRC payload `25179→25434`, incremental `+255`,
  changed-byte count `9`, Event body `12→16`; Event final body SHA-256 is
  `46edd54989cd71ac293633f9c954950476e8f2e33c01e3359fcaab913fa4ae95`. Except for DIDX / DATA appending, the four new HIRC objects mentioned above, and the target Event
  extension, other Bank chunks, original media, and original HIRC objects remain byte-exact.
- In-game acceptance based on description table: when sharpening is complete, the original sound and one random voice play synchronously; both voices can be selected, allow continuous repetition, and the pitch is re-randomized each time; sharpening interruption and other
  common actions do not play additional voices. Structure verification only proves Bank, routing, media, and Pitch contracts; final triggering, auditory perception, and random distribution must be confirmed in a recoverable game environment.
