---
design_id: wp_gun_cmn.wide_sweep
target_artifacts:
  - hm/wp/wp07/mot/w07_00/w07_00.lmt
  - sound/pl/hm_wp07_snd_ev.wwev
  - sound/wwise/Windows/wp_gun_cmn.nbnk
---

# 横扫

## 描述

保留普通地面横扫的全部原声，在第 11 帧独立叠加一次奈叶「Smasher」。两份素材分别以 70%／30% 概率随机播放，允许连续重复，每次由专属 Container 施加 ±50 cents 音调偏移。

| 名称 | 动作或状态 | 预期行为 |
|------|------------|----------|
| 普通横扫 | 下砸或全弹发射后进入普通地面横扫 | 第 11 帧与较早的金属声同步，随机播放一条 Smasher |
| 后续原声 | 同一横扫的第 27／49 帧 | 保留金属声、挥动声及两条条件路线，不额外播放 Smasher |
| 原人物语音 | Motion 143 的 EventGroup02 | 第 27 帧攻击语音保持未触发，第 166 帧人物语音保持原样 |
| 其它动作 | 拔刀、收刀、装填、下砸、空中强横扫及登墙横扫 | 不因本设计新增 Smasher；既有 Mod 语音保持原状 |
| 连续横扫 | 再次进入目标触发帧 | 每次选择一条语音，不设置新增冷却或实例上限 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|----------------|----------|
| Smasher 01 | [nanoha_smasher_01](<../../audio/wp_gun_cmn/wide_sweep/nanoha_smasher_01(gears_of_destiny.attack_voice.attack_05.1).wav>) | -21 LUFS-I | 追加独立媒体，权重 70000（70%）；一次横扫仅选一条 |
| Smasher 02 | [nanoha_smasher_02](<../../audio/wp_gun_cmn/wide_sweep/nanoha_smasher_02(movie_2nd_as.nanoha.smasher.1).wav>) | -21 LUFS-I | 追加独立媒体，权重 30000（30%）；与 01 共用 Container |

两份最终 WAV 均为 48 kHz、stereo、24-bit PCM，分别为 54000／72000 帧（1.125／1.5 秒），实测均为 -20.99 LUFS-I，true peak 为 -16.52／-14.30 dBTP。最终 SHA-256 分别为 `5b1ce355a0729b0c7ccd4de9755440775b57deeb86698a652750b851f3e05727`、`d27d09b8087ca87814d411f53972053c28c80db8d678c7cb808e8343efa4ebd2`。构建只无增益下混为 48 kHz、16-bit mono Wwise PCM，channel config `000001410000`；不在构建时校正响度。

## 实现契约

- 原始 Bank：`original/nbnk/wp_gun_cmn.nbnk`，Wwise v120，Bank ID `939294496`，SHA-256 `bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1`。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 11 帧原声委托 | 2467230206 | 281299658 | 5732403 | 402899610 / 367086010 | #6 / 367086010 | 2768755612 / 3181937101 | 102041635 / 3822519236 |

- 原 Event 的 Action 列表固定为 `(281299658,)`，该 Action 是无 delay 的 Play，指向原 Container `5732403`。本设计不修改原声对象。新 Event `4096779774` 固定为 Action 列表 `(2768755612, 3181937101)`：第一条为 PlayEvent 委托完整原 Event `2467230206`，第二条为无 delay Play，目标 Random `3645186695`。
- 两份媒体在既有 DIDX #34–#36 后追加为 #37 / Media `1484106982`、#38 / Media `2274559001`。原 DIDX #1–#33 的身份与媒体载荷不变；既有三个追加媒体和路线不变。仅允许 DIDX/DATA 追加与上述 HIRC 新对象，保留其它 chunk。
- Random `3645186695` 克隆原 Container `570218704`，完整 donor body SHA-256 `be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427`。原 playlist 为 `((647150707, 50000),)`、avoid-repeat=1；新 playlist 为 `((102041635, 70000), (3822519236, 30000))`、avoid-repeat=0。body `+0x0B` 的父级从 `768813060` 改为 `209038110`。保留 donor 的 Random/Normal、one-shot、禁用 transition、无本地 Volume 与实例上限设置；局部 Pitch 基值缺省（0 cents），随机范围固定为 `(-50.0, 50.0)`。最终 95-byte body SHA-256 `369e0b6264741e600b9e87a2a05034365fcaafa6ae82a19ed178d66357fc0efd`。
- 两个 Sound 使用标准 46-byte 语音模板，来源为 `original/nbnk/wp_cmn_epvsp.nbnk`（SHA-256 `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media `838569492`，原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`。仅改 Sound/Media ID、`DirectParentID=3645186695` 和 body `+0x20` 的 positioning vector 为 `0xC1`；沿用已确认 11 帧测试版的 Container 语音层级。
- 语音父级由 `original/nbnk/pl_act_vo_event.nbnk` 固定（SHA-256 `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`）。该父级及上级 `694534885` 无局部 Pitch；两个新 Sound 也无局部 Pitch，不叠加第二份随机偏移。原播放根及其父链未发现原生 Event 引用的匹配 Stop，不新增 Stop。两个参考 Bank 不打入 Mod。
- 序列化顺序为两个 Sound → Random → 原声委托 Action → 语音 Play Action → 新 Event。本设计新增 2 个 Sound、1 个 Random、2 个 Action、1 个 Event，HIRC 增量 `+264`、changed-byte count `4`（新 Random 的父级修改）。与当前全部既有 Bank 设计合并，媒体 38 项、HIRC 对象 `123→140`、payload `7250→7831`，总增量 `+581`、changed-byte count `5`；既有 reload Event `3476627122` 仍是唯一扩长的原对象，body `12→16`。

| 名称 | LMT | Motion | EventGroup | Slot | 赋值帧 | 原 ReqNo | 新 ReqNo | 预期触发帧 |
|------|-----|--------|------------|------|--------|----------|----------|------------|
| 横扫 | `original/lmt/w07_00.lmt` | 143 | EventGroup06 | A | 0 | 6486 | 6596 | 11 |

| 名称 | WWEV | donor ReqNo | donor Event ID | mode | record SHA-256 | 新 ReqNo | 新 Event ID |
|------|------|-------------|----------------|------|----------------|----------|-------------|
| 横扫 | `original/wwev/hm_wp07_snd_ev.wwev` | 6486 | 2467230206 | 100 | `7acef10768c67f1bd791873f65a0c345e00c9e24c50428e4c5ad2cae4bbabbfb` | 6596 | 4096779774 |

- LMT 为 v95，SHA-256 `7897e766963b177b2dc157f65204e8a4ef9a35aba4b294c8d0f0635209800b94`。Motion 143 共 187 帧，TIML `0x124BE0` 仅由该 Motion 使用。仅替换槽位 A 在第 0 帧的请求赋值：记录位置 `1202416`，预期触发帧 `(11.0,)`、trigger mask `0x01`，额外改变 1 字节。与既有 Motion 2、128、131 修改合并后 changed-byte count 为 `6`，文件长度不变。所有其它 TIML 数据保持原样，包括 EventGroup02 第 0 帧槽位 A 的 ReqNo 1129、第 27 帧 trigger=0 及第 166 帧槽位 B 的 ReqNo 1009。
- WWEV 为 v19，SHA-256 `82c7162f3cb502e3ce3e1e7c1e6ff4823d373a764148d6d761f675420bcd2a0f`。ReqNo 6486 必须仅解析出原记录 #22、mode 100、上述 Event 与完整 raw hash；新 ReqNo／Event 必须未占用。用 `append_cloned_record()` 完整克隆为 #45，仅改 ReqNo 和 Event，保留 command、unknown、WWPC，追加 129 字节。原 43 条记录和四个依赖字符串 byte-exact，既有 #44 不变，总记录数 45，总追加 `258` 字节。新记录 raw SHA-256 为 `d4a45c5e6c512f1b9688decbe9ad966e606a5674b7307ad469e6a8c60a9b8637`。
- 后续原声保持原路线：EventGroup06 第 27 帧槽位 F 为 ReqNo 6488 → Event `2467230204`；第 49 帧槽位 E 为 ReqNo 6410，按原顺序展开为 mode 200 的 Event `252365729`／`3350794741`，两条条件记录均保留。ReqNo 6488 的原 raw hash 为 `f1ad3a74af5e568cbf058b9fa10b4df01459042fd40e7b62989b51b0e3e957d9`；ReqNo 6410 两条原 raw hash 依次为 `e7fd989c59feb3d3543d02dd77ac79113f435212f795ed371cafc59a042d218c`、`9f39b9a7d1443461da8e5e75d6b9d7a62b54badd488494714312df74fd2553f2`。不追加 ReqNo 6597／6598 及 Event `1359210849`／`2281439929`。
- 所有新增 ID 均为 `wwise_fnv1("nanoha_wp_gun_cmn_wide_sweep_" + suffix)`：媒体与 Sound 使用 `smasher_01_media`／`smasher_02_media`／`smasher_01_sound`／`smasher_02_sound`，Container 使用 `random_container`，Event／Action 使用 `frame11_event`／`frame11_original_action`／`frame11_voice_action`。这些 ID 与 ReqNo 6596 已通过原版 4550 个 NBNK、1300 个 WWEV 的占用检查；同时须拒绝与当前已注册自定义 ID 冲突。
- 三个既有 artifact owner 均登记本 design ID，正式七件套保持唯一归属。跨文件验证必须在完整动画触发表中恰好解析出一次 Motion 143／EventGroup06／槽位 A／第 11 帧／ReqNo 6596／记录 #45／mode 100／Event `4096779774`，并验证完整原声委托、Random 权重与 Pitch、Sound 父级、媒体和序列化顺序；保留全部既有 bundle validators。
