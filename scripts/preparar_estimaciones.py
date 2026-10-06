"""
Estimaciones rotuladas: el último mes completado y las proyecciones a 2035.

Se corre después de preparar_series.py y preparar_instituciones.py:
    python scripts/preparar_estimaciones.py

1. Último mes completado (data/processed/vinculos_completados_sector.csv)
   Varias instituciones —sobre todo municipalidades— cargan sus datos con meses de atraso. Para los
   meses posteriores al último mes "confiable" (cuando reportó al menos el 97% de las instituciones
   que reportaron un año antes), cada institución que todavía no reportó se completa con su último
   dato disponible. El archivo muestra lo reportado, lo completado y cuántas instituciones faltan.

2. Proyecciones a 2035 (data/processed/proyecciones_2035.csv)
   Escenarios simples, no pronósticos:
   - Tendencia larga: los vínculos de cada sector crecen como en promedio desde 2017.
   - Tendencia reciente: crecen como en los últimos tres años completos.
   - Contención: el total crece 0,5% por año, repartido según el peso de cada sector.
   La masa salarial real resulta de multiplicar los vínculos por la remuneración media real del
   último año completo, con tres supuestos de aumento real: 0%, 1% y 2% por año.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from pulso import leer, instituciones, ultimo_mes, ultimo_mes_confiable, ultimo_anio_completo, deflactor, K_OEE  # noqa: E402

OUT = RAIZ / "data/processed"

# --- 1. Último mes completado ----------------------------------------------------------------------
v = leer("vinculos_mensual_oee.csv")
v = v[v.total > 0].merge(instituciones()[K_OEE + ["sector"]], on=K_OEE, how="left")
v["t"] = v.anho * 12 + v.mes - 1
ac, mc = ultimo_mes_confiable()
A1, M1 = ultimo_mes()
t0, t1 = ac * 12 + mc - 1, A1 * 12 + M1 - 1
filas = []
activos = v[(v.t > t0 - 12) & (v.t <= t0)].groupby(K_OEE).t.max()   # instituciones activas en el último año confiable
for t in range(t0 + 1, t1 + 1):
    rep = v[v.t == t]
    falt = activos.index.difference(rep.set_index(K_OEE).index)
    ult = v[v.t < t].sort_values("t").groupby(K_OEE).tail(1).set_index(K_OEE)
    comp = ult.loc[ult.index.intersection(falt)].reset_index()
    a, m = divmod(t, 12)
    for s, g in pd.concat([rep.assign(fuente="reportado"), comp.assign(fuente="completado")]).groupby("sector"):
        r = g[g.fuente == "reportado"]
        filas.append(dict(anho=a, mes=m + 1, sector=s, reportado=r.total.sum(), completado=g.total.sum(),
                          contratado_completado=g.contratado.sum(), instituciones_reportan=len(r),
                          instituciones_completadas=int((g.fuente == "completado").sum())))
nc = pd.DataFrame(filas)
nc.to_csv(OUT / "vinculos_completados_sector.csv", index=False)

# --- 2. Proyecciones a 2035 ------------------------------------------------------------------------
UA = ultimo_anio_completo()
ms = leer("masa_anual_sector.csv")
vin = ms.pivot(index="anho", columns="sector", values="vinculos_promedio")
masa = ms.pivot(index="anho", columns="sector", values="devengado_sin_aguinaldo")
D = deflactor(UA)
rem = (masa.loc[UA] / 12 / vin.loc[UA])                           # remuneración media mensual del último año
cagr_larga = (vin.loc[UA] / vin.loc[2017]) ** (1 / (UA - 2017)) - 1
cagr_rec = (vin.loc[UA] / vin.loc[UA - 3]) ** (1 / 3) - 1
peso = vin.loc[UA] / vin.loc[UA].sum()
rows = []
for anio in range(UA, 2036):
    n = anio - UA
    esc_v = {"Tendencia larga": vin.loc[UA] * (1 + cagr_larga) ** n,
             "Tendencia reciente": vin.loc[UA] * (1 + cagr_rec) ** n,
             "Contención (0,5% anual)": vin.loc[UA].sum() * 1.005 ** n * peso}
    for ev, vv in esc_v.items():
        for real in (0.0, 0.01, 0.02):
            m_ = vv * rem * (1 + real) ** n * 13       # 12 meses + aguinaldo, en guaraníes del último año completo
            for s in vv.index:
                rows.append(dict(anho=anio, escenario_vinculos=ev, aumento_real_anual=real, sector=s,
                                 vinculos=vv[s], masa_real=m_[s]))
pr = pd.DataFrame(rows)
pr["base"] = UA
pr.to_csv(OUT / "proyecciones_2035.csv", index=False)
tot = pr.groupby(["anho", "escenario_vinculos", "aumento_real_anual"])[["vinculos", "masa_real"]].sum().reset_index()
print(nc.groupby(["anho", "mes"])[["reportado", "completado", "instituciones_completadas"]].sum())
print(tot[tot.anho.isin([UA, 2030, 2035]) & (tot.aumento_real_anual == 0.01)].round(0).to_string(index=False))
