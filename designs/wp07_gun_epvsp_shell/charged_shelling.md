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

保留三种炮击类型的原版蓄力、姿态调整与蓄力爆炸声；进入水平、斜上或垂直蓄力动作时立即叠加一次奈叶「Divine」，蓄力过程中调整炮口姿态不重复播放，实际完成蓄力炮击并爆炸时仍同步叠加一次奈叶「Buster」。每次 Divine 或 Buster 开始时，当前游戏对象上尚未结束的另一条语音在 50 ms 内线性淡出停止；新语音立即播放，允许淡出期间短暂重叠。

| 名称 | 动作或状态 | 预期行为 |
|------|------------|----------|
| 水平蓄力开始 | 任意炮击类型以水平姿态进入蓄力 | 保留原版动作起始声，在 Motion 132 第 1 帧额外播放一次「Divine」，同时将尚未结束的「Buster」在 50 ms 内淡出停止 |
| 斜上蓄力开始 | 任意炮击类型以斜上姿态进入蓄力 | 保留原版动作起始声，在 Motion 133 第 1 帧额外播放一次「Divine」，同时将尚未结束的「Buster」在 50 ms 内淡出停止 |
| 垂直蓄力开始 | 任意炮击类型以垂直姿态进入蓄力 | 保留原版动作起始声，在 Motion 134 第 1 帧额外播放一次「Divine」，同时将尚未结束的「Buster」在 50 ms 内淡出停止 |
| 蓄力姿态调整 | 蓄力中在水平、斜上、垂直姿态间双向切换 | 保留 Motion 139–142 的原声；同一次蓄力不再次播放「Divine」 |
| 扩散型蓄力炮击 | 完成蓄力并触发扩散型爆炸 | 保留原版爆炸声，同步额外播放一次「Buster」，同时将尚未结束的「Divine」在 50 ms 内淡出停止 |
| 放射型蓄力炮击 | 完成蓄力并触发放射型爆炸 | 保留原版爆炸声，同步额外播放一次「Buster」，同时将尚未结束的「Divine」在 50 ms 内淡出停止 |
| 通常型蓄力炮击 | 完成蓄力并触发通常型爆炸 | 保留原版爆炸声，同步额外播放一次「Buster」，同时将尚未结束的「Divine」在 50 ms 内淡出停止 |
| 蓄力中断 | 已触发蓄力后取消或被中断 | 不触发「Buster」；不额外发出 Stop，已开始的「Divine」自然结束 |
| 未蓄力炮击、空弹与其它动作 | 未进入蓄力或非蓄力炮击 | 不播放本设计的两条追加语音 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|----------------|----------|
| 奈叶「Divine」 | [nanoha_divine_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_divine_01(battle_of_aces.attack_004.1).wav>) | -21 LUFS-I | 追加独立媒体；Motion 132–134 第 1 帧播放，同一次蓄力仅一次且无 delay；「Buster」触发时以 50 ms 线性淡出停止；自身触发时同样停止上一条「Buster」 |
| 奈叶「Buster」 | [nanoha_buster_01](<../../audio/wp07_gun_epvsp_shell/charged_shelling/nanoha_buster_01(battle_of_aces.attack_004.2).wav>) | -21 LUFS-I | 追加独立媒体；三种蓄力爆炸 Event 共用一个 Sound，每次实际触发仅播放一次且无 delay；「Divine」触发时以 50 ms 线性淡出停止；自身触发时同样停止「Divine」 |

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
- 新 Event `3452820647` 的 Action 列表固定为 `(1005770249, 1603135794, 583060699)`：依次为委托完整原 Event
  `3567942167` 的 PlayEvent、停止 Buster 的 Stop，以及目标标准语音 Sound `3754878246` 的无 delay Play。
  按 Sound → 原声委托 Action → Divine Play Action → Buster Stop Action → 新 Event → 原 Event 的顺序序列化。
  原声委托、Divine Play Action 和新 Event 的完整 body SHA-256 依次为
  `c87314f918eb3d617c61c98cf8842b0132f85e688d3ad0e8d10da6d1d41bafca`、
  `b57a2ba89422dc92d69e34539937d1235313c73ca9e8c608f1ee46e9c7008357`、
  `8b7ff8b28d19faf22c944f4386e82c925c24bcd42c2d936e30b8fcc8ce3fbcdd`。
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
  Action；本设计按用户指定行为新增双向 Stop，不将其作为原生中断路由的克隆。
- Divine 路由单独向 `wp_gun_cmn.nbnk` 新增 1 个 Sound、3 个 Action、1 个 Event，HIRC 对象 `123→128`、payload
  `7250→7395`，增量 `+145`、changed-byte count 为 `0`。与该 Bank 的现有设计合并后媒体共 45 项、HIRC 对象
  `123→153`、payload `7250→8539`，总增量 `+1289`、changed-byte count 为 `21`；既有 reload Event
  `3476627122` 仍是唯一扩长的原对象。除 DIDX/DATA 追加和上述 5 个新对象外，本设计不改变该 Bank 的原对象或其它 chunk。

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
- 三个爆炸 Event 的 Action 列表固定为 `(116178715, 1426818832, 858972567)`、`(409203877, 1225287532, 4053288866)`、
  `(530572411, 728690884, 3259504927)`，原 Action 始终在第一项，Stop 在第二项，Buster Play 在第三项；三个新 Play Action 均无 delay，共用 Buster Sound
  `3489806140`，且必须序列化在对应 Event 之前。Buster 沿用标准 46-byte C1 语音 Sound，最终 body SHA-256 为
  `3e27cfd8fa85fccbbee66c9dfe80a86c15e49e863629f120500719054341797c`。
- 三条爆炸原播放根及父链分别为 `63659294`、`176125134`、`847665525`，随后汇入
  `717111903 → 972300144 → 694534885`。原 Bank 中由 Event 引用的 Stop Action 目标集合固定为
  `{60034062, 662442083, 1054468797, 956375262, 599243561}`，未命中上述播放根或父链，本设计另按用户指定行为为三个爆炸 Event 各新增一条停止 Divine 的独立 Stop Action。
- Buster 路由单独向原 Bank 新增 1 个 Sound 和 6 个 Action，扩长 3 个原 Event，HIRC 对象 `181→188`、payload
  `11090→11318`，增量 `+228`、changed-byte count 为 `3`。与 `full_burst`、`wyverns_fire` 合并后媒体 `42→50`、
  HIRC 对象 `181→206`、payload `11090→12079`，总增量 `+989`、changed-byte count 为 `17`。除 DIDX/DATA 追加、
  上述 7 个新对象及 3 个 Event 扩展外，其它 Bank chunk、原媒体和原 HIRC 对象保持 byte-exact。

| 名称 | Stop Event ID | 结构参考 Stop Action ID / target | scope | transition / fade | exceptions | 新 Stop Action ID | 新 Stop target |
|------|---------------|----------------------------------|-------|-------------------|------------|--------------------|-----------------|
| Divine 开始停止 Buster | 3452820647 | 743936681 / 60034062 | Game Object | 50 ms / Linear | 空 | 1603135794 | Buster Sound 3489806140（Bank 3273965928） |
| 放射型 Buster 停止 Divine | 1962814816 | 743936681 / 60034062 | Game Object | 50 ms / Linear | 空 | 1225287532 | Divine Sound 3754878246（Bank 939294496） |
| 通常型 Buster 停止 Divine | 2187565051 | 743936681 / 60034062 | Game Object | 50 ms / Linear | 空 | 728690884 | Divine Sound 3754878246（Bank 939294496） |
| 扩散型 Buster 停止 Divine | 3325567640 | 743936681 / 60034062 | Game Object | 50 ms / Linear | 空 | 1426818832 | Divine Sound 3754878246（Bank 939294496） |

- Stop 结构参考为 `original/nbnk/wp07_gun_epvsp_shell.nbnk` 的 Action `743936681`，完整 body SHA-256
  `137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd`；其原始 transition 为 200 ms。
  本设计显式构造 23-byte `0x0103 / Stop_E_O` body，保留该已核实布局：`bIsBus=0`、无 delay、仅显式
  `TransitionTime=50`、无随机属性、Linear（4）、空 exceptions；不修改参考 Action 或原生龙击炮的 200 ms Stop。
- 上表顺序对应的四条新 Stop body SHA-256 为
  `f33f2c36a8e9ec2278fe3c85950abe4b8163f58a1770404fed9e531a2b4ebb65`、
  `7e8d8ce0db11ffde1a86d83040ee5812dad92236b33609a912b36ef890268c51`、
  `f35bb797fa57be95f56310f8c2ab6e5d25bee71e19485095d816fe0c35a23e03`、
  `f8a9743e56e31058af5bff91c2ae436b5072e3e9a63eb7b16e4d6cba44dd4afe`。
  放射、通常、扩散三个最终 Event body SHA-256 依次为
  `a59647473c3e3247e95a1f33c97dbbcb25e26e08e22564fc5568a22f1a184f58`、
  `64930c51ee142a4c8083b4cf204699fb568442fbf46f9950568b24afa1fd0031`、
  `e2dd258b394519b4bc114983291092a50aa559a44217c958f224b9ce644172f5`。
- 每条 Action 只能归属一个 Event。三个爆炸 Event 共用 Buster Sound，但不得共用 Play 或 Stop Action。
  在每个爆炸 Event 的原序列位置，新增 Buster Play → 该 Event 的 Divine Stop → Event；原 HIRC 对象之间的顺序不变。
- 两个 Bank 显式声明上表四条跨 Bank Stop 边，分别绑定目标 Bank ID、Sound ID 和上文完整 Sound body SHA-256。
  单 Bank 检查不得放宽其它缺失引用；完整暂存 Bank 集合必须核对实际目标 Bank、唯一 Sound、body 哈希和媒体归属。
  不复制目标 Sound 或媒体到另一 Bank，不通过停止共享父级扩大范围；目标未播放时不影响新语音和原声。
- 四个 Stop ID 沿用独立 Action 实机测试包。其 FNV-1 名称前缀为
  `nanoha_test_charged_shelling_mutual_stop_`，上表顺序的后缀依次为
  `buster_action`、`divine_action`、`divine_normal_action`、`divine_wide_action`；名称保留以稳定已验证 ID。
  四个 ID 已与原版、参考、现有自定义 Bank/WWEV 和契约数值完成碰撞检查；已有测试定义是正式沿用，不分配新值。

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
  空弹和其它铳枪动作不播放本设计语音。两方向均要求目标语音尚未结束时，在新语音开始后 50 ms 内线性淡出，允许该淡出窗口内重叠；原声和其它语音不被停止。
  独立 Action 的零过渡测试已获用户确认可加载且蓄力炮击能 Stop；本次 50 ms 听感、Divine 停止上一发 Buster、
  三种类型与姿态的完整覆盖及多人隔离仍需游戏验收。不得把结构验证或既有零过渡反馈记作 50 ms 实机通过。
