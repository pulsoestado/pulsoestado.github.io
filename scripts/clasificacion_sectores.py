"""
Clasificación sectorial de Pulso del Estado (versión 1, a validar).

Asigna cada institución (OEE) a un sector a partir del nivel presupuestario,
la entidad y el nombre del OEE. Funciona con los archivos DW (funcionarios,
presupuesto, nivel y categoría) y con el resumen de personas, aunque escriban
los nombres con o sin prefijo numérico y con o sin tildes.

Sectores:
  Educación                     MEC + universidades nacionales
  Salud                         Ministerio de Salud + IPS
  Fuerzas públicas              Policía Nacional + Ministerio de Defensa Nacional
  Servicio civil del Ejecutivo  resto del Poder Ejecutivo (incluye Presidencia,
                                Vicepresidencia y sus secretarías)
  Poder Legislativo, Poder Judicial, Municipalidades, Gobiernos departamentales,
  Entes autónomos y autárquicos, Empresas públicas, SA del Estado
  Otros organismos              Contraloría, Banco Central, entidades financieras
                                oficiales, cajas de jubilación y otros organismos
"""
import re
import unicodedata
import pandas as pd

SECTORES = [
    "Educación", "Salud", "Fuerzas públicas", "Servicio civil del Ejecutivo",
    "Poder Legislativo", "Poder Judicial", "Municipalidades", "Gobiernos departamentales",
    "Entes autónomos y autárquicos", "Empresas públicas", "SA del Estado", "Otros organismos",
]
SECTORES_CORTOS = {
    "Servicio civil del Ejecutivo": "Servicio civil",
    "Entes autónomos y autárquicos": "Entes autónomos",
    "Gobiernos departamentales": "Gobernaciones",
}


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"^\s*\d+\s*-\s*", "", s)          # prefijo numérico "005-"
    return re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()  # sigla final "(MDN)"


def sector(nivel, entidad, oee) -> str:
    n, e, o = _norm(nivel), _norm(entidad), _norm(oee)
    if "UNIVERSIDADES NACIONALES" in n or o.startswith("MINISTERIO DE EDUCACION Y C"):
        return "Educación"
    if o.startswith("MINISTERIO DE SALUD PUBLICA") or "INSTITUTO DE PREVISION SOCIAL" in o:
        return "Salud"
    if o.startswith("POLICIA NACIONAL") or o == "MINISTERIO DE DEFENSA NACIONAL":
        return "Fuerzas públicas"
    if "PODER EJECUTIVO" in n:
        return "Servicio civil del Ejecutivo"
    if "PODER LEGISLATIVO" in n:
        return "Poder Legislativo"
    if "PODER JUDICIAL" in n:
        return "Poder Judicial"
    if "MUNICIPALIDADES" in n:
        return "Municipalidades"
    if "GOBIERNOS DEPARTAMENTALES" in n:
        return "Gobiernos departamentales"
    if "ENTES AUTONOMOS" in n:
        return "Entes autónomos y autárquicos"
    if "EMPRESAS PUBLICAS" in n:
        return "Empresas públicas"
    if "SOCIEDADES ANONIMAS" in n:
        return "SA del Estado"
    return "Otros organismos"


def clasificar(df: pd.DataFrame, nivel="descripcion_nivel", entidad="descripcion_entidad",
               oee="descripcion_oee"):
    """Devuelve un array con el sector de cada fila de df."""
    claves = df[[nivel, entidad, oee]].drop_duplicates().copy()
    claves["sector"] = [sector(a, b, c) for a, b, c in claves.itertuples(index=False)]
    return df[[nivel, entidad, oee]].merge(claves, on=[nivel, entidad, oee], how="left")["sector"].values
