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

| 名称                                | 音频                                                                                                                                                                                   | 播放方式                         |
|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| Raising Heart「Charging Completed」 | [raising_heart_charging_completed](<../../audio/wp_cmn_epvsp/sharpen/raising_heart_charging_completed_01(movie_1st.raising_heart.charging_completed.1).wav>)                              | 追加独立媒体，与磨刀完成原声同步播放 |

## 实现契约

- 原始 Bank: `original/nbnk/wp_cmn_epvsp.nbnk`
- Bank ID: `1149256632`

| 名称     | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|----------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 磨刀完成 | 166276485 | 579012432    | 306760817    | 890667980 / 838569492  | #52 / 838569492    | 487645987    | 84645870    |

- 原有 71 份媒体保持 byte-exact；追加语音为 DIDX #72 / Media ID `2791080207`。
- Event `166276485` 的 Action 列表变为 `579012432, 487645987`，原 Action 保持在第一项。
- 新 Sound 克隆 donor `890667980`，仅替换 Sound ID 和媒体引用；不设 delay，并保留原定位、空间及父级属性。
- Bank 固定为 Wwise v120；HIRC 对象数由 299 增至 301，目标 Event 由 12 增至 16 字节，changed-byte count 为 `1`、payload
  增量为 `+78`。上述新 ID 已通过原 Bank 全部 Media 与 HIRC ID 的碰撞检查；除 DIDX、DATA 和上述 HIRC 变化外，其它 Bank 内容保持
  byte-exact。
