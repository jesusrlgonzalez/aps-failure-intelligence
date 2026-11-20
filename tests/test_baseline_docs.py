"""Published logistic-regression comparator: historical value kept, processor range documented consistently."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "03_baseline.md").read_text(encoding="utf-8")
RANGE = "49,550–52,950"


def _n(text):
    return int(text.replace(",", ""))


def _baseline():
    return json.loads((ROOT / "reports" / "baseline" / "baseline.json").read_text())["logistic_regression"]


def test_historical_result_is_kept():
    assert _baseline()["nested_cost"] == 52100
    assert _baseline()["nested_confusion"]["fp"] == 1660


def test_processor_table_brackets_the_published_value():
    sec = DOC.split("## Reproducibility across processors")[1]
    rows = re.findall(r"^\| (.+?) \| ([\d,]+) \| ([\d,]+) \|$", sec, re.MULTILINE)
    costs = {name: _n(c) for name, c, _ in rows}
    assert costs["Published"] == _baseline()["nested_cost"]
    observed = [c for name, c in costs.items() if name != "Published"]
    lo, hi = (_n(x) for x in RANGE.split("–"))
    assert (min(observed), max(observed)) == (lo, hi)
    assert lo <= costs["Published"] <= hi
    assert f"**Observed range: {RANGE.replace('–', ' to ')}.**" in sec


def test_range_never_reaches_the_selected_model():
    cands = json.loads((ROOT / "reports" / "candidates" / "candidates.json").read_text())
    best = min(v["nested_cost"] for k, v in cands.items() if k != "logistic_regression")
    assert best == 34600 and best < _n(RANGE.split("–")[0])


@pytest.mark.parametrize("path", ["README.md", "README.es.md", "docs/04_candidates.md", "docs/PROJECT_STATE.md"])
def test_every_mention_of_52100_carries_the_range(path):
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        if "52,100" in line:
            assert RANGE in line or "¹" in line, line
    if path == "docs/04_candidates.md":
        assert f"¹ Historical result; {RANGE}" in (ROOT / path).read_text(encoding="utf-8")
