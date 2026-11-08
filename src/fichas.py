"""
fichas.py
Generación de la ficha de emergencia (HTML) de cada participante.

Responsabilidad:
    Crear una página HTML por participante, legible desde un teléfono,
    y guardarla en su carpeta privada y en docs/p/ (carpeta pública).

Decisiones:
    - Formato HTML: se abre en cualquier navegador de celular, el texto se
      adapta a la pantalla y los teléfonos son botones para llamar (tel:).
    - Orden de lectura: 1) nombre, 2) a quién llamar, 3) cómo ayudar,
      4) referencia de ubicación. Lo urgente va primero.
    - Se muestra solo el PRIMER NOMBRE, sin apellidos: basta para llamar a
      la persona por su nombre y calmarla. La ficha muestra solo: primer
      nombre, contactos de emergencia, características (cómo ayudar) y
      ubicación general (comuna). Nunca se muestran apellidos, RUT, edad,
      email ni dirección exacta (ver config.CAMPOS_PRIVADOS).
    - Si un dato no está disponible se muestra "No informado", para que
      quien lee sepa que el dato falta y no que se olvidó.
    - Todos los textos pasan por html.escape(), para que un dato con
      símbolos como < o & no rompa la página.
    - La página lleva <meta name="robots" content="noindex">, para que
      Google no la muestre en búsquedas.
    - La ficha guarda su UUID en una etiqueta <meta>. verificar_ficha()
      lo usa para comprobar que cada archivo es de la persona correcta.
    - La ficha pública se llama <uuid>.html: el nombre no aparece en la URL.

Funciones:
    valor_o_no_informado(valor)  -> str
    nombre_publico(registro)     -> str
    formatear_telefono(telefono) -> str
    generar_html(registro)       -> str
    guardar_ficha(registro, carpeta) -> estado
    retirar_ficha_publica(uuid)  -> bool
    verificar_ficha(registro)    -> list[str]
    generar_indice()
"""

import html
import os

from src import config


def valor_o_no_informado(valor):
    """Devuelve el valor (escapado) o 'No informado' si está vacío."""
    valor = (valor or "").strip()
    return html.escape(valor) if valor else f'<span class="vacio">{config.TEXTO_NO_INFORMADO}</span>'


def nombre_publico(registro):
    """Solo el primer nombre: 'Maria Pia' -> 'Maria'."""
    partes = registro["nombres"].split()
    return partes[0] if partes else ""


def formatear_telefono(telefono):
    """'+56932434609' -> '+56 9 3243 4609' (más fácil de leer)."""
    if len(telefono) == 12 and telefono.startswith("+56"):
        return f"{telefono[:3]} {telefono[3]} {telefono[4:8]} {telefono[8:]}"
    return telefono


def _tarjeta_contacto(numero, nombre, relacion, telefono):
    """HTML de un contacto de emergencia."""
    if not nombre:
        return f"""
      <div class="contacto">
        <p class="etiqueta">Contacto {numero}</p>
        <p>{valor_o_no_informado("")}</p>
      </div>"""
    relacion_html = f" <span class=\"relacion\">({html.escape(relacion)})</span>" if relacion else ""
    boton = (
        f'<a class="llamar" href="tel:{html.escape(telefono)}">Llamar {html.escape(formatear_telefono(telefono))}</a>'
        if telefono else f"<p>{valor_o_no_informado('')}</p>"
    )
    return f"""
      <div class="contacto">
        <p class="etiqueta">Contacto {numero}</p>
        <p class="nombre-contacto">{html.escape(nombre)}{relacion_html}</p>
        {boton}
      </div>"""


def generar_html(registro):
    """Devuelve el texto HTML completo de la ficha."""
    nombre = html.escape(nombre_publico(registro))
    contacto1 = _tarjeta_contacto(1, registro["contacto1_nombre"], registro["contacto1_relacion"],
                                  registro["contacto1_telefono"])
    contacto2 = _tarjeta_contacto(2, registro["contacto2_nombre"], registro["contacto2_relacion"],
                                  registro["contacto2_telefono"])

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="ficha-uuid" content="{html.escape(registro['uuid'])}">
  <title>Ficha de emergencia - {nombre}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f2f4f7;
           color: #1a1a1a; font-size: 18px; line-height: 1.45; }}
    main {{ max-width: 560px; margin: 0 auto; padding: 16px; }}
    header {{ background: #0b5cad; color: #fff; padding: 20px 16px; border-radius: 14px; }}
    header .aviso {{ margin: 0; font-size: 14px; letter-spacing: .08em; text-transform: uppercase; }}
    header h1 {{ margin: 6px 0 4px; font-size: 30px; line-height: 1.15; }}
    header p {{ margin: 0; }}
    section {{ background: #fff; border-radius: 14px; padding: 16px; margin-top: 14px;
              box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    h2 {{ margin: 0 0 10px; font-size: 20px; color: #0b5cad; }}
    .contacto + .contacto {{ border-top: 1px solid #e3e6ea; margin-top: 12px; padding-top: 12px; }}
    .etiqueta {{ margin: 0; font-size: 14px; color: #5a6270; text-transform: uppercase; }}
    .nombre-contacto {{ margin: 2px 0 8px; font-weight: bold; font-size: 20px; }}
    .relacion {{ font-weight: normal; color: #5a6270; }}
    .llamar {{ display: block; text-align: center; background: #12823b; color: #fff;
              text-decoration: none; font-weight: bold; font-size: 20px; padding: 14px;
              border-radius: 10px; }}
    dl {{ margin: 0; }}
    dt {{ font-size: 14px; color: #5a6270; text-transform: uppercase; margin-top: 10px; }}
    dt:first-child {{ margin-top: 0; }}
    dd {{ margin: 2px 0 0; }}
    .vacio {{ color: #8a8f98; font-style: italic; }}
    footer {{ font-size: 14px; color: #5a6270; padding: 16px 4px 32px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <p class="aviso">Ficha de emergencia</p>
      <h1>Hola, me llamo {nombre}</h1>
      <p>Si me encontraste, por favor llama a mi contacto de emergencia.</p>
    </header>

    <section>
      <h2>A quién llamar</h2>{contacto1}{contacto2}
    </section>

    <section>
      <h2>Cómo ayudarme</h2>
      <dl>
        <dt>Condición</dt><dd>{valor_o_no_informado(registro['condicion'])}</dd>
        <dt>Cómo me comunico</dt><dd>{valor_o_no_informado(registro['como_me_comunico'])}</dd>
        <dt>Qué me ayuda a calmarme</dt><dd>{valor_o_no_informado(registro['que_me_ayuda'])}</dd>
        <dt>Qué evitar</dt><dd>{valor_o_no_informado(registro['que_evitar'])}</dd>
      </dl>
    </section>

    <section>
      <h2>Referencia de ubicación</h2>
      <p>Vivo en: <strong>{valor_o_no_informado(registro['referencia_publica'])}</strong></p>
    </section>

    <footer>
      <p>Actualizada el {html.escape(registro['fecha_actualizacion'] or config.TEXTO_NO_INFORMADO)}</p>
      <p>Fundación Sin Barreras · Prototipo con datos ficticios.<br>
         Para corregir o retirar esta ficha: {html.escape(config.CORREO_FUNDACION)}</p>
    </footer>
  </main>
</body>
</html>
"""


def _escribir_si_cambia(ruta, contenido):
    """Escribe el archivo solo si el contenido cambió. Devuelve el estado."""
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as archivo:
            if archivo.read() == contenido:
                return "sin cambios"
        estado = "actualizada"
    else:
        estado = "nueva"
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    return estado


def guardar_ficha(registro, carpeta):
    """Guarda la ficha en la carpeta privada y en docs/p/<uuid>.html.

    Devuelve "nueva", "actualizada" o "sin cambios" (según la ficha pública).
    """
    contenido = generar_html(registro)
    os.makedirs(config.CARPETA_PUBLICA, exist_ok=True)
    _escribir_si_cambia(carpeta / "ficha.html", contenido)
    return _escribir_si_cambia(config.CARPETA_PUBLICA / f"{registro['uuid']}.html", contenido)


def retirar_ficha_publica(uuid):
    """Borra la ficha pública de un participante retirado.

    La carpeta privada se conserva. Devuelve True si había algo que retirar.
    """
    ruta = config.CARPETA_PUBLICA / f"{uuid}.html"
    if os.path.exists(ruta):
        os.remove(ruta)
        return True
    return False


def verificar_ficha(registro):
    """Comprueba que la ficha pública corresponde a la persona correcta.

    Devuelve la lista de problemas encontrados (vacía si todo está bien).
    """
    ruta = config.CARPETA_PUBLICA / f"{registro['uuid']}.html"
    if not os.path.exists(ruta):
        return ["la ficha pública no existe"]
    with open(ruta, encoding="utf-8") as archivo:
        contenido = archivo.read()

    problemas = []
    if f'<meta name="ficha-uuid" content="{registro["uuid"]}">' not in contenido:
        problemas.append("el UUID de la ficha no coincide")
    if html.escape(nombre_publico(registro)) not in contenido:
        problemas.append("el nombre no aparece en la ficha")
    if registro["contacto1_telefono"] and registro["contacto1_telefono"] not in contenido:
        problemas.append("el teléfono del contacto 1 no aparece en la ficha")
    for campo in ("rut", "email", "direccion", "apellidos"):
        if registro[campo] and html.escape(registro[campo]) in contenido:
            problemas.append(f"la ficha muestra un dato privado ({campo})")
    return problemas


def generar_indice():
    """Crea docs/index.html: una portada SIN lista de participantes."""
    os.makedirs(config.CARPETA_DOCS, exist_ok=True)
    contenido = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>Fichas de emergencia - Fundación Sin Barreras</title>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; background: #f2f4f7; color: #1a1a1a;
           margin: 0; padding: 24px 16px; line-height: 1.5; }
    main { max-width: 560px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 14px; }
    h1 { color: #0b5cad; font-size: 24px; margin-top: 0; }
  </style>
</head>
<body>
  <main>
    <h1>Fichas de emergencia</h1>
    <p>Este sitio publica fichas de emergencia de participantes de la Fundación Sin Barreras.
       Cada ficha se abre solo escaneando el código QR de la persona.</p>
    <p>Prototipo académico con datos ficticios.</p>
  </main>
</body>
</html>
"""
    _escribir_si_cambia(config.CARPETA_DOCS / "index.html", contenido)
