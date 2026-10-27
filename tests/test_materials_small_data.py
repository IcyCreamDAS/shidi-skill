import csv
import hashlib
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/materials_small_data"
PUBLIC_FORMULATION_FILES = [
    ROOT / "README.md",
    ROOT / "README_EN.md",
    EXAMPLE / "README.md",
    EXAMPLE / "make_synthetic_data.py",
    EXAMPLE / "run_demo.py",
    EXAMPLE / "priors_template.csv",
    EXAMPLE / "data/synthetic_formulations.csv",
    EXAMPLE / "requirements.txt",
]
for base in (ROOT / "skills/shidi", ROOT / "skills/shidi/modes/pro", ROOT / "skills/shidi/modes/flash"):
    PUBLIC_FORMULATION_FILES += [
        base / "references/data-extraction-schema.md",
        base / "references/templates/formulation_properties.csv",
    ]
VALUE_KEYS = [
    "filler_wt_pct", "additive_a_wt_pct", "additive_b_wt_pct", "matrix_wt_pct",
    "melt_temp_C", "tensile_MPa", "flexural_modulus_GPa", "MFR_g_per_10min",
]
EXPECTED_COLUMNS = ["project", "sample", "matrix_grade", *VALUE_KEYS, "data_source"]
EXPECTED_VALUE_SHA256 = "311e7bdb37301f8eb50256ee0bb35bac5499a0089df1d60c7317aa167670c7de"
FORMER_LABELS = [
    "5045454b", "5041454b", "50544645", "73696c616e65", "676c617373",
    "726573696e", "636f75706c696e67", "6c7562726963616e74", "7265696e666f7263656d656e74",
    "67665f77745f706374", "726573696e5f6772616465", "726573696e5f77745f706374",
    "636f75706c696e675f6167656e745f77745f706374", "6c7562726963616e745f77745f706374",
]
FORMER_LABELS = [bytes.fromhex(value).decode("ascii") for value in FORMER_LABELS]
FORMER_LABELS += ["\u73bb\u7ea4", "\u73bb\u7483\u7ea4\u7ef4", "\u5076\u8054", "\u6da6\u6ed1", "\u6811\u8102"]


def load_generator():
    path = EXAMPLE / "make_synthetic_data.py"
    spec = importlib.util.spec_from_file_location("materials_small_data_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rows():
    with (EXAMPLE / "data/synthetic_formulations.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class MaterialsSmallDataTests(unittest.TestCase):
    def test_public_formulation_files_use_roles_only(self):
        for path in PUBLIC_FORMULATION_FILES:
            text = path.read_text(encoding="utf-8").lower()
            for label in FORMER_LABELS:
                self.assertNotIn(label.lower(), text, f"{path}: {label!r}")
            self.assertIsNone(re.search(r"\bgf\b", text), path)

    def test_synthetic_values_and_generator_are_unchanged(self):
        rows = load_rows()
        self.assertEqual(list(rows[0]), EXPECTED_COLUMNS)
        self.assertEqual(len(rows), 120)
        self.assertTrue(all(row["data_source"] == "synthetic" for row in rows))
        canonical = "\n".join(",".join(row[key] for key in VALUE_KEYS) for row in rows).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), EXPECTED_VALUE_SHA256)
        generated = load_generator().build_rows()
        self.assertEqual(len(generated), len(rows))
        for stored, fresh in zip(rows, generated):
            self.assertEqual(stored["project"], fresh["project"])
            self.assertEqual(stored["sample"], fresh["sample"])
            self.assertEqual(stored["matrix_grade"], fresh["matrix_grade"])
            self.assertEqual(stored["data_source"], fresh["data_source"])
            for key in VALUE_KEYS:
                self.assertEqual(float(stored[key]), float(fresh[key]))
        load_generator().assert_closed(generated)

    def test_current_template_copies_are_identical(self):
        for relative in ("references/data-extraction-schema.md", "references/templates/formulation_properties.csv"):
            contents = [
                (ROOT / "skills/shidi" / relative).read_bytes(),
                (ROOT / "skills/shidi/modes/pro" / relative).read_bytes(),
                (ROOT / "skills/shidi/modes/flash" / relative).read_bytes(),
            ]
            self.assertEqual(contents[0], contents[1])
            self.assertEqual(contents[0], contents[2])


if __name__ == "__main__":
    unittest.main()
