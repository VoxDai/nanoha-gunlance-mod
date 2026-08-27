---
design_id: wp07_gun_epvsp_shell.wyverns_fire
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 龙击炮

## 描述

保留龙击炮原版蓄力和爆炸声；蓄力时同步叠加奈叶与 Raising Heart 语音，爆炸时只在右侧 Event 叠加一次「Breaker」语音。

| 名称         | 动作或状态       | 预期行为                                |
|--------------|------------------|-----------------------------------------|
| 龙击炮蓄力   | 发动龙击炮       | 保留原声，两条语音同时开始且各播放一次  |
| 龙击炮爆炸   | 完成蓄力并发射   | 保留左右原声，仅右侧 Event 叠加一次「Breaker」 |
| 龙击炮中断   | 蓄力取消或被中断 | 两条蓄力语音随原生蓄力声淡出停止，不触发爆炸「Breaker」 |
| 其它铳枪动作 | 非龙击炮动作     | 不播放三条追加语音                      |

## 音频

| 名称                               | 音频                                                                                                                                                                      | 响度（LUFS-I） | 播放方式                                                    |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-------------------------------------------------------------|
| 奈叶「Starlight」                  | [nanoha_starlight_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav>)                                 | -21 LUFS-I     | 追加独立媒体，同步播放                                      |
| Raising Heart「Starlight Breaker」 | [raising_heart_starlight_breaker_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_01(movie_1st.raising_heart.starlight_breaker.1).wav>) | -24 LUFS-I     | 追加独立媒体，同步播放                                      |
| 奈叶「Breaker」                    | [nanoha_breaker_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav>)                                     | -21 LUFS-I     | 追加独立媒体，仅右侧 Event 使用一个 Action 和标准语音 Sound |

## 实现契约

- 原始 Bank: `original/nbnk/wp07_gun_epvsp_shell.nbnk`，Wwise v120，SHA-256
  `41bb0136e89e8434d716caed9c37b399e44cd0cb057f3fa9ab706437696782a1`
- Bank ID: `3273965928`

| 名称                        | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|-----------------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 龙击炮蓄力（奈叶）          | 302768804  | 51759545     | 60034062     | 990545535 / 477887770  | #23 / 477887770    | 4011774951   | 4149261730  |
| 龙击炮蓄力（Raising Heart） | 302768804  | 51759545     | 60034062     | 990545535 / 477887770  | #23 / 477887770    | 254514827    | 36215958    |
| 龙击炮爆炸（右）            | 3655102100 | 648832766    | 106161033    | 269350169 / 401136332  | #19 / 401136332    | 1866468495   | 2472459210  |

| 名称                        | Stop Event ID | donor Stop Action ID / target | scope       | transition / fade | exceptions | 新 Stop Action ID | 新 Stop target |
|-----------------------------|---------------|-------------------------------|-------------|-------------------|------------|--------------------|-----------------|
| 龙击炮蓄力（奈叶）          | 461444626     | 743936681 / 60034062          | Game Object | 200 ms / Linear   | 空         | 2987046856         | 4149261730      |
| 龙击炮蓄力（Raising Heart） | 461444626     | 743936681 / 60034062          | Game Object | 200 ms / Linear   | 空         | 3645807405         | 36215958        |

- 上表原媒体保持 byte-exact；在全弹发射的 DIDX #43 之后，依次追加奈叶「Starlight」DIDX #44 / Media ID `322318543`、 Raising
  Heart「Starlight Breaker」DIDX #45 / Media ID `3332910283` 和「Breaker」DIDX #46 / Media ID `2217266443`。
- 蓄力 Event 的 Action 列表变为 `51759545, 4011774951, 254514827`；右侧爆炸 Event 变为
  `648832766, 1866468495`，原 Action 始终在第一项。左侧 Event `3253425110` 保持 byte-exact，Action 列表仍仅为
  `120830402`，不得新增 Action `2807447016` 或 Sound `3070096299`，避免同一人物语音在成对空间路径重复播放。
- 原生蓄力 Container `60034062` 由 Event `461444626` 的 Stop Action `743936681` 停止；donor Action 的完整 body
  SHA-256 为 `137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd`。两条新 Stop Action 必须完整克隆
  donor 的 Game Object scope、属性、200 ms transition、Linear fade、空 exceptions 和未知字段，仅分别替换 Action ID
  与 target 为上表值。Stop Event 的 Action 列表由 `743936681` 变为
  `743936681, 2987046856, 3645807405`；两个克隆依此顺序序列化在该 Event 之前。
- 表中 donor 仅作为各原事件路径 guard。三个新 Sound 均使用 46-byte 标准语音 body：来源为
  `original/nbnk/wp_cmn_epvsp.nbnk`（文件 SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media `838569492`（原 body SHA-256
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），固定 `DirectParentID=209038110`、body
  `+0x20` 的 `PositioningParams.uByVector=0xC1`，标准 body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`；Action 均不设 delay。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 三份项目 WAV 固定为 48 kHz、stereo、24-bit PCM，并保持音频表记录的 -21 或 -24 LUFS-I；构建时不做增益、归一化或响度修正，
  只无增益下混为 48 kHz、16-bit mono Wwise PCM WEM。
- 本设计 HIRC 新增 5 个 Action 和 3 个 Sound，changed-byte count 为 `5`、payload 增量为 `+298`；与 `full_burst` 合并后
  changed-byte count 为 `10`、payload 增量为 `+688`。上述新 ID 已通过原 Bank 与全弹发射已占用 ID 的碰撞检查；除 DIDX、DATA
  和上述 HIRC 变化外，其它 Bank 内容保持 byte-exact。
