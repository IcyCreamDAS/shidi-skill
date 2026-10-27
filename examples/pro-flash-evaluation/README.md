# Pro / Flash / without：两组真实评测实例

这里保留 **2 个跨学科一句话问题 × 3 个独立子代理 = 6 份真实结果**。Pro=`b28eb4e`，Flash=`6e03d72`，without 不加载 Skill。所有执行代理均为 K2.8 Preview + max；禁止读取或利用宿主用户记忆。

这些实例展示的是**质量与自主性的权衡，而不是某一版本永远更好**。ChatGPT 权重续评是主要参考，Kimi 修正评分和三大汇总用于交叉检查；续评不是 ChatGPT 最终公开评分或官方成绩。

## 顺序化学逻辑

> 能不能用一串选择性化学反应代替电子逻辑电路，让材料只有在“先光照、后遇湿”时才打开？

![顺序逻辑三大汇总六维图](sequential-logic/aggregate-six-dimensions.png)

| 条件 | ChatGPT 权重续评 | Kimi 修正评分 | 三大汇总 | 核验 PDF | Agent 墙钟 |
|---|---:|---:|---:|---:|---:|
| [Pro](sequential-logic/pro/) | 93 | 88.75 | 89.25 | 6 | 1659.432 s |
| [Flash](sequential-logic/flash/) | 73 | 80.00 | 73.00 | 3 | 503.256 s |
| [without](sequential-logic/without/) | 58 | 67.50 | 58.50 | 5 | 585.335 s |

Pro 识别了水下预浸后照光不能证明逆序关闭，守住关键科学关口；Flash 更快但把反序无效说得过满；without 将同一来源误作直接证据。

其他图表：[ChatGPT 续评](sequential-logic/chatgpt-six-dimensions.png) · [Kimi 修正](sequential-logic/kimi-six-dimensions.png)。表格：[ChatGPT 细则](sequential-logic/chatgpt-rubric.md) · [Kimi 细则](sequential-logic/kimi-rubric.md) · [最终评分](sequential-logic/final-scores.md) · [用量](sequential-logic/usage.md)。

## 涂层“疫苗式损伤记忆”

> 能不能让一层涂层像打过疫苗一样，第一次划伤后留下记忆，下次受伤时修复得更快？

![损伤记忆三大汇总六维图](damage-memory/aggregate-six-dimensions.png)

| 条件 | ChatGPT 权重续评 | Kimi 修正评分 | 三大汇总 | 核验 PDF | Agent 墙钟 |
|---|---:|---:|---:|---:|---:|
| [Pro](damage-memory/pro/) | 92 | 91.25 | 90.00 | 3 + 1 XML | 316.917 s |
| [Flash](damage-memory/flash/) | 75 | 76.25 | 77.00 | 2 | 205.852 s |
| [without](damage-memory/without/) | 70 | 81.25 | 71.50 | 6 | 324.277 s |

Pro 明确“自增强不等于第二次修复加速”，并形成双循环证伪实验；Flash 的全文阅读较少；without 的中心表述存在矛盾。三组均未找到完整的二次加速时序对照证据。

其他图表：[ChatGPT 续评](damage-memory/chatgpt-six-dimensions.png) · [Kimi 修正](damage-memory/kimi-six-dimensions.png)。表格：[ChatGPT 细则](damage-memory/chatgpt-rubric.md) · [Kimi 细则](damage-memory/kimi-rubric.md) · [最终评分](damage-memory/final-scores.md) · [用量](damage-memory/usage.md)。

## 实例内容

每个组别目录均包含：

- `task.md`、`CONTEXT.md` 和 `run.json`：输入、模型、版本、用量和耗时；
- `visible_conversation.md`：可见用户问答；
- `trace-export.jsonl`：脱敏的可见文本与工具事件，不含宿主系统提示或隐藏推理；
- `output/`：最终报告、文献清单、失败记录、运行说明和 PDF 验证；
- 每案例的 4 个表（Markdown+CSV）和 3 张六维图（PNG+SVG）。

[make_radar.py](make_radar.py) 与 [make_figures.py](make_figures.py) 可复现绘图；[build_tables.py](build_tables.py) 生成表格。各案例 `RESULTS.md` 保留完整证据边界。

## 脱敏与原件边界

- 公开前扫描用户名、绝对路径、宿主记忆、账号/设备码、凭据和签名 URL；原始 wire 不进入仓库。
- 本实例不直接收录 PDF 二进制原件：公开获取不自动等于允许再分发，许可需逐项确认。文献清单保留 DOI/来源链接，`pdf-verification.json` 保留页数、字节和 SHA-256，便于复核。
- 时间/token 为平台日志数据；费用没有逐次扣费字段，统一记无法核验。实验预测阈值不是实测结果。
- 两轮 Pro 均显示增益，但单主题单次运行不能证明所有任务都有同等效果；公共提示词也已预先拆解部分研究问题。
