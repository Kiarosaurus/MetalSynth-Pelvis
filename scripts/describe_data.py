from pathlib import Path
import SimpleITK as sitk
import pandas as pd

BASE = Path.home() / "metalsynth" / "data" / "extracted"
OUT  = Path.home() / "metalsynth" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

rows = []
for f in sorted(BASE.rglob("*.nii.gz")):
    try:
        r = sitk.ImageFileReader()
        r.SetFileName(str(f))
        r.ReadImageInformation()
        sx, sy, sz = r.GetSpacing()
        dx, dy, dz = r.GetSize()
        # dataset = primera carpeta despues de BASE
        dataset = f.relative_to(BASE).parts[0]
        rows.append(dict(dataset=dataset, file=f.name,
                         sp_x=sx, sp_y=sy, sp_z=sz,
                         dim_x=dx, dim_y=dy, dim_z=dz))
    except Exception as e:
        print(f"ERROR leyendo {f}: {e}")

df = pd.DataFrame(rows)
print(f"\nTotal archivos leidos: {len(df)}")
print(df.groupby("dataset").size().rename("n_files"), "\n")

cols = ["sp_x", "sp_y", "sp_z", "dim_x", "dim_y", "dim_z"]
summary = df.groupby("dataset")[cols].agg(["median", "min", "max"])
summary.insert(0, ("n", "count"), df.groupby("dataset").size())

df.to_csv(OUT / "per_volume_stats.csv", index=False)
summary.to_csv(OUT / "dataset_summary.csv")
print(summary.to_string())
print(f"\nGuardado en {OUT}")
