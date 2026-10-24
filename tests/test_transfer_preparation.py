"""Matched new-task inputs and actual command evidence must stay inspectable."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1] / "competitions/bohrium-reading-2026-10/transfer-v1"


def module(name):
    spec = importlib.util.spec_from_file_location(name, BASE / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prepare = module("prepare")
recorder = module("record_command")


class TransferPreparationTests(unittest.TestCase):
    def test_both_arms_receive_same_inputs_without_gold_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "with", Path(tmp) / "without"
            x, y = prepare.prepare("with", a), prepare.prepare("without", b)
            for key in ("input_sha256", "task_sha256", "criteria_sha256", "recorder_sha256"):
                self.assertEqual(x[key], y[key])
            self.assertEqual(len(list((a / "input").glob("*.xml"))), 3)
            self.assertTrue((a / "skill/SKILL.md").is_file())
            self.assertFalse((b / "skill").exists())
            for root in (a, b):
                self.assertFalse((root / "evaluation").exists())
                self.assertFalse((root / "freeze.json").exists())
                self.assertEqual(list((root / "output").iterdir()), [])
            self.assertIsNone(y["native_conversation_export"])
            with self.assertRaises(FileExistsError):
                prepare.prepare("without", b)

    def test_real_failure_and_retry_streams_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = "printf 'partial\\n'; printf 'failure\\n' >&2; exit 7"
            result = recorder.execute(root, command)
            self.assertEqual(result, (7, "partial\n", "failure\n"))
            self.assertEqual(recorder.execute(root, "printf 'retry done\\n'")[0], 0)
            rows = [json.loads(x) for x in (root / "output/commands.jsonl").read_text().splitlines()]
            self.assertEqual(rows[0]["command"], command)
            self.assertEqual(rows[1]["returncode"], 7)
            self.assertEqual(rows[1]["stderr"], "failure\n")
            self.assertEqual(rows[3]["stdout"], "retry done\n")
            self.assertFalse(rows[0]["native_model_telemetry"])

    def test_budget_prevents_additional_command_execution(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(recorder, "MAX_CALLS", 1):
            root = Path(tmp)
            recorder.execute(root, "printf 'first\\n'")
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                recorder.execute(root, "touch should-not-exist")
            self.assertFalse((root / "should-not-exist").exists())

    def test_shell_pipeline_does_not_hide_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = recorder.execute(Path(tmp), "false | cat")
            self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
