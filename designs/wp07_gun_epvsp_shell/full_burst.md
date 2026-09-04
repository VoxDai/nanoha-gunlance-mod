---
design_id: wp07_gun_epvsp_shell.full_burst
target_artifacts:
  - sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk
---

# 全弹发射

## 描述

保留 1–5 发全弹发射的原版底火、爆炸和空间路径；每次有效触发额外等概率随机播放四条「Shoot」之一，允许连续选中同一条，并产生 ±50 cents 随机音调偏移。

| 名称 | 动作或状态 | 预期行为 |
|------|------------|----------|
| 1–5 发全弹发射 | 实际消耗 1–5 发炮弹 | 保留原声，额外随机播放一条「Shoot」 |
| 连续全弹发射 | 再次完成任意炮弹数的全弹发射 | 重新独立等概率选择，允许与上次相同 |
| 成对空间路径 | 3–5 发全弹发射的另一条空间 Event | 原声保持不变，不重复播放语音 |
| 其它铳枪动作 | 非全弹发射动作 | 不播放本设计的「Shoot」 |

## 音频

| 名称 | 音频 | 响度（LUFS-I） | 播放方式 |
|------|------|----------------|----------|
| Shoot 01 | [nanoha_shoot_01](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_01(battle_of_aces.attack_voice.attack_03.1).wav>) | -21 LUFS-I | 追加独立媒体，权重 `25000`（25%）；一次触发仅选一条 |
| Shoot 02 | [nanoha_shoot_02](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_02(gears_of_destiny.attack_voice.attack_03.1).wav>) | -21 LUFS-I | 追加独立媒体，权重 `25000`（25%）；与其它三条共用 Container |
| Shoot 03 | [nanoha_shoot_03](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_03(movie_1st.nanoha.shoot_02.1).wav>) | -21 LUFS-I | 追加独立媒体，权重 `25000`（25%）；与其它三条共用 Container |
| Shoot 04 | [nanoha_shoot_04](<../../audio/wp07_gun_epvsp_shell/full_burst/nanoha_shoot_04(movie_1st.nanoha.shoot_03.1).wav>) | -21 LUFS-I | 追加独立媒体，权重 `25000`（25%）；与其它三条共用 Container |

四份最终 WAV 均为 48 kHz、stereo、24-bit PCM，依次为 58000／30000／54000／42000 帧
（1.208333／0.625／1.125／0.875 秒），实测响度为 -20.99／-20.98／-21.00／-21.00 LUFS-I，true peak 为
-15.76／-15.09／-13.56／-12.26 dBTP。构建只无增益下混为 48 kHz、16-bit mono
Wwise PCM WEM，channel config `000001410000`；不在构建时校正响度。

## 实现契约

- 原始 Bank：`original/nbnk/wp07_gun_epvsp_shell.nbnk`，Wwise v120，Bank ID `3273965928`。

| 名称 | Event ID | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|------|----------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| 1 发全弹发射 | 2727643338 | 449657149 | 108007348 → 853759195 | 219848096 / 768048455 | #34 / 768048455 | 3386055930 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 2 发全弹发射 | 2727643337 | 646158903 | 58172267 → 853759195 | 46149961 / 669932693 | #30 / 669932693 | 4199321359 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 3 发全弹发射 | 1124197610 | 19077629 | 246916390 → 853759195 | 641882349 / 31902971 | #2 / 31902971 | 4100049135 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 4 发全弹发射 | 680296805 | 223369281 | 505597934 → 853759195 | 68448090 / 385933384 | #15 / 385933384 | 4272498343 | 960803121 / 479969098 / 2544331946 / 4251385954 |
| 5 发全弹发射 | 1765608260 | 403102539 | 885313651 → 853759195 | 994484287 / 272642002 | #9 / 272642002 | 3047212046 | 960803121 / 479969098 / 2544331946 / 4251385954 |

- 原媒体和原播放对象保持 byte-exact。Shoot 01 追加为 DIDX #43 / Media `242768048`；保留同 artifact owner 的龙击炮媒体
  DIDX #44–#46 及其顺序，再追加 Shoot 02–04 为 DIDX #47 / Media `954495929`、#48 / Media `2170495128`、#49 /
  Media `2062876979`。
- 五个 Event 的 Action 列表分别固定为 `(449657149, 3386055930)`、`(646158903, 4199321359)`、
  `(19077629, 4100049135)`、`(223369281, 4272498343)`、`(403102539, 3047212046)`；原 Action 始终在第一项，
  新 Action 均为无 delay Play 并指向 Random `853759195`。
- Random `853759195` 克隆原 Container `58172267`；donor 为 83-byte body，SHA-256
  `53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7`，原 playlist 为
  `((46149961, 50000),)`、`avoid-repeat=1`。新 playlist 固定为
  `((960803121, 25000), (479969098, 25000), (2544331946, 25000), (4251385954, 25000))`、
  `avoid-repeat=0`；保留 Random/Normal、one-shot、禁用 transition、每次播放重置、无本地 Volume 与实例上限设置。
- 新 Random body `+0x0B` 的父级从 `717111903` 改为标准语音 Actor-Mixer `209038110`；局部 Pitch 基值缺省，随机范围固定为
  `(-50.0, 50.0)`。最终 body 为 119 bytes，SHA-256
  `6ed503ce5f4b061e412c7221932068fb105c4cb11b72e68fa4125d76ab879895`。
- 四个 Sound 使用标准 46-byte 语音模板，Sound / Media 映射依次为 `960803121 / 242768048`、
  `479969098 / 954495929`、`2544331946 / 2170495128`、`4251385954 / 2062876979`；DirectParentID 均为
  `853759195`，body `+0x20` 的 `PositioningParams.uByVector=0xC1`，无本地 Pitch，不叠加第二份随机偏移。模板来源为
  `original/nbnk/wp_cmn_epvsp.nbnk` 的 Sound `890667980` / Media
  `838569492`，原 body SHA-256 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`；沿用项目已验证的
  Container 语音层级。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：Bank ID `3755575407`、Actor-Mixer
  `209038110` body SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 原 Bank 的 Stop Action 仅以 `60034062`、`662442083`、`1054468797`、`956375262`、`599243561` 为目标，未命中五条
  全弹原播放根或其父链；新 Random 不新增 Stop Action。3–5 发的成对空间路径只向表中 Event 追加语音，另一条成对 Event 及其
  Action 列表保持 byte-exact。
- 序列化顺序固定为四个 Sound → Random；每条新 Action 均序列化在对应 Event 之前。本设计新增 4 个 Sound、1 个 Random 和
  5 个 Action，扩长 5 个原 Event，changed-byte count 为 `9`、HIRC 增量为 `+463`。与 `wyverns_fire` 合并后媒体共 49 项、
  HIRC 对象 `181→199`、payload `11090→11851`、changed-byte count 为 `14`、HIRC 增量为 `+761`；除 DIDX、DATA 和上述
  HIRC 变化外，其它 Bank 内容保持 byte-exact。
- 新 Media `954495929`、`2170495128`、`2062876979` 与 Random `853759195` 分别由
  `wwise_fnv1("nanoha_wp07_gun_epvsp_shell_full_burst_" + suffix)` 的 `shoot_02_media`、`shoot_03_media`、
  `shoot_04_media`、`random_container` 派生；既有 Shoot 01 Media、四个 Sound 和五个 Action ID 保持不变。全部 ID 已对原 Bank
  的 42 个 Media、181 个 HIRC 对象及同 owner 的龙击炮自定义 ID 完成碰撞检查。
