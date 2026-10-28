import csv
import hashlib
import importlib.util
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
for base in (p for p in (ROOT / "skills/shidi", ROOT / "skills/shidi/modes/pro", ROOT / "skills/shidi/modes/flash") if (p / "references/data-extraction-schema.md").is_file()):
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
    def test_public_templates_are_role_only_placeholders(self):
        for path in PUBLIC_FORMULATION_FILES:
            if path.name != "formulation_properties.csv" or not path.is_file():
                continue
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({r["component"] for r in rows}, {"matrix", "filler", "additive_a", "additive_b"})
            self.assertTrue(all(r["role"] == r["component"] and r["material"] == "example-system" for r in rows))
            self.assertTrue(all(r["value_type"] == "exploratory" and r["value"] == "not-reported" for r in rows))
            self.assertTrue(all(r["doi"] == "not-reported" for r in rows))

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
                (base / relative).read_bytes()
                for base in (ROOT / "skills/shidi", ROOT / "skills/shidi/modes/pro", ROOT / "skills/shidi/modes/flash")
                if (base / relative).is_file()
            ]
            self.assertTrue(contents)
            self.assertTrue(all(value == contents[0] for value in contents))


if __name__ == "__main__":
    unittest.main()
