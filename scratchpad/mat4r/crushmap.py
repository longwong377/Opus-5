"""Where are the crushed pixels? A crushed FRACTION says how many; it does not
say which surface, and the two readings of `garden_bark` need exactly that."""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, "/home/user/Opus-5/tools")
from measure_frame import srgb_to_linear, LUMA, FLOOR, CLIP

for path in sys.argv[1:]:
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    y = srgb_to_linear(a) @ np.array(LUMA)
    h, w = y.shape
    crushed = y < FLOOR
    print(f"{path}  {w}x{h}  crushed {crushed.mean()*100:5.2f}%  "
          f"n={crushed.sum()}")
    # Row/column profile of the crushed population, in tenths.
    rows = [crushed[int(i*h/10):int((i+1)*h/10)].mean() for i in range(10)]
    cols = [crushed[:, int(i*w/10):int((i+1)*w/10)].mean() for i in range(10)]
    print("  crushed by row tenth (top->bottom): "
          + " ".join(f"{r*100:5.1f}" for r in rows))
    print("  crushed by col tenth (left->right): "
          + " ".join(f"{c*100:5.1f}" for c in cols))
    # Save a map: crushed = magenta over a dimmed copy of the frame.
    vis = (a * 0.35 * 255).astype(np.uint8)
    vis[crushed] = (255, 0, 255)
    Image.fromarray(vis).save(path.rsplit("/", 1)[-1].replace(".png", "-crushmap.png"))
