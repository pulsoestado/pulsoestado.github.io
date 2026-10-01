"""
Prepara las series de dotación del sector público a partir del resumen
"Cantidad acumulada de personas y vínculos por año y OEE (2015-2025) v2".

Entrada : data/raw/resumen_personas_vinculos_2015_2025_v2.xlsx
Salidas : data/processed/dotacion_mensual.csv
          data/processed/dotacion_anual.csv
          data/processed/dotacion_anual_nivel.csv

Definiciones usadas
-------------------
- cantidad_mensual   : personas que cobraron en el mes.
- cantidad_acumulada : personas distintas que cobraron al menos una vez
                       desde enero hasta ese mes (acumulado del año).
- permanente / contratado : vínculos del mes por tipo. Una persona puede
                       tener ambos vínculos, por eso la suma puede superar
                       a cantidad_mensual.

Ejecutar desde la raíz del repositorio:  python scripts/preparar_dotacion.py
"""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "data/raw/resumen_personas_vinculos_2015_2025_v2.xlsx"
SALIDA = RAIZ / "data/processed"
SALIDA.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(ENTRADA)

# Normalizar el nivel: quitar el prefijo numérico ("12-PODER EJECUTIVO" -> "PODER EJECUTIVO")
ETIQUETAS = {
    "PODER LEGISLATIVO": "Poder Legislativo",
    "PODER EJECUTIVO": "Poder Ejecutivo",
    "PODER JUDICIAL": "Poder Judicial",
    "PODER JUDICIAL Y ORGANISMOS AUXILIARES DE JUSTICIA": "Poder Judicial",
    "CONTRALORÍA GENERAL DE LA REPÚBLICA": "Contraloría General",
    "OTROS ORGANISMOS DEL ESTADO": "Otros organismos del Estado",
    "BANCA CENTRAL DEL ESTADO": "Banco Central",
    "GOBIERNOS DEPARTAMENTALES": "Gobiernos departamentales",
    "ENTES AUTONOMOS Y AUTARQUICOS": "Entes autónomos y autárquicos",
    "ENTIDADES PUBLICAS DE SEGURIDAD SOCIAL": "Seguridad social",
    "EMPRESAS PUBLICAS": "Empresas públicas",
    "ENTIDADES FINANCIERAS OFICIALES": "Entidades financieras oficiales",
    "UNIVERSIDADES NACIONALES": "Universidades nacionales",
    "MUNICIPALIDADES": "Municipalidades",
    "SOCIEDADES ANONIMAS CON PARTICIPACION ACCIONARIA DEL ESTADO": "Sociedades anónimas del Estado",
}
base = df["descripcion_nivel"].str.replace(r"^\d+-", "", regex=True).str.strip()
df["nivel_nombre"] = base.map(ETIQUETAS).fillna(base.str.title())

# ---- Serie mensual (solo meses con datos informados) -------------------------
mensual = (
    df.groupby(["anho", "mes"])[
        ["cantidad_mensual", "cantidad_acumulada", "permanente", "contratado"]
    ]
    .sum()
    .reset_index()
)
mensual = mensual[mensual["cantidad_mensual"] > 0].copy()
mensual["fecha"] = pd.to_datetime(
    dict(year=mensual["anho"], month=mensual["mes"], day=1)
).dt.strftime("%Y-%m")
mensual["pct_contratado"] = (
    mensual["contratado"] / (mensual["permanente"] + mensual["contratado"]) * 100
).round(2)
for c in ["cantidad_mensual", "cantidad_acumulada", "permanente", "contratado"]:
    mensual[c] = mensual[c].astype(int)
mensual.to_csv(SALIDA / "dotacion_mensual.csv", index=False)

# ---- Serie anual --------------------------------------------------------------
ultimo_mes = mensual.groupby("anho")["mes"].max().rename("ultimo_mes")
anual = (
    mensual.groupby("anho")
    .agg(
        meses_informados=("mes", "count"),
        promedio_mensual=("cantidad_mensual", "mean"),
        prom_permanente=("permanente", "mean"),
        prom_contratado=("contratado", "mean"),
    )
    .join(ultimo_mes)
    .reset_index()
)
acum = mensual.merge(anual[["anho", "ultimo_mes"]], left_on=["anho", "mes"],
                     right_on=["anho", "ultimo_mes"])
anual = anual.merge(
    acum[["anho", "cantidad_acumulada"]].rename(
        columns={"cantidad_acumulada": "personas_distintas_anio"}
    ),
    on="anho",
)
anual["pct_contratado"] = (
    anual["prom_contratado"] / (anual["prom_permanente"] + anual["prom_contratado"]) * 100
).round(2)
anual["anio_completo"] = anual["meses_informados"] == 12
for c in ["promedio_mensual", "prom_permanente", "prom_contratado"]:
    anual[c] = anual[c].round(0).astype(int)
anual.to_csv(SALIDA / "dotacion_anual.csv", index=False)

# ---- Personas distintas por nivel institucional (mes de cierre de cada año) ---
cierre = df.merge(anual[["anho", "ultimo_mes"]], left_on=["anho", "mes"],
                  right_on=["anho", "ultimo_mes"])
por_nivel = (
    cierre.groupby(["anho", "nivel_nombre"])["cantidad_acumulada"].sum().reset_index()
    .rename(columns={"cantidad_acumulada": "personas_distintas_anio"})
)
por_nivel.to_csv(SALIDA / "dotacion_anual_nivel.csv", index=False)

print(anual.to_string(index=False))
