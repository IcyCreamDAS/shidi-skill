# 来源与制图数据

## 公开实例

- 仓库与安装：https://github.com/IcyCreamDAS/shidi-skill/tree/feature/shidi-pro-flash
- 案例入口：https://github.com/IcyCreamDAS/shidi-skill/tree/feature/shidi-pro-flash/examples/pro-flash-evaluation
- 顺序逻辑分项：同目录 sequential-logic/chatgpt-rubric.md、kimi-rubric.md、final-scores.md、usage.md。
- 损伤记忆分项：同目录 damage-memory/ 的上述文件。

制图使用本次审核后的 evaluation.json、computed-scores.json 以及 PNG。发布时须与包含这些修订的公开 commit 保持一致。

## 评分方法

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

本目录为发布文案及制图脚本；八页最终图片、已发布笔记链接和完整截图需要在小红书通道提交前齐备。
