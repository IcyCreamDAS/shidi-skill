# 最终评分：两位评分者与派生汇总

| 条件 | ChatGPT 直接复评 /100 | Kimi 工作流 /100 | 汇总（公式计算）/100 |
|---|---:|---:|---:|
| pro | 78.75 | 88.75 | 77.25 |
| flash | 61.25 | 80.00 | 61.00 |
| without | 50.00 | 67.50 | 49.75 |

ChatGPT分数来自[真实复评](../independent-review/scores.json)，Kimi工作流分来自evaluation.json。均为既有输出的事后评价，每条件一次运行；不是平台成绩。
汇总沿用原公式，以真实ChatGPT分项替换早期Kimi科研深度分：Q/M/F/S保持ChatGPT加权分；E=(ChatGPT证据分+Kimi证据两项合计×20/25)÷2；A=(ChatGPT透明分+Kimi自主分)÷2；最后六项相加。汇总不是第三位评分者，也不是两个总分的平均值。旧数值另存historical-computed-scores.json。
