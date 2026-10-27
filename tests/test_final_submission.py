"""Final two-case packaging and score consistency checks."""
import importlib.util
import json
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PATH = REPO / "competitions/bohrium-reading-2026-10/final-submission/build_submission.py"
spec = importlib.util.spec_from_file_location("final_submission", PATH)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class FinalSubmissionTests(unittest.TestCase):
    def test_two_cases_have_pro_and_without_runs(self):
        self.assertEqual(set(builder.CASES), {"A", "B"})
        for config in builder.CASES.values():
            for condition in ("pro", "without"):
                run = config["run_root"] / config[condition]
                self.assertTrue((run / "output" / builder.report_for(config, condition)).is_file())
                self.assertTrue((run / "output" / builder.references_for(config, condition)).is_file())
                self.assertTrue((run / "run.json").is_file())
                self.assertTrue((run / "trace-export.jsonl").is_file())

    def test_without_report_and_reference_paths(self):
        self.assertEqual(builder.report_for(builder.CASES["A"], "without"), "先光照后遇湿_化学顺序门控报告.md")
        self.assertEqual(builder.references_for(builder.CASES["A"], "without"), "references_文献清单.md")
        self.assertEqual(builder.report_for(builder.CASES["B"], "without"), "report.md")
        self.assertEqual(builder.references_for(builder.CASES["B"], "without"), "literature.md")

    def test_historical_kimi_score_sums_are_preserved(self):
        expected = {
            "A": [93, 88.75, 89.25, 58, 67.5, 58.5],
            "B": [92, 91.25, 90.0, 70, 81.25, 71.5],
        }
        for case_id, case in (("A", "sequential-logic"), ("B", "damage-memory")):
            data = json.loads((builder.EXAMPLES / case / "historical-computed-scores.json").read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "historical_kimi_ratings_not_current_chatgpt_review")
            for arm, scores in (("pro", expected[case_id][:3]), ("without", expected[case_id][3:])):
                self.assertEqual([data["totals"][arm][key] for key in ("depth", "workflow", "aggregate")], scores)


if __name__ == "__main__":
    unittest.main()
