#!/usr/bin/env python3
"""Generate a SYNTHETIC formulation-property table for a PAEK/PEEK-style study.

EVERY NUMBER IN THE OUTPUT IS INVENTED. This script exists so the workflow
(grouped validation, GP uncertainty, constrained candidate search) can be
demonstrated on data whose ground truth is known, without touching any real
industrial formulation. Do not cite these values as material properties.

The recipes satisfy the mass-fraction closure constraint: glass fibre +
coupling agent + lubricant + resin sum to 100 wt% in every row (resin is the
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
# Per-project offsets mimic different fibre lots / test labs / operators.
PROJECT_OFFSET = {"P01": -3.2, "P02": 2.1, "P03": 0.4, "P04": 5.8, "P05": -1.6, "P06": 3.0}
RESIN = ("A", "B", "C")  # low / medium / high viscosity resin grades
COUPLING_RANGE = (0.2, 1.2)
LUBRICANT_RANGE = (0.1, 0.8)
MELT_RANGE = (345.0, 378.0)
CLOSURE_TOLERANCE = 0.5  # wt% (rounding noise only)

FIELDS = [
    "project",
    "sample",
    "resin_grade",
    "gf_wt_pct",
    "coupling_agent_wt_pct",
    "lubricant_wt_pct",
    "resin_wt_pct",
    "melt_temp_C",
    "tensile_MPa",
    "flexural_modulus_GPa",
    "MFR_g_per_10min",
    "data_source",
]


def resin_effect(grade: str) -> float:
    return {"A": 4.0, "B": 0.0, "C": -5.5}[grade]


def true_tensile(gf: float, coupling: float, melt: float, grade: str, project: str = "P03") -> float:
    """Deterministic part of the synthetic ground truth (no noise)."""
    base = 92.0 + 2.05 * gf - 0.0175 * gf * gf
    base += resin_effect(grade) + 9.5 * coupling - 0.02 * (melt - 360.0) ** 2
    return base + PROJECT_OFFSET.get(project, 0.0)


def true_modulus(gf: float, coupling: float, grade: str, project: str = "P03") -> float:
    base = 3.4 + 0.088 * gf + 0.15 * resin_effect(grade) + 0.35 * coupling
    return base + 0.10 * PROJECT_OFFSET.get(project, 0.0)


def true_mfr(gf: float, lubricant: float, melt: float, grade: str, project: str = "P03") -> float:
    grade_shift = {"A": 4.0, "B": 0.0, "C": -5.0}[grade]
    base = 38.0 - 0.42 * gf + 5.5 * lubricant + grade_shift + 0.12 * (melt - 360.0)
    return base + 0.20 * PROJECT_OFFSET.get(project, 0.0)


def closure_gap(row) -> float:
    """|sum of mass fractions - 100| for one row."""
    total = (
        float(row["gf_wt_pct"])
        + float(row["coupling_agent_wt_pct"])
        + float(row["lubricant_wt_pct"])
        + float(row["resin_wt_pct"])
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
        gf_low = 10.0 + 2.0 * project_index
        for i in range(n):
            gf = round(gf_low + 30.0 * i / (n - 1), 1)
            coupling = round(rng.uniform(*COUPLING_RANGE), 2)
            lubricant = round(rng.uniform(*LUBRICANT_RANGE), 2)
            resin = round(100.0 - gf - coupling - lubricant, 2)
            if resin <= 0:
                raise ValueError(f"invalid synthetic recipe: resin={resin}")
            melt = rng.uniform(*MELT_RANGE)
            grade = RESIN[rng.randrange(len(RESIN))]
            tensile = true_tensile(gf, coupling, melt, grade, project) + rng.gauss(0.0, 2.2)
            modulus = true_modulus(gf, coupling, grade, project) + rng.gauss(0.0, 0.14)
            mfr = true_mfr(gf, lubricant, melt, grade, project) + rng.gauss(0.0, 1.4)
            rows.append(
                {
                    "project": project,
                    "sample": f"S{i + 1:02d}",
                    "resin_grade": grade,
                    "gf_wt_pct": gf,
                    "coupling_agent_wt_pct": coupling,
                    "lubricant_wt_pct": lubricant,
                    "resin_wt_pct": resin,
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
