---
name: make-probe
description: "制作 Monster Hunter World 招式、动作和音效的游戏实测探针，在 assets/analyses 下交付可复建测试包，分析 recordings.md 并迭代定位 ID、触发时机和路由。用于探针制作及实测反馈分析；不编写正式 design、builders 或发布 release。"
---

# 制作探针

将一个待验证问题转成可恢复、易辨识的游戏实验，再将用户观察与二进制证据结合，为 `audio-design` 提供信息。`design-implement` 仍以完整 design 为输入，探针不是正式构建契约。

## 工作边界

- 只制作用户指定招式或问题的探针，或分析指定记录。先读取相关历史包及记录；已有包能回答问题时优先续测，不为“继续分析”机械地增加新包。
- 交付只写入对应 `assets/analyses/<move>/`。原版输入优先读取 `original/`，缺失时可直接读取已唯一定位的 `assets/chunk/` 输入并固定身份；不在本任务中提升或修改原始文件。
- 不修改历史已交付包、用户记录、`audio/`、`designs/`、`builders/`、`tools/`、`output/` 或 `release/`。新一轮使用新编号；分析结果写入相应 `findings.md`。
- 不安装到游戏。交付后等待用户实测，不替用户填写结果，也不把结构检查称作游戏验证。

## 包结构

```text
assets/analyses/<move>/<move>_<NN>[_description]/
├── packages/
│   ├── 00_baseline/nativePC/...
│   └── 01_motions160_163/nativePC/...
├── src/
│   ├── README.md
│   ├── build_probe.py
│   └── 路由、输入守卫、提示音、验证结果
├── recordings.md
└── findings.md
```

`move` 和可选描述用 snake_case。编号在同招式目录中递增、至少两位；探针包如 `mounted_finisher_01_control_diagnostic`。变体用 `00_baseline`、`01_motions160_163` 格式。不生成 ZIP。每个变体包含该实验需要的完整伴随文件，切换时不依赖上一变体残留。基线采用明确记录的输入集合，不自动复制整个正式 release。

## 制作

1. 明确本轮要区分的假设、候选范围和可停止条件。用 `soundbank-workflow` 和当前 `tools/soundbank_editor/README.md`、API docstrings 检查原始路由。需要编辑或验证二进制前，阅读 [技术工作流](references/probe-workflow.md)。历史数字只作线索，不作为新包的固定证据。
2. 选择最少实验：媒体替换适合验证声音身份或已知共享范围；特定 Motion 定位优先隔离请求，不直接改写所有动作共用的 Event。仅改变本轮声明的因素，保留无关原声和控制行为。
3. 优先在同包中给不同候选分配不同提示词。候选太多或可能重叠时分组；先小范围定位，再查阶段、共享范围和必要负例。使用容易执行的加载阳性，条件允许时放入每个候选变体，不要求反复进行昂贵目标动作来检查加载。
4. 单一标记可用 `assets/source_audio/testing/trigger.wav`；多种标记自动生成中文“触发一、触发二……”，加载检查用“加载成功”。不得用声数组合。运行：

   ```sh
   conda run -n nanoha-gunlance-mod python .agents/skills/make-probe/scripts/generate_markers.py --output-dir <probe>/src/markers --count 3
   ```

   默认本机 `say` 的 `Tingting`；可用 `--voice` 选已安装中文声音。脚本保存文本、参数、原始合成音、48 kHz stereo 16-bit WAV、WEM 和解码验证。不下载声音或静默改成计数短音；不可用时报告缺失条件。探针音频不套用最终项目 WAV 的命名和响度契约；检查非空、削波和辨识度，提供 WAV 试听链接。语音长短、起始静默与继承混音会影响所听时机，不能直接声称提示音起点就是精确触发时刻。
5. 在 `src` 保存显式、可复建的脚本和证据；提供 `--output`，拒绝覆盖已有输出。临时构建并通过技术验证后再交付完整 packages。技术细节、文件列表、复建命令和检查结果放 `src/README.md`，不堆进用户记录表。
6. 从 [记录模板](assets/recordings.md) 和 [分析模板](assets/findings.md) 按本轮问题生成文档，替换模板说明，删除不需要的列和行。`recordings.md` 只有“如何测试”和“测试结果”两部分；说明含简短填写实例、必要安装/恢复步骤及停止条件。表格初始“未测”，只记录足以区分假设的条件，不默认要求所有招式、炮型、怪物、负例的笛卡尔积。
7. 交付时链接 `recordings.md`、packages 和提示音试听，简述已完成的结构验证及待用户实测的部分。

## 分析与下一轮

读取用户指定记录及对应包的路由、版本/文件身份和验证结果，在 `findings.md` 中引用具体记录行、包和原始证据。旧包的 `feedback.md` 或用户称作 `recording.md` 的文件可只读使用；新交付统一 `recordings.md`。

- 区分“未测”“0/N”“不确定”，记录有效次数、所有提示词与阶段，不按预期反填实际观察。用户未填条件就保留未知，不推定其操作发生变化。
- 加载阳性缺失或旧阳性失效时先诊断加载、冲突、实际 Motion 分支及包差异；不把候选静默当排除，也不猜测引擎记录数量上限。新旧差异实验仍需保持引用有效。
- 只声称已测条件下成立的范围。Action ID 不是 Motion ID；不同 Motion 的帧数不能比较绝对先后；无录像时间戳不能量化时间间隔。多部位、方向或前置动作可能进入不同 Motion。
- 明确选择：续测现有包、制作下一轮、或停止并总结。给出最低成本且能改变结论的下一步，出现足够证据就暂停无用测试。
- 总结已验证条件、ID/完整路由、时机、共享/负例、guard 证据和未解决问题，链接原始文件和记录。交给 `audio-design` 确定最终音频与行为契约，不将临时探针 ID、marker 或推测直接转成正式设计。
