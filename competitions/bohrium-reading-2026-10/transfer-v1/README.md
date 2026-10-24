# 多篇论文支持的PEEK涂层研发判断

状态：材料、任务、事先标准与原版本Skill已冻结；实际运行状态另见 `runs/`，准备文件不代表执行完成。此批为开发验证，不是正式赛事得分。

目标是核验上一轮的场景局限：详尽专家清单和单篇整理后的输入已使两组达到预设检查上限。本批不修改Skill，先测三篇公开原始研究对同一涂层目标的证据整合。具体产品约束属于评测设定，不包含企业真实配方或数据。

- `task.md` / `criteria.md`：双方同样收到的完整业务任务与结果要求。
- `materials/`：三篇新论文的原始JATS XML、阅读副本、来源、作者和CC BY 4.0许可。
- `evaluation/reference.json`：执行前固定的24项AI参考，其中6项重大误导检查；不得给执行者，需作者人工复核。
- `PROTOCOL.md` / `freeze.json`：配对、预算、版本、记录和指标边界。不能据本批直接声称人工省时。
- `record_command.py`：保存实际shell输入、输出、失败、重试、退出码；不是平台完整会话导出。

仓库根目录准备两份相互独立的运行目录：

```sh
python3 competitions/bohrium-reading-2026-10/transfer-v1/prepare.py --arm with --out ../transfer-with-new
python3 competitions/bohrium-reading-2026-10/transfer-v1/prepare.py --arm without --out ../transfer-without-new
```

将各目录中的PROMPT.md交给全新会话，只允许读取对应目录。不要提供整个仓库或本README：其中包含评估信息及其他运行结果。任务不联网、没有真实实验或对外提交，双方最多16条记录命令、15分钟、32 KiB核心输出。

有/无Skill使用相同记录方式，例如在各自运行目录执行：

```sh
python3 record_command.py <<'COMMAND'
cat PROMPT.md
COMMAND
```

完整保留旧A组以及本批所有尝试和不利结果。若继续修改Skill，则另起版本和新验证集。本批不复用旧作品包的官方索引，不自动替换旧A成绩或宣称新增B/C加分。
