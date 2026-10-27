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
                        key = "depth" if name.startswith("chatgpt") else "workflow"
                        self.assertEqual(total, computed["totals"][arm][key])
                with (out / case / "usage.csv").open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual({r["arm"] for r in rows}, set(tables.ARMS))
                self.assertTrue(all(float(r["wall_seconds"]) > 0 for r in rows))

    def test_workflow_plot_axes_derive_from_scores_instead_of_hand_copied_values(self):
        data = tables.compute(tables.read_json(ROOT / "damage-memory/evaluation.json"))
        self.assertEqual(data["axes"]["without"]["workflow"]["证据可靠与分层"], 75)
        self.assertEqual(data["axes"]["flash"]["workflow"]["综合与失效边界"], 87.5)
        self.assertEqual(data["totals"]["pro"], {"depth": 92, "workflow": 91.25, "aggregate": 90})


if __name__ == "__main__":
    unittest.main()
