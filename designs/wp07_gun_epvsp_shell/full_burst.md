---
design_id: wp07_gun_epvsp_shell.full_burst
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 全弹发射

## 描述

保留 1–5 发全弹发射的原版底火、爆炸和空间路径；每种炮弹数对应的 Event 均追加一个 Action 和 Sound，共享一份「Shoot」语音媒体。

| 名称           | 动作或状态          | 预期行为                          |
|----------------|---------------------|-----------------------------------|
| 1–5 发全弹发射 | 实际消耗 1–5 发炮弹 | 保留原声，并额外播放一次「Shoot」 |
| 其它铳枪动作   | 非全弹发射动作      | 不播放「Shoot」                   |

## 音频

| 名称          | 音频                                                                                                                          | 响度（LUFS-I） | 播放方式                                                   |
|---------------|-------------------------------------------------------------------------------------------------------------------------------|----------------|------------------------------------------------------------|
| 奈叶「Shoot」 | [nanoha_shoot_01](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_01(battle_of_aces.attack_voice.attack_03.1).wav>) | -21 LUFS-I     | 追加一份共享媒体，五种全弹各用独立 Action 和标准语音 Sound |

## 实现契约

- 原始 Bank: `original/nbnk/wp07_gun_epvsp_shell.nbnk`，Wwise v120，SHA-256
  `41bb0136e89e8434d716caed9c37b399e44cd0cb057f3fa9ab706437696782a1`
- Bank ID: `3273965928`

| 名称         | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|--------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 1 发全弹发射 | 2727643338 | 449657149    | 108007348    | 219848096 / 768048455  | #34 / 768048455    | 3386055930   | 960803121   |
| 2 发全弹发射 | 2727643337 | 646158903    | 58172267     | 46149961 / 669932693   | #30 / 669932693    | 4199321359   | 479969098   |
| 3 发全弹发射 | 1124197610 | 19077629     | 246916390    | 46149961 / 669932693   | #2 / 31902971      | 4100049135   | 2544331946  |
| 4 发全弹发射 | 680296805  | 223369281    | 505597934    | 46149961 / 669932693   | #15 / 385933384    | 4272498343   | 4251385954  |
| 5 发全弹发射 | 1765608260 | 403102539    | 885313651    | 46149961 / 669932693   | #9 / 272642002     | 3047212046   | 1519403237  |

- 原媒体保持 byte-exact；共享语音追加为 DIDX #43 / Media ID `242768048`。
- 每个 Event 的 Action 数由 1 变为 2，原 Action 保持在第一项；表中 donor 只作为原事件路径 guard，不再作为新 Sound 的模板。
- 五个新 Sound 均使用 46-byte 标准语音 body：来源为 `original/nbnk/wp_cmn_epvsp.nbnk`（文件 SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media
  `838569492`（原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），仅替换各自
  Sound ID 与 Media ID，并固定 `DirectParentID=209038110`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`；标准 body
  SHA-256 为 `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 项目 WAV 固定为 48 kHz、stereo、24-bit PCM，并保持音频表记录的 -21 LUFS-I；构建时不做增益、归一化或响度修正，只无增益下混为
  48 kHz、16-bit mono Wwise PCM WEM。
- 3–5 发的成对空间路径仅向表中 Event 追加语音，另一个成对 Event 保持不变，避免重复播放。
- 本设计 HIRC 新增 5 个 Action 和 5 个 Sound，changed-byte count 为 `5`、payload 增量为 `+390`；与 `wyverns_fire` 合并后
  changed-byte count 为 `8`、payload 增量为 `+624`。除 DIDX、DATA 和上述 HIRC 变化外，其它 Bank 内容保持 byte-exact。
