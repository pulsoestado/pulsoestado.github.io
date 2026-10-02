"""
Piezas para redes de la serie octubre–diciembre 2026.

Para cada nota genera, en su carpeta:
  social.png              tarjeta para X / Open Graph (1200 x 630)
  ig_1.png, ig_2.png, ig_3.png   carrusel de Instagram (1080 x 1350)

Todas las cifras se calculan desde data/processed, igual que en las notas.
Ejecutar desde la raíz del repositorio:  python scripts/flyers_serie.py [carpeta]
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from marca import *  # noqa: F401,F403

D = RAIZ / "data/processed"
VERDE, AMARILLO = "#1baf7a", "#eda100"
FUENTE = "Fuente: Pulso del Estado con datos de SINARH, SICCA y BCP."


def leer(n):
    return pd.read_csv(D / n)


def pct(x, d=1):
    return coma(x, d) + "%"


def spct(x, d=1):
    return ("+" if x >= 0 else "−") + pct(abs(x), d)


# --- Plantillas --------------------------------------------------------------------------------
def guardar(fig, carpeta, nombre, fondo=PAPEL):
    fig.savefig(carpeta / nombre, dpi=100, facecolor=fondo)
    plt.close(fig)


def portada(carpeta, kicker, titulo, bajada, serie=None, color=NARANJA):
    fig = lienzo(1080, 1350, fondo=NAVY)
    logo(fig, 0.065, 0.86, 0.075, fondo="#1d3d5f")
    fig.text(0.16, 0.888, "Pulso del Estado", fontfamily=SERIF, fontsize=32, color="white", va="center")
    fig.text(0.065, 0.80, kicker.upper(), fontfamily=SANS_SB, fontsize=20, color="#ffd2bf")
    fig.text(0.065, 0.66, titulo, fontfamily=SERIF, fontsize=66, color="white", va="center", linespacing=1.05)
    fig.text(0.065, 0.50, bajada, fontfamily=SANS_SB, fontsize=27, color="#c9d3df", va="center", linespacing=1.3)
    if serie is not None:
        ax = fig.add_axes([0.065, 0.16, 0.87, 0.24])
        x, y = serie
        ax.plot(x, y, color=color, lw=5, solid_capstyle="round")
        ax.scatter([x[-1]], [y[-1]], s=180, color=color, edgecolor=NAVY, linewidth=3, zorder=3)
        ax.axis("off"); ax.set_facecolor(NAVY)
    fig.text(0.065, 0.075, "Deslizá →", fontfamily=SANS_SB, fontsize=22, color="white")
    fig.text(0.935, 0.075, URL, fontfamily=SANS_SB, fontsize=18, color="#ffd2bf", ha="right")
    guardar(fig, carpeta, "ig_1.png", NAVY)


def dato(carpeta, nombre, etiqueta, l1, grande, color, l2, l3, dibujar, fuente_txt=FUENTE):
    fig = lienzo(1080, 1350)
    cabecera(fig, etiqueta)
    fig.text(0.065, 0.835, l1, fontfamily=SANS_SB, fontsize=34, color=TINTA)
    fig.text(0.065, 0.745, grande, fontfamily=SERIF, fontsize=100, color=color, va="center")
    fig.text(0.065, 0.665, l2, fontfamily=SANS_SB, fontsize=29, color=TINTA)
    if l3:
        fig.text(0.065, 0.618, l3, fontfamily=SANS_SB, fontsize=21, color=GRIS)
    ax = fig.add_axes([0.065, 0.16, 0.87, 0.40])
    dibujar(ax)
    fuente(fig, fuente_txt)
    pie(fig)
    guardar(fig, carpeta, nombre)


def social(carpeta, titulo, grande, bajada, serie=None, color=NARANJA):
    fig = lienzo(1200, 630, fondo=NAVY)
    logo(fig, 0.05, 0.80, 0.05, fondo="#1d3d5f")
    fig.text(0.115, 0.855, "Pulso del Estado", fontfamily=SERIF, fontsize=24, color="white", va="center")
    fig.text(0.05, 0.62, titulo, fontfamily=SERIF, fontsize=42, color="white", va="center", linespacing=1.08)
    fig.text(0.05, 0.355, grande, fontfamily=SERIF, fontsize=58, color=color, va="center")
    fig.text(0.05, 0.22, bajada, fontfamily=SANS_SB, fontsize=20, color="white", va="center")
    fig.text(0.05, 0.08, URL, fontfamily=SANS_SB, fontsize=17, color="#ffd2bf", va="center")
    if serie is not None:
        ax = fig.add_axes([0.60, 0.20, 0.36, 0.50])
        x, y = serie
        ax.plot(x, y, color=color, lw=4, solid_capstyle="round")
        ax.scatter([x[-1]], [y[-1]], s=90, color=color, edgecolor=NAVY, linewidth=2, zorder=3)
        ax.axis("off")
    guardar(fig, carpeta, "social.png", NAVY)


# --- Gráficos simples para los carruseles --------------------------------------------------------
def g_barh(etq, val, txt, colores=None, xlim=None, ref=None):
    def f(ax):
        y = np.arange(len(etq))
        ax.barh(y, val, color=colores or [AZUL] * len(val), height=0.62)
        lo = min(0, min(val))
        span = (xlim[1] - xlim[0]) if xlim else (max(val) - lo)
        for i, (e, v, t) in enumerate(zip(etq, val, txt)):
            ax.text(lo - span * 0.02, i, e, ha="right", va="center", fontfamily=SANS_SB, fontsize=19, color=TINTA)
            ax.text(max(v, 0) + span * 0.015, i, t, va="center", fontfamily=SANS_XB, fontsize=19, color=TINTA)
        if ref is not None:
            ax.axvline(ref, color=NARANJA, lw=2, ls=(0, (4, 3)))
        ax.axvline(0, color="#cfcdc6", lw=1.2)
        ax.set_xlim(*(xlim or (lo - span * 0.62, max(val) * 1.3)))
        ax.set_ylim(-0.6, len(etq) - 0.4)
        ax.axis("off")
    return f


def g_lineas(x, series, ylim=None, ref=None, fmt=lambda v: coma(v, 0), ref_txt=None):
    def f(ax):
        lo, hi = ylim if ylim else (min(min(y) for y, _ in series.values()), max(max(y) for y, _ in series.values()))
        sep = (hi - lo) * 0.16
        orden = sorted(series.items(), key=lambda kv: -kv[1][0][-1])
        prev = None
        for nombre_, (y, c) in orden:
            ax.plot(x, y, color=c, lw=4, marker="o", ms=8, mec=PAPEL, mew=2)
            yl = y[-1] if prev is None else min(y[-1], prev - sep)
            prev = yl
            ax.text(x[-1] + 0.25, yl, f"{nombre_}\n{fmt(y[-1])}", fontfamily=SANS_XB, fontsize=17,
                    color=c, va="center", linespacing=1.15)
        if ref is not None:
            ax.axhline(ref, color=NARANJA if ref_txt else "#cfcdc6", lw=2 if ref_txt else 1.5, ls=(0, (4, 3)))
            if ref_txt:
                ax.text(x[0], ref, ref_txt, fontfamily=SANS_SB, fontsize=16, color=NARANJA, va="bottom")
        if ylim:
            ax.set_ylim(*ylim)
        ax.set_xlim(x[0] - 0.3, x[-1] + 2.4)
        ax.set_xticks(x[::2])
        ejes_limpios(ax, grilla_y=True)
    return f


def g_barras(x, y, txt, colores=None, ylim=None):
    def f(ax):
        ax.bar(x, y, color=colores or [AZUL] * len(y), width=0.65)
        for xi, yi, t in zip(x, y, txt):
            ax.text(xi, yi + (ylim[1] if ylim else max(y)) * 0.02, t, ha="center", fontfamily=SANS_SB,
                    fontsize=15, color=TINTA)
        if ylim:
            ax.set_ylim(*ylim)
        ax.set_yticks([])
        ax.set_xticks(x)
        ejes_limpios(ax)
        for t in ax.get_xticklabels():
            t.set_fontsize(14)
    return f


# --- Datos comunes -----------------------------------------------------------------------------------
masa = leer("masa_anual_sector.csv")
vin = leer("vinculos_mensual_sector.csv")
bcp = leer("ipc_salarios_bcp.csv").set_index("anho")
A0, A1 = 2017, 2025
T = masa[masa.anho.between(A0, A1)].groupby("anho")[
    ["devengado", "devengado_real_2025", "devengado_sin_aguinaldo", "sin_aguinaldo_real_2025", "vinculos_promedio"]].sum()
anios = list(T.index)
CORTO = {"Servicio civil del Ejecutivo": "Servicio civil", "Entes autónomos y autárquicos": "Entes autónomos",
         "Gobiernos departamentales": "Gobernaciones", "Poder Legislativo": "P. Legislativo",
         "Poder Judicial": "P. Judicial", "Fuerzas públicas": "Fuerzas públicas", "Otros organismos": "Otros organismos"}
corto = lambda s: CORTO.get(s, s)


def p01(c):
    real = T.devengado_real_2025 / 1e12
    var = (real[A1] / real[A0] - 1) * 100
    vv = (T.vinculos_promedio[A1] / T.vinculos_promedio[A0] - 1) * 100
    rem = T.sin_aguinaldo_real_2025 / 12 / T.vinculos_promedio / 1e6
    vr = (rem[A1] / rem[A0] - 1) * 100
    portada(c, "Masa salarial", "¿Cuánto paga\nel Estado\nen salarios?",
            f"{coma(T.devengado[A1] / 1e12)} billones de guaraníes en {A1}.\nDescontada la inflación, +{coma(var, 0)}% desde {A0}.",
            (anios, list(real)))
    dato(c, "ig_2.png", "Masa salarial real", f"Entre {A0} y {A1}, en guaraníes de hoy,", spct(var), NARANJA,
         "creció la masa salarial del Estado", f"Los vínculos crecieron {spct(vv)} en el mismo período",
         g_barras(anios, list(real), [coma(v) for v in real], ylim=(0, 36)))
    dato(c, "ig_3.png", "Sueldo medio real", "La remuneración media real por vínculo", spct(vr), AZUL,
         f"frente a {A0}: más gente, el mismo sueldo", "Millones de guaraníes de 2025 por mes, sin aguinaldo",
         g_lineas(anios, {"Remuneración media": (list(rem), NARANJA)}, ylim=(5.5, 7.6), fmt=lambda v: coma(v, 2)))
    social(c, "¿Cuánto paga el Estado\nen salarios?", f"{coma(T.devengado[A1] / 1e12)} billones",
           f"en {A1} · {spct(var)} real desde {A0}", (anios, list(real)))


def p02(c):
    p = leer("panel_situcap.csv"); M = int(p.mes.iloc[0]); k = ["codigo_nivel", "codigo_entidad", "codigo_oee"]
    a, b = p[p.anho == 2025].set_index(k), p[p.anho == 2026].set_index(k)
    com = a.index[a.vinculos > 0].intersection(b.index[b.vinculos > 0])
    com = com[(a.loc[com, "masa_mes"] > 0).values & (b.loc[com, "masa_mes"] > 0).values]
    a, b = a.loc[com], b.loc[com]
    vv = (b.vinculos.sum() / a.vinculos.sum() - 1) * 100
    vm = (b.masa_mes.sum() / a.masa_mes.sum() - 1) * 100
    vr = ((1 + vm / 100) / 1.015 - 1) * 100
    tot = p[p.anho == 2026]
    sec = b.groupby("sector").vinculos.sum() - a.groupby("sector").vinculos.sum()
    sec = sec.sort_values()
    serie = vin.groupby(["anho", "mes"]).total.sum()
    s12 = serie.iloc[-20:]
    portada(c, "SITUCAP N.º 1 · agosto de 2026", "Situación del\nCapital Humano\nPúblico",
            f"{miles(tot.vinculos.sum())} vínculos y {coma(tot.masa_mes.sum() / 1e12, 2)} billones\nde guaraníes en salarios en agosto.",
            (list(range(len(s12))), list(s12.values)))
    dato(c, "ig_2.png", "SITUCAP · Dotación", "En un año, con las mismas instituciones,", spct(vv), NARANJA,
         "crecieron los vínculos pagados", "Variación de vínculos por sector, ago 2025 → ago 2026",
         g_barh([corto(s) for s in sec.index], list(sec.values), [("+" if v >= 0 else "−") + miles(abs(v)) for v in sec.values],
                colores=[AZUL if v >= 0 else ROJO for v in sec.values]))
    dato(c, "ig_3.png", "SITUCAP · Masa salarial", "La masa salarial de agosto creció", spct(vm), NARANJA,
         f"en un año: {spct(vr)} descontada la inflación", "Inflación interanual de agosto: 1,5% (BCP)",
         g_barras(["Masa salarial\nnominal", "Inflación\n(IPC)", "Masa salarial\nreal"], [vm, 1.5, vr],
                  [spct(vm), "1,5%", spct(vr)], colores=[NARANJA, GRIS, AZUL], ylim=(0, 7.5)))
    social(c, "SITUCAP N.º 1\nagosto de 2026", miles(tot.vinculos.sum()), f"vínculos · {spct(vv)} interanual",
           (list(range(len(s12))), list(s12.values)))


def p03(c):
    t = T.copy(); t["rem"] = t.devengado_real_2025 / t.vinculos_promedio
    d = np.log(t[["devengado_real_2025", "vinculos_promedio", "rem"]]).diff().dropna() * 100
    ev = np.log(t.vinculos_promedio[A1] / t.vinculos_promedio[A0]) * 100
    er = np.log(t.rem[A1] / t.rem[A0]) * 100
    s = masa[masa.anho.isin([A0, A1])].pivot(index="sector", columns="anho", values=["devengado_real_2025", "vinculos_promedio"])
    vv = (s[("vinculos_promedio", A1)] / s[("vinculos_promedio", A0)] - 1) * 100
    rr = ((s[("devengado_real_2025", A1)] / s[("vinculos_promedio", A1)]) /
          (s[("devengado_real_2025", A0)] / s[("vinculos_promedio", A0)]) - 1) * 100
    tres = ["Educación", "Salud", "Fuerzas públicas"]
    portada(c, "Masa salarial", "¿Más gente\no mejores\nsueldos?",
            "Qué explica el aumento de la masa\nsalarial desde 2017, sector por sector.",
            (anios, list(t.devengado_real_2025 / 1e12)))
    dato(c, "ig_2.png", "Descomposición", "Todo el crecimiento real de la masa salarial", f"+{coma(ev)} pp", AZUL,
         "se explica por más vínculos", f"El sueldo medio real restó {coma(abs(er))} puntos ({A0}–{A1}, en logaritmos)",
         g_barh(["Más vínculos", "Sueldo medio real"], [ev, er], [f"{'+' if ev >= 0 else '−'}{coma(abs(ev))} pp", f"{'+' if er >= 0 else '−'}{coma(abs(er))} pp"],
                colores=[AZUL, NARANJA], xlim=(-12, 22)))
    dato(c, "ig_3.png", "Tres modelos", "Educación subió sueldos; Salud sumó gente", spct(rr["Educación"], 0), NARANJA,
         "remuneración media real en Educación", f"Salud: {spct(vv['Salud'], 0)} vínculos y {spct(rr['Salud'], 0)} remuneración media real",
         g_barh([f"{corto(x)} · vínculos" for x in tres] + [f"{corto(x)} · sueldo" for x in tres],
                [vv[x] for x in tres] + [rr[x] for x in tres],
                [spct(vv[x], 0) for x in tres] + [spct(rr[x], 0) for x in tres],
                colores=[AZUL] * 3 + [NARANJA] * 3, xlim=(-95, 70)))
    social(c, "¿Más gente o\nmejores sueldos?", "Más gente",
           f"explica el crecimiento real de la masa salarial desde {A0}", (anios, list(t.vinculos_promedio)))


def p04(c):
    pm = leer("pcd_mensual.csv"); po = leer("pcd_oee.csv")
    s = pm[(pm.mes == 6) & (pm.anho >= A0)]; s = s.assign(p=s.pcd / s.vinculos * 100)
    P, V = po.pcd.sum(), po.vinculos.sum(); pt = P / V * 100; falt = 0.05 * V - P
    po["p"] = po.pcd / po.vinculos * 100
    sec = po.groupby("sector")[["pcd", "vinculos"]].sum(); sec["p"] = sec.pcd / sec.vinculos * 100
    sec = sec[sec.vinculos >= 2000].sort_values("p")
    portada(c, "Inclusión", "La cuota\ndel 5%",
            f"Personas con discapacidad en el Estado:\nhoy son el {coma(pt, 2)}% del personal.",
            (list(s.anho), list(s.p)), color=AMARILLO)
    dato(c, "ig_2.png", "Cuota del 5%", "Para cumplir la ley harían falta", f"{miles(round(falt, -2))}", NARANJA,
         "personas con discapacidad más", f"Hoy hay {miles(P)} sobre {miles(V)} vínculos (junio 2026)",
         g_lineas(list(s.anho), {"Con discapacidad": (list(s.p), AZUL)}, ylim=(0, 5.5), ref=5,
                  fmt=lambda v: coma(v, 2) + "%", ref_txt="Cuota legal: 5%"))
    dato(c, "ig_3.png", "Cuota del 5%", "Solo cumplen la cuota", f"{int((po.p >= 5).sum())} de {len(po)}", NARANJA,
         "instituciones públicas", f"{int((po.pcd == 0).sum())} no registran ninguna persona con discapacidad",
         g_barh([corto(x) for x in sec.index], list(sec.p), [coma(v, 2) + "%" for v in sec.p], xlim=(-2.6, 5.6), ref=5))
    social(c, "Personas con discapacidad\nen el Estado", f"{coma(pt, 2)}%", "del personal · la ley exige al menos 5%",
           (list(s.anho), list(s.p)), color=AMARILLO)


def p05(c):
    g = leer("genero_brecha_anual.csv").set_index("anho").loc[2018:]
    gs = leer("genero_brecha_sector.csv").set_index("sector")
    u = g.loc[g.index.max()]
    o = gs[gs.cargos >= 2000].sort_values("brecha_misma_categoria_pct")
    portada(c, "Género", "¿Ganan menos\nlas mujeres\nen el Estado?",
            "En promedio ganan más. En el mismo\ncargo, todavía ganan menos.",
            (list(g.index), list(g.brecha_misma_categoria_pct)))
    dato(c, "ig_2.png", "Brecha de género", "Sueldo básico medio de las mujeres", spct(-u.brecha_bruta_pct), AZUL,
         "frente al de los hombres", "Pero en la misma institución y categoría:",
         g_barh(["Brecha bruta", "Misma institución\ny categoría"], [-u.brecha_bruta_pct, -u.brecha_misma_categoria_pct],
                [spct(-u.brecha_bruta_pct), spct(-u.brecha_misma_categoria_pct)], colores=[AZUL, NARANJA], xlim=(-7, 9)))
    dato(c, "ig_3.png", "Brecha de género", "En igual cargo, en Salud las mujeres ganan",
         pct(gs.loc["Salud", "brecha_misma_categoria_pct"]), NARANJA, "menos que los hombres",
         "Brecha en igual institución y categoría, por sector (junio 2026)",
         g_barh([corto(x) for x in o.index], list(o.brecha_misma_categoria_pct),
                [spct(v) for v in o.brecha_misma_categoria_pct],
                colores=[NARANJA if v > 0 else AZUL for v in o.brecha_misma_categoria_pct], xlim=(-9, 10)))
    social(c, "¿Ganan menos las mujeres\nen el Estado?", spct(-u.brecha_misma_categoria_pct),
           "en la misma institución y categoría", (list(g.index), list(g.brecha_misma_categoria_pct)))


def p06(c):
    va = vin[vin.anho.between(A0, A1)].groupby(["anho", "sector"]).total.mean().unstack()
    idx = va / va.loc[A0] * 100
    f = va.loc[A1].sort_values()
    part = f / f.sum() * 100
    tres = part[["Educación", "Salud", "Fuerzas públicas"]].sum()
    portada(c, "Sectores", "El Estado\npor sectores",
            "Educación, salud, seguridad y el resto:\nquién creció y cuánto cuesta.",
            (anios, list(idx["Salud"])))
    dato(c, "ig_2.png", "Sectores", "Educación, Salud y Fuerzas públicas reúnen", pct(tres, 0), NARANJA,
         f"de los vínculos públicos ({A1})", "Vínculos promedio por sector",
         g_barh([corto(x) for x in f.index[-8:]], list(f.values[-8:]), [miles(v) for v in f.values[-8:]]))
    dato(c, "ig_3.png", "Sectores", f"Desde {A0}, el personal de Salud creció", spct(idx.loc[A1, 'Salud'] - 100, 0), NARANJA,
         f"y el de Educación {spct(idx.loc[A1, 'Educación'] - 100)}", f"Índice de vínculos, {A0} = 100",
         g_lineas(anios, {"Salud": (list(idx["Salud"]), NARANJA), "Fuerzas públicas": (list(idx["Fuerzas públicas"]), NAVY),
                          "Educación": (list(idx["Educación"]), AZUL)}, ylim=(85, 160), ref=100))
    social(c, "El Estado por sectores", pct(tres, 0), "de los vínculos, en tres sectores",
           (anios, list(idx["Salud"])))


def p07(c):
    per = leer("dotacion_mensual.csv").set_index(["anho", "mes"])
    v = vin.groupby(["anho", "mes"]).total.sum()
    cargos, pm_, vm_ = 334541, per.loc[(2025, 5), "cantidad_mensual"], v.loc[(2025, 5)]
    portada(c, "Metodología", "Vínculos,\npersonas\ny cargos",
            "Tres maneras de contar al Estado,\ny por qué las cifras no coinciden.", None)
    dato(c, "ig_2.png", "Tres medidas", "¿Cuántos trabajan en el Estado? Depende:", "3 cifras", NARANJA,
         "todas correctas, miden cosas distintas", "Mayo de 2025 · cargos del PGN 2025",
         g_barh(["Cargos presupuestados\n(sin municipios)", "Personas que\ncobraron en el mes", "Vínculos pagados\nen el mes"],
                [cargos, pm_, vm_], [miles(cargos), miles(pm_), miles(vm_)], colores=[GRIS, AZUL, NARANJA],
                xlim=(-260000, 480000)))
    dato(c, "ig_3.png", "Tres medidas", "Vínculos y personas no son lo mismo:", f"+{miles(vm_ - pm_)}", NARANJA,
         "vínculos más que personas (mayo 2025)", "Quien tiene dos cargos cuenta dos veces como vínculo",
         g_barh(["Personas", "Vínculos"], [pm_, vm_], [miles(pm_), miles(vm_)], colores=[AZUL, NARANJA],
                xlim=(-150000, 470000)))
    social(c, "Vínculos, personas y cargos:\ntres maneras de contar al Estado", "334, 359 o 368 mil",
           "¿cuál es la cifra correcta?", None)


def p08(c):
    b = bcp.loc[A0:A1].copy()
    b["rp"] = T.devengado_sin_aguinaldo / 12 / T.vinculos_promedio
    idx = pd.DataFrame({k: b[col] / b[col].iloc[0] * 100 for k, col in
                        [("ipc", "ipc"), ("rp", "rp"), ("sm", "salario_minimo"), ("iss", "iss_junio")]})
    real = idx[["rp", "sm", "iss"]].div(idx.ipc, axis=0) * 100
    portada(c, "Salarios e inflación", "¿Le ganaron\nlos sueldos\na la inflación?",
            f"Precios +{coma(idx.ipc[A1] - 100, 0)}% entre {A0} y {A1}.\nSueldos: casi lo mismo.",
            (anios, list(real.rp)))
    dato(c, "ig_2.png", "Salarios e inflación", f"Entre {A0} y {A1} los precios subieron", spct(idx.ipc[A1] - 100), NARANJA,
         "y los sueldos, casi lo mismo", "Variación nominal acumulada",
         g_barh(["Precios (IPC)", "Remuneración\nmedia pública", "Salario mínimo", "Salarios privados\n(ISS)"],
                [idx.ipc[A1] - 100, idx.rp[A1] - 100, idx.sm[A1] - 100, idx.iss[A1] - 100],
                [spct(idx.ipc[A1] - 100), spct(idx.rp[A1] - 100), spct(idx.sm[A1] - 100), spct(idx.iss[A1] - 100)],
                colores=[GRIS, NARANJA, AZUL, VERDE], xlim=(-30, 58)))
    dato(c, "ig_3.png", "Poder de compra", "Descontada la inflación, el sueldo público", spct(real.rp[A1] - 100), AZUL,
         f"frente a {A0}", f"Poder de compra, índice {A0} = 100",
         g_lineas(anios, {"Pública": (list(real.rp), NARANJA), "Mínimo": (list(real.sm), AZUL)}, ylim=(90, 110), ref=100))
    social(c, "¿Le ganaron los sueldos\npúblicos a la inflación?", spct(real.rp[A1] - 100),
           f"remuneración media real {A0}–{A1}", (anios, list(real.rp)))


def p09(c):
    mm = leer("masa_mensual_sector.csv"); mm = mm[mm.anho == A1]
    grp = {"Dietas": "Dietas y g. de repr.", "Gastos de representación": "Dietas y g. de repr."}
    mm["g"] = mm.componente.map(lambda x: grp.get(x, x))
    tot = mm.groupby("g").devengado.sum(); tot = (tot / tot.sum() * 100).sort_values()
    sec = mm.groupby(["sector", "g"]).devengado.sum().unstack().fillna(0)
    sec = sec.div(sec.sum(axis=1), axis=0) * 100
    portada(c, "Remuneraciones", "¿De qué está\nhecho un sueldo\npúblico?",
            "Sueldo básico, contratos, bonificaciones,\naguinaldo, dietas y gastos de representación.", None)
    t6 = tot.tail(6)
    dato(c, "ig_2.png", "Componentes", f"En {A1}, el sueldo básico fue", pct(tot["Sueldo básico"], 0), AZUL,
         "de la masa salarial del Estado", "Composición de la masa salarial",
         g_barh(list(t6.index), list(t6.values), [pct(v) for v in t6.values], xlim=(-40, 80)))
    o = sec["Dietas y g. de repr."].sort_values().tail(6)
    dato(c, "ig_3.png", "Componentes", "En las municipalidades, dietas y gastos de", pct(sec.loc['Municipalidades', 'Dietas y g. de repr.'], 0), NARANJA,
         "representación son parte de la masa salarial", "Dietas y gastos de representación, % de la masa de cada sector",
         g_barh([corto(x) for x in o.index], list(o.values), [pct(v) for v in o.values], colores=[NARANJA] * len(o), xlim=(-16, 28)))
    social(c, "¿De qué está hecho\nun sueldo público?", pct(tot["Sueldo básico"], 0), "de la masa salarial es sueldo básico")


def p10(c):
    mu = leer("municipios_2025.csv"); mu["pc"] = mu.contratados / mu.vinculos * 100
    sys.path.insert(0, str(RAIZ / "scripts")); from pulso import nombre
    mu["n"] = mu.descripcion_oee.map(nombre)
    pc = mu.contratados.sum() / mu.vinculos.sum() * 100
    m_ = vin[(vin.sector == "Municipalidades") & vin.anho.between(A0, A1)].groupby("anho")[["total", "contratado"]].mean()
    top = mu.sort_values("vinculos", ascending=False).head(8).iloc[::-1]
    portada(c, "Municipalidades", "Municipalidades\npor dentro",
            f"{miles(mu.vinculos.sum())} vínculos: 7 de cada 10\nson contratos.", (anios, list(m_.contratado)))
    dato(c, "ig_2.png", "Municipalidades", "En las municipalidades,", pct(pc, 0), NARANJA, "de los vínculos son contratos",
         "En el resto del Estado: 1 de cada 5", g_barh(list(top.n), list(top.vinculos),
                                                       [f"{miles(v)} · {pct(p, 0)}" for v, p in zip(top.vinculos, top.pc)]))
    bins = np.arange(0, 101, 10); cnt, _ = np.histogram(mu.pc.clip(upper=99.99), bins=bins)
    dato(c, "ig_3.png", "Municipalidades", "Los contratados son mayoría en", f"{int((mu.pc >= 50).sum())} de {len(mu)}", NARANJA,
         "municipalidades", "Municipalidades según su proporción de contratados (2025)",
         g_barras([f"{a}–{a + 10}" for a in bins[:-1]], list(cnt), [str(x) for x in cnt],
                  colores=[AZUL if a < 50 else NARANJA for a in bins[:-1]], ylim=(0, max(cnt) * 1.2)))
    social(c, "Municipalidades por dentro", pct(pc, 0), "de los vínculos municipales son contratos",
           (anios, list(m_.contratado)))


PIEZAS = {
    "posts/2026-10-16-masa-salarial-real": p01,
    "situcap/ediciones/2026-08": p02,
    "posts/2026-10-30-mas-gente-o-mejores-sueldos": p03,
    "posts/2026-11-06-discapacidad-cuota-5": p04,
    "posts/2026-11-13-brecha-salarial-genero": p05,
    "posts/2026-11-20-estado-por-sectores": p06,
    "posts/2026-11-27-vinculos-personas-cargos": p07,
    "posts/2026-12-04-sueldos-vs-inflacion": p08,
    "posts/2026-12-11-de-que-esta-hecho-un-sueldo": p09,
    "posts/2026-12-18-municipalidades-por-dentro": p10,
}

if __name__ == "__main__":
    filtro = sys.argv[1] if len(sys.argv) > 1 else ""
    for carpeta, fn in PIEZAS.items():
        if filtro in carpeta:
            fn(RAIZ / carpeta)
            print("ok", carpeta)
