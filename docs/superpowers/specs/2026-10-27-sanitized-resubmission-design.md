# 最新 main 全脱敏重打包设计

## 目标

以当前公开 Pro/Flash 资源重新制作 Skill 与 GitHub 两份可上传材料。全部交付内容不得包含指定材料标签、真实企业/雇主/客户信息、NDA 或公司机密数据；工具与模型名称按用户确认保留。

## 方案比较

- 选定：保留原始运行与评分，只更新当前安装资源、文档和包装。用户确认 Pro/Flash 已是最新，无需为外壳重跑。
- 未选：使用 Claude Sonnet 新跑四组。会增加无关成本，且用户已明确否定。
- 未选：直接替换两份旧资源文件而不记录版本关系。会造成证据口径不透明，不采用。

## 包装与版本口径

- 当前安装版来自最新公开 Pro/Flash；原运行仍使用冻结的 Pro `b28eb4e`、Flash `6e03d72`。
- 对照记录、原始报告、PDF、用量、轨迹与既有 ChatGPT/Kimi 评分不改写，不冒称新运行或新评分。
- 包内明确记录当前打包 revision、历史运行版本及“文档级脱敏更新”，并验证 Pro/Flash 的 SKILL.md 与可执行脚本未发生行为性改动。
- A/B 各自保留原有 4 表 3 图，不改变评分者归属。

## 脱敏口径

- 禁止指定材料标签和“中研”出现。
- 禁止真实企业、雇主、客户、NDA、confidential 及公司机密信息；不引用真实企业配方或测试数据。
- 保留 ChatGPT、Claude、Kimi、DeepSeek 等评分/工具名称；不含真实公司机密内容。
- 所有 Markdown、CSV、JSON/JSONL、SVG、TXT、PDF 提取文本、文件路径与公开链接均纳入扫描。

## 交付

- Skill：`submission/`、原始 ZIP、review 索引、真实轨迹、官方检查与 ARM dry-run。
- GitHub：固定公开 commit 的技术分享、离线 materials.zip、submission.txt 与 ARM dry-run。
- 当前安装说明指向默认 `main`；GitHub 公开作品固定到新公开 commit。
- 不上传、不发布小红书；完成后报告可上传状态与剩余风险。

## 验收

当前资源与历史运行版本关系清楚；所有敏感扫描为零命中；原始 PDF 可读且哈希一致；官方结构检查通过；CLI 0.1.43 dry-run 通过；提交说明不含被禁内容。
