---
design_id: wp07_gun_epvsp_shell.charged_shelling
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 蓄力炮击

## 描述

保留三种炮击类型的原版蓄力、姿态调整与蓄力爆炸声；进入水平、斜上或垂直蓄力动作时立即叠加一次奈叶「Divine」，蓄力过程中调整炮口姿态不重复播放，实际完成蓄力炮击并爆炸时仍同步叠加一次奈叶「Buster」。

| 名称 | 动作或状态 | 预期行为 |
|------|------------|----------|
| 水平蓄力开始 | 任意炮击类型以水平姿态进入蓄力 | 保留原版动作起始声，在 Motion 132 第 1 帧额外播放一次「Divine」 |
| 斜上蓄力开始 | 任意炮击类型以斜上姿态进入蓄力 | 保留原版动作起始声，在 Motion 133 第 1 帧额外播放一次「Divine」 |
| 垂直蓄力开始 | 任意炮击类型以垂直姿态进入蓄力 | 保留原版动作起始声，在 Motion 134 第 1 帧额外播放一次「Divine」 |
| 蓄力姿态调整 | 蓄力中在水平、斜上、垂直姿态间双向切换 | 保留 Motion 139–142 的原声；同一次蓄力不再次播放「Divine」 |
| 扩散型蓄力炮击 | 完成蓄力并触发扩散型爆炸 | 保留原版爆炸声，同步额外播放一次「Buster」 |
| 放射型蓄力炮击 | 完成蓄力并触发放射型爆炸 | 保留原版爆炸声，同步额外播放一次「Buster」 |
| 通常型蓄力炮击 | 完成蓄力并触发通常型爆炸 | 保留原版爆炸声，同步额外播放一次「Buster」 |
| 蓄力中断 | 已触发蓄力后取消或被中断 | 不触发「Buster」；「Divine」不新增 Stop 路由并播放至结束 |
| 未蓄力炮击、空弹与其它动作 | 未进入蓄力或非蓄力炮击 | 不播放本设计的两条追加语音 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|----------------|----------|
| 奈叶「Divine」 | [nanoha_divine_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_divine_01(battle_of_aces.attack_004.1).wav>) | -21 LUFS-I | 追加独立媒体；Motion 132–134 第 1 帧播放，同一次蓄力仅一次且无 delay；不要求在「Buster」开始前播放完毕 |
| 奈叶「Buster」 | [nanoha_buster_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_01(battle_of_aces.attack_004.2).wav>) | -21 LUFS-I | 追加独立媒体；三种蓄力爆炸 Event 共用一个 Sound，每次实际触发仅播放一次且无 delay |

两份最终 WAV 均为 48 kHz、stereo、24-bit PCM。Divine 为 42000 帧（0.875 秒），以恒定 `-1.03 dB` 线性增益标准化后
实测为 `-20.98 LUFS-I`、`-12.51 dBTP`；Buster 为 54000 帧（1.125 秒），以恒定 `-5.49 dB` 线性增益标准化后实测为
`-21.01 LUFS-I`、`-16.52 dBTP`。构建只无增益下混为 48 kHz、16-bit mono Wwise PCM WEM，channel config
`000001410000`；不在构建时校正响度。

## 实现契约

- 动画与请求原件为 `original/lmt/w07_00.lmt`（LMT v95）和 `original/wwev/hm_wp07_snd_ev.wwev`（WWEV v19）。
- Divine 目标 Bank 为 `original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 蓄力开始原声委托 | 3452820647（新） | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 1005770249 | — |
| 蓄力开始 Divine | 3452820647（新） | 1061269777 | 522283251 | 233981936 / 867938822 | #27 / 867938822 | 583060699 | 3754878246 |

- 原 Event `3567942167` 的 Action 列表固定为 `(1061269777,)`，原 Action 完整 body SHA-256 为
  `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a`，必须仍为无 delay Play，目标原 Container
  `522283251`。原 Sound `233981936` / Media `867938822`、DIDX #27 和原 Event 均保持 byte-exact。
- 新 Event `3452820647` 的 Action 列表固定为 `(1005770249, 583060699)`：第一条为 PlayEvent，委托完整原 Event
  `3567942167`；第二条为无 delay Play，目标标准语音 Sound `3754878246`。按 Sound → 原声委托 Action → Divine Play
  Action → 新 Event → 原 Event 的顺序序列化。两个 Action 和新 Event 的完整 body SHA-256 依次为
  `c87314f918eb3d617c61c98cf8842b0132f85e688d3ad0e8d10da6d1d41bafca`、
  `b57a2ba89422dc92d69e34539937d1235313c73ca9e8c608f1ee46e9c7008357`、
  `0f68a177b5564488dbf983fc508e4525b34e1cee47ff8b40e8c2f0659a0793b5`。
- Divine 沿用 Media `370615719`、Sound `3754878246` 和 Action `583060699`。单独应用本设计时 Media 追加为
  `wp_gun_cmn.nbnk` DIDX #34；与该 Bank 的现有设计合并时追加为 DIDX #45。运行时媒体须读回为 48 kHz、16-bit mono
  Wwise PCM、42000 samples。
- Divine Sound 使用 `original/nbnk/wp_cmn_epvsp.nbnk` 的 Sound `890667980` / Media `838569492` 所提供的 46-byte
  标准语音 body；原 body SHA-256 为 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`，固定
  `DirectParentID=209038110`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`。最终 Sound body SHA-256 为
  `3fbe7ab23615d1874c72199690b960a83d8e82336f28250e0d81435d8fafae68`，无本地 Pitch、随机选择、delay 或额外增益。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：Bank ID `3755575407`、Actor-Mixer `209038110` body SHA-256
  `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。原生播放根及父链为
  `522283251 → 768813060 → 972300144 → 694534885`，原 `wp_gun_cmn.nbnk` 未发现由 Event 引用且命中该链的 Stop
  Action；Divine 明确播放至结束，因此不新增 Stop Action。
- Divine 路由单独向 `wp_gun_cmn.nbnk` 新增 1 个 Sound、2 个 Action、1 个 Event，HIRC 对象 `123→127`、payload
  `7250→7363`，增量 `+113`、changed-byte count 为 `0`。与该 Bank 的现有设计合并后媒体共 45 项、HIRC 对象
  `123→152`、payload `7250→8507`，总增量 `+1257`、changed-byte count 为 `21`；既有 reload Event
  `3476627122` 仍是唯一扩长的原对象。除 DIDX/DATA 追加和上述 4 个新对象外，本设计不改变该 Bank 的原对象或其它 chunk。

- Buster 目标 Bank 为 `original/nbnk/wp07_gun_epvsp_shell.nbnk`，Wwise v120，Bank ID `3273965928`。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 扩散型爆炸（Buster） | 3325567640 | 116178715 | 63659294 | 264207839 / 93971960 | #4 / 93971960 | 858972567 | 3489806140 |
| 放射型爆炸（Buster） | 1962814816 | 409203877 | 176125134 | 220939954 / 693612246 | #33 / 693612246 | 4053288866 | 3489806140 |
| 通常型爆炸（Buster） | 2187565051 | 530572411 | 847665525 | 69557296 / 849663903 | #37 / 849663903 | 3259504927 | 3489806140 |

- 原蓄力特效 Event `1308679810` 必须恢复并保持原 Action 列表 `(485858073,)`；其完整 Event / Action body SHA-256
  分别为 `09b397e743d362043c390fdbab88811990f9867b882cea25cd56b59053c19347`、
  `0cdb30628eca7abe5b4f19bf4f70c1b08d6d93b5291c4d0b5a3b9734606f7e07`。不得向该 Event 添加 Divine Action，Sound
  `3754878246`、Media `370615719` 和 Action `583060699` 只能存在于最终 `wp_gun_cmn.nbnk`。
- 原 Bank 的 42 份媒体及载荷保持 byte-exact；保留同 artifact owner 的全弹发射和龙击炮 DIDX #43–#49 及其顺序，Buster
  追加为 DIDX #50 / Media `1793121649`。运行时媒体须读回为 48 kHz、16-bit mono Wwise PCM、54000 samples。
- 三个爆炸 Event 的 Action 列表固定为 `(116178715, 858972567)`、`(409203877, 4053288866)`、
  `(530572411, 3259504927)`，原 Action 始终在第一项；三个新 Action 均为无 delay Play，共用 Buster Sound
  `3489806140`，且必须序列化在对应 Event 之前。Buster 沿用标准 46-byte C1 语音 Sound，最终 body SHA-256 为
  `3e27cfd8fa85fccbbee66c9dfe80a86c15e49e863629f120500719054341797c`。
- 三条爆炸原播放根及父链分别为 `63659294`、`176125134`、`847665525`，随后汇入
  `717111903 → 972300144 → 694534885`。原 Bank 中由 Event 引用的 Stop Action 目标集合固定为
  `{60034062, 662442083, 1054468797, 956375262, 599243561}`，未命中上述播放根或父链，因此 Buster 不新增 Stop Action。
- Buster 路由单独向原 Bank 新增 1 个 Sound 和 3 个 Action，扩长 3 个原 Event，HIRC 对象 `181→185`、payload
  `11090→11222`，增量 `+132`、changed-byte count 为 `3`。与 `full_burst`、`wyverns_fire` 合并后媒体 `42→50`、
  HIRC 对象 `181→203`、payload `11090→11983`，总增量 `+893`、changed-byte count 为 `17`。除 DIDX/DATA 追加、
  上述 4 个新对象及 3 个 Event 扩展外，其它 Bank chunk、原媒体和原 HIRC 对象保持 byte-exact。

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| 水平蓄力开始 | `original/lmt/w07_00.lmt` | 132 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| 斜上蓄力开始 | `original/lmt/w07_00.lmt` | 133 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |
| 垂直蓄力开始 | `original/lmt/w07_00.lmt` | 134 | EventGroup06 | B | 0 | 6470 | 6599 | 1 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| 三种蓄力起始姿态共享 Divine | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6599 | 3452820647 |

- `original/lmt/w07_00.lmt` 中 Motion 132 / 133 / 134 分别为 79 / 65 / 79 帧，TIML 分别位于
  `0xFE820` / `0x101280` / `0x1046A0`，均仅由自身 Motion 使用。只允许将 EventGroup06 槽 B 的赋值帧 0 请求由
  `6470` 改为 `6599`，请求位置分别为 `0xFEDF0` / `0x101850` / `0x104C70`；三者均以 trigger mask `0x02` 在第 1
  帧触发，单独 changed-byte count 为 `3`，文件长度不变。
- 姿态调整 Motion 139–142 均为 21 帧且使用独立 TIML；EventGroup06 槽 B 必须继续在第 1 帧以 trigger mask `0x02`
  触发原 ReqNo `6470`，不得改为 `6599`。端到端读回必须仅产生 Motion 132–134 三条 Divine 路由，姿态调整只解析到原
  Event `3567942167`。与现有 Motion 2、128、131、143 修改合并后，LMT changed-byte count 为 `9`；其它 Motion、TIML、
  赋值、触发与文件内容保持 byte-exact。
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
  不分配新值，并且在最终四件套中只能存在一次。
- 游戏内按描述表验收：覆盖三种炮击类型和三种初始炮口姿态；在一次蓄力中执行水平→斜上→垂直及反向多次调整，只允许首次进入
  蓄力时播放一次 Divine；蓄力取消不触发 Buster，连续两次独立蓄力各播放一次 Divine，三种爆炸各只追加一次 Buster，普通炮击、
  空弹和其它铳枪动作不播放本设计语音。允许 Divine 尾部与 Buster 重叠；结构验证不替代最终游戏触发与听感确认。
