"""Validación, limpieza y generación del reporte de mediciones."""

import csv
import re

from modelo import Paciente


PATRON_CODIGO = re.compile(r"PAC-\d{3}")
RANGOS = {
    "edad": (18, 100),
    "imc": (12, 60),
    "presion_sistolica": (70, 250),
}
GRUPOS_VALIDOS = {"A", "B"}


def convertir_numero(valor):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    return float(valor)


def validar_registro(registro):
    motivos = []
    codigo = registro.get("codigo")

    if not isinstance(codigo, str) or PATRON_CODIGO.fullmatch(codigo) is None:
        motivos.append("código con formato inválido")

    for campo, (minimo, maximo) in RANGOS.items():
        try:
            numero = convertir_numero(registro.get(campo))
        except (TypeError, ValueError):
            motivos.append(f"{campo} no numérico")
            continue

        if numero is None:
            motivos.append(f"{campo} faltante")
        elif not minimo <= numero <= maximo:
            motivos.append(f"{campo} fuera de rango")

    if registro.get("grupo") not in GRUPOS_VALIDOS:
        motivos.append("grupo inválido")

    return motivos


def limpiar(registros):
    validos = []
    rechazos = []
    codigos_aceptados = set()

    for fila, registro in enumerate(registros, start=1):
        codigo = registro.get("codigo")
        motivos = validar_registro(registro)

        if isinstance(codigo, str) and codigo in codigos_aceptados:
            motivos.append("código duplicado")

        if motivos:
            rechazos.append({
                "fila": fila,
                "codigo": codigo,
                "motivo": "; ".join(motivos),
            })
            continue

        validos.append(Paciente(
            codigo,
            convertir_numero(registro["edad"]),
            convertir_numero(registro["imc"]),
            convertir_numero(registro["presion_sistolica"]),
            registro["grupo"],
        ))
        codigos_aceptados.add(codigo)

    return validos, rechazos


def generar_reporte(pacientes):
    reporte = []

    for grupo in ("A", "B"):
        pacientes_grupo = [paciente for paciente in pacientes if paciente.grupo == grupo]
        cantidad = len(pacientes_grupo)
        presion_media = (
            round(sum(paciente.presion for paciente in pacientes_grupo) / cantidad, 2)
            if cantidad
            else 0.0
        )
        proporcion_hipertensos = (
            round(sum(paciente.es_hipertenso() for paciente in pacientes_grupo) / cantidad, 3)
            if cantidad
            else 0.0
        )
        reporte.append({
            "grupo": grupo,
            "cantidad": cantidad,
            "presion_media": presion_media,
            "proporcion_hipertensos": proporcion_hipertensos,
        })

    return reporte


def guardar_csv(filas, ruta):
    encabezados = filas[0].keys()
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=encabezados)
        escritor.writeheader()
        escritor.writerows(filas)
