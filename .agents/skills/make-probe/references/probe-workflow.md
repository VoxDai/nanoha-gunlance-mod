# 探针技术工作流

制作或验证二进制包时读取。本文件补充 `soundbank-workflow`，API 以当前 Library README 和 docstrings 为准，不复制历史构建脚本里的 ID、偏移或 guard。

## 输入和路由证据

在 `src` 固定源文件路径、nativePC 目标、格式版本、Bank ID、完整输入 SHA-256，以及所用素材和路由数据的身份。原版基准和现有 Mod 基准必须明确区分；诊断现有 Mod 时只使用显式选定且固定身份的输入，不从游戏安装状态自动取文件。

动画路由需追踪：Motion → TIML 赋值帧/触发帧与槽位 → ReqNo → 全部 WWEV mode/record/Event → Action → Container/Sound → DIDX index/Media ID → WEM。非 LMT 来源的 Event 不强行归因于 Motion。记录共享 TIML、共享媒体和所有 WWEV 展开。

## 选择修改

- 媒体替换会影响所有使用者；查清作用范围，将它作为实验条件说明。不要用共享媒体阳性推断某个唯一 Motion。
- Motion 隔离使用 `LmtEditor.replace_request()` 的 Motion、EventGroup、slot、赋值帧、旧 ReqNo 和完整触发帧守卫。不支持的共享 TIML 不绕过保护，不裸改绝对偏移或新增未知时间轴。
- 用 `WwevEditor.append_cloned_request()`（或当前等价 guarded API）完整克隆 donor 请求的所有记录，固定数量、顺序、mode 和完整 record hash。独立包装保留每条原 Event；一次逻辑提示通常只挂到其中一个包装，避免多记录重复提示。
- HIRC 使用公开 guarded API，固定 donor body、原值及所有引用；先序列化依赖再序列化其使用者。每个 Action 在 Bank 内只有一个 owning Event，共享 Sound 可用不同 Action。新 ID/ReqNo 在实际涉及的 Bank、请求表及 Motion 范围内检查碰撞并保存检查范围。
- 跨 Bank PlayEvent 需对最终伴随 Bank 集合检查唯一目标、目标类型、Action 所有权和序列顺序。无媒体的结构 Bank 按当前 Library 支持方式处理，不通过放宽验证来通过检查。
- 短 marker 不证明长语音的停止/中断行为。确需测试停止时检查原生 Stop、scope、GameObject、淡出及继承属性，安排相应长标记实验；不自动扩展每轮定位任务。

## 构建与验收

每轮 `src/build_probe.py --output <新目录>` 应能从固定输入复建完整 packages，拒绝既有输出。从临时目录构建、验证后交付，失败不留下可误装的半成品；不自动安装或生成 ZIP。

检查并保存：

- 所有输入 guard、碰撞检查、声明的编辑摘要、目标路径和输出哈希。
- 读回每个产物；完整追踪目标路线，并比较未声明的 LMT 路由、原 WWEV 记录、原对象/媒体及无关 chunks。媒体替换等有意变化单独列明。
- 对每个修改的 Bank 执行 wwiser 实际解析；提取所有新增/替换 WEM，经项目 pyvgmstream 检查与解码，验证采样率、声道、时长及与转换源 PCM 的一致性。
- 检查每个变体需要的全部文件和跨文件引用，清单哈希仅覆盖不可变的构建输入/产物，不把用户待填写记录作为固定 guard。
- 独立复建时比较 packages 内容，防止偶然依赖上一包、临时路径或游戏安装目录。

安装说明压缩到记录文档：退出游戏、备份目标及原本不存在的文件、完整切换一组文件并重启、停用目标冲突 Mod、结束恢复最初备份。只清理本轮新增的对应目标，不删除整个 nativePC；00_baseline 不替代用户 Mod 备份。

## 三种判断示例

- 骑乘候选：同包中文标记区分候选 Motion，加载检查用不同提示词；记录实际头/背/尾和阶段，不事先指定部位映射。阳性后再按需要验证其余分支。
- 龙杭起手：在相同前置动作下比较提示词与抬枪/插入/释放的先后，区分方向、命中/打空及资源状态；证据只支持最早已验证入口，不代表全部隐藏路径的绝对最早。
- 对照失效：先停止阶段扫描，核对旧完整阳性包，再按证据只改变一个文件集合。加载对照成功仍不能证明目标 Motion 被执行；若旧阳性也不复现，不把问题归咎于新增 WWEV 或 Bank。
