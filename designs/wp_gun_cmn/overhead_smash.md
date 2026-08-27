---
design_id: wp_gun_cmn.overhead_smash
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 下砸

## 描述

保留普通地面下砸的全部原版机械、金属和挥动声；仅在该动作第 32 帧追加一次奈叶「Accel」，不污染上捞、横扫、装填、拔刀或其它砸击变体。

| 名称         | 动作或状态                              | 预期行为                                      |
|--------------|-----------------------------------------|-----------------------------------------------|
| 普通下砸     | 地面连段中的 `WP_07::STRIKE` / Action 83 | 保留全部原声，并从动作第 32 帧播放一次「Accel」 |
| 相邻地面动作 | 上捞、横扫、装填或普通拔刀              | 不播放「Accel」                               |
| 其它砸击变体 | 跳跃砸击、跳跃装填砸击或快速装填派生    | 不播放「Accel」                               |

## 音频

| 名称          | 音频                                                                                                                 | 响度（LUFS-I） | 播放方式                                                           |
|---------------|----------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------|
| 奈叶「Accel」 | [nanoha_accel](<../../audio/wp_gun_cmn/overhead_smash/nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav>) | -21 LUFS-I     | 追加独立媒体；第 32 帧无 delay 开始，以标准语音 Sound 播放且不随机 |

## 实现契约

- 原始 Bank: `original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`，SHA-256
  `bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1`。

| 名称                 | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|----------------------|------------|----------------|--------------|------------------------|--------------------|----------------|-------------|
| 下砸（保留完整原声） | 1129041389 | 948030399      | 968655714    | 959908164 / 554875117  | #13 / 554875117    | 2557911997     | —           |
| 下砸（追加语音）     | 1129041389 | 948030399      | 968655714    | 959908164 / 554875117  | #13 / 554875117    | 3750542142     | 1643477631  |

| 名称     | LMT                         | Motion | EventGroup   | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|----------|-----------------------------|--------|--------------|------|--------|----------|----------|------------|
| 普通下砸 | `original/lmt/w07_00.lmt` | 128    | EventGroup06 | F    | 0      | 6505     | 6593     | 32         |

| 名称     | WWEV                                      | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | 新 ReqNo | 新 Event ID |
|----------|-------------------------------------------|-------------|----------------|------|--------------------------------------------------------------------|----------|-------------|
| 普通下砸 | `original/wwev/hm_wp07_snd_ev.wwev` | 6505        | 1129041389     | 100  | `716e10c4bb841822f8d5b178580980d654f4367e5753403474bc8b50cfb7f2c8` | 6593     | 2866569635  |

- LMT 固定为 v95，原文件 SHA-256 为 `7897e766963b177b2dc157f65204e8a4ef9a35aba4b294c8d0f0635209800b94`。Motion 128
  共 199 帧，TIML `0xEF7C0` 仅由该 Motion 使用；只允许将 EventGroup06 槽 F 赋值帧 0、偏移 `0xF0510` 的 ReqNo
  `6505` 改为 `6593`，并仅在第 32 帧以 trigger mask `0x20` 触发。文件长度不变，本设计 changed-byte count 为 `1`；与
  `stationary_draw` 合并后累计 changed-byte count 为 `2`。
- WWEV 固定为 v19，原文件 SHA-256 为 `82c7162f3cb502e3ce3e1e7c1e6ff4823d373a764148d6d761f675420bcd2a0f`。完整克隆第 28
  条、大小 `129` 字节的 donor 记录，只替换 ReqNo 和 Event ID；在 `stationary_draw` 的第 44 条记录之后追加为第 45 条，原有 43
  条记录、依赖字符串及顺序保持 byte-exact。donor ReqNo `6505` 只有一条 WWEV 记录，不展开成对路径；ReqNo `6593` 在正式输入
  `original/wwev/hm_wp07_snd_ev.wwev` 中不存在，并由 `append_cloned_record()` 的碰撞 guard 锁定。
- 原 Event `1129041389` 的 Action 列表保持 `948030399`，原路由为 Action `948030399` → Container `968655714` →
  Sound `959908164` / Media `554875117`。新 Event `2866569635` 的 Action 列表固定为 `2557911997, 3750542142`：第一条为
  PlayEvent，委托完整原 Event；第二条为无 delay 的 Play，目标新 Sound `1643477631`。两条 Action 和新 Event 必须按 Wwise
  v120 加载顺序序列化在原 Event `1129041389` 之前。
- 原有 DIDX #1–#33 保持 byte-exact；在 `stationary_draw` 的 DIDX #34 之后追加语音为 DIDX #35 / Media ID
  `1280643898`。表中 donor `959908164` 及其 Container/Aux 只作为原路径 guard；新 Sound 使用 46-byte 标准语音 body，来源为
  `original/nbnk/wp_cmn_epvsp.nbnk`（文件 SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media `838569492`（原 body SHA-256
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），仅替换 Sound ID 与 Media ID，固定
  `DirectParentID=209038110`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`；标准 body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。新 Sound 不加入 donor Container。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 项目 WAV 固定为 48 kHz、stereo、24-bit PCM，并保持音频表记录的 -21 LUFS-I；构建时不做增益、归一化或响度修正，只无增益下混为
  48 kHz、16-bit mono Wwise PCM WEM。
- 本设计向 HIRC 新增 1 个 Sound、2 个 Action 和 1 个 Event，changed-byte count 为 `0`、payload 增量为 `+113`。与
  `stationary_draw` 合并后，DIDX 共 35 项，HIRC 对象数由 `123` 增至 `131`、payload 由 `7250` 增至 `7476`、累计
  changed-byte count 为 `0`；再与 `reload` 合并后 payload 为 `7554`、changed-byte count 为 `1`。除 DIDX、DATA 和新对象外，
  其它 Bank 内容保持 byte-exact。
- 新 Media `1280643898`、Sound `1643477631`、原 Event 委托 Action `2557911997`、语音 Action `3750542142` 与 Event
  `2866569635` 分别由 `nanoha_wp_gun_cmn_overhead_smash_accel_media`、`nanoha_wp_gun_cmn_overhead_smash_accel_sound`、
  `nanoha_wp_gun_cmn_overhead_smash_original_action`、`nanoha_wp_gun_cmn_overhead_smash_voice_action` 和
  `nanoha_wp_gun_cmn_overhead_smash_event` 的 `wwise_fnv1()` 值固定，已通过原 Bank 全部 Media/HIRC ID 及
  `stationary_draw` 已占用 ID 的碰撞检查。端到端读回必须只新增 Motion 128 / 第 32 帧 / EventGroup06 / 槽 F / ReqNo
  `6593` / mode `100` / Event `2866569635` 路由，并保留既有 Motion 2 / 第 9 帧 / ReqNo `6592` 路由。
