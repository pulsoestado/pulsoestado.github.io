"""
Publicación programada: oculta las notas cuya fecha (`date:`) todavía no llegó.

Recorre posts/*/index.qmd y situcap/ediciones/*/index.qmd. Si la fecha de la nota es
posterior a hoy (hora de Asunción), agrega `draft: true  # programada` a su encabezado;
si la fecha ya llegó, quita esa línea. Las notas con `draft: true` puesto a mano
(sin el comentario `# programada`) no se tocan.

Requisitos de datos (opcional). Una nota puede declarar en su encabezado:

    requiere:
      datos: "2026-11"      # ese mes debe estar en data/processed (vínculos y masa salarial)
      ipc: "2026-11"        # esa inflación interanual debe estar en data/manual/ipc_interanual.csv
      archivo: "data/manual/poblacion_departamentos.csv"   # ese archivo debe existir

Si la fecha llegó pero falta algún requisito, la nota sigue oculta y se informa como
"pendiente". Así una nota nunca sale con datos que todavía no existen, y el sitio se
sigue generando sin errores.

Lo ejecuta la GitHub Action antes de generar el sitio, todos los días. También se puede
correr a mano:  python scripts/programar_publicaciones.py  (o con una fecha de prueba: ... 2027-03-31)

Adelantos del plan 2028–2030. Las notas con `plan: "2028-2030"` en el encabezado se
publican ya, antes de su fecha, en la sección /plan-2028-2030/ (no en la portada ni en el
RSS) y con un recuadro que avisa que son un adelanto. Si les falta un requisito de datos,
siguen ocultas. Cuando llega su fecha, el script les quita la marca `plan:` y el recuadro,
y pasan solas al listado principal.

Con la opción --retirar (solo en la GitHub Action), además borra de la copia de trabajo
las carpetas de las notas ocultas. Quarto ejecuta el código de todos los .qmd del proyecto,
aunque sean borradores: retirarlas evita que una nota que espera datos haga fallar la
generación del sitio y acorta el proceso. Nunca la uses en tu copia local: borra las notas.
"""
import datetime as dt
import re
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
MARCA = "draft: true  # programada"
MESES_TXT = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
             "octubre", "noviembre", "diciembre"]
INI, FIN = "<!-- adelanto-plan -->", "<!-- /adelanto-plan -->"


def recuadro(fecha):
    f = f"{fecha.day} de {MESES_TXT[fecha.month - 1]} de {fecha.year}"
    return (f"{INI}\n::: {{.callout-note}}\n## Adelanto del plan 2028–2030\n"
            f"Esta nota está programada para el **{f}**. La publicamos antes como adelanto del plan editorial: "
            "usa los últimos datos disponibles y, donde faltan, estimaciones rotuladas como tales. "
            "Cuando lleguen los datos de su fecha se recalcula sola y pasa al listado principal. "
            f"[Ver todo el plan](/plan-2028-2030/).\n:::\n{FIN}\n\n")
hoy = dt.datetime.now(ZoneInfo("America/Asuncion")).date()
RETIRAR = "--retirar" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if args:
    hoy = dt.date.fromisoformat(args[0])


def _meses(archivo, cols=("anho", "mes")):
    try:
        d = pd.read_csv(archivo, usecols=list(cols))
        return {f"{int(a):04d}-{int(m):02d}" for a, m in zip(d[cols[0]], d[cols[1]])}
    except (FileNotFoundError, ValueError):
        return set()


MESES_DATOS = (_meses(RAIZ / "data/processed/vinculos_mensual_sector.csv")
               & _meses(RAIZ / "data/processed/masa_mensual_sector.csv"))
MESES_IPC = _meses(RAIZ / "data/manual/ipc_interanual.csv")


def faltantes(req):
    if not isinstance(req, dict):
        return []
    f = []
    if req.get("datos") and str(req["datos"]) not in MESES_DATOS:
        f.append(f"datos de {req['datos']}")
    if req.get("ipc") and str(req["ipc"]) not in MESES_IPC:
        f.append(f"IPC de {req['ipc']}")
    for a in ([req["archivo"]] if isinstance(req.get("archivo"), str) else req.get("archivo") or []):
        if not (RAIZ / a).exists():
            f.append(a)
    return f


def flyers(carpeta, texto):
    """Nombres de los flyers de una nota: los que ya están en la carpeta y los que genera su celda `redes`."""
    n = {p.name for p in carpeta.glob("*.png")}
    if re.search(r"\bsocial\(", texto):
        n.add("social.png")
    if re.search(r"\big_portada\(", texto):
        n.add("ig_1.png")
    n |= {f"ig_{k}.png" for k in re.findall(r"\big_dato\(\s*(\d+)", texto)}
    orden = lambda s: (s != "social.png", s)
    return sorted(n, key=orden)


archivos = sorted(RAIZ.glob("posts/*/index.qmd")) + sorted(RAIZ.glob("situcap/ediciones/*/index.qmd"))
pendientes = []
agenda = []
for f in archivos:
    texto = f.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", texto, flags=re.S)
    if not m:
        continue
    cab = m.group(1)
    fecha = re.search(r"^date:\s*['\"]?(\d{4}-\d{2}-\d{2})", cab, flags=re.M)
    if not fecha:
        continue
    fecha = dt.date.fromisoformat(fecha.group(1))
    lineas = [l for l in cab.split("\n") if l.strip() != MARCA]
    try:
        meta = yaml.safe_load("\n".join(lineas)) or {}
    except yaml.YAMLError:
        meta = {}
    falta = faltantes(meta.get("requiere"))
    plan = bool(meta.get("plan"))
    adelanto = plan and fecha > hoy and not falta
    oculta = (fecha > hoy and not adelanto) or bool(falta)
    if plan and fecha <= hoy:
        lineas = [l for l in lineas if not l.startswith("plan:")]   # llegó su fecha: pasa al listado principal
    if oculta:
        lineas.append(MARCA)
    nueva = "\n".join(lineas)
    cuerpo = texto[m.end():]
    if INI in cuerpo:
        i, j = cuerpo.index(INI), cuerpo.index(FIN) + len(FIN)
        cuerpo = (cuerpo[:i] + cuerpo[j:]).lstrip("\n")
    if adelanto:
        cuerpo = recuadro(fecha) + cuerpo.lstrip("\n")
    else:
        cuerpo = "\n" + cuerpo if not cuerpo.startswith("\n") else cuerpo
    nuevo_texto = "---\n" + nueva + "\n---\n" + cuerpo
    if nuevo_texto != texto:
        f.write_text(nuevo_texto, encoding="utf-8")
    if fecha <= hoy and falta:
        estado = "PENDIENTE"
        pendientes.append(f"{fecha}  {f.parent.name}: falta {', '.join(falta)}")
    else:
        estado = "programada" if oculta else ("adelanto" if adelanto else "publicada")
    print(f"{fecha}  {estado:10s}  {f.parent.name}")
    red = meta.get("redes") or fecha
    ruta = f.parent.relative_to(RAIZ).as_posix()
    agenda.append({"redes": str(red)[:10], "titulo": meta.get("title", ""), "ruta": ruta,
                   "estado": ("en el sitio (adelanto del plan)" if adelanto else "en el sitio") if not oculta else ("programada" if fecha > hoy else "espera datos"),
                   "flyers": " ".join(flyers(f.parent, texto))})
    if oculta and RETIRAR:
        shutil.rmtree(f.parent)

# Agenda de redes: qué flyer publicar cada día en Instagram y X (página /redes/ del sitio)
ag = pd.DataFrame(agenda).sort_values(["redes", "ruta"])
(RAIZ / "redes").mkdir(exist_ok=True)
ag.to_csv(RAIZ / "redes" / "agenda.csv", index=False)
URL = "https://pulsoestado.github.io/"
for _, r in ag[ag.redes == str(hoy)].iterrows():
    aviso = f"Hoy en redes: {r.titulo} · {URL}{r.ruta}/"
    print(f"\n{aviso}" + ("" if r.estado.startswith("en el sitio") else f"  (la nota todavía no está en el sitio: {r.estado})"))
    print(f"::notice::{aviso}")

if pendientes:
    print("\nNotas con fecha cumplida que esperan datos:")
    print("\n".join("  " + p for p in pendientes))
    # En GitHub Actions, deja un aviso visible en el resumen de la ejecución
    print("\n".join(f"::warning::{p}" for p in pendientes))
