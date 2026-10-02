# Pulso del Estado

Sitio web de **Pulso del Estado**: datos y análisis sobre la dotación de personal y la masa salarial del sector público paraguayo.

🌐 https://pulsoestado.github.io · 𝕏 [@pulsoestadopy](https://x.com/pulsoestadopy) · 📷 [@pulsoestado](https://instagram.com/pulsoestado)

El sitio está hecho con [Quarto](https://quarto.org) y se publica automáticamente en GitHub Pages cada vez que se sube un cambio a la rama `main`.

---

## Puesta en marcha (una sola vez, todo desde el navegador)

### 1. Subir los archivos

1. Abrí el repositorio `pulsoestado/pulsoestado.github.io` en GitHub.
2. Clic en **Add file → Upload files**.
3. Arrastrá **todo el contenido** de la carpeta descomprimida (no la carpeta en sí): `_quarto.yml`, `index.qmd`, `about.qmd`, las carpetas `assets`, `data`, `posts`, `scripts`, etc.
4. Abajo, en *Commit changes*, escribí un mensaje (por ejemplo "Primera versión del sitio") y clic en **Commit changes**.

> **Ojo con las carpetas ocultas.** El navegador a veces no sube carpetas que empiezan con punto (`.github`). Si después de subir no ves la carpeta `.github` en el repositorio, crealo a mano en el paso 2.

### 2. Crear la publicación automática (si `.github` no se subió)

1. **Add file → Create new file**.
2. En el nombre escribí exactamente: `.github/workflows/publish.yml`
3. Pegá el contenido del archivo `.github/workflows/publish.yml` de esta carpeta.
4. **Commit changes**.

### 3. Activar GitHub Pages

1. En el repositorio: **Settings → Pages**.
2. En *Build and deployment → Source*, elegí **GitHub Actions**.

### 4. Ver el sitio

1. Pestaña **Actions**: vas a ver el proceso "Publicar sitio" en marcha (tarda 3–5 minutos la primera vez).
2. Cuando aparezca el tilde verde ✅, el sitio está en **https://pulsoestado.github.io**.

Si el proceso falla (❌), abrí el detalle y copiá el mensaje de error para revisarlo.

---

## Publicación programada (automática)

Cada nota tiene una fecha (`date:`) en su encabezado. **El sitio publica sola cada nota el día de su fecha**, sin que tengas que hacer nada:

1. Todos los días a las 07:45 (hora de Asunción) la GitHub Action se ejecuta (`schedule` en `.github/workflows/publish.yml`).
2. Antes de generar el sitio corre `scripts/programar_publicaciones.py`, que oculta las notas con fecha futura (les agrega `draft: true  # programada`) y muestra las que ya llegaron.
3. Quarto genera el sitio: las notas programadas no aparecen en la portada, el buscador, el RSS ni el mapa del sitio.

Para programar una nota nueva, basta con ponerle la fecha futura y subirla. Para adelantar o postergar una nota, cambiá su `date:`.

### Notas que esperan datos (`requiere:`)

Algunas notas necesitan datos que todavía no existen (un mes nuevo del DW, la inflación del mes, el proyecto de presupuesto). Esas notas llevan en el encabezado una clave `requiere:`:

```yaml
requiere:
  datos: "2027-06"        # el DW tiene que llegar al menos hasta junio de 2027
  ipc: "2027-05"          # data/manual/ipc_interanual.csv tiene que tener mayo de 2027
  archivo: data/manual/pib_nominal.csv   # el archivo tiene que existir
```

Si llega la fecha y falta algo, la nota **no se publica**: queda como borrador y el proceso de GitHub muestra un aviso amarillo (⚠️ *PENDIENTE*) con lo que falta. Cuando subas el dato, se publica sola en la siguiente ejecución.

Datos manuales que hay que cargar en 2027:

| Archivo | Qué es | Columnas | Lo necesitan |
|---|---|---|---|
| `data/manual/ipc_interanual.csv` | Inflación interanual de cada mes (BCP) | `anho, mes, ipc_interanual, fuente` | cada edición del SITUCAP y "El año en masa salarial" |
| `data/manual/pgn_2028_servicios_personales.csv` | Proyecto de PGN 2028, grupo 100, por institución (MEF) | `codigo_nivel, codigo_entidad, codigo_oee, proyecto_2028` | "Presupuesto 2028" (2 sep 2027) |
| `data/manual/pib_nominal.csv` | PIB nominal anual (BCP, cuentas nacionales) | `anho, pib_millones_gs, fuente` | "La masa salarial y el PIB" (27 sep 2027) |
| `data/manual/poblacion_departamentos_2022.csv` | Población por departamento, Censo 2022 (INE) | ya cargado | notas territoriales |

Además, cada mes hay que actualizar los Excel del DW en `data/raw/` y correr los scripts de preparación (ver abajo): las ediciones del SITUCAP piden el mes correspondiente.

> **Importante:** GitHub desactiva las tareas programadas de un repositorio público si pasan **60 días sin ningún cambio** en el repositorio. Mientras subas algo al menos una vez cada dos meses (por ejemplo, una edición del SITUCAP), la publicación automática sigue funcionando. Si alguna vez se desactiva, se reactiva en **Actions → Publicar sitio → Enable workflow**.

### Calendario cargado

Hay notas cargadas hasta el **30 de diciembre de 2027**: todos los lunes "El dato de la semana", todos los jueves un análisis y el tercer jueves de cada mes una edición del SITUCAP. El plan completo de 2027 está en el documento "Plan editorial 2027". Las primeras:

| Fecha | Nota |
|---|---|
| 2 oct 2026 | Radiografía del empleo público |
| 9 oct 2026 | ¿Cuántas personas cobran del Estado? |
| 16 oct 2026 | ¿Cuánto paga el Estado en salarios? |
| 23 oct 2026 | SITUCAP N.º 1 · Agosto de 2026 |
| 30 oct 2026 | ¿Más gente o mejores sueldos? |
| 6 nov 2026 | La cuota del 5%: personas con discapacidad en el Estado |
| 13 nov 2026 | ¿Ganan menos las mujeres en el Estado? |
| 20 nov 2026 | El Estado por sectores |
| 27 nov 2026 | Vínculos, personas y cargos |
| 4 dic 2026 | ¿Le ganaron los sueldos públicos a la inflación? |
| 11 dic 2026 | ¿De qué está hecho un sueldo público? |
| 18 dic 2026 | Municipalidades por dentro |

## Cómo publicar una nota nueva

1. Creá una carpeta dentro de `posts/` con el formato `AAAA-MM-DD-titulo-corto` (por ejemplo `posts/2026-10-15-masa-salarial-real/`).
2. Dentro, un archivo `index.qmd` con este encabezado:

   ```yaml
   ---
   title: "Título de la nota"
   description: "Resumen de una o dos líneas (aparece en X y en la portada)."
   date: 2026-10-15
   categories: [Masa salarial, SITUCAP]
   image: social.png
   ---
   ```

3. Escribí el texto en Markdown e insertá código Python en bloques ```` ```{python} ````.
4. Subí la carpeta y el sitio se actualiza solo.

**Desde Google Colab:** también podés escribir la nota como cuaderno (`index.ipynb`) en Colab, con una primera celda de texto que tenga el mismo encabezado YAML, y guardarla en esta carpeta con *Archivo → Guardar una copia en GitHub*. Quarto la publica igual que un `.qmd`.

## Estructura

```
_quarto.yml              configuración del sitio (menú, redes, tema, tarjetas para X)
index.qmd                portada (lista automática de notas)
situcap/  datos/         secciones
metodologia.qmd  about.qmd  enlaces.qmd (página para el link de la bio de Instagram)
posts/                   una carpeta por nota
data/processed/          series en CSV (se publican para descarga)
data/raw/                datos originales (no se suben: están en .gitignore)
                         · dw_funcionarios_sicca_sinarh.xlsx (DW_FUNCIONARIOS_SICCA_SINARH)
                         · resumen_personas_vinculos_2015_2025_v2.xlsx
                         · dw_presupuesto_sicca_sinarh.xlsx, dw_nivel_categ_sicca_sinarh.xlsx,
                           dw_funcionarios_sicca.xlsx, bcp_anexo_ipc_salarios.xlsx
situcap/ediciones/       una carpeta por edición mensual del SITUCAP (AAAA-MM)
scripts/                 preparación de datos y generación de flyers
assets/                  logo, tipografías y estilos
.github/workflows/       publicación automática en GitHub Pages
```

## Actualizar datos y flyers

Con Python instalado (o en Colab), desde la raíz del repositorio:

```bash
pip install -r requirements.txt
python scripts/preparar_series.py     # series de masa salarial, sectores, género, discapacidad, municipios y SITUCAP
python scripts/preparar_instituciones.py  # series por institución, objeto de gasto, categorías, BCP e INDEC (después de preparar_series)
python scripts/nueva_edicion_situcap.py 2027 11 16 2028-01-20  # nueva edición del SITUCAP: año, mes, número y fecha de publicación
python scripts/flyers_serie.py        # social.png e ig_1..3.png de las notas de octubre–diciembre
python scripts/preparar_dw.py         # serie principal: data/raw/dw_funcionarios_sicca_sinarh.xlsx
python scripts/flyer_radiografia.py   # carrusel_1..7.png y social.png de la Radiografía
python scripts/preparar_dotacion.py   # personas distintas: data/raw/resumen_personas_vinculos_2015_2025_v2.xlsx
python scripts/flyer_dotacion.py      # flyer_1.png, flyer_2.png y social.png de "¿Cuántas personas…?"
```

## Opcionales

- **Analítica de visitas:** crear una propiedad en Google Analytics y poner el ID en `_quarto.yml` (`google-analytics`).
- **Comentarios:** activar *Discussions* en el repositorio, instalar la app [giscus](https://giscus.app/es), obtener `repo-id` y `category-id` y descomentar el bloque `comments` en `_quarto.yml`.
- **Dominio propio:** comprar el dominio, configurarlo en *Settings → Pages → Custom domain* y actualizar `site-url` en `_quarto.yml`.

## Licencia

Contenido y datos procesados bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es). Código bajo licencia MIT.
