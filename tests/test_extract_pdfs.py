import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "shidi" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import unittest

import extract_pdfs


class ClassifyTest(unittest.TestCase):
    def test_text_variants(self):
        for value in ("text_based", "textbased", "TEXT_BASED"):
            self.assertEqual(extract_pdfs.classify(value), extract_pdfs.KIND_TEXT)

    def test_vision_variants(self):
        for value in ("scanned", "image_based", "imagebased"):
            self.assertEqual(extract_pdfs.classify(value), extract_pdfs.KIND_VISION)

    def test_mixed_and_unknown_fall_back_to_mixed(self):
        for value in ("mixed", "", None, "weird-format"):
            self.assertEqual(extract_pdfs.classify(value), extract_pdfs.KIND_MIXED)


if __name__ == "__main__":
    unittest.main()
