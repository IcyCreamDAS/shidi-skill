# 参考勘误

2026-10-23：首次试跑分派后、输出评阅前，核对原始 XML 发现 A15 的公式锚点误写为 Eq. 7，实际为 **Eq. 3 / XML disp-formula3**（AR = Nleave / Ntotal）。参考结论及检查项不变；原冻结 CSV 保留，评阅按正确锚点回查。此勘误未提供给执行代理。

同日：发现初版转写器漏掉原始 XML 在正文外保存的浮动表格和图注，影响 B 的阅读副本；完整 XML 始终包含它们。修复转写器并添加针对性测试，重新生成 B 阅读副本。旧 B 副本保存在 `pilots/interrupted-20261023/B-input-reading-copy.md`，旧 `pilot-freeze.json` 保留为历史记录；当前材料使用 `ready-freeze.json`。四次初始尝试未取得最终输出，不计算质量分。
