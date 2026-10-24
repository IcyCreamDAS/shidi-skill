# 素材来源与许可

两篇论文由作者按 CC BY 4.0 开放。原始 JATS XML 从 Europe PMC 全文接口取得，原件未改；衍生 Markdown 标明来源及变更。许可证见 https://creativecommons.org/licenses/by/4.0/ 。

本批输入不含图像像素、PDF 或补充附件；只能将图注/正文描述作为文字证据，不能声称视觉核验。PDF 来源请求返回 HTTP 403 或浏览器检查 HTML，未将这些响应冒充 PDF。

## 案例 A
Molecular Dynamics Simulation and Experimental Study of the Mechanical and Tribological Properties of GNS-COOH/PEEK/PTFE Composites

DOI: https://doi.org/10.3390/polym16182572
全文来源：https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11435391/fullTextXML
许可：CC BY 4.0；获取日期：2026-10-23 UTC。
SHA-256：`7d7fa9c4f8c17990ab5e98e2e9248da534d9a099fc162e1d4cddef92a981d468`

## 案例 B
Study of Tribological Properties and Evolution of Morphological Characteristics of Transfer Films in PTFE Composites Synergistically Reinforced with Nano-ZrO2 and PEEK Particles
Yuan Qi, Bugong Sun, Yang Zhang, Gui Gao, Peng Zhang, Xiaobao Zheng
DOI: https://doi.org/10.3390/polym15173626
全文来源：https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10490335/fullTextXML
许可：CC BY 4.0；获取日期：2026-10-23 UTC。
SHA-256：`f4023d7cd98dbac93229df0f56e06c31a68f6b0a4e3bad6a2b0f77262ce17326`

## 案例 C
从 A 的真实 XML 提取标题、DOI 和摘要，人为移除方法与结果等章节，用于测试信息不足。不是一篇新的论文，也不作为 B 的独立材料。

## 生成阅读副本
从仓库根目录运行：

```sh
python3 competitions/bohrium-reading-2026-10/readable_xml.py competitions/bohrium-reading-2026-10/materials/A/paper.xml competitions/bohrium-reading-2026-10/materials/A/paper.md
python3 competitions/bohrium-reading-2026-10/readable_xml.py competitions/bohrium-reading-2026-10/materials/B/paper.xml competitions/bohrium-reading-2026-10/materials/B/paper.md
```

Markdown 为阅读辅助，原始 XML 的数值、MathML 公式和表格合并关系为准。XML 非 PDF，不提供虚构页码。
