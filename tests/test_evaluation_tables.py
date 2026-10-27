"""Published numerical data must be portable and reproduce the stated scores."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / "examples/pro-flash-evaluation"
spec = importlib.util.spec_from_file_location("evaluation_tables", ROOT / "build_tables.py")
tables = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tables)


class EvaluationTableTests(unittest.TestCase):
    def test_all_published_csvs_contain_numeric_records_and_reproduce_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for case in tables.CASES:
                computed = tables.build_case(case, out)
                for name, count in (("chatgpt-rubric.csv", 6), ("kimi-rubric.csv", 9)):
                    with (out / case / name).open(encoding="utf-8-sig", newline="") as handle:
                        rows = list(csv.DictReader(handle))
                    self.assertEqual(len(rows), count)
                    for arm in tables.ARMS:
                        total = sum(float(row[arm]) for row in rows)
                        expected = (computed["current_chatgpt_totals"][arm] if name.startswith("chatgpt")
                                    else computed["totals"][arm]["workflow"])
                        self.assertEqual(total, expected)
                with (out / case / "usage.csv").open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual({r["arm"] for r in rows}, set(tables.ARMS))
                self.assertTrue(all(float(r["wall_seconds"]) > 0 for r in rows))

    def test_primary_scores_use_direct_chatgpt_review_not_historical_kimi_scores(self):
        expected = {"sequential-logic": [78.75, 61.25, 50.0], "damage-memory": [68.75, 67.5, 47.5]}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for case, values in expected.items():
                tables.build_case(case, out)
                with (out / case / "final-scores.csv").open(encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual([float(r["chatgpt_content_review"]) for r in rows], values)
                self.assertNotIn("Kimi 复评", (out / case / "chatgpt-rubric.md").read_text(encoding="utf-8"))

    def test_workflow_plot_axes_derive_from_scores_instead_of_hand_copied_values(self):
        data = tables.compute(tables.read_json(ROOT / "damage-memory/evaluation.json"))
        self.assertEqual(data["axes"]["without"]["workflow"]["证据可靠与分层"], 75)
        self.assertEqual(data["axes"]["flash"]["workflow"]["综合与失效边界"], 87.5)
        self.assertEqual(data["totals"]["pro"], {"depth": 92, "workflow": 91.25, "aggregate": 90})


if __name__ == "__main__":
    unittest.main()
