# Pro / Flash / without：两组实例与 ChatGPT 直接复评

**本页当前主评分由 ChatGPT 于2026-10-27直接阅读既有输出后给出。** 不是让Kimi代打分，也不是只采用ChatGPT提出的权重。评分原档位、加权分、评分者与源报告哈希见[独立复评数据](independent-review/scores.json)，量表见[RUBRIC.md](independent-review/RUBRIC.md)。

两个科研兴趣起点、六份真实运行结果。执行模型统一为K2.8 Preview + max；Pro固定为`b28eb4e`，Flash固定为`6e03d72`，without不加载Skill。每条件一次运行；ChatGPT评阅为事后、非盲、单人内容评价，不是平台成绩，不作统计显著性或稳定普遍增益结论。

六轴为问题保真15%、机制与因果25%、原始证据20%、证伪与对照20%、路线与下一步10%、透明与可审计10%。各轴0–4档，总分为各项“权重×档位÷4”之和。

## 第一题：顺序化学逻辑

> 材料能不能只在“先光照、后遇湿”时才打开？

| 条件 | ChatGPT 直接复评 | 核验 PDF | Agent 墙钟 |
|---|---:|---:|---:|
| [Pro](sequential-logic/pro/) | 78.75 | 6 | 1659.432 s |
| [Flash](sequential-logic/flash/) | 61.25 | 3 | 503.256 s |
| [without](sequential-logic/without/) | 50.00 | 5 | 585.335 s |

![顺序逻辑：ChatGPT直接复评](independent-review/sequential-logic-radar.png)

Pro识别了“水已经存在时，后来生成的酸仍可能触发反应”的逆序风险，重点展示机制与因果判断。

[0–4档位与总分](independent-review/sequential-logic-scores.md) · [六维加权分项](sequential-logic/chatgpt-rubric.md) · [当前总分](sequential-logic/final-scores.md) · [实际用量](sequential-logic/usage.md)

## 第四题：涂层损伤记忆

> 涂层能不能像打过疫苗一样，第一次划伤后，第二次修复得更快？

| 条件 | ChatGPT 直接复评 | 核验 PDF | Agent 墙钟 |
|---|---:|---:|---:|
| [Pro](damage-memory/pro/) | 68.75 | 3 + 1 XML | 316.917 s |
| [Flash](damage-memory/flash/) | 67.50 | 2 | 205.852 s |
| [without](damage-memory/without/) | 47.50 | 6 | 324.277 s |

![损伤记忆：ChatGPT直接复评](independent-review/damage-memory-radar.png)

Pro与Flash相差1.25分，不描述为明显领先。这个案例展示Skill如何把类比拆成状态产生、保持与第二次修复动力学，形成可核查的研究问题。

[0–4档位与总分](independent-review/damage-memory-scores.md) · [六维加权分项](damage-memory/chatgpt-rubric.md) · [当前总分](damage-memory/final-scores.md) · [实际用量](damage-memory/usage.md)

## 数据、图表与复现

- `independent-review/scores.json`是当前ChatGPT直接复评的唯一数据源，保留六份源报告的SHA-256。
- `chatgpt-rubric.*`、`final-scores.*`已经切换到这次直接复评；旧的`chatgpt-six-dimensions.*`链接也使用与独立复评目录逐字节相同的图。
- 各组保留任务、背景、实际提示词、模型与用量、可见问答、脱敏工具轨迹、原始报告、文献清单、失败与PDF核验信息。论文原文、模型输出和事后评阅分别保留。

在仓库根目录运行：

```bash
python examples/pro-flash-evaluation/build_tables.py
python -m pip install matplotlib numpy
python examples/pro-flash-evaluation/make_figures.py
python examples/pro-flash-evaluation/independent-review/render_radars.py --out /path/to/exports
```

表格脚本只使用标准库。旧绘图入口复制当前ChatGPT原图，并将Kimi历史图明确标为历史。独立绘图脚本验证评分、量表与源报告哈希，再重绘；无中文字体时使用英文，可用`--font`指定字体。脚本均可通过`--out`输出到独立目录。

## 历史评分的归属

早期科研深度分和工作流分均由Kimi执行；前者采用与ChatGPT讨论的量表，不能归名为ChatGPT直接评分。历史原分保留在两个案例的`evaluation.json`中；`computed-scores.json`的`totals`、`axes`为Kimi历史数据，`current_chatgpt_totals`为本次主评分，不混算成新的综合分。

[顺序逻辑历史评阅](sequential-logic/RESULTS.md) · [损伤记忆历史评阅](damage-memory/RESULTS.md)。`kimi-rubric.*`、`kimi-six-dimensions.*`和`aggregate-six-dimensions.*`只作Kimi历史评分及派生值记录。

原始科研输出与运行前冻结协议不因事后改分而重写。PDF清单保留题名、页数、来源与哈希；此目录不直接收录PDF二进制。费用无逐次扣费字段时保留null，时间与token沿用真实日志。
