"""
Prepara las series de la serie editorial (octubre–diciembre 2026).

Entradas (data/raw/):
  dw_funcionarios_sicca_sinarh.xlsx   vínculos por mes, OEE, vínculo y sexo
  dw_presupuesto_sicca_sinarh.xlsx    presupuestado y devengado mensual por objeto de gasto
  dw_nivel_categ_sicca_sinarh.xlsx    sueldo básico (objeto 111) por categoría y sexo
  dw_funcionarios_sicca.xlsx          vínculos con desagregación de personas con discapacidad
  bcp_anexo_ipc_salarios.xlsx         BCP: IPC anual, salario mínimo e Índice de Sueldos y Salarios

Salidas (data/processed/):
  ipc_salarios_bcp.csv        IPC promedio anual, salario mínimo y ISS (BCP)
  vinculos_mensual_sector.csv vínculos por mes y sector
  masa_mensual_sector.csv     devengado de servicios personales por mes, sector y componente
  masa_anual_sector.csv       masa anual por sector (nominal y a precios de 2025) + vínculos promedio
  pcd_mensual.csv             vínculos y personas con discapacidad (PcD) por mes
  pcd_oee.csv                 PcD por institución, junio de 2026
  genero_brecha_anual.csv     brecha salarial de género, bruta y dentro de la misma categoría
  genero_brecha_sector.csv    brecha por sector, junio de 2026
  municipios_2025.csv         vínculos, contratados, mujeres y masa por municipalidad, 2025

Corrección aplicada: el aguinaldo (objeto 114) de diciembre de 2021 figura unas cinco
veces por encima de lo normal en el archivo de presupuesto (6,0 billones frente a
1,2 billones en 2020 y 2022). Para cada institución se reemplaza por el promedio de sus
aguinaldos de 2020 y 2022 y la corrección queda marcada en la columna `imputado`.
Lo mismo ocurre con el aguinaldo del personal del servicio exterior (objeto 163), que
se corrige de la misma manera.

Ejecutar desde la raíz del repositorio:  python scripts/preparar_series.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from clasificacion_sectores import clasificar  # noqa: E402

RAW, OUT = RAIZ / "data/raw", RAIZ / "data/processed"
OUT.mkdir(parents=True, exist_ok=True)
CLAVE = ["codigo_nivel", "codigo_entidad", "codigo_oee"]


def num(df, cols):
    for c in cols:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


# --- 1. IPC, salario mínimo e ISS (BCP) ------------------------------------------------
x = pd.read_excel(RAW / "bcp_anexo_ipc_salarios.xlsx", sheet_name="CUADRO 1", header=None)
filas = x[pd.to_numeric(x[0], errors="coerce").between(2010, 2030)]
bcp = pd.DataFrame({
    "anho": filas[0].astype(int).values,
    "ipc": filas[1].astype(float).values,                  # base 1980 = 100, promedio anual
    "salario_minimo": filas[2].astype(float).values,       # promedio anual, Gs/mes
})
y = pd.read_excel(RAW / "bcp_anexo_ipc_salarios.xlsx", sheet_name="CUADRO 2", header=None)
iss = y[pd.to_numeric(y[0], errors="coerce").between(2010, 2030)][[0, 10]]
iss.columns = ["anho", "iss_general"]
bcp = bcp.merge(iss.astype({"anho": int, "iss_general": float}), on="anho", how="left")
# ISS de junio de cada año (la fila "Jun" que sigue a cada año)
jun, anio = {}, None
for _, r in y.iterrows():
    a0 = pd.to_numeric(r[0], errors="coerce")
    if pd.notna(a0) and 2000 <= a0 <= 2030:
        anio = int(a0)
    elif str(r[0]).strip().lower().startswith("jun") and anio:
        jun[anio] = float(r[10])
bcp["iss_junio"] = bcp.anho.map(jun)
bcp["deflactor_2025"] = bcp.loc[bcp.anho == 2025, "ipc"].iloc[0] / bcp["ipc"]
bcp.to_csv(OUT / "ipc_salarios_bcp.csv", index=False)
DEF = bcp.set_index("anho")["deflactor_2025"]

# --- 2. Vínculos por sector -----------------------------------------------------------------
dw = num(pd.read_excel(RAW / "dw_funcionarios_sicca_sinarh.xlsx"), ["total"])
dw["sector"] = clasificar(dw)
v = (dw.assign(perm=np.where(dw.vinculo == "PERMANENTE", dw.total, 0),
               contr=np.where(dw.vinculo == "CONTRATADO", dw.total, 0),
               muj=np.where(dw.sexo == "FEMENINO", dw.total, 0))
     .groupby(["anho", "mes", "sector"])[["perm", "contr", "muj", "total"]].sum().reset_index()
     .rename(columns={"perm": "permanente", "contr": "contratado", "muj": "mujeres"}))
v.to_csv(OUT / "vinculos_mensual_sector.csv", index=False)

# --- 3. Masa salarial ------------------------------------------------------------------------
p = num(pd.read_excel(RAW / "dw_presupuesto_sicca_sinarh.xlsx"), ["presupuestado", "devengado"])
p = p[p.codigo_grupo == 100].copy()
p[["presupuestado", "devengado"]] = p[["presupuestado", "devengado"]].astype(float)
p["imputado"] = False

# Corrección del aguinaldo de diciembre de 2021
ag = p[p.objeto_gasto.isin([114, 163]) & (p.mes == 12)]
ref = (ag[ag.anho.isin([2020, 2022])].groupby(CLAVE + ["objeto_gasto"])[["presupuestado", "devengado"]].mean())
m21 = p.objeto_gasto.isin([114, 163]) & (p.mes == 12) & (p.anho == 2021)
antes = p.loc[m21, "devengado"].sum()
idx = p.loc[m21].set_index(CLAVE + ["objeto_gasto"]).index
reemplazo = ref.reindex(idx)
ok = reemplazo["devengado"].notna().values
p.loc[p.index[m21][ok], ["presupuestado", "devengado"]] = reemplazo[ok].values
p.loc[p.index[m21][ok], "imputado"] = True
print(f"Aguinaldo dic-2021: {antes/1e12:.2f} → {p.loc[m21,'devengado'].sum()/1e12:.2f} billones")


def componente(o):
    o = int(o)
    if o == 111: return "Sueldo básico"
    if o == 112: return "Dietas"
    if o == 113: return "Gastos de representación"
    if o == 114: return "Aguinaldo"
    g = o // 10
    return {12: "Remuneraciones temporales", 13: "Bonificaciones y asignaciones",
            14: "Personal contratado", 16: "Servicio exterior", 19: "Otros gastos del personal"
            }.get(g, "Otros gastos del personal")


p["componente"] = p.objeto_gasto.map(componente)
p["sector"] = clasificar(p)
mm = (p.groupby(["anho", "mes", "sector", "componente"])[["presupuestado", "devengado"]]
      .sum().reset_index())
mm.to_csv(OUT / "masa_mensual_sector.csv", index=False)

anual = (p.groupby(["anho", "sector"])
         .apply(lambda g: pd.Series({
             "devengado": g.devengado.sum(),
             "devengado_sin_aguinaldo": g.loc[g.componente != "Aguinaldo", "devengado"].sum(),
             "meses": g.mes.nunique()}), include_groups=False).reset_index())
vin = v.groupby(["anho", "sector"])["total"].mean().rename("vinculos_promedio").reset_index()
anual = anual.merge(vin, on=["anho", "sector"], how="left")
anual["devengado_real_2025"] = anual.devengado * anual.anho.map(DEF)
anual["sin_aguinaldo_real_2025"] = anual.devengado_sin_aguinaldo * anual.anho.map(DEF)
anual.to_csv(OUT / "masa_anual_sector.csv", index=False)

# --- 4. Personas con discapacidad ---------------------------------------------------------------
f = num(pd.read_excel(RAW / "dw_funcionarios_sicca.xlsx"), [])
base = ["contratado_femenino", "contratado_masculino", "permanente_femenino", "permanente_masculino"]
pcd = [c for c in f.columns if c.startswith("pcd_")]
f[base + pcd] = f[base + pcd].apply(pd.to_numeric, errors="coerce").fillna(0)
f["vinculos"] = f[base].sum(axis=1)
f["pcd"] = f[pcd].sum(axis=1)
f["sector"] = clasificar(f)
pm = f.groupby(["anho", "mes"])[["vinculos", "pcd"] + pcd].sum().reset_index()
pm["oee_reportan"] = f.groupby(["anho", "mes"]).size().values
pm.to_csv(OUT / "pcd_mensual.csv", index=False)
po = (f[(f.anho == 2026) & (f.mes == 6)]
      .groupby(CLAVE + ["descripcion_oee", "sector", "agrupacion"])[["vinculos", "pcd"] + pcd]
      .sum().reset_index())
po.to_csv(OUT / "pcd_oee.csv", index=False)

# --- 5. Brecha salarial de género (sueldo básico por cargo, junio de cada año) ------------------
c = num(pd.read_excel(RAW / "dw_nivel_categ_sicca_sinarh.xlsx"), ["cantidad", "presupuestado", "devengado"])
c = c[(c.mes == 6) & (c.cantidad > 0) & (c.devengado > 0) & (~c.nivel_categoria.isin([".", "#", "-"]))]
c["sector"] = clasificar(c)
celda = CLAVE + ["nivel_categoria"]


def brechas(g):
    s = g.groupby("sexo")[["cantidad", "devengado"]].sum()
    mf = s.loc["FEMENINO", "devengado"] / s.loc["FEMENINO", "cantidad"]
    mh = s.loc["MASCULINO", "devengado"] / s.loc["MASCULINO", "cantidad"]
    w = g.pivot_table(index=celda, columns="sexo", values=["cantidad", "devengado"], aggfunc="sum").dropna()
    sf = w[("devengado", "FEMENINO")] / w[("cantidad", "FEMENINO")]
    sh = w[("devengado", "MASCULINO")] / w[("cantidad", "MASCULINO")]
    peso = w[("cantidad", "FEMENINO")] + w[("cantidad", "MASCULINO")]
    return pd.Series({
        "cargos": s.cantidad.sum(), "pct_mujeres": s.loc["FEMENINO", "cantidad"] / s.cantidad.sum() * 100,
        "sueldo_medio_mujeres": mf, "sueldo_medio_hombres": mh,
        "brecha_bruta_pct": (mh - mf) / mh * 100,
        "brecha_misma_categoria_pct": float(np.average((sh - sf) / sh * 100, weights=peso)),
        "cobertura_celdas_pct": peso.sum() / s.cantidad.sum() * 100,
    })


ga = c.groupby("anho").apply(brechas, include_groups=False).reset_index()
ga.to_csv(OUT / "genero_brecha_anual.csv", index=False)
gs = c[c.anho == 2026].groupby("sector").apply(brechas, include_groups=False).reset_index()
gs.to_csv(OUT / "genero_brecha_sector.csv", index=False)

# --- 6. Municipalidades, 2025 --------------------------------------------------------------------
mu = dw[(dw.sector == "Municipalidades") & (dw.anho == 2025)]
mv = (mu.assign(contr=np.where(mu.vinculo == "CONTRATADO", mu.total, 0),
                muj=np.where(mu.sexo == "FEMENINO", mu.total, 0))
      .groupby(["codigo_oee", "descripcion_oee", "anho", "mes"])[["total", "contr", "muj"]].sum()
      .reset_index().groupby(["codigo_oee", "descripcion_oee"])
      .agg(vinculos=("total", "mean"), contratados=("contr", "mean"), mujeres=("muj", "mean"),
           meses=("mes", "nunique")).reset_index())
mp = p[(p.sector == "Municipalidades") & (p.anho == 2025)]
mmasa = mp.pivot_table(index="codigo_oee", columns="componente", values="devengado", aggfunc="sum",
                       fill_value=0)
mmasa["masa_total"] = mmasa.sum(axis=1)
mv = mv.merge(mmasa[["masa_total", "Dietas", "Gastos de representación"]].reset_index(),
              on="codigo_oee", how="left")
mv.to_csv(OUT / "municipios_2025.csv", index=False)
# --- 7. Panel interanual del último mes (para SITUCAP) ------------------------------------
ua, um = int(v.anho.max()), int(v[v.anho == v.anho.max()].mes.max())
pv = (dw[((dw.anho == ua) | (dw.anho == ua - 1)) & (dw.mes == um)]
      .assign(contr=lambda x: np.where(x.vinculo == "CONTRATADO", x.total, 0),
              muj=lambda x: np.where(x.sexo == "FEMENINO", x.total, 0))
      .groupby(["anho"] + CLAVE + ["descripcion_oee", "sector"])[["total", "contr", "muj"]].sum()
      .reset_index().rename(columns={"total": "vinculos", "contr": "contratados", "muj": "mujeres"}))
pmasa = (p[((p.anho == ua) | (p.anho == ua - 1)) & (p.mes <= um)]
         .assign(mes_actual=lambda x: np.where(x.mes == um, x.devengado, 0))
         .groupby(["anho"] + CLAVE)[["devengado", "mes_actual"]].sum().reset_index()
         .rename(columns={"devengado": "masa_acumulada", "mes_actual": "masa_mes"}))
panel = pv.merge(pmasa, on=["anho"] + CLAVE, how="outer")
panel["mes"] = um
panel.to_csv(OUT / "panel_situcap.csv", index=False)
print("Listo")
