#!/usr/bin/env python3
"""Generate a SYNTHETIC formulation-property table for a role-based study.

EVERY NUMBER IN THE OUTPUT IS INVENTED. This script exists so the workflow
(grouped validation, GP uncertainty, constrained candidate search) can be
demonstrated on data whose ground truth is known, without touching any real
industrial formulation. Do not cite these values as material properties.

The recipes satisfy the mass-fraction closure constraint: filler +
additive_a + additive_b + matrix sum to 100 wt% in every row (matrix is the
remainder). This is checked by assert_closed() and by run_demo.py.

Usage:
    python make_synthetic_data.py            # write data/synthetic_formulations.csv
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / "data" / "synthetic_formulations.csv"
SEED = 20261021

PROJECTS = ("P01", "P02", "P03", "P04", "P05", "P06")
# Per-project offsets mimic different filler lots / test labs / operators.
PROJECT_OFFSET = {"P01": -3.2, "P02": 2.1, "P03": 0.4, "P04": 5.8, "P05": -1.6, "P06": 3.0}
MATRIX = ("A", "B", "C")  # low / medium / high viscosity matrix grades
ADDITIVE_A_RANGE = (0.2, 1.2)
ADDITIVE_B_RANGE = (0.1, 0.8)
MELT_RANGE = (345.0, 378.0)
CLOSURE_TOLERANCE = 0.5  # wt% (rounding noise only)

FIELDS = [
    "project",
    "sample",
    "matrix_grade",
    "filler_wt_pct",
    "additive_a_wt_pct",
    "additive_b_wt_pct",
    "matrix_wt_pct",
    "melt_temp_C",
    "tensile_MPa",
    "flexural_modulus_GPa",
    "MFR_g_per_10min",
    "data_source",
]


def matrix_effect(grade: str) -> float:
    return {"A": 4.0, "B": 0.0, "C": -5.5}[grade]


def true_tensile(filler: float, additive_a: float, melt: float, grade: str, project: str = "P03") -> float:
    """Deterministic part of the synthetic ground truth (no noise)."""
    base = 92.0 + 2.05 * filler - 0.0175 * filler * filler
    base += matrix_effect(grade) + 9.5 * additive_a - 0.02 * (melt - 360.0) ** 2
    return base + PROJECT_OFFSET.get(project, 0.0)


def true_modulus(filler: float, additive_a: float, grade: str, project: str = "P03") -> float:
    base = 3.4 + 0.088 * filler + 0.15 * matrix_effect(grade) + 0.35 * additive_a
    return base + 0.10 * PROJECT_OFFSET.get(project, 0.0)


def true_mfr(filler: float, additive_b: float, melt: float, grade: str, project: str = "P03") -> float:
    grade_shift = {"A": 4.0, "B": 0.0, "C": -5.0}[grade]
    base = 38.0 - 0.42 * filler + 5.5 * additive_b + grade_shift + 0.12 * (melt - 360.0)
    return base + 0.20 * PROJECT_OFFSET.get(project, 0.0)


def closure_gap(row) -> float:
    """|sum of mass fractions - 100| for one row."""
    total = (
        float(row["filler_wt_pct"])
        + float(row["additive_a_wt_pct"])
        + float(row["additive_b_wt_pct"])
        + float(row["matrix_wt_pct"])
    )
    return abs(total - 100.0)


def assert_closed(rows, tolerance: float = CLOSURE_TOLERANCE) -> None:
    """Raise if any row violates the mass-fraction closure constraint."""
    bad = [row for row in rows if closure_gap(row) > tolerance]
    if bad:
        sample = bad[0]
        raise ValueError(
            f"{len(bad)} row(s) violate mass-fraction closure; first: "
            f"{sample.get('project')}/{sample.get('sample')} gap={closure_gap(sample):.3f}"
        )


def build_rows(seed: int = SEED) -> list:
    rng = random.Random(seed)
    rows = []
    for project_index, project in enumerate(PROJECTS):
        n = 20
        filler_low = 10.0 + 2.0 * project_index
        for i in range(n):
            filler = round(filler_low + 30.0 * i / (n - 1), 1)
            additive_a = round(rng.uniform(*ADDITIVE_A_RANGE), 2)
            additive_b = round(rng.uniform(*ADDITIVE_B_RANGE), 2)
            matrix = round(100.0 - filler - additive_a - additive_b, 2)
            if matrix <= 0:
                raise ValueError(f"invalid synthetic recipe: matrix={matrix}")
            melt = rng.uniform(*MELT_RANGE)
            grade = MATRIX[rng.randrange(len(MATRIX))]
            tensile = true_tensile(filler, additive_a, melt, grade, project) + rng.gauss(0.0, 2.2)
            modulus = true_modulus(filler, additive_a, grade, project) + rng.gauss(0.0, 0.14)
            mfr = true_mfr(filler, additive_b, melt, grade, project) + rng.gauss(0.0, 1.4)
            rows.append(
                {
                    "project": project,
                    "sample": f"S{i + 1:02d}",
                    "matrix_grade": grade,
                    "filler_wt_pct": filler,
                    "additive_a_wt_pct": additive_a,
                    "additive_b_wt_pct": additive_b,
                    "matrix_wt_pct": matrix,
                    "melt_temp_C": round(melt, 1),
                    "tensile_MPa": round(max(tensile, 5.0), 2),
                    "flexural_modulus_GPa": round(max(modulus, 0.5), 3),
                    "MFR_g_per_10min": round(max(mfr, 0.5), 2),
                    "data_source": "synthetic",
                }
            )
    assert_closed(rows)
    return rows


def write_csv(rows, path=DATA_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    rows = build_rows()
    path = write_csv(rows)
    print(f"synthetic rows: {len(rows)} -> {path}")
    print("REMINDER: all values are synthetic; never cite them as real material data.")


if __name__ == "__main__":
    main()
