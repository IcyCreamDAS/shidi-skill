# 草稿构建与校验记录

这是开发试跑的可审阅草稿，不是正式参赛回执或成绩。

- `official-check.json`：原样保存官方 `check_submission.py` 的实际输出。返回 `intake_complete`，88个文件、28处证据节选，结构缺项为空；该工具不评估科学正确性或记录真实性。
- `draft-status.json`：该次ZIP的SHA-256、字节数、原始输出保留检查及证据缺口。`ready_to_submit`、`platform_trace_supplied`、`uploaded` 均为false，Attempt ID和分数为空。
- `../official-resources-lock.json`：实际下载的规则版本与官方资源哈希。执行前严格比对，避免错用另一版模板/校验器。

运行 `../build_submission.py` 可从仓库内现存原件重建草稿；命令见上一级README。原始文件不会被改写，也不会根据终端输出编造完整会话。官方工具会写入ZIP时间元数据，因此重新构建时以新的实际哈希为准，不承诺ZIP容器字节完全一致。

当前限制：完整相关会话导出未取得；第一轮四次尝试部分原始日志无法恢复；C第二次运行在生成文件后中断。A两组适用检查均为27/27，尚无准确率增益证据。新的正式验证需要遵守预先协议并使用未参与开发的材料，保留失败与零增益结果。

耗时元数据更正：无Skill运行原件使用 `duration_seconds`，其他完整运行使用 `elapsed_seconds`。打包工具现兼容两者；早期草稿在manifest中漏填无Skill耗时，原始执行说明与报告的469.749秒一直保留。当前manifest保留原件精度469.749423秒，原始输出不变。
