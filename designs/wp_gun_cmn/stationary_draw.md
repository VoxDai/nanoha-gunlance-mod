---
design_id: wp_gun_cmn.stationary_draw
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 原地拔刀

## 描述

保留原地普通攻击拔刀的原版机械音；第 9 帧从六份 Raising Heart「Standby Ready」语音中等权随机播放一份，避免同一角色连续播放同一份，每次由专属 Container 施加 ±50 cents 随机音调偏移。

| 名称             | 动作或状态                       | 预期行为                                              |
|------------------|----------------------------------|-------------------------------------------------------|
| 原地普通攻击拔刀 | 收刀状态、不推方向并按普通攻击键 | 第 9 帧保留原声，随机追加一份 Standby Ready 语音 |
| 连续原地拔刀 | 同一角色再次原地普通攻击拔刀 | 每次从六份中等权随机，允许连续选中同一份；每次重新随机音调 |
| 移动拔刀攻击     | 收刀状态、推动方向并按普通攻击键 | 不播放追加语音                                        |
| 防御拔刀         | 收刀状态下进入防御               | 不播放追加语音                                        |
| 其它铳枪动作     | 收刀、装填、磨刀或其它非目标动作 | 不播放追加语音                                        |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|----------------|----------|
| Standby Ready 01（Set Up） | [raising_heart_standby_ready_01](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_01(movie_1st.raising_heart.standby_ready_set_up.1).wav>) | -24 LUFS-I | 独立媒体，权重 50000；六份共用一个随机 Container，每次仅播放一份 |
| Standby Ready 02 | [raising_heart_standby_ready_02](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_02(movie_1st.raising_heart.standby_ready_01.1).wav>) | -24 LUFS-I | 独立媒体，权重 50000；允许连续重复 |
| Standby Ready 03 | [raising_heart_standby_ready_03](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_03(movie_1st.raising_heart.standby_ready_02.1).wav>) | -24 LUFS-I | 独立媒体，权重 50000；允许连续重复 |
| Standby Ready 04 | [raising_heart_standby_ready_04](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_04(movie_1st.raising_heart.standby_ready_03.1).wav>) | -24 LUFS-I | 独立媒体，权重 50000；允许连续重复 |
| Standby Ready 05 | [raising_heart_standby_ready_05](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_05(movie_1st.raising_heart.standby_ready_04.1).wav>) | -24 LUFS-I | 独立媒体，权重 50000；允许连续重复 |
| Standby Ready 06 | [raising_heart_standby_ready_06](<../../audio/wp_gun_cmn/stationary_draw/raising_heart_standby_ready_06(movie_1st.raising_heart.standby_ready_05.1).wav>) | -24 LUFS-I | 独立媒体，权重 50000；允许连续重复 |

六份最终 WAV 均已用恒定线性增益标准化至 -24 ±0.05 LUFS-I，保持 48 kHz、stereo、24-bit PCM 和原时长。
01–06 实测响度依次为 `-24.01, -24.03, -23.98, -24.02, -23.99, -23.99` LUFS-I，true peak 依次为
`-13.02, -13.72, -13.08, -13.72, -13.50, -13.74` dBTP，采样帧数依次为 `99000, 60000, 72000, 78000, 78000, 78000`。
播放与原版拔刀 Event 同时开始，不设 delay；Random Container 的 `avoid-repeat=0`，每次独立随机选择并允许连续重复。
构建只无增益下混为 48 kHz、16-bit mono Wwise PCM WEM，channel config `000001410000`，不在构建时修正响度。

## 实现契约

- 原始 Bank: `original/nbnk/wp_gun_cmn.nbnk`，Wwise v120
- Bank ID: `939294496`

| 名称                 | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|----------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 原地拔刀（保留原声） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 267255962    | —           |
| 原地拔刀（语音 01） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 700212875   |
| 原地拔刀（语音 02） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 776774097   |
| 原地拔刀（语音 03） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 3655378684  |
| 原地拔刀（语音 04） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 3336805367  |
| 原地拔刀（语音 05） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 1609904242  |
| 原地拔刀（语音 06） | 3567942167 | 1061269777   | 522283251    | 233981936 / 867938822  | #27 / 867938822    | 708529406    | 3412709805  |

| 语音 | DIDX / 新 Media ID |
|------|--------------------|
| 01 | #34 / 863865614 |
| 02 | #39 / 3899958096 |
| 03 | #40 / 1917220401 |
| 04 | #41 / 2922118034 |
| 05 | #42 / 3798249131 |
| 06 | #43 / 3222869860 |

- 原 Event `3567942167` 的 Action 列表固定为 `(1061269777,)`，原 Action 完整 body SHA-256 为
  `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a`，必须仍为无 delay Play，目标原 Container `522283251`。
  原 Sound `233981936` 的完整 body SHA-256 为 `708699420d9237c644f13919834d5f4374d67e29a94762dc1bc0b0b98e133186`。
- 新 Event `3176129810` 的 Action 列表固定为 `(267255962, 708529406)`：第一条为 PlayEvent，目标完整原 Event
  `3567942167`；第二条为无 delay Play，目标新 Random Container `847783544`。按六个 Sound（01–06）→ Random → 两条
  Action → 新 Event → 原 Event 的顺序序列化，保持 Wwise v120 加载顺序。
- Random 克隆原 Container `522283251`，83-byte donor body SHA-256 为
  `e47758895339f8a1e74a65b122921135b97edf7ee01ad69f5d2a388f66e1955d`；原 playlist 为 `((233981936, 50000),)`，
  avoid-repeat=`1`。新 children 和 playlist 按 01–06 的 Sound ID 排列，权重各为 `50000`，`avoid-repeat=0`。
  body `+0x0B` 父级由 `768813060` 改为 `209038110`；保留 donor 的 Random/Normal、Step、one-shot、禁用 transition、
  每次播放重置 playlist、global、无本地 Volume、无实例上限及其它未建模字段；
  局部 Pitch 基值缺省（0 cents），随机范围固定为 `(-50.0, 50.0)`。最终 143-byte body SHA-256 为
  `db3a22c71a5c29ad75d077c95b70a2b7f65f98b7c3940b4ba4c8fab2707a6644`。
- 原有 DIDX #1–#33 的身份与媒体载荷保持 byte-exact；保留既有语音 01 的 #34 和 ID，五份新媒体按 02–06 追加为 #39–#43。
  下砸、装填、横扫占用的 #35–#38、其音频和路线保持原样。
- 六个 Sound 使用 46-byte 标准语音 body，来源为 `original/nbnk/wp_cmn_epvsp.nbnk`（Bank ID `1149256632`）的 Sound `890667980` /
  Media `838569492`，原 body SHA-256 为 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。
  使用标准模板（SHA-256 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`），仅替换 Sound/Media ID
  和 `DirectParentID=847783544`，保持 body `+0x20` 的 `PositioningParams.uByVector=0xC1`；子 Sound 不设置本地 Pitch。
  该 Container → 标准语音 Sound 层级沿用横扫已确认的语音路由。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；其父级 `694534885`
  body SHA-256 为 `e55d7200a7e2df6833bc634f2b9f8518958cd882da9f18eb5f102f3a6c884bcb`。两级均无局部 Pitch，两个参考 Bank 不打入 Mod。
- 原生播放根及父链为 `522283251 → 768813060 → 972300144 → 694534885`；原 Bank 未发现原生 Event 引用的匹配 Stop Action，
  不新增 Stop，不改变原声的中断行为。
- 本设计独立增加 6 个 Sound、1 个 Random、2 个 Action、1 个 Event，HIRC 对象 `123→133`、payload `7250→7766`，
  增量 `+516`、changed-byte count `4`（新 Random 的父级）。与全部既有设计合并后媒体共 43 项，HIRC 对象
  `123→146`、payload `7250→8234`，总增量 `+984`、changed-byte count `9`。本设计不 resize、删除或修改任何原始 HIRC
  对象；合并后的唯一原对象扩长仍为 reload Event `3476627122` 的 body `12→16`。其它 Bank chunk 保持 byte-exact。
- Event `3176129810`、Action `267255962` / `708529406`、Sound `700212875` 与 Media `863865614` 保持既有稳定 ID。
  新 ID 使用 `wwise_fnv1("nanoha_wp_gun_cmn_stationary_draw_" + suffix)`：Container suffix 为 `random_container`，
  02–06 的 Sound/Media suffix 分别为 `standby_ready_<NN>_sound` / `standby_ready_<NN>_media`。所有新增 ID 已通过原 Bank
  全部 Media/HIRC 及已注册自定义 ID 的碰撞检查。

| 名称             | LMT                                         | Motion | EventGroup   | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------------------|---------------------------------------------|--------|--------------|------|--------|----------|----------|------------|
| 原地普通攻击拔刀 | `original/lmt/w07_00.lmt` | 2      | EventGroup06 | B    | 0      | 6470     | 6592     | 9          |

| 名称             | WWEV                                    | donor ReqNo | donor Event ID | mode | record SHA-256                                                     | 新 ReqNo | 新 Event ID |
|------------------|-----------------------------------------|-------------|----------------|------|--------------------------------------------------------------------|----------|-------------|
| 原地普通攻击拔刀 | `original/wwev/hm_wp07_snd_ev.wwev` | 6470        | 3567942167     | 2    | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6592     | 3176129810  |

- `original/lmt/w07_00.lmt` 固定为 v95。Motion 2 共 91
  帧，TIML `0xC6E0` 仅由该 Motion 使用；以 trigger mask `0x02` 在第 9 帧触发槽 B。只允许将赋值帧 0、偏移
  `0xCC50` 的 ReqNo `6470` 改为 `6592`，文件长度不变且 changed-byte count 为 `1`。
- `original/wwev/hm_wp07_snd_ev.wwev` 固定为 v19。完整克隆第 17 条
  donor 记录并仅替换 ReqNo 和 Event ID；追加为第 44 条、增加 `129` 字节，原有 43 条记录、依赖字符串及 顺序保持 byte-exact。
- ReqNo `6592` 保持既有值。端到端读回必须只产生 Motion 2 / 第 9 帧 / EventGroup06 / 槽 B / ReqNo `6592` / mode `2` /
  Event `3176129810` 一条新路由，并验证完整原声委托、六选一 Container、Pitch、每个 Sound 的父级和媒体，以及加载顺序。
  LMT/WWEV 构建契约保持原样，与既有设计合并后 LMT changed-byte count 为 `6`，WWEV 共 45 条记录、总追加 `258` 字节。
