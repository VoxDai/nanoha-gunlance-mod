---
design_id: wp_gun_cmn.stationary_draw
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 原地拔刀

## 描述

保留原地普通攻击拔刀的原版机械音；在开始拔刀时追加一次 Raising Heart「Standby Ready, Set Up」语音，不污染其它拔刀方式或通用动作。

| 名称             | 动作或状态                       | 预期行为                                              |
|------------------|----------------------------------|-------------------------------------------------------|
| 原地普通攻击拔刀 | 收刀状态、不推方向并按普通攻击键 | 保留原声，开始拔刀时追加一次「Standby Ready, Set Up」 |
| 移动拔刀攻击     | 收刀状态、推动方向并按普通攻击键 | 不播放追加语音                                        |
| 防御拔刀         | 收刀状态下进入防御               | 不播放追加语音                                        |
| 其它铳枪动作     | 收刀、装填、磨刀或其它非目标动作 | 不播放追加语音                                        |

## 音频

| 名称                                   | 音频                                                                                                                                                       | 响度（LUFS-I） | 播放方式                                                                        |
|----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|---------------------------------------------------------------------------------|
| Raising Heart「Standby Ready, Set Up」 | [raising_heart_standby_ready](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_01(movie_1st.raising_heart.standby_ready_set_up.1).wav>) | -24 LUFS-I     | 追加独立媒体；第 9 帧与原版拔刀 Event 同时开始，使用标准语音 Sound 且不设 delay |

## 实现契约

- 原始 Bank: `original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，SHA-256
  `bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1`
- Bank ID: `939294496`

| 名称                 | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|----------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 原地拔刀（保留原声） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 267255962    | —           |
| 原地拔刀（追加语音） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 700212875   |

| 名称             | LMT                                         | Motion | EventGroup   | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------------------|---------------------------------------------|--------|--------------|------|--------|----------|----------|------------|
| 原地普通攻击拔刀 | `original/lmt/w07_00.lmt` | 2      | EventGroup06 | B    | 0      | 6470     | 6592     | 9          |

| 名称             | WWEV                                    | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | 新 ReqNo | 新 Event ID |
|------------------|-----------------------------------------|-------------|----------------|------|--------------------------------------------------------------------|----------|-------------|
| 原地普通攻击拔刀 | `original/wwev/hm_wp07_snd_ev.wwev` | 6470        | 3567942167     | 2    | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6592     | 3176129810  |

- LMT 固定为 v95，原文件 SHA-256 为 `7897e766963b177b2dc157f65204e8a4ef9a35aba4b294c8d0f0635209800b94`。Motion 2 共 91
  帧，TIML `0xC6E0` 仅由该 Motion 使用；以 trigger mask `0x02` 在第 9 帧触发槽 B。只允许将赋值帧 0、偏移
  `0xCC50` 的 ReqNo `6470` 改为 `6592`，文件长度不变且 changed-byte count 为 `1`。
- WWEV 固定为 v19，原文件 SHA-256 为 `82c7162f3cb502e3ce3e1e7c1e6ff4823d373a764148d6d761f675420bcd2a0f`。完整克隆第 17 条
  donor 记录并仅替换 ReqNo 和 Event ID；追加为第 44 条、增加 `129` 字节，原有 43 条记录、依赖字符串及 顺序保持 byte-exact。
- 新 Event `3176129810` 的 Action 列表固定为 `267255962, 708529406`：第一条为 PlayEvent，目标原 Event
  `3567942167`；第二条为 Play，目标新 Sound `700212875`。两条 Action 和新 Event 必须按 Wwise v120 加载顺序序列化在 原 Event
  `3567942167` 之前。
- 原有 DIDX #1–#33 保持 byte-exact；追加语音为 DIDX #34 / Media ID `863865614`。表中 donor `233981936` 仅作为原路径
  guard；新 Sound 使用 46-byte 标准语音 body，来源为 `original/nbnk/wp_cmn_epvsp.nbnk`（文件 SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media
  `838569492`（原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），仅替换
  Sound ID 与 Media ID，固定 `DirectParentID=209038110`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`；标准 body
  SHA-256 为 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 项目 WAV 固定为 48 kHz、stereo、24-bit PCM，并保持音频表记录的 -24 LUFS-I；构建时不做增益、归一化或响度修正，只无增益下混为
  48 kHz、16-bit mono Wwise PCM WEM。
- Bank 固定为 Wwise v120；本设计 HIRC 对象数由 123 增至 127，payload 由 7250 增至 7363 字节，changed-byte count 为
  `0`、payload 增量为 `+113`。与 `overhead_smash`、`reload` 合并后对象数为 `133`、payload 为 `7554`，changed-byte count
  为 `1`。不 resize、删除或修改任何原始 HIRC 对象；除 DIDX、DATA 和上述新 HIRC 对象外，其它 Bank 内容保持 byte-exact。
- Event `3176129810`、Action `267255962` / `708529406`、Sound `700212875` 与 Media `863865614` 沿用
  `fbb22171` 中的稳定 `wwise_fnv1()` ID，已通过原 Bank 全部 Media/HIRC ID 碰撞检查；ReqNo `6592` 在现有 1300 个 WWEV
  文件中未占用。端到端读回必须只产生 Motion 2 / 第 9 帧 / EventGroup06 / 槽 B / ReqNo `6592` / mode `2` / Event
  `3176129810` 一条新路由。
