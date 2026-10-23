"""Prevent answer leakage and false completion in reading-run preparation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
PATH = REPO / "competitions/bohrium-reading-2026-10/prepare_run.py"
spec = importlib.util.spec_from_file_location("prepare_reading_run", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
reader_spec = importlib.util.spec_from_file_location("readable_xml", PATH.with_name("readable_xml.py"))
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)


class ReadingPreparationTests(unittest.TestCase):
    def test_matched_inputs_and_baseline_has_no_skill_or_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            with_dir, without_dir = Path(tmp) / "with", Path(tmp) / "without"
            a = module.prepare("A", "with", with_dir)
            b = module.prepare("A", "without", without_dir)
            for key in ("input_sha256", "task_sha256", "criteria_sha256", "limits"):
                self.assertEqual(a[key], b[key])
            self.assertTrue((with_dir / "skill/SKILL.md").is_file())
            self.assertFalse((without_dir / "skill").exists())
            for root in (with_dir, without_dir):
                self.assertFalse((root / "evaluation").exists())
                self.assertEqual(list((root / "output").iterdir()), [])
                self.assertIsNone(json.loads((root / "run.json").read_text())["actual_session_trace"])

    def test_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):
                module.prepare("A", "with", tmp)

    def test_missing_material_case_contains_only_abstract(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            module.prepare("C", "with", out)
            self.assertEqual([p.name for p in (out / "input").iterdir()], ["abstract.md"])

    def test_rejects_repo_output_and_unknown_case(self):
        with self.assertRaises(ValueError):
            module.prepare("A", "with", REPO / "unsafe-run")
        with self.assertRaises(ValueError):
            module.prepare("D", "with", "/tmp/unused-shidi-run")

    def test_keeps_external_floats_and_volume_units(self):
        xml = '''<article><front><article-meta><article-title>Example</article-title></article-meta></front>
<body><sec><title>Methods</title><p>See Table 1.</p></sec></body>
<floats-group><table-wrap id="t1"><label>Table 1</label><caption><p>Composition</p></caption>
<table><tr><th>PEEK (Vol.%)</th></tr><tr><td>10</td></tr></table></table-wrap>
<fig id="f1"><label>Figure 1</label><caption><p>Micrograph</p></caption></fig></floats-group></article>'''
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "paper.xml"
            source.write_text(xml)
            output = reader.render(source)
            self.assertIn("PEEK (Vol.%)", output)
            self.assertEqual(output.count("### Table 1 [t1]"), 1)
            self.assertIn("Figure 1 [f1] (caption only)", output)

    def test_does_not_duplicate_inline_table(self):
        xml = '''<article><body><sec><table-wrap id="t1"><label>Table 1</label>
<table><tr><td>value</td></tr></table></table-wrap></sec></body></article>'''
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "paper.xml"
            source.write_text(xml)
            self.assertEqual(reader.render(source).count("### Table 1 [t1]"), 1)


if __name__ == "__main__":
    unittest.main()
