---
design_id: hm_cm00_epvsp.gunlance_guard
target_artifacts:
  - sound/wwise/Windows/hm_cm00_epvsp.nbnk
---

# 铳枪盾牌防御

## 描述

严格保留铳枪盾牌防御 `#88` 的原版声音与路由；每次防御在原声之外等概率随机追加一条 Raising Heart「Protection」语音。语音播放期间再次触发防御时保留当前语音并丢弃新触发，播放结束后才允许下一次触发。

| 名称                     | 动作或状态                            | 预期行为                                                   |
|--------------------------|---------------------------------------|------------------------------------------------------------|
| 铳枪盾牌防御             | 命中原 `#88` 防御路线                 | 保留原声，额外等概率播放一条「Protection」                 |
| 连续防御                 | 当前「Protection」仍在播放时再次防御  | 不打断当前语音，也不启动下一条语音                         |
| 防御语音播放结束         | 当前 5 秒语音已结束后再次防御         | 允许重新等概率播放一条「Protection」                       |
| 其它盾牌与非防御动作     | `#7/#54/#64/#67` 路线或其它动作       | 不播放「Protection」                                       |

## 音频

| 名称                            | 音频                                                                                                                                                        | 播放方式                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| Raising Heart「Protection 01」 | [raising_heart_protection_01](<../../audio/hm_cm00_epvsp/raising_heart_protection_01(movie_1st.raising_heart.protection_01.1).wav>)                         | 独立媒体；权重 `50000`，与 Protection 02 等概率随机          |
| Raising Heart「Protection 02」 | [raising_heart_protection_02](<../../audio/hm_cm00_epvsp/raising_heart_protection_02(movie_1st.raising_heart.protection_02.1).wav>)                         | 独立媒体；权重 `50000`，与 Protection 01 等概率随机          |

两段文件均为最终音频：48 kHz、stereo、24-bit PCM、时长 5 秒。随机 Container 的 `avoid-repeat=0`，两次可播放相同条目；音频实例上限为 1，超过上限时采用 Kill Newest，因而当前语音播放期间的新触发会被丢弃。

## 实现契约

- 原始 Bank: `original/nbnk/hm_cm00_epvsp.nbnk`
- Bank ID: `707566772`

| 名称                          | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|-------------------------------|------------|----------------|--------------|------------------------|--------------------|--------------|-------------|
| Protection 01                | 4072881687 | 601196071      | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 2154199438  |
| Protection 02                | 4072881687 | 601196071      | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 640829561   |

- Bank 固定为 Wwise v120，原文件 SHA-256 为 `73b52c1a69532f0a84ab6dfa2e95bd804bf8affc5af77450786d700c177a9977`。原始媒体数为 140、HIRC 对象数为 597、HIRC payload 为 33313 字节。
- 原路线必须保持不变：Event `4072881687` → Action `601196071` → Switch Container `368774789` → Random Container `127521149` → Sound `925721864` → DIDX #88 / Media `676385730`。原 Event 只在尾部追加 Action `4197300369`，Action 列表固定变为 `601196071, 4197300369`；新 Action delay 为 `30 ms`，目标为新 Switch Container `4010844647`。
- donor Switch `368774789` 的完整 body SHA-256 固定为 `a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde1358c02ab99043bb`。其 Group 为 `3251135135`、默认值为 `3396333570`；克隆时保留 donor 前缀、属性、package 顺序和 node params，并使用同一 Group 与默认值。
- 新 Switch `4010844647` 仅包含 child `3163089818`。以下 11 个原本指向 `#88` Random `127521149` 的 Switch package 按原顺序保留并改指向新 Random：`3396333570`、`1382012724`、`345916037`、`1839555973`、`3165334324`、`3529994682`、`3846765152`、`1876434011`、`835669289`、`3295588651`、`208142906`；新 child 继承原 `127521149` 的 node params：behavior flags `0`、transition flags `1`、fade-out `0 ms`、fade-in `0 ms`。
- 以下四个 package 删除后为空，不得进入新路线：`3893559432` → Random `133098601` → `#7`，`3366211890` → Random `125400496` → `#54`，`3818705907` → Random `101900622` → `#64`，`1341411413` → Random `438972177` → `#67`。因此长枪、片手剑、盾斧和大剑防御不触发 Protection。
- 新 Random Container `3163089818` 克隆 `127521149`，body `+0x0B` 的父级从 donor Switch `368774789` 改为新 Switch `4010844647`；playlist 固定为 Sound `2154199438` / 权重 `50000` 与 Sound `640829561` / 权重 `50000`，`avoid-repeat=0`。body `+0x19` 从 `0x00` 改为 `0x01`（Kill Newest），body `+0x1B` 从 `0` 改为 `1`（音频实例上限）。其余空间、Aux、音量和输出属性保持 donor。
- 两个新 Sound 均克隆 donor `925721864`，分别引用追加的 DIDX #141 / Media `141209263` 与 DIDX #142 / Media `440767416`；仅替换 Sound ID、媒体引用，并将 body `+0x19` 的父级从 donor Random `127521149` 改为新 Random `3163089818`，其余空间、Aux、音量和输出属性保持 donor。
- 新 ID `4197300369`、`4010844647`、`3163089818`、`2154199438`、`640829561`、`141209263`、`440767416` 已通过原 Bank 全部 HIRC 与 Media ID 碰撞检查。原型读回摘要必须精确为：媒体 `140→142`、HIRC 对象 `597→602`、HIRC payload `33313→33825`、Event body `12→16`、changed-byte count `15`、HIRC 增量 `+512`；新增 HIRC 对象按类型/ID 为 Sound `2154199438`、Sound `640829561`、Random Container `3163089818`、Switch Container `4010844647`、Action `4197300369`。只允许 DIDX、DATA、HIRC 变化。
