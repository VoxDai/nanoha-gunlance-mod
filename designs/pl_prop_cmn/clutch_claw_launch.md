---
design_id: pl_prop_cmn.clutch_claw_launch
target_artifacts:
  - sound/wwise/Windows/pl_prop_cmn.nbnk
---

# 飞翔爪发射

## 描述

保留发射钩爪飞向楔虫、翼龙或怪物时的原版绳索拉伸声；同一 Event 每次触发时同步追加一次 Raising Heart「Flier Fin」语音，并重新产生
`[-50, +50] cents` 随机音调偏移。

| 名称         | 动作或状态                           | 预期行为                                                           |
|--------------|--------------------------------------|--------------------------------------------------------------------|
| 飞翔爪发射   | 发射钩爪并触发 DIDX #79              | 保留原版绳索声，同步追加一次具有 ±50 cents 随机音调的「Flier Fin」 |
| 共用钩索路径 | 飞向楔虫、翼龙或怪物并触发同一 Event | 每次触发均只追加一次语音，并重新随机音调                           |
| 发射落空     | 未触发 DIDX #79 对应 Event           | 不播放追加语音                                                     |
| 其它动作     | 未进入本设计 Event 的动作            | 不播放追加语音                                                     |

## 音频

| 名称                       | 音频                                                                                                                                           | 响度（LUFS-I） | 播放方式                                                                                      |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------------------|
| Raising Heart「Flier Fin」 | [raising_heart_flier_fin_01](<../../audio/pl_prop_cmn/clutch_claw_launch/raising_heart_flier_fin_01(movie_1st.raising_heart.flier_fin.1).wav>) | -24 LUFS-I     | 追加独立媒体，以带 ±50 cents 随机 Pitch 的标准语音 Sound 和无 delay Action 与原声同步播放一次 |

最终 WAV 为 48 kHz、stereo、24-bit PCM、48000 帧（1 秒），实测响度为 -23.5 LUFS-I。构建时不做增益、归一化或响度修正，只无增益下混为
48 kHz、16-bit mono Wwise PCM WEM，channel config `000001410000`。

## 实现契约

- 原始 Bank：`original/nbnk/pl_prop_cmn.nbnk`，Wwise v120，Bank ID `4182706408`。

| 名称                   | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------------------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 飞翔爪发射（追加语音） | 1419271252 | 546716350    | 334024264    | 653757911 / 334975050  | #79 / 334975050    | 1404747944   | 137314667   |

- 原始 DIDX #1–#241 保持 byte-exact；追加语音为 DIDX #242 / Media ID `259390702`。原 Media `334975050`、Sound `653757911` 和
  Random Container `334024264` 均不修改。
- Event `1419271252` 的 Action 列表由 `546716350` 变为 `546716350, 1404747944`，原 Action 始终在第一项；新 Action 为无
  delay Play，目标为新 Sound `137314667`，并序列化在目标 Event 之前。原 Sound、Random、Action、Event body 的 SHA-256 依次为
  `a82d8dc855b6b2051ff301e163a5f8a9d740012b49192f8d512432a3d650a06d`、
  `7cc917007a8d22b7aa678acebf3c3f08d3dc224cc5201024555ce56485a39b4c`、
  `015cffb4b6d6b5f2841719a2a2a2be8b1060bba94775c3bb52622f945498a6f7`、
  `8179cc400c084912d8bbf4ae9feb09cfdd4068e37da1f7fcfd80ffc54da02b61`。
- 新 Sound 以 46-byte 标准语音 body 为模板：来源为 `original/nbnk/wp_cmn_epvsp.nbnk` 的 Sound `890667980` / Media
  `838569492`（原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），仅替换 Sound ID 与
  Media ID，固定 `DirectParentID=209038110`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`。以
  `HircPitchSettings(None, None)` 为 guard，在新 Sound 插入随机 Pitch 范围 `(-50.0, 50.0)`，基础 Pitch 保持缺省；最终 body
  为 55 字节，SHA-256 为 `9d675712ffb82adbf9da68bc14d64c09bc3bec7b2115f73d2f53598b5c1fa409`。新 Action body SHA-256 仍为
  `069217cd5ae92ad8de3fb1197943cc225635593e338597115f8f113b0f8db071`；扩展后的 Event body SHA-256 仍为
  `e782c444805654508990b381a6a5d5b37d020f3a1e573762b4cc3472ba06cae3`。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：Bank ID `3755575407`、Actor-Mixer `209038110` body SHA-256
  `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 原生播放父链为 `334024264 → 917544551 → 694534885`。所有由 Event 引用的 Stop Action 均未命中该父链，因此不新增 Stop
  Action；语音自然播放至结束。
- 序列化顺序固定为新 Sound → 新 Action → 原 Event。本设计将媒体数由 `241` 增至 `242`、HIRC 对象数由 `742` 增至 `744`
  、payload 由 `40542` 增至 `40629`；Event 由 `12` 增至 `16` 字节，changed-byte count 为 `9`、payload 增量为 `+87`。除
  DIDX、DATA、带本地随机 Pitch 的新 Sound、新 Action 和目标 Event Action 列表扩展外，其它 Bank 内容保持 byte-exact。
- 新 Media `259390702`、Sound `137314667` 和 Action `1404747944` 分别由
  `wwise_fnv1("raising_heart_pl_prop_cmn_clutch_claw_launch_" + suffix)` 的 `media`、`sound` 和 `action` 派生；均已通过原
  Bank 全部 Media/HIRC ID 的碰撞检查。
