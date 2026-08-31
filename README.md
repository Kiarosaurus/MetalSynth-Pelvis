# MetalSynth-Pelvis — Análisis y curación de datos

Análisis descriptivo, screening de metal y definición de cohortes para la tesis
**MetalSynth-Pelvis** (síntesis condicionada de implantes de osteosíntesis y
artefactos metálicos locales en CT pélvico). PFCII, UTEC.
Autora: Kiara Balcázar. Asesor: Víctor Flores Benites.

## Datos (no incluidos en este repositorio)

Fuente: CTPelvic1K, subsets CLINIC (dataset6) y CLINIC-metal (dataset7).
Descarga: Zenodo, record 4588403. Verificación de integridad por MD5
(valores en `outputs/logs/`). Fecha de descarga: <FECHA>.

## Estructura

- `scripts/` — pipeline de análisis, en orden de ejecución:
  1. `describe_data.py` — estadísticas de headers (spacing, dimensiones)
  2. `screen_metal.py` — screening de metal (umbral 2500 HU, componentes
     conexas >= 100 mm3) sobre los 178 volúmenes + PNGs de revisión
  3. `check_dups.py` — verificación de duplicados candidatos por hash MD5 de vóxeles
  4. `finalize_screening.py` — dedup exhaustivo, lista de exclusión, selección de ejemplos
- `outputs/` — resultados derivados (CSVs, listas de IDs, logs)

## Cohortes (estado: <FECHA>)

| Cohorte | Definición | N | Lista |
|---|---|---|---|
| A | CLINIC libre de material generador de artefactos (screening + triaje visual) | 77 | complemento de `excluded_clinic_ids.csv` |
| B | CLINIC-metal únicos, sin anotación (entrenamiento renderer) | 58 | complemento de `excluded_metal_ids.csv` y `test_ids.txt` |
| C | CLINIC-metal anotados — test, intocable | 14 | `test_ids.txt` |

**Regla de aislamiento estricto:** ningún volumen de C participa en
entrenamiento ni ajuste de hiperparámetros. La pertenencia a cohortes se
define por listas explícitas de IDs versionadas en este repo, nunca por convención.

## Hallazgos de la curación

1. **Contaminación del corpus "limpio":** 24/103 volúmenes de CLINIC contienen
   metal incidental (electrodos, DIU, piercings, hardware previo) — CLINIC son
   pacientes preoperatorios, el metal incidental sobrevivió a la curación original.
2. **6 pares de volúmenes duplicados** (hash MD5 de vóxeles idéntico):
   3 entre CLINIC y CLINIC-metal, 3 internos a CLINIC-metal.
3. **Fuga train/test en el dataset original:** metal_0021 y metal_0043
   (no anotados, nominalmente entrenamiento) son copias exactas de metal_0012
   y metal_0013 (test anotado). Excluidos de B.
4. **Rango HU extendido:** el metal alcanza ~20,000–30,000 HU (sin truncamiento
   a 3071); hu_min muestra undershoots de reconstrucción hasta ~-14,000.
5. `CLINIC_0039`: detecciones = artefacto de borde de FOV (truncamiento),
   no material denso — retenido en Cohorte A.

## Triaje

Veredictos visuales en `excluded_clinic_ids.csv` (columna `estado`).
Estado actual: triaje propio, pendiente de validación por especialista.
La columna `nota` (tipo de metal) se completará en la sesión con cirujano.
