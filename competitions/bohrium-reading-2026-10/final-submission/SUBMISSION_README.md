# Shidi Pro：从一句话科研灵感到可验证问题

## 使用场景

Shidi 面向尚不会拆解研究问题的用户：把不成熟的一句话灵感转成有原文依据、边界清楚的候选路线和最小证伪实验。官方 A/B 对照均使用同一个 Pro（`b28eb4e`）版本；Flash（`6e03d72`）只作附加版本比较，不用于官方 Pro/without 配对。

## 安装与调用

仓库：`IcyCreamDAS/shidi-skill`。一次下载包含 Pro 和 Flash 两个完整模式。默认 Pro；“快速调研”或“flash 模式”选择 Flash。模式文件分别位于 `modes/pro/` 与 `modes/flash/`。官方包中的 `skill/` 为 Pro 版本。

## 运行环境与预算

两组均为 Kimi Code Desktop 独立 coder 子代理，`kimi-code/kimi-for-coding`（K2.8 Preview）+ 默认 max，profile.bind 已核对。禁止读取父会话、其他运行和宿主用户记忆。第一轮使用 12 分钟、24 查询、40 页面动作、最多 8 篇核心文献的软预算；第四轮沿用相同设置。

## 证据与结果

A（顺序逻辑）：ChatGPT 权重续评 Pro 93、without 58；Kimi Pro 88.75、without 67.50。B（损伤记忆）：续评 Pro 92、without 70；Kimi Pro 91.25、without 81.25。主要参考体系下两轮均显示增益，核心是 Pro 能发现逆序证据和“自增强不等于第二次加速”的证据链缺口。

内部续评不是官方成绩，也不表示所有任务都更好。公共提示词、主代理代答、失败和实际投入均保留。完整分项见 `evaluation/` 的 4 表 3 图。

## 人工参与与轨迹

K3.1 Pro 主代理只负责冻结协议、统一用户代答和独立评阅，没有提供代表论文或预设科学结论。`trace-export.jsonl` 是从真实 wire 提取的可见用户/助手文本和工具事件，仅对本机用户名和绝对路径做确定性脱敏，不含宿主系统提示或隐藏推理。原始 wire 仅留作者本地。合并平台导出 `submission-trace.jsonl` 保留 case/run_id，供 `--trace-kind export`。

## 原件与限制

`pdf-verification.json` 记录 PDF 页数、字节和 SHA-256。报告数值是文献报道，不是作者新实验数据。公共科学检查项已经预先拆解了一部分研究问题，因此输出深度不能完全归因于 Skill。Pro 存在确认与超时，Flash 速度快但质量随任务变化。无逐次扣费字段，费用记无法核验。

本包包含 A/B 两组真实对照，未选 C。未上传，没有 Attempt ID 或比赛成绩。官方结构检查不等于科学结论认可。
