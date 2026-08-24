---
design_id: wp07_gun_epvsp_shell.wyverns_fire
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 龙击炮

## 描述

保留龙击炮原版蓄力和爆炸声；蓄力时同步叠加奈叶与 Raising Heart 语音，爆炸时在左右路径各叠加一次共享的「Breaker」语音。

| 名称 | 动作或状态     | 预期行为                                |
|------|----------------|-----------------------------------------|
| 龙击炮蓄力 | 发动龙击炮     | 保留原声，两条语音同时开始且各播放一次  |
| 龙击炮爆炸 | 完成蓄力并发射 | 保留原声，左右路径各叠加一次「Breaker」 |

## 音频

| 名称 | 音频                                                                                                                                                                      | 播放方式                                       |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| 奈叶「Starlight」 | [nanoha_starlight_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav>)                                 | 追加独立媒体，同步播放                         |
| Raising Heart「Starlight Breaker」 | [raising_heart_starlight_breaker_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_01(movie_1st.raising_heart.starlight_breaker.1).wav>) | 追加独立媒体，同步播放                         |
| 奈叶「Breaker」 | [nanoha_breaker_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav>)                                     | 追加一份共享媒体，左右各用独立 Action 和 Sound |

## 实现契约

- 原始 Bank: `original/soundbank/wp07_gun_epvsp_shell.nbnk`
- Bank ID: `3273965928`

| 名称       | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 龙击炮蓄力       | 302768804  | 51759545     | 60034062     | 990545535 / 477887770  | #23 / 477887770    | 待分配 ×2    | 待分配 ×2   |
| 龙击炮爆炸（右） | 3655102100 | 648832766    | 106161033    | 269350169 / 401136332  | #19 / 401136332    | 待分配       | 待分配      |
| 龙击炮爆炸（左） | 3253425110 | 120830402    | 803023258    | 249028781 / 661341708  | #29 / 661341708    | 待分配       | 待分配      |

- 上表原媒体保持 byte-exact；追加 3 份媒体、4 个 Action 和 4 个 Sound，不新增 Event。
- 蓄力 Event 的 Action 数由 1 变为 3，左右爆炸 Event 各由 1 变为 2；原 Action 始终在第一项。
- 蓄力的两个 Sound 克隆 donor `990545535` 且不设 delay；Breaker 共用媒体，左右 Sound 分别克隆表中 donor 并保留空间属性。
- 新 Media、Action 和 Sound ID 由 builder 分配并 guard；除 DIDX、DATA 和上述 HIRC 变化外，其它 Bank 内容保持 byte-exact。
