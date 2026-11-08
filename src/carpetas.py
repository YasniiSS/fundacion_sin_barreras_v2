"""
carpetas.py
Gestión de carpetas por participante.

Responsabilidad:
    Crear una carpeta por cada participante dentro de participantes/,
    con un nombre seguro para cualquier sistema operativo.

Decisiones:
    - El nombre de la carpeta combina nombres, apellidos y UUID:
      jose_tomas_arriagada_penaloza_3f9c2e1a
      Así dos personas con el mismo nombre nunca comparten carpeta.
    - Se quitan tildes, ñ, espacios y símbolos con unicodedata.
    - El registro se relaciona con su carpeta por el UUID (final del nombre).
      Si la persona corrige su nombre, la carpeta se renombra: no se crea
      una segunda carpeta ni se pierden los archivos.
    - Si la carpeta ya existe, se reutiliza. Nunca se borra nada.

Funciones:
    limpiar_nombre(texto)        -> str
    nombre_carpeta(registro)     -> str
    buscar_carpeta_por_uuid(uuid) -> Path | None
    crear_carpeta(registro)      -> (Path, estado)
"""

import os
import re
import unicodedata

from src import config


def limpiar_nombre(texto):
    """'José Peña Muñoz' -> 'jose_pena_munoz'."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    solo_letras = re.sub(r"[^a-zA-Z0-9]+", "_", sin_tildes.lower())
    return solo_letras.strip("_") or "sin_nombre"


def nombre_carpeta(registro):
    """Nombre de la carpeta del participante: nombres_apellidos_uuid."""
    nombre = limpiar_nombre(f"{registro['nombres']} {registro['apellidos']}")
    return f"{nombre}_{registro['uuid']}"


def buscar_carpeta_por_uuid(uuid, base=config.CARPETA_PARTICIPANTES):
    """Busca la carpeta que termina en _<uuid>. Devuelve None si no existe."""
    if not os.path.isdir(base):
        return None
    for nombre in os.listdir(base):
        ruta = base / nombre
        if ruta.is_dir() and nombre.endswith(f"_{uuid}"):
            return ruta
    return None


def crear_carpeta(registro, base=config.CARPETA_PARTICIPANTES):
    """Crea (o reutiliza) la carpeta del participante.

    Devuelve (ruta, estado), donde estado es:
        "creada"     -> no existía
        "existente"  -> ya existía con el mismo nombre
        "renombrada" -> existía con otro nombre (se corrigió el nombre)
    """
    os.makedirs(base, exist_ok=True)
    destino = base / nombre_carpeta(registro)
    anterior = buscar_carpeta_por_uuid(registro["uuid"], base)

    if anterior is None:
        os.makedirs(destino)
        return destino, "creada"
    if anterior == destino:
        return destino, "existente"
    os.rename(anterior, destino)
    return destino, "renombrada"
