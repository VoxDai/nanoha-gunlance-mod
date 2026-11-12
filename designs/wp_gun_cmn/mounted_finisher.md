---
design_id: wp_gun_cmn.mounted_finisher
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 骑乘终结攻击

## 描述

铳枪骑乘终结时在爆炸前追加一遍奈叶「Accelerator」，保留终结攻击的原声。背、头、尾共用语音，每次播放随机偏移音调。

| 名称 | 动作或状态 | 预期行为 |
| --- | --- | --- |
| Accelerator | 背部、头部、尾部终结 | 爆炸前播放一次，音调随机偏移 ±50 cents |
| 其它动作 | 上马、途中刺击、钩爪武器攻击、龙击炮 | 保持既有声音行为 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
| --- | --- | ---: | --- |
| Accelerator | [最终 WAV](../../audio/wp_gun_cmn/mounted_finisher/nanoha_accelerator_01%28source_audio.movie_detonation.nanoha.accelerator.1%29.wav) | −20 | 三部位共用，触发时立即追加，无额外延时 |

## 实现契约

LMT v95 使用 `original/lmt/w07_00.lmt`。三处 TIML 分别位于 1788784、1863696、1937840，各仅由对应 Motion 引用，触发掩码均为 16。请求字段偏移分别为 1792672、1867552、1941728。每处只改一个字节，文件长度不变。

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 背部 | w07_00 | 170 | EventGroup06 | E | 0 | 6550 | 6615 | 82 |
| 头部 | w07_00 | 171 | EventGroup06 | E | 0 | 6550 | 6615 | 82 |
| 尾部 | w07_00 | 172 | EventGroup06 | E | 0 | 6550 | 6615 | 82 |

WWEV v19 使用 `original/wwev/hm_wp07_snd_ev.wwev`。使用 `append_cloned_request()` 原子克隆第 33、34 条记录，各 129 字节。只改克隆的 ReqNo 和 Event ID，原记录与依赖保持逐字节一致。独立应用时记录从 43 增至 45，合并后新增记录序号为 51、52。

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 第一分支 | hm_wp07_snd_ev | 6550 | 2925880017 | 2 | `b501ecd9ebb0baaf4ae7432ef8c25e161f372c7b298791664ad4567c1851736e` | 6615 | 496401681 |
| 第二分支 | hm_wp07_snd_ev | 6550 | 1080565533 | 2 | `0ce801814a4ba5382e311df66e9611d56c9972dad36aab2690ceb5a7ad1944fb` | 6615 | 3994593461 |

NBNK v120 使用 `original/nbnk/pl_wp_par_op_event_structure.nbnk`（Bank 2944223826）和 `original/nbnk/wp_gun_cmn.nbnk`（Bank 939294496）。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| 第一原生分支 | 2925880017 | 1012787452 | 987082006 | — | — | 2248472451 | — |
| 第二原生分支 | 1080565533 | 29680933 | 9236354 | — | — | 2208167511 | — |
| Accelerator | 4197115840 | — | — | 890667980 / 838569492 | 新增 50 / — | 831225203 | 2739514054 |

- 原 Event 2925880017 和 1080565533 各只拥有表中的一个原 Action。Event body SHA-256 依次为 `c9adec59ce59bd1cf3c407f2d8efa9afa051668b423459b852ffe730cface5ca`、`27390d1f2a5a2a3356cd5eee0cdbafe1d9fa9f4d734a6f8fba0f469e5a8f193b`。原 Action body SHA-256 依次为 `273437fb964544b5333f281a91f87099fdb7e6e0671e5ad786ca3c17f2a5b0b2`、`b156ed03e9878e9474778f313489e1f7c9d3ac905ba4cd8d30655e94ee780ebb`。
- 包装 Event 496401681 的 Action 列表为 `[2248472451, 2095821896]`，依次调用原第一分支和语音 Event。包装 Event 3994593461 的 Action 列表为 `[2208167511]`，调用原第二分支。各 PlayEvent Action 先于所属 Event 序列化。结构 Bank 新增五个对象，HIRC 增加 92 字节，原对象和 BKHD 原样保留。
- 语音 Event 4197115840 的唯一 Action 831225203 播放 Sound 2739514054，Media ID 3650218823，追加到已注册构建的 DIDX 索引 50。转换为 48 kHz、16-bit 单声道 Wwise PCM，无附加增益。
- 标准语音 donor 来自 `original/nbnk/wp_cmn_epvsp.nbnk`，body SHA-256 为 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。沿用 C1 定位及 `original/nbnk/pl_act_vo_event.nbnk` 的 Actor-Mixer 209038110；其 body SHA-256 为 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`。只对新增 Sound 应用 Pitch 随机范围 `[-50, 50]`，Sound body 为 55 字节，SHA-256 为 `5533fb6a951b52f8d554559b62ba2b564d0d9c3ba290362be40d407c591ecb91`。按 Sound、Action、Event 的顺序追加，HIRC 增加 100 字节，Pitch 编辑计入 8 个变更字节。保留既有 DIDX 顺序、媒体内容和其他 HIRC 对象。
- 已检查原分支的 Play 目标及其父链（987082006 → 468342192 → 972300144 → 694534885；9236354 → 460803750 → 972300144 → 694534885），项目原版 Bank 的原生 Event 中没有以这些节点为目标的 Stop Action。

游戏验收分别在背、头、尾完成一次终结，确认爆炸前各响一遍「Accelerator」且原声正常。以上马、途中刺击、钩爪武器攻击和龙击炮作对照，确认均不播放此语音。触发依据见[联合探针实测](../../assets/analyses/mounted_finisher/mounted_finisher_11_five_routes_spoken/recordings.md)。
