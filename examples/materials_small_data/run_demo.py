#!/usr/bin/env python3
"""Small-data materials ML demo on a fully synthetic PAEK/PEEK-style dataset.

What it demonstrates
  1. grouped validation (leave-one-project-out) instead of a random split,
     so same-project sibling samples cannot inflate the score;
  2. a Gaussian-process surrogate with per-point uncertainty, plus an honest
     empirical coverage table (+/-1 sigma, +/-2 sigma) on held-out projects;
  3. constrained candidate search: maximise predicted tensile strength subject
     to P(MFR >= 8 g/10min) >= threshold, ranked by expected improvement;
  4. a simulated closed loop (propose -> synthetic oracle -> refit);
  5. explicit claim labels measured / predicted / exploratory, and the rule
     that the exploration screening range is NOT a statistical confidence interval.

Usage
    python run_demo.py             # full demo (a few seconds)
    python run_demo.py --quick     # smaller pool, one active-learning round (CI)

Outputs (git-ignored, regenerated on every run)
    outputs/report.md
    outputs/logo_metrics.csv
    outputs/calibration.csv
    outputs/candidates.csv
    outputs/active_learning.csv

All data is synthetic (see make_synthetic_data.py). This directory must never
contain real industrial formulations or measurements.
"""
from __future__ import annotations

import argparse
import csv
import math
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from make_synthetic_data import (
    DATA_FILE,
    build_rows,
    true_mfr,
    true_modulus,
    true_tensile,
    write_csv as write_synthetic,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
TARGETS = ("tensile_MPa", "flexural_modulus_GPa", "MFR_g_per_10min")
MFR_CONSTRAINT = 32.0
FEASIBILITY = 0.80
SEED = 20261021

CLAIM_LABELS = [
    ("measured", "a real observation from the dataset"),
    ("predicted", "model output with uncertainty; not verified by experiment"),
    ("exploratory", "a screening recommendation; never report it as a result"),
]

CANDIDATE_FIELDS = [
    "rank",
    "claim_label",
    "resin_grade",
    "gf_wt_pct",
    "coupling_agent_wt_pct",
    "lubricant_wt_pct",
    "melt_temp_C",
    "tensile_pred_MPa",
    "tensile_sd_MPa",
    "tensile_screening_low",
    "tensile_screening_high",
    "mfr_pred_g_per_10min",
    "mfr_sd_g_per_10min",
    "p_mfr_feasible",
    "expected_improvement",
]


def load_rows(path=DATA_FILE):
    with Path(path).open(encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def features(rows):
    matrix = []
    for row in rows:
        grade = row["resin_grade"]
        matrix.append(
            [
                float(row["gf_wt_pct"]),
                float(row["coupling_agent_wt_pct"]),
                float(row["lubricant_wt_pct"]),
                (float(row["melt_temp_C"]) - 360.0) / 20.0,
                1.0 if grade == "A" else 0.0,
                1.0 if grade == "B" else 0.0,
            ]
        )
    return np.asarray(matrix, dtype=float)


def targets(rows, name):
    return np.asarray([float(row[name]) for row in rows], dtype=float)


def make_gp(n_features):
    kernel = ConstantKernel(1.0, (1e-2, 1e3)) * RBF(np.ones(n_features), (1e-2, 1e2))
    kernel = kernel + WhiteKernel(1e-1, (1e-3, 1e1))
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("gp", GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=0)),
        ]
    )


def fit_target(rows, target):
    x = features(rows)
    model = make_gp(x.shape[1])
    model.fit(x, targets(rows, target))
    return model


def logo_validation(rows, target):
    """Leave-one-project-out: every fold holds out a whole project."""
    groups = sorted({row["project"] for row in rows})
    y_true, mu_gp, sd_gp, mu_ridge = [], [], [], []
    for group in groups:
        train = [row for row in rows if row["project"] != group]
        test = [row for row in rows if row["project"] == group]
        model = fit_target(train, target)
        mu, sd = model.predict(features(test), return_std=True)
        ridge = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
        ridge.fit(features(train), targets(train, target))
        y_true.extend(targets(test, target).tolist())
        mu_gp.extend(mu.tolist())
        sd_gp.extend(sd.tolist())
        mu_ridge.extend(ridge.predict(features(test)).tolist())
    y = np.asarray(y_true)
    mean = np.asarray(mu_gp)
    std = np.maximum(np.asarray(sd_gp), 1e-9)
    ridge_mean = np.asarray(mu_ridge)
    z = (y - mean) / std
    return {
        "target": target,
        "n_holdout": int(y.size),
        "n_groups": len(groups),
        "r2_gp": float(r2_score(y, mean)),
        "rmse_gp": float(math.sqrt(mean_squared_error(y, mean))),
        "r2_ridge": float(r2_score(y, ridge_mean)),
        "rmse_ridge": float(math.sqrt(mean_squared_error(y, ridge_mean))),
        "coverage_1s": float(np.mean(np.abs(z) <= 1.0)),
        "coverage_2s": float(np.mean(np.abs(z) <= 2.0)),
    }


def normal_cdf(value):
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def normal_pdf(value):
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def expected_improvement(mean, sd, best):
    sd = max(sd, 1e-9)
    z = (mean - best) / sd
    return (mean - best) * normal_cdf(z) + sd * normal_pdf(z)


def candidate_pool(count, rng):
    grades = ("A", "B", "C")
    pool = []
    for _ in range(count):
        pool.append(
            {
                "resin_grade": grades[int(rng.integers(0, len(grades)))],
                "gf_wt_pct": rng.uniform(10.0, 45.0),
                "coupling_agent_wt_pct": rng.uniform(0.2, 1.2),
                "lubricant_wt_pct": rng.uniform(0.1, 0.8),
                "melt_temp_C": rng.uniform(345.0, 378.0),
            }
        )
    return pool


def recommend(rows, pool, top_k=8):
    """Rank candidates by expected improvement under an MFR feasibility constraint."""
    tensile_model = fit_target(rows, "tensile_MPa")
    mfr_model = fit_target(rows, "MFR_g_per_10min")
    x_pool = features(pool)
    mu_t, sd_t = tensile_model.predict(x_pool, return_std=True)
    mu_m, sd_m = mfr_model.predict(x_pool, return_std=True)
    best = float(np.max(targets(rows, "tensile_MPa")))
    p_ok = np.asarray(
        [normal_cdf((m - MFR_CONSTRAINT) / max(float(s), 1e-9)) for m, s in zip(mu_m, sd_m)]
    )
    ei = np.asarray(
        [expected_improvement(float(m), float(s), best) for m, s in zip(mu_t, sd_t)]
    )
    picked = []
    for index in np.argsort(-ei):
        if p_ok[index] < FEASIBILITY:
            continue
        candidate = dict(pool[int(index)])
        candidate.update(
            {
                "rank": len(picked) + 1,
                "claim_label": "exploratory",
                "tensile_pred_MPa": round(float(mu_t[index]), 2),
                "tensile_sd_MPa": round(float(sd_t[index]), 2),
                "tensile_screening_low": round(float(mu_t[index] - 2.0 * sd_t[index]), 2),
                "tensile_screening_high": round(float(mu_t[index] + 2.0 * sd_t[index]), 2),
                "mfr_pred_g_per_10min": round(float(mu_m[index]), 2),
                "mfr_sd_g_per_10min": round(float(sd_m[index]), 2),
                "p_mfr_feasible": round(float(p_ok[index]), 3),
                "expected_improvement": round(float(ei[index]), 3),
                "gf_wt_pct": round(candidate["gf_wt_pct"], 1),
                "coupling_agent_wt_pct": round(candidate["coupling_agent_wt_pct"], 2),
                "lubricant_wt_pct": round(candidate["lubricant_wt_pct"], 2),
                "melt_temp_C": round(candidate["melt_temp_C"], 1),
            }
        )
        picked.append(candidate)
        if len(picked) >= top_k:
            break
    return {"picked": picked, "n_feasible": int(np.sum(p_ok >= FEASIBILITY)), "best_observed": best}


def simulate_experiment(candidate, rng):
    """Synthetic oracle: the known ground-truth generator plus measurement noise."""
    gf = float(candidate["gf_wt_pct"])
    coupling = float(candidate["coupling_agent_wt_pct"])
    lubricant = float(candidate["lubricant_wt_pct"])
    melt = float(candidate["melt_temp_C"])
    grade = candidate["resin_grade"]
    return {
        "tensile_MPa": round(max(5.0, true_tensile(gf, coupling, melt, grade) + float(rng.normal(0.0, 2.2))), 2),
        "flexural_modulus_GPa": round(max(0.5, true_modulus(gf, coupling, grade) + float(rng.normal(0.0, 0.14))), 3),
        "MFR_g_per_10min": round(max(0.5, true_mfr(gf, lubricant, melt, grade) + float(rng.normal(0.0, 1.4))), 2),
    }


def active_learning(rows, rounds, pool_size, rng):
    train = list(rows)
    history = []
    for round_no in range(1, rounds + 1):
        result = recommend(train, candidate_pool(pool_size, rng), top_k=1)
        if not result["picked"]:
            break
        candidate = result["picked"][0]
        observed = simulate_experiment(candidate, rng)
        record = {key: candidate[key] for key in (
            "resin_grade", "gf_wt_pct", "coupling_agent_wt_pct", "lubricant_wt_pct", "melt_temp_C"
        )}
        record.update(observed)
        record.update({"project": "P03", "sample": f"AL{round_no:02d}", "data_source": "simulated"})
        train.append(record)
        history.append(
            {
                "round": round_no,
                "resin_grade": candidate["resin_grade"],
                "gf_wt_pct": candidate["gf_wt_pct"],
                "pred_tensile_MPa": candidate["tensile_pred_MPa"],
                "pred_sd_MPa": candidate["tensile_sd_MPa"],
                "observed_tensile_MPa": observed["tensile_MPa"],
                "pred_mfr": candidate["mfr_pred_g_per_10min"],
                "observed_mfr": observed["MFR_g_per_10min"],
            }
        )
    return history


def write_rows(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def fmt(value, digits=2):
    return f"{value:.{digits}f}"


def build_report(rows, metrics, recommendation, history, quick):
    lines = []
    add = lines.append
    add("# Materials small-data ML demo (synthetic)")
    add("")
    add("This report is generated by run_demo.py. The dataset is synthetic by construction")
    add("(see make_synthetic_data.py); no industrial or experimental data is involved.")
    add("")
    add("## Dataset")
    add("")
    add(f"- rows: {len(rows)}; projects: {len({row['project'] for row in rows})}; "
        f"targets: {', '.join(TARGETS)}")
    add("- synthetic inputs: glass-fibre load, coupling agent, lubricant, melt temperature, resin grade")
    add("- data_source column: synthetic (asserted at startup)")
    add("")
    add("## Grouped validation (leave-one-project-out)")
    add("")
    add("| target | n | GP R2 | GP RMSE | Ridge R2 | Ridge RMSE | coverage +/-1s | coverage +/-2s |")
    add("|---|---|---|---|---|---|---|---|")
    for item in metrics:
        add(
            f"| {item['target']} | {item['n_holdout']} | {item['r2_gp']:+.2f} | {item['rmse_gp']:.3f} | "
            f"{item['r2_ridge']:+.2f} | {item['rmse_ridge']:.3f} | {item['coverage_1s']:.0%} | {item['coverage_2s']:.0%} |"
        )
    add("")
    add("Target coverage for a calibrated Gaussian is 68% (+/-1 sigma) and 95% (+/-2 sigma).")
    add("With six folds the numbers are coarse; read them as a direction, not a guarantee.")
    mean_coverage = sum(item["coverage_1s"] for item in metrics) / len(metrics)
    if mean_coverage < 0.65:
        add("")
        add(f"Average +/-1 sigma coverage is {mean_coverage:.0%}, below the 68% target: when a whole "
            "project is held out, the surrogate under-states its uncertainty. That is exactly why the "
            "exploration band below must not be read as a confidence interval.")
    else:
        add("")
        add(f"Average +/-1 sigma coverage is {mean_coverage:.0%}, close to the 68% target on this "
            "synthetic set - but only six folds are available, so still treat the band as exploratory.")
    add("")
    add("## Constrained candidate search")
    add("")
    add(f"- objective: maximise predicted tensile strength")
    add(f"- constraint: P(MFR >= {MFR_CONSTRAINT:g} g/10min) >= {FEASIBILITY:.0%}")
    add(f"- feasible candidates found: {recommendation['n_feasible']} of the random pool")
    add(f"- best observed tensile in the dataset: {recommendation['best_observed']:.1f} MPa")
    add("")
    add(f"| rank | resin | GF wt% | coupling wt% | lubricant wt% | melt C | tensile pred MPa | sd | screening range | MFR pred | P(MFR>={MFR_CONSTRAINT:g}) |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for item in recommendation["picked"]:
        add(
            f"| {item['rank']} | {item['resin_grade']} | {item['gf_wt_pct']} | {item['coupling_agent_wt_pct']} | "
            f"{item['lubricant_wt_pct']} | {item['melt_temp_C']} | {item['tensile_pred_MPa']} | {item['tensile_sd_MPa']} | "
            f"[{item['tensile_screening_low']}, {item['tensile_screening_high']}] | "
            f"{item['mfr_pred_g_per_10min']} | {item['p_mfr_feasible']:.0%} |"
        )
    add("")
    add("The screening range is mean +/- 2 sd of the surrogate. It is an exploration band,")
    add("NOT a statistical confidence interval; use the coverage table above to judge calibration.")
    add("")
    add("## Simulated closed loop (propose -> synthetic oracle -> refit)")
    add("")
    add("| round | resin | GF wt% | tensile pred | sd | tensile observed | MFR observed |")
    add("|---|---|---|---|---|---|---|")
    for item in history:
        add(
            f"| {item['round']} | {item['resin_grade']} | {item['gf_wt_pct']} | {item['pred_tensile_MPa']} | "
            f"{item['pred_sd_MPa']} | {item['observed_tensile_MPa']} | {item['observed_mfr']} |"
        )
    add("")
    add("The oracle is the same synthetic generator used to create the dataset, so the loop")
    add("validates the plumbing (proposal, uncertainty, refit), not real predictive skill.")
    add("")
    add("## Claim labels")
    add("")
    add("| label | meaning |")
    add("|---|---|")
    for label, meaning in CLAIM_LABELS:
        add(f"| {label} | {meaning} |")
    add("")
    add("Rules used in this example:")
    add("")
    add("1. Only measured values may be reported as results.")
    add("2. Predicted values always carry mean and sd; never a bare number.")
    add("3. Exploratory candidates are screening suggestions; they become predictions after")
    add("   a model check and measured values after experiments.")
    add("4. Exploration screening range != statistical confidence interval.")
    add("5. Grouped splits are mandatory when samples share a project/batch.")
    add("")
    add("## What this example does NOT claim")
    add("")
    add("- It does not demonstrate real PEEK/PAEK property prediction: the data is synthetic")
    add("  and the surfaces are simple by construction.")
    add("- The GP scores do not transfer to any real formulation dataset.")
    add("- The surrogate ranking is not proven better than an experienced engineer's DOE")
    add("  intuition; that requires a real experimental loop.")
    add("")
    add(f"Run mode: {'quick (CI)' if quick else 'full'}.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic small-data materials ML demo")
    parser.add_argument("--quick", action="store_true", help="small pool and one active-learning round")
    parser.add_argument("--regenerate", action="store_true", help="regenerate the synthetic dataset first")
    args = parser.parse_args()
    warnings.filterwarnings("ignore", category=ConvergenceWarning)

    if args.regenerate or not DATA_FILE.exists():
        write_synthetic(build_rows())
        print(f"generated synthetic dataset -> {DATA_FILE}")

    rows = load_rows()
    sources = {row.get("data_source", "") for row in rows}
    if sources != {"synthetic"}:
        raise SystemExit(f"refusing to run: expected only synthetic data, found {sorted(sources)}")

    rng = np.random.default_rng(SEED)
    pool_size = 400 if args.quick else 2000
    rounds = 1 if args.quick else 3

    metrics = []
    for target in TARGETS:
        item = logo_validation(rows, target)
        metrics.append(item)
        print(
            f"LOGO {target}: GP R2={item['r2_gp']:+.2f} RMSE={item['rmse_gp']:.3f} "
            f"(Ridge R2={item['r2_ridge']:+.2f}) coverage 1s={item['coverage_1s']:.0%}"
        )

    recommendation = recommend(rows, candidate_pool(pool_size, rng))
    history = active_learning(rows, rounds, pool_size // 2, rng)

    OUT.mkdir(parents=True, exist_ok=True)
    write_rows(OUT / "logo_metrics.csv", metrics)
    write_rows(
        OUT / "calibration.csv",
        [
            {
                "target": item["target"],
                "coverage_1sigma": round(item["coverage_1s"], 4),
                "coverage_2sigma": round(item["coverage_2s"], 4),
                "target_1sigma": 0.6827,
                "target_2sigma": 0.9545,
            }
            for item in metrics
        ],
    )
    write_rows(OUT / "candidates.csv", recommendation["picked"], CANDIDATE_FIELDS)
    write_rows(OUT / "active_learning.csv", history)
    (OUT / "report.md").write_text(
        build_report(rows, metrics, recommendation, history, args.quick), encoding="utf-8"
    )

    print()
    print(f"feasible candidates: {recommendation['n_feasible']}")
    for item in recommendation["picked"][:3]:
        print(
            f"  #{item['rank']} resin {item['resin_grade']} GF {item['gf_wt_pct']} wt% -> "
            f"tensile {item['tensile_pred_MPa']} +/- {item['tensile_sd_MPa']} MPa, "
            f"P(MFR>={MFR_CONSTRAINT:g})={item['p_mfr_feasible']:.0%}"
        )
    for item in history:
        print(
            f"  round {item['round']}: predicted {item['pred_tensile_MPa']} +/- {item['pred_sd_MPa']} MPa, "
            f"observed {item['observed_tensile_MPa']} MPa"
        )
    print()
    print(f"outputs written to {OUT}")
    print("REMINDER: synthetic data only; predictions are not material data.")


if __name__ == "__main__":
    main()
