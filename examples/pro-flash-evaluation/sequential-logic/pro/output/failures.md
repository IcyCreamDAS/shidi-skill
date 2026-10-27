# 失败清单：下载与获取失败全记录

> 纪律：不把链接当已下载、不把摘要当全文。以下每一条均为真实尝试（时间戳见 run-notes.json）。

| # | 目标 | DOI/URL | 失败类型 | 细节与已试重试 |
|---|---|---|---|---|
| F1 | Margulies 2007 JACS（分子键盘锁奠基） | 10.1021/ja065317z | 付费墙 | 未尝试下载（ACS 非 OA，预算内不代寻 Sci-Hub）；经 [2] Pischel 综述转引确认内容 |
| F2 | Sequence-Dependent Mesophase Cascades（Macromolecules 2017） | 10.1021/acs.macromol.6c01668 | 反爬 403 | pubs.acs.org 文章页 FetchURL 返回 HTTP 403；仅得检索摘要（⚠） |
| F3 | Ritchie 2017 PCCP（薄膜光键盘锁） | 10.1039/C7CP02818K | 反爬 403（RSC） | articlepdf 与 getauthorversionpdf 均被 RSC Cloudflare 类防护拦截（curl 返回 5.7KB HTML 挑战页）；OpenAlex 标记 OA 但 curl/FetchURL 均 403；最终 ⚠ 摘要级 |
| F4 | Zhao 2015 RSC Adv.（PAG 形状记忆水凝胶） | 10.1039/C5RA14421C | 反爬 403（RSC） | 同上；OpenAlex 未给 OA 直链；⚠ 摘要级（检索摘要） |
| F5 | Li 2022 JMCA（光湿跳跃致动器） | 10.1039/D2TA07339K | 反爬/无 OA（RSC） | RSC 页面声明 "Author version available" 但 getauthorversionpdf 403；S2 API 持续 429 限流；题录级 |
| F6 | MDPI IJMS 2022（SP/MC 两亲分子） | 10.3390/ijms231911535 | 反爬 409（MDPI） | mdpi.com /pdf 两次尝试（含完整浏览器头+Referer）均 409；⚠ 摘要级 |
| F7 | Light-Driven Expansion of Spiropyran Hydrogels（OSTI） | https://www.osti.gov/servlets/purl/1798323 | 连接失败 | curl 返回 http 000（连接失败，疑网络层阻断），两次尝试；❌ |
| F8 | PMC 官方 OA 工具 | oa.fcgi?id=PMC3108296 | 服务 404 | NCBI oa.fcgi 404；改用 J-STAGE 直链成功（见成功记录） |
| F9 | Semantic Scholar API | — | 限流 429 | 连续 429（共享出口 IP 限流）；改用 OpenAlex/Crossref 成功核验 DOI |

## 成功记录（对照）

| 文件 | 来源 | 结果 |
|---|---|---|
| output/pdfs/01_irie2010_diarylethene_pjab.pdf | J-STAGE 官方 OA（10.2183/pjab.86.472） | 509 KB，pypdf 核验标题/作者匹配，12 页 |
| output/pdfs/02_pischel2018_keypad_csr.pdf | Chalmers 机构库 | 4.5 MB，首页题名匹配，15 页 |
| output/pdfs/03_erbas2018_logicgates_csr.pdf | Bilkent 机构库 | 6.5 MB，首页题名匹配，22 页 |
| output/pdfs/05_jacs2021_spiropyran_hydrogel.pdf | Groningen（rug.nl）作者稿 | 2.8 MB，首页题名/作者匹配，10 页 |
| output/pdfs/06_kobe_spiropyran_silica.pdf | 神户大学机构库（加密 PDF，已解密读取） | 225 KB，首页题名/刊名/年卷页匹配，12 页 |
| output/pdfs/10_weinstain2020_release_review.pdf | PMC 镜像存储（rcstorage…/PMC7833475.pdf） | 13.8 MB，首页题名/作者/刊年匹配，138 页 |

> 注：04/07/08/09 号文件名保留给了失败尝试，实际不存在对应 PDF；为避免"链接当已下载"，目录内不含这些占位文件。
