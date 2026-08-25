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

| 名称                       | 音频                                                                                                                                                     | 播放方式                                                         |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| Raising Heart「Reload」    | [raising_heart_reload_01](<../../audio/wp_gun_cmn/reload/raising_heart_reload_01(movie_2nd_as.raising_heart.reload.1).wav>)                              | 追加独立媒体；以无 delay Action 与 DIDX #1 原声同步播放一次      |

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
- 新 Sound 克隆 donor `176748589`，只替换 Sound ID 和媒体引用；保留 DirectParentID `411055943`、OverrideBusId `0`、声道、
  输出、`0xC0` 定位、`3015692424, 0, 0, 0` Aux 路由及其它属性，不改为本地 2D。Container `411055943` 保持 byte-exact，
  继续仅包含 donor Sound、权重 `50000`、avoid-repeat `1` 的原随机播放列表；新 Sound 不加入该 Container。
- 本设计单独使 HIRC 对象数由 `123` 增至 `125`、payload 由 `7250` 增至 `7354`；新增 1 个 Sound 和 1 个 Action，Event
  `3476627122` 由 `12` 增至 `16` 字节，changed-byte count 为 `1`、payload 增量为 `+104`。与 `stationary_draw` 和
  `overhead_smash` 合并后，DIDX 共 36 项，HIRC 对象数由 `123` 增至 `133`、payload 由 `7250` 增至 `7632`、累计
  changed-byte count 为 `3`。
- 新 Media `1284288484`、Sound `1474128429` 和 Action `3418611510` 分别由
  `raising_heart_wp_gun_cmn_reload_media`、`raising_heart_wp_gun_cmn_reload_sound` 和
  `raising_heart_wp_gun_cmn_reload_action` 的 `wwise_fnv1()` 值固定，已通过原 Bank 全部 Media/HIRC ID 及现有两个设计已占用
  ID 的碰撞检查。除追加 DIDX/DATA、新 Sound、新 Action 和目标 Event Action 列表扩展外，其它 Bank 内容与既有对象顺序保持
  byte-exact。
