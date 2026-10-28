"""File delivery must preserve originals and identify each input correctly."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/shidi/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import extract_pdfs
import render_report
import score_papers

PDF = b"%PDF-1.7\n" + b"new report\n" * 150


class FileDeliveryTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def test_existing_pdf_is_not_success_when_browser_produces_nothing(self):
        target = self.root / "report.pdf"
        old = b"%PDF-1.7\n" + b"old report\n" * 150
        target.write_bytes(old)
        for code in (0, 1):
            with self.subTest(returncode=code), mock.patch.object(
                render_report.subprocess, "run", return_value=SimpleNamespace(returncode=code, stderr=b"no PDF")
            ), redirect_stdout(io.StringIO()), mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertFalse(render_report.html_to_pdf("browser", self.root / "report.html", target))
            self.assertEqual(target.read_bytes(), old)

    def test_bad_or_failed_new_pdf_preserves_previous_report(self):
        target = self.root / "report.pdf"
        old = b"%PDF-1.7\n" + b"old report\n" * 150
        for payload, code in ((b"<html>error</html>" * 100, 0), (PDF, 1), (b"%PDF-1.7\nshort", 0)):
            target.write_bytes(old)
            def browser(cmd, **kwargs):
                path = next(arg.split("=", 1)[1] for arg in cmd if arg.startswith("--print-to-pdf="))
                Path(path).write_bytes(payload)
                return SimpleNamespace(returncode=code, stderr=b"failed")
            with self.subTest(code=code, bytes=len(payload)), mock.patch.object(
                render_report.subprocess, "run", side_effect=browser
            ), mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertFalse(render_report.html_to_pdf("browser", self.root / "report.html", target))
            self.assertEqual(target.read_bytes(), old)

    def test_fresh_pdf_replaces_previous_report_after_success(self):
        target = self.root / "report.pdf"
        target.write_bytes(b"previous report")
        def browser(cmd, **kwargs):
            self.assertEqual(target.read_bytes(), b"previous report")
            path = next(arg.split("=", 1)[1] for arg in cmd if arg.startswith("--print-to-pdf="))
            Path(path).write_bytes(PDF)
            return SimpleNamespace(returncode=0, stderr=b"")
        with mock.patch.object(render_report.subprocess, "run", side_effect=browser):
            self.assertTrue(render_report.html_to_pdf("browser", self.root / "report.html", target))
        self.assertEqual(target.read_bytes(), PDF)

    def test_pdf_timeout_preserves_previous_report(self):
        target = self.root / "report.pdf"
        target.write_bytes(b"previous report")
        with mock.patch.object(render_report.subprocess, "run", side_effect=subprocess.TimeoutExpired("browser", 90)), \
             mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertFalse(render_report.html_to_pdf("browser", self.root / "report.html", target))
        self.assertEqual(target.read_bytes(), b"previous report")

    def test_cli_returns_failure_when_pdf_generation_fails(self):
        source = self.root / "report.md"
        source.write_text("# report\n", encoding="utf-8")
        with mock.patch.object(sys, "argv", ["render_report.py", str(source)]), \
             mock.patch.object(render_report, "md_to_html", return_value="<h1>report</h1>"), \
             mock.patch.object(render_report, "find_browser", return_value="browser"), \
             mock.patch.object(render_report, "html_to_pdf", return_value=False), redirect_stdout(io.StringIO()):
            self.assertEqual(render_report.main(), 1)

    def test_duplicate_paper_ids_are_rejected_before_ranking(self):
        weights = score_papers.SCHEMAS["v2"]
        for topic in (15, 9):
            with self.subTest(topic=topic), self.assertRaisesRegex(ValueError, "重复.*same"):
                score_papers.score_all([{"id": "same", "dimensions": weights},
                                        {"doi": "same", "dimensions": dict(weights, topic=topic)}])

    def test_markdown_does_not_drop_records_from_legacy_duplicate_ids(self):
        weights = score_papers.SCHEMAS["v2"]
        result = score_papers.score_all([{"id": "a", "dimensions": weights},
                                        {"id": "b", "dimensions": dict(weights, topic=15)}])
        result["papers"][1]["id"] = "a"
        result["ranking"] = ["a", "a"]
        rows = score_papers.format_markdown(result).splitlines()[2:]
        self.assertIn("| 100 |", rows[0])
        self.assertIn("| 85 |", rows[1])

    def extract(self, source, out, inspector, *extra):
        with mock.patch.dict(sys.modules, {"pdf_inspector": SimpleNamespace(process_pdf_bytes=inspector)}), \
             mock.patch.object(sys, "argv", ["extract_pdfs.py", str(source), "--out", str(out), *extra]), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(extract_pdfs.main(), 0)

    @staticmethod
    def inspect(data):
        return SimpleNamespace(pdf_type="text_based", markdown=data.decode(), pages_needing_ocr=[],
                               pages_with_tables=[], confidence=1.0, has_encoding_issues=False, processing_time_ms=1)

    def test_same_named_pdfs_keep_separate_outputs_even_with_force(self):
        source, out = self.root / "pdfs", self.root / "text"
        for name in ("a", "b"):
            path = source / name / "paper.pdf"
            path.parent.mkdir(parents=True)
            path.write_bytes(name.encode())
        inspector = mock.Mock(side_effect=self.inspect)
        self.extract(source, out, inspector)
        self.extract(source, out, inspector, "--force")
        self.assertEqual(inspector.call_count, 4)
        for name in ("a", "b"):
            self.assertEqual((out / name / "paper.md").read_text(encoding="utf-8"), name)
            meta = json.loads((out / name / "paper.meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["source"], name + "/paper.pdf")

    def test_cache_refreshes_changed_input_and_missing_markdown(self):
        source, out = self.root / "paper.pdf", self.root / "text"
        source.write_bytes(b"first")
        inspector = mock.Mock(side_effect=self.inspect)
        self.extract(source, out, inspector)
        self.extract(source, out, inspector)
        self.assertEqual(inspector.call_count, 1)
        source.write_bytes(b"second")
        self.extract(source, out, inspector)
        self.assertEqual(inspector.call_count, 2)
        self.assertEqual((out / "paper.md").read_text(encoding="utf-8"), "second")
        meta = json.loads((out / "paper.meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["source_sha256"], hashlib.sha256(b"second").hexdigest())
        (out / "paper.md").unlink()
        self.extract(source, out, inspector)
        self.assertEqual(inspector.call_count, 3)

    def test_separate_inputs_cannot_silently_overwrite_shared_output(self):
        first, second, out = self.root / "a/paper.pdf", self.root / "b/paper.pdf", self.root / "text"
        first.parent.mkdir(); second.parent.mkdir()
        first.write_bytes(b"first"); second.write_bytes(b"second")
        self.extract(first, out, self.inspect)
        with mock.patch.dict(sys.modules, {"pdf_inspector": SimpleNamespace(process_pdf_bytes=self.inspect)}), \
             mock.patch.object(sys, "argv", ["extract_pdfs.py", str(second), "--out", str(out)]), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(extract_pdfs.main(), 1)
        self.assertEqual((out / "paper.md").read_text(encoding="utf-8"), "first")
        self.extract(second, out, self.inspect, "--force")
        self.assertEqual((out / "paper.md").read_text(encoding="utf-8"), "second")

    def test_legacy_cache_without_source_hash_is_rebuilt(self):
        source, out = self.root / "paper.pdf", self.root / "text"
        source.write_bytes(b"current")
        out.mkdir()
        (out / "paper.meta.json").write_text('{"source":"paper.pdf","markdown_written":true}', encoding="utf-8")
        (out / "paper.md").write_text("stale", encoding="utf-8")
        inspector = mock.Mock(side_effect=self.inspect)
        self.extract(source, out, inspector)
        self.assertEqual(inspector.call_count, 1)
        self.assertEqual((out / "paper.md").read_text(encoding="utf-8"), "current")

    def test_textless_new_input_does_not_leave_stale_markdown(self):
        source, out = self.root / "paper.pdf", self.root / "text"
        source.write_bytes(b"first")
        self.extract(source, out, self.inspect)
        source.write_bytes(b"")
        self.extract(source, out, self.inspect)
        self.assertFalse((out / "paper.md").exists())
        meta = json.loads((out / "paper.meta.json").read_text(encoding="utf-8"))
        self.assertFalse(meta["markdown_written"])

    def test_released_mode_scripts_match_the_tested_entrypoints(self):
        for mode in ("pro", "flash"):
            for name in ("render_report.py", "score_papers.py", "extract_pdfs.py"):
                self.assertEqual((ROOT / "skills/shidi/modes" / mode / "scripts" / name).read_bytes(),
                                 (SCRIPTS / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
