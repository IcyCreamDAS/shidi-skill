# Shidi：早期指定论文阅读准备记录

**历史记录入口。** 当前两组探索案例及最终包说明见 [final-submission](final-submission/SUBMISSION_README.md)；本页以下保留早期指定论文阅读试跑的原始状态。

目标是帮助材料研发人员判断论文里的数据是否可比较、方法是否值得进一步复核。使用公开的 PTFE/PEEK 复合材料论文，不使用企业配方或实验数据。

- [实验协议](PROTOCOL.md)：同条件对照、版本冻结、输入边界、日志与成本记录。
- [任务和验收标准](cases/)：A 为模拟与实验并存的论文；B 为体积分数配方与分阶段磨损实验；C 为有意仅保留摘要的材料不足案例。
- [素材来源与许可](materials/SOURCES.md)：原始开放全文 XML、确定性阅读副本及哈希。
- [评估参考](evaluation/README.md)：运行代理不得读取；当前参考由 AI 标注，需人工复核。
- [进展与限制](STATUS.md)：区分代码检查、试跑结果和正式赛事证据。
- [真实试跑报告](pilot-report.md)：A对照未测出准确率增益；B换篇复用完成；C保留部分输出和中断记录。原始输出、用时与失败如实保留。
- [草稿打包与实际校验记录](packaging/README.md)：已通过官方结构检查；完整会话证据仍缺，尚未提交。
- [下一轮多论文对照](transfer-v1/README.md)：保持Skill不变、三篇新论文、24项预先检查，测试涂层研发判断的证据适用性。

## 开始一次独立运行

从仓库根目录执行（仅准备文件，不调用模型，不产生模型费用）：

```sh
python3 competitions/bohrium-reading-2026-10/prepare_run.py --case A --arm with --out ../shidi-reading-runs/A-with-01
python3 competitions/bohrium-reading-2026-10/prepare_run.py --case A --arm without --out ../shidi-reading-runs/A-without-01
```

在相互独立、无共享记忆的模型会话中，分别提供目录内 `PROMPT.md` 及输入文件。`with` 目录额外包含冻结的 Skill；`without` 不包含 Skill。两组使用相同模型、设置、工具权限和预算。不要把整个仓库交给执行代理：仓库含评估参考和其他运行结果。

脚本拒绝覆盖已有目录，记录输入与 Skill 文件哈希；`run.json` 是准备记录，**不是实际会话轨迹**。必须另存宿主原生日志或逐条原样导出的可见对话，保留失败与重试。当前准备脚本不会创建官方 `manifest.json`，也不会把未运行状态包装为有效提交。

将运行目录放在能够持久保存的位置，并及时归档真实输出与日志。不要把 `/tmp` 中尚未导出的记录当作已保存成果；初次开发试跑已遇到会话中断后临时日志无法恢复的问题，状态记录保留在 `pilots/interrupted-20261023/`。

## 赛事资源与提交

[赛题](https://play.bohrium.com/challenge/skill-13890f6a)要求 A 至少一组独立对照；B/C 为可选加分。当前工作按赛题正文六维量表准备，最终规则与期限以主办方通知为准。

```sh
playground task download --challenge-id skill-13890f6a --out my-skill-challenge
```

完整官方资源已取得，下载时未使用 `--skip-datasets`。`official-resources-lock.json` 固定14份资源的版本、大小和SHA-256；官方脚本不随本仓库重新分发。账号登录已解决，凭据不入库。

在仓库根目录运行下列命令，资源参数指向实际下载目录，输出必须是仓库外尚不存在的目录：

```sh
python3 competitions/bohrium-reading-2026-10/build_submission.py \
  --resources ../bohrium-challenge/datasets/paper2arm-task-skill-13890f6a-e481adb7/1/resources \
  --out ../shidi-submission-draft-new
```

脚本先校验官方资源、冻结材料与原始试跑哈希，再复制原件、创建索引并调用同版本 `make_review.py` 与 `check_submission.py`。输出包含 `deliverables/submission.zip`、`official-check.json`、`draft-status.json`；不调用模型、联网或上传，拒绝覆盖。官方工具会给新增ZIP条目写入运行时间，因此不同构建的最终ZIP哈希可能不同；各原始文件保持一致。

当前草稿固定标记为 `ready_to_submit: false`：完整真实会话导出仍缺，失败日志缺口与C中断已披露。取得会话记录、按协议完成正式验证后才能另行准备提交；本脚本不会运行 `submit.py` 或产生回执。
