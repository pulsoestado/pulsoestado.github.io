"""
Utilidades compartidas por las notas de Pulso del Estado: rutas, formato de números en
estilo paraguayo, paleta y estilo de los gráficos interactivos (Plotly).

Uso en una nota (.qmd):
    import sys, pathlib
    raiz = next(p for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents] if (p / "_quarto.yml").exists())
    sys.path.insert(0, str(raiz / "scripts"))
    from pulso import *
"""
from pathlib import Path
import pandas as pd
import numpy as _np
_np.set_printoptions(legacy="1.25")  # los escalares se muestran como 12 y no como np.int64(12) en el texto en línea

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "processed"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MES_C = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Paleta (validada para daltonismo en el orden 1→3; ver skill de visualización)
AZUL, NARANJA, VERDE_AGUA = "#2a78d6", "#eb6834", "#1baf7a"
AMARILLO, ROJO, VIOLETA, NAVY, GRIS = "#eda100", "#e34948", "#4a3aa7", "#0f2a44", "#8a8984"
TINTA_GRAF = "#77766f"
CONFIG = {"displayModeBar": False, "locale": "es"}


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(DATOS / nombre)


# --- Formato -------------------------------------------------------------------------------
def miles(x, dec=0):
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def coma(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def pct(x, dec=1):
    return coma(x, dec) + "%"


def signo(x, f=None):
    f = f or miles
    return ("+" if x >= 0 else "−") + f(abs(x))


def spct(x, dec=1):
    return signo(x, lambda v: pct(v, dec))


def billones(gs, dec=1):
    """Guaraníes a 'billones' (millones de millones)."""
    return coma(gs / 1e12, dec)


def milmillones(gs, dec=0):
    return miles(gs / 1e9, dec)


def millones(gs, dec=1):
    return coma(gs / 1e6, dec)


def kpis(tiles):
    """tiles = [(valor, etiqueta), …] → HTML de tarjetas (usar con #| output: asis)."""
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="valor">{v}</div><div class="etiqueta">{e}</div></div>'
        for v, e in tiles) + "</div>"


# --- Gráficos ---------------------------------------------------------------------------------
def estilo(fig, alto=380, leyenda=True):
    fig.update_layout(
        height=alto, margin=dict(l=10, r=20, t=10, b=10),
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=TINTA_GRAF),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        separators=",.", hovermode="x unified", showlegend=leyenda,
        hoverlabel=dict(font=dict(family="Inter, sans-serif")),
        legend=dict(orientation="h", y=1.1, x=0, title=None),
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(128,128,128,.4)", ticks="", fixedrange=True)
    fig.update_yaxes(gridcolor="rgba(128,128,128,.18)", zeroline=False, ticks="", fixedrange=True)
    return fig


def barras_h(etiquetas, valores, textos, colores=None, alto=None, hover=None, rango=None):
    """Barras horizontales ordenadas, con etiqueta de valor al final de cada barra."""
    import plotly.graph_objects as go
    colores = colores or [AZUL if v >= 0 else ROJO for v in valores]
    fig = go.Figure(go.Bar(
        y=etiquetas, x=valores, orientation="h", marker_color=colores, marker_line_width=0,
        text=textos, textposition="outside", textfont=dict(color=TINTA_GRAF), cliponaxis=False,
        hovertemplate=hover or "<b>%{y}</b>: %{text}<extra></extra>",
    ))
    estilo(fig, alto=alto or 60 + 34 * len(etiquetas), leyenda=False).update_layout(
        hovermode="closest", bargap=0.35, margin=dict(l=10, r=40, t=10, b=10))
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,.18)", zeroline=True,
                     zerolinecolor="rgba(128,128,128,.5)", range=rango)
    fig.update_yaxes(showgrid=False)
    return fig


def etiqueta_final(fig, x, y, texto, color, yshift=0):
    """Etiqueta directa al final de una línea."""
    fig.add_annotation(x=x, y=y, text=f"<b>{texto}</b>", xanchor="left", xshift=8, yshift=yshift,
                       showarrow=False, font=dict(color=color, size=13))


# --- Nombres de instituciones -----------------------------------------------------------------
_NOMBRES = {
    "MINISTERIO DE EDUCACION Y CIENCIAS": "Ministerio de Educación y Ciencias",
    "MINISTERIO DE SALUD PUBLICA Y BIENESTAR SOCIAL": "Ministerio de Salud Pública y Bienestar Social",
    "POLICIA NACIONAL": "Policía Nacional",
    "INSTITUTO DE PREVISION SOCIAL": "Instituto de Previsión Social",
    "CORTE SUPREMA DE JUSTICIA": "Corte Suprema de Justicia",
    "MINISTERIO PUBLICO": "Ministerio Público",
    "FACULTAD DE CIENCIAS MEDICAS": "Facultad de Ciencias Médicas (UNA)",
    "MINISTERIO DE DEFENSA NACIONAL": "Ministerio de Defensa Nacional",
    "UNIVERSIDAD NACIONAL DE ASUNCION": "Universidad Nacional de Asunción",
    "ADMINISTRACION NACIONAL DE ELECTRICIDAD": "ANDE",
}


_MUNICIPIOS = {
    "ENCARNACION": "Encarnación", "CAPIATA": "Capiatá", "LAMBARE": "Lambaré", "ITAUGUA": "Itauguá",
    "CONCEPCION": "Concepción", "PEDRO J. CABALLERO": "Pedro Juan Caballero", "CAAGUAZU": "Caaguazú",
    "PARAGUARI": "Paraguarí", "ITA": "Itá", "AREGUA": "Areguá", "YPANE": "Ypané", "CAACUPE": "Caacupé",
    "MINGA GUAZU": "Minga Guazú", "NEMBY": "Ñemby", "SAN JUAN BAUTISTA": "San Juan Bautista",
    "FERNANDO DE LA MORA": "Fernando de la Mora", "CIUDAD DEL ESTE": "Ciudad del Este",
}


def nombre(oee: str) -> str:
    """Nombre legible de una institución a partir de su descripción en los registros."""
    import re, unicodedata
    base = re.sub(r"^\s*\d+\s*-\s*", "", str(oee))
    sigla = re.search(r"\(([^)]*)\)\s*$", base)
    base = re.sub(r"\s*\([^)]*\)\s*$", "", base).strip()
    clave = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode().upper()
    if clave in _NOMBRES:
        return _NOMBRES[clave]
    if clave.startswith("MUNICIPALIDAD DE "):
        lugar = clave[len("MUNICIPALIDAD DE "):]
        if lugar in _MUNICIPIOS:
            return _MUNICIPIOS[lugar]
        t = " ".join(base[len("MUNICIPALIDAD DE "):].split()).title()
        t = t.replace(" De ", " de ").replace(" Del ", " del ").replace(" La ", " la ").replace(" El ", " el ")
        return " ".join(_TILDES.get(w, w) for w in t.split(" "))
    if clave in _ESPECIALES:
        return _ESPECIALES[clave]
    base = re.sub(r"^[IVX]+ DEPARTAMENTO:\s*", "", base, flags=re.I)
    base = re.sub(r"^GOBIERNO DEPARTAMENTAL DE ", "GOBERNACION DE ", base, flags=re.I)
    t = base.title()
    for a in [" De ", " Del ", " La ", " Las ", " Los ", " Y ", " El ", " Para ", " Por ", " En ", " E ", " A ", " Con ", " Al "]:
        t = t.replace(a, a.lower())
    t = " ".join(_TILDES.get(w, w) for w in t.split(" "))
    return t + (f" ({sigla.group(1)})" if sigla else "")


_ESPECIALES = {
    "DIRECC.GRAL.DE ESTAD.ENC.Y CENSOS": "Dirección General de Estadística, Encuestas y Censos",
    "SEC. NAC.POR LOS DDHH DE LAS PERS.CON DISCAPACIDAD": "SENADIS",
    "SRIA.DE DESARROLLO P/ REPATRIADOS Y REFUGIADOS CONNACIONALES": "Secretaría de Repatriados",
    "SECRETARIA NAC. DE ADM. DE BIENES INCAUTADOS Y COMISADOS": "SENABICO",
    "SECRETARIA NACIONAL DE TECNOLOGIAS DE LA INF. Y COM.": "SENATICs",
}

_TILDES = {w.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u"): w
           for w in """Pública Público Públicas Públicos República Cámara Compañía Dirección Aeronáutica Economía
Espíritu Educación Tecnología Información Comunicación Comunicaciones Asunción Concepción Nación Eléctrica
Administración Promoción Policía Secretaría Energía Técnica Técnico Crédito Inclusión Acción Planificación
Indígena Contraloría Garantía Científica Investigación Hábitat Gobernación Itapúa Paraná Guairá Caaguazú
Caazapá Paraguarí Ñeembucú Canindeyú Boquerón Médicas Químicas Económicas Jurídicas Políticas Odontología
Filosofía Ingeniería Agronómicas Tecnológico Tecnológica Ganadería Jubilación Previsión Pensión Pensiones
Política Ejército Armada Aérea Fármacos Biológicas Agrícola Bioquímica Física Matemática Estadística Geografía
Turístico Turística Química Electrónica Cooperación Instrucción Producción Integración Atención Inversión Gestión
Prevención Formación Capacitación Regulación Coordinación Ejecución Supervisión Protección Promoción Innovación
Electoral Aduanas Comisión Cooperativo Marítima Hídricos Minería Nuclear Ciencias Género Niñez Lingüísticas
Única Médica Farmacéutica Veterinarias Exactas Diseño""".split()}
_TILDES.update({"Compañia": "Compañía", "Linguisticas": "Lingüísticas", "Linguistica": "Lingüística",
                "Nuñez": "Núñez", "Navegacion": "Navegación", "Petroleos": "Petróleos",
                "Normalizacion": "Normalización", "Artesania": "Artesanía", "Transito": "Tránsito",
                "Evaluacion": "Evaluación", "Acreditacion": "Acreditación", "Radiologica": "Radiológica",
                "Estadisticas": "Estadísticas", "Prestamos": "Préstamos", "Defensoria": "Defensoría",
                "Habilitacion": "Habilitación", "Tecnologias": "Tecnologías", "Funcion": "Función",
                "Anticorrupcion": "Anticorrupción", "Procuraduria": "Procuraduría", "Auditoria": "Auditoría",
                "Escribania": "Escribanía", "Sinfonica": "Sinfónica", "Musica": "Música",
                "Politecnica": "Politécnica", "Ande": "ANDE"})
_TILDES.update({w.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u"): w
                for w in """Humaitá Yguazú Lázaro José Simón Bolívar Unión Guazú Tomás Ypacaraí Ybycuí Itacurubí
Ygatimí María Belén Asunción Paraná Guaraní Jesús Martín Ramón Julián Andrés Hernández Hernández Pirapó
Itakyry Ñacunday Tavaí Yhú Ñumí Tebicuarymí Mbuyapey Quiindy Caapucú Ybytymí Itá Arroyos Tobatí Atyrá
Emboscada Altos Ñemby Areguá Capiatá Limpio Itauguá Ypané Guarambaré Villeta Nueva Colombia Mbocayaty
Iturbe Natalicio Talavera Félix Pérez Cardozo Eusebio Ayala Isla Puku Caazapá Abaí Yuty Maciel Fulgencio
Yegros Tavapy Ybyrarobaná Curuguaty Ypehú Corpus Christi Katueté Carayaó Coronel Oviedo Vaquería Raúl
Repatriación Mariscal Estigarribia Fuerte Olimpo Bahía Negra Puerto Casado Pinasco Ayolas Villa Florida
Santiago Quiteria Tacuaras Humaitá Mayor Martínez Desmochados Cerrito Isla Umbú Laureles Pilar Paso Oliva""".split()})


# --- Ayudas para las notas de 2027 ----------------------------------------------------------------
K_OEE = ["codigo_nivel", "codigo_entidad", "codigo_oee"]


def ultimo_mes():
    """(año, mes) del último mes con vínculos y masa salarial."""
    v = leer("vinculos_mensual_sector.csv")
    m = leer("masa_mensual_sector.csv")
    a = sorted(set(zip(v.anho, v.mes)) & set(zip(m.anho, m.mes)))[-1]
    return int(a[0]), int(a[1])


def ultimo_anio_completo():
    """Último año con los 12 meses de vínculos y de masa salarial."""
    v = leer("vinculos_mensual_sector.csv").groupby("anho").mes.nunique()
    m = leer("masa_mensual_sector.csv").groupby("anho").mes.nunique()
    return int(max(a for a in v.index if v[a] == 12 and m.get(a, 0) == 12))


def fecha_txt(anho, mes):
    return f"{MESES[int(mes) - 1]} de {int(anho)}"


def instituciones():
    return leer("instituciones.csv")


def vin_oee():
    """Vínculos por mes e institución, con nombre y sector."""
    return leer("vinculos_mensual_oee.csv").merge(
        instituciones()[K_OEE + ["nombre", "nombre_largo", "sector", "nivel", "descripcion_entidad", "descripcion_oee"]],
        on=K_OEE, how="left")


def vin_promedio_oee(anho):
    """Promedio mensual de vínculos de cada institución en un año."""
    v = vin_oee()
    v = v[v.anho == anho]
    g = v.groupby(K_OEE + ["nombre", "nombre_largo", "sector", "nivel", "descripcion_entidad"])
    out = g[["permanente", "contratado", "mujeres", "total"]].mean()
    out["meses"] = g.mes.nunique()
    return out.reset_index()


def masa_oee_anual(anho=None):
    """Masa salarial anual por institución (total y por componente, columnas anchas)."""
    m = leer("masa_anual_oee.csv")
    if anho is not None:
        m = m[m.anho == anho]
    w = m.pivot_table(index=["anho"] + K_OEE, columns="componente", values="devengado",
                      aggfunc="sum", fill_value=0)
    w["masa"] = w.sum(axis=1)
    w = w.reset_index()
    return w.merge(instituciones()[K_OEE + ["nombre", "nombre_largo", "sector", "nivel", "descripcion_entidad"]],
                   on=K_OEE, how="left")


def ipc_interanual(anho, mes):
    """Inflación interanual del mes (data/manual/ipc_interanual.csv) o None."""
    d = pd.read_csv(RAIZ / "data/manual/ipc_interanual.csv")
    f = d[(d.anho == anho) & (d.mes == mes)]
    return None if f.empty else float(f.ipc_interanual.iloc[0])


def deflactor(base):
    """Serie para pasar guaraníes de cada año a guaraníes del año `base` (IPC promedio anual del BCP)."""
    b = leer("ipc_salarios_bcp.csv").set_index("anho")["ipc"]
    return b.loc[base] / b


def serie_mensual(sector=None):
    """Vínculos totales por mes (todo el Estado o un sector), con columna fecha."""
    v = leer("vinculos_mensual_sector.csv")
    if sector:
        v = v[v.sector == sector]
    s = v.groupby(["anho", "mes"])[["permanente", "contratado", "mujeres", "total"]].sum().reset_index()
    s["fecha"] = pd.to_datetime(dict(year=s.anho, month=s.mes, day=1))
    return s


def ficha_html(filas):
    """Tabla compacta de dos columnas: [(etiqueta, valor), …]."""
    return "| | |\n|---|--:|\n" + "\n".join(f"| {a} | {b} |" for a, b in filas)


# --- Estimaciones rotuladas (para notas sobre meses que todavía no tienen datos) ---------------------
def _proyectar(s, hasta):
    """s: Serie mensual indexada por Timestamp (primer día del mes). Extiende hasta `hasta` con el
    mismo mes del año anterior × el crecimiento interanual de los últimos 12 meses observados."""
    s = s.sort_index().copy()
    ult = s.index.max()
    if hasta <= ult:
        return s, pd.Series(False, index=s.index)
    base = s.loc[ult - pd.DateOffset(months=11):ult].sum()
    prev = s.loc[ult - pd.DateOffset(months=23):ult - pd.DateOffset(months=12)].sum()
    g = base / prev if prev else 1.0
    est = pd.Series(False, index=s.index)
    f = ult
    while f < hasta:
        f = f + pd.DateOffset(months=1)
        s.loc[f] = s.loc[f - pd.DateOffset(months=12)] * g
        est.loc[f] = True
    return s.sort_index(), est.sort_index()


def ultimo_mes_confiable(umbral=0.97):
    """Último mes en que reportó al menos el 97% de las instituciones que reportaron el mismo mes del año
    anterior (antes de eso, la carga tardía —sobre todo de municipalidades— achica los totales)."""
    v = leer("vinculos_mensual_oee.csv")
    n = v[v.total > 0].groupby(["anho", "mes"]).size()
    for a, m in sorted(n.index, reverse=True):
        if (a - 1, m) in n.index and n[(a, m)] >= umbral * n[(a - 1, m)]:
            return int(a), int(m)
    return ultimo_mes()


def serie_extendida(anho, mes, sector=None):
    """Vínculos por mes (total, permanente, contratado, mujeres) hasta (anho, mes). Los meses posteriores
    al último mes confiable se estiman y quedan marcados en la columna `estimado`."""
    s = serie_mensual(sector)
    ac, mc = ultimo_mes_confiable()
    s = s[(s.anho * 100 + s.mes) <= ac * 100 + mc].set_index("fecha")
    hasta = pd.Timestamp(year=int(anho), month=int(mes), day=1)
    out, est = {}, None
    for c in ["total", "permanente", "contratado", "mujeres"]:
        out[c], e = _proyectar(s[c].astype(float), hasta)
        est = e if est is None else est
    d = pd.DataFrame(out)
    d["estimado"] = est.reindex(d.index).fillna(False).astype(bool)
    d["anho"], d["mes"] = d.index.year, d.index.month
    return d.reset_index().rename(columns={"index": "fecha"})


def masa_extendida(anho, mes, sector=None):
    """Masa salarial devengada por mes hasta (anho, mes), con meses estimados marcados."""
    m = leer("masa_mensual_sector.csv")
    if sector:
        m = m[m.sector == sector]
    m = m.groupby(["anho", "mes"]).devengado.sum().reset_index()
    ac, mc = ultimo_mes_confiable()
    m = m[(m.anho * 100 + m.mes) <= ac * 100 + mc]
    m["fecha"] = pd.to_datetime(dict(year=m.anho, month=m.mes, day=1))
    s, e = _proyectar(m.set_index("fecha").devengado.astype(float), pd.Timestamp(year=int(anho), month=int(mes), day=1))
    d = pd.DataFrame({"devengado": s, "estimado": e.reindex(s.index).fillna(False).astype(bool)})
    d["anho"], d["mes"] = d.index.year, d.index.month
    return d.reset_index().rename(columns={"index": "fecha"})


def aviso_estimacion(texto):
    """Recuadro visible de estimación provisoria (usar con #| output: asis)."""
    print(f"::: {{.callout-warning}}\n**Estimación provisoria.** {texto} La nota se recalcula sola con los datos reales "
          "cuando estén cargados.\n:::\n")


def hay_datos(anho, mes):
    a, m = ultimo_mes()
    return (a, m) >= (int(anho), int(mes))
