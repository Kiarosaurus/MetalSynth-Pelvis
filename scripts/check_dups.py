import hashlib
from pathlib import Path
import SimpleITK as sitk
BASE = Path.home() / "metalsynth" / "data" / "extracted"
pairs = [("CTPelvic1K_dataset6_data/dataset6_CLINIC_0037_data.nii.gz",
          "CTPelvic1K_dataset7_data/dataset7_CLINIC_metal_0061_data.nii.gz"),
         ("CTPelvic1K_dataset6_data/dataset6_CLINIC_0048_data.nii.gz",
          "CTPelvic1K_dataset7_data/dataset7_CLINIC_metal_0036_data.nii.gz"),
         ("CTPelvic1K_dataset6_data/dataset6_CLINIC_0070_data.nii.gz",
          "CTPelvic1K_dataset7_data/dataset7_CLINIC_metal_0064_data.nii.gz")]
def vhash(p):
    a = sitk.GetArrayFromImage(sitk.ReadImage(str(BASE/p)))
    return hashlib.md5(a.tobytes()).hexdigest()
for a, b in pairs:
    ha, hb = vhash(a), vhash(b)
    print(f"{'DUPLICADO' if ha==hb else 'DISTINTO '}  {Path(a).name} <-> {Path(b).name}")
