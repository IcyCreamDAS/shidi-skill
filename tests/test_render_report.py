import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "shidi" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import render_report


class BrowserDiscoveryTest(unittest.TestCase):
    def test_env_override_comes_first(self):
        with mock.patch.dict(os.environ, {"SHIDI_BROWSER": "/opt/custom/chrome"}):
            self.assertEqual(next(render_report.browser_candidates()), "/opt/custom/chrome")

    def test_timeout_exception_is_the_real_one(self):
        # 回归守卫:旧代码写了不存在的 subprocess.TimeoutExpiredError
        source = Path(render_report.__file__).read_text(encoding="utf-8")
        self.assertNotIn("TimeoutExpiredError", source)
        self.assertTrue(hasattr(subprocess, "TimeoutExpired"))


class MissingMarkdownTest(unittest.TestCase):
    def test_missing_markdown_raises_actionable_error(self):
        with mock.patch.dict(sys.modules, {"markdown": None}):
            with self.assertRaises(RuntimeError) as ctx:
                render_report.md_to_html("# hi")
        self.assertIn("pip install markdown", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
