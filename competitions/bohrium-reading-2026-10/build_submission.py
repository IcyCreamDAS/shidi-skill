#!/usr/bin/env python3
"""Build an explicitly incomplete evidence draft using hash-pinned official tools.

No model calls, network requests, credential access, scoring or upload. Historical
artifacts are copied byte-for-byte; missing conversations are never synthesized.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
SKILL_VERSION = "git:60e3bac54d5e7de4ffd914c1db237f3656ec7463"
RUNS = ("A-with-02", "A-without-02", "B-with-02", "C-with-02")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_relative(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError("Unsafe relative path: " + name)
    if any(x in ("", ".", "..") for x in name.split("/")):
        raise ValueError("Non-canonical relative path: " + name)
    return p


def checked_file(root, name):
    safe_relative(name)
    p = root / name
    if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError("Missing, linked or escaping source: " + name)
    if any(parent.is_symlink() for parent in p.parents if parent != root.parent):
        raise ValueError("Symlink in source ancestry: " + name)
    return p


def verify_resources(resources, lock):
    for item in lock["files"]:
        p = checked_file(resources, item["path"])
        if p.stat().st_size != item["bytes"] or sha(p) != item["sha256"]:
            raise ValueError("Official resource hash/size mismatch: " + item["path"])


def reserve_output(path, repo=REPO):
    path = path.resolve()
    repo = repo.resolve()
    if path == repo or path.is_relative_to(repo) or repo.is_relative_to(path):
        raise ValueError("Output must be outside the source repository and its ancestors")
    path.mkdir(parents=True, exist_ok=False)
    return path


def verify_artifacts():
    freeze = read_json(BASE / "ready-freeze.json")["sha256"]
    for name, expected in freeze.items():
        if sha(checked_file(REPO, name)) != expected:
            raise ValueError("Frozen input/Skill/reference changed: " + name)
    for run in RUNS:
        origin = BASE / "pilots" / run
        index = read_json(origin / "archive-index.json")
        for name, expected in index["sha256"].items():
            if name.startswith("skill/"):
                p = checked_file(REPO / "skills/shidi", name.removeprefix("skill/"))
            elif name.startswith("input/"):
                p = checked_file(BASE / "materials" / run[0], name.removeprefix("input/"))
            else:
                p = checked_file(origin, name)
            if sha(p) != expected:
                raise ValueError("Archived artifact changed: " + run + "/" + name)
    return freeze


def copy_file(source, target):
    if source.is_symlink() or not source.is_file() or not source.stat().st_size:
        raise ValueError("Only nonempty regular files can be packaged: " + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def deterministic_zip(source, archive):
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source.rglob("*")):
            if p.is_symlink():
                raise ValueError("Symlinks cannot be archived")
            if p.is_file():
                rel = str(p.relative_to(source))
                safe_relative(rel)
                if not p.stat().st_size:
                    raise ValueError("Empty artifact: " + rel)
                info = zipfile.ZipInfo("submission/" + rel, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes())


def source_selection(source, path, purpose, *, marker=None, start=0, chars=1800):
    text = (source / path).read_text(encoding="utf-8")
    if marker is not None:
        start = text.index(marker)
    end = min(len(text), start + chars)
    while len(text[start:end].encode("utf-8")) > 8 * 1024:
        end -= 1
    if not 0 <= start < end <= len(text):
        raise ValueError("Invalid source selection: " + path)
    return {"path": path, "start": start, "end": end, "purpose": purpose}


def make_manifest(resources):
    m = read_json(resources / "templates/manifest-with-bonus.json")
    m["skill_version"] = SKILL_VERSION
    m["environment"] = {
        "host": "ChatGPT Work Mode / Codex；独立代理会话，fork_turns=none",
        "model": "Codex，开发者身份说明为 GPT-6；非实际服务端点核验",
        "model_version": "无法取得：接口未暴露精确模型版本；所有运行继承相同父会话设置，未覆写模型或推理档位",
        "tools": ["functions.exec", "exec_command", "Python standard library", "local shell"],
        "dependencies": ["Python 3", "Linux shell；阅读试跑未安装额外依赖或联网"],
        "budget": "每会话最多12次工具调用、15分钟、report.md+evidence.csv合计24 KiB；调用/时间是软限，核心字节有断言；token上限不可取得",
        "human_steps": "用户授权准备及完成网页登录；主代理选择公开输入、制定标准、归档并进行非盲AI初核。阅读执行中无人工补值或提示；参考未经作者人工复核。",
        "isolation_limit": "独立目录和会话；访问范围由指令约束，没有OS级沙箱",
        "usage_unavailable_reason": "接口未暴露模型token及费用，均不填0；环境安装与主代理评阅未计入子任务墙钟",
    }
    sources = {row["case"]: row for row in read_json(BASE / "materials/sources.json")}
    m["materials"] = []
    for case in "ABC":
        names = ["abstract.md"] if case == "C" else ["paper.xml", "paper.md"]
        original = sources["A" if case == "C" else case]
        for name in names:
            row = {
                "path": f"materials/{case}/{name}", "case_ids": [case], "role": "input",
                "source": original["url"], "version": "2026-10-23 snapshot; SHA-256 in ready-freeze.json",
                "retrieved_at": original["retrieved_date_utc"],
                "data_type": "真实摘要，人工截取形成材料不足情境" if case == "C" else "真实公开论文；XML原文及确定性阅读副本",
                "sharing_basis": "CC BY 4.0；作者、DOI、来源和改动见 materials/SOURCES.md",
            }
            if name == "paper.xml": row["text_companion"] = f"materials/{case}/paper.md"
            m["materials"].append(row)
    for case in m["cases"]:
        cid = case["id"]
        case.update(task_file=f"cases/{cid}/task.md", acceptance_criteria_file=f"cases/{cid}/criteria.md",
                    input_files=[r["path"] for r in m["materials"] if cid in r["case_ids"]], reference_files=[])
    m["runs"] = []
    for rid in RUNS:
        folder = BASE / "pilots" / rid
        note_file = folder / "output/run-notes.json"
        notes = read_json(note_file) if note_file.exists() else {}
        with_skill = "without" not in rid
        outputs = [f"runs/{rid}/output/{name}" for name in ("report.md", "evidence.csv")]
        logs = [f"runs/{rid}/output/commands.log"]
        if notes: logs.append(f"runs/{rid}/output/run-notes.json")
        else: logs.append(f"runs/{rid}/coordinator-status.json")
        m["runs"].append({
            "id": rid, "case_id": rid[0], "condition": "with_skill" if with_skill else "without_skill",
            "skill_version": SKILL_VERSION if with_skill else "none",
            "output_files": outputs, "primary_output_files": outputs, "trace_files": logs,
            "started_at": notes.get("started_at_utc", "2026-10-23T06:08:39Z"),
            "duration_seconds": notes.get("elapsed_seconds", notes.get("duration_seconds")), "cost": None,
            "unavailable_metadata": "精确模型配置、token和费用不可取得；C结束时间及工具计数也不可取得",
            "human_steps": [],
            "result": "运行完成；只作开发试跑，评阅见 report.md" if notes else "写出核心文件后因用量限制中断；部分文本符合预期，不声明完整运行或预算合规",
            "trace_scope": "commands.log为真实终端stdout/stderr，run-notes为执行代理说明；不是完整会话导出。coordinator-status只记录主代理观察。",
            "complete_conversation_available": False,
        })
    m["attempt_history"] = {
        "earlier_attempts": ["A-with-01", "A-without-01", "B-with-01", "C-with-01"],
        "status_record": "history/interrupted-20261023/failure-status.json",
        "raw_logs_available": False,
        "reason": "临时目录在会话中断后丢失；仅保留当时已观察状态，不能补建成真实日志。没有把这些失败伪装成有完整输出/轨迹的索引运行。",
    }
    m["submission_readiness"] = {
        "status": "draft-evidence-incomplete", "ready_to_submit": False,
        "gaps": ["平台要求的完整真实相关会话导出尚缺", "早期四次中断的原始日志不可恢复", "C第二次运行缺成功结束及完整元数据", "模型参数不可锁定；参考未经人工复核；正式验证应遵守预先协议另用未参与开发的材料"],
        "official_structure_pass_is_not_scientific_validation": True,
    }
    return m


def make_selections(source):
    rows = []
    def add(path, purpose, **kw): rows.append(source_selection(source, path, purpose, **kw))
    add("materials/A/paper.md", "A原始输入中的力学结果、作者比较及表3", marker="### Table 3", chars=2500)
    add("materials/A/paper.md", "A原始输入中的磨耗表4和性能代价", marker="### Table 4", chars=1500)
    add("materials/B/paper.md", "B摘要报告的最低磨损率；与正文冲突需保留", chars=2400)
    add("materials/B/paper.md", "B正文摩擦阶段及最低磨损率", marker="### 3.1.", chars=5000)
    add("materials/B/paper.md", "B配方体积分数表，不换写成质量分数", marker="### Table 1", chars=1200)
    add("materials/C/abstract.md", "C全部实际输入，仅摘要且人为构造材料不足", chars=10000)
    for rid in RUNS:
        prefix = f"runs/{rid}/output/"
        add(prefix + "report.md", rid + "原始报告：结论、边界与关键结果", chars=2300)
        add(prefix + "evidence.csv", rid + "原始结构化证据：字段、原文定位和条件", chars=2000)
        add(prefix + "commands.log", rid + "实际终端记录开头；不冒充完整会话", chars=1000)
        if rid != "C-with-02":
            add(prefix + "run-notes.json", rid + "实际耗时、重试或未知计量说明", chars=1800)
    log = (source / "runs/A-with-02/output/commands.log").read_text()
    failure_at = log.index("Traceback")
    add("runs/A-with-02/output/commands.log", "保留有Skill首次超限断言失败及真实重试上下文", start=max(0, failure_at-300), chars=1800)
    add("runs/B-with-02/output/report.md", "B磨损率定义、跨阶段比较限制及摘要正文数值冲突", marker="## 4.", chars=2300)
    add("runs/C-with-02/coordinator-status.json", "C用量限制中断与缺失记录；这是主代理说明", chars=10000)
    add("history/interrupted-20261023/failure-status.json", "早期四次尝试失败、原始临时日志丢失的完整披露", chars=10000)
    add("evaluation/A-pilot-assessment.csv", "A双方同标准初核及A28不可评估理由；未测出增益", chars=10000)
    add("evaluation/B-pilot-assessment.csv", "B预设16项的非盲AI初核", chars=10000)
    add("evaluation/C-partial-assessment.csv", "C仅针对保存文本的边界检查，不代表完成运行", chars=10000)
    return rows


def run_official(resources, script, args, log):
    result = subprocess.run([sys.executable, str(resources / script), *map(str, args)],
                            capture_output=True, text=True, cwd=resources)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise ValueError("Official tool failed; draft retained for inspection: " + str(log))
    return json.loads(result.stdout)


def build(resources, output):
    resources = resources.resolve()
    lock = read_json(BASE / "official-resources-lock.json")
    verify_resources(resources, lock)
    freeze = verify_artifacts()
    output = reserve_output(output)
    source = output / "submission"
    source.mkdir()
    # Only pre-registered input/Skill/reference paths and named artifacts are copied.
    for name in freeze:
        if name.startswith("skills/shidi/"):
            target = "skill/" + name.removeprefix("skills/shidi/")
        else:
            target = str(Path(name).relative_to(BASE.relative_to(REPO)))
        copy_file(REPO / name, source / target)
    for name in ("A-pilot-assessment.csv", "B-pilot-assessment.csv", "C-partial-assessment.csv"):
        copy_file(BASE / "evaluation" / name, source / "evaluation" / name)
    for rid in RUNS:
        origin = BASE / "pilots" / rid
        index = read_json(origin / "archive-index.json")
        for name in index["sha256"]:
            if not name.startswith(("input/", "skill/")):
                copy_file(origin / name, source / "runs" / rid / name)
        copy_file(origin / "archive-index.json", source / "runs" / rid / "archive-index.json")
        if rid == "C-with-02":
            copy_file(origin / "coordinator-status.json", source / "runs" / rid / "coordinator-status.json")
    for name in ("failure-status.json", "B-input-reading-copy.md"):
        copy_file(BASE / "pilots/interrupted-20261023" / name, source / "history/interrupted-20261023" / name)
    for name in ("ready-freeze.json", "pilot-freeze.json", "pilot-dispatch.json", "PROTOCOL.md", "official-resources-lock.json"):
        copy_file(BASE / name, source / name)
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        copy_file(REPO / name, source / name)
    copy_file(BASE / "submission-readme.md", source / "README.md")
    report = (BASE / "pilot-report.md").read_text(encoding="utf-8")
    report = report.replace("pilots/interrupted-20261023/", "history/interrupted-20261023/").replace("pilots/", "runs/")
    report = ("# 作品草稿：证据记录尚未齐备\n\n本包用于结构校验和内容审阅，尚不可声明正式提交就绪。原始输出按字节保留；"
              "平台完整相关会话导出缺失，早期四次尝试的原始临时日志无法恢复，C第二次运行中断。"
              "缺口见 manifest.json 的 submission_readiness 和 README。结构检查不能消除这些事实。\n\n" + report)
    (source / "report.md").write_text(report, encoding="utf-8")
    manifest = make_manifest(resources)
    write_json(source / "manifest.json", manifest)
    selections = make_selections(source)
    write_json(output / "selections.json", selections)
    original = output / "original-submission.zip"
    deterministic_zip(source, original)
    final = output / "deliverables/submission.zip"
    run_official(resources, "make_review.py", ["--archive", original, "--selections", output / "selections.json", "--out", final, "--track", "read"], output / "make-review-result.json")
    check = run_official(resources, "check_submission.py", ["--archive", final, "--track", "read"], output / "official-check.json")
    with zipfile.ZipFile(final) as z:
        for rid in RUNS:
            for name in ("report.md", "evidence.csv", "commands.log"):
                rel = f"runs/{rid}/output/{name}"
                if z.read("submission/" + rel) != (BASE / "pilots" / rid / "output" / name).read_bytes():
                    raise ValueError("Packaged original differs from archive: " + rel)
    status = {"status": "draft-evidence-incomplete", "ready_to_submit": False,
              "archive_sha256": sha(final), "archive_bytes": final.stat().st_size,
              "official_structure_check": check, "rules_version": lock["rules_version"],
              "source_outputs_preserved_byte_for_byte": True,
              "gaps": manifest["submission_readiness"]["gaps"], "platform_trace_supplied": False,
              "submit_helper_run": False, "uploaded": False, "attempt_id": None, "score": None}
    write_json(output / "draft-status.json", status)
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", required=True, type=Path, help="Unmodified, complete pinned official resources directory")
    parser.add_argument("--out", required=True, type=Path, help="New directory outside the repository; never overwritten")
    args = parser.parse_args()
    try:
        result = build(args.resources, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "needs_revision", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
