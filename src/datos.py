"""
datos.py
Lectura, escritura y validación del CSV de participantes.

Responsabilidad:
    Ser el único módulo que lee y escribe datos/participantes.csv.
    También decide qué registros están listos para publicarse.

Decisiones:
    - El RUT es la clave interna: sirve para saber si una persona ya existe.
      Se normaliza (sin puntos, con guion, K mayúscula) antes de comparar.
      No se valida el dígito verificador porque los datos son ficticios.
    - El UUID es la clave pública: se usa en la URL y en la carpeta.
      Una vez asignado, nunca cambia (así el QR impreso sigue sirviendo).
    - El CSV se escribe primero en un archivo temporal y luego se reemplaza,
      para no dejarlo a medias si el programa se interrumpe.
    - Un registro se clasifica como:
        válido    -> se publica
        retirado  -> sin consentimiento o marcado inactivo: se quita su ficha
        omitido   -> incompleto o repetido: no se publica y se informa el motivo

Funciones:
    normalizar_rut(rut)                  -> str
    rut_tiene_formato(rut)               -> bool
    normalizar_telefono(telefono)        -> str
    telefono_es_valido(telefono)         -> bool
    generar_uuid(existentes)             -> str
    fecha_hoy()                          -> str
    leer_participantes(ruta)             -> list[dict]
    escribir_participantes(participantes, ruta)
    buscar_por_rut(participantes, rut)   -> dict | None
    guardar_participante(registro, ruta) -> str ("creado" / "actualizado")
    asignar_uuid_faltantes(participantes) -> int
    validar_registro(registro)           -> list[str]
    clasificar_participantes(participantes) -> (validos, retirados, omitidos)
"""

import csv
import os
import re
import uuid
from datetime import date

from src import config


# --- Normalización y validación de campos ------------------------------

def normalizar_rut(rut):
    """Deja el RUT en un formato único: 12345678-9 (K en mayúscula).

    Devuelve "" si el texto está vacío.
    """
    limpio = rut.replace(".", "").replace("-", "").replace(" ", "").strip().upper()
    if len(limpio) < 2:
        return limpio
    return f"{limpio[:-1]}-{limpio[-1]}"


def rut_tiene_formato(rut):
    """Revisa solo el formato (números, guion, dígito o K). No calcula el DV."""
    return re.fullmatch(r"\d{7,8}-[\dK]", normalizar_rut(rut)) is not None


def normalizar_telefono(telefono):
    """Deja el teléfono como +56XXXXXXXXX (sin espacios).

    Acepta "+569 1234 5678", "56912345678" o "912345678".
    Si no se puede normalizar, devuelve el texto sin espacios.
    """
    digitos = re.sub(r"\D", "", telefono)
    if len(digitos) == 9:            # 912345678 -> falta el código de país
        digitos = "56" + digitos
    if len(digitos) == 11 and digitos.startswith("56"):
        return "+" + digitos
    return telefono.replace(" ", "").strip()


def telefono_es_valido(telefono):
    """Un teléfono chileno válido tiene +56 y 9 dígitos más."""
    return re.fullmatch(r"\+56\d{9}", normalizar_telefono(telefono)) is not None


def generar_uuid(existentes):
    """Genera un identificador corto (8 caracteres) que no esté en 'existentes'."""
    while True:
        nuevo = uuid.uuid4().hex[: config.LARGO_UUID]
        if nuevo not in existentes:
            return nuevo


def fecha_hoy():
    """Fecha actual en formato AAAA-MM-DD."""
    return date.today().isoformat()


# --- Lectura y escritura del CSV ---------------------------------------

def leer_participantes(ruta=config.RUTA_CSV):
    """Lee el CSV y devuelve una lista de diccionarios.

    Si el archivo no existe, devuelve una lista vacía (primera ejecución).
    Los campos que falten en el archivo se agregan vacíos.
    """
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding=config.CODIFICACION) as archivo:
        lector = csv.DictReader(archivo, delimiter=config.SEPARADOR)
        participantes = []
        for fila in lector:
            registro = {campo: (fila.get(campo) or "").strip() for campo in config.CAMPOS}
            participantes.append(registro)
    return participantes


def escribir_participantes(participantes, ruta=config.RUTA_CSV):
    """Escribe la lista completa en el CSV, de forma segura."""
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    temporal = str(ruta) + ".tmp"
    with open(temporal, "w", newline="", encoding=config.CODIFICACION) as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=config.CAMPOS, delimiter=config.SEPARADOR)
        escritor.writeheader()
        for registro in participantes:
            escritor.writerow({campo: registro.get(campo, "") for campo in config.CAMPOS})
    os.replace(temporal, ruta)


def buscar_por_rut(participantes, rut):
    """Devuelve el registro con ese RUT, o None si no existe."""
    rut = normalizar_rut(rut)
    for registro in participantes:
        if normalizar_rut(registro["rut"]) == rut:
            return registro
    return None


def guardar_participante(registro, ruta=config.RUTA_CSV):
    """Agrega un participante nuevo o actualiza uno existente (según su RUT).

    Al actualizar se conservan el UUID y la fecha de registro originales.
    Devuelve "creado" o "actualizado".
    """
    participantes = leer_participantes(ruta)
    registro = dict(registro)
    registro["rut"] = normalizar_rut(registro["rut"])
    registro["fecha_actualizacion"] = fecha_hoy()

    existente = buscar_por_rut(participantes, registro["rut"])
    if existente is not None:
        registro["uuid"] = existente["uuid"]
        registro["fecha_registro"] = existente["fecha_registro"]
        existente.update(registro)
        resultado = "actualizado"
    else:
        if not registro.get("uuid"):
            registro["uuid"] = generar_uuid({p["uuid"] for p in participantes})
        registro.setdefault("fecha_registro", fecha_hoy())
        if not registro["fecha_registro"]:
            registro["fecha_registro"] = fecha_hoy()
        participantes.append(registro)
        resultado = "creado"

    escribir_participantes(participantes, ruta)
    return resultado


def asignar_uuid_faltantes(participantes):
    """Asigna UUID a los registros agregados a mano en el CSV sin UUID.

    Devuelve cuántos UUID se asignaron.
    """
    existentes = {p["uuid"] for p in participantes if p["uuid"]}
    asignados = 0
    for registro in participantes:
        if not registro["uuid"]:
            registro["uuid"] = generar_uuid(existentes)
            existentes.add(registro["uuid"])
            asignados += 1
    return asignados


# --- Validación y clasificación ----------------------------------------

def validar_registro(registro):
    """Devuelve la lista de problemas del registro (vacía si está correcto)."""
    problemas = []
    for campo in config.CAMPOS_OBLIGATORIOS:
        if not registro.get(campo, "").strip():
            problemas.append(f"falta '{campo}'")

    if registro.get("rut") and not rut_tiene_formato(registro["rut"]):
        problemas.append("RUT con formato inválido")

    for numero in ("contacto1_telefono", "contacto2_telefono"):
        valor = registro.get(numero, "")
        if valor and not telefono_es_valido(valor):
            problemas.append(f"'{numero}' inválido ({valor})")
    return problemas


def clasificar_participantes(participantes):
    """Separa los registros en válidos, retirados y omitidos.

    Devuelve tres listas:
        validos   -> registros listos para publicar
        retirados -> registros cuya ficha pública debe quitarse
        omitidos  -> tuplas (registro, motivo) que no se procesan
    """
    validos, retirados, omitidos = [], [], []
    ruts_vistos, uuids_vistos = set(), set()

    for registro in participantes:
        rut = normalizar_rut(registro["rut"])

        if rut and rut in ruts_vistos:
            omitidos.append((registro, f"RUT repetido ({rut}): se usa el primer registro"))
            continue
        if registro["uuid"] and registro["uuid"] in uuids_vistos:
            omitidos.append((registro, f"UUID repetido ({registro['uuid']})"))
            continue
        ruts_vistos.add(rut)
        uuids_vistos.add(registro["uuid"])

        if registro["autoriza_publicacion"].lower() != "si" or registro["activo"].lower() == "no":
            retirados.append(registro)
            continue

        problemas = validar_registro(registro)
        if problemas:
            omitidos.append((registro, "; ".join(problemas)))
        else:
            validos.append(registro)

    return validos, retirados, omitidos
