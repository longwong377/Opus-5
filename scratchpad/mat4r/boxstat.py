import sys, numpy as np
from PIL import Image
sys.path.insert(0, "/home/user/Opus-5/tools")
from measure_frame import srgb_to_linear, LUMA, FLOOR

path = sys.argv[1]
a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
lin = srgb_to_linear(a); y = lin @ np.array(LUMA)
h, w = y.shape
for spec in sys.argv[2:]:
    name, l, t, r, b = spec.split(",")
    l, t, r, b = float(l), float(t), float(r), float(b)
    sub = y[int(t*h):int(b*h), int(l*w):int(r*w)]
    subrgb = a[int(t*h):int(b*h), int(l*w):int(r*w)]
    print(f"{name:22s} px={sub.size:6d}  linY med={np.median(sub):.5f} "
          f"p5={np.percentile(sub,5):.5f} p95={np.percentile(sub,95):.5f} "
          f"crushed={np.mean(sub<FLOOR)*100:5.1f}%  "
          f"sRGB byte med={np.median(subrgb*255,axis=(0,1)).round(1)}")
