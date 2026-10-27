# main 双模式发布设计

## 目标

让普通用户从默认 `main` 安装稳定的 Pro/Flash 双模式 Skill，同时保持竞赛材料与产品发布分离。

## 纳入

- `skills/shidi/SKILL.md` 的轻量 Router，以及 `modes/pro/`、`modes/flash/` 的完整流程、脚本与资源。
- 双模式所需根资源 `focused-reading.md`，以及 `tests/test_mode_router.py`。
- 根中英文 README 的双模式说明、默认 main 安装方式和现有脱敏 ML 示例。
- 保留 main 当前 `paper-reading.md` 与 `data-extraction-schema.md`，并让 Pro/Flash 的 schema 与 main 当前版本一致。

## 排除

- `competitions/`、`examples/pro-flash-evaluation/`、原始运行轨迹、参赛报告及其链接。
- `AUTHOR_STORY.md`、`GITHUB_SHARE.md` 和包含竞赛路径的第三方通知变更。
- 不改变当前 main 的其他功能或历史。

## 验收

默认 main 安装说明有效；Pro/Flash 路由与冻结文件哈希通过；README 相对链接完整；完整测试、ML 快速演示和脱敏扫描通过；发布分支经 PR 合并后再验证 main。
