---
design_id: wp_gun_cmn.reload
target_artifacts:
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 装填

## 描述

保留完整装填和起爆龙航装填的原版机械音；在两种动作触发 DIDX #1 原声时同步追加一次 Raising Heart「Reload」，不污染快速装填或其它铳枪动作。

| 名称         | 动作或状态                     | 预期行为                                      |
|--------------|--------------------------------|-----------------------------------------------|
| 完整装填     | 执行会触发 DIDX #1 的完整装填  | 保留全部原声，并同步额外播放一次「Reload」    |
| 起爆龙航装填 | 装填起爆龙航并触发 DIDX #1     | 保留全部原声，并同步额外播放一次「Reload」    |
| 快速装填     | 执行快速装填                   | 不播放「Reload」                              |
| 其它铳枪动作 | 非上述两种 DIDX #1 装填路径    | 不播放「Reload」                              |

## 音频

| 名称                    | 音频                                                                                                                        | 响度（LUFS-I） | 播放方式                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------|----------------|------------------------------------------------------------------------------|
| Raising Heart「Reload」 | [raising_heart_reload_01](<../../audio/wp_gun_cmn/reload/raising_heart_reload_01(movie_2nd_as.raising_heart.reload.1).wav>) | -24 LUFS-I     | 追加独立媒体；以标准语音 Sound 和无 delay Action 与 DIDX #1 原声同步播放一次 |

## 实现契约

- 原始 Bank: `original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`，SHA-256
  `bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1`。

| 名称                  | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|-----------------------|------------|----------------|--------------|------------------------|--------------------|----------------|-------------|
| 装填（追加语音）      | 3476627122 | 126049847      | 411055943    | 176748589 / 86782159   | #1 / 86782159      | 3418611510     | 1474128429  |

- 原始 DIDX #1–#33 保持 byte-exact；在 `stationary_draw` 的 DIDX #34 和 `overhead_smash` 的 DIDX #35 之后，追加语音为
  DIDX #36 / Media ID `1284288484`。本设计不修改前两个设计追加的媒体。
- Event `3476627122` 的 Action 列表由 `126049847` 变为 `126049847, 3418611510`，原 Action 始终在第一项；新 Action 为无
  delay 的 Play，目标新 Sound `1474128429`，并序列化在目标 Event 之前。
- 表中 donor `176748589` 及 Container `411055943` 只作为原路径 guard；新 Sound 使用 46-byte 标准语音 body，来源为
  `original/nbnk/wp_cmn_epvsp.nbnk`（文件 SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media `838569492`（原 body SHA-256
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`），仅替换 Sound ID 与 Media ID，固定
  `DirectParentID=209038110`、body `+0x20` 的 `PositioningParams.uByVector=0xC1`；标准 body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。Container 保持 byte-exact，继续仅包含 donor
  Sound、权重 `50000`、avoid-repeat `1` 的原随机播放列表；新 Sound 不加入该 Container。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 项目 WAV 固定为 48 kHz、stereo、24-bit PCM，并保持音频表记录的 -24 LUFS-I；构建时不做增益、归一化或响度修正，只无增益下混为
  48 kHz、16-bit mono Wwise PCM WEM。
- 本设计单独使 HIRC 对象数由 `123` 增至 `125`、payload 由 `7250` 增至 `7328`；新增 1 个 Sound 和 1 个 Action，Event
  `3476627122` 由 `12` 增至 `16` 字节，changed-byte count 为 `1`、payload 增量为 `+78`。与 `stationary_draw` 和
  `overhead_smash` 合并后，DIDX 共 36 项，HIRC 对象数由 `123` 增至 `133`、payload 由 `7250` 增至 `7554`、累计
  changed-byte count 为 `1`。
- 新 Media `1284288484`、Sound `1474128429` 和 Action `3418611510` 分别由
  `raising_heart_wp_gun_cmn_reload_media`、`raising_heart_wp_gun_cmn_reload_sound` 和
  `raising_heart_wp_gun_cmn_reload_action` 的 `wwise_fnv1()` 值固定，已通过原 Bank 全部 Media/HIRC ID 及现有两个设计已占用
  ID 的碰撞检查。除追加 DIDX/DATA、新 Sound、新 Action 和目标 Event Action 列表扩展外，其它 Bank 内容与既有对象顺序保持
  byte-exact。
