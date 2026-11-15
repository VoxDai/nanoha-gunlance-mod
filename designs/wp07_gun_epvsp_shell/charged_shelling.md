---
design_id: wp07_gun_epvsp_shell.charged_shelling
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# Charged Shelling

## Description

All shelling types keep their original charge, aim adjustment, and charged explosion sounds. Starting a horizontal, diagonal, or vertical charge immediately plays one of two equally likely Nanoha “Divine” clips. Adjusting the aim during a charge does not replay it. A completed charged shot plays one of three equally likely “Buster” clips in sync with the explosion. The shot after insertion in the Clutch Claw Weapon Attack uses the same Buster pool. The two stages choose independently of each other and of the clip source, and repeats are allowed. Each playback has a
±50 cents random pitch offset. When Divine or Buster starts, any unfinished line from the other stage on the same game object fades out linearly over 50 ms. The new line starts immediately and can briefly overlap the fade. The vanilla character grunt is muted when firing ordinary or charged shots in any of the three types and directions. All weapon effects and charge-start sounds are preserved, and ordinary shelling remains without a character voice.

| Name                       | Action or State                             | Expected Behavior                                                                                                       |
|----------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------------------|
| Horizontal Charge Start | Begin charging with a horizontal aim in any shelling type | Keep the original start sound. Play Divine once at Motion 132 frame 1 and fade out any unfinished Buster over 50 ms. |
| Diagonal Charge Start | Begin charging with a diagonal aim in any shelling type | Keep the original start sound. Play Divine once at Motion 133 frame 1 and fade out any unfinished Buster over 50 ms. |
| Vertical Charge Start | Begin charging with a vertical aim in any shelling type | Keep the original start sound. Play Divine once at Motion 134 frame 1 and fade out any unfinished Buster over 50 ms. |
| Aim Adjustment During Charge | Switch between horizontal, diagonal, and vertical aim while charging | Keep the original sounds in Motions 139–142. Divine does not replay during the same charge. |
| Wide Charged Shelling | Complete a charge and trigger a Wide explosion | Keep the original explosion. Play Buster once in sync and fade out any unfinished Divine over 50 ms. |
| Long Charged Shelling | Complete a charge and trigger a Long explosion | Keep the original explosion. Play Buster once in sync and fade out any unfinished Divine over 50 ms. |
| Normal Charged Shelling | Complete a charge and trigger a Normal explosion | Keep the original explosion. Play Buster once in sync and fade out any unfinished Divine over 50 ms. |
| Clutch Claw Weapon Attack Shot | Fire after inserting the gunlance into the monster | Keep the explosion and play the shared Buster Container once. Preserve the original insertion sound. |
| Interrupted Charge | Cancel or interrupt a charge after it begins | Buster does not trigger. Divine plays to completion without an additional Stop. |
| Consecutive Charges and Shots | Begin another charge or trigger another explosion | Each stage makes a fresh independent choice: 50% per Divine and 1/3 per Buster. Repeats are allowed and the stages do not have to match clip sources. |
| Character Voice on Charged Shots | Release a charged Normal, Long, or Wide shot horizontally, diagonally, or vertically | Mute the original character grunt. Retain the original weapon sounds and Buster. |
| Ordinary Shelling | Uncharged shots in all three shelling types and all three directions | Mute the original character grunt and retain the original weapon sounds. Ordinary shots receive no replacement character voice, Divine, or Buster. |
| Empty Shots and Other Moves | Empty shots, Full Burst, and other Gunlance moves | Retain each move’s existing audio design. This design adds no voice and does not extend character voice muting to these moves. |

## Audio

| Name      | Audio                                                                                                                                    | Loudness (LUFS-I) | Playback                                                                                                              |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------|
| Divine 01 | [nanoha_divine_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_divine_01(battle_of_aces.attack_04.1).wav>)                | -21 LUFS-I     | Independent appended media with weight 50000 (50%). Shares a Random Container with Divine 02, which selects one clip at frame 1 of Motions 132–134 with no delay. Stops all three Buster clips. |
| Divine 02 | [nanoha_divine_02](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_divine_02(gears_of_destiny.attack_voice.attack_04.1).wav>) | -21 LUFS-I     | Independent appended media with weight 50000 (50%). Shares Divine 01’s trigger, random pitch, and Stop behavior. |
| Buster 01 | [nanoha_buster_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_01(battle_of_aces.attack_04.2).wav>)                | -21 LUFS-I     | Independent appended media with weight 50000 (1/3). The three Buster clips share a Random Container. Each of the three explosion Events selects one clip with no delay and stops both Divine clips. |
| Buster 02 | [nanoha_buster_02](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_02(gears_of_destiny.attack_voice.attack_04.2).wav>) | -21 LUFS-I     | Independent appended media with weight 50000 (1/3). Shares Buster 01’s trigger, random pitch, and Stop behavior. |
| Buster 03 | [nanoha_buster_03](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_03(movie_reflection.nanoha.excellion_buster.1).wav>) | -22 LUFS-I | Weight 50000 (1/3). Shares the trigger, random pitch, and Stop behavior of Buster 01/02. |

All five final WAVs are 48 kHz stereo 24-bit PCM. In table order, the first four retain 42000/48000/60000/60000 frames (0.875/1/1.25/1.25 seconds). They were standardized using constant linear gains of
-1.06/+1.03/-5.26/-6.20 dB to target -21 LUFS-I. Final measurements are -21.00/-20.95/-21.02/-21.00 LUFS-I, with true peaks of
-12.54/-10.33/-16.29/-17.40 dBTP. The updated Buster 03 is 60000 frames (1.25 seconds) and measures −21.97 LUFS-I and −11.41 dBTP. A trigger fades out the other pool over 50 ms. Only one clip plays per trigger, and repeats are allowed. The build downmixes without gain to
48 kHz, 16-bit mono Wwise PCM WEM, channel config
`000001410000`. The build applies no loudness correction.

## Implementation Contract

- The original animation and request files are `original/lmt/w07_00.lmt` (LMT v95), `original/wwev/hm_wp07_snd_ev.wwev`, and `original/wwev/pl_voice.wwev` (both WWEV v19).
- Divine target Bank is `original/nbnk/wp_gun_cmn.nbnk`, Wwise v120, Bank ID `939294496`.

| Name             | Event ID         | Original Action ID | Container ID           | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID             |
|------------------|------------------|--------------|------------------------|------------------------|--------------------|--------------|-------------------------|
| Charged Start Original Sound Commission | 3452820647 (New) | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 1005770249 | — |
| Charged Start Divine | 3452820647 (New) | 1061269777 | 522283251 → 1153640130 | 233981936 / 867938822 | #27 / 867938822 | 583060699 | 3754878246 / 4035275377 |

- The Action list for the original Event `3567942167` is fixed to `(1061269777,)`, and the original Action full body SHA-256 is
  `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a`, which must remain a no-delay Play, targeting the original Container
  `522283251`. The original Sound `233981936` / Media `867938822`, DIDX #27, and original Event all remain byte-exact.
- The Action list for the new Event `3452820647` is fixed to `(1005770249, 1603135794, 85406655, 2076396906, 583060699)`: sequentially the commissioned full original Event
  `3567942167`'s PlayEvent, sequentially stopping Buster 01/02/03, and the no-delay Play of the target Random `1153640130`. Following two Sounds →
  Random → Original Sound Commission Action → Three Buster Stop Actions → Divine Play Action → New Event → Original Event, serialized in order.
  The full body SHA-256 of the Original Sound Commission, Divine Play Action, and New Event are sequentially
  `c87314f918eb3d617c61c98cf8842b0132f85e688d3ad0e8d10da6d1d41bafca`,
  `ac01f6c3c01f4b9870cf14af9c1f6614cc78fa2d2d1f01dcc16bed071da1be38`,
  `8e966f8f23233c1839a1f9a464e3e2a26eda29b3c457e30ddfbe7935ea3f5582`.
- Divine 01 uses Media `370615719`, Sound `3754878246`, and Action `583060699`; Divine 02 uses Media `3246372848`, Sound
  `4035275377`. When applied individually, the two Media files are appended as DIDX #34–#35; when merged with the existing design of this Bank, they are #45–#46. Runtime media must be read back as 48
  kHz, 16-bit mono Wwise PCM, with 42000/48000 samples respectively.
- Divine Random `1153640130` clones the original Container `570218704`, the 83-byte donor body SHA-256 is
  `be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427`, the original playlist `((647150707, 50000),)`,
  avoid-repeat=1. The new playlist is `((3754878246, 50000), (4035275377, 50000))`, avoid-repeat=0; retain one-shot
  Random/Normal, disable transition, reset on every play; no local Volume or instance limit. The body `+0x0B` parent changes from `768813060` to `209038110`
  , Pitch base defaults, random range `(-50.0, 50.0)`. The final 95-byte body SHA-256 is
  `40b6d65e0aa7f692932836ead31d07e91a63606975dd12d0be46389a4ca8a426`.
- Two Divine Sounds use `original/nbnk/wp_cmn_epvsp.nbnk`'s Sound `890667980` / Media `838569492` provided 46-byte
  standard voice body; original body SHA-256 is `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`, fixed
  `DirectParentID=1153640130`, body `+0x20`'s `PositioningParams.uByVector=0xC1`; reuse the project-verified Container voice hierarchy.
  01/02 final Sound body SHA-256 are `251b8841b03f2489535afa09e60afae689137fbc3249a0a60bab8cd7481e372d`,
  `047453c18d735292b6965b2dfb4e83b79803bf9311836232b60bad6a9da27b87` respectively. Sub-Sounds have no local Pitch, delay, or extra gain.
- External parent is locked by `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer `209038110` body SHA-256
  `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; this reference Bank is not included in the Mod. The native playback root and parent chain are
  `522283251 → 768813060 → 972300144 → 694534885`, and no original `wp_gun_cmn.nbnk` was found to be referenced by an Event and hitting this chain for a Stop
  Action; This design adds bidirectional Stop based on user-specified behavior, rather than cloning them as native interrupt routes.
- Divine routing adds 2 Sound, 1 Random, 5 Action, and 1 Event, with HIRC objects `123→132` and payload
  `7250→7610`, an increment of `+360`, and a changed-byte count of `4`. Excluding the following character mute objects, merging with the existing design of this Bank results in 46 media items, HIRC objects
  `123→157`, and payload `7250→8754`, with a total increment of `+1504` and a changed-byte count of `25`; the existing reload Event
  `3476627122` remains the only expanded original object. Aside from DIDX/DATA appending, the aforementioned 9 new objects, and the following 3 mute objects, this design does not change the original objects or other chunks of this Bank.

| Name | Event ID | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| Normal and Charged Shelling character mute wrapper | 2825008231 (new) | — | — | — | — | 3500432807 | — |
| Mute PlayEvent target | 3344928599 (new) | — | — | — | — | — | — |

- Two mute Events and Actions are both newly added to the Bank `939294496` constructed by `original/nbnk/wp_gun_cmn.nbnk`.
  The complete Action list for Event `2825008231` is `(3500432807,)`; Action `3500432807` is a zero-delay 13-byte PlayEvent,
  which only delegates to the zero-Action Event `3344928599` within the same Bank, the latter of which has a complete list of `()`. No new media, Sound, Container, Play, or Stop are added,
  no original character Events `281150953` are referenced, and no original character Banks or shared mixing parents are modified. The mute route has no playable root and does not add corresponding Stops.
- The serialization order is fixed as Action `3500432807` → zero-Action Event `3344928599` → wrapper Event `2825008231` →
  original Event `3567942167`; maintaining the relative order and body of all previous objects. The three complete bodies' SHA-256 are respectively
  `373a8565c017faed8e9dbe7e0d0bc985c74f7fff140e96be452760fb387de9ed`,
  `b690ca747f5c2f83d75a560d068fbd86abaa6f20ce8a6eeacb4d669ce978277c`,
  `4d0ae624d720e9762e04c1e6bd78afb8045cd44b78d323fe32db3af2563ac1c5`.
- The mute route independently adds 1 Action and 2 Events: HIRC objects `123→126`, payload `7250→7298`, an increment of `+48`,
  and a changed-byte count of `0`. Combined with this design's Divine routing applied separately as `123→135`, `7250→7658`, the total increment is `+408`,
  and the changed-byte count is `4`; merging with all registered designs in the Common Bank results in 49 media items, HQIRC objects `123→172`,
  and payload `7250→9150`, with a total increment of `+1900` and a changed-byte count of `49`. Does not change DIDX/DATA, existing media, or other chunks.
- ReqNo `6608` and the three mute HIRC IDs follow the-already-tested-in-game local mute route without reallocation; the original 8 reference Banks have been reviewed,
  and there are no conflicts with current design/builder values or original WWEV requests and Events. This route does not require cross-Bank PlayEvent APIs.

- Buster target Bank is `original/nbnk/wp07_gun_epvsp_shell.nbnk`, Wwise v120, Bank ID `3273965928`.

| Name                 | Event ID   | Original Action ID | Container ID           | donor Sound / Media ID | DIDX / Original Media ID | New Action ID | New Sound ID             |
|----------------------|------------|--------------|------------------------|------------------------|--------------------|--------------|-------------------------|
| Wide Explosion (Buster) | 3325567640 | 116178715 | 63659294 → 2510752860 | 264207839 / 93971960 | #4 / 93971960 | 858972567 | 3489806140 / 3928375835 / 690215586 |
| Long Explosion (Buster) | 1962814816 | 409203877 | 176125134 → 2510752860 | 220939954 / 693612246 | #33 / 693612246 | 4053288866 | 3489806140 / 3928375835 / 690215586 |
| Normal Explosion (Buster) | 2187565051 | 530572411 | 847665525 → 2510752860 | 69557296 / 849663903 | #37 / 849663903 | 3259504927 | 3489806140 / 3928375835 / 690215586 |

- The original Charged effect Event `1308679810` must be restored and its original Action list `(485858073,)` maintained; its complete Event / Action body SHA-256
  are `09b397e743d362043c390fdbab88811990f9867b882cea25cd56b59053c19347`,
  `0cdb30628eca7abe5b4f19bf4f70c1b08d6d93b5291c4d0b5a3b9734606f7e07` respectively. No Divine Action or Sound may be added to this Event.
  `3754878246`/`4035275377`, Media `370615719`/`3246372848`, Random `1153640130` and Action `583060699`
  Can only exist in final `wp_gun_cmn.nbnk`.
- Original Bank's 42 media and payload remain byte-exact; retain Full Burst and Wyvern's Fire DIDX #43–#49 and their order for the same artifact owner, with Buster 01 appended as
  DIDX #50 / Media `1793121649`, 02 for #51 / Media `570980126`, 03 appended as #59 / Media `2785082779`, and retain existing indices #52–#58. When applied individually, it is #43–#45. At runtime, all three media must be read back as 48
  kHz, 16-bit mono Wwise PCM, 60000 samples.
- The Action list for the three explosion Events is fixed to `(116178715, 1426818832, 515837897, 858972567)`,
  `(409203877, 1225287532, 1287808358, 4053288866)`, `(530572411, 728690884, 1267644869, 3259504927)`; the original Action is always first, stop
  Actions for Divine 01/02 are in the middle, followed by Buster Play. All three Buster Play Actions have no delay and share Random `2510752860`. Wide/Long/Normal Play body SHA-256 are respectively
  `0fe2ec6e037d63bc1a91eb264ff999ed2d1adf856a8604e181ac9f436c1f9a1d`,
  `878806e7a14fe72a5cb1ff69a7d60f5db611861c3032ac10c8fb67b299458989`,
  `f0fa0a8665a23264e891f26ddbe4335aed7815ae8afb6733e3e35feb46d64992`.
- Buster Random `2510752860` clones the original Container `58172267`, 83-byte donor body SHA-256 is
  `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`, original playlist `((46149961, 50000),)`, avoid-repeat=1.
  New playlist is `((3489806140, 50000), (3928375835, 50000), (690215586, 50000))`, avoid-repeat=0; other Random modes and Pitch are the same as Divine.
  body `+0x0B` parent changes from `717111903` to `209038110`. Final 107-byte body SHA-256 is
  `1d3240b0b6205ac132d53ddf81f7647375ae2c56a365e4c904d7819491862a33`.
- Buster Sound `3489806140`/`3928375835`/`690215586` uses the above standard 46-byte C1 template, all DirectParentID are `2510752860`, child Sounds have no local
  Pitch, delay, or extra gain. Final body SHA-256 are respectively
  `bbc603bac06e30ea54aa58de3b749e1d413c8275c2834a931e015b8835c7e06d`,
  `2e5a7e3eb467114ad41a2a742e5204f51a5dcf9bf45bc0a011f8c1a3cd8663a4`,
  `8851587d5cec37e5055865facfd818745aa344bf30ca4a001f5caea89b87bcf0`.
- The three explosion original play roots and parent chains are `63659294`, `176125134`, `847665525`, which then merge into
  `717111903 → 972300144 → 694534885`. The set of Stop Action targets referenced by Events in the original Bank is fixed to
  `{60034062, 662442083, 1054468797, 956375262, 599243561}`; none match the play roots or parent chains. To implement the requested interruption behavior, this design adds
  two independent Stop Actions per explosion Event to stop Divine.
- Buster routing individually adds 3 Sounds, 1 Random, and 9 Actions, extends 3 original Events, HIRC objects `181→194`, payload
  `11090→11628`, incremental `+538`, changed-byte count is `13`. After merging with all registered designs, media `42→59`, HIRC objects
  `181→226`, payload `11090→13246`, total increment `+2156`, changed-byte count is `42`. This design, besides DIDX/DATA appending, the above 13 new objects, and 3
  Event extensions, keeps other Bank chunks, original media, and original HIRC objects byte-exact.

| Name | Stop Event ID | Structure Reference Stop Action ID / target | scope | transition / fade | exceptions | New Stop Action ID | New Stop Target |
|------------------------------|---------------|----------------------------------|-------------|-------------------|------------|-------------------|--------------------------------------------|
| Divine start stops Buster | 3452820647 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 1603135794 | Buster Sound 3489806140 (Bank 3273965928) |
| Long Buster stops Divine | 1962814816 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 1225287532 | Divine Sound 3754878246 (Bank 939294496) |
| Normal-type Buster stops Divine | 2187565051 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 728690884 | Divine Sound 3754878246 (Bank 939294496) |
| Wide Buster stops Divine | 3325567640 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 1426818832 | Divine Sound 3754878246 (Bank 939294496) |
| Divine start stops Buster 02 | 3452820647 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 85406655 | Buster Sound 3928375835 (Bank 3273965928) |
| Wide Buster stops Divine 02 | 3325567640 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 515837897 | Divine Sound 4035275377 (Bank 939294496) |
| Long Buster stops Divine 02 | 1962814816 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 1287808358 | Divine Sound 4035275377 (Bank 939294496) |
| Normal-type Buster stops Divine 02 | 2187565051 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 1267644869 | Divine Sound 4035275377 (Bank 939294496) |
| Divine start stops Buster 03 | 3452820647 | 743936681 / 60034062 | Game Object | 50 ms / Linear | None | 2076396906 | Buster Sound 690215586 (Bank 3273965928) |

- Stop structure reference is the Action `743936681` of `original/nbnk/wp07_gun_epvsp_shell.nbnk`, with full body SHA-256
  `137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd`; its original transition is 200 ms.
  This design explicitly constructs a 23-byte `0x0103 / Stop_E_O` body, preserving this verified layout: `bIsBus=0`, no delay, only explicit
  `TransitionTime=50`, no random attributes, Linear (4), no exceptions; does not modify reference Action or native Wyrmstake Cannon 200 ms Stop.
- The SHA-256 of the first four Stop bodies in the table above is
  `f33f2c36a8e9ec2278fe3c85950abe4b8163f58a1770404fed9e531a2b4ebb65`,
  `7e8d8ce0db11ffde1a86d83040ee5812dad92236b33609a912b36ef890268c51`,
  `f35bb797fa57be95f56310f8c2ab6e5d25bee71e19485095d816fe0c35a23e03`,
  `f8a9743e56e31058af5bff91c2ae436b5072e3e9a63eb7b16e4d6cba44dd4afe`. The SHA-256 of the last four Stop bodies are respectively
  `a3e37d407b2de99b7f29088dc93127b5c02a5423a8c702196df2315edfa7b13d`,
  `528b713f34e7cadf416b2612ba9cc56a7813ad1f54409fcdcb4172610f114de7`,
  `6f9143c623e3e346b9a72f77961b896c8e67b70101113fac9ade4f8ddae9f051`,
  `e13eb2147999bf1de1e6e4b45a82ff8d241ee91ad564d1a34068f9fd4b2f9724`.
  Buster 03 Stop body SHA-256 is `546bee5372b864ea27999bb884e4aa030466b7fda336e9629d9a2b89015bbacb`.
  The SHA-256 of the three final Event bodies for Long, Normal, and Wide are respectively
  `4785364970e4080e0ddbec1853ed77f428c4dabd1a73028b8a3ff6f9072f6214`,
  `a8a3fd311a313491b6b4871b35668004d7195b0ad9b64b26c3024f845d4cff24`,
  `8d8857c2dfce5ebc9121f055016074b8b131b98c624b344b8833c30860726dae`.
- Each Action can only belong to one Event. The three explosion Events share Buster Random, but must not share Play or Stop Actions. First serialize three Sounds →
  Random; insert two Divine Stop → Buster Play → Event sequences at the original sequence position of each explosion Event; the order between original HIRC objects remains unchanged.
- The two Banks explicitly declare the nine cross-Bank Stop edges in the table above, binding respectively to the target Bank ID, Sound ID, and the full Sound body SHA-256 mentioned above.
  Single-Bank checks must not relax other missing references; the complete temporary Bank set must verify the actual target Bank, unique Sound, body hash, and media ownership.
  Do not copy target Sounds or media to another Bank, and do not expand scope by stopping shared parents; if the target is not playing, it does not affect the new voice and the original sound.
- The first four Stop IDs follow the independent Action live test package. Their FNV-1 name prefixes are
  `nanoha_test_charged_shelling_mutual_stop_`, and the suffixes in the order of the table above are
  `buster_action`, `divine_action`, `divine_normal_action`, `divine_wide_action`; names are preserved to maintain stable verified IDs.
  The four IDs have undergone collision checks with the original, reference, and existing custom Bank/WWEV and contract values; existing test definitions are formally adopted, no new values are assigned.
- All newly added IDs this time are derived from `wwise_fnv1("nanoha_wp07_gun_epvsp_shell_charged_shelling_" + suffix)`:
  `divine_02_media`/`divine_02_sound`/`divine_random_container` for `3246372848`/`4035275377`/`1153640130`;
  `buster_02_media`/`buster_02_sound`/`buster_random_container` for `570980126`/`3928375835`/`2510752860`;
  `buster_02_stop_action`,`divine_02_wide_stop_action`,`divine_02_long_stop_action`,`divine_02_normal_stop_action`
  for `85406655`/`515837897`/`1287808358`/`1267644869`. Verified to be unique from each other and do not conflict with the local original Bank's HIRC/Media or existing
  design/builder custom ID collision.

- Buster 03 uses the old Clutch Claw independent routes for Media `2785082779` and Sound `690215586`, both defined only in shell Bank. Stop `2076396906`'s derivative suffix is `buster_03_stop_action`, defined only in common Bank.
- [Clutch Claw Weapon Attack](../wp_gun_cmn/clutch_weapon_attack.md) only retains independent gun-drawing voice lines. Tested and confirmed that Clutch shots trigger the shared Buster routes; the coverage of the three shot types has been tested and accepted.

| Name | LMT | Motion | EventGroup | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| Horizontal Charged Shelling Start | `original/lmt/w07_00.lmt` | 132 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| Upward-Diagonal Charged Shelling Start | `original/lmt/w07_00.lmt` | 133 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| Vertical Charged Shelling Start | `original/lmt/w07_00.lmt` | 134 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| Horizontal Normal/Charged Shelling Fire Character Mute | `original/lmt/w07_00.lmt` | 101 | EventGroup02 | A | 0 | 1305 | 6608 | 5 |
| Upward-Diagonal Normal/Charged Shelling Fire Character Mute | `original/lmt/w07_00.lmt` | 102 | EventGroup02 | A | 0 | 1305 | 6608 | 5 |
| Vertical Normal/Charged Shelling Fire Character Mute | `original/lmt/w07_00.lmt` | 103 | EventGroup02 | A | 0 | 1305 | 6608 | 5 |

| Name | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | New ReqNo | New Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| Three types of Charged Shelling start poses share Divine | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6599 | 3452820647 |
| Normal/Charged Shelling Fire Character Mute | `original/wwev/pl_voice.wwev` | 1409 | 967571325 | 4 | `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507` | 6608 | 2825008231 |

- In `original/lmt/w07_00.lmt`, Motion 132 / 133 / 134 are 79 / 65 / 79 frames respectively, and TIML are located at
  `0xFE820` / `0x101280` / `0x1046A0`, each used only by its own Motion. Only allow the assignment frame 0 request for EventGroup06 slot B to be changed from
  `6470` to `6599`, with request positions being `0xFEDF0` / `0x101850` / `0x104C70`; all three trigger via trigger mask `0x02` at frame 1,
  with a separate changed-byte count of `3`, and file length remains unchanged.
- Motion 139–142-style-adjustments are all 21 frames and use independent TIML; EventGroup06 slot B must continue at frame 1 to trigger mask `0x02`
  Trigger original ReqNo `6470`, must not be changed to `6599`. End-to-end readout must only produce three Divine routes of Motion 132–134, posture adjustment only parses to the original
  Event `3567942167`. Divine and existing Motion 2, 128, 131, 143 modifications merge into `9` changed bytes, plus the following Motion 101–103
  mute modifications, the LMT changed-byte count is `15`; undeclared Motion, TIML, assignment, and triggers remain byte-exact with the file content.
- Motion 101/102/103 original lengths are 85/89/95 frames, TIML located at decimal offsets `603840`/`624896`/`645968`,
  each used only by its own Motion. Only replace the assignment frame 0 requests for EventGroup02/A in the table above, with assignment positions at decimal offsets
  `606048`/`627200`/`648272`; retain frame 5 trigger and mask `0x01`. Use guarded requests for replacement, do not write directly by file offset.
  Each of the three requests changes 2 bytes, the mute-only changed-byte count is `6`, and file length remains unchanged; the six LMT modifications in this design total `9`.
  Original ReqNo `1305` parses uniquely to `pl_voice.wwev` #17, mode `4`, Event `281150953`; keep original records unchanged, only change the routing of these three Motions.
  End-to-end readback must result in exactly three `Motion 101–103 → ReqNo 6608 → Event 2825008231`; all unselected requests remain as-is,
  including the three EventGroup06/D ReqNo `6460`, weapon trigger at frame 8, and Motion 132–134, 139–142 and the overhead smash route.
- `original/wwev/pl_voice.wwev`'s donor ReqNo `1409` uniquely parses to original record #20, mode `4`, Event `967571325`,
  size `129` bytes, see the table above for the full raw hash. A full clone, only changing ReqNo/Event ID to `6608`/`2825008231`;
  the new record raw SHA-256 is `2b21f2a836c096e164751adfcad860aa8f919fea0a857f11fa64ac4de40798c4`.
  When applied individually, it is #101, recording `100→101`, appending `129` bytes; when merged with the downward-slam ReqNo `6595` #101, it is appended as #102,
  total records `100→102`, total appended `258` bytes. The original 100 records, four dependency strings, existing downward-slam records, unknown fields, and boundaries all remain byte-exact,
  only updating record counts and tail-end appends is allowed.
- Action lists for Normal/Spread/Wide shelling Events `2629885944`/`1888950507`/`192028055` remain
  `(667354318,)`/`(680466555,)`/`(511124205,)`; no character-recovery Actions are added, nor are Normal or Charged explosion media changed.
- `original/wwev/hm_wp07_snd_ev.wwev`'s ReqNo `6470` uniquely parses to original record #17, mode `2`, Event `3567942167`, size
  `129` bytes and the full raw hash from the table above. A full clone of this record, replacing only ReqNo and Event ID; the new record raw SHA-256 is
  `0b6c6e87c3c78c669ac6bc6cd09112c54445e7bce5401380fc68e2fad136e8ee`. When applied individually, it appends as #44; when merged with existing ReqNo
  `6592` / `6596`, it appends as #46, total records `43→46`, total appended X-`387` bytes. The original 43 records, four dependency strings, existing
  #44–#45, record boundaries, and order remain byte-exact.
- Media `370615719`, Sound `3754878246`, Action `583060699` reuse
  `wwise_fnv1("nanoha_wp07_gun_epvsp_shell_charged_shelling_" + suffix)`'s `divine_01_media` / `divine_01_sound` /
  `divine_01_action`. The new Event `3452820647` and original voice-commissioned Action `1005770249` are derived from suffix
  `divine_01_motion_start_event` / `divine_01_motion_start_original_action` respectively. Buster Media `1793121649`, Sound
  `3489806140`, and Action `858972567` / `4053288866` / `3259504927` reuse `buster_01_media`,
  `buster_01_sound`, and `buster_01_wide_action` / `buster_01_long_action` / `buster_01_normal_action` respectively. ReqNo `6599` and the two
  new HIRC IDs have completed collision checks against the original 4550 NBNK, 1300 WWEV, and existing custom IDs; the three Divine stable IDs are migrations of existing contracts,
  do not allocate new values, and can only exist once in the final five target artifacts.
- In-game acceptance based on the description table: covers three shelling types and three initial muzzle postures; performing horizontal→upward-diagonal→vertical and reverse multiple adjustments in a single charge, only allowing Divine to play once
  upon the first entry into charging; canceling the charge does not trigger Buster, two consecutive independent charges each play Divine once, and each of the three explosions appends Buster only once; Normal shelling,
  air shots, and other gunlance actions do not play this design's voice. Normal and Charged shelling cover three types and three directions respectively, and no original character "hmph" sounds may appear during firing;
  Normal shelling does not add character voices, nor plays Divine/Buster. Comparative testing of air shots, Full Burst, continuous shelling, cancels, and posture adjustments must confirm that muting does not spread and all weapon sound effects are preserved.
  Existing partial muting has been tested to cover Charged firing for all three types; only the three directions of Normal shelling have been tested, other types still require acceptance and cannot be extrapolated as passed.
  Both directions require that when the target voice is not yet finished, it linearly fades out within 50 ms after the new voice begins, allowing overlap within this fade-out window; except for the aforementioned firing character requesting mute, the original voice and other voices are not stopped.
  User confirmation has been obtained for the zero-transition test of independent Actions, confirming they are loadable and Charged Shelling can Stop; this 50 ms auditory-feel, Divine stops the previous Buster,
  All candidate combinations for both sets, random repetition, ±50 cents auditory-feel, full coverage of the three types and postures, and multi-player isolation still require game acceptance. Do not record structural verification or existing zero-transition feedback as a random container or
  50 ms actual gameplay pass.
