# Nanoha Gunlance Mod

本项目用于制作《怪物猎人：世界》语音 Mod，将游戏中铳枪相关音效替换或叠加为《魔法少女奈叶》中奈叶及 Raising Heart
的战斗语音。开发内容包括游戏音频事件分析、素材整理与处理、音效设计、构建器实现，以及完整 Mod 的验证和发布。

## 基本步骤

1. 使用 `soundbank-workflow` 只读分析原版 NBNK、LMT、WWEV，整理事件、动作、媒体和路由证据。
2. 收集并处理最终语音素材；需要从本地媒体截取时可使用 `extract-audio`。
3. 使用 `audio-design` 将预期播放行为、最终音频、原始 artifact、guard 和验收要求固化到 `designs/`。
4. 使用 `design-implement` 将指定 design 实现为显式 artifact builders、bundle validators 和测试。
5. 使用 `build-mod` 执行完整 dry-run，并在全部验证通过后事务发布 `release/nativePC/`。
6. 在可恢复的游戏环境中验证触发范围、播放时机、音量、空间感、中断行为和 Mod 冲突。

## 目录结构

- `assets/`：原始素材、游戏提取数据及只读测试参考。
    - `assets/chunk/`：从《怪物猎人：世界》提取的完整原版数据；保持不变。
    - `assets/mod_samples/`：逆向分析用参考 Mod；保持不变。
    - `assets/source_audio/`：奈叶相关游戏及动画的源语音；`testing/` 仅存放探针和测试音频。
    - `assets/testing_mod_files/`：可恢复验证使用的历史或临时测试包，不属于正式 release。
- `audio/`：design 使用的最终项目 WAV，按目标 artifact 和动作整理。
- `builders/`：唯一可执行构建契约。
    - `SoundBankBuildPlan`、`LmtBuildPlan`、`WwevBuildPlan` 显式声明 design ID、源和 nativePC 目标、原始哈希、 媒体
      index/Media ID、guarded 回调及精确摘要。
    - `ModBuildPlan` 显式注册完整 release 成员和跨文件 validators；不从目录内容或文档推断。
    - `builders/base.py` 负责临时构建、深度验证和带回滚的整树事务发布。
- `designs/`：按用户可感知动作记录触发范围、声音层、技术实现契约和验收要求；不是 builder 配置文件。
- `docs/`：研究和参考资料。
    - `docs/mapping/`：原版音频、事件和动作映射，仅供研究。
    - `docs/reference/`：招式、语音等参考资料。
- `original/`：已确认并固定给 design/builder 使用的原版输入；禁止原地修改。
    - `original/nbnk/`：原版 NBNK SoundBanks。
    - `original/lmt/`：原版 LMT Motion 文件。
    - `original/wwev/`：原版 WWEV 请求表。
    - `original/audio_files/<SoundBank>/{wav,wem}/`：按 SoundBank 分类的原版媒体提取结果。
- `output/`：用户明确请求的单 artifact 调试输出；不构成正式 Mod。
- `release/`：`build-mod` 事务发布的完整 Mod 树；不得手工拼装或发布子集。
- `tools/`：格式 Library、音频转换和第三方分析工具。

## 本地开发环境

项目专用 conda 环境为 `nanoha-gunlance-mod`，Python 3.12，完整依赖见 `environment.yml`。环境包含
`ffmpeg`、`pyvgmstream` 及项目测试和分析依赖。

```sh
# 运行单个命令
conda run -n nanoha-gunlance-mod mycommand

# 运行多行 Python
conda run -n nanoha-gunlance-mod python <<'PY'
...
PY
```

项目使用 Git LFS 管理 `.nbnk`、`.wav`、`.wem`、`.lmt` 和 `.wwev` 等二进制文件。在 `.git` 仅可读的沙箱中，
检查普通文本文件时可使用 `git -c filter.lfs.process= -c filter.lfs.required=false diff --check -- <paths>` 跳过
LFS filter；完整检查应申请写入权限。

## 项目工具

- `tools.soundbank_editor`：通过 `from tools import soundbank_editor` 使用，提供 NBNK/DIDX/DATA/HIRC、LMT v95/TIML、WWEV v19
  的无损解析、guarded 编辑、结构重建和读回验证。
- `ffmpeg`：用于音视频格式转换、裁剪和提取。通过
  `conda run -n nanoha-gunlance-mod ffmpeg ...` 执行。
- `pyvgmstream`：统一通过 `tools/utils/pyvgmstream.py` 封装调用，用于检查 WEM 和解码 WAV；添加 `-h` 查看参数。
- `tools/utils/wav_to_wem.py`：将最终音频转换为项目验证过的 48 kHz、16-bit、stereo Wwise PCM WEM。
- `tools/wwiser/`：Git Submodule 管理的
  [wwiser](https://github.com/bnnm/wwiser)，用于解析 NBNK、HIRC 路由、导出结构和 TXTP。 使用
  `conda run -n nanoha-gunlance-mod python tools/wwiser/wwiser.py <文件.nbnk>`。

## 参考资料

- [MHW:IB Labelled Audio](https://docs.google.com/spreadsheets/d/10A_YEfm7KV0ATw7uD-3_o_ZOGSlGXtzWWMGXKs_neYM/edit)
  ：社区维护的《怪物猎人：世界／冰原》音频标注表，包含 NBNK/NPCK 用途、WEM 编号、Bank Index、角色语音预设和部分试听说明； 内容不完整，带
  `?` 的标注及旧版本编号需要自行验证。
- [Modding MH:W — wwiseutil Wiki](https://github.com/hpxro7/wwiseutil/wiki/Modding-MH%3AW)
  ：介绍 MHW 的 NBNK/NPCK/WEM 结构和替换流程。资料可作参考，实际解析优先使用项目中的 wwiser。
- [Player Weapon Action IDs](https://github.com/AniBullet/MonsterHunterWorldModding/wiki/Player-Weapon-Action-IDs)
  ：玩家武器 Action ID 和动作名称参考，可辅助动作事件分析和 FSM 编辑。
