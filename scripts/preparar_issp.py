"""
Índice de Sueldos del Sector Público (ISSP) y medidas de estructura salarial.

Se corre después de preparar_series.py y preparar_instituciones.py:
    python scripts/preparar_issp.py

Qué mide. El ISSP responde cuánto subió el sueldo básico de un mismo cargo, sin el efecto de
quién entra y quién sale. Compara cada período con el anterior usando solo las "celdas" que
existen en los dos: una celda es una categoría salarial dentro de una institución
(institución × letra de categoría). El precio de una celda es su sueldo básico medio
(devengado del objeto 111 ÷ cargos) y su peso, la cantidad de cargos.

  Laspeyres = Σ p1·q0 / Σ p0·q0   (pesos del período anterior)
  Paasche   = Σ p1·q1 / Σ p0·q1   (pesos del período actual)
  Fisher    = √(Laspeyres × Paasche)   ← índice principal
Los eslabones se encadenan y el índice se expresa con base promedio 2025 = 100.

Entradas: data/raw/dw_nivel_categ_sicca_sinarh.xlsx (DW_NIVEL_CATEG_SICCA_SINARH).
Criterios: cargos > 0, devengado > 0, categoría distinta de ".", "#" o "-".
Corrección: junio de 2017 tiene un pago retroactivo en la Policía Nacional (categoría P) y en
el Ministerio de Defensa (categoría M); el índice usa mayo de 2017 en lugar de junio de ese año
(ver data/manual/correcciones.csv).

Salidas (data/processed/):
  issp_trimestral.csv   índice trimestral (marzo, junio, septiembre, diciembre), total
  issp_anual.csv        índice de junio de cada año, real, sueldo medio, efecto composición,
                        compresión y dispersión
  issp_sector_anual.csv índice de junio por sector
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from clasificacion_sectores import clasificar  # noqa: E402

RAW, OUT = RAIZ / "data/raw", RAIZ / "data/processed"
K = ["codigo_nivel", "codigo_entidad", "codigo_oee"]
CELDA = K + ["nivel_categoria"]

c = pd.read_excel(RAW / "dw_nivel_categ_sicca_sinarh.xlsx")
for col in ["cantidad", "devengado"]:
    c[col] = pd.to_numeric(c[col], errors="coerce").fillna(0)
c = c[(c.cantidad > 0) & (c.devengado > 0) & (~c.nivel_categoria.astype(str).isin([".", "#", "-"]))].copy()
c["sector"] = clasificar(c)
cel = c.groupby(["anho", "mes", "sector"] + CELDA)[["cantidad", "devengado"]].sum().reset_index()
cel["p"] = cel.devengado / cel.cantidad


def periodo(a, m):
    """Mes efectivo que representa al período (junio de 2017 → mayo de 2017)."""
    return (a, 5) if (a, m) == (2017, 6) else (a, m)


def eslabon(d0, d1):
    j = d0.merge(d1, on=CELDA, suffixes=("0", "1"))
    if j.empty:
        return np.nan, np.nan, np.nan, 0, 0
    L = (j.p1 * j.cantidad0).sum() / (j.p0 * j.cantidad0).sum()
    P = (j.p1 * j.cantidad1).sum() / (j.p0 * j.cantidad1).sum()
    cob = j.cantidad1.sum() / d1.cantidad.sum() * 100
    return np.sqrt(L * P), L, P, cob, len(j)


def cadena(periodos, datos, base_anio=2025):
    filas, idx = [], {"F": 1.0, "L": 1.0, "P": 1.0}
    prev = None
    for a, m in periodos:
        ea, em = periodo(a, m)
        d = datos[(datos.anho == ea) & (datos.mes == em)]
        if d.empty:
            continue
        if prev is None:
            filas.append(dict(anho=a, mes=m, F=1.0, L=1.0, P=1.0, cobertura_pct=np.nan, celdas=len(d)))
        else:
            F, L, P, cob, n = eslabon(prev, d)
            idx = {"F": idx["F"] * F, "L": idx["L"] * L, "P": idx["P"] * P}
            filas.append(dict(anho=a, mes=m, **idx, cobertura_pct=cob, celdas=n))
        prev = d
    t = pd.DataFrame(filas)
    if t.empty:
        return t
    b = t[t.anho == base_anio]
    if b.empty:
        b = t.tail(1)
    for k, n in [("F", "fisher"), ("L", "laspeyres"), ("P", "paasche")]:
        t[n] = t[k] / b[k].mean() * 100
    return t.drop(columns=["F", "L", "P"])


tot = cel.groupby(["anho", "mes"] + CELDA)[["cantidad", "devengado"]].sum().reset_index()
tot["p"] = tot.devengado / tot.cantidad
meses_ok = sorted(set(zip(tot.anho, tot.mes)))
ultimo = meses_ok[-1]

# --- Trimestral --------------------------------------------------------------------------------
trim = [(a, m) for a in range(2015, ultimo[0] + 1) for m in (3, 6, 9, 12) if (a, m) <= ultimo and (a, m) >= (2015, 12)]
q = cadena(trim, tot)
q["trimestre"] = (q.mes // 3).astype(int)
q["var_trimestral"] = q.fisher.pct_change() * 100
q["var_interanual"] = q.fisher.pct_change(4) * 100
q.to_csv(OUT / "issp_trimestral.csv", index=False)

# --- Anual (junio) -----------------------------------------------------------------------------
an = cadena([(a, 6) for a in range(2016, ultimo[0] + 1)], tot)
an = an[["anho", "fisher", "laspeyres", "paasche", "cobertura_pct", "celdas"]]
ipc = pd.read_csv(OUT / "ipc_salarios_bcp.csv").set_index("anho")["ipc"]
an["ipc"] = an.anho.map(ipc)
an["fisher_real"] = an.fisher / an.ipc * ipc.get(2025, an.ipc.iloc[-1])
an["var"] = an.fisher.pct_change() * 100
an["var_real"] = an.fisher_real.pct_change() * 100
sm = tot.groupby(["anho", "mes"]).apply(lambda g: g.devengado.sum() / g.cantidad.sum(), include_groups=False)
an["sueldo_medio"] = [sm.get(periodo(a, 6), np.nan) for a in an.anho]
an["var_sueldo_medio"] = an.sueldo_medio.pct_change() * 100
an["efecto_composicion_pp"] = an.var_sueldo_medio - an["var"]


def estructura(a):
    ea, em = periodo(a, 6)
    d = tot[(tot.anho == ea) & (tot.mes == em)]
    w = d.pivot_table(index=K, columns="nivel_categoria", values="p")
    bg = (w["B"] / w["G"]).dropna() if {"B", "G"} <= set(w.columns) else pd.Series(dtype=float)
    s = d.sort_values("p")
    cum = s.cantidad.cumsum() / s.cantidad.sum()
    p10 = s.p[cum >= 0.10].iloc[0]
    p90 = s.p[cum >= 0.90].iloc[0]
    return pd.Series({"ratio_b_g": bg.median() if len(bg) else np.nan, "p90_p10": p90 / p10})


an = an.join(an.anho.apply(estructura))
an.to_csv(OUT / "issp_anual.csv", index=False)

# --- Por sector (junio) -------------------------------------------------------------------------
sec = []
for s_, g in cel.groupby("sector"):
    t = cadena([(a, 6) for a in range(2016, ultimo[0] + 1)], g)
    if not t.empty:
        t["sector"] = s_
        sec.append(t[["anho", "sector", "fisher", "cobertura_pct", "celdas"]])
ss = pd.concat(sec)
ss["var"] = ss.groupby("sector").fisher.pct_change() * 100
ss.to_csv(OUT / "issp_sector_anual.csv", index=False)

print(an[["anho", "fisher", "var", "var_real", "efecto_composicion_pp", "ratio_b_g", "p90_p10"]].round(2).to_string(index=False))
print(q.tail(6)[["anho", "mes", "fisher", "var_trimestral", "var_interanual", "cobertura_pct"]].round(2).to_string(index=False))
