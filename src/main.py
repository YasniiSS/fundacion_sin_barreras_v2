"""
main.py
Ejecuta el proceso completo, en orden.

Responsabilidad:
    Coordinar los demás módulos. No tiene lógica propia: solo llama a
    las funciones en el orden correcto e informa el resultado.

Orden del proceso:
    1. Carga inicial: si no existe participantes.csv, se importa bbdd.csv.
    2. Se lee el CSV y se asigna UUID a los registros que no lo tienen.
    3. Se clasifican los registros: válidos, retirados y omitidos.
    4. Por cada válido: carpeta, ficha HTML y QR. Además se crea
       participantes/qr_imprimir.html con todos los QR para imprimir.
    5. Se quitan las fichas públicas de los retirados y las que ya no
       corresponden a nadie (por ejemplo, una fila borrada del CSV).
    6. Se verifica que cada ficha pública es de la persona correcta y que
       cada QR, al leerlo, contiene la URL de esa misma persona.
    7. Se escribe el log en datos/log_proceso.txt.

Decisiones:
    - Ejecutarlo varias veces da el mismo resultado: no duplica carpetas,
      no borra archivos privados y solo reescribe lo que cambió.

Uso:
    python -m src.main

Funciones:
    procesar(mostrar=True) -> dict (resumen)
    escribir_log(resumen)
    imprimir_resumen(resumen)
    ruta_relativa(ruta)      -> str
"""

import os
from datetime import datetime

from src import config
from src import datos
from src.carga import importar_bbdd
from src.carpetas import crear_carpeta
from src.fichas import generar_indice, guardar_ficha, retirar_ficha_publica, verificar_ficha
from src.qr import generar_hoja_impresion, generar_qr_lote, url_participante, verificar_qr


def procesar(mostrar=True):
    """Ejecuta todo el proceso y devuelve un resumen con lo ocurrido."""
    resumen = {"carga_inicial": None, "uuid_asignados": 0, "procesados": [], "hoja_qr": None,
               "retirados": [], "omitidos": [], "huerfanas": [], "errores_verificacion": []}

    # 1. Carga inicial
    if not os.path.exists(config.RUTA_CSV) and os.path.exists(config.RUTA_BBDD):
        resumen["carga_inicial"] = importar_bbdd()

    # 2. Lectura y UUID faltantes
    participantes = datos.leer_participantes()
    resumen["uuid_asignados"] = datos.asignar_uuid_faltantes(participantes)
    if resumen["uuid_asignados"]:
        datos.escribir_participantes(participantes)

    # 3. Clasificación
    validos, retirados, omitidos = datos.clasificar_participantes(participantes)
    resumen["omitidos"] = omitidos

    # 4. Carpetas, fichas y QR
    lista_qr = []
    estados = {}
    for registro in validos:
        carpeta, estado_carpeta = crear_carpeta(registro)
        estado_ficha = guardar_ficha(registro, carpeta)
        estados[registro["uuid"]] = (carpeta, estado_carpeta, estado_ficha)
        lista_qr.append((registro, carpeta))

    resultados_qr = generar_qr_lote(lista_qr)
    resumen["hoja_qr"] = generar_hoja_impresion(resultados_qr)
    for registro, ruta_qr, estado_qr in resultados_qr:
        carpeta, estado_carpeta, estado_ficha = estados[registro["uuid"]]
        if not verificar_qr(registro, ruta_qr):
            resumen["errores_verificacion"].append((registro["uuid"], ["el QR no contiene su URL"]))
        resumen["procesados"].append({
            "uuid": registro["uuid"],
            "nombre": f"{registro['nombres']} {registro['apellidos']}",
            "carpeta": carpeta.name,
            "carpeta_estado": estado_carpeta,
            "ficha_estado": estado_ficha,
            "qr_estado": estado_qr,
            "qr": ruta_qr.name,
            "url": url_participante(registro),
        })

    # 5. Retiros y fichas huérfanas
    for registro in retirados:
        if retirar_ficha_publica(registro["uuid"]):
            resumen["retirados"].append(f"{registro['nombres']} {registro['apellidos']} ({registro['uuid']})")

    uuids_validos = {r["uuid"] for r in validos}
    uuids_omitidos = {r["uuid"] for r, _ in omitidos}
    if os.path.isdir(config.CARPETA_PUBLICA):
        for archivo in os.listdir(config.CARPETA_PUBLICA):
            uuid = archivo.removesuffix(".html")
            # Las fichas de registros omitidos se conservan (último dato válido).
            if archivo.endswith(".html") and uuid not in uuids_validos and uuid not in uuids_omitidos:
                os.remove(config.CARPETA_PUBLICA / archivo)
                resumen["huerfanas"].append(uuid)

    # 6. Verificación
    for registro in validos:
        problemas = verificar_ficha(registro)
        if problemas:
            resumen["errores_verificacion"].append((registro["uuid"], problemas))

    generar_indice()

    # 7. Log
    escribir_log(resumen)
    if mostrar:
        imprimir_resumen(resumen)
    return resumen


def escribir_log(resumen):
    """Agrega el resultado de esta ejecución a datos/log_proceso.txt."""
    os.makedirs(config.CARPETA_DATOS, exist_ok=True)
    with open(config.RUTA_LOG, "a", encoding="utf-8") as log:
        log.write(f"\n=== Ejecución {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")
        if resumen["carga_inicial"]:
            log.write(f"Carga inicial desde bbdd.csv: {resumen['carga_inicial']}\n")
        if resumen["uuid_asignados"]:
            log.write(f"UUID asignados a registros nuevos: {resumen['uuid_asignados']}\n")
        for p in resumen["procesados"]:
            log.write(f"OK       {p['uuid']}  {p['nombre']}  carpeta={p['carpeta_estado']}  "
                      f"ficha={p['ficha_estado']}  qr={p['qr_estado']}\n")
        for registro, motivo in resumen["omitidos"]:
            log.write(f"OMITIDO  {registro['uuid'] or '-'}  {registro['nombres']} "
                      f"{registro['apellidos']}  motivo: {motivo}\n")
        for texto in resumen["retirados"]:
            log.write(f"RETIRADO {texto}\n")
        for uuid in resumen["huerfanas"]:
            log.write(f"BORRADA  ficha pública sin registro: {uuid}\n")
        for uuid, problemas in resumen["errores_verificacion"]:
            log.write(f"ERROR    {uuid}: {'; '.join(problemas)}\n")


def imprimir_resumen(resumen):
    """Muestra el resultado en pantalla."""
    if resumen["carga_inicial"]:
        print(f"Carga inicial desde bbdd.csv: {resumen['carga_inicial']}")
    if resumen["uuid_asignados"]:
        print(f"UUID asignados: {resumen['uuid_asignados']}")

    print(f"\nProcesados: {len(resumen['procesados'])}")
    for p in resumen["procesados"]:
        print(f"  {p['uuid']}  {p['nombre']:<38} carpeta={p['carpeta_estado']:<10} "
              f"ficha={p['ficha_estado']:<11} qr={p['qr_estado']}")

    if resumen["omitidos"]:
        print(f"\nOmitidos (no se publican): {len(resumen['omitidos'])}")
        for registro, motivo in resumen["omitidos"]:
            print(f"  {registro['nombres']} {registro['apellidos']}: {motivo}")
    if resumen["retirados"]:
        print("\nFichas retiradas:", ", ".join(resumen["retirados"]))
    if resumen["huerfanas"]:
        print("\nFichas públicas borradas (sin registro):", ", ".join(resumen["huerfanas"]))

    if resumen["errores_verificacion"]:
        print("\nERRORES de verificación:")
        for uuid, problemas in resumen["errores_verificacion"]:
            print(f"  {uuid}: {'; '.join(problemas)}")
    else:
        print("\nVerificación: cada ficha y cada QR corresponden a su participante.")
    # Rutas relativas al proyecto: no se muestran carpetas del computador.
    if resumen["hoja_qr"]:
        print(f"\nQR para imprimir: {ruta_relativa(resumen['hoja_qr'])}")
    print(f"Log: {ruta_relativa(config.RUTA_LOG)}")


def ruta_relativa(ruta):
    """'<carpeta del proyecto>/datos/log.txt' -> 'datos/log.txt'."""
    return ruta.relative_to(config.BASE_DIR).as_posix()


if __name__ == "__main__":
    procesar()
