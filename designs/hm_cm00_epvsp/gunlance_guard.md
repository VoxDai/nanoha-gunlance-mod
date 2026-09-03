---
design_id: hm_cm00_epvsp.gunlance_guard
target_artifacts:
  - sound/wwise/Windows/hm_cm00_epvsp.nbnk
---

# 铳枪盾牌防御

## 描述

保留共享防御 Event 的原版声音与路由；仅当 `pl_weapon_type` 为枪铳时，在原声之外等概率随机追加一条 Raising
Heart「Protection」语音，每次有效播放随机产生 `[-50, +50] cents` 音调偏移。其它武器命中同一 Event 时只经过 10 ms
静音回退，不播放自定义语音。

| 名称             | 动作或状态                           | 预期行为                                    |
|------------------|--------------------------------------|---------------------------------------------|
| 铳枪盾牌防御     | 枪铳命中共享防御 Event               | 保留原声，两份「Protection」各以 50% 概率播放，音调随机偏移 ±50 cents |
| 连续防御         | 当前「Protection」仍在播放时再次防御 | 不打断当前语音，也不启动下一条语音          |
| 防御语音播放结束 | 当前语音实际播放结束后再次防御      | 重新随机选择语音及音调，允许连续选中同一份  |
| 其它武器防御     | 非枪铳武器命中同一共享防御 Event     | 保留各自原声，仅播放不可闻的 10 ms 静音回退 |
| 非防御动作       | 未命中共享防御 Event                 | 不播放「Protection」或静音回退              |

## 音频

| 名称                           | 音频                                                                                                                                | 响度（LUFS-I）        | 播放方式                                            |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------|-----------------------------------------------------|
| Raising Heart「Protection 01」 | [raising_heart_protection_01](<../../audio/hm_cm00_epvsp/raising_heart_protection_01(movie_1st.raising_heart.protection_01.1).wav>) | -24 LUFS-I            | 独立媒体；权重 `50000`，与 Protection 02 等概率随机；继承 Container 的 ±50 cents 随机音调 |
| Raising Heart「Protection 02」 | [raising_heart_protection_02](<../../audio/hm_cm00_epvsp/raising_heart_protection_02(movie_1st.raising_heart.protection_02.1).wav>) | -24 LUFS-I            | 独立媒体；权重 `50000`，与 Protection 01 等概率随机；继承 Container 的 ±50 cents 随机音调 |
| 10 ms 静音回退                 | [silence_10ms](../../audio/hm_cm00_epvsp/silence_10ms.wav)                                                                          | -∞ LUFS-I（特殊静音） | 独立媒体；只供非枪铳或未匹配武器值的默认分支播放    |

两段 Protection 均为 48 kHz、stereo、24-bit PCM、5 秒，并保持表中记录的 -24 LUFS-I。静音回退是功能性特殊音频，允许不符合普通
语音的 24-bit 与命名规范；实际为 48 kHz、stereo、16-bit PCM、480 帧全零采样、-∞ LUFS-I，SHA-256 为
`94988ef93524fb8b65c1884f413729ae71b526e694d63aca79adf27e27b02222`。三份 WAV 构建时均不做增益、归一化或响度修正，只无增益下混为
48 kHz、16-bit mono Wwise PCM WEM。随机 Container 的 `avoid-repeat=0`，两份语音各有 50% 概率，允许连续选中同一份。
每次有效播放在 Container 上随机产生 `[-50, +50] cents` 音调偏移；两个 Protection Sound 继承该偏移，不再添加本地
Pitch 属性。实例上限为 1，超过上限时采用 Kill Newest。素材文件时长保持 5 秒，运行时播放时长可随音调变化，连续防御的
抑制以当前语音实际播放结束为准。

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
- 原生 Play target Switch `368774789` 及其父级链 Actor-Mixer `422956649` → `694534885` 未发现由原生 Event 引用的匹配
  Stop Action，本路线不新增 Stop Action。
- donor Switch `368774789` 的完整 body SHA-256 为 `a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde1358c02ab99043bb`
  ，Group `3251135135` 为 `pl_weapon_type`，默认值为 `3396333570`。新 Switch `4010844647` 只含两个 child：默认值
  `3396333570` → 静音 Sound `3060148569`，枪铳值 `3529994682` → Protection Random `3163089818`；两者 node params 均为
  behavior flags `0`、transition flags `1`、fade-out/in `0 ms`。其它 Switch package 不进入新路线。保留 donor 前缀与未建模属性，仅将
  body `+0x0B` 的父级从 `422956649` 改为 Actor-Mixer `209038110`，并显式重建上述 topology tail。
- Protection Random `3163089818` 克隆 donor `127521149`，donor 的完整 79-byte body SHA-256 为
  `dd0dfececc9d361c76f00553fe4179e4558f9adf909199c64c0fd28e9997237f`。原 playlist guard 固定为
  `((925721864, 50000),)`、`expected_avoid_repeat_count=1`；新 playlist 固定为 Sound `2154199438` / 权重 `50000` 与
  Sound `640829561` / 权重 `50000`，Random mode 保持不变，`avoid-repeat=0`。双条目克隆 body 为 91 字节。
- 新 Random 的父级、实例限制和 Pitch 必须组合后以一次 guarded 完整 body replacement 应用：在独立内存 HircEditor 中，
  先将 91-byte 克隆 body `+0x0B` 的父级从 donor Switch `368774789` 改为新 Switch `4010844647`，`+0x19` 从 `0x00`
  改为 `0x01`（Kill Newest），`+0x1B` 从 `0` 改为 `1`（实例上限）；序列化并重解析该临时 HIRC，再调用 `set_pitch()`，
  以 `HircPitchSettings(None, None)` 为初始 guard，仅设置 `random_range_cents=(-50, 50)`，基础 Pitch 属性保持缺省。
  将所得完整 body 通过 `replace_object_body()` 替换主编辑器中的 91-byte 克隆 body，expected 必须为上述修改前的完整克隆
  body；不得在主编辑器中先对同一 Random 应用字段补丁，再插入 Pitch 属性。
- 随机 Pitch 属性 `0x02` 插入使新 Random body `91→100` 字节；最终读回必须为 `HircPitchSettings(None, (-50, 50))`。
  父级字段仍在 `+0x0B`，Kill Newest 与实例上限字段分别移至 `+0x22` 和 `+0x24`。最终 body SHA-256 固定为
  `396592e4835d0108b6049e3f40c2d1e6fb66c628c52fb59da3506f49c0c4756f`；除明确声明的 ID、父级、playlist、avoid-repeat、
  实例限制和随机 Pitch 外，保留 donor 的其它属性与未知字节。
- 三个新 Sound 均使用 46-byte 标准语音 body：来源为 `original/nbnk/wp_cmn_epvsp.nbnk`（SHA-256
  `76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8`）的 Sound `890667980` / Media `838569492`，原 body
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
  payload `33313→33743`、Event body `12→16`、changed-byte count `51`、HIRC 增量 `+430`。其中新 Random 的完整 body
  replacement 计入 46 个 changed bytes，新 Switch 父级补丁计入 4 个，Event 扩展计入 1 个；resized objects 摘要仍仅含
  Event `4072881687` 的 `12→16`。新增 HIRC 对象为三个 Sound、Random `3163089818`、Switch `4010844647`、Action
  `4197300369`；三个 Sound 必须先于其父级 Container 序列化，Random 先于 Switch，Switch 先于新 Action，新 Action 先于
  Event `4072881687`。除 DIDX、DATA、HIRC 外其它内容保持 byte-exact；原媒体及上述 Event 之外的原 HIRC 对象保持 byte-exact。
- 游戏内按描述表验收：间隔触发可听到两份 Protection 及随机音调变化，允许同一份连续出现；播放期间再次防御不打断、不叠加，
  实际播放结束后恢复随机触发；其它武器防御和非防御动作不播放自定义语音。
