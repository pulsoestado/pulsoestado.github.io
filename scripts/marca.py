"""
Elementos de marca compartidos para las piezas gráficas (flyers y tarjetas).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parents[1]
for f in (RAIZ / "assets/fonts").glob("*.ttf"):
    fm.fontManager.addfont(str(f))

NAVY, NARANJA, AZUL, ROJO = "#0f2a44", "#eb6834", "#2a78d6", "#e34948"
PAPEL, TINTA, GRIS, GRILLA = "#fcfcfb", "#1b1b1a", "#5f5e5a", "#ebe9e3"
SANS, SANS_SB, SANS_XB = "Inter", "Inter SemiBold", "Inter ExtraBold"
SERIF = "Source Serif 4 Bold"
URL = "pulsoestado.github.io"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def miles(x):
    return f"{x:,.0f}".replace(",", ".")


def coma(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def lienzo(w, h, fondo=PAPEL):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    fig.patch.set_facecolor(fondo)
    return fig


def logo(fig, x, y, s, fondo=NAVY):
    ax = fig.add_axes([x, y, s, s * fig.get_figwidth() / fig.get_figheight()])
    ax.set_xlim(0, 64); ax.set_ylim(0, 64); ax.axis("off")
    ax.add_patch(FancyBboxPatch((2, 2), 60, 60, boxstyle="round,pad=0,rounding_size=13",
                                fc=fondo, ec="none"))
    ax.plot([8, 20, 25, 32, 39, 45, 56], [30, 30, 44, 18, 50, 30, 30], color=NARANJA,
            lw=3.2 * s / 0.06, solid_capstyle="round", solid_joinstyle="round")


def cabecera(fig, etiqueta, h_rel=0.095):
    fig.add_artist(plt.Rectangle((0, 1 - h_rel), 1, h_rel, transform=fig.transFigure,
                                 color=NAVY, zorder=0))
    logo(fig, 0.065, 1 - h_rel * 0.78, 0.065, fondo="#1d3d5f")
    fig.text(0.155, 1 - h_rel * 0.47, "Pulso del Estado", fontfamily=SERIF, fontsize=30,
             color="white", va="center")
    fig.text(0.935, 1 - h_rel * 0.47, etiqueta, fontfamily=SANS_SB, fontsize=17,
             color="#ffd2bf", va="center", ha="right")


def pie(fig, texto="Análisis completo · link en bio"):
    fig.add_artist(plt.Rectangle((0, 0), 1, 0.075, transform=fig.transFigure, color=NAVY))
    fig.text(0.065, 0.0375, texto, fontfamily=SANS_SB, fontsize=17, color="white", va="center")
    fig.text(0.935, 0.0375, URL, fontfamily=SANS_SB, fontsize=17, color="#ffd2bf",
             va="center", ha="right")


def fuente(fig, texto, y=0.11):
    fig.text(0.065, y, texto, fontfamily=SANS, fontsize=13.5, color=GRIS, va="center")


def ejes_limpios(ax, grilla_y=False):
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#cfcdc6")
    ax.tick_params(length=0, labelsize=17, colors=GRIS)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_fontfamily(SANS)
    ax.set_facecolor(PAPEL)
    if grilla_y:
        ax.grid(axis="y", color=GRILLA, lw=1)
        ax.set_axisbelow(True)
