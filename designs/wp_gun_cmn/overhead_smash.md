---
design_id: wp_gun_cmn.overhead_smash
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 下砸

## 描述

保留普通下砸与快速装填下砸的全部原版机械、金属和挥动声；每次从两份奈叶「Accel」中等概率随机播放一份，替换 Motion 131 与
Motion 128 的原版人物哼声，允许连续重复，每次由专属 Container 施加 ±50 cents 随机音调偏移。不在原第 32
帧重复追加语音，也不污染跳跃独立变体或其它人物语音。

| 名称         | 动作或状态                                     | 预期行为                                                                                                  |
|--------------|------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| 普通下砸     | 经 Motion 131 进入 `WP_07::STRIKE` / Action 83 | 第 14 帧不播放原版哼声，改为等概率随机播放一份「Accel」，音调随机偏移 ±50 cents；原版机械声保持不变       |
| 快速装填下砸 | Motion 128 的 `WP_07::STRIKE_QR` / Action 84   | 第 18 帧不播放原版哼声，改为等概率随机播放一份「Accel」，音调随机偏移 ±50 cents；第 32 帧只触发原版机械声 |
| 连续下砸     | 再次进入任一目标触发帧                         | 每次重新选择一份语音及音调偏移，允许连续选中同一份；不新增冷却或实例上限                                  |
| 原版机械声   | Motion 128 第 32 帧及普通下砸后续原路线        | 原版 Event、Container、Sound、媒体和播放时机保持不变，不提前或重复                                        |
| 跳跃独立变体 | 跳跃下砸与跳跃装填下砸                         | 保持原版，不因本设计新增「Accel」                                                                         |
| 其它人物语音 | 非 Motion 128/131 的攻击、受击、回避或其它动作 | 保持原版人物语音，不发生全局静音或替换                                                                    |

## 音频

| 名称     | 音频                                                                                                                                                          | 响度（LUFS-I） | 播放方式                                                                                   |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------------------------|
| Accel 01 | [nanoha_accel_01](<../../audio/wp_gun_cmn/overhead_smash/nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav>)                                       | -21 LUFS-I     | 追加独立媒体，权重 `50000`（50%）；两条下砸路线共用一个 Random Container，一次触发仅选一份 |
| Accel 02 | [nanoha_accel_02](<../../audio/wp_gun_cmn/overhead_smash/nanoha_accel_02(gears_of_destiny.attack_voice.attack_03.1+movie_2nd_as.nanoha.accel_shooter.1).wav>) | -21 LUFS-I     | 追加独立媒体，权重 `50000`（50%）；与 01 共用 Container，允许连续重复                      |

两份最终 WAV 统一至 `-21 ±0.05 LUFS-I`，保持 48 kHz、stereo、24-bit PCM，分别为 34000／48000 帧 （0.708333／1 秒）。01 保留原文件，实测
`-21.01 LUFS-I`、`-14.65 dBTP`；02 经恒定 `-0.76 dB` 线性增益标准化后， 实测 `-21.02 LUFS-I`、`-12.44 dBTP`。两条路线分别在
Motion 131 第 14 帧与 Motion 128 第 18 帧无 delay 播放一次， 替代原人物哼声。每次由 Container 产生 `[-50, +50] cents`
偏移，两个子 Sound 继承该偏移，不设置本地 Pitch。 构建时不做增益、归一化或响度修正，只无增益下混为 48 kHz、16-bit mono Wwise
PCM WEM，channel config `000001410000`。

## 实现契约

- 原始 Bank：`original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`。

| 名称                   | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID            | 新 Sound ID             |
|------------------------|------------|--------------|--------------|------------------------|--------------------|-------------------------|-------------------------|
| 下砸机械声（保持原版） | 1129041389 | 948030399    | 968655714    | 959908164 / 554875117  | #13 / 554875117    | —                       | —                       |
| 人物哼声替换为 Accel   | 2866569635 | —            | 1487507844   | 890667980 / 838569492  | 追加 #35、#44 / —  | 2176868439 / 3750542142 | 1643477631 / 3476329532 |
| 静音 PlayEvent 目标    | 971912882  | —            | —            | —                      | —                  | —                       | —                       |

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| 快速装填下砸人物语音 | `original/lmt/w07_00.lmt` | 128 | EventGroup02 | B | 0 | 1409 | 6595 | 18 |
| 普通下砸人物语音 | `original/lmt/w07_00.lmt` | 131 | EventGroup02 | A | 0 | 1409 | 6595 | 14 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| 两类下砸共享人物语音替换 | `original/wwev/pl_voice.wwev` | 1409 | 967571325 | 4 | `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507` | 6595 | 2866569635 |

- `original/lmt/w07_00.lmt` 固定为 v95。Motion 128
  共 199 帧，TIML `0xEF7C0` 仅由该 Motion 使用；只允许将 EventGroup02 槽 B 赋值帧 0、偏移 `0xF03C0` 的 ReqNo
  `1409` 改为 `6595`，并以 trigger mask `0x02` 在第 18 帧触发。Motion 131 共 23 帧，TIML `0xFC040` 仅由该 Motion
  使用；只允许将 EventGroup02 槽 A 赋值帧 0、偏移 `0xFC5A0` 的 ReqNo `1409` 改为 `6595`，并以 trigger mask
  `0x01` 在第 14 帧触发。两个 ReqNo 替换各改变 2 字节；与 `stationary_draw` 的 Motion 2 修改合并后，文件长度不变，累计
  `LmtEditSummary.changed_byte_count` 为 `5`；再计入既有 `wide_sweep` 的 Motion 143 修改后为 `6`，本次不增加 LMT 修改。
- Motion 128 的 EventGroup06 槽 F 必须保持原赋值帧 0 / ReqNo `6505`，并在第 32 帧以 trigger mask `0x20` 触发；不得再改为
  ReqNo `6593`。Motion 151 的 EventGroup02 槽 B / 第 18 帧 / ReqNo `1409` 同样保持原样，作为未扩散控制路线。
- `original/wwev/pl_voice.wwev` 固定为 v19。完整克隆第 20 条、大小 `129` 字节的 donor
  记录，只替换 ReqNo 与 Event ID，追加为第 101 条；新增记录 SHA-256 为
  `c430e117fad198b99f94187fc7ff7c3ca1140c1ae618ad306037c16d9f4a7ed6`。原有 100 条记录、四个依赖字符串、顺序及
  记录边界保持 byte-exact。donor ReqNo `1409` 唯一解析为 mode `4` / Event `967571325`；ReqNo `6595` 已在
  `assets/chunk/` 的 1300 个 WWEV、52816 条记录中确认零占用，并由 `append_cloned_record()` 的碰撞 guard 锁定。
- `original/wwev/hm_wp07_snd_ev.wwev` 固定为 v19。原记录 #28 / ReqNo `6505` / mode `100` /
  Event `1129041389` / 完整记录 SHA-256
  `716e10c4bb841822f8d5b178580980d654f4367e5753403474bc8b50cfb7f2c8` 必须保持 byte-exact；该 artifact 只允许 既有
  `stationary_draw` 追加 ReqNo `6592` 为记录 #44、`wide_sweep` 追加 ReqNo `6596` 为记录 #45，两者保持不变； 本设计不追加
  ReqNo `6593` 或任何记录。合并后仍为 45 条记录、总追加 `258` 字节。
- 原 Event `1129041389` 的 Action 列表保持 `(948030399,)`，原路由保持 Action `948030399` → Container
  `968655714` → Sound `959908164` / Media `554875117`，DIDX #13 身份及全部对象保持 byte-exact。新 Event
  `2866569635` 的 Action 列表固定为 `(2176868439, 3750542142)`：第一条 Action 是 `PlayEvent`，目标零 Action Event
  `971912882`；第二条 Action 是无 delay 的 Play，目标新 Random Container `1487507844`。静音 Event 的 Action 列表必须为 `()`
  ，不得包含
  Media、Sound、Container、Play 或 Stop 路由。实机已确认该静音前导可让 `pl_voice.wwev` 的 mode `4` 路由执行 Accel，同时不产生
  提前或重复的机械声；孤立的 `(3750542142,)` Event 会同时吞掉原人物哼声和 Accel，因此不得恢复为单 Action 结构。
- 静音前导 Action `2176868439` 的 13-byte body SHA-256 固定为
  `cae38dfc9dcbfac1472669624ad21db1b2354d3043423e58c5f6cb6fa72c7138`；静音 Event `971912882` 的 8-byte body SHA-256 固定为
  `7b80a7d5a9de0359f31a89f18cd167d2c4b8863a0b631f21a6207b3ee0e08b20`；最终 Event
  `2866569635` 的 16-byte body SHA-256 固定为
  `c48f67dfffd2c4da82f8c01b499831978d9affcf65d83b69abfb60b2c88cdd03`。指向 Random 的 Accel Play Action
  `3750542142` 为 18-byte body，SHA-256 为 `e8e1110f9c4918a32b395f1d0857e854c730816c9d4f8a511c4d597336251d82`。
  序列化顺序固定为标准语音 Sound `1643477631` → Sound `3476329532` → Random `1487507844` → Accel Play Action
  `3750542142` → 静音前导 Action `2176868439` → 静音 Event `971912882` → 人物语音 Event
  `2866569635` → 原机械 Event `1129041389`。旧的原机械 Event 委托 Action `2557911997` 不得创建；静音前导不得 引用原机械
  Event。
- 原有 DIDX #1–#33 的身份及媒体载荷保持 byte-exact；Accel 01 沿用 DIDX #35 / Media ID `1280643898`， Accel 02 在所有既有媒体之后追加为
  DIDX #44 / Media ID `1779645041`。`stationary_draw` 的 #34、#39–#43、
  `reload` 的 #36、`wide_sweep` 的 #37–#38 及其媒体顺序均保持不变，两条下砸路线共享这两份媒体。
- Random `1487507844` 克隆原 Container `570218704`，83-byte donor body SHA-256 为
  `be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427`。原 playlist 为 `((647150707, 50000),)`、
  avoid-repeat=`1`；新 children 顺序为 `(1643477631, 3476329532)`，playlist 固定为
  `((1643477631, 50000), (3476329532, 50000))`、avoid-repeat=`0`。body `+0x0B` 的父级由 `768813060` 改为
  `209038110`。保留 donor 的 Random/Normal、Step、one-shot、禁用 transition、每次播放重置 playlist、global、 无本地
  Volume、无实例上限及其它未建模字段；以 `HircPitchSettings(None, (-50.0, 50.0))` 为 guard 保留其 Pitch， 基础 Pitch
  缺省，随机范围为 `(-50.0, 50.0)`。最终 95-byte body SHA-256 为
  `14d8a2b8bc85006842ce55cc6be9a29941d92baee5047b3ce049baedabada0f8`。
- 两个新 Sound 均使用 46-byte 标准语音 body，来源为
  `original/nbnk/wp_cmn_epvsp.nbnk` 的 Sound `890667980` / Media
  `838569492`（原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），仅替换 Sound ID、Media
  ID 和父级，固定 `DirectParentID=1487507844`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`； 标准模板 body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。 Sound / Media 映射依次为
  `1643477631 / 1280643898`、`3476329532 / 1779645041`；最终 body SHA-256 依次为
  `6306b71c6ddbb1d3623c0eb203d5a8cc7d9fe0a9ae3554c42c78d44ea07d1d9a`、
  `b2d63396a981e857c8a5338700a95a251a84d9b9795cab4b48fc617ce59b77ea`。两者均无本地 Pitch，不叠加第二份随机偏移， 不加入原机械
  Container；沿用已验证的横扫 Container → 标准语音 Sound 层级。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；其父级 `694534885`
  body SHA-256 为 `e55d7200a7e2df6833bc634f2b9f8518958cd882da9f18eb5f102f3a6c884bcb`，两级均无局部 Pitch。 两个参考 Bank
  不打入 Mod。原人物语音 Event `967571325` 的两条 Play 根及父链为
  `123580933 → 390816861 → 694534885`、`1030793858 → 753306426 → 402681221 → 694534885`；连同标准外部父链
  `209038110 → 694534885`，在原人物语音 Bank、目标 Bank 和标准 Sound donor Bank 中均未发现原生 Event 引用的匹配 Stop
  Action，因此本设计不新增 Stop Action，不改变原声的中断行为。
- 内存原型中，本设计单独向 HIRC 新增 2 个 Sound、1 个 Random、2 个 Action 和 2 个 Event，对象 `123→130`、 payload `7250→7527`
  ，增量 `+277`，changed-byte count 为 `4`（新 Random 的父级修改），所有原 HIRC 对象保持 byte-exact。 替换当前已注册的单语音下砸契约后，本次净增加
  1 个 Sound、1 个 Random、1 份媒体，HIRC 增量 `+151`；与当前
  `stationary_draw`、`reload`、`wide_sweep` 合并后，DIDX 共 44 项，HIRC 对象 `123→148`、payload `7250→8394`， 累计
  changed-byte count 为 `21`、payload 增量为 `+1144`。该合并值以当前已注册 HIRC 增量 `+993`、 changed-byte count `17`
  为基线，加上本次独立原型差值；Event `3476627122` 仍仅由 reload 设计从 12 字节扩展至
  16 字节。除声明的 DIDX/DATA、新对象和 reload Event 扩展外，其它 Bank 内容保持 byte-exact。
- Media `1280643898`、Sound `1643477631`、Accel Action `3750542142` 与 Event `2866569635` 分别沿用
  `nanoha_wp_gun_cmn_overhead_smash_accel_media`、`nanoha_wp_gun_cmn_overhead_smash_accel_sound`、
  `nanoha_wp_gun_cmn_overhead_smash_voice_action` 和 `nanoha_wp_gun_cmn_overhead_smash_event` 的稳定
  `wwise_fnv1()` 值。静音前导 Action `2176868439` 沿用
  `nanoha_wp_gun_cmn_overhead_smash_silent_prime_action`，静音 Event `971912882` 沿用已实机验证探针的
  `nanoha_pl_act_vo_event_motion131_silent_event`。新增 Sound `3476329532`、Media `1779645041`、Random `1487507844`
  分别由 `wwise_fnv1("nanoha_wp_gun_cmn_overhead_smash_" + suffix)` 的 `accel_02_sound`、`accel_02_media`、
  `random_container` 派生；已对全部 `original/nbnk/` 的 Bank、Media、HIRC ID 及当前已注册自定义 ID 检查，三者互不重复且无碰撞。
  端到端读回必须
  恰好产生 Motion 128 / 第 18
  帧和 Motion 131 / 第 14 帧两条 ReqNo `6595` / mode `4` / Event `2866569635` 路由，同时保留 Motion 128 / 第 32 帧 /
  ReqNo `6505` / mode `100` / Event `1129041389` 的原机械路线及既有 Motion 2 / 第 9 帧 / ReqNo `6592`、 Motion 143 / 第
  11 帧 / ReqNo `6596` 路由，并验证两份媒体身份、等权 playlist、avoid-repeat=`0`、Pitch、父级和加载顺序。
- 实机按描述表验收：两类下砸均只在既定帧替换一次人物哼声，多次触发可听到两份 Accel 及轻微音调变化，允许同一份连续出现；
  原机械声、跳跃独立变体和其它人物语音保持原状。新双语音组合已完成结构验证，实机听感与加载行为在后续实现后验证。
