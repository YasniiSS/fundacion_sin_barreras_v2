"""
formulario.py
Formulario de registro de participantes con input().

Responsabilidad:
    Pedir los datos de un participante, validarlos mientras se escriben
    y guardarlos en datos/participantes.csv (a través de datos.py).

Decisiones:
    - Lo primero es el consentimiento: se explica qué se publicará y quién
      podrá verlo. Si no se autoriza, no se guarda nada.
    - El RUT se busca en el CSV. Si ya existe, se muestran los datos y se
      ofrece actualizarlos: al presionar Enter se mantiene el valor actual,
      y el UUID no cambia (el QR impreso sigue sirviendo).
    - Cada pregunta se repite hasta recibir un dato válido.
    - Se puede retirar una ficha (opción 2 del menú): el registro no se
      borra, se marca como inactivo y main.py quita su ficha pública.
    - Todas las funciones reciben 'leer' (por defecto input). En el notebook
      se reemplaza por respuestas_simuladas() para que la demostración se
      pueda repetir sin escribir a mano.

Funciones:
    respuestas_simuladas(lista)          -> función que reemplaza a input
    pedir_texto(pregunta, obligatorio, actual, leer) -> str
    pedir_si_no(pregunta, leer)          -> bool
    pedir_edad(actual, leer)             -> str
    pedir_email(actual, leer)            -> str
    pedir_telefono(pregunta, obligatorio, actual, leer) -> str
    pedir_rut(leer)                      -> str
    pedir_consentimiento(leer)           -> str (nombre de quien autoriza) | None
    mostrar_resumen(registro)
    registrar_participante(leer)         -> str | None
    retirar_participante(leer)           -> bool
    ejecutar_formulario(leer)
"""

from src import config
from src import datos
from src.carga import extraer_comuna


def respuestas_simuladas(lista):
    """Devuelve una función que responde las preguntas con los valores de 'lista'.

    Sirve para probar el formulario en el notebook sin escribir a mano.
    """
    pendientes = list(lista)

    def leer(pregunta=""):
        respuesta = pendientes.pop(0)
        print(f"{pregunta}{respuesta}")
        return respuesta

    return leer


def pedir_texto(pregunta, obligatorio=True, actual="", leer=input):
    """Pide un texto. Si hay valor actual, Enter lo mantiene."""
    sufijo = f" [{actual}]" if actual else ""
    while True:
        valor = " ".join(leer(f"{pregunta}{sufijo}: ").split())
        if not valor:
            valor = actual
        if valor or not obligatorio:
            return valor
        print("  -> Este dato es obligatorio.")


def pedir_si_no(pregunta, leer=input):
    """Acepta solo s/n. Devuelve True para sí."""
    while True:
        valor = leer(f"{pregunta} (s/n): ").strip().lower()
        if valor in ("s", "si", "sí"):
            return True
        if valor in ("n", "no"):
            return False
        print("  -> Responde s o n.")


def pedir_edad(actual="", leer=input):
    """Edad opcional, pero si se escribe debe ser un número entre 0 y 120."""
    while True:
        valor = pedir_texto("Edad (opcional)", obligatorio=False, actual=actual, leer=leer)
        if not valor or (valor.isdigit() and 0 <= int(valor) <= 120):
            return valor
        print("  -> Escribe un número entre 0 y 120.")


def pedir_email(actual="", leer=input):
    """Email opcional, pero si se escribe debe tener @ y un punto."""
    while True:
        valor = pedir_texto("Email de contacto (opcional)", obligatorio=False, actual=actual, leer=leer)
        if not valor or ("@" in valor and "." in valor.split("@")[-1]):
            return valor
        print("  -> Email inválido. Ejemplo: nombre@correo.cl")


def pedir_telefono(pregunta, obligatorio=True, actual="", leer=input):
    """Pide un teléfono chileno y lo devuelve normalizado (+56XXXXXXXXX)."""
    while True:
        valor = pedir_texto(pregunta, obligatorio=obligatorio, actual=actual, leer=leer)
        if not valor and not obligatorio:
            return ""
        if datos.telefono_es_valido(valor):
            return datos.normalizar_telefono(valor)
        print("  -> Teléfono inválido. Ejemplo: +56 9 1234 5678")


def pedir_rut(leer=input):
    """Pide un RUT con formato 12345678-9 (no se valida el dígito verificador)."""
    while True:
        valor = pedir_texto("RUT (ej: 12.345.678-9)", leer=leer)
        if datos.rut_tiene_formato(valor):
            return datos.normalizar_rut(valor)
        print("  -> Formato inválido. Ejemplo: 12.345.678-9")


def pedir_consentimiento(leer=input):
    """Explica qué se publicará y pide autorización.

    Devuelve el nombre de quien autoriza, o None si no autoriza.
    """
    print("\n--- Consentimiento ---")
    print("Se publicará una ficha de emergencia en internet, visible para")
    print("cualquier persona que escanee el código QR. La ficha mostrará:")
    print("  - Solo el primer nombre (sin apellidos)")
    print("  - Contactos de emergencia y sus teléfonos")
    print("  - Características: condición y cómo ayudar a la persona")
    print("  - Ubicación general: comuna o punto de referencia (NO la dirección exacta)")
    print("NO se publicarán: apellidos, RUT, edad, email ni dirección exacta.")
    print(f"Para corregir o retirar la ficha: {config.CORREO_FUNDACION}")
    print("Los contactos de emergencia deben saber que su número será visible.\n")

    if not pedir_si_no("¿La persona o su tutor legal autoriza la publicación?", leer):
        return None
    return pedir_texto("Nombre de quien autoriza (persona o tutor)", leer=leer)


def mostrar_resumen(registro):
    """Muestra los datos antes de guardar."""
    print("\n--- Resumen ---")
    for campo in config.CAMPOS:
        if registro.get(campo):
            privado = " (privado)" if campo in config.CAMPOS_PRIVADOS else ""
            print(f"  {campo}: {registro[campo]}{privado}")


def registrar_participante(leer=input):
    """Registra un participante nuevo o actualiza uno existente.

    Devuelve "creado", "actualizado" o None si se canceló.
    """
    quien_autoriza = pedir_consentimiento(leer)
    if quien_autoriza is None:
        print("Sin autorización no se guardan datos.")
        return None

    rut = pedir_rut(leer)
    participantes = datos.leer_participantes()
    actual = datos.buscar_por_rut(participantes, rut)

    if actual is not None:
        print(f"\nYa existe un registro con el RUT {rut}:")
        mostrar_resumen(actual)
        if not pedir_si_no("¿Quieres actualizarlo?", leer):
            print("No se hicieron cambios.")
            return None
        print("(Presiona Enter para mantener el valor actual)")
    else:
        actual = {campo: "" for campo in config.CAMPOS}

    registro = dict(actual)
    registro["rut"] = rut
    registro["nombres"] = pedir_texto("Nombres", actual=actual["nombres"], leer=leer)
    registro["apellidos"] = pedir_texto("Apellidos", actual=actual["apellidos"], leer=leer)

    if not actual["uuid"]:
        # Aviso si ya hay otra persona con el mismo nombre (puede ser un error de RUT)
        for p in participantes:
            if (p["nombres"].lower(), p["apellidos"].lower()) == (
                registro["nombres"].lower(), registro["apellidos"].lower()
            ):
                print(f"  Aviso: ya existe otra persona con ese nombre (RUT {p['rut']}).")
                if not pedir_si_no("¿Es una persona distinta?", leer):
                    print("Revisa el RUT e intenta de nuevo.")
                    return None
                break

    registro["edad"] = pedir_edad(actual["edad"], leer)
    registro["email"] = pedir_email(actual["email"], leer)
    registro["direccion"] = pedir_texto("Dirección (privada, no se publica)", obligatorio=False,
                                        actual=actual["direccion"], leer=leer)
    sugerida = actual["referencia_publica"] or extraer_comuna(registro["direccion"])
    registro["referencia_publica"] = pedir_texto("Comuna o referencia pública",
                                                 actual=sugerida, leer=leer)

    print("\n--- Cómo apoyar a la persona (opcional) ---")
    registro["condicion"] = pedir_texto("Condición (ej: Autismo no verbal)", obligatorio=False,
                                        actual=actual["condicion"], leer=leer)
    registro["como_me_comunico"] = pedir_texto("Cómo se comunica", obligatorio=False,
                                               actual=actual["como_me_comunico"], leer=leer)
    registro["que_me_ayuda"] = pedir_texto("Qué le ayuda a calmarse", obligatorio=False,
                                           actual=actual["que_me_ayuda"], leer=leer)
    registro["que_evitar"] = pedir_texto("Qué evitar (ej: no tocar sin avisar)", obligatorio=False,
                                         actual=actual["que_evitar"], leer=leer)

    print("\n--- Contacto de emergencia 1 (obligatorio) ---")
    registro["contacto1_nombre"] = pedir_texto("Nombre", actual=actual["contacto1_nombre"], leer=leer)
    registro["contacto1_relacion"] = pedir_texto("Relación (ej: madre)", obligatorio=False,
                                                 actual=actual["contacto1_relacion"], leer=leer)
    registro["contacto1_telefono"] = pedir_telefono("Teléfono", actual=actual["contacto1_telefono"],
                                                    leer=leer)

    print("\n--- Contacto de emergencia 2 (opcional) ---")
    registro["contacto2_nombre"] = pedir_texto("Nombre", obligatorio=False,
                                               actual=actual["contacto2_nombre"], leer=leer)
    if registro["contacto2_nombre"]:
        registro["contacto2_relacion"] = pedir_texto("Relación", obligatorio=False,
                                                     actual=actual["contacto2_relacion"], leer=leer)
        registro["contacto2_telefono"] = pedir_telefono("Teléfono",
                                                        actual=actual["contacto2_telefono"], leer=leer)

    registro["autoriza_publicacion"] = "si"
    registro["nombre_quien_autoriza"] = quien_autoriza
    registro["activo"] = "si"

    mostrar_resumen(registro)
    if not pedir_si_no("¿Guardar estos datos?", leer):
        print("No se guardó nada.")
        return None

    resultado = datos.guardar_participante(registro)
    print(f"\nParticipante {resultado}. Ejecuta main.py para generar su ficha y QR.")
    return resultado


def retirar_participante(leer=input):
    """Marca un participante como inactivo. main.py quitará su ficha pública."""
    rut = pedir_rut(leer)
    participantes = datos.leer_participantes()
    registro = datos.buscar_por_rut(participantes, rut)
    if registro is None:
        print("No existe un participante con ese RUT.")
        return False
    print(f"Participante: {registro['nombres']} {registro['apellidos']}")
    if not pedir_si_no("¿Retirar su ficha pública?", leer):
        return False
    registro["activo"] = "no"
    datos.guardar_participante(registro)
    print("Ficha marcada para retiro. Ejecuta main.py y publica los cambios.")
    return True


def ejecutar_formulario(leer=input):
    """Menú principal del formulario."""
    while True:
        print("\n=== Fundación Sin Barreras - Registro de fichas ===")
        print("1. Registrar o actualizar participante")
        print("2. Retirar ficha de un participante")
        print("3. Salir")
        opcion = leer("Opción: ").strip()
        if opcion == "1":
            registrar_participante(leer)
        elif opcion == "2":
            retirar_participante(leer)
        elif opcion == "3":
            break
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    ejecutar_formulario()
