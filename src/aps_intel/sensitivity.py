"""Sensitivity of the workshop decision to the cost of an unnecessary check (python -B -m aps_intel.sensitivity).

Reads only stored scores: training out-of-fold (OOF) scores, used as development data, and the
scores of the official test set, whose single final evaluation was already consumed. Every
threshold and every "best policy" is chosen on the OOF scores; the test set only reports the
consequences of policies fixed beforehand. No model is refitted.

Costs are IDA 2016 challenge cost units (10 per unnecessary check, 500 per missed failure),
not currency and not a saving measured at a company. Only the cost of a check is varied; the
cost of a missed failure stays at 500.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from aps_intel.cost import COST_FN, COST_FP, confusion, cost_optimal_threshold
from aps_intel.data import ROOT

OUT = Path("reports/sensitivity")
UNITS = "IDA 2016 challenge cost units (not currency; not a saving measured at a company)"
FACTORS = (0.8, 1.0, 1.2, 1.5, 2.0, 3.0)   # multiplier on the cost of an unnecessary check
CAPACITIES = (20, 30, 45)                   # illustrative workshop capacity, checks per 1,000 trucks
POLICIES = ("flag_none", "flag_all", "fixed_official_threshold", "reoptimized_on_oof")
BOOT, SEED = 2000, 42


def load_scores(root: Path = ROOT):
    root = Path(root)
    oof = pd.read_csv(root / "reports/analysis/oof_scores.csv")
    test = pd.read_csv(root / "reports/analysis/holdout_scored.csv")
    execution = json.loads((root / "reports/final/execution.json").read_text(encoding="utf-8"))
    if execution["status"] != "CONSUMED_FINAL_EVALUATION":
        raise RuntimeError("The final evaluation has not been consumed; sensitivity never opens the test set.")
    return (oof["label"].to_numpy(), oof["score"].to_numpy(), test["label"].to_numpy(), test["score"].to_numpy(),
            float(execution["threshold"]))


def choose_threshold(y_dev, s_dev, cost_fp: float, cost_fn: float = COST_FN) -> float:
    """The only place a threshold is chosen. It must receive development (OOF) data only."""
    return cost_optimal_threshold(y_dev, s_dev, cost_fp, cost_fn)


def choose_best_policy(development: dict) -> str:
    """The only place the best policy is chosen. It must receive development (OOF) metrics only."""
    return min(POLICIES, key=lambda p: (development[p]["cost"], POLICIES.index(p)))


def _metrics(y, flag, cost_fp, cost_fn) -> dict:
    c = confusion(y, flag)
    return dict(cost=round(cost_fp * c["fp"] + cost_fn * c["fn"], 2), checks_per_1000=round(1000 * flag.mean(), 2),
                recall=round(c["tp"] / max(1, y.sum()), 4), **c)


def _flags(s, policy, threshold, frozen):
    if policy == "flag_none":
        return np.zeros(len(s), dtype=bool)
    if policy == "flag_all":
        return np.ones(len(s), dtype=bool)
    return s >= (frozen if policy == "fixed_official_threshold" else threshold)


def _bootstrap_diff(y, flag_a, flag_b, cost_fp, cost_fn, n=BOOT, seed=SEED) -> list[float]:
    """95 % interval of cost(a) − cost(b) on the test set, resampling trucks."""
    rng = np.random.default_rng(seed)
    per_a = np.where(flag_a & (y == 0), cost_fp, 0) + np.where(~flag_a & (y == 1), cost_fn, 0)
    per_b = np.where(flag_b & (y == 0), cost_fp, 0) + np.where(~flag_b & (y == 1), cost_fn, 0)
    d = per_a - per_b
    sums = np.array([d[rng.integers(0, len(d), len(d))].sum() for _ in range(n)])
    return [round(float(np.percentile(sums, 2.5)), 1), round(float(np.percentile(sums, 97.5)), 1)]


def _capacity(y_dev, s_dev, y_test, s_test, k_per_1000, cost_fp, cost_fn, needed_per_1000) -> dict:
    """If the workshop cannot absorb the re-optimised load, check the top-k scores; k fixed on OOF."""
    if needed_per_1000 <= k_per_1000:
        return dict(capacity_per_1000=k_per_1000, binding=False)
    t = float(np.quantile(s_dev, 1 - k_per_1000 / 1000))
    return dict(capacity_per_1000=k_per_1000, binding=True, threshold=t,
                development=_metrics(y_dev, s_dev >= t, cost_fp, cost_fn),
                test=_metrics(y_test, s_test >= t, cost_fp, cost_fn))


def scenario(factor, y_dev, s_dev, y_test, s_test, frozen) -> dict:
    cost_fp, cost_fn = COST_FP * factor, COST_FN
    t = choose_threshold(y_dev, s_dev, cost_fp, cost_fn)
    dev = {p: _metrics(y_dev, _flags(s_dev, p, t, frozen), cost_fp, cost_fn) for p in POLICIES}
    test = {p: _metrics(y_test, _flags(s_test, p, t, frozen), cost_fp, cost_fn) for p in POLICIES}
    best_dev = choose_best_policy(dev)
    re_f, fx_f, no_f = (_flags(s_test, p, t, frozen) for p in ("reoptimized_on_oof", "fixed_official_threshold",
                                                                "flag_none"))
    return dict(
        factor=factor, cost_check=cost_fp, cost_missed_failure=cost_fn, ratio_missed_to_check=round(cost_fn / cost_fp, 2),
        threshold_reoptimized=t, threshold_fixed=frozen, best_policy_on_development=best_dev,
        development=dev, test=test,
        test_saving_vs_flag_none_pct=round(100 * (1 - test["reoptimized_on_oof"]["cost"] / test["flag_none"]["cost"]), 1),
        test_diff_reoptimized_minus_fixed_95=_bootstrap_diff(y_test, re_f, fx_f, cost_fp, cost_fn),
        test_diff_reoptimized_minus_none_95=_bootstrap_diff(y_test, re_f, no_f, cost_fp, cost_fn),
        capacity=[_capacity(y_dev, s_dev, y_test, s_test, k, cost_fp, cost_fn,
                            dev["reoptimized_on_oof"]["checks_per_1000"]) for k in CAPACITIES])


def break_even_factor_fixed(y_dev, s_dev, frozen) -> float:
    """Check-cost multiplier at which the fixed official threshold costs as much as checking nobody (OOF)."""
    c = confusion(y_dev, s_dev >= frozen)
    return round(COST_FN * c["tp"] / (COST_FP * c["fp"]), 2) if c["fp"] else float("inf")


def run(root: Path = ROOT, write: bool = True) -> dict:
    y_dev, s_dev, y_test, s_test, frozen = load_scores(root)
    result = dict(
        units=UNITS,
        scope=("Only the cost of an unnecessary check varies; thresholds and the best policy are chosen on training "
               "out-of-fold scores; the official test set (already evaluated once) only reports consequences. "
               "Capacities are illustrative assumptions."),
        n_development=int(len(y_dev)), n_test=int(len(y_test)),
        scenarios=[scenario(f, y_dev, s_dev, y_test, s_test, frozen) for f in FACTORS],
        break_even_factor_fixed_threshold=break_even_factor_fixed(y_dev, s_dev, frozen))
    check_no_test_selection(result, y_dev, s_dev)
    if write:
        (Path(root) / OUT).mkdir(parents=True, exist_ok=True)
        (Path(root) / OUT / "sensitivity.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def check_no_test_selection(result: dict, y_dev, s_dev) -> None:
    """Guard: every reported threshold must be the one chosen on development data, and units must stay abstract."""
    if result.get("units") != UNITS or "MXN" in json.dumps(result) or "$" in json.dumps(result):
        raise AssertionError("Sensitivity results must be in challenge cost units, never currency.")
    for sc in result["scenarios"]:
        expected = choose_threshold(y_dev, s_dev, sc["cost_check"], sc["cost_missed_failure"])
        if not np.isclose(sc["threshold_reoptimized"], expected, rtol=0, atol=0):
            raise AssertionError(f"Threshold for factor {sc['factor']} was not chosen on development data.")
        dev = sc["development"]
        if sc["best_policy_on_development"] != min(POLICIES, key=lambda p: (dev[p]["cost"], POLICIES.index(p))):  # independent
            raise AssertionError(f"Best policy for factor {sc['factor']} was not selected on development data.")


def main() -> None:
    r = run()
    print(f"{'factor':>6} {'threshold':>10} {'checks/1000':>11} {'FP':>4} {'FN':>3} {'cost':>9} {'vs none':>8} best(dev)")
    for sc in r["scenarios"]:
        t = sc["test"]["reoptimized_on_oof"]
        print(f"{sc['factor']:>6} {sc['threshold_reoptimized']:>10.6f} {t['checks_per_1000']:>11} {t['fp']:>4} "
              f"{t['fn']:>3} {t['cost']:>9} {sc['test_saving_vs_flag_none_pct']:>7}% {sc['best_policy_on_development']}")
    print(f"Fixed threshold breaks even with 'check nobody' at a check-cost factor of "
          f"{r['break_even_factor_fixed_threshold']} (OOF). Units: {r['units']}")


if __name__ == "__main__":
    main()
