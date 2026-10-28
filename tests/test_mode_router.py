"""Pro/Flash routing and instruction texts stay stable across helper fixes."""
import hashlib
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
ROUTER = REPO / "skills/shidi/SKILL.md"
EXPECTED = {
    "pro": "51e04a4e853668e6619a824afcd9820531ea7ab267ceba944f9d54d5d65e0eed",
    "flash": "f5b3a4e97e69a48f6d0f1dd99c56f62aa29094f370ba69df40ee7054dcfc01d2",
}


class ModeRouterTests(unittest.TestCase):
    def test_default_and_explicit_routes(self):
        text = ROUTER.read_text(encoding="utf-8")
        self.assertIn("未专门提到“详细”“快速”“pro”或“flash”", text)
        self.assertIn("**Pro（默认）**：`modes/pro/SKILL.md`", text)
        self.assertIn("“师弟，帮我详细调研一下 XXX”", text)
        self.assertIn("“师弟，请你用 pro 模式给我调研一下 XXX”", text)
        self.assertIn("“师弟，帮我快速调研一下 XXX”", text)
        self.assertIn("“师弟，请你用 flash 模式给我调研一下 XXX”", text)
        self.assertIn("`modes/flash/SKILL.md`", text)

    def test_mode_instruction_hashes_and_bundle_files(self):
        for mode, expected in EXPECTED.items():
            root = REPO / "skills/shidi/modes" / mode
            files = [p for p in root.rglob("*") if p.is_file()]
            self.assertEqual(len(files), 18)
            self.assertEqual(hashlib.sha256((root / "SKILL.md").read_bytes()).hexdigest(), expected)
            for name in ("references/paper-reading.md", "scripts/fetch_pdfs.py", "scripts/verify_refs.py"):
                self.assertTrue((root / name).is_file())

    def test_readme_documents_single_download_and_default_pro(self):
        for name in ("README.md", "README_EN.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertIn("pro 模式", text)
            self.assertIn("flash 模式", text)
            self.assertIn("**Pro", text)
            self.assertIn("**One download" if name.endswith("_EN.md") else "**一次下载", text)


if __name__ == "__main__":
    unittest.main()
