---
design_id: wp_gun_cmn.reload
target_artifacts:
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# Reload

## Description

Full Reload and the Load Wyrmstake Blast move keep their original mechanical sounds. When either move triggers the original DIDX #1 sound, Raising Heart’s “Reload” plays once in sync with a fresh `[-50, +50] cents` random pitch offset. Quick Reload and other Gunlance moves are outside this change.

| Name         | Action or State                     | Expected Behavior                                      |
|--------------|--------------------------------|-----------------------------------------------|
| Full Reload | Perform a Full Reload that triggers DIDX #1 | Keep the original sounds and play “Reload” in sync with a ±50 cents random pitch offset. |
| Load Wyrmstake Blast | Load Wyrmstake Blast and trigger DIDX #1 | Keep the original sounds and play “Reload” in sync with a ±50 cents random pitch offset. |
| Quick Reload | Perform a Quick Reload | No "Reload" played |
| Other Gunlance Actions | Other routes that do not trigger the reload sound at DIDX #1 | No "Reload" played |

## Audio

| Name                    | Audio                                                                                                                        | Loudness (LUFS-I) | Playback                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------|----------------|------------------------------------------------------------------------------|
| Raising Heart “Reload” | [raising_heart_reload_01](<../../audio/wp_gun_cmn/reload/raising_heart_reload_01(movie_2nd_as.raising_heart.reload.1).wav>) | -24 LUFS-I | Add independent media; play once synchronized with DIDX #1 original sound with standard voice Sound and no delay, with a random offset of ±50 cents each time |

## Implementation Contract

- Original Bank: `original/nbnk/wp_gun_cmn.nbnk`, Wwise v120, Bank ID `939294496`.

| Name                  | Event ID   | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|-----------------------|------------|----------------|--------------|------------------------|--------------------|----------------|-------------|
| Reload (Additional Voice) | 3476627122 | 126049847 | 411055943 | 176748589 / 86782159 | #1 / 86782159 | 3418611510 | 1474128429 |

- Original DIDX #1–#33 remain byte-exact; after DIDX #34 of `stationary_draw` and DIDX #35 of `overhead_smash`, the additional voice is
  DIDX #36 / Media ID `1284288484`. This design does not modify the media added by the first two designs.
- The Action list of Event `3476627122` changes from `126049847` to `126049847, 3418611510`, with the original Action always remaining as the first item; the new Action is a Play with no
  delay, targeting the new Sound `1474128429`, and serialized before the target Event.
- The donor `176748589` and Container `411055943` in the table serve only as guards for the original path; the new Sound uses the 46-byte standard voice body as a template, sourced from
  `original/nbnk/wp_cmn_epvsp.nbnk`'s Sound `890667980` / Media `838569492` (original body SHA-256
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`), replacing only the Sound ID and Media ID, fixing
  `DirectParentID=209038110`, and the `PositioningParams.uByVector=0xC1` of body `+0x20`. Using
  `HircPitchSettings(None, None)` as a guard, only a random Pitch range of `(-50.0, 50.0)` is inserted into the new Sound, with the base Pitch
  remaining default; the final body is 55 bytes, and SHA-256 is
  `49b0c3c0cd9a4532abf62b92e701f30cb3f6418d5385c98b1e50ca45d2665c21`. The Container remains byte-exact, continuing to contain only the donor
  Sound, weight `50000`, and the original random playback list with avoid-repeat `1`; the new Sound is not added to this Container, and the original mechanical sounds do not inherit the new Pitch.
- External parent locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; this reference Bank is not included in the Mod.
- Project WAVs are fixed at 48 kHz, stereo, 24-bit PCM, and maintain the -24 LUFS-I recorded in the audio table; no gain, normalization, or loudness correction during build, only downmixing without gain to
  48 kHz, 16-bit mono Wwise PCM WEM.
- This design individually increases the HIRC object count from `123` to `125`, and the payload from `7250` to `7337`; adds 1 Sound and 1 Action, Event
  `3476627122` increased from `12` to `16` bytes, changed-byte count is `9`, payload increment is `+87`. When merged with the rest of the design from the current artifact owner,
  DIDX contains a total of 43 items, HIRC object count increased from `123` to `146`, payload from `7250` to `8243`, cumulative
  changed-byte count is `17`, payload increment is `+993`.
- New Media `1284288484`, Sound `1474128429`, and Action `3418611510` are fixed by
  `raising_heart_wp_gun_cmn_reload_media`, `raising_heart_wp_gun_cmn_reload_sound`, and
  `raising_heart_wp_gun_cmn_reload_action`'s `wwise_fnv1()` values respectively; collision checks for all original Bank Media/HIRC IDs and IDs occupied by other designs from the same owner have passed.
  Except for the addition of DIDX/DATA, new Sounds with local random Pitch, new Actions, and the expansion of the target Event Action list, other Bank
  contents maintain byte-exact order with existing objects.
