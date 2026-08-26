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

| 名称          | 音频                                                                                                                               | 播放方式                                                   |
|---------------|------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| 奈叶「Accel」 | [nanoha_accel](<../../audio/wp_gun_cmn/overhead_smash/nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav>) | 追加独立媒体；第 32 帧无 delay 开始，以本地 2D 播放且不随机 |

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
  条记录、依赖字符串及顺序保持 byte-exact。donor ReqNo `6505` 只有一条 WWEV 记录，不展开成对路径；ReqNo `6593` 已确认在
  `assets/chunk/` 的 1300 个 WWEV 中未占用。
- 原 Event `1129041389` 的 Action 列表保持 `948030399`，原路由为 Action `948030399` → Container `968655714` →
  Sound `959908164` / Media `554875117`。新 Event `2866569635` 的 Action 列表固定为 `2557911997, 3750542142`：第一条为
  PlayEvent，委托完整原 Event；第二条为无 delay 的 Play，目标新 Sound `1643477631`。两条 Action 和新 Event 必须按 Wwise
  v120 加载顺序序列化在原 Event `1129041389` 之前。
- 原有 DIDX #1–#33 保持 byte-exact；在 `stationary_draw` 的 DIDX #34 之后追加语音为 DIDX #35 / Media ID
  `1280643898`。新 Sound 克隆 donor `959908164`，保留 DirectParentID `968655714`、OverrideBusId `0`、声道、输出、
  `3015692424, 0, 0, 0` Aux 路由及其它属性，仅替换 Sound ID 和媒体引用，并将 body `+0x2A` 的
  `PositioningParams.uByVector` 从 `0xC0` 改为 `0xC1`；不新建 Container、不共享媒体、不参与 donor Container 的随机选择。
- 本设计向 HIRC 新增 1 个 Sound、2 个 Action 和 1 个 Event，changed-byte count 为 `1`、payload 增量为 `+139`。与
  `stationary_draw` 合并后，DIDX 共 35 项，HIRC 对象数由 `123` 增至 `131`、payload 由 `7250` 增至 `7528`、累计
  changed-byte count 为 `2`；除 DIDX、DATA、新对象和两个新 Sound 的定位字节外，其它 Bank 内容保持 byte-exact。
- 新 Media `1280643898`、Sound `1643477631`、原 Event 委托 Action `2557911997`、语音 Action `3750542142` 与 Event
  `2866569635` 分别由 `nanoha_wp_gun_cmn_overhead_smash_accel_media`、`nanoha_wp_gun_cmn_overhead_smash_accel_sound`、
  `nanoha_wp_gun_cmn_overhead_smash_original_action`、`nanoha_wp_gun_cmn_overhead_smash_voice_action` 和
  `nanoha_wp_gun_cmn_overhead_smash_event` 的 `wwise_fnv1()` 值固定，已通过原 Bank 全部 Media/HIRC ID 及
  `stationary_draw` 已占用 ID 的碰撞检查。端到端读回必须只新增 Motion 128 / 第 32 帧 / EventGroup06 / 槽 F / ReqNo
  `6593` / mode `100` / Event `2866569635` 路由，并保留既有 Motion 2 / 第 9 帧 / ReqNo `6592` 路由。
