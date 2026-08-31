"""
1) Dedup exhaustivo por hash de voxeles (178 volumenes)
2) excluded_clinic_ids.csv provisional
3) Seleccion estratificada de ejemplos para el asesor (copia PNGs)
"""
import hashlib, shutil, csv
from pathlib import Path
from collections import defaultdict
import pandas as pd
import SimpleITK as sitk

BASE = Path.home() / "metalsynth" / "data" / "extracted"
OUT  = Path.home() / "metalsynth" / "outputs"
PNG  = OUT / "metal_png"
EX   = OUT / "ejemplos_asesor"
EX.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(OUT / "metal_screening.csv")

# ---------- 1) DEDUP EXHAUSTIVO ----------
print("=== Dedup por hash de voxeles (tarda ~5-15 min) ===")
hashes = defaultdict(list)
folders = {"dataset6": "CTPelvic1K_dataset6_data", "dataset7": "CTPelvic1K_dataset7_data"}
for tag, folder in folders.items():
    for f in sorted((BASE / folder).glob("*.nii.gz")):
        a = sitk.GetArrayFromImage(sitk.ReadImage(str(f)))
        h = hashlib.md5(a.tobytes()).hexdigest()
        hashes[h].append(f.name)
        print(".", end="", flush=True)
dups = {h: v for h, v in hashes.items() if len(v) > 1}
print(f"\nGrupos duplicados encontrados: {len(dups)}")
dup_d6 = set()
with open(OUT / "duplicados.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["md5_voxeles", "archivos"])
    for h, v in dups.items():
        w.writerow([h, " | ".join(v)])
        print("  DUP:", " <-> ".join(v))
        for name in v:
            if name.startswith("dataset6"):
                dup_d6.add(name)

# ---------- 2) LISTA DE EXCLUSION PROVISIONAL ----------
d6pos = df[(df.dataset == "dataset6") & df.has_metal].copy()
rows = []
for _, r in d6pos.iterrows():
    if r.file in dup_d6:
        pareja = next(x for h, v in dups.items() if r.file in v for x in v if x != r.file)
        motivo, estado = f"duplicado_de_{pareja}", "definitivo"
    else:
        motivo, estado = "metal_detectado", "pendiente_revision"
    rows.append(dict(file=r.file, motivo=motivo, estado=estado,
                     n_comp=r.n_comp, total_mm3=r.total_mm3,
                     hu_max=r.hu_max, png=f"{r.file.replace('.nii.gz','')}_z{r.z_best}.png"))
pd.DataFrame(rows).to_csv(OUT / "excluded_clinic_ids.csv", index=False)
n_def = sum(1 for r in rows if r["estado"] == "definitivo")
print(f"\nExclusiones: {len(rows)} total ({n_def} definitivas, {len(rows)-n_def} pendientes de triaje)")
print(f"Cohorte A provisional: {103 - len(rows)} volumenes (puede crecer si hay FPs en el triaje)")

# ---------- 3) SELECCION DE EJEMPLOS ----------
d7 = df[(df.dataset == "dataset7") & df.has_metal].sort_values("total_mm3", ascending=False).reset_index(drop=True)
grandes  = d7.head(3)                                  # THA / material masivo
n = len(d7); medianos = d7.iloc[[n//2 - 1, n//2, n//2 + 1]]  # banda de la mediana
pequenos = d7.tail(2)                                  # tornillos aislados
sel = pd.concat([grandes, medianos, pequenos])
print("\n=== Ejemplos seleccionados (8) ===")
copiados = 0
for _, r in sel.iterrows():
    png_name = f"{r.file.replace('.nii.gz','')}_z{r.z_best}.png"
    src = PNG / png_name
    if src.exists():
        shutil.copy(src, EX / png_name); copiados += 1
        print(f"  {r.file}  {r.total_mm3/1000:6.1f} cm3  {r.n_comp} comp  -> {png_name}")
    else:
        print(f"  FALTA PNG: {png_name}")
sel.to_csv(OUT / "ejemplos_seleccion.csv", index=False)
print(f"\n{copiados} PNGs copiados a {EX}")
