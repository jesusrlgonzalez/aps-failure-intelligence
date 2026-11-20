"""APS-02: sensitivity to the cost of a check; thresholds chosen only on training out-of-fold scores."""
import copy
import json

import numpy as np
import pytest

from aps_intel import sensitivity as sv
from aps_intel.cost import cost_optimal_threshold
from aps_intel.data import ROOT


@pytest.fixture(scope="module")
def scores():
    return sv.load_scores(ROOT)


@pytest.fixture(scope="module")
def result():
    return sv.run(ROOT, write=False)


def by_factor(result, f):
    return next(s for s in result["scenarios"] if s["factor"] == f)


def test_factor_one_reproduces_the_official_decision(result, scores):
    *_, frozen = scores
    sc = by_factor(result, 1.0)
    assert sc["threshold_reoptimized"] == pytest.approx(frozen, abs=1e-10)  # OOF scores stored with 10 decimals
    official = sc["test"]["fixed_official_threshold"]
    assert (official["cost"], official["fp"], official["fn"], official["tp"]) == (11540, 354, 16, 359)
    assert sc["test"]["reoptimized_on_oof"] == official


def test_cost_is_recomputed_from_the_confusion_matrix(result):
    for sc in result["scenarios"]:
        for part in ("development", "test"):
            for m in sc[part].values():
                assert m["cost"] == pytest.approx(sc["cost_check"] * m["fp"] + sc["cost_missed_failure"] * m["fn"])


def test_dearer_checks_never_lower_the_threshold_or_raise_the_load(result):
    sc = result["scenarios"]
    assert [s["factor"] for s in sc] == sorted(s["factor"] for s in sc)
    thresholds = [s["threshold_reoptimized"] for s in sc]
    loads = [s["development"]["reoptimized_on_oof"]["checks_per_1000"] for s in sc]
    assert thresholds == sorted(thresholds) and loads == sorted(loads, reverse=True)


def test_reoptimised_policy_is_best_on_development_by_construction(result):
    for sc in result["scenarios"]:
        dev = sc["development"]
        assert dev["reoptimized_on_oof"]["cost"] <= min(m["cost"] for m in dev.values())


def test_flag_none_and_flag_all_are_exact_references(result, scores):
    y_dev, _, y_test, _, _ = scores
    for sc in result["scenarios"]:
        assert sc["test"]["flag_none"]["cost"] == sc["cost_missed_failure"] * y_test.sum()
        assert sc["test"]["flag_all"]["cost"] == pytest.approx(sc["cost_check"] * (len(y_test) - y_test.sum()))


def test_capacity_threshold_is_fixed_on_development_and_respected(result):
    for sc in result["scenarios"]:
        for cap in sc["capacity"]:
            if cap["binding"]:
                assert cap["development"]["checks_per_1000"] <= cap["capacity_per_1000"] + 0.05


def test_run_is_deterministic_and_matches_the_stored_report(result):
    assert sv.run(ROOT, write=False) == result
    stored = json.loads((ROOT / sv.OUT / "sensitivity.json").read_text(encoding="utf-8"))
    assert stored == json.loads(json.dumps(result))


# Adversarial checks: the guard must catch a threshold chosen on the test set and any currency label.
def test_guard_rejects_a_threshold_chosen_on_the_test_set(result, scores):
    y_dev, s_dev, y_test, s_test, _ = scores
    tampered = copy.deepcopy(result)
    sc = by_factor(tampered, 2.0)
    sc["threshold_reoptimized"] = cost_optimal_threshold(y_test, s_test, sc["cost_check"], sc["cost_missed_failure"])
    assert sc["threshold_reoptimized"] != by_factor(result, 2.0)["threshold_reoptimized"]
    with pytest.raises(AssertionError, match="not chosen on development"):
        sv.check_no_test_selection(tampered, y_dev, s_dev)


def test_guard_rejects_a_best_policy_picked_on_the_test_set(result, scores):
    y_dev, s_dev, *_ = scores
    tampered = copy.deepcopy(result)
    tampered["scenarios"][0]["best_policy_on_development"] = "fixed_official_threshold"
    with pytest.raises(AssertionError, match="not selected on development"):
        sv.check_no_test_selection(tampered, y_dev, s_dev)


@pytest.mark.parametrize("label", ["MXN", "$"])
def test_guard_rejects_currency(result, scores, label):
    y_dev, s_dev, *_ = scores
    tampered = copy.deepcopy(result)
    tampered["units"] = f"{label} saved"
    with pytest.raises(AssertionError, match="never currency"):
        sv.check_no_test_selection(tampered, y_dev, s_dev)


def test_choose_threshold_never_sees_test_labels(monkeypatch, scores):
    """Every call to the selector must receive the development arrays, never the test arrays."""
    y_dev, s_dev, y_test, s_test, _ = scores
    seen = []
    real = sv.choose_threshold
    monkeypatch.setattr(sv, "choose_threshold", lambda y, s, *a: seen.append(len(y)) or real(y, s, *a))
    sv.run(ROOT, write=False)
    assert seen and set(seen) == {len(y_dev)} and len(y_dev) != len(y_test)
    assert np.isfinite(s_test).all()


def test_best_policy_is_chosen_from_development_metrics_only(monkeypatch, result):
    """The policy selector must receive each scenario's development metrics, never the test metrics."""
    seen = []
    real = sv.choose_best_policy
    monkeypatch.setattr(sv, "choose_best_policy", lambda m: seen.append(m) or real(m))
    sv.run(ROOT, write=False)
    assert seen == [sc["development"] for sc in result["scenarios"]]


@pytest.mark.parametrize("readme", ["README.md", "README.es.md"])
def test_readme_table_matches_the_report(readme):
    """Every row of the README sensitivity table must equal the stored report."""
    text = (ROOT / readme).read_text(encoding="utf-8")
    stored = json.loads((ROOT / sv.OUT / "sensitivity.json").read_text(encoding="utf-8"))
    for sc in stored["scenarios"]:
        m = sc["test"]["reoptimized_on_oof"]
        cells = [f"{sc['threshold_reoptimized']:.5f}", f"{m['checks_per_1000']:.1f}", f"{m['fp']}", f"{m['fn']}",
                 f"{m['cost']:,.0f}", f"{sc['test_saving_vs_flag_none_pct']:.1f} %"]
        row = [ln for ln in text.splitlines() if ln.startswith("|") and f"(×{sc['factor']:g})" in ln
               or (sc["factor"] == 1.0 and ln.startswith("| **10 (o"))]
        assert len(row) == 1, (readme, sc["factor"])
        for c in cells:
            assert c in row[0].replace("**", ""), (readme, sc["factor"], c)
