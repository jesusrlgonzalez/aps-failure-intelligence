"""Piloto P01 (Nivel A): criterios de aceptación C1-C7 sobre la capa operativa sintética."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from aps_intel import pilot_p01 as p

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "pilots" / "P01"


@pytest.fixture(scope="module")
def runs():
    return {sc.id: p.operate(sc) for sc in p.SCENARIOS}


def test_c1_every_manifest_rule_is_detected_or_corrected():
    rec = p.check_reconciliation()
    assert all(rec[f"D{i}"] for i in range(1, 8)), rec
    assert rec["filas_validas"] == rec["esperado"]


def test_manifest_covers_all_rules_and_keeps_the_original():
    truth = p.truth_history()
    raw, log = p.inject(truth, p.Imperfections(), seed=21, pending_from=p.HIST_WEEKS - p.PENDING_WEEKS)
    assert {r["regla"] for r in log} == {f"D{i}" for i in range(1, 8)}
    assert all(r["filas"] > 0 for r in log)
    assert truth.equals(p.truth_history())  # la inyección no altera la fuente original
    assert len(raw) == len(truth) + next(r["filas"] for r in log if r["regla"] == "D1")


def test_c2_rule_uses_only_closed_outcomes_before_operation(runs):
    pending_start = p._monday(p.HIST_WEEKS - p.PENDING_WEEKS)
    for r in runs.values():
        assert r["entrenamiento"]["fecha"].max() < pending_start
        assert r["historial"]["resultado_pendiente"] > 0


def test_c3_weekly_list_never_exceeds_workshop_capacity(runs):
    for r in runs.values():
        assert r["semanas"]["revisiones_lista"].le(r["escenario"].capacidad).all()
        assert r["decisiones"].groupby("semana")["decision"].apply(lambda d: (d == "revisar").sum()).le(r["escenario"].capacidad).all()


def test_c6_limits_suspend_and_unknown_types_are_never_auto_decided(runs):
    w = runs["S3"]["semanas"].set_index("semana")
    assert w.loc[8, "suspendida"] and "sin puntaje" in w.loc[8, "motivo_suspension"]      # captura caída
    assert w.loc[w["motivo_suspension"] == "ALERTA", "suspendida"].all()
    unknown = runs["S3"]["decisiones"].query("tipo_alerta == @p.UNKNOWN_TYPE")
    assert len(unknown) == 6 and unknown["decision"].eq("revision_humana").all()
    # Observado y reportado como reserva: el monitor suspende 2 de las 3 semanas con cambio de firmware.
    assert w.loc[w["deriva_inyectada"], "suspendida"].sum() == 2


def test_c7_every_decision_is_traceable(runs):
    dec = pd.concat([r["decisiones"] for r in runs.values()])
    cols = ["escenario", "semana", "id_alerta", "unidad", "tipo_alerta", "decision", "motivo", "regla"]
    assert dec[cols].notna().all().all()
    assert set(dec["decision"]) <= {"revisar", "no_revisar", "revision_humana"}
    assert dec.groupby("escenario")["regla"].nunique().eq(1).all()


def test_committed_outputs_match_evidence_hashes():
    ev = json.loads((OUT / "evidence.json").read_text(encoding="utf-8"))
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()  # noqa: E731
    for name, h in ev["salidas"].items():
        assert sha(OUT / name) == h, name
    for path, h in ev["codigo"].items():
        assert sha(ROOT / path) == h, path
    assert all(ev["criterios"].values())


def test_results_report_quotes_the_generated_numbers():
    res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    text = (ROOT / "docs" / "pilots" / "P01" / "03_resultados.md").read_text(encoding="utf-8")
    for sc in ("S1", "S2", "S3"):
        r = res["escenarios"][sc]["resumen"]
        for key in ("costo_sistema", "costo_actual", "costo_simple", "ahorro_neto", "ahorro_lo", "ahorro_hi"):
            assert f"{r[key]:,.0f}" in text, (sc, key)
