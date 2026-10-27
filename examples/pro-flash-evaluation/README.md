# Pro / Flash / without：两组跨领域探索实例

两个科研兴趣起点，六份真实运行结果。Pro 固定为 `b28eb4e`，Flash 固定为 `6e03d72`，without 不加载 Skill；执行模型统一为 K2.8 Preview + max。各组从独立会话开始，按共同任务要求探索，实际问答与投入保留在记录中。

[技术文章](../../GITHUB_SHARE.md)解释如何从论文中的相似机制，找到原问题尚缺的证据。

## 顺序化学逻辑

> 能不能用一串选择性化学反应代替电子逻辑电路，让材料只有在“先光照、后遇湿”时才打开？

Pro 识别了“水已在时后来生成的酸仍可能反应”的逆序风险，将问题推进到中间状态保持与反向路径验证。

| 条件 | 科研深度评分 | 工作流评分 | 综合展示 | 核验 PDF | Agent 墙钟 |
|---|---:|---:|---:|---:|---:|
| [Pro](sequential-logic/pro/) | 93 | 88.75 | 89.25 | 6 | 1659.432 s |
| [Flash](sequential-logic/flash/) | 73 | 80.00 | 73.00 | 3 | 503.256 s |
| [without](sequential-logic/without/) | 58 | 67.50 | 58.50 | 5 | 585.335 s |

![顺序逻辑科研深度](sequential-logic/chatgpt-six-dimensions.png)

[工作流图](sequential-logic/kimi-six-dimensions.png) · [综合展示图](sequential-logic/aggregate-six-dimensions.png) · [深度分项](sequential-logic/chatgpt-rubric.md) · [工作流分项](sequential-logic/kimi-rubric.md) · [总分](sequential-logic/final-scores.md) · [用量](sequential-logic/usage.md)

## 涂层损伤记忆

> 能不能让一层涂层像打过疫苗一样，第一次划伤后留下记忆，下次受伤时修复得更快？

Pro 区分损伤自增强与第二次修复加速，比较潜伏活性种、机械自由基两条路线，并将状态保持与双循环修复动力学作为验证问题。

| 条件 | 科研深度评分 | 工作流评分 | 综合展示 | 核验 PDF | Agent 墙钟 |
|---|---:|---:|---:|---:|---:|
| [Pro](damage-memory/pro/) | 92 | 91.25 | 90.00 | 3 + 1 XML | 316.917 s |
| [Flash](damage-memory/flash/) | 75 | 76.25 | 77.00 | 2 | 205.852 s |
| [without](damage-memory/without/) | 70 | 81.25 | 71.50 | 6 | 324.277 s |

![损伤记忆科研深度](damage-memory/chatgpt-six-dimensions.png)

[工作流图](damage-memory/kimi-six-dimensions.png) · [综合展示图](damage-memory/aggregate-six-dimensions.png) · [深度分项](damage-memory/chatgpt-rubric.md) · [工作流分项](damage-memory/kimi-rubric.md) · [总分](damage-memory/final-scores.md) · [用量](damage-memory/usage.md)

## 评分与图表

两套内部评分均由 Kimi 完成。六维科研深度量表源于与 ChatGPT 的讨论，实际分数由 Kimi 复评给出。综合展示按公开公式计算，并非另一次独立评阅。每案例每条件运行一次。

每个案例的 `evaluation.json` 保存原始分项与来源；`computed-scores.json` 保存派生总分和图轴。深度六轴是问题、机制、证据、证伪、路线、透明与自主。工作流图由九项指标归并成探索、证据、PDF、主题判据、综合与边界、交互六轴，按图上的实际轴名解释。

保留历史文件名 `chatgpt-rubric.*` / `chatgpt-six-dimensions.*` 以兼容既有链接；显示名称与评分执行者以本页及表内说明为准。

## 离线复现表格与图表

从仓库根目录执行：

```bash
python examples/pro-flash-evaluation/build_tables.py
python -m pip install matplotlib numpy
python examples/pro-flash-evaluation/make_figures.py
```

原始数据随仓库提供，无需作者电脑上的目录。表格脚本只使用 Python 标准库。制图脚本优先使用系统中文字体，否则使用英文轴名；也可加 `--font /path/to/CJK-font.otf` 指定字体。`make_radar.py` 是同一绘图入口的兼容名称。两脚本均支持 `--out /path/to/output`，可将复现产物输出到独立目录。

## 文件索引

每个组别目录保留 `task.md`、`CONTEXT.md`、`PROMPT.md`、`run.json`、`visible_conversation.md`、`trace-export.jsonl` 和 `output/`。轨迹包含可见文本与工具事件，登录跳转中的账号信息及本机路径做脱敏；不含宿主系统提示或隐藏推理。

每个案例另含四类表格（深度分项、工作流分项、总分、用量；Markdown + CSV）及三类图（PNG + SVG）。`RESULTS.md` 为原始协调评阅记录。

本目录提供文献 DOI、来源、PDF 核验信息与 SHA-256；不在本目录直接收录 PDF 二进制。金额无逐次扣费字段，保留 null。
