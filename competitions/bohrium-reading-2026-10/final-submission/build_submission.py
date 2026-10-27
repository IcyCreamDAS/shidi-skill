#!/usr/bin/env python3
"""Build the two-case Pro/without final package with pinned official tools."""
import argparse
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
spec = importlib.util.spec_from_file_location("sequential_builder", REPO / "competitions/bohrium-reading-2026-10/sequential-logic-v1/build_submission.py")
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

SKILL_VERSION = "git:b28eb4e"
CASES = {
    "A": {
        "run_root": Path("C:/AGENTDATA/kimicode/shidi-sequential-logic-runs/b28eb4e-k28max-01"),
        "pro": "with", "without": "without",
        "report": "report.md", "references": "literature-list.md",
        "without_report": "先光照后遇湿_化学顺序门控报告.md",
        "without_references": "references_文献清单.md",
        "result": "RESULTS.md",
    },
    "B": {
        "run_root": Path("C:/AGENTDATA/kimicode/shidi-damage-memory-runs"),
        "pro": "pro-b28", "without": "without",
        "report": "损伤记忆涂层调研报告.md", "references": "参考文献清单.md",
        "without_report": "report.md", "without_references": "literature.md",
        "result": "RESULTS.md",
    },
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def report_for(config, condition):
    return config["report"] if condition == "pro" else config.get("without_report", config["report"])


def references_for(config, condition):
    return config["references"] if condition == "pro" else config.get("without_references", config["references"])


def make_manifest(resources):
    m = common.read_json(resources / "templates/manifest-with-bonus.json")
    m["cases"] = [case for case in m["cases"] if case["id"] in CASES]
    m["skill_version"] = SKILL_VERSION
    m["environment"] = {
        "host": "Kimi Code Desktop；独立 coder 子代理，无跨会话记忆",
        "model": "kimi-code/kimi-for-coding（K2.8 Preview），默认 max；profile.bind 已核对",
        "model_version": "K2.8 Preview；服务端精确构建号无法取得",
        "tools": ["WebSearch", "FetchURL", "Bash", "Python", "pypdf"],
        "dependencies": ["Python 3", "pypdf", "matplotlib（仅评阅绘图）"],
        "budget": "每组12分钟软墙、24查询、40页面动作、8篇核心文献；软限非平台硬停止",
        "human_steps": "主代理 K3.1 Pro 冻结协议、统一代答并独立评阅；未提供路线、论文或评分答案",
        "isolation_limit": "独立目录和会话，禁止读取/利用宿主记忆；指令边界不是OS沙箱",
        "usage_unavailable_reason": "日志无逐次人民币扣费字段；cost=null，不填0或估价",
    }
    m["materials"] = []
    for case_id, config in CASES.items():
        for name in ("task.md", "CONTEXT.md"):
            m["materials"].append({"path": f"materials/{case_id}/{name}", "case_ids": [case_id], "role": "input",
                                   "source": "用户本轮提供的合成研究探索提示；非实验数据",
                                   "version": "2026-10-26/27 frozen", "retrieved_at": "2026-10-27",
                                   "data_type": "一句话研究请求与最小共同背景",
                                   "sharing_basis": "用户授权用于本次评测与参赛"})
        for case in m["cases"]:
            if case["id"] == case_id:
                case.update(task_file=f"cases/{case_id}/task.md", acceptance_criteria_file=f"cases/{case_id}/criteria.md",
                            input_files=[f"materials/{case_id}/task.md", f"materials/{case_id}/CONTEXT.md"], reference_files=[])
    m["runs"] = []
    for case_id, config in CASES.items():
        for condition in ("pro", "without"):
            arm = config[condition]
            run = config["run_root"] / arm
            state = common.read_json(run / "run.json")
            notes = common.read_json(run / "output/run-notes.json")
            rid = f"{case_id}-{condition}"
            outputs = [f"runs/{rid}/output/{name}" for name in (report_for(config, condition), references_for(config, condition),
                                                                  "run-notes.json", "pdf-verification.json")]
            m["runs"].append({
                "id": rid, "case_id": case_id, "condition": "with_skill" if condition == "pro" else "without_skill",
                "skill_version": SKILL_VERSION if condition == "pro" else "none",
                "output_files": outputs, "primary_output_files": outputs,
                "trace_files": [f"runs/{rid}/trace-export.jsonl", f"runs/{rid}/run.json", f"runs/{rid}/visible_conversation.md"],
                "started_at": notes.get("start_utc", notes.get("started_at", notes.get("started_at_local"))),
                "duration_seconds": state["wall_time_seconds_total"], "cost": None,
                "unavailable_metadata": "精确服务端构建号和人民币扣费无法取得",
                "human_steps": ([{"role": "coordinator-as-user", "record": f"runs/{rid}/visible_conversation.md",
                                  "scope": "按冻结立场回答；未给路线或论文"}] if condition == "pro" else []),
                "result": state["status"],
                "trace_scope": "完整可见文本与工具事件；本机用户名和绝对路径已脱敏；原始wire留作者本地",
                "complete_conversation_available": True,
            })
    m["attempt_history"] = {"earlier_attempts": [], "raw_logs_available": True,
                            "reason": "A/B两个真实独立案例；问答、失败、重试均保留"}
    m["submission_readiness"] = {
        "status": "ready-for-local-official-validation", "ready_to_submit": True,
        "gaps": [],
        "limits": ["单主题单次运行，增益不可外推", "公共提示词指导是归因限制", "费用无法核验"],
        "official_structure_pass_is_not_scientific_validation": True,
    }
    return m


def make_selections(source):
    rows = []
    def add(path, purpose, **kw): rows.append(common.source_selection(source, path, purpose, **kw))
    add("report.md", "A/B方法、主要增益、用量与边界", chars=4200)
    for case_id, config in CASES.items():
        add(f"materials/{case_id}/task.md", case_id + "一句话原始输入", chars=500)
        add(f"evaluation/{case_id}/final-scores.md", case_id + "三大评分与增益", chars=1500)
        add(f"evaluation/{case_id}/usage.md", case_id + "实际用量与PDF", chars=1800)
        for condition in ("pro", "without"):
            rid = f"{case_id}-{condition}"
            add(f"runs/{rid}/output/{report_for(config, condition)}", rid + "核心结果与证据边界", chars=2300)
            add(f"runs/{rid}/output/{references_for(config, condition)}", rid + "文献清单与阅读深度", chars=1600)
            add(f"runs/{rid}/output/run-notes.json", rid + "真实运行与失败记录", chars=1600)
            add(f"runs/{rid}/output/pdf-verification.json", rid + "PDF原件与SHA-256", chars=1500)
            add(f"runs/{rid}/trace-export.jsonl", rid + "可见对话与工具轨迹开头", chars=1000)
    return rows


def build(resources, output):
    resources = resources.resolve()
    lock = common.verify_resources(resources)
    output = common.reserve_output(output)
    source = output / "submission"
    source.mkdir()
    common.copy_tree(CASES["A"]["run_root"] / "with/skill", source / "skill")
    common.copy_tree(BASE / "cases", source / "cases")
    common.copy_file(BASE / "SUBMISSION_README.md", source / "README.md")
    common.copy_file(BASE / "SUBMISSION_REPORT.md", source / "report.md")
    common.copy_file(REPO / "LICENSE", source / "LICENSE")
    common.copy_file(REPO / "THIRD_PARTY_NOTICES.md", source / "THIRD_PARTY_NOTICES.md")
    common.copy_file(REPO / "competitions/bohrium-reading-2026-10/official-resources-lock.json",
                      source / "official-resources-lock.json")
    final_root = Path("C:/AGENTDATA/kimicode/competition-final")
    for case_id, config in CASES.items():
        for name in ("task.md", "CONTEXT.md"):
            common.copy_file(config["run_root"] / config["pro"] / name, source / "materials" / case_id / name)
        for condition in ("pro", "without"):
            arm = config[condition]
            rid = f"{case_id}-{condition}"
            common.copy_tree(config["run_root"] / arm / "output", source / "runs" / rid / "output")
            for name in ("run.json", "visible_conversation.md", "trace-export.jsonl"):
                common.copy_file(config["run_root"] / arm / name, source / "runs" / rid / name)
        case_final = final_root / ("sequential-logic" if case_id == "A" else "damage-memory")
        for name in ("chatgpt-rubric.md", "chatgpt-rubric.csv", "kimi-rubric.md", "kimi-rubric.csv",
                     "final-scores.md", "final-scores.csv", "usage.md", "usage.csv",
                     "chatgpt-six-dimensions.png", "chatgpt-six-dimensions.svg",
                     "kimi-six-dimensions.png", "kimi-six-dimensions.svg",
                     "aggregate-six-dimensions.png", "aggregate-six-dimensions.svg"):
            common.copy_file(case_final / name, source / "evaluation" / case_id / name)
        common.copy_file(config["run_root"] / config["result"], source / "evaluation" / case_id / "RESULTS.md")
    common.write_json(source / "manifest.json", make_manifest(resources))
    common.write_json(output / "selections.json", make_selections(source))
    original = output / "original-submission.zip"
    common.deterministic_zip(source, original)
    final = output / "deliverables/submission.zip"
    common.run_official(resources, "make_review.py", ["--archive", original, "--selections", output / "selections.json",
                                                      "--out", final, "--track", "read"], output / "make-review-result.json")
    check = common.run_official(resources, "check_submission.py", ["--archive", final, "--track", "read"],
                                output / "official-check.json")
    status = {"status": "ready-to-submit-locally-validated", "ready_to_submit": True,
              "archive_sha256": common.sha(final), "archive_bytes": final.stat().st_size,
              "official_structure_check": check, "rules_version": lock["rules_version"],
              "limits": ["单主题单次运行，增益不可外推", "公共提示词指导是归因限制", "费用无法核验"],
              "submit_helper_run": False, "uploaded": False, "attempt_id": None, "score": None}
    common.write_json(output / "submission-status.json", status)
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.resources, args.out), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "needs_revision", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
