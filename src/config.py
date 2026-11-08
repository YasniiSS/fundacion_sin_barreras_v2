"""
config.py
Configuración central del proyecto.

Responsabilidad:
    Guardar en un solo lugar las rutas, la URL de publicación y la lista
    de campos del CSV. Ningún otro módulo escribe rutas "a mano".

Decisiones:
    - Las rutas se calculan desde la ubicación de este archivo, así el
      proyecto funciona en cualquier computador sin editar nada.
    - Si cambia el lugar de publicación, solo se cambia URL_BASE.
    - El CSV usa ";" como separador, igual que Excel en español.

Funciones:
    (no tiene funciones, solo constantes)
"""

from pathlib import Path

# --- Rutas -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

CARPETA_DATOS = BASE_DIR / "datos"                 # PRIVADO
RUTA_BBDD = CARPETA_DATOS / "bbdd.csv"             # carga inicial (datos originales)
RUTA_CSV = CARPETA_DATOS / "participantes.csv"     # fuente oficial del proceso
RUTA_LOG = CARPETA_DATOS / "log_proceso.txt"

CARPETA_PARTICIPANTES = BASE_DIR / "participantes"  # PRIVADO: una carpeta por persona
RUTA_HOJA_QR = CARPETA_PARTICIPANTES / "qr_imprimir.html"  # PRIVADO: todos los QR para imprimir
CARPETA_DOCS = BASE_DIR / "docs"                    # PÚBLICO: lo único que publica GitHub Pages
CARPETA_PUBLICA = CARPETA_DOCS / "p"                # fichas públicas, una por UUID

# --- Publicación -------------------------------------------------------
# GitHub Pages publica la carpeta docs/ en esta dirección.
URL_BASE = "https://yasniiss.github.io/fundacion_sin_barreras_v2/p/"

# --- Formato del CSV ---------------------------------------------------
SEPARADOR = ";"
CODIFICACION = "utf-8-sig"   # utf-8 con BOM: Excel muestra bien las tildes

LARGO_UUID = 8               # ej: a3f9c2e1

CAMPOS = [
    "uuid",
    "rut",
    "nombres",
    "apellidos",
    "edad",
    "email",
    "direccion",             # PRIVADO: dirección exacta
    "referencia_publica",    # PÚBLICO: comuna o punto de referencia
    "condicion",
    "como_me_comunico",
    "que_me_ayuda",
    "que_evitar",
    "contacto1_nombre",
    "contacto1_relacion",
    "contacto1_telefono",
    "contacto2_nombre",
    "contacto2_relacion",
    "contacto2_telefono",
    "autoriza_publicacion",  # si / no
    "nombre_quien_autoriza",
    "fecha_registro",
    "fecha_actualizacion",
    "activo",                # si / no  (no = ficha retirada)
]

# Sin estos campos no se puede generar una ficha útil.
CAMPOS_OBLIGATORIOS = [
    "uuid",
    "rut",
    "nombres",
    "apellidos",
    "referencia_publica",
    "contacto1_nombre",
    "contacto1_telefono",
]

# Campos que NUNCA aparecen en la ficha pública.
CAMPOS_PRIVADOS = ["rut", "edad", "email", "direccion", "nombre_quien_autoriza"]

TEXTO_NO_INFORMADO = "No informado"

# Correo ficticio para pedir corrección o retiro de una ficha.
CORREO_FUNDACION = "contacto@fundacion-ficticia.cl"
