---
design_id: wp07_gun_epvsp_shell.wyverns_fire
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
  - sound/pl/hm_wp07_epvsp_snd_ev.wwev
  - wp/gun/sound/hm_wp07.epvsp
---

# 龙击炮

## 描述

保留原版蓄力和炮击声。龙击炮蓄力时分别从奈叶和 Raising Heart 两组语音中各选一句；炮击时从奈叶 Breaker 中选一句。三组均等权随机，允许连续选中同一句，每次音高随机偏移 ±50 cents。

| 名称 | 动作或状态 | 预期行为 |
|---|---|---|
| Container 1 | 龙击炮开始蓄力 | 奈叶 Starlight 从三条中等权选一，0 ms 即响 |
| Container 2 | 龙击炮开始蓄力 | Raising Heart Starlight Breaker 从两条中等权选一，每次随机延迟 0–50 ms |
| Container 3 | 龙击炮开炮 | 奈叶 Breaker 从三条中等权选一，只随右侧发射路径播放一次 |
| 蓄力停止 | 正常发射、取消或受击中断 | 两组蓄力语音随原生 Stop 淡出；未发射时无 Breaker，等待延迟的语音不应在中断后补响 |
| 其它动作 | 钩爪武器攻击、骑乘终结、普通炮击等 | 保留原声，不播放本设计的追加语音 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|---|---|---:|---|
| 奈叶 Starlight 01 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav>) | −21 | 追加，Container 1 |
| 奈叶 Starlight 02 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_02(battle_of_aces.attack_voice.attack_01.1).wav>) | −21 | 追加，Container 1 |
| 奈叶 Starlight 03 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_starlight_03(movie_1st.nanoha.starlight_breaker.1).wav>) | −23 | 追加，Container 1 |
| Raising Heart Starlight Breaker 01 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_01(movie_1st.raising_heart.starlight_breaker.1).wav>) | −24 | 追加，Container 2 |
| Raising Heart Starlight Breaker 02 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/raising_heart_starlight_breaker_02(movie_2nd_as.raising_heart.starlight_breaker.1).wav>) | −24 | 追加，Container 2 |
| 奈叶 Breaker 01 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav>) | −21 | 追加，Container 3 |
| 奈叶 Breaker 02 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_02(battle_of_aces.attack_voice.attack_01.2).wav>) | −21 | 追加，Container 3 |
| 奈叶 Breaker 03 | [WAV](<../../audio/wp07_gun_epvsp_shell/wyverns_fire/nanoha_breaker_03(movie_1st.nanoha.starlight_breaker.2).wav>) | −23 | 追加，Container 3 |

按表序复测为 −21.00、−21.00、−23.17、−23.98、−24.00、−20.98、−21.02、−22.69 LUFS-I。三份获准调整的素材仅应用固定增益（Starlight 02 −3.03 dB、Breaker 02 −3.92 dB、Raising Heart 02 +1.22 dB）。源均为 48 kHz、stereo、24-bit PCM；构建无增益下混为 48 kHz、mono、16-bit Wwise PCM WEM，channel config `000001410000`。

## 实现契约

- `original/epvsp/hm_wp07.epvsp`：ESP v8，Iceborne mark `0x18091001`，WWCT path hash type `0x45185BED`，路径 `wp\gun\sound\hm_wp07_epvsp_snd_ct`，101 条请求、0 条 TriggerData。只改第 0 行 `(0,26501,26502,2000,0)` → `(0,26690,26502,2000,0)`，其余记录、停止请求、文件大小和头不变。元素 2020 行 `(0,26501,26502,2020,0)` 保持原样。
- `original/wwev/hm_wp07_epvsp_snd_ev.wwev`：v19，完整克隆第 1 条、129 字节的 Req26501（mode −1，Event302768804，记录 SHA-256 `9fea5c28772ab6bc99423844a29926803733ac708639e15eb16d0de280c1da89`），作为第 27 条 Req26690 → Event281273126。仅替换 ReqNo 与 Event ID；原 26 条记录及依赖保留。Req26502 → Event461444626 不变。
- `original/nbnk/wp07_gun_epvsp_shell.nbnk`：Wwise v120，Bank ID `3273965928`。原蓄力 Event 和左侧炮击 Event 字节不变；右侧保留原 Action 后追加 Container 3。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|---|---:|---:|---:|---|---|---:|---|
| 原蓄力 | 302768804 | 51759545 | 60034062 | 990545535 / 477887770 | #23 / 477887770 | — | — |
| 私有蓄力包装的原声调用 | 281273126 | — | — | — | — | 3388979775 | — |
| Container 1 | 281273126 | — | 3610379736 | 标准语音体 | 追加 #44、54、55 | 4011774951 | 4149261730、2849114849、1620588112 |
| Container 2 | 281273126 | — | 3391377780 | 标准语音体 | 追加 #45、56 | 254514827 | 36215958、1229173909 |
| Container 3 | 3655102100 | 648832766 | 362366644 | 269350169 / 401136332（原炮击） | #19 / 401136332 保留；追加 #46、57、58 | 1866468495 | 2472459210、3984040149、3346634804 |

| 追加 DIDX | Media ID | 声音 |
|---:|---:|---|
| 44 | 322318543 | Starlight 01 |
| 45 | 3332910283 | Raising Heart 01 |
| 46 | 2217266443 | Breaker 01 |
| 54 | 2014220448 | Starlight 02 |
| 55 | 3735305437 | Starlight 03 |
| 56 | 941385580 | Raising Heart 02 |
| 57 | 3696251564 | Breaker 02 |
| 58 | 631532425 | Breaker 03 |

- Event281273126 的 Actions 为 `3388979775, 4011774951, 254514827`；第一项 PlayEvent 调用完整原 Event302768804。原 Event302768804 仍只有 `51759545`，因此 2020 不启动新增语音。右侧 Event3655102100 为 `648832766, 1866468495`；左侧 Event3253425110 仍只有 `120830402`。每个新增 Action 仅有一个所属 Event，序列化顺序为子 Sound、容器、Play Action、所属 Event。
- 三个容器克隆 `58172267`：原体 SHA-256 `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`，原播放列表 `[(46149961,50000)]`，原 avoid-repeat=1。保留 Normal Random、单次选播、非连续模式，按表序替换子列表，权重均 50000，avoid-repeat 改为 0。直接父级由 717111903 改为 209038110；容器 Pitch 基准缺省、随机范围 `[-50.0,50.0]` cents。三个最终容器体 SHA-256 按序为：
  - `1e448d3da356472e8305b9247cb8518aa7292ce67b40150bdcae96cfe7f69c8c`
  - `4e837dd3701b18dd8d4113ada5535974e0a6e9ca60a09605f451ef652df8b610`
  - `1a6016233c7c433dba061964d783e44889891ff67394984189773a35cdc0e263`
- 子 Sound 使用 46 字节标准语音体：`original/nbnk/wp_cmn_epvsp.nbnk` 的 Sound890667980 / Media838569492，原体 SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。保留标准语音的 positioning `0xC1` 和混音设置，每个 Sound 只换自身 ID、Media ID 及对应容器的 DirectParentID。容器的外部父级锁定 `original/nbnk/pl_act_vo_event.nbnk` 中的 Actor-Mixer209038110（Bank3755575407，body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`），该参考 Bank 不打入 Mod。
- Container 1、3 不写延迟属性。Container 2 的 Play Action254514827 写 DelayTime（0x0F）基准 0 ms、范围偏移 `[0,50]` ms。选音、容器音高和 Action 延迟分别配置，WAV 中不加入延迟。

| 名称 | Stop Event ID | donor Stop Action ID / target | scope | transition / fade | exceptions | 新 Stop Action ID | 新 Stop target |
|---|---:|---|---|---|---|---:|---:|
| Container 1 停止 | 461444626 | 743936681 / 60034062 | Game Object | 200 ms / Linear | 空 | 2987046856 | 3610379736 |
| Container 2 停止 | 461444626 | 743936681 / 60034062 | Game Object | 200 ms / Linear | 空 | 3645807405 | 3391377780 |

Stop donor body SHA-256 为 `137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd`。只改克隆的 Action ID 与目标，保留其余属性，两个克隆在 Stop Event 前序列化；Event461444626 从 `743936681` 扩展为 `743936681, 2987046856, 3645807405`。不新增 Motion107 起点或 Motion108 停音。

本设计追加 8 个 Sound、3 个容器、6 个 Action 和 1 个 Event。原对象只调整原生停止 Event 与右侧炮击 Event 的 Action 列表（12→20、12→16 字节）；单设计 HIRC changed-byte count 为 15，payload 增量 +926。合并完整 shell Bank 后追加媒体 #43–58，原媒体和其它设计已有序号不变；HIRC changed-byte count 为 42，payload 增量 +2093。除声明的 DIDX、DATA、HIRC 变化外其它 chunk 字节不变。

以正式素材实测正常发射、未发射中断和钩爪负例。特别检查 Container 2 尚未开始播放时的中断：不得在中断后补响。探针的原生停止结果不代替实际容器与随机延迟的运行时验收。
