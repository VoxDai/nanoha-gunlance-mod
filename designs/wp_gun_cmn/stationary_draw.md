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

| 名称                                   | 音频                                                                                                                                                    | 播放方式                                                                     |
|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| Raising Heart「Standby Ready, Set Up」 | [raising_heart_standby_ready](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_01(movie_1st.raising_heart.standby_ready_set_up.1).wav>) | 追加独立媒体；第 9 帧与原版拔刀 Event 同时开始，使用本地 2D 定位且不设 delay |

## 实现契约

- 原始 Bank: `original/nbnk/wp_gun_cmn.nbnk`
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
- 原有 DIDX #1–#33 保持 byte-exact；追加语音为 DIDX #34 / Media ID `863865614`。新 Sound 克隆 donor
  `233981936`，仅替换 Sound ID 和媒体引用，并将 body `+0x2A` 的 `PositioningParams.uByVector` 从 `0xC0` 改为
  `0xC1`；不设 delay，保留其余输出、父级和 Aux 属性。
- Bank 固定为 Wwise v120；HIRC 对象数由 123 增至 127，payload 由 7250 增至 7389 字节，changed-byte count 为
  `1`。不 resize、删除或修改任何原始 HIRC 对象；除 DIDX、DATA 和上述 HIRC 变化外，其它 Bank 内容保持 byte-exact。
- Event `3176129810`、Action `267255962` / `708529406`、Sound `700212875` 与 Media `863865614` 沿用
  `fbb22171` 中的稳定 `wwise_fnv1()` ID，已通过原 Bank 全部 Media/HIRC ID 碰撞检查；ReqNo `6592` 在现有 1300 个 WWEV
  文件中未占用。端到端读回必须只产生 Motion 2 / 第 9 帧 / EventGroup06 / 槽 B / ReqNo `6592` / mode `2` / Event
  `3176129810` 一条新路由。
