# Nanoha Gunlance Mod

本项目用于制作《怪物猎人：世界》语音 Mod，将游戏中铳枪相关音效替换为《魔法少女奈叶》中奈叶的战斗语音。开发内容包括游戏音频事件分析、语音素材整理与处理，以及
`.nbnk` Mod 文件的生成和验证。

## 基本步骤

1. 逆向分析现有 Mod 或游戏源文件，整理“游戏事件—音频文件”映射关系。
2. 收集并筛选《魔法少女奈叶》动画或游戏中的语音素材，完成裁剪、降噪、音量调整及格式转换。
3. 根据事件映射替换对应音频，或通过额外 Action 在原版音效上叠加音频，生成 `.nbnk` 文件。
4. 在可恢复的测试环境中安装并验证 Mod，确认触发事件、语音内容和播放效果符合预期。

## 目录结构

- `assets/`：存放项目资源及测试文件。
  - `assets/chunk/`：存放从《怪物猎人：世界》提取的游戏完整原版数据；样本文件应保持不变。
    - `assets/mod_samples/`：存放用于逆向分析的参考 Mod 样本；样本文件应保持不变。
    - `assets/source_audio/`：存放《魔法少女奈叶》相关游戏及动画语音素材；`assets/source_audio/testing/` 存放测试音频。
    - `assets/testing_mod_files/`：存放用于测试的 Mod 文件。
- `builders/`：每个 SoundBank 的同名 Python 脚本是一份 `BankBuildPlan`，负责读取映射、调用编辑器修改原始 Bank
  并保存；公共转换、验证和发布逻辑由 `builders/base.py` 复用。需要保留原版媒体并叠加声音时，用 `MappingMediaOverlay` 消费指定
  Audio 行、追加一份共享媒体，并在该 Bank 的 `apply_edits()` 中声明 HIRC 路由。
- `docs/`：存放招式、语音和其他研究资料。
- `mapping/`：存放逆向分析记录、文件格式说明及游戏事件与音频文件的映射表。
- `original/`：存放从《怪物猎人：世界》提取的铳枪相关游戏原版数据；样本文件应保持不变。
    - `original/soundbank/`：存放原版 `.nbnk` SoundBank 文件。
    - `original/audio_files/<SoundBank>/{wav,wem}/`：存放按 SoundBank 分类提取的原版音频文件及其 WAV 转换文件。
- `tools/`：存放用于分析、提取、转换音频和重建 SoundBank 的工具脚本。
  - `tools/soundbank_editor/`：纯 Python SoundBank Library，提供 NBNK/DIDX/DATA/HIRC 的解析、媒体提取、guarded 编辑、v120
    结构重建和读回验证；通过 `from tools import soundbank_editor` 使用。
    - `tools/utils/`：存放项目公共音频工具，包括 pyvgmstream 封装和 Wwise PCM WEM 转换脚本。
    - `tools/wwiser/`：解析 Wwise SoundBank 结构、HIRC 关系并生成分析结果。

## 本地开发环境

本项目专用 conda 环境 `nanoha-gunlance-mod`，Python 版本为 3.12，完整依赖声明见 `environment.yml`。 环境包含 `ffmpeg`、
`pyvgmstream`，以及用于 PDF、文档、表格和网页解析的常用包。

```sh
# 运行单个命令
conda run -n nanoha-gunlance-mod mycommand

# 运行多行命令
conda run -n nanoha-gunlance-mod python <<'PY' ... PY
```

## 项目工具

- `ffmpeg`：用于音视频格式转换、裁剪、提取等处理。使用 `conda run -n nanoha-gunlance-mod ffmpeg -i <输入文件> <输出文件>`
  执行，并通过指定参数完成相应处理。
- `pyvgmstream`：用于识别 Wwise `.wem` 元数据、将 WEM 解码为 WAV 以及批量转换。项目统一通过
  `tools/utils/pyvgmstream.py` 调用，例如：
  `conda run -n nanoha-gunlance-mod python tools/utils/pyvgmstream.py inspect <文件.wem>`，或添加 `-h` 查看完整参数。
- `tools.soundbank_editor`：使用 `SoundBank.from_file()` 解析 Bank，通过 1-based DIDX index 或 Media ID 提取媒体；使用
  `SoundBankEditor` 替换/追加媒体并执行 guarded HIRC 编辑。该 Library 不提供 CLI，持久修改应写入同名 builder；映射 overlay
  属于 builder 编排能力，不属于 Library 的 JSON 或 CLI 接口。
- `tools/utils/wav_to_wem.py`：将输入音频转换为项目验证过的 48 kHz、16-bit、stereo Wwise PCM WEM 布局。
- `tools/wwiser/`：通过 Git Submodule 管理的 [wwiser](https://github.com/bnnm/wwiser)，用于解析 Wwise `.bnk`/`.nbnk` 的区块和
  HIRC 音频事件关系、导出结构信息及生成 TXTP。克隆主仓库后运行 `git submodule update --init --recursive` 获取工具。使用
  `conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py <文件.nbnk>` 解析文件，或添加 `-h` 查看完整参数。

## 参考资料

- [MHW:IB Labelled Audio](https://docs.google.com/spreadsheets/d/10A_YEfm7KV0ATw7uD-3_o_ZOGSlGXtzWWMGXKs_neYM/edit)
  ：社区维护的《怪物猎人：世界／冰原》音频标注表，包含 `.nbnk`/`.npck` 用途、内部 WEM 编号、Bank Index、角色语音预设和部分人工试听说明。内容并不完整，带
  `?` 的标注及旧版本编号需要自行验证。
- [Modding MH:W — wwiseutil Wiki](https://github.com/hpxro7/wwiseutil/wiki/Modding-MH%3AW)：介绍《怪物猎人：世界》的
  `.nbnk`/`.npck`、`.wem` 音频结构及提取、替换流程，并链接上述社区标注表。`wwiseutil` 已较旧，资料可作为参考；实际结构解析优先使用项目中的
  `wwiser`。
- [Player Weapon Action IDs](https://github.com/AniBullet/MonsterHunterWorldModding/wiki/Player-Weapon-Action-IDs)
  ：整理《怪物猎人：世界》各类玩家武器的 Action ID、动作名称及对应类名，可用于武器动作事件分析和 FSM 编辑。
