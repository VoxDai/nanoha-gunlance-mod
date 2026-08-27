---
design_id: hm_cm00_epvsp.gunlance_guard
target_artifacts:
  - sound/wwise/Windows/hm_cm00_epvsp.nbnk
---

# 铳枪盾牌防御

## 描述

保留共享防御 Event 的原版声音与路由；仅当 `pl_weapon_type` 为枪铳时，在原声之外等概率随机追加一条 Raising
Heart「Protection」语音。其它武器命中同一 Event 时只经过 10 ms 静音回退，不播放自定义语音。

| 名称             | 动作或状态                           | 预期行为                                    |
|------------------|--------------------------------------|---------------------------------------------|
| 铳枪盾牌防御     | 枪铳命中共享防御 Event               | 保留原声，额外等概率播放一条「Protection」  |
| 连续防御         | 当前「Protection」仍在播放时再次防御 | 不打断当前语音，也不启动下一条语音          |
| 防御语音播放结束 | 当前 5 秒语音已结束后再次防御        | 允许重新等概率播放一条「Protection」        |
| 其它武器防御     | 非枪铳武器命中同一共享防御 Event     | 保留各自原声，仅播放不可闻的 10 ms 静音回退 |
| 非防御动作       | 未命中共享防御 Event                 | 不播放「Protection」或静音回退              |

## 音频

| 名称                           | 音频                                                                                                                                | 响度（LUFS-I）        | 播放方式                                            |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------|-----------------------------------------------------|
| Raising Heart「Protection 01」 | [raising_heart_protection_01](<../../audio/hm_cm00_epvsp/raising_heart_protection_01(movie_1st.raising_heart.protection_01.1).wav>) | -24 LUFS-I            | 独立媒体；权重 `50000`，与 Protection 02 等概率随机 |
| Raising Heart「Protection 02」 | [raising_heart_protection_02](<../../audio/hm_cm00_epvsp/raising_heart_protection_02(movie_1st.raising_heart.protection_02.1).wav>) | -24 LUFS-I            | 独立媒体；权重 `50000`，与 Protection 01 等概率随机 |
| 10 ms 静音回退                 | [silence_10ms](../../audio/hm_cm00_epvsp/silence_10ms.wav)                                                                          | -∞ LUFS-I（特殊静音） | 独立媒体；只供非枪铳或未匹配武器值的默认分支播放    |

两段 Protection 均为 48 kHz、stereo、24-bit PCM、5 秒，并保持表中记录的 -24 LUFS-I。静音回退是功能性特殊音频，允许不符合普通
语音的 24-bit 与命名规范；实际为 48 kHz、stereo、16-bit PCM、480 帧全零采样、-∞ LUFS-I，SHA-256 为
`94988ef93524fb8b65c1884f413729ae71b526e694d63aca79adf27e27b02222`。三份 WAV 构建时均不做增益、归一化或响度修正，只无增益下混为
48 kHz、16-bit mono Wwise PCM WEM。随机 Container 的 `avoid-repeat=0`；实例上限为 1，超过上限时采用 Kill Newest。

## 实现契约

- 原始 Bank: `original/nbnk/hm_cm00_epvsp.nbnk`，Wwise v120，SHA-256
  `73b52c1a69532f0a84ab6dfa2e95bd804bf8affc5af77450786d700c177a9977`
- Bank ID: `707566772`

| 名称          | Event ID   | 原 Action ID | Container ID | donor Sound / Media ID | DIDX / 原 Media ID | 新 Action ID | 新 Sound ID |
|---------------|------------|--------------|--------------|------------------------|--------------------|--------------|-------------|
| Protection 01 | 4072881687 | 601196071    | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 2154199438  |
| Protection 02 | 4072881687 | 601196071    | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 640829561   |
| 静音回退      | 4072881687 | 601196071    | 368774789    | 925721864 / 676385730  | #88 / 676385730    | 4197300369   | 3060148569  |

- 原始媒体数为 140、HIRC 对象数为 597、HIRC payload 为 33313 字节。原路线保持 byte-exact：Event `4072881687` → Action
  `601196071` → Switch `368774789` → Random `127521149` → Sound `925721864` → DIDX #88 / Media `676385730`。Event 只在尾部追加
  Action `4197300369`，Action 列表固定为 `601196071, 4197300369`；新 Action delay 为 `30 ms`，目标为 Switch `4010844647`。
- donor Switch `368774789` 的完整 body SHA-256 为 `a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde1358c02ab99043bb`
  ，Group `3251135135` 为 `pl_weapon_type`，默认值为 `3396333570`。新 Switch `4010844647` 只含两个 child：默认值
  `3396333570` → 静音 Sound `3060148569`，枪铳值 `3529994682` → Protection Random `3163089818`；两者 node params 均为
  behavior flags `0`、transition flags `1`、fade-out/in `0 ms`。其它 Switch package 不进入新路线。保留 donor 前缀与未建模属性，仅将
  body `+0x0B` 的父级从 `422956649` 改为 Actor-Mixer `209038110`，并显式重建上述 topology tail。
- Protection Random `3163089818` 克隆 donor `127521149`，body `+0x0B` 的父级从 donor Switch `368774789` 改为新 Switch
  `4010844647`；playlist 固定为 Sound `2154199438` / 权重 `50000` 与 Sound `640829561` / 权重 `50000`，`avoid-repeat=0`
  。body `+0x19` 从 `0x00` 改为 `0x01`（Kill Newest），body `+0x1B` 从 `0` 改为 `1`（实例上限）。
- 三个新 Sound 均使用 46-byte 标准语音 body：来源为 `original/nbnk/wp_cmn_epvsp.nbnk`（SHA-256
  `76b1bc422e3041fafc5db2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media `838569492`，原 body
  SHA-256 为 `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`，标准 C1 body SHA-256 为
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`。Protection 两个 Sound 的
  `DirectParentID=3163089818`，静音 Sound 的 `DirectParentID=4010844647`，三者 body `+0x20` 的
  `PositioningParams.uByVector=0xC1`。
- 外部父级由 `original/nbnk/pl_act_vo_event.nbnk` 锁定：文件 SHA-256
  `4830c1c0394a5af14f52adf8d7b96463032b7631f0e20061ee6a829da6358582`、Bank ID `3755575407`、Actor-Mixer `209038110` body
  SHA-256 `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`；该参考 Bank 不打入 Mod。
- 依次追加 DIDX #141 / Media `141209263`、#142 / Media `440767416`、#143 / Media `2901559960`。三份运行时媒体均为
  48 kHz、16-bit mono Wwise PCM，并由构建读回验证格式。
- 新 ID `4197300369`、`4010844647`、`3163089818`、`2154199438`、`640829561`、`3060148569`、`141209263`、`440767416`、
  `2901559960` 已通过原 Bank 全部 HIRC 与 Media ID 碰撞检查。读回摘要固定为：媒体 `140→143`、HIRC 对象 `597→603`、HIRC
  payload `33313→33734`、Event body `12→16`、changed-byte count `11`、HIRC 增量 `+421`。新增 HIRC 对象为三个 Sound、Random
  `3163089818`、Switch `4010844647`、Action `4197300369`；除 DIDX、DATA、HIRC 外其它内容保持 byte-exact。
