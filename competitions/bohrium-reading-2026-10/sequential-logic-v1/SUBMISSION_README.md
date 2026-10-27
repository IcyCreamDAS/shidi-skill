# Shidi：从一句科研灵感到可核验的顺序化学逻辑探索

## 使用场景

本作品评估旧版 Shidi 能否帮助材料研发人员把“只有先光照、后遇湿才打开”的一句话设想转化为有原文依据、边界清楚的候选研究路线。重点不是罗列光敏/湿敏文献，而是区分顺序逻辑、状态保持、跨尺度放大和证据等级。

Skill 位于 `skill/`，版本为 Git `b28eb4e`；`SKILL.md` SHA-256=`51e04a4e853668e6619a824afcd9820531ea7ab267ceba944f9d54d5d65e0eed`。A 案例使用同一版本；没有使用后续的 6e03d72。

## 如何复跑

- `materials/task.md` 是一句用户原始请求，`materials/CONTEXT.md` 是最小共同背景。
- `cases/A/criteria.md` 是运行前冻结的验收标准。
- `runs/A-with/` 含旧 Skill、完整输出和记录；`runs/A-without/` 不含 Skill。
- 两组均为 Kimi Code Desktop 独立 coder 子代理，`kimi-code/kimi-for-coding`（K2.8 Preview）+ 默认 max。只向各组提供自己的 PROMPT、task、CONTEXT 和（with 独有）Skill。禁止读取父会话、其他运行、用户完整档案及宿主全局记忆。
- 预算为每组 12 分钟软墙、24 查询、40 页面动作、8 篇核心文献；允许公开搜索、读取、脚本和 PDF 下载。软限不是平台硬停止器。

## 人工参与与轨迹

主代理 K3.1 Pro 负责冻结协议、统一用户代答和独立核验。with 首轮提问后，主代理按 `ANSWERS.md` 的共同立场具体回答目标、对照、交付和场景，没有提供化学路线、代表论文或评分答案；without 未提问。问答原文见 `runs/A-with/visible_conversation.md`。

`trace-export.jsonl` 由 `export_visible.py` 从真实子代理 wire 事件提取，包含全部可见用户/助手文本和工具事件，不含宿主系统提示、个人背景或隐藏推理。导出仅对本机用户名和绝对路径做确定性脱敏，原始 wire 保存在作者本地；脱敏版不是逐字节原始系统日志，也不含私有思维链或伪造的工具调用。

## 结果与投入摘要

内部九维初核：with 88.75、without 67.50，差 21.25，达到预设的单案例效果门槛。with 的顺序逻辑和证据分级更好，但超过软时间预算，且 token/耗时更高；不能据此宣称稳定优势、官方高分或成本节约。官方高增益档要求至少两组独立公平对照，本包只有一组。

with：6 篇经 pypdf 打开和题名核验的 PDF，Agent 墙钟 1659.432 秒；without：5 篇，585.335 秒。费用均无逐次扣费字段，记“无法核验”，不填 0。完整数字见 `report.md` 和 `evaluation.json`。

## 证据与限制

`pdf-verification.json` 保留每个 PDF 的页数、字节和 SHA-256。报告数值是文献报道值，不是作者新实验数据。without 将水下预浸后照光的纳米海绵误判为顺序排他直接证据；该反例保留，不删除。with 的旧流程产生额外参数确认且超时，亦如实保留。

本包只做 A 的一组配对，未选 B/C。所有已知失败、反爬、付费墙、重试和人工代答均保留。`manifest.json` 和 `review.json` 提供索引。官方结构检查不等于科学结论认可；本包未上传，没有 Attempt ID 或比赛成绩。
