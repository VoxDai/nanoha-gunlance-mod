---
design_id: pl_prop_cmn.clutch_claw_launch
target_artifacts:
  - sound/wwise/Windows/pl_prop_cmn.nbnk
---

# Clutch Claw Launch

## Description

The original rope tension sound plays when the claw is fired toward a Wedge Beetle, Wingdrake, or monster. Each trigger of the same Event also plays Raising Heart’s “Flier Fin” in sync, with a fresh
`[-50, +50] cents` random pitch offset.

| Name         | Action or State                           | Expected Behavior                                                           |
|--------------|--------------------------------------|--------------------------------------------------------------------|
| Clutch Claw Launch | Launch claw and trigger DIDX #79 | Retain original rope sounds, synchronously append one “Flier Fin” with ±50 cents random pitch |
| Shared Hook Path | Fly towards Wedge Beetles, Wingdrakes, or monsters and trigger the same Event | Each trigger plays the line once with a fresh pitch offset. |
| Missed Shot | The Event that plays DIDX #79 does not trigger | No additional voice line played |
| Other Actions | Actions that do not trigger this Event | No additional voice line played |

## Audio

| Name                       | Audio                                                                                                                                           | Loudness (LUFS-I) | Playback                                                                                      |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------------------|
| Raising Heart “Flier Fin” | [raising_heart_flier_fin_01](<../../audio/pl_prop_cmn/clutch_claw_launch/raising_heart_flier_fin_01(movie_1st.raising_heart.flier_fin.1).wav>) | -24 LUFS-I | Append independent media, playing once synchronously with the original sound as a standard voice Sound with ±50 cents random Pitch and no delay Action |

Final WAV is 48 kHz, stereo, 24-bit PCM, 48000 frames (1 second), measured loudness is -23.5 LUFS-I. No gain, normalization, or loudness correction during build; only downmix without gain to
48 kHz, 16-bit mono Wwise PCM WEM, channel config `000001410000`.

## Implementation Contract

- Original Bank: `original/nbnk/pl_prop_cmn.nbnk`, Wwise v120, Bank ID `4182706408`.

| Name                   | Event ID   | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|------------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| Clutch Claw Launch (Added Voice) | 1419271252 | 546716350 | 334024264 | 653757911 / 334975050 | #79 / 334975050 | 1404747944 | 137314667 |

- Original DIDX #1–#241 remains byte-exact; added voice is DIDX #242 / Media ID `259390702`. Original Media `334975050`, Sound `653757911`, and
  Random Container `334024264` are all unmodified.
- Event `1419271252` Action list changes from `546716350` to `546716350, 1404747944`, the original Action always remains the first item; the new Action is a
  Play Action with no delay, targeting the new Sound `137314667`, and serialized before the target Event. The SHA-256 of the original Sound, Random, Action, and Event body are respectively
  `a82d8dc855b6b2051ff301e163a5f8a9d740012b49192f8d512432a3d650a06d`,
  `7cc917007a8d22b7aa678acebf3c3f08d3dc224cc5201024555ce56485a39b4c`,
  `015cffb4b6d6b5f2841719a2a2a2be8b1060bba94775c3bb52622f945498a6f7`,
  `8179cc400c084912d8bbf4ae9feb09cfdd4068e37da1f7fcfd80ffc54da02b61`.
- New Sound using 46-byte standard voice body as template: source from `original/nbnk/wp_cmn_epvsp.nbnk` Sound `890667980` / Media
  `838569492` (original body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`), only replacing Sound ID and
  Media ID, fixed `DirectParentID=209038110`, body `+0x20` `PositioningParams.uByVector=0xC1`. Using
  `HircPitchSettings(None, None)` as a guard, insert random Pitch range `(-50.0, 50.0)` into the new Sound, base Pitch remains default; the final body
  is 55 bytes, SHA-256 is `9d675712ffb82adbf9da68bc14d64c09bc3bec7b2115f73d2f53598b5c1fa409`. The new Action body SHA-256 remains
  `069217cd5ae92ad8de3fb1197943cc225635593e338597115f8f113b0f8db071`; the expanded Event body SHA-256 remains
  `e782c444805654508990b381a6a5d5b37d020f3a1e573762b4cc3472ba06cae3`.
- External parent locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer `209038110` body SHA-256
  `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; this reference Bank is not included in the Mod.
- Original playback parent chain is `334024264 → 917544551 → 694534885`. No Stop Action referenced by the Event targets this parent chain. The design adds no Stop
  Action, so the voice plays to completion.
- Serialization order is fixed as New Sound → New Action → Original Event. This design increases the number of media from `241` to `242` and the number of HIRC objects from `742` to `744`.
  The payload grows from `40542` to `40629` and the Event grows from `12` to `16` bytes. The changed-byte count is `9` and the payload delta is `+87`. Except for
  DIDX, DATA, new Sounds with local random Pitch, new Actions, and the expansion of the target Event Action list, other Bank contents remain byte-exact.
- New Media `259390702`, Sound `137314667`, and Action `1404747944` are derived from
  `wwise_fnv1("raising_heart_pl_prop_cmn_clutch_claw_launch_" + suffix)`'s `media`, `sound`, and `action` respectively; all have passed the collision checks for all Media/HIRC IDs in the original
  Bank.
