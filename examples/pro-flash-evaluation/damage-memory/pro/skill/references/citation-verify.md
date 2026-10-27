# 引用导出与多源核验

从 nature-citation + nature-ref-verifier 内化。文献调研输出阶段使用。

## 引用格式导出

- 默认 **GB/T 7714**（中文论文/报告）；用户指定其他格式（ACS / Nature / APA）时按其执行
- 导出字段完整：作者（全列或 et al. 截断按格式规则）、标题、期刊、年、卷、页、DOI
- 输出形式：Markdown 引用列表 + 可选的 .bib / .ris 文件

## 多源核验（防假引用）

交付引用列表前，每条引用必须通过核验：

| 检查项 | 方法 |
|:--|:--|
| DOI 真实性 | 用 DOI 查询 OpenAlex（`https://api.openalex.org/works/https://doi.org/<DOI>`）或 Crossref（`https://api.crossref.org/works/<DOI>`），确认存在且标题匹配 |
| 标题-期刊匹配 | 标题、期刊、年份三字段与检索结果交叉比对，不一致即标"⚠ 待核实" |
| 页码/卷期 | 从 API 元数据核对；API 无此信息则标"未验证" |

## 硬规则

1. **绝不编造 DOI / 文献**——这是红线。无法核验的引用标记"未验证"，或从结果中剔除并说明
2. 每篇文献至少有一个来源锚点（DOI / URL / 数据库 ID）
3. 同一文献在两个来源信息冲突时，以原始出版方/数据库为准，冲突处显式标注

## 他引/引用者审计（用户需要时）

参考 nature-academic-search 的 strict-other-citation 逻辑：

- 查某篇文章的被引数、严格他引数（排除作者自引）
- 识别引用者身份（院士、Fellow、领域大牛）——只报告事实，不做价值判断
- 工具：OpenAlex 被引数据（`filter=cites:<work_id>` 查询引用者）

## 输出模板

```markdown
## 参考文献（N 篇，已核验 M 篇）

[1] 作者. 标题. 期刊, 年, 卷, 页. DOI: 10.xxxx/xxxx ✅
[2] ... ⚠ 未验证（缺少来源锚点）
```
