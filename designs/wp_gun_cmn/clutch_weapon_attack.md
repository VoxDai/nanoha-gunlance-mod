---
design_id: wp_gun_cmn.clutch_weapon_attack
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/pl/pl_voice.wwev
  - sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 钩爪武器攻击

## 描述

铳枪吸附怪物后的武器攻击在起手拔枪时播放一次奈叶语音。静音拔枪后和插枪前的两处原版人物语音，保留拔枪、插枪和炮击的原版武器声。实际炮击使用[蓄力炮击设计](../wp07_gun_epvsp_shell/charged_shelling.md)的共享 Buster。

| 名称 | 动作或状态 | 预期行为 |
|------|------------|----------|
| 起手蓄力 | 持械或收刀起始，吸附后执行武器攻击并拔枪 | 播放一次「Excellion」，保留拔枪声，静音原版人物「哼」 |
| 插枪 | 枪插入怪物，爆炸前 | 保留两条原版武器声分支，静音插枪前的原版人物「哼」 |
| 炮击 | 插枪后实际开炮 | 从共享容器等权选播一次「Buster」，保留爆炸原声 |
| 炮击前中断 | 未触发实际炮击 | 不触发「Buster」 |
| 其它动作 | 飞翔爪发射、龙击炮、骑乘终结、普通攻击及落地 | 保持既有声音行为 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|---------------|----------|
| 奈叶「Excellion」 | [nanoha_excellion_01](<../../audio/wp_gun_cmn/clutch_weapon_attack/nanoha_excellion_01(movie_reflection.nanoha.excellion_buster.1).wav>) | −24 | 起手追加一次，无延迟，独立随机 Pitch ±50 cents |

## 实现契约

两个 Bank 均为 Wwise v120。原始输入为 `original/nbnk/wp_gun_cmn.nbnk`（Bank ID `939294496`）和 `original/nbnk/pl_wp_par_op_event_structure.nbnk`（Bank ID `2944223826`）。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|-------------|--------------|------------------------|--------------------|-------------|-----------|
| 起手原声委托 | 146964709 → 3567942167 | 1061269777 | 522283251 | — | — | 1984195518 | — |
| Excellion | 146964709 → 2405966492 | — | — | 890667980 / 838569492 | #49 / — | 1423603563 → 1277608954 | 507956785 |

- 拔枪包装 Event `146964709` 的 Action 列表为 `[1984195518,1423603563]`。两条无延迟 PlayEvent 先调用完整原声，再调用语音 Event `2405966492`，并在包装 Event 前序列化。语音 Event 只含 Play Action `1277608954`，在 Sound 与 Action 之后序列化。插枪两条原 Event 保持原始 Action 与对象 body。
- 原版 Event / Action 完整 body SHA-256，按起手、插枪第一分支、插枪第二分支列出。

| Event ID | Event SHA-256 | Action SHA-256 |
|----------|---------------|----------------|
| 3567942167 | `cdf654b3ef9e93d51971da97cc9479fcfd85ad8baaa6923f1a94bb6784844f15` | `6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a` |
| 1024101668 | `9e0727fd4f80e2a0410e6b26cb44565a62194e49011716232d2e07a68c460876` | `b5a74054bd5d85178c6129c3668a6ec8f211f897e40477b17d02a7a7901ad5c8` |
| 1080565533 | `27390d1f2a5a2a3356cd5eee0cdbafe1d9fa9f4d734a6f8fba0f469e5a8f193b` | `b156ed03e9878e9474778f313489e1f7c9d3ac905ba4cd8d30655e94ee780ebb` |

- 原版 Play 目标及父级分别为 `522283251 → 768813060`、`186074123 → 468342192`、`9236354 → 460803750`，各自继续指向 `972300144 → 694534885`。原版 Bank 中没有指向这些目标或父级的 Stop Action，本设计无新增 Stop。龙击炮原生停止链和 EPVSP 分流独立保留。
- 标准语音 donor 来自 `original/nbnk/wp_cmn_epvsp.nbnk`（Bank ID `1149256632`），原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。保留模板 C1 positioning 和 Aux，DirectParentID 为 `209038110`（`original/nbnk/pl_act_vo_event.nbnk`，Bank ID `3755575407`，Actor-Mixer body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`）。模板标准化后 SHA-256 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。仅替换 Sound/Media ID 并加入随机 Pitch `(-50.0, 50.0)`，无基础 Pitch 偏移。最终 Sound body SHA-256 为 `0b8d9f6f3c01e0f9f91234fc65954a1ec1db9f4f0c502577bd5f97dc28dfef8c`。
- 仅在 #49 追加 Media `3631037616`。48 kHz、双声道、24-bit PCM WAV 无增益下混为 48 kHz、16-bit、单声道 Wwise PCM WEM，channel config `000001410000`。原媒体保持 byte-exact，DIDX/DATA 仅有追加及重建所需的偏移和对齐变化。新增 ID 由 `wwise_fnv1("wp_gun_cmn_clutch_weapon_attack_" + suffix)` 派生，已检查 4550 个原版 NBNK 和 1300 个原版 WWEV 的占用。
- 本设计对 common Bank 新增 1 Sound、1 Action、1 Event，HIRC 增量 `+100`，合并后 `+1900`，随机 Pitch 使 changed-byte count 增加 `8`，合并后为 `49`。对结构 Bank 新增 2 Action、1 Event，HIRC 增量 `+57`，合并后 `+228`，changed-byte count 为 `0`。结构 Bank 的 BKHD 与所有原始 HIRC 对象 byte-exact。

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| 起手 | `original/lmt/w07_00.lmt` | 335 | EventGroup06 | F | 0 | 6470 | 6613 | 5 |
| 拔枪后人物语音 | `original/lmt/w07_00.lmt` | 335 | EventGroup02 | B | 0 | 1409 | 6750 | 16 |
| 插枪前人物语音 | `original/lmt/w07_00.lmt` | 335 | EventGroup02 | A | 0 | 1309 | 6750 | 107 |
| 插枪 | `original/lmt/w07_00.lmt` | 335 | EventGroup06 | H | 0 | 6460 | 保留原值 | 110 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| 起手 | `original/wwev/hm_wp07_snd_ev.wwev` | 6470 | 3567942167 | 2 | `1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f` | 6613 | 146964709 |
| 插枪第一分支 | 同上 | 6460 | 1024101668 | 2 | `ee5b6bfa669cd61e9828e3dc88db75219ec5a55babe87548eabd65c159c0a52e` | — | 保留原 Event |
| 插枪第二分支 | 同上 | 6460 | 1080565533 | 2 | `641f251490902f7b5e322be89c5bd4b72bfe3b5100f3a85d1ccc26563d7e8f32` | — | 保留原 Event |

- LMT v95，Motion 335 共 359 帧，TIML `2913472` 独占。F／H 赋值偏移分别为 `2915840`／`2915904`，trigger mask 分别为 `0x20`／`0x80`。用 `replace_request()` 修改 F 的赋值，改 1 字节。人物语音 B／A 的赋值偏移分别为 `2915504`／`2915472`，trigger mask 分别为 `0x02`／`0x01`，各改 2 字节。钩爪共改 5 字节，合并后 51 字节，文件大小不变。
- WWEV v19，原 #17 完整克隆为 #50（129 字节），仅改变 ReqNo 和 Event ID。原 #14／#15 保持原顺序及字节内容。合并后 50 条，累计追加 903 字节。
- 人物语音原表为 `original/wwev/pl_voice.wwev` v19。原 Req1409 仅有 #20／mode 4／Event `967571325`，record SHA-256 为 `73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507`。原 Req1309 仅有 #18／mode 4／Event `3262711103`，record SHA-256 为 `505d806915b6b08b37add31895e56e4e45faf84cc0e85883a4414873927390f9`。两条原记录保留。
- 复用[龙杭设计](../wp07_gun_epvsp_shell/wyrmstake_cannon.md)的 Req6750。人物语音表保持合并后的 103 条记录，追加量仍为 387 字节。#103 为唯一 Req6750／mode 4／Event `2846173097`，record SHA-256 为 `c44060757af7fe2b1ba1c5bc505e738d20342f68cd5754d7184283bca6432f00`。common Bank 沿用空 Event `3938800881` → PlayEvent Action `1604422970` → 包装 Event `2846173097` 的序列化顺序，包装调用空 Event。此静音改动只编辑 LMT。
- 五个既有 artifact owner 登记本设计。跨文件验证两条人物语音改道及空 Event、Excellion 播放、插枪两条 mode 2 原版分支，以及旧 Req6614、专用包装、语音 Event 和 common Bank 的 Buster 媒体缺席。
- [静音探针](../../assets/analyses/clutch_weapon_attack/clutch_weapon_attack_11_grunt_mute/recordings.md)的持械和收刀起手各测两次。两处「哼」均为 0/2，Excellion、插枪原声和 Buster 正常，基线栏未测。正式包验收覆盖两种起手状态、插枪原声、三种炮型实际炮击只响一次共享 Buster、炮击前中断，以及龙击炮、骑乘终结和普通炮击对照。
