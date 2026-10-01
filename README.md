# Pulso del Estado

Sitio web de **Pulso del Estado** - Observatorio del Capital Humano del Sector Público paraguayo: datos y análisis sobre la dotación de personal y la masa salarial de la administración pública en el Paraguay.

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
scripts/                 preparación de datos y generación de flyers
assets/                  logo, tipografías y estilos
.github/workflows/       publicación automática en GitHub Pages
```

## Actualizar datos y flyers

Con Python instalado (o en Colab), desde la raíz del repositorio:

```bash
pip install -r requirements.txt
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
