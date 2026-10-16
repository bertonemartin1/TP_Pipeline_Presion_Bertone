"""Pruebas automáticas del flujo de procesamiento."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from statistics import correlation


RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from fuentes import FuenteCSV, FuenteDatos, FuenteJSON
from modelo import Paciente
from pipeline import (
    convertir_numero,
    generar_reporte,
    guardar_csv,
    limpiar,
    validar_registro,
)


RUTA_CSV = RAIZ / "data" / "mediciones.csv"
RUTA_JSON = RAIZ / "data" / "mediciones.json"


class PruebasPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registros_csv = FuenteCSV().cargar(RUTA_CSV)
        cls.registros_json = FuenteJSON().cargar(RUTA_JSON)
        cls.validos, cls.rechazos = limpiar(cls.registros_csv)

    def test_lecturas_csv_y_json(self):
        self.assertEqual(len(self.registros_csv), 58)
        self.assertEqual(len(self.registros_json), 58)
        self.assertIsInstance(self.registros_csv[0], dict)
        self.assertEqual(
            set(self.registros_csv[0]),
            {"codigo", "edad", "imc", "presion_sistolica", "grupo"},
        )
        self.assertIsInstance(self.registros_csv[0]["edad"], str)
        self.assertIsInstance(self.registros_json[0]["edad"], int)

    def test_archivo_inexistente_y_json_no_listado(self):
        with self.assertRaises(FileNotFoundError):
            FuenteCSV().cargar(RAIZ / "data" / "no_existe.csv")

        with tempfile.TemporaryDirectory() as carpeta_temporal:
            ruta_json = Path(carpeta_temporal) / "objeto.json"
            ruta_json.write_text(json.dumps({"codigo": "PAC-001"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lista"):
                FuenteJSON().cargar(ruta_json)

    def test_fuente_datos_es_abstracta(self):
        with self.assertRaises(TypeError):
            FuenteDatos()

    def test_convertir_numero(self):
        self.assertEqual(convertir_numero("28.8"), 28.8)
        self.assertEqual(convertir_numero(28.8), 28.8)
        self.assertIsNone(convertir_numero(""))
        self.assertIsNone(convertir_numero("   "))
        self.assertIsNone(convertir_numero(None))
        with self.assertRaises(ValueError):
            convertir_numero("abc")

    def test_validar_registro_y_limites(self):
        registro = {
            "codigo": "PAC-999",
            "edad": "18",
            "imc": "12",
            "presion_sistolica": "70",
            "grupo": "A",
        }
        self.assertEqual(validar_registro(registro), [])
        self.assertEqual(
            validar_registro({
                **registro,
                "edad": "100",
                "imc": "60",
                "presion_sistolica": "250",
            }),
            [],
        )

        casos_invalidos = [
            {"codigo": "PAC01"},
            {"edad": ""},
            {"imc": "abc"},
            {"presion_sistolica": "999"},
            {"grupo": "C"},
            {"edad": "-45"},
            {"presion_sistolica": None},
        ]
        for cambio in casos_invalidos:
            with self.subTest(cambio=cambio):
                self.assertTrue(validar_registro({**registro, **cambio}))

    def test_limpieza_conserva_primera_aparicion_y_registra_rechazos(self):
        self.assertEqual(len(self.validos), 50)
        self.assertEqual(len(self.rechazos), 8)
        self.assertTrue(all(isinstance(paciente, Paciente) for paciente in self.validos))
        self.assertTrue(all(isinstance(paciente.edad, float) for paciente in self.validos))
        self.assertEqual(
            [rechazo["fila"] for rechazo in self.rechazos if rechazo["codigo"] == "PAC01"],
            [6],
        )
        self.assertTrue(any(
            rechazo["codigo"] == "PAC-012" and "código duplicado" in rechazo["motivo"]
            for rechazo in self.rechazos
        ))
        paciente_12 = [paciente for paciente in self.validos if paciente.codigo == "PAC-012"]
        self.assertEqual(len(paciente_12), 1)
        self.assertEqual(paciente_12[0].presion, 123.0)

    def test_lecturas_csv_y_json_producen_los_mismos_resultados(self):
        validos_json, rechazos_json = limpiar(self.registros_json)
        self.assertEqual(generar_reporte(validos_json), generar_reporte(self.validos))
        self.assertEqual(
            [rechazo["motivo"] for rechazo in rechazos_json],
            [rechazo["motivo"] for rechazo in self.rechazos],
        )

    def test_limpieza_no_modifica_los_registros(self):
        registros = [{
            "codigo": "PAC-999",
            "edad": "40",
            "imc": "25",
            "presion_sistolica": "120",
            "grupo": "A",
        }]
        copia = [dict(registro) for registro in registros]
        limpiar(registros)
        self.assertEqual(registros, copia)

    def test_paciente(self):
        self.assertEqual(str(Paciente("PAC-001", 21.0, 28.8, 97.0, "B")),
                         "PAC-001 | grupo B | 21 años | PAS 97 mmHg")
        for edad, franja in [
            (18, "18-39"),
            (39, "18-39"),
            (40, "40-59"),
            (59, "40-59"),
            (60, "60+"),
        ]:
            with self.subTest(edad=edad):
                self.assertEqual(
                    Paciente("PAC-001", float(edad), 25.0, 120.0, "A").franja_etaria(),
                    franja,
                )
        self.assertTrue(Paciente("PAC-001", 50.0, 25.0, 140.0, "A").es_hipertenso())
        self.assertFalse(Paciente("PAC-001", 50.0, 25.0, 139.0, "A").es_hipertenso())

    def test_reporte_por_grupo_y_lista_vacia(self):
        reporte = generar_reporte(self.validos)
        self.assertEqual([fila["grupo"] for fila in reporte], ["A", "B"])
        fila_a, fila_b = reporte
        self.assertEqual((fila_a["cantidad"], fila_b["cantidad"]), (27, 23))
        self.assertEqual(fila_a["presion_media"], 127.26)
        self.assertEqual(fila_b["presion_media"], 118.61)
        self.assertEqual(fila_a["proporcion_hipertensos"], 0.185)
        self.assertEqual(fila_b["proporcion_hipertensos"], 0.13)
        self.assertTrue(all(fila["cantidad"] == 0 for fila in generar_reporte([])))

        correlacion = correlation(
            [paciente.edad for paciente in self.validos],
            [paciente.presion for paciente in self.validos],
        )
        self.assertAlmostEqual(correlacion, 0.794, places=3)

    def test_guardar_csv(self):
        filas = generar_reporte(self.validos)
        with tempfile.TemporaryDirectory() as carpeta_temporal:
            ruta_csv = Path(carpeta_temporal) / "reporte.csv"
            guardar_csv(filas, ruta_csv)
            releido = FuenteCSV().cargar(ruta_csv)
        self.assertEqual(len(releido), 2)
        self.assertEqual(releido[0]["grupo"], "A")

    def test_comando_principal(self):
        resultado = subprocess.run(
            [
                sys.executable,
                str(RAIZ / "src" / "main.py"),
                "data/mediciones.csv",
            ],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("Leídos: 58 | válidos: 50 | rechazados: 8", resultado.stdout)
        self.assertTrue((RAIZ / "outputs" / "reporte.csv").is_file())
        self.assertTrue((RAIZ / "outputs" / "rechazos.csv").is_file())


if __name__ == "__main__":
    resultado_pruebas = unittest.main(verbosity=2, exit=False)
    if not resultado_pruebas.result.wasSuccessful():
        sys.exit(1)
    print("Todas las pruebas pasaron.")
