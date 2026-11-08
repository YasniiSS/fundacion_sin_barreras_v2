# Fichas de emergencia con código QR · Fundación Sin Barreras

Prototipo de la Solemne I de Programación II (INGO002, USS).
Genera, a partir de un CSV, una carpeta, una ficha de emergencia (HTML) y un código QR por participante.
Quien encuentra a una persona extraviada escanea el QR y ve a quién llamar y cómo ayudarla.

> Todos los datos son **ficticios**.

El reporte completo (decisiones, código, pruebas y manual) está en **[reporte_solemne1.ipynb](reporte_solemne1.ipynb)**.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

| Acción | Comando |
|---|---|
| Registrar, actualizar o retirar participantes | `python -m src.formulario` |
| Generar carpetas, fichas y QR | `python -m src.main` |
| Imprimir todos los QR | Abrir `participantes/qr_imprimir.html` y presionar Ctrl+P |
| Publicar las fichas | `git add docs` → `git commit` → `git push` |
| Abrir el reporte | `python -m notebook reporte_solemne1.ipynb` |

La primera vez que se ejecuta `main`, se importa `datos/bbdd.csv` a `datos/participantes.csv`.

El formulario corre en el computador (en la terminal o en Jupyter), no en la página publicada: GitHub Pages solo muestra archivos.

## Estructura

```
src/            código (un módulo por tarea)
datos/          PRIVADO: bbdd.csv, participantes.csv y log (excluido de Git)
participantes/  PRIVADO: una carpeta por persona con su ficha y QR (excluido de Git)
docs/           PÚBLICO: lo único que publica GitHub Pages
evidencias/     capturas de las pruebas
```

## Uso de inteligencia artificial

Este proyecto se desarrolló con apoyo de **Claude (Anthropic)**, usado a través de Claude Code. La IA ayudó a analizar el enunciado, proponer el diseño y escribir el código y el reporte. Las decisiones de diseño son del equipo, y los resultados se verificaron con pruebas.
El detalle está en la sección 16 del notebook.

## Publicación (primera vez)

En GitHub: *Settings → Pages → Deploy from a branch → `main` / `/docs`*.
Las fichas quedan en `https://yasniiss.github.io/fundacion_sin_barreras_v2/p/<uuid>.html`.
