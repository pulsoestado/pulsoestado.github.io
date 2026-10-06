"""
Series por institución y series largas del BCP para las notas de 2027.

Se corre después de preparar_series.py, cada vez que se actualizan los archivos del DW:
    python scripts/preparar_series.py
    python scripts/preparar_instituciones.py

Entradas (data/raw/): los mismos archivos de preparar_series.py y
  resumen_personas_vinculos_2015_2025_v2.xlsx   personas y vínculos por mes y OEE

Salidas (data/processed/):
  instituciones.csv           catálogo: claves, nombre legible, nivel, entidad, agrupación y sector
  vinculos_mensual_oee.csv    vínculos por mes e institución (permanentes, contratados, mujeres)
  vinculos_tipo_sexo.csv      vínculos por mes, sector, tipo de vínculo y sexo
  masa_mensual_oee.csv        devengado y presupuestado del grupo 100 por mes e institución
  masa_anual_oee.csv          devengado anual por institución y componente
  masa_anual_oee_objeto.csv   devengado anual por institución de los objetos 12x, 13x, 14x y 16x
  categorias_oee.csv          sueldo básico (objeto 111) por categoría y sexo, junio de cada año
                              y último mes disponible
  pcd_oee_anual.csv           personas con discapacidad por institución, junio de cada año y último mes
  personas_vinculos_oee.csv   personas y vínculos por mes e institución (resumen 2015–2025)
  bcp_salario_minimo.csv      salario mínimo legal nominal y real, 1980 en adelante
  bcp_salario_minimo_tramos.csv  valores vigentes del salario mínimo por tramo
  bcp_iss_ramas.csv           Índice de Sueldos y Salarios por rama, junio y diciembre de cada año
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from clasificacion_sectores import clasificar  # noqa: E402
from pulso import nombre  # noqa: E402

RAW, OUT = RAIZ / "data/raw", RAIZ / "data/processed"
K = ["codigo_nivel", "codigo_entidad", "codigo_oee"]


def num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


# --- Catálogo de instituciones ------------------------------------------------------------------
dw = num(pd.read_excel(RAW / "dw_funcionarios_sicca_sinarh.xlsx"), ["total"])
dw["sector"] = clasificar(dw)
ult = dw.sort_values(["anho", "mes"]).groupby(K).tail(1)
cat = ult[K + ["descripcion_nivel", "descripcion_entidad", "descripcion_oee", "agrupacion", "sector"]].copy()
cat["nombre"] = cat.descripcion_oee.map(nombre)
cat["nombre_largo"] = np.where(cat.sector == "Municipalidades", "Municipalidad de " + cat.nombre, cat.nombre)
cat["nivel"] = cat.descripcion_nivel.str.replace(r"^\d+-", "", regex=True).str.strip()
cat.to_csv(OUT / "instituciones.csv", index=False)

# --- Vínculos por mes e institución --------------------------------------------------------------
v = (dw.assign(permanente=np.where(dw.vinculo == "PERMANENTE", dw.total, 0),
               contratado=np.where(dw.vinculo == "CONTRATADO", dw.total, 0),
               mujeres=np.where(dw.sexo == "FEMENINO", dw.total, 0))
     .groupby(["anho", "mes"] + K)[["permanente", "contratado", "mujeres", "total"]].sum().reset_index())
v.to_csv(OUT / "vinculos_mensual_oee.csv", index=False)
dw.groupby(["anho", "mes", "sector", "vinculo", "sexo"]).total.sum().reset_index() \
    .to_csv(OUT / "vinculos_tipo_sexo.csv", index=False)

# --- Masa salarial por institución ---------------------------------------------------------------
p = num(pd.read_excel(RAW / "dw_presupuesto_sicca_sinarh.xlsx"), ["presupuestado", "devengado"])
p = p[p.codigo_grupo == 100].copy()
p[["presupuestado", "devengado"]] = p[["presupuestado", "devengado"]].astype(float)
# Misma corrección del aguinaldo de diciembre de 2021 que en preparar_series.py (Administración Central ÷ 6)
m21 = (p.objeto_gasto.isin([114, 163]) & (p.mes == 12) & (p.anho == 2021)
       & p.agrupacion.astype(str).str.startswith("I -"))
p.loc[m21, ["presupuestado", "devengado"]] = p.loc[m21, ["presupuestado", "devengado"]] / 6

def componente(o):
    o = int(o)
    fijo = {111: "Sueldo básico", 112: "Dietas", 113: "Gastos de representación", 114: "Aguinaldo"}
    if o in fijo:
        return fijo[o]
    return {12: "Remuneraciones temporales", 13: "Bonificaciones y asignaciones", 14: "Personal contratado",
            16: "Servicio exterior"}.get(o // 10, "Otros gastos del personal")


p["componente"] = p.objeto_gasto.map(componente)
p["aguinaldo"] = np.where(p.componente == "Aguinaldo", p.devengado, 0)
mm = p.groupby(["anho", "mes"] + K)[["presupuestado", "devengado", "aguinaldo"]].sum().reset_index()
mm.to_csv(OUT / "masa_mensual_oee.csv", index=False)
ma = p.groupby(["anho"] + K + ["componente"])[["presupuestado", "devengado"]].sum().reset_index()
ma.to_csv(OUT / "masa_anual_oee.csv", index=False)
# Objetos complementarios por institución y año (12x, 13x, 14x, 16x)
p[(p.objeto_gasto // 10).isin([12, 13, 14, 16])].groupby(["anho"] + K + ["objeto_gasto"]).devengado.sum().reset_index() \
    .to_csv(OUT / "masa_anual_oee_objeto.csv", index=False)
# Objetos de gasto del grupo 100 por año (para notas sobre bonificaciones y contratos)
p.groupby(["anho", "objeto_gasto", "componente"])[["presupuestado", "devengado"]].sum().reset_index() \
    .to_csv(OUT / "masa_anual_objeto.csv", index=False)

# --- Categorías salariales ------------------------------------------------------------------------
c = num(pd.read_excel(RAW / "dw_nivel_categ_sicca_sinarh.xlsx"), ["cantidad", "presupuestado", "devengado"])
ua = int(c.anho.max()); um = int(c[c.anho == ua].mes.max())
sel = (c.mes == 6) | ((c.anho == ua) & (c.mes == um))
c = c[sel & (c.cantidad > 0) & (~c.nivel_categoria.astype(str).isin([".", "#", "-"]))]
c = c.groupby(["anho", "mes"] + K + ["nivel_categoria", "sexo"])[["cantidad", "devengado"]].sum().reset_index()
c.to_csv(OUT / "categorias_oee.csv", index=False)

# --- Personas con discapacidad por institución --------------------------------------------------------
f = pd.read_excel(RAW / "dw_funcionarios_sicca.xlsx")
base = ["contratado_femenino", "contratado_masculino", "permanente_femenino", "permanente_masculino"]
pc = [x for x in f.columns if x.startswith("pcd_")]
f = num(f, base + pc)
f["vinculos"] = f[base].sum(axis=1)
f["mujeres"] = f.contratado_femenino + f.permanente_femenino
f["pcd"] = f[pc].sum(axis=1)
ua, um = int(f.anho.max()), int(f[f.anho == f.anho.max()].mes.max())
f = f[(f.mes == 6) | ((f.anho == ua) & (f.mes == um))]
f["sector"] = clasificar(f)
f.groupby(["anho", "mes"] + K + ["descripcion_oee", "sector"])[["vinculos", "mujeres", "pcd"] + pc].sum() \
    .reset_index().to_csv(OUT / "pcd_oee_anual.csv", index=False)

# --- Personas y vínculos (resumen) ----------------------------------------------------------------------
r = pd.read_excel(RAW / "resumen_personas_vinculos_2015_2025_v2.xlsx")
r = r.rename(columns={"nivel": "codigo_nivel", "entidad": "codigo_entidad", "oee": "codigo_oee"})
r["vinculos"] = r.permanente + r.contratado
r[["anho", "mes"] + K + ["cantidad_mensual", "cantidad_acumulada", "permanente", "contratado", "vinculos"]] \
    .rename(columns={"cantidad_mensual": "personas", "cantidad_acumulada": "personas_acumuladas"}) \
    .to_csv(OUT / "personas_vinculos_oee.csv", index=False)

# --- BCP: salario mínimo desde 1980 e ISS por rama -------------------------------------------------------
x = pd.read_excel(RAW / "bcp_anexo_ipc_salarios.xlsx", sheet_name="CUADRO 1", header=None)
anual, tramos, anio = [], [], None
for _, fila in x.iloc[10:].iterrows():
    a = pd.to_numeric(fila[0], errors="coerce")
    if pd.notna(a) and 1980 <= a <= 2100:
        anio = int(a)
        anual.append({"anho": anio, "ipc": float(fila[1]), "salario_minimo": float(fila[2]),
                      "salario_minimo_real_1980": float(fila[3])})
    elif anio and isinstance(fila[0], str) and pd.notna(fila[2]):
        tramos.append({"anho": anio, "periodo": fila[0].strip(), "salario_minimo": float(fila[2])})
sm = pd.DataFrame(anual)
sm["salario_minimo_real_ultimo"] = sm.salario_minimo * sm.ipc.iloc[-1] / sm.ipc
sm.to_csv(OUT / "bcp_salario_minimo.csv", index=False)
pd.DataFrame(tramos).to_csv(OUT / "bcp_salario_minimo_tramos.csv", index=False)

y = pd.read_excel(RAW / "bcp_anexo_ipc_salarios.xlsx", sheet_name="CUADRO 2", header=None)
ramas = [str(s).strip() for s in y.iloc[8, 1:11]]
ramas = [r_.replace("Electriciadad", "Electricidad") for r_ in ramas]
filas, anio = [], None
for _, fila in y.iloc[10:].iterrows():
    a = pd.to_numeric(fila[0], errors="coerce")
    if pd.notna(a) and 2000 <= a <= 2100:
        anio = int(a)
    elif anio and str(fila[0]).strip()[:3].lower() in ("jun", "dic") and pd.notna(fila[10]):
        d = {"anho": anio, "periodo": str(fila[0]).strip()[:3].lower()}
        d.update({rn: float(fila[i + 1]) for i, rn in enumerate(ramas)})
        filas.append(d)
pd.DataFrame(filas).to_csv(OUT / "bcp_iss_ramas.csv", index=False)
print("Listo:", len(cat), "instituciones;", v.anho.max(), int(v[v.anho == v.anho.max()].mes.max()))

# --- INDEC (Argentina): dotación de la Administración Pública Nacional ----------------------------------
try:
    d = pd.read_excel(RAW / "indec_serie_dotacion_apn.xlsx", sheet_name="serie  cuadro 1", header=None)
    MES_AB = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
              "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12}

    def fecha_indec(x):
        if hasattr(x, "year"):
            return pd.Timestamp(x.year, x.month, 1), False
        m, a = str(x).split(" ")[0].split("-")
        return pd.Timestamp(2000 + int(a), MES_AB[m], 1), "(i)" in str(x)

    filas = []
    for j in range(1, d.shape[1]):
        if pd.isna(d.iloc[3, j]):
            continue
        f, imp = fecha_indec(d.iloc[3, j])
        filas.append({"fecha": f.date(), "anho": f.year, "mes": f.month, "imputado": imp,
                      "total": float(d.iloc[6, j]), "apn": float(d.iloc[8, j]), "empresas": float(d.iloc[14, j])})
    pd.DataFrame(filas).to_csv(OUT / "indec_dotacion_apn.csv", index=False)
except FileNotFoundError:
    pass
