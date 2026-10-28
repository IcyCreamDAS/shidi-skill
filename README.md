# 师弟 · shidi — 科研愿望实现器 🧑‍🔬
### *Your junior lab mate in an Agent Skill — ideas in, files out*

[![License](https://img.shields.io/badge/license-MIT-2ea44f)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.0-blue)](https://github.com/IcyCreamDAS/shidi-skill/releases)
[![GitHub stars](https://img.shields.io/github/stars/IcyCreamDAS/shidi-skill.svg?style=social)](https://github.com/IcyCreamDAS/shidi-skill/stargazers)
[![Agent](https://img.shields.io/badge/agent-Claude%20Code%20%7C%20Codex%20%7C%20OpenClaw-111827)](README.md)
[![Zero-Dep](https://img.shields.io/badge/dependencies-zero-ff69b4)](README.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/IcyCreamDAS/shidi-skill/pulls)

中文 | [English](./README_EN.md)

**从一句兴趣起点出发，发现跨领域证据链的缺口，再形成自己的研究问题。** Shidi 组织检索、原文获取、候选比较与验证方案，交付可继续追问的文件。

> **师兄说想法，师弟跑断腿。** — *You bring the ideas, shidi does the legwork.*
>
> shidi 不是填模板的自动化——它是一条跑在 AI IDE 里的完整科研工作流：把脑海中的想法丢给它（文献调研 / 实验方案 / 作图 / 精读 / 数据整理），它在你的机器上跑完脏活累活，交付**真实可用的文件**，产物保存在你的工作目录，不锁任何平台或模型。
>
> *shidi is a complete research workflow living inside your AI IDE — not a prompt template. Hand it an idea (literature research / experiment design / figures / paper reading / data chores), and it returns **real deliverable files**. Deliverables are saved in your working directory. No platform or model lock-in.*

> **它不是放养型的。** 师弟是一个你一边忙别的、一边顺手使唤的 skill：喊一嗓子"师弟，帮我……"，它该问就问、该跑就跑，跑完把文件递到你手上。
>
> *It's not fire-and-forget, either — shidi is meant to be bossed around while you do something else. Yell "shidi, help me with …", and it asks when it must, runs the rest, and hands you the files.*

> **为 AI for Science 与科研 Agent 而生** — 面向 AI4S 场景、理工科研究生与所有用 Agent 辅助科研的人：文献调研、实验方案、作图、精读,从"聊天答案"变成可交付、可交叉验证的文件。
> *Built for AI for Science workflows, grad students and researchers using agentic AI — deliverable, cross-verifiable files instead of chat answers.*

<p align="center">
  <a href="#-whats-new--更新日志"><strong>What's New</strong></a> ·
  <a href="#-deliverables--交付物"><strong>Deliverables</strong></a> ·
  <a href="#-why-shidi--为什么用它"><strong>Why shidi</strong></a> ·
  <a href="#-quick-start--快速开始"><strong>Quick Start</strong></a> ·
  <a href="#-demo--示例预览"><strong>Demo</strong></a> ·
  <a href="#-guardrails--防护机制"><strong>Guardrails</strong></a> ·
  <a href="#ai4s-evidence"><strong>AI4S</strong></a>
</p>

---

## 👀 Demo · 示例预览

> 下图是**结构示例**(内容脱敏)——真实交付按你的课题动态生成,每次跑完都是新文件。
> *Screenshots below are **illustrative** (content redacted) — real runs produce fresh files for your own topic.*

<p align="center">
  <img src="assets/demo-report.png" alt="Final report structure" width="560"/>
  <img src="assets/demo-verify.png" alt="Cross-verification brief structure" width="560"/>
</p>

**真实 Pro / Flash / without 对照实例：** [两个跨学科问题、六份结果与三组六维雷达图](examples/pro-flash-evaluation/README.md)——展示如何识别逆序风险、区分损伤自增强与修复加速，并形成实验问题。

---

## ✨ What's New · 更新日志

- **2026-10-27：Pro / Flash 双模式** — 一次安装包含两套完整流程；默认 Pro，“快速调研 / flash 模式”选择 Flash。当前公开安装分支为 `feature/shidi-pro-flash`。
- **两个真实探索案例** — [顺序化学逻辑与涂层损伤记忆](examples/pro-flash-evaluation/README.md)，各含 Pro / Flash / without 输出、两套评分细则、用量及图表；[技术文章](GITHUB_SHARE.md)介绍证据链拆解方法。
- **参赛材料** — [最终 A/B 案例说明](competitions/bohrium-reading-2026-10/final-submission/SUBMISSION_README.md)整理两组 Pro/without 对照。此前的指定论文阅读试跑与打包记录保留在 [历史准备目录](competitions/bohrium-reading-2026-10/README.md)。
- **2026-10** — 🛡 **发布版自检闭环**：GitHub Actions CI + `validate.py`（版本/链接/脚本编译/必需文件）+ `tests/` 离线单测 · 补上 `verify_refs.py` 引用核验（DOI 解析/撤稿检测/文风 lint）· 修 `render_report.py` 超时 bug 并支持跨平台浏览器探测 · `fetch_pdfs.py` 去掉硬编码邮箱、加指数退避
- **2026-10** — 🔬 **确定性评分 + 数据 schema + AI4S 示例升级**：`score_papers.py` 七维评分（封顶/一票否决/排序由脚本算，v2 权重下调期刊与人脉）· 文献→配方/性能抽取 schema（测试标准/条件/n/误差/三类标签）· 示例升级（质量分数闭合、ARD 长度尺度、ECI 采集函数、1-2 基准配方校准对比、Pareto 前沿、文献先验边界接口）
- **2026-08** — 📥 **PDF 批量下载**（OpenAlex/Unpaywall 自动定位 OA 直链，失败分类报告，不静默跳过）· *batch PDF download with honest failure reports*
- **2026-08** — 📄 **多格式报告**（Markdown → HTML → PDF，Edge 无头打印，零依赖）· *MD → HTML → PDF rendering, zero deps*
- **2026-08** — 🔍 **PDF 抽取层**（文本型转 Markdown 省上下文，扫描件自动标 needs_vision 走视觉路径）· *PDF extraction layer: text → Markdown, scans → vision route*
- **2026-08** — 🗂 **分角度中间报告**（多角度并行调研每角度落盘独立文件，汇总只读文件、主上下文不炸）· *per-angle intermediate reports for parallel multi-agent research*

## 📤 Deliverables · 交付物

每一单活都交付**实打实的文件**——不是聊天记录里的文字。
*Every job ends in real files — not chat text.*

<table>
  <tr>
    <td align="center" width="50%">
      <b>📄 Final Report 最终报告</b>（`~/shidi-output/`）<br/>
      <sub>Markdown / Word · 完整方案或调研报告</sub>
      <pre><code>shidi_&lt;主题&gt;_v3_20260814.md
├── 一、任务背景与选定方案
├── 二、实验原理（文献锚定）
├── 三、操作步骤和细节
├── 四、注意事项
├── 五、漏洞清单（不掩饰）
├── 六、文献总结（按角度分组）
├── 七、参考文献（阅读深度 ✅/⚠/❌ 标注）
└── 八、变更记录（v1→v2→v3）</code></pre>
    </td>
    <td align="center" width="50%">
      <b>✅ Cross-Verification Brief 交叉验证任务书</b>（`~/shidi-verify/`）<br/>
      <sub>交给另一个 LLM 的"任务书"，也是自查清单</sub>
      <pre><code>shidi-verify_&lt;主题&gt;_v3_20260814.md
├── 1. 任务说明
├── 2. 原始问题（一字不改）
├── 3. 完整输出（含阅读深度）
├── 4. 验证重点（逐项检查清单）
└── 5. 输出格式要求</code></pre>
    </td>
  </tr>
</table>

> 每次交付都长这样。你可以拿去给**另一个 LLM** 做独立交叉验证，验证意见逐条回应，回环迭代到满意为止。
> *Every delivery looks like this. Take the brief to another LLM for independent verification — every comment gets an adopt/reject + reason, loop until you're satisfied.*

## ✨ Why shidi · 为什么用它

| 直接跟模型聊天 | 师弟 shidi |
|:--|:--|
| 答案在聊天记录里 | 交付**文件**：报告 / 任务书 / 图 / 数据 CSV，可直接归档、引用、发给别人 |
| 你盯着一步步催 | 完整工作流内置（检索→评分→阅读→报告→验证），问完三个参数就开跑 |
| 幻觉靠自觉 | 七维评分（脚本算分）、引用核验（DOI/撤稿）、DOI 三级去重、**不编造**红线、阅读深度标注，验证任务书强制输出 |
| 换个模型就换套行为 | 纯 SKILL.md + Markdown，Claude Code / Codex / OpenClaw 都能用 |

*Left: chatting with a raw model. Right: shidi — file-based deliverables, built-in workflow, anti-hallucination guardrails, agent-agnostic.*

## 🚀 Capabilities · 它能干什么

| Capability 能力 | 说明 Description |
|:--|:--|
| 📚 **文献调研** *Lit research* | 三参数一次问完 → 发散 3×3=9 角度 → 顶刊定向检索+降级链 → 七维评分（v2，脚本校验）→ 分级阅读 → PDF 批量下载 → 文件报告 |
| 🧪 **实验方案设计** *Experiment design* | 自由发散方案 → 文献支撑 → 原理/步骤/注意事项/**漏洞清单**（不掩饰） |
| 📈 **科研作图** *Figures* | CSV/TXT/Excel → 清洗 → 计算（numpy/scipy/sympy）→ 出版级渲染，附 Origin 复刻说明 |
| 🔬 **论文精读** *Paper reading* | source-map 六步精读 → 16 节论文卡片 → 术语表 |
| 🔄 **交叉验证门（灵魂）** *Cross-verification* | 必出验证任务书 → 交给另一个 LLM 独立验证 → 回环迭代 |
| 📋 **实验记录** *Lab notes* | 实验 ID / 批次 ID 标准化，YAML frontmatter 归档 |

<a id="ai4s-evidence"></a>
## 🧪 AI4S Evidence · 材料信息学方法学示例

[`examples/materials_small_data/`](examples/materials_small_data/) 是一个**只用合成数据**的小样本「配方 → 性能」建模示例，演示 shidi 做 AI4S 数据工作时坚持的口径：

- **分组留出验证**（按项目整组留出 LOGO）——同批次样本不参与训练，避免分数虚高
- **GP 预测带不确定性**——在留出项目上统计 ±1σ / ±2σ 的**实际覆盖率**，和 68% / 95% 理论值对照
- **批次校准对比**——零样本 vs 加 1–2 个基准配方再训练；实测覆盖率基本不变 → 不假设"校准好了"，负结果写进报告
- **ARD 特征相关性**——每个特征的 GP 长度尺度（越小越关键；停在上界 = 数据识别不了）
- **约束候选用 ECI**——`ECI = EI × P(MFR ≥ 28)`，不做硬阈值截断；另给"仅可行域"排行榜
- **多目标 Pareto 前沿**——拉伸强度 vs MFR 后验均值的非支配集
- **质量分数闭合**——填料 + 添加剂 A + 添加剂 B + 基体 = 100 wt%，候选另加 `matrix ≥ 40 wt%`
- **文献先验接口**——`priors_template.csv` 把文献边界喂给搜索空间（只约束边界，不注入先验均值）
- **三类证据标签分开**——`measured` / `predicted` / `exploratory`，结论只允许用 `measured`
- **硬规则：探索级筛选范围 ≠ 统计置信区间**

```bash
cd examples/materials_small_data
pip install -r requirements.txt && python run_demo.py
python run_demo.py --priors priors_template.csv   # 用文献先验边界约束搜索空间
```

**它不主张什么**：数据是合成的，不能预测任何真实材料的性能；GP 分数不能迁移到真实配方；候选不保证优于工程师的 DOE 直觉；独立单输出 GP 忽略输出相关（拉伸↔弯曲 ≈ 0.9）；1–2 个基准配方校不准批次偏移（正确解法是混合效应 GP）。真实企业配方受 NDA 约束不会进仓库——公开的是**方法**，不是数据。

## 🧭 Flow · 流程图

```mermaid
flowchart TD
    A["确定选题<br/>Decide topics"] --> B["调研文献<br/>Research"]
    B --> C["三参数<br/>{数量, 领域, 特殊要求}"]
    C --> D["开始搜索<br/>Search (T1→T2→T3)"]
    D --> H["整合结果<br/>Merge & score"]
    H --> E["学习、阅读<br/>Read (✅/⚠/❌)"]

    E -->|输出| F["文献总结 ①<br/>Lit summary"]
    E -->|输出| G["参考文献 ②③<br/>PDF or DOI+GB/T 7714"]

    F --> I{"需要补全文?<br/>More full-texts?"}
    G --> I

    I -->|是| J["用户上传 PDF<br/>User uploads"]
    J -->|补充文献| H

    I -->|否| K["输出最终报告<br/>Final report"]
    I -->|否| L["交叉验证任务书<br/>Verify brief (always)"]
    K --> M{"交叉验证?<br/>Verify?"}
    L --> M

    M -->|是| N["另一个 LLM 验证<br/>Independent check"]
    N -->|补检/修订| D

    M -->|否| O["结束<br/>Done ✓"]
```

## 🚀 Quick Start · 快速开始

```bash
git clone --branch feature/shidi-pro-flash --single-branch https://github.com/IcyCreamDAS/shidi-skill.git
mkdir -p ~/.claude/skills
cp -r shidi-skill/skills/shidi ~/.claude/skills/
```

然后直接说 / *then just say*：

```text
师弟，帮我详细调研一下 XXX              # Pro
师弟，请你用 pro 模式给我调研一下 XXX   # Pro
师弟，帮我快速调研一下 XXX              # Flash
师弟，请你用 flash 模式给我调研一下 XXX # Flash
```

**一次下载即包含 Pro 和 Flash 两个完整版本。** 未专门提到“详细”“快速”“pro”或“flash”时，默认 **Pro**：适合完整检索框架、交互确认和深度交付；Flash 适合少确认、快速启动。两种模式改变工作流程，可以使用宿主支持的模型。

其他任务示例：

```text
师弟，设计一个 XX 实验方案
师弟，把这个数据画成图
师弟，帮我把这篇论文精读一下
```

只喊"师弟"也行——它会先跟你确认任务类型再开工。兼容任何支持 SKILL.md 规范的 agent（Claude Code / Codex / OpenClaw / OpenCode 等）。
*Just "shidi" works too — it confirms the task type before starting. Compatible with any agent that follows the SKILL.md spec.*

> [!IMPORTANT]
> ### 这是执行者，不是许愿池 *An executor, not a genie*
> `harness + model = agent`——师弟只拥有工作流，模型决定天花板。Pro 把角度选择和参数确认交还给你；Flash 会给出明确默认建议并减少形式化确认。脏活累活它拿走，但那个"想法"和"判断"，永远是师兄你的。
> *shidi owns the workflow, the model sets the ceiling. And it never decides for you — angle selection, parameters, trade-offs all bounce back to you. It takes the grunt work; the ideas and judgment stay yours.*

## 🤖 Persona · 人设

- 称呼你为**师兄**（默认；你表明女性身份时称师姐）*calls you "senior" by default*
- 低年级师弟口吻：谦逊有分寸、自然亲近——"师兄，这是我做的 XXXX，你看要不要 XXXX" *a humble, slightly cheeky junior — "here's what I made, what do you think?"*
- 被你指出问题时略带崇拜（"还是师兄眼尖"），但科研判断就事论事 *praises you when corrected, never bends on science*
- 人设仅在"师弟"触发时生效 *persona activates only on the trigger word*

*整个过程中你输入的轮次会比较多——只有保留了师弟没事就爱问问题的特性，你才知道你用的确实是师弟 skill :)*
*Yes, it asks a lot of questions — that's how you know it's really shidi.*

## ⚙️ Dependencies · 依赖

- **核心零依赖** *Zero core deps*：纯 SKILL.md + Markdown，无需安装任何包
- 报告渲染 *Report rendering*：`markdown` 包（HTML/PDF），本机 Edge / Chrome / Chromium（PDF，自动跨平台探测，可用 `SHIDI_BROWSER` 指定）
- 可选增强 *Optional*：作图分支 numpy/scipy/matplotlib/pandas/sympy（3D 用 pyvista）；PDF 抽取层 pdf-inspector
- 评分 / 引用核验脚本 *score_papers.py / verify_refs.py*：stdlib 零依赖
- 检索降级链 *Search fallback chain*：WebSearch → 开放学术 API（OpenAlex/Crossref/arXiv，无需 key）；PDF 下载的 Unpaywall 兜底需 `UNPAYWALL_EMAIL`

## 🛡 Guardrails · 防护机制

1. 七维评分每维封顶，总分/排序由 `score_papers.py` 计算（不信任模型心算）*seven-dim caps; totals and ranking computed by script*
2. 主题匹配 <10 分一票否决 *topic-match <10 → veto*
3. DOI / arXiv ID / URL 三级去重 *triple dedup*
4. **不编造**：无法核验的引用/DOI/数据一律标"未验证"；报告落盘后必跑 `verify_refs.py`（DOI 解析/撤稿/文风）*no fabrication; every report passes verify_refs.py before rendering*
5. 阅读状态透明：全文 ✅ / 仅摘要 ⚠ / 不可获取 ❌ *honest reading-depth labels*
6. 交叉验证意见逐条回应（采纳/不采纳+理由），不盲从 *every verification comment gets adopt/reject + reason*

## 📜 Credits · 致谢

设计理念借鉴 [nature-skills](https://github.com/Yuan1z0825/nature-skills)（袁一哲团队）：Router 分层、评分维度设计（v1 六维 → v2 七维）、检索降级链、论文卡片等机制。
*Design ideas borrowed from nature-skills (Yuan1z0825 team): routing, scoring, search fallback, paper cards.*

## 📄 License · 许可证

[MIT License](LICENSE) — 随便用，记得请师弟喝奶茶 🧋 *Free to use — just buy shidi a bubble tea.*


[公开资源与历史范围 / Public resources and historical scope](PRIVACY.md)
