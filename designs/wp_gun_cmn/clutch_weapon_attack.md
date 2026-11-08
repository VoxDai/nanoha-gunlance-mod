---
design_id: wp_gun_cmn.clutch_weapon_attack
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 钩爪武器攻击

## 描述

保留铳枪吸附怪物后的武器攻击原声，在起手拔枪和插枪时各追加一次奈叶语音。

| 名称 | 动作或状态 | 预期行为 |
|------|------------|----------|
| 起手蓄力 | 持械或收刀起始，吸附后执行武器攻击并拔枪 | 播放一次「Excellion」，保留原声 |
| 插枪 | 枪插入怪物，爆炸前 | 播放一次「Buster」，保留两条原声分支 |
| 插枪前中断 | 未进入插枪阶段 | 不触发「Buster」 |
| 其它动作 | 飞翔爪发射、龙击炮、骑乘终结、普通攻击及落地 | 保持既有声音行为 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|---------------|----------|
| 奈叶「Excellion」 | [nanoha_excellion_01](<../../audio/wp_gun_cmn/clutch_weapon_attack/nanoha_excellion_01(movie_reflection.nanoha.excellion_buster.1).wav>) | −24 | 起手追加一次，无延迟，独立随机 Pitch ±50 cents |
| 奈叶「Buster」 | [nanoha_buster_03](<../../audio/wp_gun_cmn/clutch_weapon_attack/nanoha_buster_03(movie_reflection.nanoha.excellion_buster.1).wav>) | −22 | 插枪第一分支追加一次，无延迟，独立随机 Pitch ±50 cents |

## 实现契约

两个 Bank 均为 Wwise v120。原始输入为 `original/nbnk/wp_gun_cmn.nbnk`（Bank ID `939294496`）和 `original/nbnk/pl_wp_par_op_event_structure.nbnk`（Bank ID `2944223826`）。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|-------------|--------------|------------------------|--------------------|-------------|-----------|
| 起手原声委托 | 146964709 → 3567942167 | 1061269777 | 522283251 | — | — | 1984195518 | — |
| 插枪原声委托 | 1767044258 → 1024101668 | 220419703 | 186074123 | — | — | 2910429509 | — |
| 插枪第二分支原声委托 | 3205911733 → 1080565533 | 29680933 | 9236354 | — | — | 2396863630 | — |
| Excellion | 146964709 → 2405966492 | — | — | 890667980 / 838569492 | #49 / — | 1423603563 → 1277608954 | 507956785 |
| Buster | 1767044258 → 3228545391 | — | — | 890667980 / 838569492 | #50 / — | 2515977290 → 1585582823 | 690215586 |

- 包装 Event 的 Action 列表依次为 `[1984195518,1423603563]`、`[2910429509,2515977290]`、`[2396863630]`。各 Action 使用无延迟 PlayEvent，按顺序在其所属 Event 前序列化。语音 Event 分别只含 Play Action `1277608954`、`1585582823`，在对应 Sound 和 Action 之后序列化。原版 Event 保持各自单 Action 列表及原始对象 body。
- 原版 Event / Action 完整 body SHA-256，按起手、插枪第一分支、插枪第二分支列出。

| Event ID | Event SHA-256 | Action SHA-256 |
|----------|---------------|----------------|
| 3567942167 | `cdf654b3ef9e93d51971da97cc9479fcfd85ad8baaa6923f1a94bb6784844f15` | `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a` |
| 1024101668 | `9e0727fd4f80e2a0410e6b26cb44565a62194e49011716232d2e07a68c460876` | `b5a74054bd5d85178c6129c3668a6ec8f211f897e40477b17d02a7a7901ad5c8` |
| 1080565533 | `27390d1f2a5a2a3356cd5eee0cdbafe1d9fa9f4d734a6f8fba0f469e5a8f193b` | `b156ed03e9878e9474778f313489e1f7c9d3ac905ba4cd8d30655e94ee780ebb` |

- 原版 Play 目标及父级分别为 `522283251 → 768813060`、`186074123 → 468342192`、`9236354 → 460803750`，各自继续指向 `972300144 → 694534885`。原版 Bank 中没有指向这些目标或父级的 Stop Action，本设计无新增 Stop。龙击炮原生停止链和 EPVSP 分流独立保留。
- 标准语音 donor 来自 `original/nbnk/wp_cmn_epvsp.nbnk`（Bank ID `1149256632`），原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。保留模板 C1 positioning 和 Aux，DirectParentID 为 `209038110`（`original/nbnk/pl_act_vo_event.nbnk`，Bank ID `3755575407`，Actor-Mixer body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`）。模板标准化后 SHA-256 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。仅替换 Sound/Media ID 并加入随机 Pitch `(-50.0, 50.0)`，无基础 Pitch 偏移。最终 Sound body SHA-256 分别为 `0b8d9f6f3c01e0f9f91234fc65954a1ec1db9f4f0c502577bd5f97dc28dfef8c`、`38a24e9f1761e74c1f7e02a400e890fb6ad966ec4989895805be414e9fff44ab`。
- 依次追加 Media `3631037616`、`2785082779`。48 kHz、双声道、24-bit PCM WAV 无增益下混为 48 kHz、16-bit、单声道 Wwise PCM WEM，channel config `000001410000`。原媒体保持 byte-exact，DIDX/DATA 仅有追加及重建所需的偏移和对齐变化。新增 ID 由 `wwise_fnv1("wp_gun_cmn_clutch_weapon_attack_" + suffix)` 派生，已检查 4550 个原版 NBNK 和 1300 个原版 WWEV 的占用。
- 本设计对 common Bank 新增 2 Sound、2 Action、2 Event，HIRC 增量 `+200`，合并后 `+1968`，随机 Pitch 使 changed-byte count 增加 `16`，合并后为 `57`。对结构 Bank 新增 5 Action、3 Event，HIRC 增量 `+149`，合并后 `+320`，changed-byte count 为 `0`。两者保留既有编辑与对象顺序，结构 Bank 的 BKHD 与所有原始 HIRC 对象 byte-exact。

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| 起手 | `original/lmt/w07_00.lmt` | 335 | EventGroup06 | F | 0 | 6470 | 6613 | 5 |
| 插枪 | `original/lmt/w07_00.lmt` | 335 | EventGroup06 | H | 0 | 6460 | 6614 | 110 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| 起手 | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6613 | 146964709 |
| 插枪第一分支 | 同上 | 6460 | 1024101668 | 2 | `ee5b6bfa669cd61e9828e3dc88db75219ec5a55babe87548eabd65c159c0a52e` | 6614 | 1767044258 |
| 插枪第二分支 | 同上 | 6460 | 1080565533 | 2 | `641f251490902f7b5e322be89c5bd4b72bfe3b5100f3a85d1ccc26563d7e8f32` | 6614 | 3205911733 |

- LMT v95，Motion 335 共 359 帧，TIML `2913472` 独占。两处赋值偏移为 `2915840`、`2915904`，trigger mask 为 `0x20`、`0x80`。使用 `replace_request()`，仅改 2 字节，合并后 48 字节，文件大小不变。
- WWEV v19，原记录 #17、#14、#15 分别完整克隆为 #50、#51、#52，每条 129 字节。插枪通过 `append_cloned_request()` 原子克隆两条记录并保留顺序。仅改变 ReqNo 和 Event ID，原记录与依赖区保持 byte-exact。合并后为 52 条，累计追加 1161 字节。
- 四个既有 artifact owner 登记本设计，跨文件验证仅允许这两条动画入口、三条 mode 2 展开和每阶段一次语音。游戏验收覆盖两种持械起始状态、插枪前中断、完整攻击，以及龙击炮、骑乘终结、飞翔爪发射与普通动作对照。
