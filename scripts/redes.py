"""
Piezas para redes generadas por la propia nota al momento de renderizarse.

Cada nota de 2027 termina con una celda oculta que llama a estas funciones con sus propias
cifras. Así la tarjeta de X (social.png) y las láminas de Instagram (ig_*.png) siempre
coinciden con el texto, también cuando los datos se actualizan.

    from redes import social, ig_portada, ig_dato, lineas, barras_h, barras
    social("Título corto", "12,3%", "bajada en una línea", serie=(x, y))
    ig_portada("El dato de la semana", "Título\nen tres\nlíneas", "Bajada", serie=(x, y))
    ig_dato(2, "Etiqueta", "Frase de entrada", "12,3%", "frase de cierre", "nota pequeña",
            barras_h(etiquetas, valores, textos))

Los archivos se guardan en la carpeta de la nota (el directorio de trabajo al renderizar).
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from marca import (NAVY, NARANJA, AZUL, PAPEL, TINTA, GRIS, SANS, SANS_SB, SANS_XB, SERIF, URL,
                   lienzo, logo, cabecera, pie, fuente, ejes_limpios, coma)

VERDE, AMARILLO = "#1baf7a", "#eda100"
FUENTE = "Fuente: Pulso del Estado con datos de SINARH y SICCA."


def _guardar(fig, nombre, fondo=PAPEL, carpeta="."):
    fig.savefig(Path(carpeta) / nombre, dpi=100, facecolor=fondo)
    plt.close(fig)


def _mini(ax, serie, color, fondo, tipo="linea"):
    x, y = serie
    if tipo == "barras":
        apagado = "#3f5f82" if fondo == NAVY else "#c9d3df"
        ax.bar(range(len(y)), y, color=[apagado] * (len(y) - 1) + [color], width=0.7)
        ax.axhline(0, color=apagado, lw=1)
    else:
        ax.plot(x, y, color=color, lw=4.5, solid_capstyle="round")
        ax.scatter([x[-1]], [y[-1]], s=150, color=color, edgecolor=fondo, linewidth=3, zorder=3)
    ax.set_facecolor(fondo)
    ax.axis("off")


def social(titulo, grande, bajada, serie=None, color=NARANJA, tipo="linea", carpeta="."):
    """Tarjeta 1200 x 630 para X y Open Graph."""
    fig = lienzo(1200, 630, fondo=NAVY)
    logo(fig, 0.05, 0.80, 0.05, fondo="#1d3d5f")
    fig.text(0.115, 0.855, "Pulso del Estado", fontfamily=SERIF, fontsize=24, color="white", va="center")
    n = titulo.count("\n") + 1
    fig.text(0.05, 0.62, titulo, fontfamily=SERIF, fontsize=42 if n < 3 else 36, color="white",
             va="center", linespacing=1.08)
    fig.text(0.05, 0.355, grande, fontfamily=SERIF, fontsize=58, color=color, va="center")
    _ajustar(fig, 0.05, 0.22, bajada, 20, ancho=0.9, minimo=0.7, dos_lineas=False, fontfamily=SANS_SB, color="white", va="center")
    fig.text(0.05, 0.08, URL, fontfamily=SANS_SB, fontsize=17, color="#ffd2bf", va="center")
    if serie is not None:
        _mini(fig.add_axes([0.60, 0.20, 0.36, 0.50]), serie, color, NAVY, tipo)
    _guardar(fig, "social.png", NAVY, carpeta)


def ig_portada(kicker, titulo, bajada, serie=None, color=NARANJA, tipo="linea", deslizar=True, carpeta="."):
    """Primera lámina del carrusel (1080 x 1350)."""
    fig = lienzo(1080, 1350, fondo=NAVY)
    logo(fig, 0.065, 0.86, 0.075, fondo="#1d3d5f")
    fig.text(0.16, 0.888, "Pulso del Estado", fontfamily=SERIF, fontsize=32, color="white", va="center")
    fig.text(0.065, 0.80, kicker.upper(), fontfamily=SANS_SB, fontsize=20, color="#ffd2bf")
    n = titulo.count("\n") + 1
    fig.text(0.065, 0.66, titulo, fontfamily=SERIF, fontsize=66 if n <= 3 else 56, color="white",
             va="center", linespacing=1.05)
    fig.text(0.065, 0.50, bajada, fontfamily=SANS_SB, fontsize=27, color="#c9d3df", va="center", linespacing=1.3)
    if serie is not None:
        _mini(fig.add_axes([0.065, 0.16, 0.87, 0.24]), serie, color, NAVY, tipo)
    fig.text(0.065, 0.075, "Deslizá →" if deslizar else "Nota completa · link en bio",
             fontfamily=SANS_SB, fontsize=22, color="white")
    fig.text(0.935, 0.075, URL, fontfamily=SANS_SB, fontsize=18, color="#ffd2bf", ha="right")
    _guardar(fig, "ig_1.png", NAVY, carpeta)


def _ajustar(fig, x, y, texto, size, ancho=0.87, minimo=0.72, dos_lineas=True, **kw):
    """Escribe el texto achicando la letra (hasta `minimo` del tamaño) o partiéndolo en dos líneas
    para que no se salga de la lámina. Con dos líneas, la primera sube y la segunda queda en `y`."""
    W = fig.get_figwidth() * fig.dpi * ancho
    r = fig.canvas.get_renderer()
    t = fig.text(x, y, texto, fontsize=size, **kw)
    s = size
    while t.get_window_extent(r).width > W and s > size * minimo:
        s -= 1; t.set_fontsize(s)
    if t.get_window_extent(r).width <= W or not dos_lineas or "\n" in texto:
        return t
    pal = texto.split(" ")
    corte = min(range(1, len(pal)), key=lambda i: abs(len(" ".join(pal[:i])) - len(" ".join(pal[i:]))))
    t.set_text(" ".join(pal[:corte]) + "\n" + " ".join(pal[corte:]))
    t.set_va("bottom"); t.set_linespacing(1.1)
    t.set_position((x, y - 0.012))
    s = size * 0.85; t.set_fontsize(s)
    while t.get_window_extent(r).width > W and s > 14:
        s -= 1; t.set_fontsize(s)
    return t


def ig_dato(n, etiqueta, l1, grande, l2, l3, dibujar, color=NARANJA, fuente_txt=FUENTE, carpeta="."):
    """Lámina con una cifra grande y un gráfico (1080 x 1350)."""
    fig = lienzo(1080, 1350)
    cabecera(fig, etiqueta)
    _ajustar(fig, 0.065, 0.835, l1, 32, fontfamily=SANS_SB, color=TINTA)
    _ajustar(fig, 0.065, 0.745, grande, 100 if len(grande) < 12 else 78, minimo=0.5, dos_lineas=False,
             fontfamily=SERIF, color=color, va="center")
    _ajustar(fig, 0.065, 0.665, l2, 28, minimo=0.6, dos_lineas=False, fontfamily=SANS_SB, color=TINTA)
    if l3:
        _ajustar(fig, 0.065, 0.618, l3, 20, minimo=0.7, dos_lineas=False, fontfamily=SANS_SB, color=GRIS)
    izq = getattr(dibujar, "izq", 0.065)
    ax = fig.add_axes([izq, 0.16, 0.935 - izq, 0.40])
    dibujar(ax)
    fuente(fig, fuente_txt)
    pie(fig)
    _guardar(fig, f"ig_{n}.png", carpeta=carpeta)


# --- Gráficos para las láminas ---------------------------------------------------------------------
def barras_h(etq, val, txt, colores=None, ref=None):
    etq, val, txt = list(etq), [float(v) for v in val], list(txt)

    def f(ax):
        y = np.arange(len(etq))
        ax.barh(y, val, color=colores or [AZUL] * len(val), height=0.62)
        lo, hi = min(0, min(val)), max(0, max(val))
        span = hi - lo or 1
        for i, (e, v, t) in enumerate(zip(etq, val, txt)):
            ax.text(lo - span * 0.02, i, e, ha="right", va="center", fontfamily=SANS_SB, fontsize=18, color=TINTA)
            ax.text(max(v, 0) + span * 0.015, i, t, va="center", fontfamily=SANS_XB, fontsize=18, color=TINTA)
        if ref is not None:
            ax.axvline(ref, color=NARANJA, lw=2, ls=(0, (4, 3)))
        ax.axvline(0, color="#cfcdc6", lw=1.2)
        ax.set_xlim(lo - span * 0.75, hi + span * 0.32)
        ax.set_ylim(-0.6, len(etq) - 0.4)
        ax.axis("off")
    return f


def lineas(x, series, ylim=None, ref=None, fmt=lambda v: coma(v, 0), ref_txt=None):
    """series = {nombre: (valores, color)}. x puede ser numérico o una lista de etiquetas."""
    x = list(x)
    etiquetas = None
    import numbers
    if x and not all(isinstance(v, numbers.Real) and not isinstance(v, bool) for v in x):
        etiquetas, x = [str(v) for v in x], list(range(len(x)))

    def f(ax):
        todos = [v for y, _ in series.values() for v in y]
        lo, hi = ylim if ylim else (min(todos), max(todos))
        sep = (hi - lo) * 0.16 or 1
        prev = None
        for nombre_, (y, c) in sorted(series.items(), key=lambda kv: -kv[1][0][-1]):
            y = list(y)
            ax.plot(x, y, color=c, lw=4, marker="o" if len(x) <= 16 else None, ms=8, mec=PAPEL, mew=2)
            yl = y[-1] if prev is None else min(y[-1], prev - sep)
            prev = yl
            ax.text(x[-1] + (x[-1] - x[0]) * 0.03, yl, f"{nombre_}\n{fmt(y[-1])}", fontfamily=SANS_XB,
                    fontsize=17, color=c, va="center", linespacing=1.15)
        if ref is not None:
            ax.axhline(ref, color=NARANJA if ref_txt else "#cfcdc6", lw=2 if ref_txt else 1.5, ls=(0, (4, 3)))
            if ref_txt:
                ax.text(x[0], ref, ref_txt, fontfamily=SANS_SB, fontsize=16, color=NARANJA, va="bottom")
        if ylim:
            ax.set_ylim(*ylim)
        ax.set_xlim(x[0] - (x[-1] - x[0]) * 0.02, x[-1] + (x[-1] - x[0]) * 0.3)
        paso = max(1, len(x) // 6)
        ax.set_xticks(x[::paso])
        if etiquetas:
            ax.set_xticklabels(etiquetas[::paso])
        ejes_limpios(ax, grilla_y=True)
    if max(abs(v) for y, _ in series.values() for v in y) >= 1000:
        f.izq = 0.10
    return f


def barras(x, y, txt, colores=None, ylim=None, rot=0):
    x, y, txt = list(x), [float(v) for v in y], list(txt)

    def f(ax):
        pos = np.arange(len(x))
        ax.bar(pos, y, color=colores or [AZUL] * len(y), width=0.65)
        top = ylim[1] if ylim else max(max(y), 0)
        bot = ylim[0] if ylim else min(min(y), 0)
        span = (top - bot) or 1
        for xi, yi, t in zip(pos, y, txt):
            if yi >= 0:
                ax.text(xi, yi + span * 0.02, t, ha="center", va="bottom", fontfamily=SANS_SB, fontsize=15, color=TINTA)
            else:
                ax.text(xi, yi - span * 0.02, t, ha="center", va="top", fontfamily=SANS_SB, fontsize=15, color=TINTA)
        ax.axhline(0, color="#cfcdc6", lw=1.2)
        ax.set_ylim(*(ylim or (bot - span * 0.12 if bot < 0 else 0, top + span * 0.12 if top > 0 else span * 0.04)))
        ax.set_yticks([])
        ax.set_xticks(pos, [str(v) for v in x], rotation=rot)
        ejes_limpios(ax)
        for t in ax.get_xticklabels():
            t.set_fontsize(14 if len(x) > 8 else 16)
    return f
