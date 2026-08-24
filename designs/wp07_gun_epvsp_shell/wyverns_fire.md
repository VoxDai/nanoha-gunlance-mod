---
design_id: wp07_gun_epvsp_shell.wyverns_fire
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 龙击炮

## 描述

保留龙击炮原版蓄力和爆炸声；蓄力时同步叠加奈叶与 Raising Heart 语音，爆炸时在左右路径各叠加一次共享的「Breaker」语音。

| 名称         | 动作或状态       | 预期行为                                |
|--------------|------------------|-----------------------------------------|
| 龙击炮蓄力   | 发动龙击炮       | 保留原声，两条语音同时开始且各播放一次  |
| 龙击炮爆炸   | 完成蓄力并发射   | 保留原声，左右路径各叠加一次「Breaker」 |
| 龙击炮中断   | 蓄力取消或被中断 | 不触发爆炸「Breaker」                   |
| 其它铳枪动作 | 非龙击炮动作     | 不播放三条追加语音                      |

## 音频

| 名称                               | 音频                                                                                                                                                                      | 播放方式                                       |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| 奈叶「Starlight」                  | [nanoha_starlight_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav>)                                 | 追加独立媒体，同步播放                         |
| Raising Heart「Starlight Breaker」 | [raising_heart_starlight_breaker_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_01(movie_1st.raising_heart.starlight_breaker.1).wav>) | 追加独立媒体，同步播放                         |
| 奈叶「Breaker」                    | [nanoha_breaker_01](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav>)                                     | 追加一份共享媒体，左右各用独立 Action 和 Sound |

## 实现契约

- 原始 Bank: `original/nbnk/wp07_gun_epvsp_shell.nbnk`
- Bank ID: `3273965928`

| 名称                        | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|-----------------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 龙击炮蓄力（奈叶）          | 302768804  | 51759545     | 60034062     | 990545535 / 477887770  | #23 / 477887770    | 4011774951   | 4149261730  |
| 龙击炮蓄力（Raising Heart） | 302768804  | 51759545     | 60034062     | 990545535 / 477887770  | #23 / 477887770    | 254514827    | 36215958    |
| 龙击炮爆炸（右）            | 3655102100 | 648832766    | 106161033    | 269350169 / 401136332  | #19 / 401136332    | 1866468495   | 2472459210  |
| 龙击炮爆炸（左）            | 3253425110 | 120830402    | 803023258    | 249028781 / 661341708  | #29 / 661341708    | 2807447016   | 3070096299  |

- 上表原媒体保持 byte-exact；在全弹发射的 DIDX #43 之后，依次追加奈叶「Starlight」DIDX #44 / Media ID `322318543`、 Raising
  Heart「Starlight Breaker」DIDX #45 / Media ID `3332910283` 和「Breaker」DIDX #46 / Media ID `2217266443`。
- 蓄力 Event 的 Action 列表变为 `51759545, 4011774951, 254514827`；左右爆炸 Event 分别变为
  `648832766, 1866468495` 和 `120830402, 2807447016`，原 Action 始终在第一项。
- 蓄力的两个 Sound 克隆 donor `990545535` 且不设 delay；Breaker 共用媒体，左右 Sound 分别克隆表中 donor 并保留空间属性。
- HIRC 新增 4 个 Action 和 4 个 Sound，changed-byte count 为 `4`、payload 增量为 `+312`；上述新 ID 已通过原 Bank 与全弹发射
  已占用 ID 的碰撞检查，除 DIDX、DATA 和上述 HIRC 变化外，其它 Bank 内容保持 byte-exact。
