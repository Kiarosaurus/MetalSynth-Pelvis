"""
Reporte final: responde las tareas de la semana (Sep 3) a partir de los CSVs curados.
Entradas : per_volume_stats.csv, metal_screening.csv, excluded_clinic_ids.csv,
           excluded_metal_ids.csv, test_ids.txt, ejemplos_seleccion.csv
Salidas  : reporte_semana.md, cohorte_A_ids.txt, cohorte_B_ids.txt, macros_datos.tex
"""
from pathlib import Path
import pandas as pd

OUT = Path.home() / "metalsynth" / "outputs"

pv   = pd.read_csv(OUT / "per_volume_stats.csv")
scr  = pd.read_csv(OUT / "metal_screening.csv")
exc6 = pd.read_csv(OUT / "excluded_clinic_ids.csv")
exc7 = pd.read_csv(OUT / "excluded_metal_ids.csv")
sel  = pd.read_csv(OUT / "ejemplos_seleccion.csv")
test_ids = [l.strip() for l in open(OUT / "test_ids.txt") if l.strip()]

# ---------- Solo imagenes (excluir mascaras) ----------
img = pv[pv.file.str.endswith("_data.nii.gz")].copy()
d6 = img[img.dataset == "CTPelvic1K_dataset6_data"]
d7 = img[img.dataset == "CTPelvic1K_dataset7_data"]

def rango(d, c, fmt="{:.3f}"):
    return f"mediana {fmt.format(d[c].median())}, rango [{fmt.format(d[c].min())} – {fmt.format(d[c].max())}]"

# ---------- Cohortes desde las listas de exclusion ----------
excl6_files = set(exc6[exc6.estado != "falso_positivo"].file)
cohA = sorted(set(d6.file) - excl6_files)

excl7_files = set(exc7.file)
test_files  = {f"dataset7_{t}_data.nii.gz" for t in test_ids}
cohB = sorted(set(d7.file) - excl7_files - test_files)

# Consistencia
assert len(d6) == 103 and len(d7) == 75, "conteo de imagenes inesperado"
assert len(test_files & set(d7.file)) == 14, "test_ids no cuadra con dataset7"
assert not (set(cohB) & test_files), "FUGA: volumen de test en cohorte B"
assert not (excl7_files & test_files), "excluido de d7 marcado como test"

(OUT / "cohorte_A_ids.txt").write_text("\n".join(cohA) + "\n")
(OUT / "cohorte_B_ids.txt").write_text("\n".join(cohB) + "\n")

# ---------- Screening / metal ----------
s7 = scr[scr.dataset == "dataset7"]
s6 = scr[scr.dataset == "dataset6"]
n6_metal = len(excl6_files) - 3          # exclusiones menos los 3 duplicados
fp6 = (exc6.estado == "falso_positivo").sum()

# ---------- Ejemplos: estratos y rangos HU ----------
d7m = scr[(scr.dataset == "dataset7")].sort_values("total_mm3", ascending=False)
q33, q66 = d7m.total_mm3.quantile([.33, .66])
def estrato(v):
    return "grande" if v >= q66 else ("mediano" if v >= q33 else "pequeno")
sel = sel.copy()
sel["estrato"] = sel.total_mm3.apply(estrato)

# ---------- Reporte ----------
L = []
L.append("# Respuestas — tareas de la semana (Sep 3)\n")
L.append("## 1. Data description\n")
L.append("**Datasets:** CTPelvic1K, subsets CLINIC (dataset6, preoperatorio) y "
         "CLINIC-metal (dataset7, con metal). Fuente: Zenodo record 4588403.\n")
L.append("**Numero de imagenes:**\n")
L.append(f"- CLINIC: {len(d6)} imagenes (103 mascaras oseas)")
L.append(f"- CLINIC-metal: {len(d7)} imagenes (14 mascaras oseas)\n")
L.append("**Voxel spacing (mm):**\n")
for name, d in [("CLINIC", d6), ("CLINIC-metal", d7)]:
    L.append(f"- {name}: in-plane {rango(d,'sp_x')} | z {rango(d,'sp_z','{:.4f}')}")
L.append("\n**Dimensiones (voxeles):** 512x512 in-plane en el 100% de los volumenes.\n")
for name, d in [("CLINIC", d6), ("CLINIC-metal", d7)]:
    L.append(f"- {name}: z {rango(d,'dim_z','{:.0f}')}")

L.append("\n## 2. Identify the images with metal\n")
L.append(f"**Que dataset contiene metal:** CLINIC-metal por diseno "
         f"({int(s7.has_metal.sum())}/{len(s7)} con metal detectado, umbral 2500 HU, "
         f"componentes >= 100 mm3). Hallazgo: CLINIC ('limpio') contiene metal "
         f"incidental en {n6_metal} volumenes (electrodos, DIU, piercings, hardware previo) "
         f"+ 3 duplicados de CLINIC-metal; {fp6} deteccion resulto falso positivo "
         f"(artefacto de borde de FOV).\n")
L.append(f"**Cuantas imagenes:** {int(s7.has_metal.sum())} en CLINIC-metal "
         f"(72 unicas tras deduplicacion por hash de voxeles) + {n6_metal} incidentales en CLINIC.\n")
L.append("**Ejemplos** (carpeta `ejemplos_asesor/`, seleccion estratificada por volumen de metal):\n")
for _, r in sel.iterrows():
    L.append(f"- `{r.file}` — {r.estrato}: {r.total_mm3/1000:.1f} cm3, "
             f"{r.n_comp} componentes, HUmax {r.hu_max}")
L.append(f"\nCriterio: cubrir el rango completo de carga metalica "
         f"({d7m.total_mm3.min()/1000:.1f}–{d7m.total_mm3.max()/1000:.1f} cm3, factor ~300x): "
         f"estrato grande = protesis/material masivo, mediano = caso tipico, "
         f"pequeno = tornillos/objetos aislados cuyo artefacto excede con mucho su mascara. "
         f"HUmax observado en dataset7: {s7.hu_max.min()}–{s7.hu_max.max()} "
         f"(rango extendido, sin truncamiento a 3071).\n")

L.append("## 3. Training / testing\n")
L.append(f"| Cohorte | Definicion | N |\n|---|---|---|")
L.append(f"| A | CLINIC libre de material generador de artefactos (screening + triaje) | {len(cohA)} |")
L.append(f"| B | CLINIC-metal unicos sin anotacion (entrenamiento renderer) | {len(cohB)} |")
L.append(f"| C | CLINIC-metal anotados — test intocable | {len(test_ids)} |")
L.append("\nListas versionadas: `cohorte_A_ids.txt`, `cohorte_B_ids.txt`, `test_ids.txt`. "
         "Exclusiones con motivo: `excluded_clinic_ids.csv`, `excluded_metal_ids.csv`. "
         "Duplicados (6 pares, incluida fuga train/test del dataset original): `duplicados.csv`.\n")

rep = "\n".join(L)
(OUT / "reporte_semana.md").write_text(rep)
print(rep)

# ---------- Macros LaTeX ----------
(OUT / "macros_datos.tex").write_text(
    f"% Generado por reporte_semana.py — no editar a mano\n"
    f"\\newcommand{{\\Nmetal}}{{75}}\n"
    f"\\newcommand{{\\NmetalUnicos}}{{72}}\n"
    f"\\newcommand{{\\Neval}}{{{len(test_ids)}}}\n"
    f"\\newcommand{{\\NcohorteA}}{{{len(cohA)}}}\n"
    f"\\newcommand{{\\NcohorteB}}{{{len(cohB)}}}\n"
    f"\\newcommand{{\\NclinicTotal}}{{103}}\n"
    f"\\newcommand{{\\NclinicExcluidos}}{{{len(excl6_files)}}}\n")
print(f"\nOK: reporte_semana.md, cohorte_A_ids.txt ({len(cohA)}), "
      f"cohorte_B_ids.txt ({len(cohB)}), macros_datos.tex")
