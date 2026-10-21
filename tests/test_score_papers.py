import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "shidi" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import score_papers


def dims_v1(topic=30, method=18, journal=12, network=4, application=8, archive=6):
    return {"topic": topic, "method": method, "journal": journal,
            "network": network, "application": application, "archive": archive}


def dims_v2(topic=30, method=18, data=12, journal=8, network=2, application=8, archive=6):
    return {"topic": topic, "method": method, "data": data, "journal": journal,
            "network": network, "application": application, "archive": archive}


class ScoreRulesTest(unittest.TestCase):
    def test_caps_dimension_and_recomputes_total(self):
        result = score_papers.score_all([{"id": "a", "dimensions": dims_v1(topic=36)}], schema="v1")
        paper = result["papers"][0]
        self.assertEqual(paper["dimensions"]["topic"], 35)
        self.assertEqual(paper["total"], 35 + 18 + 12 + 4 + 8 + 6)
        self.assertTrue(any("超过上限" in item for item in result["warnings"]))

    def test_strict_rejects_over_cap(self):
        with self.assertRaises(ValueError):
            score_papers.score_all([{"id": "a", "dimensions": dims_v2(topic=31)}], schema="v2", strict=True)

    def test_topic_veto(self):
        result = score_papers.score_all([{"id": "a", "dimensions": dims_v2(topic=9)}], schema="v2")
        self.assertTrue(result["papers"][0]["vetoed"])
        self.assertEqual(result["ranking"], [])

    def test_ranking_order(self):
        data = [
            {"id": "low", "dimensions": dims_v2(topic=20)},
            {"id": "high", "dimensions": dims_v2(topic=30)},
        ]
        result = score_papers.score_all(data, schema="v2")
        self.assertEqual(result["ranking"], ["high", "low"])
        self.assertEqual(result["papers"][1]["rank"], 1)

    def test_schema_weights_sum_to_100(self):
        for weights in score_papers.SCHEMAS.values():
            self.assertEqual(sum(weights.values()), 100)


class ValidationTest(unittest.TestCase):
    def test_missing_dimension_raises(self):
        broken = dims_v2()
        del broken["data"]
        with self.assertRaises(ValueError):
            score_papers.score_all([{"id": "a", "dimensions": broken}], schema="v2")

    def test_unknown_dimension_raises(self):
        broken = dims_v2()
        broken["noise"] = 1
        with self.assertRaises(ValueError):
            score_papers.score_all([{"id": "a", "dimensions": broken}], schema="v2")

    def test_unknown_schema_raises(self):
        with self.assertRaises(ValueError):
            score_papers.score_all([{"id": "a", "dimensions": dims_v2()}], schema="v9")

    def test_integer_scores_required(self):
        broken = dims_v2()
        broken["method"] = 12.5
        with self.assertRaises(ValueError):
            score_papers.score_all([{"id": "a", "dimensions": broken}], schema="v2")

    def test_markdown_contains_rows(self):
        result = score_papers.score_all([{"id": "a", "dimensions": dims_v2()}], schema="v2")
        table = score_papers.format_markdown(result)
        self.assertIn("| rank | id |", table)
        self.assertIn("| 1 | a |", table)


if __name__ == "__main__":
    unittest.main()
