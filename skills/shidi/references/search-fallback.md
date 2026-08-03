# 搜索源降级链 + 高质量期刊定向策略

从 nature-academic-search（T1→T2→T3 源路由）内化，裁剪到本环境可用工具（WebSearch / WebFetch / curl / 免费学术 API）。

## 降级链（每个角度都按此顺序执行）

| 层 | 源 | 用法 | 失败时 |
|:--|:--|:--|:--|
| T1 | **WebSearch 高质量期刊定向** | 关键词 + 期刊名/域名组合查询（如 "关键词" + "期刊名"） | 降 T2 |
| T2 | **WebSearch 普通检索** | 纯关键词（中英文各一轮），不限期刊 | 降 T3 |
| T3 | **开放学术 API**（免费无 key） | OpenAlex / Crossref / arXiv（见下） | 记录"该角度检索受限"并如实报告 |

## 高质量期刊定向策略（T1）

目的：优先命中期刊清单（journal-list.md）内的 🔴高质量文献。

1. 每个角度先用 1-2 个"关键词 + 顶刊名"组合查询（如：`"关键词" + 顶刊名` 或直接组合期刊名）
2. 期刊名用清单内高频项（JACS / Angew / Adv Mater / Macromolecules 等），不必全列——每轮换 1-2 个
3. T1 结果与 T2 合并去重后，命中清单的标 🔴

## 开放学术 API（T3 兜底，结构化数据）

无需 key，WebFetch 或 curl 可用：

- **OpenAlex**：`https://api.openalex.org/works?search=关键词&per-page=25`
  - 返回结构化元数据：标题、期刊（host venue）、年份、被引数、DOI、开放获取状态
  - 可选过滤：`filter=primary_location.source.issn:...`
- **Crossref**：`https://api.crossref.org/works?query=关键词&rows=25`
  - 返回标题、期刊（container-title）、DOI、年份
- **arXiv API**：`http://export.arxiv.org/api/query?search_query=all:关键词&max_results=25`
  - 预印本补充（注意：arXiv 非同行评审，标注"预印本"）

## 全文获取链（A5 阶段）

1. **OA 优先**：检查 OpenAlex 元数据中的 OA 状态 / Unpaywall（`https://api.unpaywall.org/v2/DOI?email=你的邮箱`）
2. **ResearchGate**：`site:researchgate.net + 文献标题` 搜索——作者常上传 author copy / 自传 PDF，这是付费墙外最常见来源；找到 publication 页面后确认"Download full-text"可用
3. **预印本**：arXiv / 作者主页
4. **机构库/商业库**：用户所在机构数据库（CNKI 等）——**提示用户自行下载**，师弟不绕过付费墙
5. 全部尝试后仍获取失败 → 如实报告"未能获取全文"（含已尝试的来源），不编造内容

## 去重规则

- 合并所有来源结果后：按 DOI → arXiv ID → URL 顺序三重去重
- 去重后数量不足 N 篇 → 如实报告缺口，并询问用户是否放宽（数量/关键词/领域）
