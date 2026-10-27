# Shidi Pro：从一句科研灵感到可验证问题

## 使用场景

Shidi 面向只有兴趣起点、尚未形成系统研究问题的用户，组织跨领域检索与原文核验，交付候选比较、证据分级及验证方案。本包的 A/B 案例均以 Pro `b28eb4e` 与 without 配对；Flash `6e03d72` 的结果另作流程比较。

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

科研深度内部评分：A 的 Pro/without 为 93/58，B 为 92/70。两套量表均由 Kimi 执行；科研深度量表源于与 ChatGPT 的讨论，工作流评分单列，综合展示按公式派生。分项、来源与用量见 `evaluation/`。

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

本包对应所列两次案例运行，内部评分用于展示具体判断与交付，平台成绩以提交回执为准。
