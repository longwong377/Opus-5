"""Is the screen the brightest thing in its own room? Measured, not looked at."""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, "/home/user/Opus-5/tools")
from measure_frame import srgb_to_linear, LUMA
path = sys.argv[1]
a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
y = srgb_to_linear(a) @ np.array(LUMA)
h, w = y.shape
for spec in sys.argv[2:]:
    name, l, t, r, b = spec.split(",")
    sub = y[int(float(t)*h):int(float(b)*h), int(float(l)*w):int(float(r)*w)]
    print(f"  {name:26s} linY med={np.median(sub):.5f}  p95={np.percentile(sub,95):.5f}"
          f"  max={sub.max():.5f}")
