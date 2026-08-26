---
design_id: wp_cmn_epvsp.sharpen
target_artifacts:
  - sound/wwise/Windows/wp_cmn_epvsp.nbnk
---

# 磨刀完成

## 描述

保留磨刀完成原声；完成磨刀时同步叠加一次 Raising Heart「Charging Completed」语音。

| 名称       | 动作或状态       | 预期行为                                                   |
|------------|------------------|------------------------------------------------------------|
| 磨刀完成   | 完成整个磨刀动作 | 保留原声，并同步额外播放一次「Charging Completed」         |
| 磨刀中断   | 磨刀取消或被中断 | 不播放「Charging Completed」                               |
| 其它通用动作 | 非磨刀完成动作   | 不播放「Charging Completed」                               |

## 音频

| 名称                                | 音频                                                                                                                                                         | 响度（LUFS-I） | 播放方式                                              |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-------------------------------------------------------|
| Raising Heart「Charging Completed」 | [raising_heart_charging_completed](<../../audio/wp_cmn_epvsp/sharpen/raising_heart_charging_completed_01(movie_1st.raising_heart.charging_completed.1).wav>) | -24 LUFS-I     | 追加独立媒体，以标准语音 Sound 与磨刀完成原声同步播放 |

## 实现契约

- 原始 Bank: `original/nbnk/wp_cmn_epvsp.nbnk`
- Bank ID: `1149256632`

| 名称     | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|----------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 磨刀完成 | 166276485 | 579012432    | 306760817    | 890667980 / 838569492  | #52 / 838569492    | 487645987    | 84645870    |

- 原有 71 份媒体保持 byte-exact；追加语音为 DIDX #72 / Media ID `2791080207`。
- Event `166276485` 的 Action 列表变为 `579012432, 487645987`，原 Action 保持在第一项。
- 新 Sound 以 donor `890667980` 的 46-byte body 为标准来源；原 Bank 文件 SHA-256 为
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`，原 body SHA-256 为
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。新 Sound 替换 Sound ID 和媒体引用，并将
  `DirectParentID` 从 `306760817` 固定为外部 Actor-Mixer `209038110`、body `+0x20` 的
  `PositioningParams.uByVector` 从 `0xC0` 固定为 `0xC1`；标准 body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`，Action 不设 delay。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 项目 WAV 固定为 48 kHz、stereo、24-bit PCM，并保持音频表记录的 -24 LUFS-I；构建时不做增益、归一化或响度修正，只无增益下混为
  48 kHz、16-bit mono Wwise PCM WEM。
- Bank 固定为 Wwise v120；HIRC 对象数由 299 增至 301，目标 Event 由 12 增至 16 字节，changed-byte count 为 `1`、payload
  增量为 `+78`。上述新 ID 已通过原 Bank 全部 Media 与 HIRC ID 的碰撞检查；除 DIDX、DATA 和上述 HIRC 变化外，其它 Bank 内容保持
  byte-exact。
