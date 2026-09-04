---
design_id: wp_cmn_epvsp.sharpen
target_artifacts:
  - sound/wwise/Windows/wp_cmn_epvsp.nbnk
---

# 磨刀完成

## 描述

保留磨刀完成原声；完成磨刀时同步叠加一份 Raising Heart 语音，在「Charging Completed」与「Condition Green」之间等概率随机选择，每次播放重新产生 ±50 cents 随机音调偏移。

| 名称         | 动作或状态             | 预期行为                                                       |
|--------------|------------------------|----------------------------------------------------------------|
| 磨刀完成     | 完成整个磨刀动作       | 保留原声，并同步随机额外播放一份 Raising Heart 语音            |
| 连续磨刀完成 | 再次完成整个磨刀动作   | 重新随机选择语音与音调，允许连续选中同一份                     |
| 磨刀中断     | 磨刀取消或被中断       | 不播放两份追加语音                                             |
| 其它通用动作 | 非磨刀完成动作         | 不播放两份追加语音                                             |

## 音频

| 名称                                | 音频                                                                                                                                                              | 响度（LUFS-I） | 播放方式                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------|
| Raising Heart「Charging Completed」 | [raising_heart_charging_completed_01](<../../audio/wp_cmn_epvsp/sharpen/raising_heart_charging_completed_01(movie_1st.raising_heart.charging_completed.1).wav>)     | -24 LUFS-I     | 追加独立媒体，权重 `50000`；与 Condition Green 等概率随机并继承 Container Pitch |
| Raising Heart「Condition Green」    | [raising_heart_condition_green_01](<../../audio/wp_cmn_epvsp/sharpen/raising_heart_condition_green_01(movie_1st.raising_heart.condition_green.1).wav>)             | -24 LUFS-I     | 追加独立媒体，权重 `50000`；与 Charging Completed 等概率随机并继承 Container Pitch |

两份最终 WAV 均为 48 kHz、stereo、24-bit PCM、72000 帧（1.5 秒）。Charging Completed 实测为 `-24.01 LUFS-I`、`-11.32 dBTP`；
Condition Green 以恒定 `-0.67 dB` 线性增益标准化后实测为 `-23.99 LUFS-I`、`-13.78 dBTP`。
播放与磨刀完成原声同时开始，不设 delay；Random Container 的 `avoid-repeat=0`，每次独立随机选择并允许连续重复。Container 的局部
Pitch 基值缺省，随机范围为 `[-50, +50] cents`；两个 Sound 不设置本地 Pitch。构建时不做增益、归一化或响度修正，只无增益下混为
48 kHz、16-bit mono Wwise PCM WEM，channel config `000001410000`。

## 实现契约

- 原始 Bank: `original/nbnk/wp_cmn_epvsp.nbnk`，Wwise v120，SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`
- Bank ID: `1149256632`

| 名称                                | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|-------------------------------------|----------|----------------|--------------|------------------------|--------------------|--------------|-------------|
| 磨刀完成（Charging Completed）      | 166276485 | 579012432     | 306760817    | 890667980 / 838569492  | #52 / 838569492    | 487645987    | 84645870    |
| 磨刀完成（Condition Green）         | 166276485 | 579012432     | 306760817    | 890667980 / 838569492  | #52 / 838569492    | 487645987    | 2168824776  |

- 原有 71 份媒体及载荷保持 byte-exact；依次追加 Charging Completed 为 DIDX #72 / Media ID `2791080207`、Condition Green 为
  DIDX #73 / Media ID `2163208725`。两份运行时媒体均须读回为 48 kHz、16-bit mono Wwise PCM、72000 samples。
- 原声播放路径保持 byte-exact：Action `579012432` → Random `306760817` → Sound `890667980` → DIDX #52 /
  Media `838569492`。Event 的 Action 列表固定为 `579012432, 487645987`，原 Action 保持第一项；新 Action `487645987` 为无 delay
  Play，目标新 Random Container `3800640078`，最终 18-byte body SHA-256 为
  `21ca6e777442d1b1f1f0e0a57ae207aaa599e428113b4dcb50fbe45b02228f5d`。
- 新 Random `3800640078` 克隆原 Container `306760817`；donor 为 109-byte body，SHA-256
  `5f4b68b79ee8809c2c1f6bc8ed3dfde2e247e7c42a25e2b97b31cd58feb7fca0`，原 playlist 为 `((890667980, 50000),)`、
  `avoid-repeat=1`、局部 Pitch 为 `HircPitchSettings(None, (-25, 25))`。新 playlist 固定为 Sound `84645870` / 权重 `50000` 与
  Sound `2168824776` / 权重 `50000`，`avoid-repeat=0`；保留 donor 的 Random/Normal、one-shot、禁用 transition、每次播放重置
  playlist、global 及其它未建模字段。
- 新 Random body `+0x0B` 的父级从 `914939451` 改为标准语音 Actor-Mixer `209038110`；以
  `HircPitchSettings(None, (-25, 25))` 为 guard，仅将随机范围改为 `(-50, 50)`，基础 Pitch 保持缺省。最终 body 为 121 字节，
  SHA-256 `30dac3ea0e65598e2b1aa56e6cdca67ad72a016908dfdec627a8f744851fcec9`。
- 两个新 Sound 均使用 donor `890667980` / Media `838569492` 的 46-byte 标准语音 body；原 body SHA-256 为
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`，标准 C1 donor-ID body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。仅替换各自 Sound / Media ID，将
  `DirectParentID=3800640078`，并将 body `+0x20` 的 `PositioningParams.uByVector` 固定为 `0xC1`；Charging Completed 与
  Condition Green 的最终 body SHA-256 分别为 `5052b089e940f8b99e5b4f8091ebfa54f5e6de51fa09e4a1854a8c2f1598518e`、
  `25b4895802884802a7955c98a9357d8b9de7e29d196c40f2da2753b38fca268d`。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 原生播放根及父级链为 `306760817 → 914939451 → 972300144 → 694534885`；未发现由原生 Event 引用且以该链任一对象为目标的
  Stop Action，因此不新增 Stop 路由。
- 新 ID 使用 `wwise_fnv1("nanoha_wp_cmn_epvsp_sharpen_" + suffix)`：Container suffix 为 `random_container`，Condition Green
  的 Media / Sound suffix 分别为 `condition_green_01_media` / `condition_green_01_sound`；所得 ID 依次为 `3800640078`、
  `2163208725`、`2168824776`。Action `487645987`、Charging Completed Sound `84645870` / Media `2791080207` 保持既有稳定 ID；
  所有 ID 已通过原 Bank 全部 Media、HIRC 与当前已注册自定义 ID 的碰撞检查。
- 序列化顺序固定为 Charging Completed Sound → Condition Green Sound → Random `3800640078` → Action `487645987` → Event
  `166276485`。内存原型读回摘要固定为：媒体 `71→73`、HIRC 对象 `299→303`、HIRC payload `25179→25434`、增量 `+255`、
  changed-byte count `9`、Event body `12→16`；Event 最终 body SHA-256 为
  `46edd54989cd71ac293633f9c954950476e8f2e33c01e3359fcaab913fa4ae95`。除 DIDX / DATA 追加、上述四个新 HIRC 对象及目标 Event
  扩展外，其它 Bank chunk、原媒体和原 HIRC 对象保持 byte-exact。
- 游戏内按描述表验收：磨刀完成时原声与一份随机语音同步播放，两份语音均可被选中、允许连续重复且每次音调重新随机；磨刀中断与其它
  通用动作不播放追加语音。结构验证只证明 Bank、路由、媒体和 Pitch 契约，最终触发、听感与随机分布须在可恢复游戏环境中确认。
