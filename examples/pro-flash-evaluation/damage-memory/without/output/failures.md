# 失败清单

1. **Li et al. 2025, Adv. Funct. Mater.（10.1002/adfm.202507220）全文 PDF 未取得**。OpenAlex 确认 is_oa=false、无任何机构库全文。仅获得摘要（NASA ADS + 北京化工大学新闻页交叉确认题名/作者）。这是与"损伤触发加固"最直接相关的 2025 年论文，建议通过机构订阅获取。
2. **MDPI 两篇 OA 综述下载被反爬拦截**（返回 406 Access Denied）：
   - Sanyal et al. 2024, "Emerging Trends in Smart Self-Healing Coatings", _Coatings_ 14(3), 324（10.3390/coatings14030324）
   - Wang et al. 2025, "Autonomic Self-Healing of Polymers", _Molecules_ 30(3), 469（10.3390/molecules30030469）
   均为 OA 但 curl 被拦；浏览器通道时间不够逐篇抓取。损失已用 PMC 同类综述（Al-Maadeed 2019、Cremaldi 2018）补偿。
3. **Hayes et al. 2007（PMC2359850）PDF 未下载**：仅用于一条反证数据（65%→35%→30%），在预算内选择不消耗页面动作。
4. **下载通道重试记录**：PMC 直接 PDF 端点（Cloudflare/JS 挑战）失败 2 轮；europepmc.org ?pdf=render 失败 2 轮；最终通过 europepmc.org `/api/getPdf?pmcid=` 端点全部成功。
5. **Nature 正刊出版版**：Matsuda 2025 取得的是 PMC 绿色 OA 作者稿（内容与正刊基本一致，但排版为投稿稿），非出版商排版版。
