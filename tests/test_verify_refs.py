import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "shidi" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import unittest

import verify_refs


class ExtractDoisTest(unittest.TestCase):
    def test_bare_and_url_doi(self):
        text = "See 10.1021/acs.joc.0c01234 and https://doi.org/10.1002/anie.202001234."
        self.assertEqual(
            verify_refs.extract_dois(text),
            ["10.1002/anie.202001234", "10.1021/acs.joc.0c01234"],
        )

    def test_html_entities_stripped(self):
        text = "doi: 10.1016/j.polymer.2020.122456&nbsp; (open access)"
        self.assertEqual(verify_refs.extract_dois(text), ["10.1016/j.polymer.2020.122456"])

    def test_no_doi(self):
        self.assertEqual(verify_refs.extract_dois("no identifiers here"), [])

    def test_trailing_parenthesis_balance(self):
        text = "see (10.1038/s41586-020-2649-2)"
        self.assertEqual(verify_refs.extract_dois(text), ["10.1038/s41586-020-2649-2"])


class QuoteDoiPathTest(unittest.TestCase):
    def test_reserved_characters_encoded(self):
        self.assertEqual(verify_refs.quote_doi_path("10.1234/a(b)"), "10.1234/a%28b%29")

    def test_plain_doi_unchanged(self):
        self.assertEqual(verify_refs.quote_doi_path("10.1021/acs.joc.0c01234"), "10.1021/acs.joc.0c01234")


class StylePassTest(unittest.TestCase):
    def test_clean_text_passes(self):
        text = "# Title\n\n## Method\n\nShort sentence.\n\n## Result\n\nAnother one."
        self.assertTrue(verify_refs.style_pass(text)["ok"])

    def test_em_dash_spam_flagged(self):
        text = "word " * 200 + "dash — " * 12
        codes = {issue["code"] for issue in verify_refs.style_pass(text)["issues"]}
        self.assertIn("EMDASH", codes)

    def test_honest_framing_flagged(self):
        codes = {i["code"] for i in verify_refs.style_pass("The honest answer is no.")["issues"]}
        self.assertIn("HONEST", codes)

    def test_flat_structure_flagged(self):
        text = "\n".join(f"## Section {i}" for i in range(8))
        codes = {i["code"] for i in verify_refs.style_pass(text)["issues"]}
        self.assertIn("FLATSTRUCT", codes)


if __name__ == "__main__":
    unittest.main()
