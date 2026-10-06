"""
Genera las notas del plan editorial 2028–2030 (lunes: el dato de la semana; jueves: análisis;
tercer jueves de cada mes: SITUCAP).

    python scripts/plan_2028_2030.py            # escribe posts/ y situcap/ediciones/ y planes/calendario_2028_2030.csv
    python scripts/plan_2028_2030.py --revisar  # solo muestra el calendario, sin escribir

Tipos de pieza:
  re        reedición anual de una nota existente (mismo código, título y fecha nuevos)
  unica     nota nueva (scripts/_plantillas_notas/unicas/*.qmd)
  familia   nota de una serie con parámetros (scripts/_plantillas_notas/*.qmd): institución de la
            semana, departamento, sector, objeto de gasto, ISSP trimestral, quince años, cambio de
            gobierno, monitor electoral, presupuesto
  situcap   edición mensual (scripts/nueva_edicion_situcap.py)

Todas las cifras se calculan al publicarse. Si una nota necesita un mes sin datos, lo estima y lo
rotula (ver pulso.serie_extendida); si necesita un dato que no se puede estimar (la ley de presupuesto
aprobada), espera con `requiere:` y aparece como pendiente.
"""
import calendar
import datetime as dt
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PL = RAIZ / "scripts" / "_plantillas_notas"
sys.path.insert(0, str(RAIZ / "scripts"))
REVISAR = "--revisar" in sys.argv
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# ---------------------------------------------------------------------------------------------------
# Reediciones: slug de la nota original → (título con {Y} = año de la pieza, {Y1} = año anterior,
# descripción nueva o None para conservar la original, reemplazos de texto)
REED = {
    "2027-01-04-el-bache-de-enero": ("El bache de enero de {Y}", None, {}),
    "2027-01-07-empleo-publico-en-10-graficos": ("Balance {Y1}: el empleo público en 10 gráficos", None, {}),
    "2027-01-18-cuanto-cuesta-el-aguinaldo": ("Cuánto costó el aguinaldo de {Y1}", None, {}),
    "2027-02-15-mujeres-en-el-estado": ("Mujeres en el Estado: cuántas son en {Y}", None, {}),
    "2027-02-22-cuantas-instituciones-reportan": ("Cuántas instituciones reportan sus datos ({Y})", None, {}),
    "2027-02-11-educacion-al-empezar-las-clases": ("Educación al empezar las clases de {Y}", None, {}),
    "2027-03-01-la-brecha-en-un-numero": ("La brecha salarial de género en un número ({Y})", None, {}),
    "2027-03-08-mujeres-con-discapacidad": ("8M {Y}: las mujeres con discapacidad en el empleo público", None, {}),
    "2027-03-04-el-techo-de-cristal": ("¿Hay un techo de cristal en el Estado? Medición {Y}", None, {}),
    "2027-04-19-masa-salarial-del-trimestre": ("La masa salarial del último trimestre ({Y})", None, {}),
    "2026-10-30-mas-gente-o-mejores-sueldos": ("Masa salarial {Y1}: ¿más gente o mejores sueldos?",
        "Cuánto creció la masa salarial real del Estado, qué parte se explica por más vínculos y qué parte por mejores remuneraciones, sector por sector.", {}),
    "2027-04-29-cuanto-gana-un-docente": ("¿Cuánto gana un docente? Edición {Y}", None, {}),
    "2027-05-03-cargos-con-sueldo-minimo": ("1 de mayo de {Y}: cargos públicos con sueldo básico bajo el mínimo", None, {}),
    "2027-05-10-promociones-policiales": ("Las promociones policiales de {Y}", None, {}),
    "2027-05-06-publico-y-privado": ("Público y privado: los salarios por rama ({Y})", None, {}),
    "2027-06-28-lo-que-va-del-ano": ("Lo que va de {Y}: vínculos y masa salarial", None, {}),
    "2027-06-03-contratados": ("Contratados {Y}: quiénes son y dónde están", None, {}),
    "2027-07-05-el-nuevo-salario-minimo": ("El salario mínimo de {Y} y la remuneración pública", None, {}),
    "2027-07-26-sueldo-basico-medio": ("El sueldo básico medio de un cargo público ({Y})", None, {}),
    "2027-08-02-el-estado-en-un-ano": ("El Estado en un año: cuántos vínculos sumó ({Y})", None,
        {"; los picos corresponden a la pandemia, cuando Salud sumó miles de contratos, y a las promociones policiales de 2025 y 2026.":
         "; los picos de la serie coinciden con la pandemia, cuando Salud sumó miles de contratos, y con las promociones policiales."}),
    "2027-09-27-masa-salarial-y-pib": ("La masa salarial como porcentaje del PIB ({Y})", None, {}),
    "2027-09-06-vinculos-por-habitante": ("Vínculos públicos por cada 100 habitantes ({Y})", None, {}),
    "2027-09-09-bonificaciones": ("Bonificaciones {Y}: la parte del sueldo que no es sueldo", None, {}),
    "2027-10-25-contrato-o-planta": ("¿Cuesta más un contrato o un cargo de planta? ({Y})", None, {}),
    "2027-08-26-presupuestado-y-pagado": ("Presupuestado y pagado en {Y}", None, {}),
    "2027-07-08-cuanto-cuesta-un-punto": ("¿Cuánto costaría un punto de reajuste en {Y2}?", None, {}),
    "2027-11-01-las-que-mas-crecieron-en-un-ano": ("Las instituciones que más crecieron en el último año ({Y})", None, {}),
    "2027-12-06-aguinaldo-2027": ("Aguinaldo {Y}: cuánto costará", None, {}),
    "2027-12-20-el-ano-en-masa-salarial": ("{Y} en masa salarial", None, {}),
    "2027-12-27-el-dato-del-ano": ("El dato de {Y}: de dónde vino el crecimiento", None,
        {"Un año preelectoral es un buen momento para seguir este número ([contratos en el año preelectoral](../2027-10-04-contratos-ano-preelectoral/)).": ""}),
    "2027-12-02-discapacidad-balance": ("Discapacidad {Y}: ¿avanzó la cuota del 5%?", None, {}),
    "2027-12-23-anuario-2027": ("Anuario {Y}: el empleo público en 12 gráficos", "El cierre del año de Pulso del Estado: dotación, contratos, mujeres, masa salarial, remuneraciones, aguinaldo y discapacidad, en doce gráficos con los últimos datos.",
        {" El lunes, el dato del año; el jueves, las preguntas que nos dejamos para 2028.": "", "Anuario 2027": "Anuario {Y}"}),
    "2026-12-18-municipalidades-por-dentro": ("Municipalidades por dentro ({Y})",
        "Cuánto personal tienen las municipalidades, qué proporción son contratos, cuánto cuestan y cuáles son las más grandes.", {}),
    "2027-08-30-que-mirar-del-presupuesto-2028": ("Qué mirar del Presupuesto {Y1p} en personal", None, "PGN"),
    "2027-09-02-presupuesto-2028": ("Presupuesto {Y1p}: qué pide en personal", None, "PGN"),
    "2027-09-23-masa-salarial-2028-escenarios": ("La masa salarial en {Y1p}: tres escenarios", None, "PGN"),
}

# Familias ---------------------------------------------------------------------------------------------
OBJETOS = [(142, "Contratación de personal de salud"), (133, "Bonificaciones"), (136, "Bonificación por exposición al peligro"),
           (144, "Jornales"), (131, "Subsidio familiar"), (145, "Honorarios profesionales"), (123, "Remuneración extraordinaria"),
           (125, "Remuneración adicional"), (137, "Gratificaciones por servicios especiales"), (122, "Gastos de residencia")]
SECTORES = ["Servicio civil del Ejecutivo", "Poder Judicial", "Entes autónomos y autárquicos", "Gobiernos departamentales",
            "Empresas públicas", "Poder Legislativo", "SA del Estado", "Otros organismos", "Salud", "Fuerzas públicas", "Educación", "Municipalidades"]
NO_INST = {(23, 40, 1), (28, 1, 1), (12, 7, 1), (12, 3, 2), (11, 1, 1), (11, 2, 1), (11, 3, 1), (13, 1, 1), (13, 2, 1), (12, 9, 1), (12, 8, 1)}

U = {  # clave: (archivo, título, descripción, categorías)
    "contratos_vencen": ("contratos_vencen", "Cuántos contratos vencen con el año", "Cuántos contratos del Estado se caen entre diciembre y enero, en qué sectores y cómo se compara con años anteriores.", ["El dato de la semana", "Contratados"]),
    "correcciones_lanz": ("correcciones_lanz", "Cómo corregimos los datos: el registro de correcciones", "Un registro público de cada corrección a los datos de origen y una estimación rotulada del último mes, para que las limitaciones de los registros queden a la vista.", ["El dato de la semana", "Metodología", "Datos abiertos"]),
    "issp_lanzamiento": ("issp_lanzamiento", "El Índice de Sueldos del Sector Público: cómo leerlo", "Un índice trimestral de cuánto sube el sueldo básico de los mismos cargos, sin el efecto de quién entra y quién sale del Estado.", ["ISSP", "Remuneraciones", "Productos"]),
    "tres_meses": ("tres_meses", "El Estado a tres meses de votar", "Cuántos vínculos pagaba el Estado tres meses antes de las elecciones generales de 2028, frente a 2018 y 2023.", ["El dato de la semana", "Ciclo electoral"]),
    "deriva": ("deriva", "La deriva salarial: cuánto se paga además del sueldo básico", "Por cada 100 guaraníes de sueldo básico, cuánto paga el Estado en bonificaciones y otros complementos, sector por sector y desde 2016.", ["Remuneraciones", "Bonificaciones", "Estructura salarial"]),
    "traspaso_cifras": ("traspaso_cifras", "El Estado que recibe el próximo gobierno, en cinco cifras", "Vínculos, contratos, masa salarial, remuneración media y sueldo de los mismos cargos: el punto de partida del gobierno que asume el 15 de agosto de 2028.", ["El dato de la semana", "Ciclo electoral"]),
    "informe_traspaso": ("informe_traspaso", "Informe de traspaso: el Estado de 2023 a 2028", "Cuántos vínculos permanentes y contratados sumó el Estado entre julio de 2023 y julio de 2028, y cómo se compara con el período 2018–2023.", ["Ciclo electoral", "Dotación", "Masa salarial"]),
    "compresion": ("compresion", "Compresión salarial: cuánto más gana la categoría más alta", "Cuántas veces gana la categoría salarial mejor paga frente a la peor paga en cada institución, y cómo cambió la dispersión de los sueldos básicos.", ["Remuneraciones", "Categorías", "Estructura salarial"]),
    "periodo_sector": ("periodo_sector", "Cinco años de gobierno, sector por sector", "Qué sectores sumaron y cuáles perdieron personal entre 2023 y 2028, con contratos y masa salarial real.", ["Ciclo electoral", "Sectores"]),
    "rotacion": ("rotacion", "Rotación: las instituciones con más recambio de personas", "Cuántas personas distintas pasan por cada institución en un año frente a las que tiene en un mes promedio: una aproximación al recambio de personal.", ["Dotación", "Personas", "Instituciones"]),
    "simulador_lanz": ("simulador_lanz", "Cómo usar el simulador de reajustes", "Cuánto cuesta por año un aumento salarial según a quién alcanza y sobre qué base se aplica: una herramienta para seguir el debate del Presupuesto.", ["Productos", "Presupuesto", "Masa salarial"]),
    "fichas_lanz": ("fichas_lanz", "Las fichas por institución: cómo usarlas", "Una página para cada institución del Estado con su personal, contratos, mujeres, masa salarial, categorías y personas con discapacidad.", ["Productos", "Instituciones"]),
    "cambiaron": ("cambiaron", "Las instituciones que más cambiaron con el nuevo gobierno", "Las cinco instituciones con el mayor cambio de vínculos desde el último mes completo del gobierno anterior.", ["El dato de la semana", "Ciclo electoral", "Instituciones"]),
    "techo_decada": ("techo_decada", "Techo de cristal: ¿se movió en diez años?", "La participación de las mujeres en el 10% de cargos mejor pagos de cada institución, desde 2018.", ["Género", "Remuneraciones"]),
    "issp_docentes": ("issp_docentes", "El índice de sueldos de los docentes", "Cuánto subió el sueldo básico real de los mismos cargos en Educación frente al resto del Estado.", ["El dato de la semana", "Educación", "ISSP"]),
    "explorador_lanz": ("explorador_lanz", "El explorador de datos: tres preguntas en un minuto", "Vínculos, contratos, mujeres y masa salarial por sector desde 2015, para graficar y descargar.", ["Productos", "Datos abiertos"]),
    "salud_diez": ("salud_diez", "Salud: diez años de contratos", "Cómo cambió la planta del Ministerio de Salud y del IPS antes, durante y después de la pandemia.", ["Salud", "Contratados"]),
    "ley1": ("ley1", "La ley de la función pública a cuatro años (I): lo que muestran los datos", "Qué de la Ley 7445/2025 se puede seguir con los datos públicos de SINARH y SICCA, y qué no.", ["Servicio civil", "Gestión pública", "Contratados"]),
    "ley2": ("ley2", "La ley de la función pública a cuatro años (II): contratos, planta y escalas", "Vínculos permanentes, contratos y escalas salariales antes y después de julio de 2025.", ["Servicio civil", "Gestión pública", "Categorías"]),
    "mitad_mandato": ("mitad_mandato", "Gobernaciones y municipalidades a mitad de mandato", "Cuánto cambió el personal de municipalidades y gobernaciones desde las elecciones municipales de octubre de 2026.", ["Municipalidades", "Gobernaciones", "Ciclo electoral"]),
    "atraso": ("atraso", "Instituciones que reportan con atraso", "Cuántas instituciones todavía no cargaron los datos del último mes y cuántos vínculos faltan.", ["El dato de la semana", "Metodología"]),
    "calidad": ("calidad", "Calidad de datos: el primer informe anual", "Cuánto tardan en llegar los datos de SINARH y SICCA, qué sectores cargan con atraso y qué correcciones aplicamos.", ["Metodología", "Datos abiertos"]),
    "informe_nota": ("informe_nota", "Estado del capital humano público: el informe anual", "El informe anual de Pulso del Estado, en web y PDF: dotación, masa salarial, sueldos, género, discapacidad y metodología.", ["Productos", "Balance"]),
    "estado_2015": ("estado_2015", "El Estado de hoy frente al de 2015", "Cuántos vínculos más paga el Estado que en 2015, en qué sectores y con qué contratos.", ["El dato de la semana", "Dotación"]),
    "quince_genero": ("quince_genero", "Quince años de datos: género", "La participación de las mujeres y la brecha de sueldo básico en el Estado, de 2015 a hoy.", ["Quince años", "Género"]),
    "minimo15": ("minimo15", "Quince años de salario mínimo y sueldo básico público", "Cómo evolucionaron, descontada la inflación, el salario mínimo legal y el sueldo básico medio de un cargo público.", ["El dato de la semana", "Salario mínimo", "Quince años"]),
    "municipal_fin": ("municipal_fin", "Municipalidades al final del mandato", "Cuánto cambió el personal municipal desde las elecciones de 2026, frente al mismo tramo del mandato anterior.", ["El dato de la semana", "Municipalidades", "Ciclo electoral"]),
    "proyecciones_nota": ("proyecciones_nota", "Proyecciones 2030–2035: cuánto personal y cuánta masa salarial", "Tres escenarios de vínculos y masa salarial real hasta 2035 según las tendencias actuales. No son pronósticos.", ["Proyecciones", "Dotación", "Masa salarial"]),
    "pcd15": ("pcd15", "Quince años de cuota de discapacidad", "Cuánto avanzó la proporción de personas con discapacidad en el Estado desde 2015 y cuántas faltan para el 5% legal.", ["El dato de la semana", "Discapacidad", "Quince años"]),
    "decada": ("decada", "Anuario 2030: diez preguntas para la próxima década", "Quince años de datos y diez preguntas sobre el empleo público hasta 2035, con lo que falta publicar para responderlas.", ["Balance", "Agenda"]),
}

# Plan mes a mes: (L = lunes, J = jueves sin contar el SITUCAP). Cada pieza: ("re", slug) | ("u", clave) | (familia, params)
PLAN = {
 2028: {
  1: {"L": [("re", "2027-01-04-el-bache-de-enero"), ("u", "contratos_vencen"), ("u", "correcciones_lanz"), ("re", "2027-01-18-cuanto-cuesta-el-aguinaldo")],
      "J": [("re", "2027-01-07-empleo-publico-en-10-graficos"), ("u", "issp_lanzamiento")]},
  2: {"L": [("u", "tres_meses"), ("re", "2027-02-15-mujeres-en-el-estado"), ("re", "2027-02-22-cuantas-instituciones-reportan")],
      "J": [("monitor", dict(ELEC="2028-04-01", PREV=["2018-04-22", "2023-04-30"], FASE="antes", SECTOR=None, REF=False, T="Monitor electoral I: los contratos antes de votar en 2028")),
            ("re", "2027-02-11-educacion-al-empezar-las-clases")]},
  3: {"L": [("re", "2027-03-01-la-brecha-en-un-numero"), ("re", "2027-03-08-mujeres-con-discapacidad")],
      "J": [("u", "deriva"), ("issp", {}), ("re", "2027-03-04-el-techo-de-cristal")]},
  4: {"L": [("u", "traspaso_cifras"), ("re", "2027-04-19-masa-salarial-del-trimestre")],
      "J": [("u", "informe_traspaso"), ("re", "2026-10-30-mas-gente-o-mejores-sueldos"), ("re", "2027-04-29-cuanto-gana-un-docente")]},
  5: {"L": [("re", "2027-05-03-cargos-con-sueldo-minimo"), ("re", "2027-05-10-promociones-policiales")],
      "J": [("monitor", dict(ELEC="2028-04-01", PREV=["2018-04-22", "2023-04-30"], FASE="despues", SECTOR=None, REF=False, T="Monitor electoral II: los contratos después de votar")),
            ("re", "2027-05-06-publico-y-privado")]},
  6: {"L": [("re", "2027-06-28-lo-que-va-del-ano")], "J": [("u", "compresion"), ("issp", {}), ("re", "2027-06-03-contratados")]},
  7: {"L": [("re", "2027-07-05-el-nuevo-salario-minimo"), ("re", "2027-07-26-sueldo-basico-medio")], "J": [("u", "periodo_sector")]},
  8: {"L": [("gobierno", dict(K=0, T="El Estado el día del traspaso", ETIQ="en el mes del traspaso")), ("re", "2027-08-02-el-estado-en-un-ano"), ("re", "2027-08-30-que-mirar-del-presupuesto-2028")],
      "J": [("gobierno", dict(K=1, T="Cambio de gobierno en tiempo real: los contratos de agosto", ETIQ="en el primer mes del nuevo gobierno"))]},
  9: {"L": [("re", "2027-09-27-masa-salarial-y-pib"), ("re", "2027-09-06-vinculos-por-habitante")],
      "J": [("re", "2027-09-02-presupuesto-2028"), ("issp", {}), ("re", "2027-09-23-masa-salarial-2028-escenarios"), ("re", "2027-09-09-bonificaciones")]},
  10: {"L": [("gobierno", dict(K=2, T="Los primeros contratos del nuevo gobierno", ETIQ="en los primeros dos meses")), ("re", "2027-10-25-contrato-o-planta")],
       "J": [("u", "rotacion"), ("re", "2027-08-26-presupuestado-y-pagado")]},
  11: {"L": [("re", "2027-07-08-cuanto-cuesta-un-punto"), ("re", "2027-11-01-las-que-mas-crecieron-en-un-ano")],
       "J": [("gobierno", dict(K=3, T="Los primeros 100 días: el empleo público", ETIQ="en los primeros cien días")), ("pgn_congreso", {}), ("u", "simulador_lanz")]},
  12: {"L": [("re", "2027-12-06-aguinaldo-2027"), ("re", "2027-12-20-el-ano-en-masa-salarial"), ("re", "2027-12-27-el-dato-del-ano")],
       "J": [("re", "2027-12-02-discapacidad-balance"), ("issp", {}), ("re", "2027-12-23-anuario-2027")]},
 },
 2029: {
  1: {"L": [("re", "2027-01-04-el-bache-de-enero"), ("u", "cambiaron"), ("re", "2027-01-18-cuanto-cuesta-el-aguinaldo")],
      "J": [("re", "2027-01-07-empleo-publico-en-10-graficos"), ("u", "fichas_lanz")]},
  2: {"L": [("gobierno", dict(K=6, T="Seis meses de gobierno: el empleo público", ETIQ="en los primeros seis meses")), ("re", "2027-02-15-mujeres-en-el-estado"), ("re", "2027-02-22-cuantas-instituciones-reportan")],
      "J": [("re", "2027-02-11-educacion-al-empezar-las-clases")]},
  3: {"L": [("re", "2027-03-01-la-brecha-en-un-numero"), ("re", "2027-03-08-mujeres-con-discapacidad")], "J": [("u", "techo_decada"), ("issp", {})]},
  4: {"L": [("u", "issp_docentes"), ("re", "2027-04-19-masa-salarial-del-trimestre")],
      "J": [("re", "2026-10-30-mas-gente-o-mejores-sueldos"), ("re", "2027-04-29-cuanto-gana-un-docente")]},
  5: {"L": [("re", "2027-05-03-cargos-con-sueldo-minimo"), ("re", "2027-05-10-promociones-policiales")],
      "J": [("u", "explorador_lanz"), ("u", "salud_diez"), ("re", "2027-05-06-publico-y-privado")]},
  6: {"L": [("re", "2027-06-28-lo-que-va-del-ano")], "J": [("u", "ley1"), ("issp", {}), ("re", "2027-06-03-contratados")]},
  7: {"L": [("re", "2027-07-05-el-nuevo-salario-minimo"), ("re", "2027-07-26-sueldo-basico-medio")], "J": [("u", "ley2")]},
  8: {"L": [("re", "2027-08-02-el-estado-en-un-ano"), ("re", "2027-08-30-que-mirar-del-presupuesto-2028")],
      "J": [("gobierno", dict(K=12, T="Un año de gobierno frente a los dos anteriores", ETIQ="en el primer año de gestión"))]},
  9: {"L": [("re", "2027-09-27-masa-salarial-y-pib"), ("re", "2027-09-06-vinculos-por-habitante")],
      "J": [("re", "2027-09-02-presupuesto-2028"), ("issp", {}), ("re", "2027-09-23-masa-salarial-2028-escenarios"), ("re", "2027-09-09-bonificaciones")]},
  10: {"L": [("re", "2027-10-25-contrato-o-planta"), ("re", "2027-11-01-las-que-mas-crecieron-en-un-ano")], "J": [("u", "mitad_mandato"), ("re", "2027-08-26-presupuestado-y-pagado")]},
  11: {"L": [("u", "atraso"), ("re", "2027-07-08-cuanto-cuesta-un-punto")], "J": [("u", "calidad"), ("pgn_congreso", {}), ("u", "informe_nota")]},
  12: {"L": [("re", "2027-12-06-aguinaldo-2027"), ("re", "2027-12-20-el-ano-en-masa-salarial"), ("re", "2027-12-27-el-dato-del-ano")],
       "J": [("re", "2027-12-02-discapacidad-balance"), ("issp", {}), ("re", "2027-12-23-anuario-2027")]},
 },
 2030: {
  1: {"L": [("re", "2027-01-04-el-bache-de-enero"), ("u", "estado_2015"), ("re", "2027-01-18-cuanto-cuesta-el-aguinaldo")],
      "J": [("re", "2027-01-07-empleo-publico-en-10-graficos"), ("quince", dict(SECTOR=None, T="Quince años de datos: el Estado entero"))]},
  2: {"L": [("re", "2027-02-15-mujeres-en-el-estado"), ("re", "2027-02-22-cuantas-instituciones-reportan")],
      "J": [("quince", dict(SECTOR="Educación", T="Quince años de datos: Educación")), ("re", "2027-02-11-educacion-al-empezar-las-clases")]},
  3: {"L": [("re", "2027-03-01-la-brecha-en-un-numero"), ("re", "2027-03-08-mujeres-con-discapacidad")], "J": [("u", "quince_genero"), ("issp", {}), ("re", "2027-03-04-el-techo-de-cristal")]},
  4: {"L": [("re", "2027-09-27-masa-salarial-y-pib"), ("re", "2027-04-19-masa-salarial-del-trimestre")],
      "J": [("re", "2026-10-30-mas-gente-o-mejores-sueldos"), ("re", "2027-04-29-cuanto-gana-un-docente")]},
  5: {"L": [("u", "minimo15"), ("re", "2027-05-03-cargos-con-sueldo-minimo")],
      "J": [("quince", dict(SECTOR="Salud", T="Quince años de datos: Salud")), ("re", "2027-05-06-publico-y-privado")]},
  6: {"L": [("re", "2027-06-28-lo-que-va-del-ano")], "J": [("quince", dict(SECTOR="Fuerzas públicas", T="Quince años de datos: Fuerzas públicas")), ("issp", {})]},
  7: {"L": [("re", "2027-07-05-el-nuevo-salario-minimo"), ("re", "2027-07-26-sueldo-basico-medio")], "J": [("re", "2027-06-03-contratados")]},
  8: {"L": [("u", "municipal_fin"), ("re", "2027-08-02-el-estado-en-un-ano"), ("re", "2027-08-30-que-mirar-del-presupuesto-2028")], "J": [("u", "proyecciones_nota")]},
  9: {"L": [("re", "2027-09-06-vinculos-por-habitante")],
      "J": [("re", "2027-09-02-presupuesto-2028"), ("issp", {}), ("re", "2027-09-23-masa-salarial-2028-escenarios"), ("re", "2027-09-09-bonificaciones")]},
  10: {"L": [("re", "2027-10-25-contrato-o-planta"), ("re", "2026-12-18-municipalidades-por-dentro")],
       "J": [("quince", dict(SECTOR="Municipalidades", T="Quince años de datos: las municipalidades")), ("re", "2027-08-26-presupuestado-y-pagado")]},
  11: {"L": [("u", "pcd15"), ("re", "2027-07-08-cuanto-cuesta-un-punto")],
       "J": [("u", "informe_nota"), ("pgn_congreso", {}), ("quince", dict(SECTOR="Servicio civil del Ejecutivo", T="Quince años de datos: el servicio civil"))]},
  12: {"L": [("re", "2027-12-06-aguinaldo-2027"), ("re", "2027-12-20-el-ano-en-masa-salarial"), ("re", "2027-12-27-el-dato-del-ano")],
       "J": [("re", "2027-12-02-discapacidad-balance"), ("issp", {}), ("u", "decada")]},
 },
}


def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return "-".join(t.split("-")[:9])


def dias(y, m, wd):
    return [dt.date(y, m, d) for d in range(1, calendar.monthrange(y, m)[1] + 1) if dt.date(y, m, d).weekday() == wd]


def front(meta, extra=""):
    def q(s):
        return '"' + s.replace('"', '\\"') + '"'
    cats = "[" + ", ".join(meta["cats"]) + "]"
    return (f"---\ntitle: {q(meta['title'])}\ndescription: {q(meta['desc'])}\ndate: {meta['date']}\ncategories: {cats}\n"
            f"image: social.png\nimage-alt: {q(meta['title'])}\nresources: [\"ig_*.png\"]\nplan: \"2028-2030\"\n{extra}---\n\n")


SETUP = '''```{{python}}
#| label: setup
import sys, pathlib
raiz = next(p for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents] if (p / "_quarto.yml").exists())
sys.path.insert(0, str(raiz / "scripts"))
from pulso import *
import numpy as np
import plotly.graph_objects as go
{params}
```

'''


def leer_post(slug):
    t = (RAIZ / "posts" / slug / "index.qmd").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", t, flags=re.S)
    import yaml
    meta = yaml.safe_load(m.group(1))
    return meta, t[m.end():]


def main():
    from pulso import leer, vin_promedio_oee, ultimo_anio_completo, K_OEE
    UA = ultimo_anio_completo()
    p = vin_promedio_oee(UA).sort_values("total", ascending=False)
    insts = [tuple(int(x) for x in k) for k in p[K_OEE].itertuples(index=False, name=None) if tuple(int(x) for x in k) not in NO_INST]
    insts = [k for k in insts if not p.set_index(K_OEE).loc[k, "sector"] in ("Municipalidades",)][:150]
    pob = pd.read_csv(RAIZ / "data/manual/poblacion_departamentos_2022.csv").set_index("codigo_departamento")
    deps = [(int(c), r.departamento) for c, r in pob.iterrows() if c > 0]
    q_lun = []
    oi = 0
    for i, k in enumerate(insts):
        q_lun.append(("institucion", dict(KEY=k)))
        if i % 3 == 2 and oi < len(OBJETOS):
            q_lun.append(("objeto", dict(OBJ=OBJETOS[oi][0], NOMBRE=OBJETOS[oi][1]))); oi += 1
    q_jue = []
    si = 0
    for i, (c, n) in enumerate(deps):
        q_jue.append(("departamento", dict(DEP=c, DEPNOMBRE=n)))
        if i % 2 == 1 and si < len(SECTORES):
            q_jue.append(("sector", dict(SECTOR=SECTORES[si]))); si += 1
    q_jue += [("sector", dict(SECTOR=s)) for s in SECTORES[si:]]
    q_jue += [("objeto", dict(OBJ=o, NOMBRE=n)) for o, n in OBJETOS[oi:]]
    q_jue += [("sector", dict(SECTOR=s)) for _ in range(2) for s in SECTORES]   # el sector, de nuevo cada año

    piezas, ed_n = [], 16
    carry_L, carry_J = [], []
    for y in (2028, 2029, 2030):
        for m in range(1, 13):
            lun, jue = dias(y, m, 0), dias(y, m, 3)
            situ = jue[2]
            jue = [d for d in jue if d != situ]
            L, J = carry_L + list(PLAN[y][m]["L"]), carry_J + list(PLAN[y][m]["J"])
            carry_L, carry_J = L[len(lun):], J[len(jue):]      # lo que no entra pasa al mes siguiente
            L, J = L[:len(lun)], J[:len(jue)]
            if carry_L or carry_J:
                print(f"  {y}-{m:02d}: pasan al mes siguiente {len(carry_L)} lunes y {len(carry_J)} jueves")
            while len(L) < len(lun):
                L.append(q_lun.pop(0))
            while len(J) < len(jue):
                J.append(q_jue.pop(0))
            for d, it in zip(lun, L):
                piezas.append((d, "L", it))
            for d, it in zip(jue, J):
                piezas.append((d, "J", it))
            am = (y, m - 2) if m > 2 else (y - 1, m + 10)
            piezas.append((situ, "S", ("situcap", dict(A=am[0], M=am[1], N=ed_n)))); ed_n += 1
    piezas.sort(key=lambda x: x[0])
    filas = []
    slugs = {}
    # primera pasada: títulos y slugs
    for d, dia, (kind, prm) in piezas:
        y = d.year
        if kind == "issp":
            prm = dict(prm, _mes=d.month)
        meta = titulo(kind, prm, y)
        meta["date"] = d.isoformat()
        if kind == "situcap":
            meta["slug"] = f"{prm['A']}-{prm['M']:02d}"
        else:
            meta["slug"] = f"{d.isoformat()}-{slugify(meta['title'])}"
            if kind == "u":
                slugs[prm] = meta["slug"]
            if kind == "re" and prm == "2027-09-02-presupuesto-2028":
                slugs[f"_pgn{y + 1}"] = meta["slug"]
        filas.append((d, dia, kind, prm, meta))
    estados = []
    for d, dia, kind, prm, meta in filas:
        estado = escribir(kind, prm, meta, d, slugs) if not REVISAR else "—"
        estados.append(estado)
    cal = pd.DataFrame([dict(fecha=d.isoformat(), dia={"L": "lunes", "J": "jueves", "S": "jueves (SITUCAP)"}[dia], tipo=kind if kind != "u" else "unica",
                             titulo=meta["title"], ruta=("situcap/ediciones/" if kind == "situcap" else "posts/") + meta["slug"], datos=e)
                        for (d, dia, kind, prm, meta), e in zip(filas, estados)])
    if not REVISAR:
        (RAIZ / "planes").mkdir(exist_ok=True)
        cal.to_csv(RAIZ / "planes" / "calendario_2028_2030.csv", index=False)
    print(cal.groupby([cal.fecha.str[:4], "tipo"]).size().unstack(fill_value=0))
    print(len(cal), "piezas")


def titulo(kind, prm, y):
    if kind == "re":
        t, dsc, _ = REED[prm]
        meta, _b = leer_post(prm)
        return dict(title=t.format(Y=y, Y1=y - 1, Y2=y + 1, Y1p=y + 1), desc=(dsc or meta.get("description", "")).replace("2028", str(y + 1)) if REED[prm][2] == "PGN" else (dsc or meta.get("description", "")),
                    cats=[c for c in meta.get("categories", [])])
    if kind == "u":
        f, t, dsc, cats = U[prm]
        return dict(title=t, desc=dsc, cats=cats)
    if kind == "situcap":
        return dict(title=f"SITUCAP N.º {prm['N']} · {MESES[prm['M'] - 1].capitalize()} de {prm['A']}", desc="", cats=[])
    if kind == "institucion":
        from pulso import instituciones, K_OEE
        n = instituciones().set_index(K_OEE).loc[prm["KEY"], "nombre_largo"]
        return dict(title=f"La institución de la semana: {n}", desc=f"Personal, contratos, mujeres, masa salarial y remuneración media de {n}, con el enlace a su ficha completa.",
                    cats=["La institución de la semana", "Instituciones"])
    if kind == "departamento":
        return dict(title=f"{prm['DEPNOMBRE']}: la gobernación y las municipalidades por dentro",
                    desc=f"Cuánto personal tienen la gobernación y las municipalidades de {prm['DEPNOMBRE']}, cuántos son contratos y cuánto representa por habitante.",
                    cats=["Territorio", "Municipalidades", "Gobernaciones"])
    if kind == "sector":
        return dict(title=f"{prm['SECTOR']}: el último año en cifras", desc=f"Vínculos, contratos, masa salarial real, sueldos de los mismos cargos y las instituciones que más cambiaron en {prm['SECTOR'].lower()}.",
                    cats=["Sectores", prm["SECTOR"]])
    if kind == "objeto":
        return dict(title=f"Objeto {prm['OBJ']}: {prm['NOMBRE'].lower()}, quién lo paga y cuánto", desc=f"Cuánto paga el Estado en el objeto de gasto {prm['OBJ']} ({prm['NOMBRE'].lower()}), qué instituciones lo usan y cómo evolucionó.",
                    cats=["Objetos de gasto", "Masa salarial"])
    if kind == "issp":
        tq = {3: f"cuarto trimestre de {y - 1}", 6: f"primer trimestre de {y}", 9: f"segundo trimestre de {y}", 12: f"tercer trimestre de {y}"}[prm["_mes"]]
        return dict(title=f"ISSP del {tq}: los sueldos de los mismos cargos", desc="El Índice de Sueldos del Sector Público del último trimestre con datos: cuánto subió el sueldo básico de los mismos cargos, en total y por sector.",
                    cats=["ISSP", "Remuneraciones"])
    if kind == "quince":
        return dict(title=prm["T"], desc=f"Vínculos, contratos, masa salarial real y sueldos de los mismos cargos de {(prm['SECTOR'] or 'el Estado entero').lower()} desde 2015.",
                    cats=["Quince años", prm["SECTOR"] or "Dotación"])
    if kind == "gobierno":
        return dict(title=prm["T"], desc="Cómo cambiaron los contratos y la planta del Estado con el cambio de gobierno de 2028, frente a los de 2018 y 2023.",
                    cats=(["El dato de la semana"] if prm["K"] in (0, 2, 6) else []) + ["Ciclo electoral", "Contratados"])
    if kind == "monitor":
        return dict(title=prm["T"], desc="Cuánto cambiaron los contratos del Estado en los seis meses alrededor de la elección, frente a los mismos meses de otros años y a los ciclos anteriores.",
                    cats=["Ciclo electoral", "Contratados"])
    if kind == "pgn_congreso":
        return dict(title=f"Presupuesto {y + 1}: qué cambió el Congreso en personal", desc=f"Cuánto modificó el Congreso el proyecto del Ejecutivo para servicios personales en el Presupuesto {y + 1}, sector por sector.",
                    cats=["Presupuesto", f"PGN {y + 1}"])
    raise ValueError(kind)


def escribir(kind, prm, meta, d, slugs):
    y = d.year
    if kind == "situcap":
        dest = RAIZ / "situcap" / "ediciones" / meta["slug"] / "index.qmd"
        if not dest.exists():
            subprocess.run([sys.executable, str(RAIZ / "scripts" / "nueva_edicion_situcap.py"), str(prm["A"]), str(prm["M"]), str(prm["N"]), d.isoformat()], check=True, capture_output=True)
        return f"espera los datos de {prm['A']}-{prm['M']:02d}"
    dest = RAIZ / "posts" / meta["slug"] / "index.qmd"
    dest.parent.mkdir(parents=True, exist_ok=True)
    extra, estado = "", "con los datos disponibles"
    if kind == "re":
        _m, body = leer_post(prm)
        body = re.sub(r"\A\s*<!--.*?-->\s*", "", body, flags=re.S) if REED[prm][2] != "PGN" else body
        repl = REED[prm][2]
        if repl == "PGN":
            Y = y + 1
            body = body.replace("2027-09-02-presupuesto-2028", "@@PGN@@")
            body = body.replace("2029", str(Y + 1)).replace("2028", str(Y))
            body = body.replace("@@PGN@@", slugs.get(f"_pgn{Y}", "2027-09-02-presupuesto-2028"))
            if "presupuesto-2028" in prm:
                estado = f"estimación provisoria hasta que se cargue data/manual/pgn_{Y}_servicios_personales.csv"
        else:
            for a, b in repl.items():
                body = body.replace(a, b.format(Y=y))
        txt = front(meta) + body
    elif kind == "u":
        body = (PL / "unicas" / f"{U[prm][0]}.qmd").read_text(encoding="utf-8")
        txt = front(meta) + SETUP.format(params="") + body
        if "serie_extendida" in body or "aviso_estimacion" in body:
            estado = "estima los meses sin datos (rotulado)"
    else:
        fam = {"institucion": "institucion", "departamento": "departamento", "sector": "sector", "objeto": "objeto", "issp": "issp",
               "quince": "quince", "gobierno": "gobierno", "monitor": "monitor", "pgn_congreso": "pgn_congreso"}[kind]
        body = (PL / f"{fam}.qmd").read_text(encoding="utf-8")
        params = []
        if kind == "institucion":
            params.append(f"KEY = {prm['KEY']}")
        elif kind == "departamento":
            params += [f"DEP = {prm['DEP']}", f"DEPNOMBRE = {prm['DEPNOMBRE']!r}"]
        elif kind in ("sector", "quince"):
            params.append(f"SECTOR = {prm['SECTOR']!r}")
        elif kind == "objeto":
            params += [f"OBJ = {prm['OBJ']}", f"NOMBRE = {prm['NOMBRE']!r}"]
        elif kind == "gobierno":
            params += [f"K = {prm['K']}", f"ETIQ = {prm['ETIQ']!r}", f"TITULO_RED = {prm['T'].replace(': ', ':' + chr(10), 1)!r}"]
            estado = "estima los meses sin datos (rotulado)"
        elif kind == "monitor":
            params += [f"ELEC = {prm['ELEC']!r}", f"PREV = {prm['PREV']!r}", f"FASE = {prm['FASE']!r}", f"SECTOR = {prm['SECTOR']!r}",
                       f"REF_CONFIRMADA = {prm['REF']}", f"TITULO_RED = {prm['T'].replace(': ', ':' + chr(10), 1)!r}"]
            estado = "estima los meses sin datos (rotulado)"
        elif kind == "pgn_congreso":
            Y = y + 1
            body = body.replace("[[Y]]", str(Y))
            extra = f'requiere:\n  archivo:\n    - "data/manual/pgn_{Y}_servicios_personales.csv"\n    - "data/manual/pgn_{Y}_aprobado.csv"\n'
            estado = f"pendiente: necesita el proyecto y la ley aprobada del PGN {Y}"
        txt = front(meta, extra) + SETUP.format(params="\n".join(params)) + body
    # enlaces entre notas nuevas
    txt = re.sub(r"\[\[LINK:([a-z_0-9]+)\]\]", lambda m_: f"../{slugs[m_.group(1)]}/", txt)
    txt = re.sub(r"\[\[SLUG:([a-z_0-9]+)\]\]", lambda m_: slugs[m_.group(1)], txt)
    dest.write_text(txt, encoding="utf-8")
    return estado


if __name__ == "__main__":
    main()
