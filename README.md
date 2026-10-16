# Pipeline de control de presión arterial

## Problema y usuario

Un equipo de salud recibe mediciones de presión arterial en CSV y JSON con errores
de carga. El programa descarta registros inválidos, informa el motivo de cada
rechazo y resume la presión sistólica por grupo del estudio.

## Estructura

```text
.
├── README.md
├── .gitignore
├── data/
│   ├── README.md
│   ├── EstudioPresionEdad (1).csv
│   ├── mediciones.csv
│   └── mediciones.json
├── outputs/                 # se genera al ejecutar el programa
├── src/
│   ├── fuentes.py
│   ├── modelo.py
│   ├── pipeline.py
│   └── main.py
└── tests/
    └── test_pipeline.py
```

## Datos

Ver [data/README.md](data/README.md). Cada registro corresponde a un paciente
adulto con una medición.

## Requisitos y ejecución

Se requiere Python 3.10 o superior. El programa no necesita paquetes externos.
Desde la raíz del repositorio, ejecutar:

```bash
python src/main.py data/mediciones.csv
```

El comando imprime la cantidad de registros leídos, válidos y rechazados, y
genera `outputs/reporte.csv` y `outputs/rechazos.csv`.

## Pruebas

Desde la raíz del repositorio:

```bash
python tests/test_pipeline.py
```

Si todas las verificaciones pasan, se imprime `Todas las pruebas pasaron.`

## Reglas de limpieza

- El código debe cumplir el formato `PAC-` seguido de tres dígitos (`PAC-\d{3}`).
- La edad debe estar entre 18 y 100 años, inclusive.
- El IMC debe estar entre 12 y 60 kg/m², inclusive.
- La presión sistólica debe estar entre 70 y 250 mmHg, inclusive.
- El grupo debe ser `A` (control) o `B` (intervención).
- Los valores faltantes y no numéricos se rechazan indicando el motivo.
- Si un código válido ya fue aceptado, las apariciones posteriores se rechazan
  como duplicadas; se conserva la primera aparición.
- Los motivos múltiples de rechazo se separan con `; `.

## Resultado de ejemplo

Con los datos incluidos, el programa procesa 58 registros: acepta 50 y rechaza
8. El resumen por grupo es:

| Grupo | Cantidad | Presión sistólica media | Proporción de hipertensos |
|---|---:|---:|---:|
| A | 27 | 127.26 mmHg | 0.185 |
| B | 23 | 118.61 mmHg | 0.130 |

El umbral didáctico para considerar hipertensión es 140 mmHg o más; no constituye
un diagnóstico clínico.

## Limitaciones

Los datos son simulados y corresponden a 50 pacientes adultos; se añadieron
8 registros incorrectos con fines didácticos. El umbral de hipertensión es un
criterio simplificado y el programa no debe utilizarse para tomar decisiones
clínicas.
