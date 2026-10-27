# 来源与制图数据

## 公开实例

- 仓库与安装：https://github.com/IcyCreamDAS/shidi-skill/tree/feature/shidi-pro-flash
- 案例入口：https://github.com/IcyCreamDAS/shidi-skill/tree/feature/shidi-pro-flash/examples/pro-flash-evaluation
- 当前评分与图表：同目录 independent-review/ 的 scores.json、RUBRIC.md、两案例分项与新雷达图。
- 实际用量：sequential-logic/usage.md 与 damage-memory/usage.md；此前评分保留在各案例历史表。

本版制图使用 independent-review/scores.json 与 render_radars.py 生成的 PNG/SVG，分项表可逐项核算。发布时须与包含这些修订的公开 commit 保持一致。

## 当前主展示

当前采用ChatGPT于2026-10-27直接执行的六维内容复评：第一题78.75/61.25/50，第四题68.75/67.50/47.50。图表、分项、量表和源文件哈希见公开实例的 `independent-review/` 目录。此前Kimi分数属于历史评阅，不再作为本版图文主展示。

## 创作缘起与外部来源

- 八月创作经历、Claude Code/Mermaid、两个月使用感受及七年科研经历：作者在本轮直接提供的自述。
- 数学报道：https://openai.com/index/sharing-ai-progress-in-mathematics/
- 官方数学仓库：https://github.com/openai/math （2026-10-27读取为721篇手稿、373个问题族；主稿使用“七百余篇手稿”。）
- 萨特引句：https://plato.stanford.edu/entries/sartre/ （经典表述为“存在先于本质”；“使用中发现意义”为作者自己的联想。）
- DeepSeek价格调整历史：https://api-docs.deepseek.com/news/news260813/ （主稿不固定具体价格，使用预算与模型选择建议。）

## 历史评分方法

两套内部评分均由 Kimi 执行。六维科研深度量表源于与 ChatGPT 的讨论，93、92 等是 Kimi 复评分值。工作流评分单独展示；综合展示仅合并两套量表的证据与自主相关分量，其他分量沿用深度分。

每个案例设三个独立会话，分别运行 Pro、Flash、without；每条件 n=1。Pro、Flash 是 Skill 流程名称，without 是不加载 Skill 的对照；执行模型统一为 K2.8 Preview + max。

## 关键原文

- UV 响应纳米海绵：https://doi.org/10.1038/srep12908
- 分子键盘锁综述：https://doi.org/10.1039/C7CS00287D
- 二芳基乙烯光致变色综述：https://doi.org/10.2183/pjab.86.472
- 损伤自增强水凝胶（Wang 等，Nature Materials 2025）：https://doi.org/10.1038/s41563-025-02137-6
- 聚合物机械化学工具：https://doi.org/10.1039/d0cs00940g
- 力化学级联强化：https://doi.org/10.1002/anie.202010043
- 潜伏催化剂与活性种持久性：https://doi.org/10.1021/om300161z

## 用量与配图

时间与 token 来自各组 run.json；PDF 数量来自 pdf-verification.json。损伤记忆 Pro 另取得一个全文 XML。材料未产生新的作者实验实测数据。

本目录为发布文案及制图脚本；十页最终图片、已发布笔记链接和完整截图需要在小红书通道提交前齐备。
