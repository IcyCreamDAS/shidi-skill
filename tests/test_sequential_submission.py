"""Sequential-logic effect gate and evidence export checks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
RUN = Path("C:/AGENTDATA/kimicode/shidi-sequential-logic-runs/b28eb4e-k28max-01")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("sequential_submission", REPO / "competitions/bohrium-reading-2026-10/sequential-logic-v1/build_submission.py")
exporter = load("sequential_export", RUN / "export_visible.py")


class SequentialSubmissionTests(unittest.TestCase):
    def test_effect_gate_requires_twenty_point_gain_and_no_with_serious_error(self):
        self.assertTrue(builder.effect_is_obvious(88.75, 67.5))
        self.assertFalse(builder.effect_is_obvious(85, 67.5))
        self.assertFalse(builder.effect_is_obvious(95, 60, True))
        self.assertFalse(builder.effect_is_obvious(74.9, 0))

    def test_unsafe_paths_are_rejected(self):
        for name in ("../secret", "a\\b", "C:/secret", "a//b", "/absolute"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.safe_relative(name)

    def test_visible_export_excludes_host_prompt_and_reasoning(self):
        rows = [
            {"type": "profile.bind", "systemPrompt": "private host memory"},
            {"type": "context.append_message", "time": 1,
             "message": {"role": "user", "content": [{"type": "text", "text": "task"}]}},
            {"type": "context.append_loop_event", "time": 2,
             "event": {"type": "content.part", "part": {"type": "think", "think": "hidden"}}},
            {"type": "context.append_loop_event", "time": 3,
             "event": {"type": "content.part", "part": {"type": "text", "text": "visible"}}},
            {"type": "context.append_loop_event", "time": 4,
             "event": {"type": "tool.call", "toolCallId": "t1", "name": "Read", "args": {"path": "x"}}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "wire.jsonl", Path(tmp) / "export.jsonl"
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            result = exporter.export(source, target)
            exported = target.read_text(encoding="utf-8")
            self.assertEqual(result["records"], 3)
            self.assertIn("visible", exported)
            self.assertIn("tool.call", exported)
            self.assertNotIn("private host memory", exported)
            self.assertNotIn("hidden", exported)

    def test_selection_offsets_are_unicode_with_byte_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "record.txt").write_text("前言\n证据🧪" + "x" * 3000, encoding="utf-8")
            row = builder.source_selection(source, "record.txt", "test", marker="证据", chars=10000)
            self.assertEqual(row["start"], 3)
            selected = (source / "record.txt").read_text(encoding="utf-8")[row["start"]:row["end"]]
            self.assertLessEqual(len(selected.encode("utf-8")), 8192)


if __name__ == "__main__":
    unittest.main()
