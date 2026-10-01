"""
Prepara las series del archivo principal DW_FUNCIONARIOS_SICCA_SINARH
(vínculos pagados por mes, OEE, tipo de vínculo y sexo).

Entrada : data/raw/dw_funcionarios_sicca_sinarh.xlsx
Salidas : data/processed/dw_mensual.csv
          data/processed/dw_mensual_sector.csv
          data/processed/dw_anual_sector.csv
          data/processed/dw_panel_interanual.csv

Unidad de medida: VÍNCULOS pagados en el mes (una persona con dos vínculos
cuenta dos veces). No es lo mismo que "personas distintas" ni que
"cargos presupuestados" del PGN.

Ejecutar desde la raíz del repositorio:  python scripts/preparar_dw.py
"""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "data/raw/dw_funcionarios_sicca_sinarh.xlsx"
SALIDA = RAIZ / "data/processed"
SALIDA.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(ENTRADA)
df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0).astype(int)


def sector(oee: str) -> str:
    """Sectores seleccionados a partir del nombre del OEE."""
    o = oee.upper()
    if "MINISTERIO DE EDUCACION Y CIENCIAS" in o or "MINISTERIO DE EDUCACION Y CULTURA" in o:
        return "Educación (MEC)"
    if "MINISTERIO DE SALUD PUBLICA" in o:
        return "Salud (MSPBS)"
    if "POLICIA NACIONAL" in o:
        return "Policía Nacional"
    if "MINISTERIO DE DEFENSA NACIONAL" in o:
        return "Defensa Nacional"
    return "Resto del sector público"


df["sector"] = df["descripcion_oee"].map(sector)

# ---- Serie mensual total ---------------------------------------------------------
def resumir(g):
    return pd.Series({
        "permanente": g.loc[g.vinculo == "PERMANENTE", "total"].sum(),
        "contratado": g.loc[g.vinculo == "CONTRATADO", "total"].sum(),
        "mujeres": g.loc[g.sexo == "FEMENINO", "total"].sum(),
        "hombres": g.loc[g.sexo == "MASCULINO", "total"].sum(),
    })

mensual = df.groupby(["anho", "mes"]).apply(resumir, include_groups=False).reset_index()
mensual["total"] = mensual["permanente"] + mensual["contratado"]
reportan = (df[["anho", "mes", "codigo_nivel", "codigo_entidad", "codigo_oee"]]
            .drop_duplicates().groupby(["anho", "mes"]).size().rename("oee_reportan"))
mensual = mensual.merge(reportan, on=["anho", "mes"])
mensual["fecha"] = mensual["anho"].astype(str) + "-" + mensual["mes"].astype(str).str.zfill(2)
mensual.to_csv(SALIDA / "dw_mensual.csv", index=False)

# ---- Serie mensual por sector -----------------------------------------------------
sec = df.groupby(["anho", "mes", "sector"]).apply(resumir, include_groups=False).reset_index()
sec["total"] = sec["permanente"] + sec["contratado"]
sec["fecha"] = sec["anho"].astype(str) + "-" + sec["mes"].astype(str).str.zfill(2)
sec.to_csv(SALIDA / "dw_mensual_sector.csv", index=False)

# ---- Promedios anuales por sector (solo años completos) ---------------------------
completos = mensual.groupby("anho")["mes"].count()
completos = completos[completos == 12].index
anual = (sec[sec.anho.isin(completos)]
         .groupby(["anho", "sector"])[["permanente", "contratado", "mujeres", "hombres", "total"]]
         .mean().round(0).astype(int).reset_index())
anual.to_csv(SALIDA / "dw_anual_sector.csv", index=False)

# ---- Panel constante: último mes vs. mismo mes del año anterior -----------------
# Solo OEE que reportaron en ambos meses, para que la comparación no dependa
# de instituciones que todavía no cargaron sus datos.
ult = mensual.iloc[-1]
a1, m1 = int(ult.anho), int(ult.mes)
claves = ["codigo_nivel", "codigo_entidad", "codigo_oee"]
oee = (df[((df.anho == a1) | (df.anho == a1 - 1)) & (df.mes == m1)]
       .groupby(["anho", *claves, "descripcion_oee", "agrupacion", "sector", "vinculo"])["total"]
       .sum().unstack("vinculo", fill_value=0).reset_index())
oee.columns.name = None
oee = oee.rename(columns={"PERMANENTE": "permanente", "CONTRATADO": "contratado"})
oee.to_csv(SALIDA / "dw_panel_interanual.csv", index=False)

print(mensual.tail(3).to_string(index=False))
