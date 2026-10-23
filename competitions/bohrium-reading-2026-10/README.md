# Shidi：材料论文的实验条件提取与证据核验

**状态：参赛准备 / 开发试跑；未上传、未取得赛事成绩。**

目标是帮助材料研发人员判断论文里的数据是否可比较、方法是否值得进一步复核。使用公开的 PTFE/PEEK 复合材料论文，不使用企业配方或实验数据。

- [实验协议](PROTOCOL.md)：同条件对照、版本冻结、输入边界、日志与成本记录。
- [任务和验收标准](cases/)：A 为模拟与实验并存的论文；B 为体积分数配方与分阶段磨损实验；C 为有意仅保留摘要的材料不足案例。
- [素材来源与许可](materials/SOURCES.md)：原始开放全文 XML、确定性阅读副本及哈希。
- [评估参考](evaluation/README.md)：运行代理不得读取；当前参考由 AI 标注，需人工复核。
- [进展与限制](STATUS.md)：区分代码检查、试跑结果和正式赛事证据。
- [真实试跑报告](pilot-report.md)：A对照未测出准确率增益；B换篇复用完成；C保留部分输出和中断记录。原始输出、用时与失败如实保留。

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

完整取得官方资源后，使用同版本 `make_review.py`、`check_submission.py` 和 `submit.py`，按模板生成作品、索引与回执。不要加 `--skip-datasets`。账号登录在本机进行，密钥不入库。提交需要真实会话导出；本目录不包含伪造的原生轨迹，也不提供假成绩。
