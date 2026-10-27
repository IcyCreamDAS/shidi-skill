# 文献 → 配方/性能数据抽取 schema

用途：把多篇文献里的「配方 → 性能」数据整理成**可比、可建模**的表格。
适用：材料/高分子/涂层方向的文献调研与 AI4S 数据准备；不适用于纯理论/综述文献的性能汇总。

> **核心纪律：没有测试标准与条件的性能数字不可比。** 同样是"拉伸强度"，ASTM D638 与
> ISO 527 的样条尺寸/拉伸速率不同；同样是 MFR，2.16 kg vs 5 kg 载荷、360 °C vs 400 °C
> 结果能差数倍。缺元数据 → 标"信息不足"，不硬凑进同一张表。

## 必需列（CSV 模板见 `templates/formulation_properties.csv`）

| 列名 | 说明 | 示例 |
|:--|:--|:--|
| `doi` | 来源 DOI，必填（便于回查） | 10.1016/j.polymer.2020.122456 |
| `source_page` | 数据所在页码/表号 | p.7 Table 3 |
| `material` | 材料体系（示例统一匿名） | example-system |
| `formulation_id` | 文献内配方编号（没有就填 1,2,3） | F3 |
| `component` | 组分角色名（matrix / filler / additive_a / additive_b…） | filler |
| `role` | 组分角色（与 component 对应） | matrix / filler / additive_a / additive_b |
| `wt_pct` | 质量分数（%）；若原文为 phr/vol%，换算后注明 | 30 |
| `property` | 性能名（统一命名） | tensile strength |
| `value` | 数值 | 182.5 |
| `unit` | 单位（统一到 SI 或行业惯用单位并注明） | MPa |
| `standard` | 测试标准编号，**必填** | ISO 527-2 |
| `test_conditions` | 速率/载荷/跨距/样条等关键条件 | 5 mm/min, type 1A |
| `temperature_C` / `humidity_pct` | 环境温湿度（未给标 not-reported） | 23 / 50 |
| `n` | 样本数（未给标 not-reported） | 5 |
| `error_type` / `error_value` | SD / SEM / CI95 / range | SD / 3.2 |
| `value_type` | `measured` / `predicted` / `exploratory`（见下） | measured |
| `notes` | 换算、可疑点、原文矛盾 | converted from phr |

## value_type 三类标签（必须分开）

| 标签 | 含义 | 能否当结论 |
|:--|:--|:--|
| `measured` | 文献报告的实测值 | ✅ 可以，附标准与条件 |
| `predicted` | 文献里的模型/模拟预测 | ⚠️ 可引用为模型结果，不得与实测混算 |
| `exploratory` | 本文档/Agent 的筛选级推断 | ❌ 只能当候选，不进统计 |

**探索级筛选范围 ≠ 统计置信区间**：模型给出的 mean ± 2σ 是筛选带，不要写成 95% CI。

## 汇总规则

1. **同标准同条件才可合并**：不同标准的数据分表存放；要合并必须先换算并注明。
2. **负样本必收**：失败配方/未达指标的数据一并记录（`value_type=measured`，notes 标"failed formulation"），只收冠军数据会让模型学到偏差。
3. **单位统一**：MPa / GPa / kJ/m² / g·10min⁻¹；混用单位会在建模时被当作噪声。
4. **来源可追溯**：每行必须有 doi + source_page；聚合值（如文献综述的表）标原始出处。
5. **缺元数据**：一律 `not-reported`，不要猜；建模前按缺失模式决定是否剔除该行。

## 与建模示例的衔接

`examples/materials_small_data/` 演示了下一步：把这类表喂给分组留出验证 + GP 不确定性 +
约束候选搜索。示例只用合成数据；真实项目仅在有明确公开授权时使用可分享数据。
