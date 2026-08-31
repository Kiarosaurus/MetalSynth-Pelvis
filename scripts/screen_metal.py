"""
Screening de metal por umbral HU + componentes conexas.
Corre sobre dataset7 (CLINIC-metal) y dataset6 (CLINIC, verificacion de limpieza).
Salidas: metal_screening.csv + PNGs de revision en outputs/metal_png/
"""
from pathlib import Path
import time, csv
import numpy as np
import SimpleITK as sitk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------- Parametros (documentar en bitacora) ----------------
THR_HU      = 2500    # umbral metal: > hueso cortical (~1900) y calcificaciones
MIN_VOL_MM3 = 100     # volumen minimo de componente para descartar ruido
CLIP_HU     = 3071    # valor tipico de clipping int12; se reporta meseta
BASE = Path.home() / "metalsynth" / "data" / "extracted"
OUT  = Path.home() / "metalsynth" / "outputs"
PNG  = OUT / "metal_png"
PNG.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "dataset7": BASE / "CTPelvic1K_dataset7_data",
    "dataset6": BASE / "CTPelvic1K_dataset6_data",
}

def window(arr2d, wl, ww):
    lo, hi = wl - ww/2, wl + ww/2
    return np.clip((arr2d - lo) / (hi - lo), 0, 1)

def review_png(arr, mask, z, name, info):
    img = arr[z]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))
    axes[0].imshow(window(img, 400, 1800), cmap="gray"); axes[0].set_title("Osea WL400/WW1800")
    axes[1].imshow(window(img, 500, 4000), cmap="gray"); axes[1].set_title("Amplia WL500/WW4000")
    axes[2].imshow(window(img, 500, 4000), cmap="gray")
    axes[2].contour(mask[z], levels=[0.5], colors="r", linewidths=0.8)
    axes[2].set_title("Metal > %d HU" % THR_HU)
    for ax in axes: ax.axis("off")
    fig.suptitle(f"{name}  slice z={z}  |  {info}", fontsize=10)
    fig.tight_layout()
    fig.savefig(PNG / f"{name}_z{z}.png", dpi=110, bbox_inches="tight")
    plt.close(fig)

rows = []
for tag, folder in DATASETS.items():
    files = sorted(folder.glob("*.nii.gz"))
    print(f"\n### {tag}: {len(files)} volumenes")
    for f in files:
        t0 = time.time()
        img = sitk.ReadImage(str(f))
        arr = sitk.GetArrayFromImage(img).astype(np.int32)  # (z,y,x)
        hu_min, hu_max = int(arr.min()), int(arr.max())
        plateau = int((arr >= CLIP_HU).sum())

        bin_img = sitk.GetImageFromArray((arr > THR_HU).astype(np.uint8))
        bin_img.CopyInformation(img)
        cc = sitk.ConnectedComponent(bin_img)
        st = sitk.LabelShapeStatisticsImageFilter()
        st.Execute(cc)
        comps = [(l, st.GetPhysicalSize(l)) for l in st.GetLabels()
                 if st.GetPhysicalSize(l) >= MIN_VOL_MM3]
        has_metal = len(comps) > 0
        total = sum(v for _, v in comps)
        vmax  = max((v for _, v in comps), default=0.0)

        z_best = -1
        if has_metal:
            mask = (sitk.GetArrayFromImage(cc) > 0)
            # limpiar componentes pequenas de la mascara de visualizacion
            keep = {l for l, _ in comps}
            cc_arr = sitk.GetArrayFromImage(cc)
            mask = np.isin(cc_arr, list(keep))
            z_best = int(mask.sum(axis=(1, 2)).argmax())  # slice con mas metal
            info = f"{len(comps)} comp | {total/1000:.1f} cm3 | HUmax {hu_max}"
            review_png(arr, mask, z_best, f.name.replace(".nii.gz", ""), info)

        dt = time.time() - t0
        rows.append(dict(dataset=tag, file=f.name, has_metal=has_metal,
                         n_comp=len(comps), total_mm3=round(total, 1),
                         max_comp_mm3=round(vmax, 1), z_best=z_best,
                         hu_min=hu_min, hu_max=hu_max,
                         n_vox_at_clip=plateau, sec=round(dt, 1)))
        flag = "METAL" if has_metal else "  -  "
        print(f"[{flag}] {f.name}  comps={len(comps)}  {total/1000:6.1f} cm3  "
              f"HUmax={hu_max}  clip_vox={plateau}  {dt:.1f}s")

with open(OUT / "metal_screening.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

n7 = sum(r["has_metal"] for r in rows if r["dataset"] == "dataset7")
n6 = sum(r["has_metal"] for r in rows if r["dataset"] == "dataset6")
print(f"\nRESUMEN: dataset7 con metal: {n7}/75 | dataset6 con metal: {n6}/103")
print(f"CSV: {OUT/'metal_screening.csv'} | PNGs: {PNG}")
