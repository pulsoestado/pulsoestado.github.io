"""
Genera las piezas gráficas para redes de la nota
"¿Cuántas personas cobran del Estado?":

  - flyer_1.png, flyer_2.png  (Instagram, 1080 x 1350, carrusel)
  - social.png                (tarjeta para X / Open Graph, 1200 x 630)
  - assets/img/social-default.png (tarjeta genérica del sitio)

Ejecutar desde la raíz del repositorio:  python scripts/flyer_dotacion.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parents[1]
POST = RAIZ / "posts/2026-10-09-cuantas-personas-cobran-del-estado"
FUENTES = RAIZ / "assets/fonts"
for f in FUENTES.glob("*.ttf"):
    fm.fontManager.addfont(str(f))

# --- Identidad visual -----------------------------------------------------------
NAVY, NARANJA, AZUL = "#0f2a44", "#eb6834", "#2a78d6"
PAPEL, TINTA, GRIS = "#fcfcfb", "#1b1b1a", "#5f5e5a"
SANS, SANS_SB, SANS_XB = "Inter", "Inter SemiBold", "Inter ExtraBold"
SERIF = "Source Serif 4 Bold"
URL = "pulsoestado.github.io"


def miles(x):
    return f"{x:,.0f}".replace(",", ".")


def coma(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


anual = pd.read_csv(RAIZ / "data/processed/dotacion_anual.csv")
s = anual[(anual.anho >= 2017) & anual.anio_completo]
a0, a1 = s.iloc[0], s.iloc[-1]
var = (a1.personas_distintas_anio / a0.personas_distintas_anio - 1) * 100
crec_c = (a1.prom_contratado / a0.prom_contratado - 1) * 100
crec_p = (a1.prom_permanente / a0.prom_permanente - 1) * 100


def lienzo(w, h, fondo=PAPEL):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    fig.patch.set_facecolor(fondo)
    return fig


def logo(fig, x, y, s, fondo=NAVY):
    """Isotipo (pulso) en coordenadas de figura."""
    ax = fig.add_axes([x, y, s, s * fig.get_figwidth() / fig.get_figheight()])
    ax.set_xlim(0, 64); ax.set_ylim(0, 64); ax.axis("off")
    ax.add_patch(FancyBboxPatch((2, 2), 60, 60, boxstyle="round,pad=0,rounding_size=13",
                                fc=fondo, ec="none"))
    xs = [8, 20, 25, 32, 39, 45, 56]; ys = [30, 30, 44, 18, 50, 30, 30]
    ax.plot(xs, ys, color=NARANJA, lw=3.2 * s / 0.06, solid_capstyle="round",
            solid_joinstyle="round")


def cabecera(fig, h_rel, etiqueta):
    fig.add_artist(plt.Rectangle((0, 1 - h_rel), 1, h_rel, transform=fig.transFigure,
                                 color=NAVY, zorder=0))
    logo(fig, 0.065, 1 - h_rel * 0.78, 0.065, fondo="#1d3d5f")
    fig.text(0.155, 1 - h_rel * 0.47, "Pulso del Estado", fontfamily=SERIF, fontsize=30,
             color="white", va="center")
    fig.text(0.935, 1 - h_rel * 0.47, etiqueta, fontfamily=SANS_SB, fontsize=17,
             color="#ffd2bf", va="center", ha="right")


def pie(fig, texto):
    fig.add_artist(plt.Rectangle((0, 0), 1, 0.075, transform=fig.transFigure, color=NAVY))
    fig.text(0.065, 0.0375, texto, fontfamily=SANS_SB, fontsize=17, color="white", va="center")
    fig.text(0.935, 0.0375, URL, fontfamily=SANS_SB, fontsize=17, color="#ffd2bf",
             va="center", ha="right")


def fuente(fig, y):
    fig.text(0.065, y, "Fuente: Pulso del Estado con datos de SICCA y SINARH. "
             "Personas distintas que cobraron al menos un mes en el año.",
             fontfamily=SANS, fontsize=13.5, color=GRIS, va="center")


def ejes_limpios(ax):
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#cfcdc6")
    ax.tick_params(length=0, labelsize=17, colors=GRIS)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_fontfamily(SANS)
    ax.set_facecolor(PAPEL)


# --- Flyer 1: cuántas personas --------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, 0.095, "SITUCAP · Dotación")
fig.text(0.065, 0.835, "En 2024 cobraron del Estado", fontfamily=SANS_SB, fontsize=34,
         color=TINTA)
fig.text(0.065, 0.745, miles(a1.personas_distintas_anio), fontfamily=SERIF, fontsize=104,
         color=NAVY, va="center")
fig.text(0.065, 0.665, "personas distintas", fontfamily=SANS_SB, fontsize=34, color=TINTA)
fig.text(0.065, 0.615, f"+{coma(var)}% que en 2017  ·  {miles(a1.personas_distintas_anio - a0.personas_distintas_anio)} personas más",
         fontfamily=SANS_SB, fontsize=24, color=NARANJA)

ax = fig.add_axes([0.065, 0.165, 0.87, 0.41])
colores = [NAVY if a == a1.anho else AZUL for a in s.anho]
ax.bar(s.anho, s.personas_distintas_anio / 1000, color=colores, width=0.62)
for a, v in zip(s.anho, s.personas_distintas_anio):
    if a in (a0.anho, a1.anho, 2020):
        ax.text(a, v / 1000 + 6, miles(v / 1000) + " mil", ha="center", fontfamily=SANS_SB,
                fontsize=16, color=TINTA)
ax.set_ylim(0, 430)
ax.set_yticks([])
ax.set_xticks(s.anho)
ax.set_xticklabels([str(a) for a in s.anho])
ejes_limpios(ax)
fuente(fig, 0.11)
pie(fig, "Análisis completo · link en bio")
fig.savefig(POST / "flyer_1.png", dpi=100, facecolor=PAPEL)
plt.close(fig)

# --- Flyer 2: contratados vs permanentes ---------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, 0.095, "SITUCAP · Vínculos")
fig.text(0.065, 0.835, "Los contratados crecieron", fontfamily=SANS_SB, fontsize=34,
         color=TINTA)
fig.text(0.065, 0.745, f"+{coma(crec_c, 0)}%", fontfamily=SERIF, fontsize=104, color=NARANJA,
         va="center")
fig.text(0.065, 0.665, f"frente a +{coma(crec_p, 0)}% de los permanentes (2017–2024)",
         fontfamily=SANS_SB, fontsize=30, color=TINTA)
fig.text(0.065, 0.615, f"Hoy {coma(a1.pct_contratado)}% de los vínculos son contratos "
         f"(en 2017: {coma(a0.pct_contratado)}%)", fontfamily=SANS_SB, fontsize=24, color=GRIS)

ax = fig.add_axes([0.065, 0.165, 0.72, 0.39])
idx_c = s.prom_contratado / a0.prom_contratado * 100
idx_p = s.prom_permanente / a0.prom_permanente * 100
ax.axhline(100, color="#cfcdc6", lw=1.5, ls=(0, (2, 3)))
for y, c, nombre in [(idx_c, NARANJA, "Contratados"), (idx_p, AZUL, "Permanentes")]:
    ax.plot(s.anho, y, color=c, lw=4, marker="o", ms=10, mec=PAPEL, mew=2.5)
    ax.text(s.anho.iloc[-1] + 0.3, y.iloc[-1], f"{nombre}\n{coma(y.iloc[-1], 0)}",
            fontfamily=SANS_XB, fontsize=19, color=c, va="center", linespacing=1.2)
ax.set_ylim(90, 155)
ax.set_xticks(s.anho[::2])
ax.set_yticks([100, 120, 140])
ejes_limpios(ax)
ax.grid(axis="y", color="#ebe9e3", lw=1)
ax.set_axisbelow(True)
fig.text(0.065, 0.575, "Índice 2017 = 100 · promedio mensual de vínculos", fontfamily=SANS,
         fontsize=16, color=GRIS)
fig.text(0.065, 0.11, "Fuente: Pulso del Estado con datos de SICCA y SINARH.",
         fontfamily=SANS, fontsize=13.5, color=GRIS, va="center")
pie(fig, "Análisis completo · link en bio")
fig.savefig(POST / "flyer_2.png", dpi=100, facecolor=PAPEL)
plt.close(fig)

# --- Tarjeta social del post (X / Open Graph) ----------------------------------
fig = lienzo(1200, 630, fondo=NAVY)
logo(fig, 0.05, 0.80, 0.05, fondo="#1d3d5f")
fig.text(0.115, 0.855, "Pulso del Estado", fontfamily=SERIF, fontsize=24, color="white",
         va="center")
fig.text(0.05, 0.64, "¿Cuántas personas\ncobran del Estado?", fontfamily=SERIF, fontsize=44,
         color="white", va="center", linespacing=1.1)
fig.text(0.05, 0.36, miles(a1.personas_distintas_anio), fontfamily=SERIF, fontsize=60,
         color=NARANJA, va="center")
fig.text(0.05, 0.22, f"personas en 2024 · +{coma(var)}% desde 2017", fontfamily=SANS_SB,
         fontsize=22, color="white", va="center")
fig.text(0.05, 0.08, URL, fontfamily=SANS_SB, fontsize=17, color="#ffd2bf", va="center")
ax = fig.add_axes([0.58, 0.14, 0.37, 0.58])
ax.bar(s.anho, s.personas_distintas_anio / 1000,
       color=[NARANJA if a == a1.anho else "#4f8fdc" for a in s.anho], width=0.62)
ax.set_ylim(0, 400); ax.axis("off")
fig.savefig(POST / "social.png", dpi=100, facecolor=NAVY)
plt.close(fig)

# --- Tarjeta genérica del sitio ------------------------------------------------
fig = lienzo(1200, 630, fondo=NAVY)
logo(fig, 0.06, 0.56, 0.13, fondo="#1d3d5f")
fig.text(0.06, 0.40, "Pulso del Estado", fontfamily=SERIF, fontsize=58, color="white",
         va="center")
fig.text(0.06, 0.26, "Dotación y masa salarial del sector público paraguayo",
         fontfamily=SANS_SB, fontsize=24, color="#ffd2bf", va="center")
fig.text(0.06, 0.10, URL, fontfamily=SANS_SB, fontsize=18, color="white", va="center")
fig.savefig(RAIZ / "assets/img/social-default.png", dpi=100, facecolor=NAVY)
plt.close(fig)
print("Listo")
