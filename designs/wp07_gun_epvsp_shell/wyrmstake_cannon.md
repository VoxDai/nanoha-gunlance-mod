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

# 龙杭炮

## 描述

保留普通龙杭炮的原版机械声、伸出／插入声、命中／打空后的释放与爆炸声。在游戏探针验证的抬枪前入口叠加奈叶「ACS」，在插入后释放炮弹的入口叠加「Drive」，每个入口一次。起爆龙杭装填后直接发射先在 Motion 310 第 3 帧播放 ACS，再在共用后段 Motion 182 播放 Drive；310 的 ACS 出现在装填完毕时，即使尚未进入发射后段也会触发。龙杭动作自身触发的 12
处原版人物语音改走无播放内容的事件；普通龙杭命中并释放时，在命中释放音效 28 上叠加一次 Raising Heart 语音，从「Strike
Flame」与「ACS Standby」中等权随机选择。ACS、Drive 与命中释放语音每次播放时各自抽取 `-50` 至 `+50 cents`
的音调偏移；其他动作的人物语音及龙杭原版武器声音保持原样。龙杭输入前已开始播放的人物语音可能延续到动作中，不在本次改道范围内。

| 名称                             | 动作或状态                                       | 预期行为                                                                                                |
|----------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| 斜上炮击、横扫、全弹派生普通龙杭 | Motion 144 开始，抬枪前                          | 原版事件与 ACS 同步开始，随后进入 Motion 145 时播放 Drive                                               |
| 正上炮击派生普通龙杭             | Motion 178 开始，抬枪前                          | 原版事件与 ACS 同步开始，随后进入 Motion 179 时播放 Drive                                               |
| 水平炮击派生普通龙杭             | Motion 181 开始，抬枪前                          | 原版事件与 ACS 同步开始，随后进入 Motion 182 时播放 Drive                                               |
| 普通龙杭命中并释放               | 命中释放音效 28，随后是命中爆炸音效 40           | ACS、Drive 各一次；释放时等权随机追加一次「Strike Flame」或「ACS Standby」，40 保留原版爆炸声及静音规则 |
| 普通龙杭打空                     | 未命中释放音效 38，未触发命中爆炸音效 40         | ACS、Drive 各一次；不播放两条命中释放语音，保留原版打空声及静音规则                                     |
| 起爆龙杭装填后直接发射           | Motion 310 第 3 帧，随后进入 182                 | 装填完毕时播放 ACS；插入后释放时播放 Drive；310、182 中的原版人物语音静音                               |
| 其它起爆龙杭派生                 | 进入 310 或上述普通龙杭起手 Motion               | 每个实际触发的 ACS 入口各播放一次；进入后段时播放 Drive，原版人物语音静音                               |
| 无杭尝试                         | 进入起手但未进入实际释放后段                     | 起手播放 ACS；没有后段触发时不播放 Drive；已进入的龙杭 Motion 不触发原版人物语音                        |
| 非龙杭动作                       | 单独炮击、横扫／全弹后停止、普通装填、拔刀／收刀 | 不播放 ACS、Drive 或命中释放随机语音；原版人物语音保持原样                                              |

## 音频

| 名称                          | 音频                                                                                                                                                              | 响度（LUFS-I） | 播放方式                                                                                            |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| 奈叶「ACS」                   | [nanoha_acs_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/nanoha_acs_01(gears_of_destiny.attack_voice.attack_02.1).wav>)                                 | -21 LUFS-I     | 普通龙杭抬枪前或 Motion 310 装填完毕时，共用既有媒体／Event；每次触发单次播放，随机音调 `±50 cents` |
| 奈叶「Drive」                 | [nanoha_drive_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/nanoha_drive_01(gears_of_destiny.attack_voice.attack_02.2).wav>)                             | -21 LUFS-I     | 插入后释放入口追加独立媒体；无延迟，单次播放，随机音调 `±50 cents`                                  |
| Raising Heart「Strike Flame」 | [raising_heart_strike_flame_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/raising_heart_strike_flame_01(movie_2nd_as.raising_heart.strike_flame.1).wav>) | -24 LUFS-I     | 命中释放 Event 28 的随机候选之一；等权、无延迟、允许连续重复，继承 Container 的 `±50 cents`         |
| Raising Heart「ACS Standby」  | [raising_heart_acs_standby_01](<../../audio/wp07_gun_epvsp_shell/wyrmstake_cannon/raising_heart_acs_standby_01(movie_2nd_as.raising_heart.acs_standby.1).wav>)    | -24 LUFS-I     | 命中释放 Event 28 的随机候选之一；等权、无延迟、允许连续重复，继承 Container 的 `±50 cents`         |

ACS／Drive 两份最终 WAV 为 48 kHz、stereo、24-bit PCM，分别为 42000／43583 帧（0.875／0.907979 秒）。经用户确认以恒定增益调整后，实测响度分别为
-21.01／-21.04 LUFS-I，true peak 为 -14.09／-14.33 dBTP。构建时仅无增益下混为 48 kHz、16-bit mono Wwise PCM WEM（channel
config `000001410000`），不再校正响度。ACS 与 Drive 使用独立 Event、Action、Sound、Media，不随机选择音频文件，不互相延迟；两条
Sound 均以无本地 Pitch 基值和 `(-50.0, 50.0)` cents 局部随机范围独立变调。Strike Flame 为 54000 帧（1.125 秒），经用户确认以
+1.40 dB 恒定增益调整后实测 -24.00 LUFS-I、true peak -12.32 dBTP；最终 WAV 同为 48 kHz、stereo、24-bit PCM。ACS Standby 更新后为
78000 帧（1.625 秒），沿用用户已确认的 -24 LUFS-I 目标，以 +2.58 dB 恒定增益从 -26.58 LUFS-I 调整后实测 -24.00 LUFS-I、true
peak -10.13 dBTP；同为 48 kHz、stereo、24-bit PCM。两条命中释放 WAV 各使用独立 Media／Sound；构建时无增益下混为 48 kHz、16-bit
mono Wwise PCM
WEM（channel config `000001410000`）。两条 Sound 均无本地 Pitch，由共同的 Random Container 等权择一，`avoid-repeat=0`
，允许连续重复；Container 的本地 Pitch 基值缺省，随机范围 `(-50.0, 50.0)` cents。命中释放 Event 的新 Action 无
delay。原版武器声路由不继承自定义随机 Pitch。

## 实现契约

- 原始炮弹 Bank：`original/nbnk/wp07_gun_epvsp_shell.nbnk`，Wwise v120，Bank ID `3273965928`。命中释放、未命中释放和命中爆炸由同
  Bank 的独立原版 Event 管理；命中释放随机语音的命中判定不依赖这次 Motion 310 的 LMT 改道，不修改炮弹脚本。
- 原始 Common Bank：`original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`。原始事件结构 Bank：
  `original/nbnk/pl_wp_par_op_event_structure.nbnk`，Wwise v120，Bank ID `2944223826`，仅有 BKHD 与 HIRC，没有
  DIDX/DATA；必须保持这种 chunk 结构。标准语音 Sound donor 来自 `original/nbnk/wp_cmn_epvsp.nbnk`，Bank ID `1149256632`
  ，Sound `890667980`／Media `838569492`，46-byte donor body SHA-256
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 的
  Actor-Mixer `209038110` 锁定，body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；参考 Bank
  不打包。

| 名称                            | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID               | 新 Action ID | 新 Sound ID           |
|---------------------------------|------------|--------------|--------------|------------------------|----------------------------------|--------------|-----------------------|
| ACS，144 起手原路由             | 2798914977 | 193548488    | 564339955    | 890667980 / 838569492  | #28 / 970807803、#29 / 971330098 | 2004285408   | 1847466623            |
| Drive，145／179／182 后段原路由 | 2279772715 | 479984650    | 68493596     | 890667980 / 838569492  | #23 / 732840854                  | 551409861    | 573906608             |
| 随机语音，命中释放原路由        | 1581859410 | 705609317    | 75663767     | 151638268 / 629066097  | #28 / 629066097                  | 1821689211   | 38895430 / 1727570929 |

- 已确认的动作时间线为命中释放 DIDX #28／Media `629066097`（Sound `151638268` → Container `75663767` → Action `705609317` → Event `1581859410`），随后命中爆炸 DIDX #40／Media `932229979`（Sound `762689746` → Container `969725659` → Action `208572495` → Event `1465516383`）；打空独走 DIDX #38／Media `858252802`（Sound `835886265` → Container `1049048275` → Action `951626294` → Event `3115395173`）。三条原 Event 的 Action 列表均只有表述的原 Action。命中释放 Event／Action／Container／Sound 的原完整 body SHA-256 依次为 `5e098d73a0645fc0d81188cadafe728e3325fd9eda7c67230d85579676e9b26d`／`29045c6ed5c13a286828f7c6e351b3b75a6f8b781539a59861b0cde3aa700521`／`43f44064e18427629d77e5a482d03f415822739ce82b138d07a4372a74cfceb8`／`a1208fe2fdb8a16dd7ec60f1c904ff593922a5d6d06e892a19ea0bbe6192f8b5`。命中爆炸 Event／Action／Container／Sound 的原完整 body SHA-256 依次为 `2c7b630cdd0276e580e69fcbe8a751ff13f4faee6df765cf87887cdc75fd1962`／`62d140af4d2431b7da43e4ca08246271d73da2d2cc544b7d78bd8839c9452450`／`fa0dd955ba17db67bae2e17c57c5d3de804026a91803d54a3f85d54808bf133a`／`8470dd13a4e97610fe5de92d0c7b1a1c9ca6988ad2e49b6f5b57888593ccd821`；打空 Event／Action body SHA-256 为 `fe73b26bcad55501da8c1dcbc4298069cf4e3748d81e12589b61b203089b1340`／`d4e189a50744ef1b00b429df4ee15fc90e93a466089d139c4f519d2313e29c19`。爆炸 Event `1465516383` 和打空 Event `3115395173`、所有原 Action／Container／Sound／Media 保持 byte-exact。
- 在现有 DIDX #51 后依次追加 Strike Flame DIDX #52／Media `949600199` 与 ACS Standby DIDX #53／Media `938668400`。两个
  46-byte 标准语音 Sound 分别为 `38895430`、`1727570929`，从标准 donor Sound `890667980`／Media `838569492` 复制，仅替换
  Sound／Media ID 与 DirectParentID `2393951905`；`PositioningParams.uByVector=0xC1`，无本地 Pitch 或 Aux 变更。完整 body
  SHA-256 分别为 `05b6321f093b39b5a0ebd59c8bf0208b117680a6541d60eabd1d64868f38ca3b`、
  `ad97250dde54b4126721605eca752ca090b214d0ec40b135cf930ee07bd8528c`。
- Random Container `2393951905` 克隆同 Bank 原版 Container `58172267`；donor 为 83-byte body，SHA-256
  `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`，原 playlist `((46149961, 50000),)`、`avoid-repeat=1`
  、Random mode、本地 Pitch `(-50.0, 50.0)` cents。新 playlist 固定为 `((38895430, 50000), (1727570929, 50000))`，
  `avoid-repeat=0`，保留 donor 的 Random/Normal、one-shot、无 transition 和每次播放重置设置；父级从 `717111903` 改为标准语音
  Actor-Mixer `209038110`，本地 Pitch 基值缺省、随机范围仍为 `(-50.0, 50.0)` cents。最终 body 为 95 bytes，SHA-256
  `7a018ec43f7d5f17ff03bddb144b2f8237f5d04d108ecc04a5bf68b7045dd95c`。音调随机化只设置在 Container 上，两条 Sound
  不叠加第二次音调偏移。
- Play Action `1821689211` 无 delay，指向 Random Container `2393951905`，完整 body SHA-256
  `5f4a3da7a272d283668687ca5cc137ce3cc3d1e7b9944ca2ccde2f95a6005d78`。命中释放 Event `1581859410` 的 Action 列表由
  `(705609317,)` 变为 `(705609317, 1821689211)`，新 Event body SHA-256
  `a47d26b6238ffb6d0552bd9b3438dfb2cba86a15cc59a266d1f6d5b412ce7fa6`。序列化次序为两个 Sound → Random → 新 Action → 命中释放
  Event；新 Action 只属于该 Event。命中爆炸 Event `1465516383` 仍只有原 Action `208572495`，打空 Event `3115395173` 也保持原样。
- 命中释放原播放根 `75663767` 及父链 `717111903→972300144→694534885` 与本 Bank 原生 Stop 的目标 `60034062`、`662442083`、
  `1054468797`、`956375262`、`599243561` 无交集，因此新 Random 不新增 Stop。它不附加到命中爆炸 Event `1465516383` 或打空
  Event `3115395173`；是否由其它游戏路径调用同一命中释放 Event 须在游戏中复测。
- Strike Flame 既有 Media／Sound／Action ID 沿用 `wwise_fnv1("nanoha_wp07_wyrmstake_strike_flame_" + suffix)`；ACS Standby
  Media／Sound 与 Random Container ID 依次由 `wwise_fnv1("nanoha_wp07_wyrmstake_hit_release_" + suffix)` 的
  `acs_standby_media`／`acs_standby_sound`／`random_container` 派生。新增 ID 已与原版 Bank HIRC／Media、原 WWEV Event ID 和同
  owner 已有设计 ID 检查无碰撞。炮弹 Bank 合并全部设计后，媒体 `42→53` 项、HIRC 对象 `181→215`、payload `11090→12555`
  ，changed-byte count `32`、HIRC 增量 `+1465`；本次相对原单条 Strike Flame 方案追加一项媒体、一个 Sound、一个 Random，并将音调属性从
  Strike Flame Sound 移到 Random。原 Bank 的其它对象、音频和非 DIDX／DATA／HIRC chunk 保持 byte-exact。

- 原版两个 Common Event 的完整 body SHA-256 分别为 `92c0853b4112e8fe3e1a476d2225950c728ea8441e5014ee6d4083b6dbc89a80`、
  `0d24089543173b9f1f9a9200a11ab8e05169362751754b03483004a6d11e207c`；原 Action body SHA-256 分别为
  `bc6d45828f7dba59fa6068d9aaf4420cb961a3765ee868c600384da0f3740e6b`、
  `f4c3e1d1071787fd47d9e83cf385309fac8b92f397164d50e4c83022487fde63`。表中原路由仅作 guard，原 Event、Action、Container
  和媒体都保持 byte-exact。
- Common Bank 在既有设计媒体 DIDX #46 后追加 ACS 为 DIDX #47／Media `1484632890`，Drive 为 DIDX #48／Media `3113081405`
  。两条标准 Sound 分别为 `1847466623`／`573906608`，DirectParentID `209038110`，PositioningParams `uByVector=0xC1`，最终 55-byte body
  SHA-256 分别为 `56f69bfb7ca7002283351feba3c2beb81e6f19dabbdda69c0cc78078bcbd0a70`／
  `564dfecdf7e2054a3e86eea6f2768a8a31da359cb6c912d9c2bebd8c3e613fb6`。两条 Sound 的本地 Pitch 基值缺省，随机范围均为 `(-50.0, 50.0)` cents，不修改其标准语音父级。各自使用无延迟 Play Action `2004285408`／`551409861`
  和单 Action Event `1289400830`／`1358515313`；Sound → Action → Event 序列化。不存在相匹配的原生 Stop：Common Bank 没有
  Stop Action，结构 Bank 两个 Stop 的目标不在起手原容器及其父链上，因此不添加 Stop。
- 事件结构 Bank 中原 Event `1517840452` 的 Action 列表为 `(446594426,)`，其 Action 指向 Switch `381232159`；Event／Action
  body SHA-256 分别为 `16fa0d520fed4ceb2268c3c208bcfd0fc7fefad2d271215c69a324ac6935fdfa`／
  `47c43eb3751fc1b5a0e984d2f2c0eee3bbb1ff65f82761db044581aa78579301`。三个新包装 Event 只在明确的 Motion 请求上使用，每个有两个独占
  PlayEvent Action，第一项调用完整原 Event，第二项调用 Common Bank 的语音 Event。序列化顺序为两个 Action → 包装 Event；每个
  Action 仅归属于一个 Event。

| 名称               | 包装 Event ID | 原 Event ID | 语音 Event ID | 原 PlayEvent Action ID | 语音 PlayEvent Action ID |
|--------------------|---------------|-------------|---------------|------------------------|--------------------------|
| 144 起手           | 2456922025    | 2798914977  | 1289400830    | 1727625947             | 1013300236               |
| 178／181 起手与 310 衔接 | 4272667772    | 1517840452  | 1289400830    | 1192238746             | 318061507                |
| 145／179／182 后段 | 3413751962    | 2279772715  | 1358515313    | 2725269056             | 3159197441               |

- 原始 LMT：`original/lmt/w07_00.lmt`，v95。下表七个 Motion 的 TIML 均独占，ReqNo 赋值帧均为 0；只替换表中一个槽位的原请求，保留所有原触发掩码、帧和其它赋值。

| 名称                   | LMT                       | Motion | EventGroup   | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------------------------|---------------------------|--------|--------------|------|--------|----------|----------|------------|
| 斜上／横扫／全弹起手   | `original/lmt/w07_00.lmt` | 144    | EventGroup06 | G    | 0      | 6456     | 6610     | 2          |
| 正上起手               | `original/lmt/w07_00.lmt` | 178    | EventGroup07 | A    | 0      | 6570     | 6611     | 1          |
| 水平起手               | `original/lmt/w07_00.lmt` | 181    | EventGroup07 | A    | 0      | 6570     | 6611     | 1          |
| 起爆龙杭装填后衔接   | `original/lmt/w07_00.lmt` | 310    | EventGroup07 | A    | 0      | 6570     | 6611     | 3          |
| 斜上／横扫／全弹后段   | `original/lmt/w07_00.lmt` | 145    | EventGroup06 | H    | 0      | 6525     | 6612     | 1          |
| 正上后段               | `original/lmt/w07_00.lmt` | 179    | EventGroup06 | G    | 0      | 6525     | 6612     | 1          |
| 水平与起爆龙杭直发后段 | `original/lmt/w07_00.lmt` | 182    | EventGroup06 | G    | 0      | 6525     | 6612     | 1          |

- Motion 310 的 TIML offset `2689312`、frame count `59`、trigger mask `0x01`；新增受保护的 ReqNo 赋值 offset `2691488`，原 `6570` 在 `original/wwev/hm_wp07_snd_ev.wwev` 的 #38 展开为 mode `100`／原 Event `1517840452`，与 178／181 的 donor 相同。重定向到既有 ReqNo `6611`／WWEV #48／包装 Event `4272667772`，由该 Event 先调用完整原 Event，再调用 Common Bank ACS Event `1289400830`。不新增 WWEV 记录、HIRC 对象或媒体；Motion 310 现有第 53 帧原版人物语音静音路由保持原样。
- 原始人物语音 WWEV：`original/wwev/pl_voice.wwev`，v19。原版 `EventGroup02` 的下列 12 个触发均展开为一条 mode `4`
  的人物语音记录；只替换这 12 个独占 TIML 的请求赋值，其他 Motion 中复用的原 ReqNo 仍正常播放。原版人物语音 Event、媒体及
  `original/nbnk/pl_act_vo_event.nbnk` 均不修改。前置动作已经起播的语音不由这些请求改道停止。

| 名称                             | LMT                       | Motion | EventGroup   | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|----------------------------------|---------------------------|-------:|--------------|------|-------:|---------:|---------:|-----------:|
| 斜上／横扫／全弹起手人物语音     | `original/lmt/w07_00.lmt` |    144 | EventGroup02 | A    |      0 |     1129 |     6750 |         27 |
| 斜上／横扫／全弹后段人物语音 1   | `original/lmt/w07_00.lmt` |    145 | EventGroup02 | B    |      0 |     1105 |     6750 |         80 |
| 斜上／横扫／全弹后段人物语音 2   | `original/lmt/w07_00.lmt` |    145 | EventGroup02 | C    |      0 |     1019 |     6750 |        183 |
| 正上起手人物语音                 | `original/lmt/w07_00.lmt` |    178 | EventGroup02 | A    |      0 |     1309 |     6750 |         19 |
| 正上后段人物语音 1               | `original/lmt/w07_00.lmt` |    179 | EventGroup02 | B    |      0 |     1119 |     6750 |          2 |
| 正上后段人物语音 2               | `original/lmt/w07_00.lmt` |    179 | EventGroup02 | A    |      0 |     1109 |     6750 |         68 |
| 正上后段人物语音 3               | `original/lmt/w07_00.lmt` |    179 | EventGroup02 | C    |      0 |     1009 |     6750 |        176 |
| 水平起手人物语音                 | `original/lmt/w07_00.lmt` |    181 | EventGroup02 | A    |      0 |     1309 |     6750 |         34 |
| 水平／起爆龙杭直发后段人物语音 1 | `original/lmt/w07_00.lmt` |    182 | EventGroup02 | B    |      0 |     1119 |     6750 |          4 |
| 水平／起爆龙杭直发后段人物语音 2 | `original/lmt/w07_00.lmt` |    182 | EventGroup02 | A    |      0 |     1109 |     6750 |         65 |
| 水平／起爆龙杭直发后段人物语音 3 | `original/lmt/w07_00.lmt` |    182 | EventGroup02 | C    |      0 |     1009 |     6750 |        184 |
| 起爆龙杭直发前过渡人物语音       | `original/lmt/w07_00.lmt` |    310 | EventGroup02 | A    |      0 |     1309 |     6750 |         53 |

- 7 个所选 Motion 的 `EventGroup02` 可解析人物语音触发恰为表中 12 处，原 ReqNo／Event ID 分别为 `1129→2509923097`、
  `1105→365584827`、`1019→1121077459`、`1309→3262711103`、`1119→1510209164`、`1109→2158071957`、`1009→3779993687`。以上 12 处均为
  Motion 内的动画帧，不跨 Motion 换算秒数；原 LMT 赋值帧、触发 mask、其他槽位和未选路由保持 byte-exact。每处原请求的字节改动数均为
  `2`；与现有设计合并后 LMT `changed-byte count 21→46`、编辑项 `16→29`，长度不变。构建器中现有的 7 处 ACS／Drive 改道必须保留。
- 人物语音 WWEV 只在现有 #101／#102 之后追加 #103，完整克隆原 ReqNo `1409`／Event `967571325`／mode `4` 的单条 donor 记录，原记录
  SHA-256 `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507`；新请求 `6750` 指向下述无声包装 Event
  `2846173097`。新记录 SHA-256 `c44060757af7fe2b1ba1c5bc505e738d20342f68cd5754d7184283bca6432f00`，保留 donor 的 command
  data、未知字节和 WWPC；原 WWEV 记录不变。合并摘要为记录 `100→103`，追加 `387` bytes（本设计新增 `129` bytes）。

| 名称                 | WWEV                          | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | 新 ReqNo | 新 Event ID |
|----------------------|-------------------------------|------------:|---------------:|-----:|--------------------------------------------------------------------|---------:|------------:|
| 龙杭原版人物语音静音 | `original/wwev/pl_voice.wwev` |        1409 |      967571325 |    4 | `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507` |     6750 |  2846173097 |

- 原始 Common Bank `wp_gun_cmn.nbnk` 中已有设计的媒体与 HIRC 全部保持。按 `Event 3938800881`（空 Action 列表）→
  `PlayEvent Action 1604422970`（目标为该空 Event）→ `Event 2846173097`（唯一 Action 为 `1604422970`）的顺序追加 3 个对象，不添加
  Sound／Media／Stop、不替换或删除原语音。三个完整 body SHA-256 依次为
  `21525a5823a2687ce13e25a0e09d58d97909bbf80da668325e915651bfcfc040`、
  `7ef8b289c598aab00f84deb221ff22cd47921220296f54848e173f257a172bb9`、
  `4685644e360014eb448b4937e8c353f5a9359e0d50dea3bb0e649baace7cca04`。`Event 2846173097` 只由新 WWEV 请求 `6750` 进入；空
  Event 本身没有 Action，故不播放任何人物或武器声音。
- 上述三个 Wwise ID 由 `wwise_fnv1("nanoha_wp07_wyrmstake_voice_mute_" + suffix)` 的 `empty_event`／`play_empty_action`／
  `route_event` 派生，已与 `original/nbnk/` 的 HIRC／Media ID、原 WWEV Event ID 和现有设计及构建器 ID 碰撞检查；`6750` 也未被原版
  WWEV/LMT 使用。Common Bank 合并后 DIDX 仍为 48 项、HIRC 对象 `123→168`、payload `7250→9018`、changed-byte count 为 `41`
  ，HIRC 增量 `+1768`；现有 42 个新增对象中仅 ACS／Drive 的 Sound body 增加随机 Pitch 属性，全部原 HIRC 对象不变；本设计还额外追加 3 个静音对象。除原已声明的 DIDX/DATA/HIRC
  修改外，不改动其它 chunk。
- 结构验证需将全部 12 个 Motion/ReqNo 路由解析到 `pl_voice.wwev` 的 #103，再验证无声 Event 的完整 Action 链、原语音与原武器路由保留性、跨
  Bank ID 唯一性；游戏复测普通龙杭各方向及派生、起爆龙杭直发、命中／打空、无杭尝试、其它动作的人物语音和原版武器声音。探针静音包在这些条件的已填写测试中均为
  `0/3` 原版人声、武器声音正常；基线栏未测，故这属于支持静音范围的实测反馈，不等于对随机原版语音的严格对照证明。

- 原始 WWEV：`original/wwev/hm_wp07_snd_ev.wwev`，v19。各 donor ReqNo 均只展开为一条记录；完整克隆，保留 mode、未知字节及所有原记录。新
  ReqNo 在原始 LMT/WWEV 和现有 builder 中无冲突。

| 名称          | WWEV                                | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | 新 ReqNo | 新 Event ID |
|---------------|-------------------------------------|-------------|----------------|------|--------------------------------------------------------------------|----------|-------------|
| 144 起手      | `original/wwev/hm_wp07_snd_ev.wwev` | 6456        | 2798914977     | 100  | `0cd7f3f60ba152c1d3a4e0ed7cba9c0256734fb9175fd7bcfff06cd5ed3202d7` | 6610     | 2456922025  |
| 178／181 起手及 310 衔接 | `original/wwev/hm_wp07_snd_ev.wwev` | 6570        | 1517840452     | 100  | `031bca6cf48747ae66243e53702d31b824a8a4fe4f01f7d31a9a2ed6476057b1` | 6611     | 4272667772  |
| 后段          | `original/wwev/hm_wp07_snd_ev.wwev` | 6525        | 2279772715     | 200  | `e60a91a79ea0e6c8488818862ab9ea9ade123cd9e8599668ec29b75fa0def7cb` | 6612     | 3413751962  |

- 新记录 6610／6611／6612 依次为 WWEV #47／#48／#49，完整 SHA-256 分别为
  `318a4299d8c16e1450dfa072e3cfd9080f2de1c45b5a610289209bcb8dccc2db`／
  `94447d2580119dbb23821e040464b0e457b6e84eacabbc39ebb208dcea03f62a`／
  `c473b030f54c3b11d63f1dac581dda3a524eeb0c412f62bded65539a7ed15ecf`。
- 所有新 Wwise／Media ID 由 `wwise_fnv1("nanoha_wp07_wyrmstake_" + suffix)` 固定派生，并与原版 Bank 的 HIRC／Media ID、同
  owner 现有设计新增 ID 及彼此进行碰撞检查。新请求 6610–6612 经原版 WWEV/LMT 与现有 builder 检查无冲突。
- 合并同 owner 已有设计后的 Common Bank 媒体 `33→48` 项，HIRC 对象 `123→168`，payload `7250→9018`，changed-byte count `41`
  、HIRC 增量 `+1768`；只允许声明的 DIDX/DATA/HIRC 变化。结构 Bank HIRC 对象 `17385→17394`，payload `1789719→1789890`，只添加
  9 个对象，原 HIRC 对象和 BKHD 完全不变。LMT 合并摘要 changed-byte count `46`（ACS／Drive 7 项各 1 byte，静音 12 项各 2
  bytes）；武器 WWEV 记录 `43→49`，合并追加 `774` bytes（本设计 3 项各 129 bytes）；人物语音 WWEV 记录 `100→103`，合并追加
  `387` bytes。交付前须联合验证全部跨 Bank Event 目标、Action
  归属、请求到媒体的完整路径，并在游戏中复测加载、命中／打空、两条命中释放语音的等权随机和连续重复、与原版命中释放声的同步、Motion
  310 装填完毕时的 ACS、装填后不发射，以及 310 与普通起手连续触发时是否重复播放 ACS。
