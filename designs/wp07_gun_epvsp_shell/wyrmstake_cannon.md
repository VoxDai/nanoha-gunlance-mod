---
design_id: wp07_gun_epvsp_shell.wyrmstake_cannon
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
  - sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk
---

# Wyrmstake Cannon

## Description

The ordinary Wyrmstake Cannon keeps its mechanical, extension or insertion, release, and explosion sounds on hit and miss. Nanoha’s “ACS” plays once at the pre-lift entry verified by the gameplay probe, and “Drive” plays once at the post-insertion discharge entry. Firing immediately after loading Wyrmstake Blast plays ACS at Motion 310 frame 3, then Drive in the shared follow-up Motion 182. The ACS in 310 triggers when loading finishes even if firing has yet to begin. The 12
vanilla character voice triggers belonging to the Wyrmstake action are rerouted to silent events. When the ordinary stake hits and discharges, release sound 28 gains one Raising Heart voice line chosen with equal probability from “Unit Set” and “ACS Standby.” ACS, Drive, and the hit release line each pick a fresh pitch offset from `-50` to `+50 cents`
on every playback. Other actions’ character voices and the original Wyrmstake weapon sounds stay intact. Character lines that were already playing before the Wyrmstake input may continue into the move and are outside this reroute.

| Name                             | Action or State                                       | Expected Behavior                                                                                                |
|----------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| Ordinary Wyrmstake from diagonal shelling, Wide Sweep, or Full Burst | Start of Motion 144, before the gunlance lifts | The original Event and ACS start together. Drive plays on entry into Motion 145. |
| Ordinary Wyrmstake from vertical shelling | Start of Motion 178, before the gunlance lifts | The original Event and ACS start together. Drive plays on entry into Motion 179. |
| Ordinary Wyrmstake from horizontal shelling | Start of Motion 181, before the gunlance lifts | The original Event and ACS start together. Drive plays on entry into Motion 182. |
| Ordinary Wyrmstake hits and releases | Hit release sound 28, then hit explosion sound 40 | ACS and Drive each play once. Release adds either “Unit Set” or “ACS Standby” with equal probability. Sound 40 retains the original explosion and muting rules. |
| Ordinary Wyrmstake misses | Miss release sound 38, with no hit explosion sound 40 | ACS and Drive each play once. The original miss sound and muting rules apply, without the hit release lines. |
| Fire immediately after loading Wyrmstake Blast | Motion 310 frame 3, followed by Motion 182 | ACS plays when loading finishes. Drive plays on release after insertion. Vanilla character lines in 310 and 182 are muted. |
| Other Wyrmstake Blast follow-ups | Enter Motion 310 or one of the ordinary Wyrmstake starting Motions above | Each triggered ACS entry plays once. Drive plays on entry into the follow-up, and vanilla character lines are muted. |
| Attempt without a stake | Begin the move without entering the release follow-up | ACS plays on startup. Drive requires the follow-up. The Wyrmstake Motions entered play no vanilla character lines. |
| Moves outside Wyrmstake | Shelling alone, stopping after Wide Sweep or Full Burst, Full Reload, drawing, or sheathing | Keep the vanilla character lines. These moves do not play ACS, Drive, or either hit release line. |

## Audio

| Name                          | Audio                                                                                                                                                              | Loudness (LUFS-I) | Playback                                                                                            |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| Nanoha “ACS” | [nanoha_acs_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/nanoha_acs_01(gears_of_destiny.attack_voice.attack_02.1).wav>)                                 | -21 LUFS-I     | Shares existing Media and Event for ordinary Wyrmstake before lifting or for completion of loading in Motion 310. Plays once per trigger with `±50 cents` random pitch. |
| Nanoha “Drive” | [nanoha_drive_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/nanoha_drive_01(gears_of_destiny.attack_voice.attack_02.2).wav>)                             | -21 LUFS-I     | Appends independent media at the post-insertion release entry. Plays once without delay with `±50 cents` random pitch. |
| Raising Heart “Unit Set” | [raising_heart_unit_set_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/raising_heart_unit_set_01(movie_detonation.raising_heart.unit_set.1).wav>) | -24 LUFS-I     | One of the random choices for hit release Event 28. Equal weight, no delay, repeats allowed. Inherits the Container’s `±50 cents` pitch range. |
| Raising Heart “ACS Standby” | [raising_heart_acs_standby_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/raising_heart_acs_standby_01(movie_2nd_as.raising_heart.acs_standby.1).wav>)    | -24 LUFS-I     | One of the random choices for hit release Event 28. Equal weight, no delay, repeats allowed. Inherits the Container’s `±50 cents` pitch range. |

The final ACS and Drive WAVs are 48 kHz stereo 24-bit PCM, with 42000 and 43583 frames respectively (0.875 and 0.907979 seconds). After user-approved constant-gain adjustments, their measured loudness is
-21.01 and -21.04 LUFS-I, with true peaks of -14.09 and -14.33 dBTP. The build downmixes without gain to 48 kHz 16-bit mono Wwise PCM WEM (channel
config `000001410000`) and applies no loudness correction. ACS and Drive each have their own Event, Action, Sound, and Media. Each uses its assigned file and neither delays the other. The two
Sounds have no local base Pitch and independently apply a local `(-50.0, 50.0)` cents random range. Unit Set has 44752 frames (0.932333 seconds). A +2.84 dB constant gain adjustment from -26.84 LUFS-I measures -23.99 LUFS-I with a true peak of -9.93 dBTP. The final WAV is likewise 48 kHz stereo 24-bit PCM. The updated ACS Standby WAV has
78000 frames (1.625 seconds). It uses the previously approved -24 LUFS-I target. A +2.58 dB constant gain adjustment from -26.58 LUFS-I yields -24.00 LUFS-I and a true
peak of -10.13 dBTP. This WAV is also 48 kHz stereo 24-bit PCM. The two hit release WAVs use separate Media and Sounds. The build downmixes them without gain to 48 kHz 16-bit
mono Wwise PCM
WEM (channel config `000001410000`). Neither Sound sets a local Pitch. Their shared Random Container selects one with equal probability and `avoid-repeat=0`
, allows continuous repetition; Container's local Pitch base is default, random range `(-50.0, 50.0)` cents. New Action of the hit-release Event has no
delay. Original weapon sound routing does not inherit custom random Pitch.

## Implementation Contract

- Original projectile Bank: `original/nbnk/wp07_gun_epvsp_shell.nbnk`, Wwise v120, Bank ID `3273965928`. Hit-release, miss-release, and hit-explosion are managed by independent original Events from the same
  Bank; hit-release random voice hit detection does not depend on this Motion 310's LMT redirection, and does not modify the projectile script.
- Original Common Bank: `original/nbnk/wp_gun_cmn.nbnk`, Wwise v120, Bank ID `939294496`. Original event structure Bank:
  `original/nbnk/pl_wp_par_op_event_structure.nbnk`, Wwise v120, Bank ID `2944223826`, contains only BKHD and HIRC, no
  DIDX/DATA; this chunk structure must be maintained. Standard voice Sound donor comes from `original/nbnk/wp_cmn_epvsp.nbnk`, Bank ID `1149256632`
  , Sound `890667980`/Media `838569492`, 46-byte donor body SHA-256
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`. External parent is locked by `original/nbnk/pl_act_vo_event.nbnk`'s
  Actor-Mixer `209038110`, body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`; reference Bank
  is not packed.

| Name                            | Event ID   | Original Action ID | Container ID | donor Sound / Media ID | DIDX / Original Media ID               | New Action ID | New Sound ID           |
|---------------------------------|------------|--------------|--------------|------------------------|----------------------------------|--------------|-----------------------|
| ACS, 144 start original routing | 2798914977 | 193548488 | 564339955 | 890667980 / 838569492 | #28 / 970807803, #29 / 971330098 | 2004285408 | 1847466623 |
| Drive, 145/179/182 end original routing | 2279772715 | 479984650 | 68493596 | 890667980 / 838569492 | #23 / 732840854 | 551409861 | 573906608 |
| Random voice, hit-release original routing | 1581859410 | 705609317 | 75663767 | 151638268 / 629066097 | #28 / 629066097 | 1821689211 | 38895430 / 1727570929 |

- Confirmed action timeline is hit-release DIDX #28/Media `629066097` (Sound `151638268` → Container `75663767` → Action `705609317` → Event `1581859410`), followed by hit-explosion DIDX #40/Media `932229979` (Sound `762689746` → Container `969725659` → Action `208572495` → Event `1465516383`); miss-hit standalone DIDX #38/Media `858252802` (Sound `835886265` → Container `1049048275` → Action `951626294` → Event `3115395173`). The Action lists of the three original Events contain only the described original Actions. The original full body SHA-256 of the hit-release Event/Action/Container/Sound are `5e098d73a0645fc0d81188cadafe728e3325fd9eda7c67230d85579676e9b26d`/`29045c6ed5c13a286828f7c6e351b3b75a6f8b781539a59861b0cde3aa700521`/`43f44064e18427629d77e5a482d03f415822739ce82b138d07a4372a74cfceb8`/`a1208fe2fdb8a16dd7ec60f1c904ff593922a5d6d06e892a19ea0bbe6192f8b5` respectively. The original full body SHA-256 of the hit-explosion Event/Action/Container/Sound are `2c7b630cdd0276e580e69fcbe8a751ff13f4faee6df765cf87887cdc75fd1962`/`62d140af4d2431b7da43e4ca08246271d73da2d2cc544b7d78bd8839c9452450`/`fa0dd955ba17db67bae2e17c57c5d3de804026a91803d54a3f85d54808bf133a`/`8470dd13a4e97610fe5de92d0c7b1a1c9ca6988ad2e49b6f5b57888593ccd821` respectively; the miss-hit Event/Action body SHA-256 is `fe73b26bcad55501da8c1dcbc4298069cf4e3748d81e12589b61b203089b1340`/`d4e189a50744ef1b00b429df4ee15fc90e93a466089d139c4f519d2313e29c19`. Explosion Event `1465516383` and miss-hit Event `3115395173`, and all original Action/Container/Sound/Media remain byte-exact.
- Append Unit Set DIDX #52/Media `949600199` and ACS Standby DIDX #53/Media `938668400` sequentially after the existing DIDX #51. Two
  46-byte standard voice Sounds are `38895430` and `1727570929` respectively, copied from standard donor Sound `890667980`/Media `838569492`, only replacing
  Sound/Media ID and DirectParentID `2393951905`; `PositioningParams.uByVector=0xC1`, with no local Pitch or Aux changes. Full body
  SHA-256 are `05b6321f093b39b5a0ebd59c8bf0208b117680a6541d60eabd1d64868f38ca3b` and
  `ad97250dde54b4126721605eca752ca090b214d0ec40b135cf930ee07bd8528c`.
- Random Container `2393951905` clones the same Bank's original Container `58172267`; donor is 83-byte body, SHA-256
  `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`, original playlist `((46149961, 50000),)`, `avoid-repeat=1`
  , Random mode, local Pitch `(-50.0, 50.0)` cents. New playlist is fixed to `((38895430, 50000), (1727570929, 50000))`,
  `avoid-repeat=0`, retaining the donor's Random/Normal, one-shot, no transition, and reset on each play settings; parent changes from `717111903` to standard voice
  Actor-Mixer `209038110`, local Pitch base is default, random range remains `(-50.0, 50.0)` cents. Final body is 95 bytes, SHA-256
  `7a018ec43f7d5f17ff03bddb144b2f8237f5d04d108ecc04a5bf68b7045dd95c`. Pitch randomization is only set on the Container, so the two Sounds
  do not stack a second pitch offset.
- Play Action `1821689211` no delay, pointing towards Random Container `2393951905`, full body SHA-256
  `5f4a3da7a272d283668687ca5cc137ce3cc3d1e7b9944ca2ccde2f95a6005d78`. The Action list for the Event `1581859410` released on hit changes from
  `(705609317,)` to `(705609317, 1821689211)`, with a new Event body SHA-256
  `a47d26b6238ffb6d0552bd9b3438dfb2cba86a15cc59a266d1f6d5b412ce7fa6`. The serialization order is two Sound → Random → New Action → Released on hit
  Event; the new Action belongs only to that Event. The hit explosion Event `1465516383` still only has the original Action `208572495`, and the miss Event `3115395173` remains unchanged.
- The original playback root `75663767` and parent chain `717111903→972300144→694534885` released on hit have no intersection with the original Bank's Stop targets `60034062`, `662442083`,
  `1054468797`, `956375262`, `599243561`, therefore the new Random does not add new Stops. It is not attached to the hit explosion Event `1465516383` or the miss
  Event `3115395173`; whether the same hit-release Event is called by other game paths must be re-tested in-game.
- Unit Set retains the existing Media/Sound/Action IDs derived from `wwise_fnv1("nanoha_wp07_wyrmstake_strike_flame_" + suffix)`; ACS Standby
  Media/Sound and Random Container IDs are derived from `wwise_fnv1("nanoha_wp07_wyrmstake_hit_release_" + suffix)`'s
  `acs_standby_media`/`acs_standby_sound`/`random_container` respectively. New IDs have been checked against the original Bank HIRC/Media, original WWEV Event IDs, and existing design IDs under the same
  owner to ensure no collisions. After merging all designs for the Shell Bank, the media count is `42→59`, HIRC object count is `181→226`, and HIRC payload is `11090→13246` (`+2156`) with `42` changed bytes. Other objects, audio, and non-DIDX/DATA/HIRC chunks of the original Bank remain byte-exact.

- The complete bodies SHA-256 of the two original Common Events are `92c0853b4112e8fe3e1a476d2225950c728ea8441e5014ee6d4083b6dbc89a80` and
  `0d24089543173b9f1f9a9200a11ab8e05169362751754b03483004a6d11e207c` respectively; the original Action body SHA-256 is
  `bc6d45828f7dba59fa6068d9aaf4420cb961a3765ee868c600384da0f3740e6b`,
  `f4c3e1d1071787fd47d9e83cf385309fac8b92f397164d50e4c83022487fde63`. The original routing in the table is for guard only; the original Event, Action, Container
  and media all remain byte-exact.
- ACS is appended to the Common Bank after the existing design media DIDX #46 as DIDX #47/Media `1484632890`, and Drive as DIDX #48/Media `3113081405`
  . The two standard Sounds are `1847466623`/`573906608` respectively, with DirectParentID `209038110`, PositioningParams `uByVector=0xC1`, and final 55-byte bodies
  SHA-256 as `56f69bfb7ca7002283351feba3c2beb81e6f19dabbdda69c0cc78078bcbd0a70`/
  `564dfecdf7e2054a3e86eea6f2768a8a31da359cb6c912d9c2bebd8c3e613fb6` respectively. The local Pitch base values for the two Sounds are default, with a random range of `(-50.0, 50.0)` cents, and do not modify their standard voice parents. Each uses a zero-latency Play Action `2004285408`/`551409861`
  and a single Action Event `1289400830`/`1358515313`; Sound → Action → Event serialization. No matching native Stop exists: the Common Bank has no
  Stop Action, and the targets of the two Stops in the structure Bank are not on the initial container or its parent chain, so no Stops are added.
- In the event structure Bank, the Action list of the original Event `1517840452` is `(446594426,)`, and its Action points to Switch `381232159`; the Event/Action
  body SHA-256 are `16fa0d520fed4ceb2268c3c208bcfd0fc7fefad2d271215c69a324ac6935fdfa`/
  `47c43eb3751fc1b5a0e984d2f2c0eee3bbb1ff65f82761db044581aa78579301` respectively. The three new wrapped Events are used only on explicit Motion requests, each having two exclusive
  PlayEvent Actions. The first calls the complete original Event and the second calls the voice Event in the Common Bank. Serialize both Actions before the wrapper Event. Each
  Action belongs to only one Event.

| Name | Wrapper Event ID | Original Event ID | Voice Event ID | Original PlayEvent Action ID | Voice PlayEvent Action ID |
|--------------------|---------------|-------------|---------------|------------------------|--------------------------|
| 144 startup | 2456922025    | 2798914977  | 1289400830    | 1727625947             | 1013300236               |
| 178/181 startup and 310 transition | 4272667772    | 1517840452  | 1289400830    | 1192238746             | 318061507                |
| 145/179/182 follow-up | 3413751962    | 2279772715  | 1358515313    | 2725269056             | 3159197441               |

- Original LMT is `original/lmt/w07_00.lmt`, v95. The seven Motions below each have an exclusive TIML and a ReqNo assignment at frame 0. Replace only the original request in the listed slot. Preserve all original trigger masks, frames, and other assignments.

| Name                   | LMT                       | Motion | EventGroup   | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|------------------------|---------------------------|--------|--------------|------|--------|----------|----------|------------|
| Diagonal shelling / Wide Sweep / Full Burst startup | `original/lmt/w07_00.lmt` | 144    | EventGroup06 | G    | 0      | 6456     | 6610     | 2          |
| Vertical startup | `original/lmt/w07_00.lmt` | 178    | EventGroup07 | A    | 0      | 6570     | 6611     | 1          |
| Horizontal startup | `original/lmt/w07_00.lmt` | 181    | EventGroup07 | A    | 0      | 6570     | 6611     | 1          |
| Transition after loading Wyrmstake Blast | `original/lmt/w07_00.lmt` | 310    | EventGroup07 | A    | 0      | 6570     | 6611     | 3          |
| Diagonal shelling / Wide Sweep / Full Burst follow-up | `original/lmt/w07_00.lmt` | 145    | EventGroup06 | H    | 0      | 6525     | 6612     | 1          |
| Vertical follow-up | `original/lmt/w07_00.lmt` | 179    | EventGroup06 | G    | 0      | 6525     | 6612     | 1          |
| Horizontal and direct Wyrmstake Blast follow-up | `original/lmt/w07_00.lmt` | 182    | EventGroup06 | G    | 0      | 6525     | 6612     | 1          |

- Motion 310 uses TIML offset `2689312`, frame count `59`, and trigger mask `0x01`. Add a guard for ReqNo assignment offset `2691488`. Original ReqNo `6570` expands to mode `100` and original Event `1517840452` in record #38 of `original/wwev/hm_wp07_snd_ev.wwev`, the same donor as for Motions 178 and 181. Redirect to existing ReqNo `6611`, WWEV record #48, and wrapper Event `4272667772`. The wrapper calls the complete original Event first, then ACS Event `1289400830` in the Common Bank. Add no WWEV records, HIRC objects, or media. Preserve Motion 310’s existing mute route for the vanilla character line at frame 53.
- The original character voice WWEV is `original/wwev/pl_voice.wwev`, v19. Each of the following 12 original `EventGroup02` triggers expands to one mode `4`
  character voice record. Replace only the assignments in these 12 exclusive TIMLs. The original ReqNos still play when reused by other Motions. Preserve the vanilla character voice Events and media and
  `original/nbnk/pl_act_vo_event.nbnk`. These reroutes leave lines already started by preceding actions playing.

| Name                             | LMT                       | Motion | EventGroup   | Slot | Assignment Frame | Original ReqNo | New ReqNo | Expected Trigger Frame |
|----------------------------------|---------------------------|-------:|--------------|------|-------:|---------:|---------:|-----------:|
| Diagonal shelling / Wide Sweep / Full Burst startup voice | `original/lmt/w07_00.lmt` |    144 | EventGroup02 | A    |      0 |     1129 |     6750 |         27 |
| Diagonal shelling / Wide Sweep / Full Burst follow-up voice 1 | `original/lmt/w07_00.lmt` |    145 | EventGroup02 | B    |      0 |     1105 |     6750 |         80 |
| Diagonal shelling / Wide Sweep / Full Burst follow-up voice 2 | `original/lmt/w07_00.lmt` |    145 | EventGroup02 | C    |      0 |     1019 |     6750 |        183 |
| Vertical startup voice | `original/lmt/w07_00.lmt` |    178 | EventGroup02 | A    |      0 |     1309 |     6750 |         19 |
| Vertical follow-up voice 1 | `original/lmt/w07_00.lmt` |    179 | EventGroup02 | B    |      0 |     1119 |     6750 |          2 |
| Vertical follow-up voice 2 | `original/lmt/w07_00.lmt` |    179 | EventGroup02 | A    |      0 |     1109 |     6750 |         68 |
| Vertical follow-up voice 3 | `original/lmt/w07_00.lmt` |    179 | EventGroup02 | C    |      0 |     1009 |     6750 |        176 |
| Horizontal startup voice | `original/lmt/w07_00.lmt` |    181 | EventGroup02 | A    |      0 |     1309 |     6750 |         34 |
| Horizontal/Wyrmstake Blast end character voice 1 | `original/lmt/w07_00.lmt` | 182 | EventGroup02 | B | 0 | 1119 | 6750 | 4 |
| Horizontal/Wyrmstake Blast end character voice 2 | `original/lmt/w07_00.lmt` | 182 | EventGroup02 | A | 0 | 1109 | 6750 | 65 |
| Horizontal/Wyrmstake Blast end character voice 3 | `original/lmt/w07_00.lmt` | 182 | EventGroup02 | C | 0 | 1009 | 6750 | 184 |
| Wyrmstake Blast transition character voice | `original/lmt/w07_00.lmt` | 310 | EventGroup02 | A | 0 | 1309 | 6750 | 53 |

- 7 selected Motion's `EventGroup02` parsable character voice triggers exactly at 12 in the table, where the original ReqNo/Event ID were `1129→2509923097`,
  `1105→365584827`, `1019→1121077459`, `1309→3262711103`, `1119→1510209164`, `1109→2158071957`, `1009→3779993687`. The above 12 are all
  animation frames within the Motion, not converted to seconds across Motions; original LMT assignment frames, trigger masks, other slots, and unselected routes remain byte-exact. The number of byte changes for each original request is
  `2`; after merging with existing designs, LMT `changed-byte count 21→46`, edit items `16→29`, length remains unchanged. The existing ACS/Drive rerouting at 7 in the builder must be preserved.
- Character voice WWEV is appended only after the existing #101/#102 as #103, a full clone of the original ReqNo `1409`/Event `967571325`/mode `4` single donor record, the original record
  SHA-256 `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507`; the new request `6750` points to the following silent-wrapped Event
  `2846173097`. New record SHA-256 `c44060757af7fe2b1ba1c5bc505e738d20342f68cd5754d7184283bca6432f00`, preserving the donor's command
  data, unknown bytes, and WWPC; the original WWEV record remains unchanged. The merged summary is record `100→103`, appending `387` bytes (this design adds `129` bytes).

| Name                 | WWEV                          | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | New ReqNo | New Event ID |
|----------------------|-------------------------------|------------:|---------------:|-----:|--------------------------------------------------------------------|---------:|------------:|
| Wyrmstake original character voice mute | `original/wwev/pl_voice.wwev` | 1409 | 967571325 | 4 | `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507` | 6750 | 2846173097 |

- Keep all media and HIRC already designed in the original Common Bank `wp_gun_cmn.nbnk`. According to `Event 3938800881` (empty Action list) →
  `PlayEvent Action 1604422970` (target is that empty Event) → `Event 2846173097` (the only Action is `1604422970`), append 3 objects in that order, without adding
  Sound/Media/Stop, and without replacing or deleting original voices. The three complete body SHA-256 are sequentially
  `21525a5823a2687ce13e25a0e09d58d97909bbf80da668325e915651bfcfc040`,
  `7ef8b289c598aab00f84deb221ff22cd47921220296f54848e173f257a172bb9`,
  `4685644e360014eb448b4937e8c353f5a9359e0d50dea3bb0e649baace7cca04`. `Event 2846173097` is entered only by the new WWEV request `6750`; the empty
  Event itself has no Action, so no character or weapon sounds are played.
- The above three Wwise IDs are derived from `wwise_fnv1("nanoha_wp07_wyrmstake_voice_mute_" + suffix)`'s `empty_event`/`play_empty_action`/
  `route_event`, and have undergone collision checks with `original/nbnk/`'s HIRC/Media ID, original WWEV Event ID, existing designs, and builder IDs; `6750` is also not used by the original
  WWEV/LMT. After merging the Common Bank, DIDX remains 48 items, HIRC objects `123→168`, payload `7250→9018`, changed-byte count is `41`,
  HIRC increment `+1768`; among the 42 newly added objects, only the Sound body of ACS/Drive adds a random Pitch attribute, all original HIRC objects remain unchanged; this design also additionally appends 3 mute objects. Aside from the originally declared DIDX/DATA/HIRC
  modifications, no other chunks are changed.
- Structural verification requires parsing all 12 Motion/ReqNo routes to `pl_voice.wwev`'s #103, then verifying the complete Action chain of the silent Event, the preservation of original voice and original weapon routing, and cross-
  Bank ID uniqueness;- Re-test the game for character voices and original weapon sounds for all directions and derivatives of normal Wyrmstake, Wyrmstake Blast, hit/miss, no-stake attempts, and other actions. Probe mute packets in these-filled test conditions are all
  `0/3` original human voices and weapon sounds normal; the baseline column was not tested, so this is-actual feedback supporting the mute range, not an equivalent to strict-controlled proof of random original voices.

- Original WWEV: `original/wwev/hm_wp07_snd_ev.wwev`, v19. Each donor ReqNo expands to only one record; full clone, preserving mode, unknown bytes, and all original records. New
  ReqNo has no conflicts in the original LMT/WWEV and existing builder.

| Name          | WWEV                                | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | New ReqNo | New Event ID |
|---------------|-------------------------------------|-------------|----------------|------|--------------------------------------------------------------------|----------|-------------|
| 144 starter | `original/wwev/hm_wp07_snd_ev.wwev` | 6456 | 2798914977 | 100 | `0cd7f3f60ba152c1d3a4e0ed7cba9c0256734fb9175fd7bcfff06cd5ed3202d7` | 6610 | 2456922025 |
| 178/181 starter and 310 connection | `original/wwev/hm_wp07_snd_ev.wwev` | 6570 | 1517840452 | 100 | `031bca6cf48747ae66243e53702d31b824a8a4fe4f01f7d31a9a2ed6476057b1` | 6611 | 4272667772 |
| End section | `original/wwev/hm_wp07_snd_ev.wwev` | 6525 | 2279772715 | 200 | `e60a91a79ea0e6c8488818862ab9ea9ade123cd9e8599668ec29b75fa0def7cb` | 6612 | 3413751962 |

- New records 6610/6611/6612 are respectively WWEV #47/#48/#49, full SHA-256 are respectively
  `318a4299d8c16e1450dfa072e3cfd9080f2de1c45b5a610289209bcb8dccc2db`/
  `94447d2580119dbb23821e040464b0e457b6e84eacabbc39ebb208dcea03f62a`/
  `c473b030f54c3b11d63f1dac581dda3a524eeb0c412f62bded65539a7ed15ecf`.
- All new Wwise/Media IDs are derived fixed from `wwise_fnv1("nanoha_wp07_wyrmstake_" + suffix)`, and undergo collision checks with the original Bank's HIRC/Media ID, the same
  owner's existing design's new IDs, and each other. New requests 6610–6612 have no conflicts with the original WWEV/LMT and existing builder.
- Common Bank media `33→48` items after merging with existing designs of the same owner, HIRC object `123→168`, payload `7250→9018`, changed-byte count `41`
  , HIRC increment `+1768`; only declared DIDX/DATA/HIRC changes are allowed. Structure Bank HIRC object `17385→17394`, payload `1789719→1789890`, only adds
  9 objects, original HIRC objects and BKHD remain completely unchanged. LMT merge summary changed-byte count `46` (ACS/Drive 7 items each 1 byte, Mute 12 items each 2
  bytes); weapon WWEV records `43→49`, merged append `774` bytes (this design 3 items each 129 bytes); character voice WWEV records `100→103`, merged append
  `387` bytes. Before delivery, joint verification of all cross-Bank Event targets, Action
  ownership, and full paths from requests to media must be performed, and re-tested in-game for loading, hit/miss, equal-weight random and continuous repetition of the two hit-release voices, synchronization with the original hit-release sound, Motion
  310 when the ACS is fully loaded, no firing after loading, and whether 310 repeats the ACS when triggered continuously with a normal starter.
