# Respuestas — tareas de la semana (Sep 3)

## 1. Data description

**Datasets:** CTPelvic1K, subsets CLINIC (dataset6, preoperatorio) y CLINIC-metal (dataset7, con metal). Fuente: Zenodo record 4588403.

**Numero de imagenes:**

- CLINIC: 103 imagenes (103 mascaras oseas)
- CLINIC-metal: 75 imagenes (14 mascaras oseas)

**Voxel spacing (mm):**

- CLINIC: in-plane mediana 0.839, rango [0.640 – 1.129] | z mediana 0.8000, rango [0.7990 – 0.8010]
- CLINIC-metal: in-plane mediana 0.820, rango [0.601 – 1.266] | z mediana 0.8000, rango [0.7990 – 0.8010]

**Dimensiones (voxeles):** 512x512 in-plane en el 100% de los volumenes.

- CLINIC: z mediana 350, rango [294 – 388]
- CLINIC-metal: z mediana 350, rango [187 – 351]

## 2. Identify the images with metal

**Que dataset contiene metal:** CLINIC-metal por diseno (75/75 con metal detectado, umbral 2500 HU, componentes >= 100 mm3). Hallazgo: CLINIC ('limpio') contiene metal incidental en 23 volumenes (electrodos, DIU, piercings, hardware previo) + 3 duplicados de CLINIC-metal; 1 deteccion resulto falso positivo (artefacto de borde de FOV).

**Cuantas imagenes:** 75 en CLINIC-metal (72 unicas tras deduplicacion por hash de voxeles) + 23 incidentales en CLINIC.

**Ejemplos** (carpeta `ejemplos_asesor/`, seleccion estratificada por volumen de metal):

- `dataset7_CLINIC_metal_0037_data.nii.gz` — grande: 99.0 cm3, 7 componentes, HUmax 22999
- `dataset7_CLINIC_metal_0047_data.nii.gz` — grande: 77.6 cm3, 12 componentes, HUmax 19895
- `dataset7_CLINIC_metal_0023_data.nii.gz` — grande: 65.1 cm3, 5 componentes, HUmax 18782
- `dataset7_CLINIC_metal_0007_data.nii.gz` — mediano: 16.4 cm3, 4 componentes, HUmax 17265
- `dataset7_CLINIC_metal_0056_data.nii.gz` — mediano: 15.7 cm3, 3 componentes, HUmax 17790
- `dataset7_CLINIC_metal_0063_data.nii.gz` — mediano: 15.5 cm3, 2 componentes, HUmax 21233
- `dataset7_CLINIC_metal_0036_data.nii.gz` — pequeno: 0.9 cm3, 1 componentes, HUmax 18002
- `dataset7_CLINIC_metal_0064_data.nii.gz` — pequeno: 0.3 cm3, 1 componentes, HUmax 14389

Criterio: cubrir el rango completo de carga metalica (0.3–99.0 cm3, factor ~300x): estrato grande = protesis/material masivo, mediano = caso tipico, pequeno = tornillos/objetos aislados cuyo artefacto excede con mucho su mascara. HUmax observado en dataset7: 3678–24970 (rango extendido, sin truncamiento a 3071).

## 3. Training / testing

| Cohorte | Definicion | N |
|---|---|---|
| A | CLINIC libre de material generador de artefactos (screening + triaje) | 77 |
| B | CLINIC-metal unicos sin anotacion (entrenamiento renderer) | 58 |
| C | CLINIC-metal anotados — test intocable | 14 |

Listas versionadas: `cohorte_A_ids.txt`, `cohorte_B_ids.txt`, `test_ids.txt`. Exclusiones con motivo: `excluded_clinic_ids.csv`, `excluded_metal_ids.csv`. Duplicados (6 pares, incluida fuga train/test del dataset original): `duplicados.csv`.
