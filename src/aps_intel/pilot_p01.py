"""Piloto demostrativo P01 (Nivel A): triaje semanal de alertas de una flota ficticia con taller limitado.

Capa operativa sintética sobre el calibrador de alertas (``alert_intake`` + ``alert_calibrator``), que no se
modifica. No lee ni toca el conjunto oficial de Scania: sus resultados (docs/06) son la evidencia científica;
los de aquí son **resultados de escenario** de una empresa ficticia.

Flujo: exportación con errores -> conciliación con bitácora -> regla elegida solo con resultados ya cerrados ->
lista semanal con cupo estricto, revisión humana y suspensión -> costos contra la práctica actual y una regla
sencilla por tipo -> escenarios, sensibilidad y evidencia.

    PYTHONPATH=src python -B -m aps_intel.pilot_p01        # regenera reports/pilots/P01/
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from aps_intel import alert_calibrator as ac
from aps_intel import alert_intake as ai

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "pilots" / "P01"
EMPRESA = "Transportes Ficticios del Altiplano, S.A. (empresa ficticia)"
HIST_WEEKS, PENDING_WEEKS, OPS_WEEKS = 21, 4, 9   # historial, semanas con resultado aún abierto, semanas operadas
START = pd.Timestamp("2026-01-05")
B_FROM_WEEK = 10                                   # el proveedor B cambia a escala 0-1 desde esta semana
COSTO_OPERACION_SEMANA = 1_500.0                   # dos horas de analista por semana (supuesto del caso)
MAX_SIN_PUNTAJE, MAX_EXCLUIDAS = 0.20, 0.10        # compuertas de calidad de la semana
UNKNOWN_TYPE = "SPN 5246 FMI 7"

# Catálogo de nomenclatura: variantes que llegan en las exportaciones -> nombre canónico.
VARIANTS = {
    "Presión de aire baja": ["PRESION DE AIRE BAJA", "Pres. aire baja", "Low air pressure"],
    "Temperatura de refrigerante alta": ["TEMP REFRIGERANTE ALTA", "Coolant temp high"],
    "Presión de aceite baja": ["PRESION ACEITE BAJA", "Low oil pressure"],
    "Voltaje de batería bajo": ["VOLTAJE BATERIA BAJO", "Low battery voltage"],
    "Filtro de partículas saturado": ["DPF saturado", "FILTRO PARTICULAS SATURADO"],
    "Sensor ABS intermitente": ["ABS intermitente", "ABS sensor intermittent"],
    "Desgaste de balatas": ["DESGASTE BALATAS", "Brake pad wear"],
    "Falla de comunicación CAN": ["Falla CAN", "CAN communication fault"],
}


def _norm(text) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


CATALOG = {_norm(c): c for c in VARIANTS} | {_norm(v): c for c, vs in VARIANTS.items() for v in vs}


@dataclass(frozen=True)
class Imperfections:
    duplicados: float = 0.03        # D1 doble envío de la telemática
    sin_puntaje: float = 0.08       # D2 falla de captura del puntaje
    variantes: float = 0.10         # D4 nomenclatura contradictoria
    fecha_iso: float = 0.05         # D5 formatos de fecha mezclados (además 2 seriales de Excel)
    errores: int = 7                # D6 errores de integración (fecha imposible, unidad vacía, valor sí/no inválido)


@dataclass(frozen=True)
class Scenario:
    id: str
    nombre: str
    capacidad: int
    ops: Imperfections = Imperfections(errores=0)
    deriva: tuple[int, ...] = ()          # semanas operadas (1-9) con firmware que dispara alertas ABS
    sin_puntaje_semana: dict | None = None  # {semana operada: fracción} para fallas masivas de captura
    desconocidos: tuple[int, ...] = ()      # semanas operadas con un código nuevo que el catálogo no conoce
    ruido: float = 0.0                      # fracción del puntaje reemplazada por ruido (proveedor de telemática pobre)


SCENARIOS = (
    Scenario("S1", "Referencia: operación normal", 30),
    Scenario("S2", "Adversa: personal reducido a la mitad y captura degradada", 15,
             Imperfections(duplicados=0.06, sin_puntaje=0.15, variantes=0.15, errores=0)),
    Scenario("S3", "Límites: cambio de firmware, código nuevo y captura caída", 30,
             deriva=(4, 5, 6), sin_puntaje_semana={8: 0.35}, desconocidos=(2, 7)),
)


# ---------------------------------------------------------------- datos sintéticos
def _monday(week: int) -> pd.Timestamp:
    return START + pd.Timedelta(weeks=week)


def _with_ids(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.insert(0, "id_alerta", [f"{prefix}-{i:05d}" for i in range(1, len(df) + 1)])
    df["proveedor"] = np.where(df["unidad"].str[2:].astype(int) > 170, "B", "A")
    df["semana"] = ((pd.to_datetime(df["fecha"], format="%d/%m/%Y") - START).dt.days // 7).astype(int)
    return df


def _noise(df: pd.DataFrame, q: float, seed: int) -> pd.DataFrame:
    if q <= 0:
        return df
    rng = np.random.default_rng(seed)
    hit = rng.random(len(df)) < q
    df.loc[hit, "puntaje"] = rng.integers(1, 100, int(hit.sum())).astype(float)
    return df


def truth_history(seed: int = 11, ruido: float = 0.0) -> pd.DataFrame:
    """Verdad sintética del historial: limpia, con lo que se hizo (``revisada``) y lo que pasó (``falla``)."""
    return _noise(_with_ids(ai.example_data(weeks=HIST_WEEKS, seed=seed, start=str(START.date())), "H"), ruido, 5)


def truth_ops(sc: Scenario) -> pd.DataFrame:
    weeks = [ai.example_data(weeks=1, seed=500 + w, start=str(_monday(HIST_WEEKS + w).date()), drift=w + 1 in sc.deriva)
             for w in range(OPS_WEEKS)]
    df = _with_ids(pd.concat(weeks, ignore_index=True), "O")
    rng = np.random.default_rng(77)
    extra = []
    for w in sc.desconocidos:
        for _ in range(3):
            extra.append(dict(unidad=f"T-{rng.integers(101, 241)}", tipo_alerta=UNKNOWN_TYPE, puntaje=float(rng.integers(40, 90)),
                              fecha=(_monday(HIST_WEEKS + w - 1) + pd.Timedelta(days=int(rng.integers(0, 7)))).strftime("%d/%m/%Y"),
                              revisada="sí", falla="sí" if rng.random() < 0.3 else "no"))
    if extra:
        df = _with_ids(pd.concat([df.drop(columns=["id_alerta", "proveedor", "semana"]), pd.DataFrame(extra)], ignore_index=True), "O")
    return _noise(df, sc.ruido, 6)


def inject(truth: pd.DataFrame, imp: Imperfections, seed: int, pending_from: int | None = None,
           missing_by_week: dict | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Exportación tal como llega, más el manifiesto de cada modificación (ids afectados)."""
    rng = np.random.default_rng(seed)
    raw = truth.astype(object).copy()
    raw["puntaje"] = raw["puntaje"].astype(float)
    n = len(raw)
    pool = rng.permutation(n)
    pos = [0]

    def take(k: int) -> list[int]:  # índices disjuntos entre reglas
        pos[0] += k
        return [int(i) for i in pool[pos[0] - k:pos[0]]]

    log: list[dict] = []

    def rec(rid, tipo, ids, **kw):
        log.append(dict(regla=rid, tipo=tipo, ids=sorted(raw.loc[ids, "id_alerta"].tolist()), filas=len(ids), **kw))

    err = take(imp.errores)
    for k, i in enumerate(err):
        col, val = [("fecha", "31/02/2026"), ("unidad", ""), ("falla", "tal vez")][k % 3]
        if col == "falla" and "falla" not in raw:
            col, val = "fecha", "31/02/2026"
        raw.at[i, col] = val
    if err:
        rec("D6", "Errores de integración", err)

    miss = take(int(round(n * imp.sin_puntaje)))
    if missing_by_week:
        for w, frac in missing_by_week.items():
            rows = [i for i in np.flatnonzero(raw["semana"].to_numpy() == HIST_WEEKS + w - 1) if i not in miss and i not in err]
            miss += [int(i) for i in rng.choice(rows, int(round(len(rows) * frac)), replace=False)]
    raw.loc[miss, "puntaje"] = np.nan
    rec("D2", "Puntaje ausente", miss)

    b = np.flatnonzero((raw["proveedor"] == "B").to_numpy() & (raw["semana"].to_numpy() >= B_FROM_WEEK) & raw["puntaje"].notna().to_numpy())
    raw.loc[b, "puntaje"] = raw.loc[b, "puntaje"] / 100
    rec("D3", "Cambio de unidades del puntaje (proveedor B, escala 0-1)", list(b))

    var = take(int(round(n * imp.variantes)))
    var = [i for i in var if raw.at[i, "tipo_alerta"] in VARIANTS]
    for i in var:
        opts = VARIANTS[raw.at[i, "tipo_alerta"]]
        raw.at[i, "tipo_alerta"] = opts[int(rng.integers(0, len(opts)))]
    rec("D4", "Nomenclatura contradictoria", var)

    iso = take(int(round(n * imp.fecha_iso)))
    raw.loc[iso, "fecha"] = pd.to_datetime(raw.loc[iso, "fecha"], format="%d/%m/%Y").dt.strftime("%Y-%m-%d")
    ser = take(2)
    raw.loc[ser, "fecha"] = [str((pd.Timestamp(d.split("/")[2] + "-" + d.split("/")[1] + "-" + d.split("/")[0]) - pd.Timestamp("1899-12-30")).days)
                             for d in raw.loc[ser, "fecha"]]
    rec("D5", "Formatos de fecha mezclados (ISO y serial de Excel)", iso + ser)

    if pending_from is not None:
        pend = list(np.flatnonzero(raw["semana"].to_numpy() >= pending_from))
        raw.loc[pend, "falla"] = ""
        rec("D7", "Resultado aún abierto (ventana de 30 días sin cerrar)", pend)

    dup = take(int(round(n * imp.duplicados)))
    rec("D1", "Registros duplicados", dup)
    raw = pd.concat([raw, raw.loc[dup]], ignore_index=True)

    raw["puntaje"] = raw["puntaje"].map(lambda v: "" if pd.isna(v) else f"{v:g}")
    return raw.drop(columns="semana"), log


# ---------------------------------------------------------------- conciliación
def reconcile(raw: pd.DataFrame, need_outcome: bool = True) -> tuple[pd.DataFrame, dict, list]:
    """Fuente analítica conciliada. Devuelve (datos, bitácora de correcciones, avisos de validación).

    No modifica ``raw``. Las alertas de tipo desconocido se conservan con ``tipo_conocido=False``."""
    df = raw.copy()
    canon = df["tipo_alerta"].map(lambda t: CATALOG.get(_norm(t)))
    bit = dict(filas_recibidas=len(df), nomenclatura_corregida=int((canon.notna() & (canon != df["tipo_alerta"])).sum()),
               tipos_desconocidos=int(canon.isna().sum()))
    df["tipo_conocido"] = canon.notna()
    df["tipo_alerta"] = canon.fillna(df["tipo_alerta"])

    score = pd.to_numeric(df["puntaje"].astype(str).str.replace(",", "."), errors="coerce")
    dates = ai._dates(df["fecha"])
    week = ((dates - START).dt.days // 7)
    scale = (score.groupby([df["proveedor"], week]).transform("max") <= 1) & score.notna()
    df.loc[scale, "puntaje"] = (score[scale] * 100).round().map(lambda v: f"{v:g}")
    bit["puntaje_reescalado"] = int(scale.sum())

    if need_outcome:
        open_ = df["falla"].astype(str).str.strip().eq("")
        bit["resultado_pendiente"] = int(open_.sum())
        df = df[~open_]
    data, issues = ai.validate(df.drop(columns=["id_alerta"]), need_outcome=need_outcome)
    keys = df.assign(fecha=ai._dates(df["fecha"]), unidad=df["unidad"].astype(str).str.strip())
    keys = keys.drop_duplicates(["unidad", "fecha", "tipo_alerta"])[["unidad", "fecha", "tipo_alerta", "id_alerta", "proveedor", "tipo_conocido"]]
    data = data.merge(keys, on=["unidad", "fecha", "tipo_alerta"], how="left", validate="one_to_one")
    data["puntaje_imputado"] = data["id_alerta"].isin(df.loc[score.reindex(df.index).isna(), "id_alerta"]) if "puntaje" in data else False
    bit.update(filas_validas=len(data), filas_excluidas=len(df) - len(data) - _dups(df),
               duplicados_eliminados=_dups(df), sin_puntaje=float(score.isna().mean()))
    return data, bit, issues


def _dups(df: pd.DataFrame) -> int:
    k = df.assign(f=ai._dates(df["fecha"]), u=df["unidad"].astype(str).str.strip()).dropna(subset=["f"])
    k = k[k["u"] != ""]
    return int(k.duplicated(["u", "f", "tipo_alerta"]).sum())


# ---------------------------------------------------------------- operación semanal
def rule_id(rule: ac.Rule, st: ac.Settings, train: pd.DataFrame) -> str:
    key = dict(modo=rule.modo, corte=round(float(rule.corte), 6), costos=[st.costo_revision, st.costo_falla],
               capacidad=st.capacidad_semana, entrenamiento=[str(train["fecha"].min().date()), str(train["fecha"].max().date())], n=len(train))
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:12]


def _cap_fifo(flag: np.ndarray, fecha: pd.Series, cap: int) -> np.ndarray:
    """Práctica actual con cupo: se atiende por orden de llegada hasta llenar el taller."""
    order = np.argsort(fecha.to_numpy(), kind="stable")
    keep = np.zeros(len(flag), bool)
    chosen = [i for i in order if flag[i]][:cap]
    keep[chosen] = True
    return keep


def _cap_priority(priority: np.ndarray, corte: float, cap: int) -> tuple[np.ndarray, np.ndarray]:
    cand = np.flatnonzero(priority >= corte)
    cand = cand[np.argsort(-priority[cand], kind="stable")]
    top = np.zeros(len(priority), bool)
    top[cand[:cap]] = True
    over = np.zeros(len(priority), bool)
    over[cand[cap:]] = True
    return top, over


def operate(sc: Scenario, st: ac.Settings | None = None, seed: int = 11) -> dict:
    st = st or ac.Settings(capacidad_semana=sc.capacidad)
    hist_raw, hist_log = inject(truth_history(seed, sc.ruido), Imperfections(), seed=21, pending_from=HIST_WEEKS - PENDING_WEEKS)
    hist, hist_bit, _ = reconcile(hist_raw)
    train = hist[hist["tipo_conocido"]].drop(columns=["id_alerta", "proveedor", "tipo_conocido", "puntaje_imputado"])
    rule = ac.fit_rule(train, st)
    rule_s = ac.fit_rule(train.drop(columns="puntaje"), st)          # alternativa sencilla: tasa por tipo
    rid = rule_id(rule, st, train)

    truth = truth_ops(sc)
    ops_raw, ops_log = inject(truth.drop(columns=["revisada", "falla"]), sc.ops, seed=31, missing_by_week=sc.sin_puntaje_semana)
    tr = truth.set_index("id_alerta")
    rows, weeks = [], []
    for w in range(OPS_WEEKS):
        wk_raw = ops_raw[pd.to_datetime(ai._dates(ops_raw["fecha"])).sub(_monday(HIST_WEEKS + w)).dt.days.between(0, 6)]
        data, bit, _ = reconcile(wk_raw, need_outcome=False)
        data["falla"] = data["id_alerta"].map(tr["falla"]).eq("sí").to_numpy()
        data["actual"] = data["id_alerta"].map(tr["revisada"]).eq("sí").to_numpy()
        known = data["tipo_conocido"].to_numpy()
        k = data[known].reset_index(drop=True)
        u = data[~known].reset_index(drop=True)
        gate = []
        if bit["sin_puntaje"] > MAX_SIN_PUNTAJE:
            gate.append(f"{bit['sin_puntaje']:.0%} de alertas sin puntaje")
        if bit["filas_excluidas"] / max(1, bit["filas_recibidas"]) > MAX_EXCLUIDAS:
            gate.append("demasiadas filas inválidas")
        mon = None if gate or "puntaje" not in k else ac.monitor_week(k.drop(columns=["falla", "actual"]), rule)
        suspend = bool(gate) or (mon is not None and mon["estado"] == "ALERTA")
        practice = _cap_fifo(data["actual"].to_numpy(), data["fecha"], sc.capacidad)
        pr_s = rule_s.priority(k)
        simple, _ = _cap_priority(pr_s, rule_s.corte, sc.capacidad)
        if suspend:
            sys_flag = practice.copy()
            dec = np.full(len(data), "revision_humana", object)
            why = np.full(len(data), "Recomendación suspendida: " + ("; ".join(gate) if gate else "el monitor detectó un cambio"), object)
            prio = np.full(len(data), np.nan)
            if mon is not None:
                prio[known] = rule.priority(k)
        else:
            pk = rule.priority(k)
            top, over = _cap_priority(pk, rule.corte, sc.capacidad)
            sys_flag = np.zeros(len(data), bool)
            dec = np.empty(len(data), object)
            why = np.empty(len(data), object)
            prio = np.full(len(data), np.nan)
            ki, ui = np.flatnonzero(known), np.flatnonzero(~known)
            prio[ki] = pk
            sys_flag[ki] = top
            dec[ki] = np.where(top, "revisar", np.where(over, "revision_humana", "no_revisar"))
            why[ki] = np.where(top, "Prioridad sobre el corte y dentro del cupo",
                               np.where(over, "Atendible sin cupo: decide el jefe de taller (horas extra o posponer)", "Prioridad bajo el corte de costo"))
            spare = sc.capacidad - int(top.sum())
            for j, i in enumerate(ui):   # el jefe de taller usa el cupo sobrante en lo que el sistema no reconoce
                dec[i], why[i] = "revision_humana", "Tipo de alerta desconocido: el sistema no decide"
                sys_flag[i] = j < spare
        y = data["falla"].to_numpy(bool)
        cost = lambda f: float(st.costo_revision * f.sum() + st.costo_falla * (y & ~f).sum())  # noqa: E731
        weeks.append(dict(semana=w + 1, alertas=len(data), suspendida=suspend, motivo_suspension="; ".join(gate) or (mon or {}).get("estado"),
                          deriva_inyectada=w + 1 in sc.deriva, desconocidas=int((~known).sum()),
                          revisiones_sistema=int(sys_flag.sum()), revisiones_lista=int(((dec == "revisar")).sum()),
                          revision_humana=int((dec == "revision_humana").sum()),
                          costo_sistema=cost(sys_flag) + COSTO_OPERACION_SEMANA, costo_actual=cost(practice),
                          costo_simple=cost(_pad(simple, known)), fallas=int(y.sum()),
                          en_ruta_sistema=int((y & ~sys_flag).sum()), en_ruta_actual=int((y & ~practice).sum()),
                          en_ruta_simple=int((y & ~_pad(simple, known)).sum()), revisiones_actual=int(practice.sum()),
                          revisiones_simple=int(simple.sum())))
        rows.append(pd.DataFrame(dict(escenario=sc.id, semana=w + 1, id_alerta=data["id_alerta"], unidad=data["unidad"],
                                      fecha=data["fecha"].dt.strftime("%Y-%m-%d"), tipo_alerta=data["tipo_alerta"],
                                      prioridad=np.round(prio, 2), decision=dec, motivo=why, regla=rid)))
    wk = pd.DataFrame(weeks)
    return dict(escenario=sc, settings=st, regla=rule, regla_id=rid, entrenamiento=train, historial=hist_bit,
                manifiesto=dict(historial=hist_log, operacion=ops_log), semanas=wk,
                decisiones=pd.concat(rows, ignore_index=True), resumen=summary(wk, st))


def _pad(flag_known: np.ndarray, known: np.ndarray) -> np.ndarray:
    out = np.zeros(len(known), bool)
    out[np.flatnonzero(known)] = flag_known
    return out


def _boot(s: np.ndarray, seed: int, level: float, reps: int) -> tuple[float, float, str]:
    boot = s[np.random.default_rng(seed).integers(0, len(s), size=(reps, len(s)))].sum(axis=1)
    lo, hi = np.quantile(boot, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi), "conviene" if lo > 0 else ("desfavorable" if hi < 0 else "indiferente")


def summary(wk: pd.DataFrame, st: ac.Settings, level: float = 0.90, reps: int = 2000) -> dict:
    s = wk["costo_actual"].to_numpy() - wk["costo_sistema"].to_numpy()
    lo, hi, ver = _boot(s, st.semilla, level, reps)
    s2 = wk["costo_simple"].to_numpy() - wk["costo_sistema"].to_numpy()
    lo2, hi2, ver2 = _boot(s2, st.semilla, level, reps)
    out = {c: float(wk[c].sum()) for c in ("costo_sistema", "costo_actual", "costo_simple")}
    out.update({c: int(wk[c].sum()) for c in ("revisiones_sistema", "revisiones_actual", "revisiones_simple", "fallas",
                                              "en_ruta_sistema", "en_ruta_actual", "en_ruta_simple", "revision_humana")})
    out.update(ahorro_neto=float(s.sum()), ahorro_lo=float(lo), ahorro_hi=float(hi), semanas_suspendidas=int(wk["suspendida"].sum()),
               max_lista_semana=int(wk["revisiones_lista"].max()),
               veredicto=ver, ahorro_vs_simple=float(s2.sum()), vs_simple_lo=lo2, vs_simple_hi=hi2, veredicto_vs_simple=ver2)
    return out


# ---------------------------------------------------------------- criterios, sensibilidad y evidencia
def check_reconciliation(seed: int = 11) -> dict:
    """C1/C2: cada regla del manifiesto, comparada contra la verdad sintética."""
    truth = truth_history(seed)
    raw, log = inject(truth, Imperfections(), seed=21, pending_from=HIST_WEEKS - PENDING_WEEKS)
    data, bit, _ = reconcile(raw)
    ids = {r["regla"]: set(r["ids"]) for r in log}
    t = truth.set_index("id_alerta")
    d = data.set_index("id_alerta")
    closed = set(t.index[t["semana"] < HIST_WEEKS - PENDING_WEEKS])
    present = set(d.index)
    sc = d.loc[sorted(ids["D3"] & present - ids["D2"])]
    dt = d.loc[sorted(ids["D5"] & present)]
    return dict(
        D1=bool(d.index.is_unique and bit["duplicados_eliminados"] == len(ids["D1"] & present)),
        D2=bool(d.loc[sorted(ids["D2"] & present), "puntaje_imputado"].all() and not d.loc[sorted(present - ids["D2"]), "puntaje_imputado"].any()),
        D3=bool(np.allclose(sc["puntaje"].astype(float), t.loc[sc.index, "puntaje"].astype(float))),
        D4=bool(set(d["tipo_alerta"]) <= set(VARIANTS) and (d.loc[sorted(ids["D4"] & present), "tipo_alerta"] == t.loc[sorted(ids["D4"] & present), "tipo_alerta"]).all()),
        D5=bool((dt["fecha"].dt.strftime("%d/%m/%Y") == t.loc[dt.index, "fecha"]).all()),
        D6=bool(not (ids["D6"] & present)),
        D7=bool(not (ids["D7"] & present) and present <= closed),
        filas_validas=len(data), filas_verdad_cerradas=len(closed), esperado=len(closed - ids["D6"]))


def sensitivity(ratios=(2, 5, 10, 21.1, 40, 80), caps=(10, 15, 20, 30, 45, 0), ruidos=(0.0, 0.5, 1.0)) -> pd.DataFrame:
    """Costo (razón falla/revisión), capacidad y calidad del puntaje. Ahorro neto contra la práctica actual y contra la regla por tipo."""
    base = SCENARIOS[0]
    grid = [(r, c, 0.0) for r in ratios for c in caps] + [(r, 30, q) for q in ruidos if q > 0 for r in ratios]
    out = []
    for r, c, q in grid:
        st = ac.Settings(costo_falla=round(1_800 * r, 2), capacidad_semana=c)
        res = operate(replace(base, capacidad=c if c else 10_000, ruido=q), st)["resumen"]
        out.append(dict(razon_falla_revision=r, capacidad=c or "sin límite", ruido_puntaje=q,
                        vs_actual=round(res["ahorro_neto"], 2), vs_actual_lo=round(res["ahorro_lo"], 2), vs_actual_hi=round(res["ahorro_hi"], 2),
                        veredicto_vs_actual=res["veredicto"], vs_simple=round(res["ahorro_vs_simple"], 2),
                        vs_simple_lo=round(res["vs_simple_lo"], 2), vs_simple_hi=round(res["vs_simple_hi"], 2), veredicto_vs_simple=res["veredicto_vs_simple"]))
    return pd.DataFrame(out)


def acceptance(runs: dict, rec: dict) -> dict:
    s1, s2, s3 = (runs[k] for k in ("S1", "S2", "S3"))
    dec = pd.concat([r["decisiones"] for r in runs.values()])
    w3 = s3["semanas"]
    unknown = dec[dec["tipo_alerta"] == UNKNOWN_TYPE]
    must = w3["motivo_suspension"].fillna("").str.contains("sin puntaje|inválidas|ALERTA")
    return dict(
        C1=all(rec[k] for k in ("D1", "D2", "D3", "D4", "D5", "D6")) and rec["filas_validas"] == rec["esperado"],
        C2=bool(rec["D7"] and all(r["entrenamiento"]["fecha"].max() < _monday(HIST_WEEKS - PENDING_WEEKS) for r in runs.values())),
        C3=all(r["semanas"]["revisiones_lista"].le(r["escenario"].capacidad).all() for r in runs.values()),
        C4=s1["resumen"]["ahorro_lo"] > 0,
        C5=s2["resumen"]["costo_sistema"] <= s2["resumen"]["costo_actual"],
        C6=bool(w3.loc[must, "suspendida"].all() and unknown["decision"].eq("revision_humana").all() and len(unknown) > 0),
        C7=bool(dec[["semana", "unidad", "tipo_alerta", "decision", "motivo", "escenario", "regla"]].notna().all().all()),
    )


def _r(x):
    if isinstance(x, float):
        return round(x, 2)
    if isinstance(x, dict):
        return {k: _r(v) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [_r(v) for v in x]
    return x


def run(out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    runs = {sc.id: operate(sc) for sc in SCENARIOS}
    rec = check_reconciliation()
    acc = acceptance(runs, rec)
    s1 = runs["S1"]
    manifest = dict(empresa=EMPRESA, naturaleza="Datos sintéticos generados con aps_intel.alert_intake.example_data; no son datos de Scania ni de una empresa real",
                    semillas=dict(historial=11, imperfecciones_historial=21, operacion="500 + semana", imperfecciones_operacion=31),
                    reglas={sc: [dict(regla=r["regla"], tipo=r["tipo"], filas=r["filas"]) for r in runs[sc]["manifiesto"]["operacion"]] for sc in runs}
                    | dict(historial=[dict(regla=r["regla"], tipo=r["tipo"], filas=r["filas"]) for r in s1["manifiesto"]["historial"]]),
                    conciliacion_historial=s1["historial"])
    results = dict(empresa=EMPRESA, nivel="A (demostración operativa reproducible, datos sintéticos)",
                   costos=dict(revision=s1["settings"].costo_revision, falla_en_ruta=s1["settings"].costo_falla, operacion_semana=COSTO_OPERACION_SEMANA, moneda="MXN de escenario"),
                   regla=dict(id=s1["regla_id"], modo=s1["regla"].modo, corte=round(float(s1["regla"].corte), 4),
                              entrenamiento=[str(s1["entrenamiento"]["fecha"].min().date()), str(s1["entrenamiento"]["fecha"].max().date())],
                              alertas_entrenamiento=len(s1["entrenamiento"])),
                   conciliacion=rec, criterios=acc,
                   escenarios={k: dict(nombre=r["escenario"].nombre, capacidad=r["escenario"].capacidad, resumen=r["resumen"],
                                       semanas=r["semanas"].to_dict("records")) for k, r in runs.items()})
    (out / "manifest.json").write_text(json.dumps(_r(manifest), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps(_r(results), ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    pd.concat([r["decisiones"] for r in runs.values()]).to_csv(out / "decisions.csv", index=False, lineterminator="\n")
    raw, _ = inject(truth_history(), Imperfections(), seed=21, pending_from=HIST_WEEKS - PENDING_WEEKS)
    raw.to_csv(out / "raw_export_history.csv", index=False, lineterminator="\n")
    sensitivity().to_csv(out / "sensitivity.csv", index=False, lineterminator="\n")
    files = sorted(p for p in out.iterdir() if p.name != "evidence.json")
    code = [ROOT / "src/aps_intel" / f for f in ("pilot_p01.py", "alert_intake.py", "alert_calibrator.py", "monitor.py", "cost.py")]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    evidence = dict(piloto="P01", nivel="A", comando="PYTHONPATH=src python -B -m aps_intel.pilot_p01",
                    python=".".join(map(str, sys.version_info[:2])), pandas=pd.__version__, numpy=np.__version__,
                    codigo={p.relative_to(ROOT).as_posix(): sha(p) for p in code},
                    salidas={p.name: sha(p) for p in files}, criterios=acc)
    (out / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    res = run()
    print(json.dumps(dict(criterios=res["criterios"], **{k: v["resumen"] for k, v in res["escenarios"].items()}), ensure_ascii=False, indent=1, default=str))
