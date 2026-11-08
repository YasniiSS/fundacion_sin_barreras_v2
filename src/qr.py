"""
qr.py
Generación masiva de códigos QR.

Responsabilidad:
    Crear un código QR por participante que abra su ficha pública,
    y guardarlo en su carpeta.

Decisiones:
    - La URL se construye solo con el UUID:
      https://yasniiss.github.io/fundacion_sin_barreras_v2/p/<uuid>.html
      No incluye el nombre ni el RUT (privacidad) y no cambia si se
      actualizan los datos: el QR impreso sigue funcionando.
    - Bajo el código se imprime SOLO el UUID (sin nombre): el QR va en la
      ropa o en una pulsera, y un desconocido no debe ver datos sin escanearlo.
      El equipo sabe a quién pertenece cada QR por el nombre del archivo y
      por la hoja de impresión (ambos privados).
    - El archivo se llama qr_<nombre_carpeta>.png y se guarda en la
      carpeta del participante: imagen y persona quedan asociadas.
    - Corrección de errores nivel M (15%): el QR se puede leer aunque
      esté algo sucio o arrugado (ej: en una pulsera o en la ropa).
    - Si el QR no cambió, el archivo no se vuelve a escribir.

Funciones:
    url_participante(registro)       -> str
    crear_imagen_qr(registro)        -> Image
    generar_qr(registro, carpeta)    -> (Path, estado)
    leer_qr(ruta)                    -> str
    verificar_qr(registro, ruta)     -> bool
    generar_qr_lote(lista)           -> list[(registro, Path, estado)]
    generar_hoja_impresion(resultados) -> Path

Hoja de impresión:
    participantes/qr_imprimir.html reúne todos los QR en una página, cada uno
    con el nombre completo y el código bajo cada uno, para que el equipo sepa
    a quién entregar cada QR al imprimirlos en lote. Es privada (no se sube a
    GitHub) y se regenera en cada ejecución, así nunca muestra un QR retirado.
"""

import html
import io
import os
from datetime import date

import qrcode
from PIL import Image, ImageDraw, ImageFont

from src import config
from src.carpetas import nombre_carpeta


def url_participante(registro):
    """URL pública de la ficha, construida con el UUID."""
    return f"{config.URL_BASE}{registro['uuid']}.html"


def _fuente(tamano):
    """Fuente con tildes y ñ: Arial (Windows) o DejaVu (Linux); si no, la de Pillow."""
    for nombre in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default(size=tamano)


def crear_imagen_qr(registro):
    """Crea la imagen del QR con solo el UUID escrito debajo."""
    codigo = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=10, border=4)
    codigo.add_data(url_participante(registro))
    codigo.make(fit=True)
    imagen_qr = codigo.make_image(fill_color="black", back_color="white").convert("RGB")

    ancho, alto = imagen_qr.size
    alto_texto = 30
    imagen = Image.new("RGB", (ancho, alto + alto_texto), "white")
    imagen.paste(imagen_qr, (0, 0))

    dibujo = ImageDraw.Draw(imagen)
    fuente = _fuente(22)
    texto = registro["uuid"]
    ancho_texto = dibujo.textlength(texto, font=fuente)
    dibujo.text(((ancho - ancho_texto) / 2, alto - 12), texto, fill="black", font=fuente)
    return imagen


def generar_qr(registro, carpeta):
    """Guarda el QR en la carpeta del participante.

    Devuelve (ruta, estado) con estado "nuevo", "actualizado" o "sin cambios".
    También borra QR antiguos de la carpeta (si el nombre cambió).
    """
    ruta = carpeta / f"qr_{nombre_carpeta(registro)}.png"

    for archivo in os.listdir(carpeta):
        if archivo.startswith("qr_") and archivo.endswith(".png") and archivo != ruta.name:
            os.remove(carpeta / archivo)

    memoria = io.BytesIO()
    crear_imagen_qr(registro).save(memoria, format="PNG")
    nuevo = memoria.getvalue()

    if os.path.exists(ruta):
        with open(ruta, "rb") as archivo:
            if archivo.read() == nuevo:
                return ruta, "sin cambios"
        estado = "actualizado"
    else:
        estado = "nuevo"
    with open(ruta, "wb") as archivo:
        archivo.write(nuevo)
    return ruta, estado


def leer_qr(ruta):
    """Lee la imagen QR (como lo haría un celular) y devuelve el texto que contiene.

    Usa OpenCV. Devuelve "" si no se pudo leer.
    """
    import cv2   # se importa aquí: solo se necesita para verificar

    imagen = cv2.imread(str(ruta))
    if imagen is None:
        return ""
    # Se prueban dos lectores: el simple falla con algunos QR que sí son válidos.
    for lector in (cv2.QRCodeDetector(), cv2.QRCodeDetectorAruco()):
        texto, _, _ = lector.detectAndDecode(imagen)
        if texto:
            return texto
    return ""


def verificar_qr(registro, ruta):
    """True si el QR contiene exactamente la URL de este participante."""
    return leer_qr(ruta) == url_participante(registro)


def generar_qr_lote(lista):
    """Genera el QR de todos los participantes.

    'lista' contiene tuplas (registro, carpeta).
    Devuelve una lista de tuplas (registro, ruta_qr, estado).
    """
    resultados = []
    for registro, carpeta in lista:
        ruta, estado = generar_qr(registro, carpeta)
        resultados.append((registro, ruta, estado))
    return resultados


def generar_hoja_impresion(resultados):
    """Crea participantes/qr_imprimir.html con todos los QR en una sola página.

    'resultados' es la lista que devuelve generar_qr_lote().
    Las imágenes se enlazan con rutas relativas (carpeta/qr.png), así la hoja
    funciona mientras esté dentro de participantes/.
    Devuelve la ruta de la hoja.
    """
    ordenados = sorted(resultados, key=lambda r: (r[0]["nombres"], r[0]["apellidos"]))
    tarjetas = ""
    for registro, ruta_qr, _ in ordenados:
        imagen = f"{ruta_qr.parent.name}/{ruta_qr.name}"
        tarjetas += f"""
    <div class="tarjeta">
      <img src="{html.escape(imagen)}" alt="QR {html.escape(registro['uuid'])}">
      <p class="nombre">{html.escape(registro['nombres'])} {html.escape(registro['apellidos'])}</p>
      <p class="codigo">Código: {html.escape(registro['uuid'])}</p>
    </div>"""

    contenido = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QR para imprimir - Fundación Sin Barreras</title>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; margin: 24px; color: #1a1a1a; background: #fff; }}
    h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .nota {{ color: #5a6270; margin: 0 0 20px; font-size: 14px; }}
    .grilla {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
    .tarjeta {{ border: 1px dashed #9aa1ab; border-radius: 8px; padding: 10px; text-align: center;
               break-inside: avoid; page-break-inside: avoid; }}
    .tarjeta img {{ width: 100%; max-width: 220px; height: auto; }}
    .nombre {{ font-weight: bold; margin: 6px 0 2px; font-size: 14px; }}
    .codigo {{ color: #5a6270; margin: 0; font-size: 12px; }}
    @media print {{
      body {{ margin: 10mm; }}
      .nota {{ display: none; }}
      .grilla {{ grid-template-columns: repeat(3, 1fr); }}
    }}
  </style>
</head>
<body>
  <h1>Códigos QR para imprimir ({len(ordenados)})</h1>
  <p class="nota">Generado el {date.today().isoformat()}. Documento PRIVADO: no publicar.
     Imprimir con Ctrl+P y recortar por la línea punteada.</p>
  <div class="grilla">{tarjetas}
  </div>
</body>
</html>
"""
    with open(config.RUTA_HOJA_QR, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    return config.RUTA_HOJA_QR
