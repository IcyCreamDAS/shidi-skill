"""Discovery runs must preserve matched prompts and hide evaluation profiles."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1] / "competitions/bohrium-reading-2026-10/discovery-v1"
spec = importlib.util.spec_from_file_location("discovery_prepare", BASE / "prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class DiscoveryPreparationTests(unittest.TestCase):
    def test_both_arms_match_without_profile_or_gold_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "with", Path(tmp) / "without"
            x, y = (prepare.prepare("dev-peek", arm, out, "freeze-patched.json")
                    for arm, out in (("with", a), ("without", b)))
            self.assertEqual(x["task_sha256"], y["task_sha256"])
            self.assertIn("PEEK", (a / "PROMPT.md").read_text(encoding="utf-8"))
            self.assertTrue((a / "skill/SKILL.md").is_file())
            skill_text = (prepare.REPO / "skills/shidi/SKILL.md").read_text(encoding="utf-8")
            self.assertIn(skill_text, (a / "PROMPT.md").read_text(encoding="utf-8"))
            self.assertFalse((b / "skill").exists())
            for root in (a, b):
                self.assertFalse((root / "evaluation").exists())
                self.assertNotIn("已有玻纤增强 PEEK 实验室小试条件", (root / "PROMPT.md").read_text(encoding="utf-8"))
                self.assertEqual(list((root / "output").iterdir()), [])
            self.assertIsNone(y["cost"])
            for state in (x, y):
                self.assertEqual(state["required_model"], "kimi-code/kimi-for-coding")
                self.assertEqual(state["required_reasoning_effort"], "max")
                self.assertIsNone(state["model"])
                self.assertIsNone(state["reasoning_effort"])
                self.assertEqual(state["cost_currency"], "CNY")
            with self.assertRaises(FileExistsError):
                prepare.prepare("dev-peek", "without", b, "freeze-patched.json")

    def test_cases_are_single_sentence_research_sparks(self):
        expected = {
            "dev-peek": "能不能用化学试剂处理玻纤，让玻纤增强 PEEK 的力学性能再往上提一提？",
            "holdout-pd": "PTFE 悬浮液总是团聚沉降，能不能从颗粒表面下手把它做稳定？",
            "holdout-gre": "能不能让配体先折叠好，再引导裸 Pd(II) 组装出机械互锁笼？",
        }
        for case, sentence in expected.items():
            with self.subTest(case=case):
                lines = (BASE / "cases" / case / "task.md").read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines, ["# 用户原始请求", "", sentence])

    def test_changed_skill_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            with patch.object(prepare, "hashes", return_value={}):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    prepare.prepare("dev-peek", "with", out, "freeze-patched.json")
            self.assertFalse(out.exists())

    def test_run_folder_cannot_be_inside_repository(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            prepare.prepare("dev-peek", "without", prepare.REPO / "generated-run", "freeze-patched.json")
        self.assertFalse((prepare.REPO / "generated-run").exists())


if __name__ == "__main__":
    unittest.main()
