# Shidi Pro：从一句科研灵感到可验证问题

## 使用场景

Shidi 面向只有兴趣起点、尚未形成系统研究问题的用户，组织跨领域检索与原文核验，交付候选比较、证据分级及验证方案。本包的 A/B 案例均以 Pro `b28eb4e` 与 without 配对；Flash `6e03d72` 的结果另作流程比较。

## 创作缘起

2026年8月的一个工作日，作者把多年借助AI检索文献、寻找思路时积累的痛点画成流程图，借助Claude Code和Mermaid做成Shidi。作者希望它像真实师弟一样接住一两句话的想法，组织检索、追索原文，遇到影响判断的地方回来询问，再一起讨论课题。两个月的实际使用，让这个节省精力的工具逐渐成为七年科研经历的一份创造性产物。

## 安装与调用

Pro/Flash 当前位于公开的 `feature/shidi-pro-flash` 分支。一次安装包含两种完整模式，默认 Pro；“快速调研”或“flash 模式”选择 Flash。本包 `skill/` 为实验时冻结的 Pro 文件。

```bash
git clone --branch feature/shidi-pro-flash --single-branch https://github.com/IcyCreamDAS/shidi-skill.git
mkdir -p ~/.claude/skills
cp -r shidi-skill/skills/shidi ~/.claude/skills/
```

## 案例与结果

- A 顺序逻辑：Pro 识别水已存在时后续生成酸仍可能反应的逆序风险，提出状态保持与反向路径验证。
- B 损伤记忆：Pro 区分损伤自增强与第二次修复加速，比较潜伏活性种和机械自由基路线，形成双循环动力学实验问题。

主展示采用ChatGPT直接执行的六维内容复评：A的Pro/without为78.75/50，B为68.75/47.50。第一题突出Pro识别逆序风险；第四题展示从灵感形成研究问题。完整分项与两张新雷达图见 `evaluation/independent-review/`。此前Kimi评分和工作流记录保留为历史材料。

## 执行与记录

执行模型统一为 Kimi Code 的 K2.8 Preview + max，各组从独立会话开始，使用同一初始问题、共同任务要求及工具预算。预算为每组 12 分钟软墙、24 查询、40 页面动作、最多 8 篇核心文献；实际问答、重试、用时与 token 均按日志保留。

协调代理负责协议、用户代答、整理与评阅；执行组未得到代表论文或评分答案。轨迹为真实 wire 中的可见文本与工具事件，去除宿主提示及隐藏推理，并脱敏本机路径和登录账号信息。

PDF 页数、字节与 SHA-256 见各组 `pdf-verification.json`。论文数据、Agent 提议和作者评阅分别保留；本案例没有新增作者实验实测数据。

## 复现与包状态

公开实例的四类表格和三类图可使用随仓库提供的数据重建。重新构建完整 Skill 参赛包时，还需提供原始 PDF 运行档案，不能以核验清单代替文件：

```bash
python competitions/bohrium-reading-2026-10/final-submission/build_submission.py \
  --resources /path/to/official/resources \
  --runs-root /path/to/full-runs \
  --out /path/to/new-output
```

完整运行目录布局为 `sequential-logic/{pro,without}/` 和 `damage-memory/{pro,without}/`，各组保留 `output/pdfs/`。`--out` 必须是尚不存在的目录。脚本先检查原件哈希，再打包和运行官方结构检查，不自动上传。

评分是事后、非盲的内容复评；权重为15/25/20/20/10/10，各维0–4档。单独重绘导出的评分图可给 render_radars.py 加 --scores-only，回到完整仓库运行时默认还会校验源报告哈希。本包对应所列两次案例运行，平台成绩以提交回执为准。

## 模型与预算建议

Pro在较宽范围内会产生更多检索、核验与交互。建议先用低成本模型，约定文献上限、补检轮次和停止条件，再按证据缺口扩展。本次两案例的执行模型均为K2.8 Preview + max，实际完成了检索、原文整理、证据比较与问题拆解。
