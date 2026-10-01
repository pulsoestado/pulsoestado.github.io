"""
Carrusel de Instagram y tarjeta social de la nota
"Radiografía del empleo público: seis hallazgos".

Salidas (en la carpeta de la nota):
  carrusel_1.png ... carrusel_7.png  (1080 x 1350)
  social.png                          (1200 x 630, para X / Open Graph)

Ejecutar desde la raíz del repositorio:  python scripts/flyer_radiografia.py
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))
from marca import *  # noqa: F401,F403

POST = RAIZ / "posts/2026-10-02-radiografia-empleo-publico"
D = RAIZ / "data/processed"
mensual = pd.read_csv(D / "dw_mensual.csv")
sec_m = pd.read_csv(D / "dw_mensual_sector.csv")
sec_a = pd.read_csv(D / "dw_anual_sector.csv")
panel = pd.read_csv(D / "dw_panel_interanual.csv")
mensual["f"] = pd.to_datetime(mensual.fecha + "-01")
sec_m["f"] = pd.to_datetime(sec_m.fecha + "-01")

BASE, ULT = 2017, int(sec_a.anho.max())
ult = mensual.iloc[-1]
A1, M1 = int(ult.anho), int(ult.mes)
rec = mensual.loc[mensual.total.idxmax()]

k = ["codigo_nivel", "codigo_entidad", "codigo_oee"]
p0 = panel[panel.anho == A1 - 1].set_index(k)
p1 = panel[panel.anho == A1].set_index(k)
c = p0.index.intersection(p1.index)
dP = p1.loc[c, "permanente"].sum() - p0.loc[c, "permanente"].sum()
dC = p1.loc[c, "contratado"].sum() - p0.loc[c, "contratado"].sum()

sa = sec_a.pivot(index="sector", columns="anho", values="total")
sa["dif"] = sa[ULT] - sa[BASE]
sa["aporte"] = sa["dif"] / sa["dif"].sum() * 100
aporte_sp = sa.loc[["Salud (MSPBS)", "Policía Nacional"], "aporte"].sum()

sal = sec_m[sec_m.sector == "Salud (MSPBS)"]
sal_u = sal.iloc[-1]
pol = sec_m[sec_m.sector == "Policía Nacional"].set_index("fecha")
pol_u, pol_0 = pol.iloc[-1].total, pol.loc[f"{A1-2}-{M1:02d}"].total

ETIQ = {"Salud (MSPBS)": "Salud", "Policía Nacional": "Policía", "Educación (MEC)": "Educación",
        "Defensa Nacional": "Defensa", "Resto del sector público": "Resto del Estado"}
FUENTE = "Fuente: Pulso del Estado con datos de SICCA y SINARH. Vínculos pagados por mes."


def titulo(fig, l1, grande, color_grande, l2, l3=None):
    fig.text(0.065, 0.835, l1, fontfamily=SANS_SB, fontsize=34, color=TINTA)
    fig.text(0.065, 0.745, grande, fontfamily=SERIF, fontsize=100, color=color_grande, va="center")
    fig.text(0.065, 0.665, l2, fontfamily=SANS_SB, fontsize=30, color=TINTA)
    if l3:
        fig.text(0.065, 0.618, l3, fontfamily=SANS_SB, fontsize=22, color=GRIS)


def guardar(fig, nombre, fondo=PAPEL):
    fig.savefig(POST / nombre, dpi=100, facecolor=fondo)
    plt.close(fig)


# --- 1. Portada ----------------------------------------------------------------------
fig = lienzo(1080, 1350, fondo=NAVY)
logo(fig, 0.065, 0.86, 0.075, fondo="#1d3d5f")
fig.text(0.16, 0.888, "Pulso del Estado", fontfamily=SERIF, fontsize=32, color="white", va="center")
fig.text(0.065, 0.74, "Radiografía del\nempleo público", fontfamily=SERIF, fontsize=72,
         color="white", va="center", linespacing=1.05)
fig.text(0.065, 0.615, f"6 hallazgos a {MESES[M1-1]} de {A1}", fontfamily=SANS_SB, fontsize=32,
         color="#ffd2bf")
ax = fig.add_axes([0.065, 0.2, 0.87, 0.33])
s = mensual[mensual.anho >= BASE]
ax.plot(s.f, s.total / 1000, color=NARANJA, lw=4)
ax.scatter([pd.Timestamp(f"{int(rec.anho)}-{int(rec.mes):02d}-01")], [rec.total / 1000], s=160,
           color=NARANJA, edgecolor=NAVY, linewidth=3, zorder=3)
ax.text(pd.Timestamp(f"{int(rec.anho)}-{int(rec.mes):02d}-01"), rec.total / 1000 + 7,
        f"{miles(rec.total)}", ha="right", fontfamily=SERIF, fontsize=34, color="white")
ax.text(pd.Timestamp(f"{int(rec.anho)}-{int(rec.mes):02d}-01"), rec.total / 1000 + 22,
        f"máximo histórico · {MESES[int(rec.mes)-1]} {int(rec.anho)}", ha="right",
        fontfamily=SANS_SB, fontsize=17, color="#ffd2bf")
ax.set_ylim(290, 410); ax.axis("off"); ax.set_facecolor(NAVY)
fig.text(0.065, 0.165, "Vínculos pagados por mes en el sector público, 2017–2026",
         fontfamily=SANS, fontsize=16, color="#c9d3df")
fig.text(0.065, 0.075, "Deslizá →", fontfamily=SANS_SB, fontsize=22, color="white")
fig.text(0.935, 0.075, URL, fontfamily=SANS_SB, fontsize=18, color="#ffd2bf", ha="right")
guardar(fig, "carrusel_1.png", NAVY)

# --- 2. Contratos en el último año ---------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, "Hallazgo 1 de 6")
titulo(fig, "En el último año,", "7 de cada 10", NARANJA, "nuevos vínculos fueron contratos",
       f"{MESES[M1-1].capitalize()} {A1-1} → {MESES[M1-1]} {A1}, mismas instituciones")
ax = fig.add_axes([0.065, 0.18, 0.87, 0.36])
ax.barh([1, 0], [dC, dP], color=[NARANJA, AZUL], height=0.55)
for y, v, n in [(1, dC, "Contratados"), (0, dP, "Permanentes")]:
    ax.text(0, y + 0.42, n, fontfamily=SANS_SB, fontsize=22, color=TINTA, va="center")
    ax.text(v + 120, y, f"+{miles(v)}", fontfamily=SERIF, fontsize=40, color=TINTA, va="center")
ax.set_xlim(0, dC * 1.35); ax.set_ylim(-0.5, 1.8); ax.axis("off")
fuente(fig, FUENTE)
pie(fig)
guardar(fig, "carrusel_2.png")

# --- 3. Salud y Policía ---------------------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, "Hallazgo 2 de 6")
titulo(fig, "Salud y Policía explican", f"{coma(aporte_sp, 0)}%", NARANJA,
       f"del crecimiento del empleo público", f"Variación de vínculos, promedio anual {BASE}–{ULT}")
o = sa.sort_values("dif")
ax = fig.add_axes([0.065, 0.16, 0.87, 0.40])
y = range(len(o))
cols = [ROJO if v < 0 else (NARANJA if s_ in ("Salud (MSPBS)", "Policía Nacional") else AZUL)
        for s_, v in zip(o.index, o.dif)]
ax.barh(list(y), o.dif, color=cols, height=0.6)
for yi, (s_, v) in enumerate(zip(o.index, o.dif)):
    ax.text(-600 if v >= 0 else v - 600, yi, ETIQ[s_], ha="right", va="center", fontfamily=SANS_SB,
            fontsize=20, color=TINTA)
    ax.text(v + 400 if v >= 0 else 400, yi, ("+" if v >= 0 else "−") + miles(abs(v)), va="center",
            fontfamily=SANS_XB, fontsize=20, color=TINTA)
ax.set_xlim(-11000, o.dif.max() * 1.3); ax.axis("off")
ax.axvline(0, color="#cfcdc6", lw=1.5)
fuente(fig, FUENTE)
pie(fig)
guardar(fig, "carrusel_3.png")

# --- 4. Salud contratados ------------------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, "Hallazgo 3 de 6")
pc = sal_u.contratado / sal_u.total * 100
titulo(fig, "En el Ministerio de Salud,", f"{coma(pc, 0)}%", NARANJA, "del personal es contratado",
       "Los contratos de la pandemia nunca se revirtieron")
ax = fig.add_axes([0.065, 0.17, 0.72, 0.39])
s = sal[sal.anho >= BASE]
ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-12-31"), color="#f1efea", lw=0)
ax.text(pd.Timestamp("2020-04-01"), 41500, "Pandemia", fontfamily=SANS_SB, fontsize=15, color=GRIS)
for col, colr, n in [("contratado", NARANJA, "Contratados"), ("permanente", AZUL, "Permanentes")]:
    ax.plot(s.f, s[col], color=colr, lw=4)
    ax.text(s.f.iloc[-1] + pd.Timedelta(days=60), s[col].iloc[-1], f"{n}\n{miles(s[col].iloc[-1])}",
            fontfamily=SANS_XB, fontsize=18, color=colr, va="center", linespacing=1.2)
ax.set_ylim(10000, 44000)
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_yticks([20000, 30000, 40000]); ax.set_yticklabels(["20 mil", "30 mil", "40 mil"])
ejes_limpios(ax, grilla_y=True)
fuente(fig, FUENTE)
pie(fig)
guardar(fig, "carrusel_4.png")

# --- 5. Policía ------------------------------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, "Hallazgo 4 de 6")
titulo(fig, "La Policía Nacional creció", f"+{coma((pol_u/pol_0-1)*100, 0)}%", NARANJA, "en solo dos años",
       f"De {miles(pol_0)} a {miles(pol_u)} vínculos ({MESES[M1-1][:3]} {A1-2} → {MESES[M1-1][:3]} {A1})")
ax = fig.add_axes([0.065, 0.17, 0.87, 0.39])
s = sec_m[(sec_m.sector == "Policía Nacional") & (sec_m.anho >= BASE)]
ax.step(s.f, s.total, where="post", color=AZUL, lw=4)
for fch, txt in [("2025-05-01", "may 2025"), ("2026-05-01", "may 2026")]:
    v = s.set_index("fecha").loc[fch[:7]].total
    ax.annotate(txt, (pd.Timestamp(fch), v), xytext=(-12, 14), textcoords="offset points",
                ha="right", fontfamily=SANS_SB, fontsize=16, color=NAVY)
ax.set_ylim(0, 48000)
ax.set_yticks([0, 20000, 40000]); ax.set_yticklabels(["0", "20 mil", "40 mil"])
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ejes_limpios(ax, grilla_y=True)
fuente(fig, FUENTE)
pie(fig)
guardar(fig, "carrusel_5.png")

# --- 6. Educación estancada -----------------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, "Hallazgo 5 de 6")
mec = sa.loc["Educación (MEC)"]
titulo(fig, "Mientras tanto, Educación", f"−{coma(abs(mec.dif / mec[BASE] * 100), 1)}%", AZUL,
       f"tiene menos vínculos que en {BASE}",
       f"El MEC sigue siendo la mayor institución: {miles(mec[ULT])} vínculos")
ax = fig.add_axes([0.065, 0.17, 0.87, 0.39])
anios = list(range(BASE, ULT + 1))
idx = sec_a[sec_a.anho >= BASE].pivot(index="anho", columns="sector", values="total")
idx = idx / idx.loc[BASE] * 100
series = [("Salud (MSPBS)", NARANJA), ("Policía Nacional", NAVY), ("Educación (MEC)", AZUL)]
pos = sorted([(idx[s_].iloc[-1], s_) for s_, _ in series], reverse=True)
ylab, prev = {}, None
for v, s_ in pos:  # separa etiquetas que quedarían superpuestas
    y_ = v if prev is None else min(v, prev - 7)
    ylab[s_], prev = y_, y_
for sec_, colr in series:
    ax.plot(idx.index, idx[sec_], color=colr, lw=4, marker="o", ms=9, mec=PAPEL, mew=2.5)
    ax.text(ULT + 0.25, ylab[sec_], f"{ETIQ[sec_]} {coma(idx[sec_].iloc[-1], 0)}",
            fontfamily=SANS_XB, fontsize=18, color=colr, va="center")
ax.axhline(100, color="#cfcdc6", lw=1.5, ls=(0, (2, 3)))
ax.set_xlim(BASE - 0.3, ULT + 2.2); ax.set_ylim(90, 160)
ax.set_xticks(anios[::2]); ax.set_yticks([100, 125, 150])
ejes_limpios(ax, grilla_y=True)
fig.text(0.065, 0.575, f"Índice {BASE} = 100 · promedio anual de vínculos", fontfamily=SANS,
         fontsize=16, color=GRIS)
fuente(fig, FUENTE)
pie(fig)
guardar(fig, "carrusel_6.png")

# --- 7. Mujeres --------------------------------------------------------------------------
fig = lienzo(1080, 1350)
cabecera(fig, "Hallazgo 6 de 6")
pm = ult.mujeres / ult.total * 100
titulo(fig, "Las mujeres ya son mayoría:", f"{coma(pm)}%", NARANJA, "de los vínculos del Estado",
       "Pero muy concentradas en Salud y Educación")
x = sec_a[sec_a.anho == ULT].copy()
x["pm"] = x.mujeres / x.total * 100
x = x.sort_values("pm")
ax = fig.add_axes([0.065, 0.16, 0.87, 0.40])
ax.barh(range(len(x)), x.pm, color=NARANJA, height=0.6)
for i, (s_, v) in enumerate(zip(x.sector, x.pm)):
    ax.text(-1.5, i, ETIQ[s_], ha="right", va="center", fontfamily=SANS_SB, fontsize=20, color=TINTA)
    ax.text(v + 1.2, i, f"{coma(v, 0)}%", va="center", fontfamily=SANS_XB, fontsize=20, color=TINTA)
ax.axvline(50, color="#cfcdc6", lw=1.5, ls=(0, (2, 3)))
ax.text(50, len(x) - 0.35, "50%", ha="center", fontfamily=SANS, fontsize=14, color=GRIS)
ax.set_xlim(-38, 85); ax.axis("off")
fuente(fig, f"Fuente: Pulso del Estado con datos de SICCA y SINARH. Promedio {ULT} por sector.")
pie(fig)
guardar(fig, "carrusel_7.png")

# --- Tarjeta social ---------------------------------------------------------------------
fig = lienzo(1200, 630, fondo=NAVY)
logo(fig, 0.05, 0.80, 0.05, fondo="#1d3d5f")
fig.text(0.115, 0.855, "Pulso del Estado", fontfamily=SERIF, fontsize=24, color="white", va="center")
fig.text(0.05, 0.62, "Radiografía del\nempleo público", fontfamily=SERIF, fontsize=46,
         color="white", va="center", linespacing=1.08)
fig.text(0.05, 0.36, miles(rec.total), fontfamily=SERIF, fontsize=58, color=NARANJA, va="center")
fig.text(0.05, 0.225, f"vínculos en {MESES[int(rec.mes)-1]} {int(rec.anho)}, máximo histórico",
         fontfamily=SANS_SB, fontsize=21, color="white", va="center")
fig.text(0.05, 0.08, URL, fontfamily=SANS_SB, fontsize=17, color="#ffd2bf", va="center")
ax = fig.add_axes([0.56, 0.18, 0.4, 0.55])
s = mensual[mensual.anho >= BASE]
ax.plot(s.f, s.total, color=NARANJA, lw=3.5)
ax.axis("off")
guardar(fig, "social.png", NAVY)
print("Listo")
