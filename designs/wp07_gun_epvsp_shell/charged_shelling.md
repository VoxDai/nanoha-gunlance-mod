---
design_id: wp07_gun_epvsp_shell.charged_shelling
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 蓄力炮击

## 描述

保留三种炮击类型的原版蓄力、姿态调整与蓄力爆炸声；进入水平、斜上或垂直蓄力动作时立即等概率随机叠加两条奈叶「Divine」之一，蓄力过程中调整炮口姿态不重复播放，实际完成蓄力炮击并爆炸时同步等概率随机叠加三条「Buster」之一。钩爪武器攻击插枪后的炮击也共用这一组 Buster。两阶段独立选择，允许连续重复且不绑定素材来源；每次播放产生
±50 cents 随机音调偏移。每次 Divine 或 Buster 开始时，当前游戏对象上尚未结束的对侧语音在 50 ms 内线性淡出停止；新语音立即播放，允许淡出期间短暂重叠。关闭三种类型、三个方向的普通炮击与蓄力完成后发射时的原人物“哼”声；保留全部原武器音效，不改动蓄力开始时的声音，也不补回普通炮击人物语音。

| 名称                       | 动作或状态                             | 预期行为                                                                                                       |
|----------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------------------|
| 水平蓄力开始               | 任意炮击类型以水平姿态进入蓄力         | 保留原版动作起始声，在 Motion 132 第 1 帧额外播放一次「Divine」，同时将尚未结束的「Buster」在 50 ms 内淡出停止 |
| 斜上蓄力开始               | 任意炮击类型以斜上姿态进入蓄力         | 保留原版动作起始声，在 Motion 133 第 1 帧额外播放一次「Divine」，同时将尚未结束的「Buster」在 50 ms 内淡出停止 |
| 垂直蓄力开始               | 任意炮击类型以垂直姿态进入蓄力         | 保留原版动作起始声，在 Motion 134 第 1 帧额外播放一次「Divine」，同时将尚未结束的「Buster」在 50 ms 内淡出停止 |
| 蓄力姿态调整               | 蓄力中在水平、斜上、垂直姿态间双向切换 | 保留 Motion 139–142 的原声；同一次蓄力不再次播放「Divine」                                                     |
| 扩散型蓄力炮击             | 完成蓄力并触发扩散型爆炸               | 保留原版爆炸声，同步额外播放一次「Buster」，同时将尚未结束的「Divine」在 50 ms 内淡出停止                      |
| 放射型蓄力炮击             | 完成蓄力并触发放射型爆炸               | 保留原版爆炸声，同步额外播放一次「Buster」，同时将尚未结束的「Divine」在 50 ms 内淡出停止                      |
| 通常型蓄力炮击             | 完成蓄力并触发通常型爆炸               | 保留原版爆炸声，同步额外播放一次「Buster」，同时将尚未结束的「Divine」在 50 ms 内淡出停止                      |
| 钩爪武器攻击炮击 | 插入怪物后实际触发炮击 | 保留原版爆炸声，使用同一 Buster 容器播放一次；插枪时保留原声 |
| 蓄力中断                   | 已触发蓄力后取消或被中断               | 不触发「Buster」；不额外发出 Stop，已开始的「Divine」自然结束                                                  |
| 连续独立蓄力与炮击         | 再次开始蓄力或实际爆炸                 | 每个阶段独立重新选择一条语音，Divine 各 50%，Buster 各 1/3，允许与上次相同；Divine 与 Buster 不绑定同一来源                  |
| 蓄力炮击发射人物语音 | 通常、放射、扩散型以水平、斜上或垂直方向完成蓄力并发射 | 原人物“哼”声静音；原武器音效及本设计 Buster 保持不变 |
| 普通炮击 | 三种类型、三个方向的未蓄力炮击 | 原人物“哼”声静音，保留原武器音效；不补回人物语音，不新增 Divine/Buster |
| 空弹与其它动作 | 空弹、全弹发射及其它铳枪动作 | 不播放本设计追加语音；保持各动作既有声音设计，不扩大人物静音范围 |

## 音频

| 名称      | 音频                                                                                                                                    | 响度（LUFS-I） | 播放方式                                                                                                              |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------|
| Divine 01 | [nanoha_divine_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_divine_01(battle_of_aces.attack_04.1).wav>)                | -21 LUFS-I     | 独立追加媒体，权重 50000（50%）；与 Divine 02 共用 Random，Motion 132–134 第 1 帧无 delay 选一条；停止对侧三份 Buster |
| Divine 02 | [nanoha_divine_02](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_divine_02(gears_of_destiny.attack_voice.attack_04.1).wav>) | -21 LUFS-I     | 独立追加媒体，权重 50000（50%）；与 Divine 01 共享触发、随机音调和停止语义                                            |
| Buster 01 | [nanoha_buster_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_01(battle_of_aces.attack_04.2).wav>)                | -21 LUFS-I     | 独立追加媒体，权重 50000（1/3）；三条 Buster 共用 Random，三种爆炸 Event 无 delay 选一条；停止对侧两份 Divine        |
| Buster 02 | [nanoha_buster_02](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_02(gears_of_destiny.attack_voice.attack_04.2).wav>) | -21 LUFS-I     | 独立追加媒体，权重 50000（1/3）；与 Buster 01 共享触发、随机音调和停止语义                                            |
| Buster 03 | [nanoha_buster_03](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_03(movie_reflection.nanoha.excellion_buster.1).wav>) | -22 LUFS-I | 权重 50000（1/3），与 Buster 01／02 共享触发、随机音调和停止语义 |

五份最终 WAV 均为 48 kHz、stereo、24-bit PCM。前四份按上表顺序保留 42000／48000／60000／60000 帧 （0.875／1／1.25／1.25 秒），分别以恒定
-1.06／+1.03／-5.26／-6.20 dB 线性增益标准化到 -21 LUFS-I 目标； 最终实测为 -21.00／-20.95／-21.02／-21.00 LUFS-I，true peak 为
-12.54／-10.33／-16.29／-17.40 dBTP。新版 Buster 03 为 60000 帧（1.25 秒），实测 −21.97 LUFS-I、−11.41 dBTP。两组语音在对侧触发时均以 50 ms 线性淡出停止；每次仅播放一个候选，允许重复。构建只无增益下混为
48 kHz、16-bit mono Wwise PCM WEM，channel config
`000001410000`；不在构建时校正响度。

## 实现契约

- 动画与请求原件为 `original/lmt/w07_00.lmt`（LMT v95）、`original/wwev/hm_wp07_snd_ev.wwev` 和 `original/wwev/pl_voice.wwev`（均为 WWEV v19）。
- Divine 目标 Bank 为 `original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`。

| 名称             | Event ID         | 原 Action ID | Container ID           | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID             |
|------------------|------------------|--------------|------------------------|------------------------|--------------------|--------------|-------------------------|
| 蓄力开始原声委托 | 3452820647（新） | 1061269777   | 522283251              | 233981936 / 867938822  | #27 / 867938822    | 1005770249   | —                       |
| 蓄力开始 Divine  | 3452820647（新） | 1061269777   | 522283251 → 1153640130 | 233981936 / 867938822  | #27 / 867938822    | 583060699    | 3754878246 / 4035275377 |

- 原 Event `3567942167` 的 Action 列表固定为 `(1061269777,)`，原 Action 完整 body SHA-256 为
  `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a`，必须仍为无 delay Play，目标原 Container
  `522283251`。原 Sound `233981936` / Media `867938822`、DIDX #27 和原 Event 均保持 byte-exact。
- 新 Event `3452820647` 的 Action 列表固定为 `(1005770249, 1603135794, 85406655, 2076396906, 583060699)`：依次为委托完整原 Event
  `3567942167` 的 PlayEvent、依次停止 Buster 01／02／03，以及目标 Random `1153640130` 的无 delay Play。 按两个 Sound →
  Random → 原声委托 Action → 三个 Buster Stop Action → Divine Play Action → 新 Event → 原 Event 的顺序序列化。
  原声委托、Divine Play Action 和新 Event 的完整 body SHA-256 依次为
  `c87314f918eb3d617c61c98cf8842b0132f85e688d3ad0e8d10da6d1d41bafca`、
  `ac01f6c3c01f4b9870cf14af9c1f6614cc78fa2d2d1f01dcc16bed071da1be38`、
  `8e966f8f23233c1839a1f9a464e3e2a26eda29b3c457e30ddfbe7935ea3f5582`。
- Divine 01 沿用 Media `370615719`、Sound `3754878246` 和 Action `583060699`；Divine 02 使用 Media `3246372848`、 Sound
  `4035275377`。单独应用时两份 Media 依次追加为 DIDX #34–#35；与该 Bank 现有设计合并时为 #45–#46。 运行时媒体须读回为 48
  kHz、16-bit mono Wwise PCM，分别为 42000／48000 samples。
- Divine Random `1153640130` 克隆原 Container `570218704`，83-byte donor body SHA-256 为
  `be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427`，原 playlist `((647150707, 50000),)`、
  avoid-repeat=1。新 playlist 为 `((3754878246, 50000), (4035275377, 50000))`、avoid-repeat=0； 保留 one-shot
  Random/Normal、禁用 transition、每次播放重置；无本地 Volume 或实例上限。 body `+0x0B` 父级从 `768813060` 改为 `209038110`
  ，Pitch 基值缺省、随机范围 `(-50.0, 50.0)`。 最终 95-byte body SHA-256 为
  `40b6d65e0aa7f692932836ead31d07e91a63606975dd12d0be46389a4ca8a426`。
- 两个 Divine Sound 使用 `original/nbnk/wp_cmn_epvsp.nbnk` 的 Sound `890667980` / Media `838569492` 所提供的 46-byte
  标准语音 body；原 body SHA-256 为 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`，固定
  `DirectParentID=1153640130`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`；沿用项目已验证的 Container 语音层级。
  01／02 最终 Sound body SHA-256 分别为 `251b8841b03f2489535afa09e60afae689137fbc3249a0a60bab8cd7481e372d`、
  `047453c18d735292b6965b2dfb4e83b79803bf9311836232b60bad6a9da27b87`。子 Sound 无本地 Pitch、delay 或额外增益。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：Bank ID `3755575407`、Actor-Mixer `209038110` body SHA-256
  `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。原生播放根及父链为
  `522283251 → 768813060 → 972300144 → 694534885`，原 `wp_gun_cmn.nbnk` 未发现由 Event 引用且命中该链的 Stop
  Action；本设计按用户指定行为新增双向 Stop，不将其作为原生中断路由的克隆。
- Divine 路由单独新增 2 个 Sound、1 个 Random、5 个 Action、1 个 Event，HIRC 对象 `123→132`、payload
  `7250→7610`，增量 `+360`、changed-byte count 为 `4`。不含下述发射人物静音对象时，与该 Bank 现有设计合并后媒体共 46 项、HIRC 对象
  `123→157`、payload `7250→8754`，总增量 `+1504`、changed-byte count 为 `25`；既有 reload Event
  `3476627122` 仍是唯一扩长的原对象。除 DIDX/DATA 追加、上述 9 个新对象及下述 3 个静音对象外，本设计不改变该 Bank 的原对象或其它 chunk。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 普通与蓄力炮击发射人物静音包装 | 2825008231（新） | — | — | — | — | 3500432807 | — |
| 静音 PlayEvent 目标 | 3344928599（新） | — | — | — | — | — | — |

- 两个静音 Event 与 Action 均新增于 `original/nbnk/wp_gun_cmn.nbnk` 所构建的 Bank `939294496`。
  Event `2825008231` 的完整 Action 列表为 `(3500432807,)`；Action `3500432807` 为无 delay 的 13-byte PlayEvent，
  仅委托同 Bank 的零 Action Event `3344928599`，后者完整列表为 `()`。不新增媒体、Sound、Container、Play 或 Stop，
  不引用原人物 Event `281150953`，不修改原人物 Bank 或共享混音父级。静音路线没有可播放根，不增加对应 Stop。
- 序列化顺序固定为 Action `3500432807` → 零 Action Event `3344928599` → 包装 Event `2825008231` →
  原 Event `3567942167`；保持此前所有对象的相对顺序和 body 不变。三份完整 body SHA-256 依次为
  `373a8565c017faed8e9dbe7e0d0bc985c74f7fff140e96be452760fb387de9ed`、
  `b690ca747f5c2f83d75a560d068fbd86abaa6f20ce8a6eeacb4d669ce978277c`、
  `4d0ae624d720e9762e04c1e6bd78afb8045cd44b78d323fe32db3af2563ac1c5`。
- 静音路线独立新增 1 个 Action、2 个 Event：HIRC 对象 `123→126`、payload `7250→7298`，增量 `+48`，
  changed-byte count 为 `0`。连同本设计 Divine 路由单独应用为 `123→135`、`7250→7658`，增量 `+408`、
  changed-byte count 为 `4`；与 Common Bank 全部已注册设计合并后媒体为 49 项，HIRC 对象 `123→172`、
  payload `7250→9150`，总增量 `+1900`、changed-byte count 为 `49`。不改变 DIDX/DATA、既有媒体或其它 chunk。
- ReqNo `6608` 与三个静音 HIRC ID 沿用已实机测试的局部静音路线，不重新分配；已复核原版 8 个参考 Bank、
  当前 design／builder 数值及原版 WWEV 请求和 Event 均无冲突。此路线不需要跨 Bank PlayEvent API。

- Buster 目标 Bank 为 `original/nbnk/wp07_gun_epvsp_shell.nbnk`，Wwise v120，Bank ID `3273965928`。

| 名称                 | Event ID   | 原 Action ID | Container ID           | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID             |
|----------------------|------------|--------------|------------------------|------------------------|--------------------|--------------|-------------------------|
| 扩散型爆炸（Buster） | 3325567640 | 116178715    | 63659294 → 2510752860  | 264207839 / 93971960   | #4 / 93971960      | 858972567    | 3489806140 / 3928375835 / 690215586 |
| 放射型爆炸（Buster） | 1962814816 | 409203877    | 176125134 → 2510752860 | 220939954 / 693612246  | #33 / 693612246    | 4053288866   | 3489806140 / 3928375835 / 690215586 |
| 通常型爆炸（Buster） | 2187565051 | 530572411    | 847665525 → 2510752860 | 69557296 / 849663903   | #37 / 849663903    | 3259504927   | 3489806140 / 3928375835 / 690215586 |

- 原蓄力特效 Event `1308679810` 必须恢复并保持原 Action 列表 `(485858073,)`；其完整 Event / Action body SHA-256
  分别为 `09b397e743d362043c390fdbab88811990f9867b882cea25cd56b59053c19347`、
  `0cdb30628eca7abe5b4f19bf4f70c1b08d6d93b5291c4d0b5a3b9734606f7e07`。不得向该 Event 添加 Divine Action，Sound
  `3754878246`／`4035275377`、Media `370615719`／`3246372848`、Random `1153640130` 和 Action `583060699`
  只能存在于最终 `wp_gun_cmn.nbnk`。
- 原 Bank 的 42 份媒体及载荷保持 byte-exact；保留同 artifact owner 的全弹发射和龙击炮 DIDX #43–#49 及其顺序，Buster 01 追加为
  DIDX #50 / Media `1793121649`，02 为 #51 / Media `570980126`，03 追加为 #59 / Media `2785082779`，保留 #52–#58 的既有索引。单独应用时为 #43–#45。运行时三份媒体均须读回为 48
  kHz、16-bit mono Wwise PCM、60000 samples。
- 三个爆炸 Event 的 Action 列表固定为 `(116178715, 1426818832, 515837897, 858972567)`、
  `(409203877, 1225287532, 1287808358, 4053288866)`、`(530572411, 728690884, 1267644869, 3259504927)`； 原 Action 始终第一，停止
  Divine 01／02 居中，Buster Play 最后。三个 Play 均无 delay，共用 Random `2510752860`。 扩散／放射／通常 Play body SHA-256 分别为
  `0fe2ec6e037d63bc1a91eb264ff999ed2d1adf856a8604e181ac9f436c1f9a1d`、
  `878806e7a14fe72a5cb1ff69a7d60f5db611861c3032ac10c8fb67b299458989`、
  `f0fa0a8665a23264e891f26ddbe4335aed7815ae8afb6733e3e35feb46d64992`。
- Buster Random `2510752860` 克隆原 Container `58172267`，83-byte donor body SHA-256 为
  `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`，原 playlist `((46149961, 50000),)`、avoid-repeat=1。
  新 playlist 为 `((3489806140, 50000), (3928375835, 50000), (690215586, 50000))`、avoid-repeat=0；其余 Random 模式和 Pitch 与 Divine 相同。
  body `+0x0B` 父级从 `717111903` 改为 `209038110`。最终 107-byte body SHA-256 为
  `1d3240b0b6205ac132d53ddf81f7647375ae2c56a365e4c904d7819491862a33`。
- Buster Sound `3489806140`／`3928375835`／`690215586` 使用上述标准 46-byte C1 模板，DirectParentID 均为 `2510752860`， 子 Sound 无本地
  Pitch、delay 或额外增益。最终 body SHA-256 分别为
  `bbc603bac06e30ea54aa58de3b749e1d413c8275c2834a931e015b8835c7e06d`、
  `2e5a7e3eb467114ad41a2a742e5204f51a5dcf9bf45bc0a011f8c1a3cd8663a4`、
  `8851587d5cec37e5055865facfd818745aa344bf30ca4a001f5caea89b87bcf0`。
- 三条爆炸原播放根及父链分别为 `63659294`、`176125134`、`847665525`，随后汇入
  `717111903 → 972300144 → 694534885`。原 Bank 中由 Event 引用的 Stop Action 目标集合固定为
  `{60034062, 662442083, 1054468797, 956375262, 599243561}`，未命中上述播放根或父链，本设计按用户指定行为为每个爆炸 Event
  新增两条停止 Divine 候选的独立 Stop Action。
- Buster 路由单独新增 3 个 Sound、1 个 Random 和 9 个 Action，扩长 3 个原 Event，HIRC 对象 `181→194`、payload
  `11090→11628`，增量 `+538`、changed-byte count 为 `13`。与全部已注册设计合并后媒体 `42→59`、HIRC 对象
  `181→226`、payload `11090→13246`，总增量 `+2156`、changed-byte count 为 `42`。本设计除 DIDX/DATA 追加、上述 13 个新对象及 3 个
  Event 扩展外，其它 Bank chunk、原媒体和原 HIRC 对象保持 byte-exact。

| 名称                         | Stop Event ID | 结构参考 Stop Action ID / target | scope       | transition / fade | exceptions | 新 Stop Action ID | 新 Stop target                             |
|------------------------------|---------------|----------------------------------|-------------|-------------------|------------|-------------------|--------------------------------------------|
| Divine 开始停止 Buster       | 3452820647    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 1603135794        | Buster Sound 3489806140（Bank 3273965928） |
| 放射型 Buster 停止 Divine    | 1962814816    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 1225287532        | Divine Sound 3754878246（Bank 939294496）  |
| 通常型 Buster 停止 Divine    | 2187565051    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 728690884         | Divine Sound 3754878246（Bank 939294496）  |
| 扩散型 Buster 停止 Divine    | 3325567640    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 1426818832        | Divine Sound 3754878246（Bank 939294496）  |
| Divine 开始停止 Buster 02    | 3452820647    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 85406655          | Buster Sound 3928375835（Bank 3273965928） |
| 扩散型 Buster 停止 Divine 02 | 3325567640    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 515837897         | Divine Sound 4035275377（Bank 939294496）  |
| 放射型 Buster 停止 Divine 02 | 1962814816    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 1287808358        | Divine Sound 4035275377（Bank 939294496）  |
| 通常型 Buster 停止 Divine 02 | 2187565051    | 743936681 / 60034062             | Game Object | 50 ms / Linear    | 空         | 1267644869        | Divine Sound 4035275377（Bank 939294496）  |
| Divine 开始停止 Buster 03 | 3452820647 | 743936681 / 60034062 | Game Object | 50 ms / Linear | 空 | 2076396906 | Buster Sound 690215586（Bank 3273965928） |

- Stop 结构参考为 `original/nbnk/wp07_gun_epvsp_shell.nbnk` 的 Action `743936681`，完整 body SHA-256
  `137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd`；其原始 transition 为 200 ms。
  本设计显式构造 23-byte `0x0103 / Stop_E_O` body，保留该已核实布局：`bIsBus=0`、无 delay、仅显式
  `TransitionTime=50`、无随机属性、Linear（4）、空 exceptions；不修改参考 Action 或原生龙击炮的 200 ms Stop。
- 上表前四条 Stop body SHA-256 为
  `f33f2c36a8e9ec2278fe3c85950abe4b8163f58a1770404fed9e531a2b4ebb65`、
  `7e8d8ce0db11ffde1a86d83040ee5812dad92236b33609a912b36ef890268c51`、
  `f35bb797fa57be95f56310f8c2ab6e5d25bee71e19485095d816fe0c35a23e03`、
  `f8a9743e56e31058af5bff91c2ae436b5072e3e9a63eb7b16e4d6cba44dd4afe`。 后四条 Stop body SHA-256 依次为
  `a3e37d407b2de99b7f29088dc93127b5c02a5423a8c702196df2315edfa7b13d`、
  `528b713f34e7cadf416b2612ba9cc56a7813ad1f54409fcdcb4172610f114de7`、
  `6f9143c623e3e346b9a72f77961b896c8e67b70101113fac9ade4f8ddae9f051`、
  `e13eb2147999bf1de1e6e4b45a82ff8d241ee91ad564d1a34068f9fd4b2f9724`。
  Buster 03 Stop body SHA-256 为 `546bee5372b864ea27999bb884e4aa030466b7fda336e9629d9a2b89015bbacb`。
  放射、通常、扩散三个最终 Event body SHA-256 依次为
  `4785364970e4080e0ddbec1853ed77f428c4dabd1a73028b8a3ff6f9072f6214`、
  `a8a3fd311a313491b6b4871b35668004d7195b0ad9b64b26c3024f845d4cff24`、
  `8d8857c2dfce5ebc9121f055016074b8b131b98c624b344b8833c30860726dae`。
- 每条 Action 只能归属一个 Event。三个爆炸 Event 共用 Buster Random，但不得共用 Play 或 Stop Action。 先序列化三个 Sound →
  Random；在每个爆炸 Event 原序列位置插入两条 Divine Stop → Buster Play → Event；原 HIRC 对象之间顺序不变。
- 两个 Bank 显式声明上表九条跨 Bank Stop 边，分别绑定目标 Bank ID、Sound ID 和上文完整 Sound body SHA-256。
  单 Bank 检查不得放宽其它缺失引用；完整暂存 Bank 集合必须核对实际目标 Bank、唯一 Sound、body 哈希和媒体归属。
  不复制目标 Sound 或媒体到另一 Bank，不通过停止共享父级扩大范围；目标未播放时不影响新语音和原声。
- 前四个 Stop ID 沿用独立 Action 实机测试包。其 FNV-1 名称前缀为
  `nanoha_test_charged_shelling_mutual_stop_`，上表顺序的后缀依次为
  `buster_action`、`divine_action`、`divine_normal_action`、`divine_wide_action`；名称保留以稳定已验证 ID。
  四个 ID 已与原版、参考、现有自定义 Bank/WWEV 和契约数值完成碰撞检查；已有测试定义是正式沿用，不分配新值。
- 本次新增 ID 均由 `wwise_fnv1("nanoha_wp07_gun_epvsp_shell_charged_shelling_" + suffix)` 派生：
  `divine_02_media`／`divine_02_sound`／`divine_random_container` 为 `3246372848`／`4035275377`／`1153640130`；
  `buster_02_media`／`buster_02_sound`／`buster_random_container` 为 `570980126`／`3928375835`／`2510752860`；
  `buster_02_stop_action`、`divine_02_wide_stop_action`、`divine_02_long_stop_action`、`divine_02_normal_stop_action`
  为 `85406655`／`515837897`／`1287808358`／`1267644869`。已核实彼此唯一，且不与本地 original Bank 的 HIRC／Media 或现有
  design／builder 自定义 ID 碰撞。

- Buster 03 沿用钩爪旧独立路线的 Media `2785082779` 和 Sound `690215586`，两者仅在 shell Bank 定义。Stop `2076396906` 的派生后缀为 `buster_03_stop_action`，仅在 common Bank 定义。
- [钩爪武器攻击](../wp_gun_cmn/clutch_weapon_attack.md)只保留独立的拔枪语音。实测确认钩爪炮击会触发共享的 Buster 路由，三种炮型的覆盖范围分别实测验收。

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| 水平蓄力开始 | `original/lmt/w07_00.lmt` | 132 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| 斜上蓄力开始 | `original/lmt/w07_00.lmt` | 133 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| 垂直蓄力开始 | `original/lmt/w07_00.lmt` | 134 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| 水平普通／蓄力炮击发射人物静音 | `original/lmt/w07_00.lmt` | 101 | EventGroup02 | A | 0 | 1305 | 6608 | 5 |
| 斜上普通／蓄力炮击发射人物静音 | `original/lmt/w07_00.lmt` | 102 | EventGroup02 | A | 0 | 1305 | 6608 | 5 |
| 垂直普通／蓄力炮击发射人物静音 | `original/lmt/w07_00.lmt` | 103 | EventGroup02 | A | 0 | 1305 | 6608 | 5 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| 三种蓄力起始姿态共享 Divine | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6599 | 3452820647 |
| 普通／蓄力炮击发射人物静音 | `original/wwev/pl_voice.wwev` | 1409 | 967571325 | 4 | `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507` | 6608 | 2825008231 |

- `original/lmt/w07_00.lmt` 中 Motion 132 / 133 / 134 分别为 79 / 65 / 79 帧，TIML 分别位于
  `0xFE820` / `0x101280` / `0x1046A0`，均仅由自身 Motion 使用。只允许将 EventGroup06 槽 B 的赋值帧 0 请求由
  `6470` 改为 `6599`，请求位置分别为 `0xFEDF0` / `0x101850` / `0x104C70`；三者均以 trigger mask `0x02` 在第 1
  帧触发，单独 changed-byte count 为 `3`，文件长度不变。
- 姿态调整 Motion 139–142 均为 21 帧且使用独立 TIML；EventGroup06 槽 B 必须继续在第 1 帧以 trigger mask `0x02`
  触发原 ReqNo `6470`，不得改为 `6599`。端到端读回必须仅产生 Motion 132–134 三条 Divine 路由，姿态调整只解析到原
  Event `3567942167`。Divine 与现有 Motion 2、128、131、143 修改合并为 `9` 个变化字节，再加下述 Motion 101–103
  静音修改后，LMT changed-byte count 为 `15`；未声明的 Motion、TIML、赋值、触发与文件内容保持 byte-exact。
- Motion 101／102／103 原长度为 85／89／95 帧，TIML 分别位于十进制偏移 `603840`／`624896`／`645968`，
  均仅由自身 Motion 使用。只替换上表 EventGroup02/A 的赋值帧 0 请求，赋值位置分别为十进制偏移
  `606048`／`627200`／`648272`；保留第 5 帧触发和 mask `0x01`。使用 guarded 请求替换，不直接按文件偏移写入。
  三条请求各改变 2 字节，静音独立 changed-byte count 为 `6`，文件长度不变；本设计六条 LMT 修改单独合计为 `9`。
  原 ReqNo `1305` 唯一解析为 `pl_voice.wwev` #17、mode `4`、Event `281150953`；保留原记录不变，只改变这三个 Motion 的路由。
  端到端读回必须三条且仅三条 `Motion 101–103 → ReqNo 6608 → Event 2825008231`；所有未选请求保持原样，
  包括三者 EventGroup06/D 的 ReqNo `6460`、第 8 帧武器触发，以及 Motion 132–134、139–142 与下砸路线。
- `original/wwev/pl_voice.wwev` 的 donor ReqNo `1409` 唯一解析为原记录 #20、mode `4`、Event `967571325`、
  大小 `129` 字节，完整 raw hash 见上表。完整克隆，仅将 ReqNo／Event ID 改为 `6608`／`2825008231`；
  新记录 raw SHA-256 为 `2b21f2a836c096e164751adfcad860aa8f919fea0a857f11fa64ac4de40798c4`。
  单独应用时为 #101，记录 `100→101`、追加 `129` 字节；与下砸 ReqNo `6595` 的 #101 合并后追加为 #102，
  总记录 `100→102`、总追加 `258` 字节。原 100 条记录、四个依赖字符串、既有下砸记录、未知字段与边界全部保持 byte-exact，
  只允许更新记录计数及尾部追加。
- 普通炮击通常／放射／扩散 Event `2629885944`／`1888950507`／`192028055` 的 Action 列表保持
  `(667354318,)`／`(680466555,)`／`(511124205,)`；不添加人物补回 Action，也不改变普通或蓄力爆炸媒体。
- `original/wwev/hm_wp07_snd_ev.wwev` 的 ReqNo `6470` 唯一解析为原记录 #17、mode `2`、Event `3567942167`、大小
  `129` 字节及上表完整 raw hash。完整克隆该记录，只替换 ReqNo 和 Event ID；新增记录 raw SHA-256 为
  `0b6c6e87c3c78c669ac6bc6cd09112c54445e7bce5401380fc68e2fad136e8ee`。单独应用时追加为 #44；与现有 ReqNo
  `6592` / `6596` 记录合并时追加为 #46，记录总数 `43→46`、总追加 `387` 字节。原 43 条记录、四个依赖字符串、现有
  #44–#45、记录边界和顺序保持 byte-exact。
- Media `370615719`、Sound `3754878246`、Action `583060699` 沿用
  `wwise_fnv1("nanoha_wp07_gun_epvsp_shell_charged_shelling_" + suffix)` 的 `divine_01_media` / `divine_01_sound` /
  `divine_01_action`。新 Event `3452820647` 与原声委托 Action `1005770249` 分别由 suffix
  `divine_01_motion_start_event` / `divine_01_motion_start_original_action` 派生。Buster Media `1793121649`、Sound
  `3489806140` 与 Action `858972567` / `4053288866` / `3259504927` 分别沿用 `buster_01_media`、
  `buster_01_sound`、`buster_01_wide_action` / `buster_01_long_action` / `buster_01_normal_action`。ReqNo `6599` 和两个
  新 HIRC ID 已对原始 4550 个 NBNK、1300 个 WWEV 及现有自定义 ID 完成碰撞检查；Divine 三个稳定 ID 是对现有契约的迁移，
  不分配新值，并且在最终五个目标 artifact 中只能存在一次。
- 游戏内按描述表验收：覆盖三种炮击类型和三种初始炮口姿态；在一次蓄力中执行水平→斜上→垂直及反向多次调整，只允许首次进入
  蓄力时播放一次 Divine；蓄力取消不触发 Buster，连续两次独立蓄力各播放一次 Divine，三种爆炸各只追加一次 Buster，普通炮击、
  空弹和其它铳枪动作不播放本设计语音。普通与蓄力炮击分别覆盖三种类型、三个方向，发射时均不得出现原人物“哼”声；
  普通炮击不补回人声，也不播放 Divine/Buster。对照测试空弹、全弹、连续炮击、取消与姿态调整，确认静音不扩散且全部武器音效保留。
  既有局部静音实测覆盖三种类型的蓄力发射；普通炮击仅通常型三个方向已有实测，其它类型仍需验收，不能外推为通过。
  两方向均要求目标语音尚未结束时，在新语音开始后 50 ms 内线性淡出，允许该淡出窗口内重叠；除上述发射人物请求静音外，原声和其它语音不被停止。
  独立 Action 的零过渡测试已获用户确认可加载且蓄力炮击能 Stop；本次 50 ms 听感、Divine 停止上一发 Buster、
  两组全部候选组合、随机重复、±50 cents 听感、三种类型与姿态的完整覆盖及多人隔离仍需游戏验收。 不得把结构验证或既有零过渡反馈记作随机容器或
  50 ms 实机通过。
