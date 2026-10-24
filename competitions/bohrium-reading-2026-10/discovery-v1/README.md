# discovery：一句话科研灵感的低负担启动

状态：一句话案例与候选 Skill 冻结后进行配对验证；运行结果见 `runs/` 和 `RESULTS.md`。本批不是正式赛事得分。目录名保留 `discovery-v1`，当前协议为 v2；旧 PEEK 耐磨基线单独标注，不与新案例混算。

- `PROTOCOL.md`：配对、隔离、回合与修改纪律。
- `criteria.md`：灵感保真、澄清负担、最小验证交付物和完成度检查。
- `cases/`：每组只有一句科研设想；`evaluation/profiles.json` 仅供协调者按需回答。
- `freeze.json`：旧任务基线锁；`freeze-patched.json`：当前候选锁。
- `prepare.py`：准备隔离运行目录，不调用模型，不执行检索；with 的提示直接内嵌冻结 Skill，避免“要求不调用工具却又要求读 Skill”的隔离矛盾。

从仓库根目录准备开发配对（输出必须是不存在的新目录）：

```bash
python competitions/bohrium-reading-2026-10/discovery-v1/prepare.py --case dev-peek --arm with --lock freeze-patched.json --out ../shidi-discovery-runs/dev-peek-spark-k28max-01-with
python competitions/bohrium-reading-2026-10/discovery-v1/prepare.py --case dev-peek --arm without --lock freeze-patched.json --out ../shidi-discovery-runs/dev-peek-spark-k28max-01-without
```

每组只读取自己的 `PROMPT.md`。父代理按协议保存可见对话和 `run.json`；这些是可见记录，不是平台完整原生会话。
