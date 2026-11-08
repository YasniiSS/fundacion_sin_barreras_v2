"""
carga.py
Carga inicial: importa datos/bbdd.csv al CSV del proyecto.

Responsabilidad:
    Convertir la planilla original (bbdd.csv) al formato de
    datos/participantes.csv, que es la fuente oficial del proceso.

Decisiones:
    - bbdd.csv no se modifica: queda como respaldo de los datos originales.
    - Se reconoce cada columna aunque tenga tildes, mayúsculas o errores
      de tipeo (ej: "Conteción" se reconoce como "contención").
    - "Nombre completo" se separa así: los dos últimos términos son los
      apellidos y el resto son los nombres.
    - La dirección exacta se guarda en privado. Solo la comuna (el texto
      después de la última coma) pasa a "referencia_publica".
    - bbdd.csv no tiene columna de consentimiento. Como el prototipo usa
      datos ficticios, se simula que el contacto de emergencia autorizó.
      En una implementación real, este paso debe ser una autorización firmada.
    - Si un RUT ya está en participantes.csv, no se vuelve a importar.
      Así la carga puede ejecutarse varias veces sin duplicar.

Funciones:
    clave_columna(texto)           -> str
    separar_nombre(nombre_completo) -> (nombres, apellidos)
    extraer_comuna(direccion)      -> str
    convertir_fila(fila)           -> dict
    importar_bbdd(ruta_bbdd, ruta_csv) -> dict (resumen)
"""

import csv
import os
import unicodedata

from src import config
from src import datos

# Nombre de columna en bbdd.csv (ya limpio) -> campo del proyecto
COLUMNAS = {
    "nombre_completo": "nombre_completo",
    "rut": "rut",
    "edad": "edad",
    "condicion": "condicion",
    "contencion": "que_me_ayuda",
    "contecion": "que_me_ayuda",        # así viene escrito en bbdd.csv
    "direccion": "direccion",
    "nombre_contacto": "contacto1_nombre",
    "telefono_de_contacto": "contacto1_telefono",
    "telefono_contacto": "contacto1_telefono",
}


def clave_columna(texto):
    """'Teléfono de contacto' -> 'telefono_de_contacto'."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "_".join(sin_tildes.lower().split())


def separar_nombre(nombre_completo):
    """Separa 'Maria Pia Alvarez Muños' en ('Maria Pia', 'Alvarez Muños')."""
    partes = nombre_completo.split()
    if len(partes) >= 3:
        return " ".join(partes[:-2]), " ".join(partes[-2:])
    if len(partes) == 2:
        return partes[0], partes[1]
    return nombre_completo.strip(), ""


def extraer_comuna(direccion):
    """'El Parron #113, La Cisterna' -> 'La Cisterna'."""
    if "," not in direccion:
        return ""
    comuna = direccion.rsplit(",", 1)[1]
    comuna = comuna.replace("#", " ").strip()
    return " ".join(comuna.split()).title()


def convertir_fila(fila):
    """Convierte una fila de bbdd.csv en un registro del proyecto."""
    original = {}
    for columna, valor in fila.items():
        if columna is None:
            continue
        campo = COLUMNAS.get(clave_columna(columna))
        if campo:
            original[campo] = " ".join((valor or "").split())   # quita espacios dobles

    nombres, apellidos = separar_nombre(original.get("nombre_completo", ""))
    registro = {campo: "" for campo in config.CAMPOS}
    registro.update({
        "rut": datos.normalizar_rut(original.get("rut", "")),
        "nombres": nombres,
        "apellidos": apellidos,
        "edad": original.get("edad", ""),
        "direccion": original.get("direccion", ""),
        "referencia_publica": extraer_comuna(original.get("direccion", "")),
        "condicion": original.get("condicion", ""),
        "que_me_ayuda": original.get("que_me_ayuda", ""),
        "contacto1_nombre": original.get("contacto1_nombre", ""),
        "contacto1_telefono": datos.normalizar_telefono(original.get("contacto1_telefono", "")),
        # Consentimiento simulado (ver "Decisiones" arriba).
        "autoriza_publicacion": "si",
        "nombre_quien_autoriza": original.get("contacto1_nombre", ""),
        "fecha_registro": datos.fecha_hoy(),
        "fecha_actualizacion": datos.fecha_hoy(),
        "activo": "si",
    })
    return registro


def importar_bbdd(ruta_bbdd=config.RUTA_BBDD, ruta_csv=config.RUTA_CSV):
    """Importa bbdd.csv a participantes.csv sin duplicar RUT.

    Devuelve un resumen: {"importados": n, "ya_existian": n, "sin_rut": n}.
    """
    if not os.path.exists(ruta_bbdd):
        raise FileNotFoundError(f"No se encontró {ruta_bbdd}")

    participantes = datos.leer_participantes(ruta_csv)
    existentes = {datos.normalizar_rut(p["rut"]) for p in participantes}
    uuids = {p["uuid"] for p in participantes}
    resumen = {"importados": 0, "ya_existian": 0, "sin_rut": 0}

    with open(ruta_bbdd, newline="", encoding=config.CODIFICACION) as archivo:
        for fila in csv.DictReader(archivo, delimiter=config.SEPARADOR):
            registro = convertir_fila(fila)
            if not registro["rut"]:
                resumen["sin_rut"] += 1
                continue
            if registro["rut"] in existentes:
                resumen["ya_existian"] += 1
                continue
            registro["uuid"] = datos.generar_uuid(uuids)
            uuids.add(registro["uuid"])
            existentes.add(registro["rut"])
            participantes.append(registro)
            resumen["importados"] += 1

    datos.escribir_participantes(participantes, ruta_csv)
    return resumen


if __name__ == "__main__":
    print(importar_bbdd())
