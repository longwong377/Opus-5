"""Measurements for the docking bay craft round. Not a gate; a notebook.

Every statistic here is taken in LINEAR light (sRGB decoded), because a mean
of gamma-encoded bytes is not a mean of anything physical.
"""
import sys
import numpy as np
from PIL import Image


def lin(path, box=None):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float64) / 255.0
    if box:
        l, t, r, b = box
        w, h = im.size
        a = a[int(t * h):int(b * h), int(l * w):int(r * w)]
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def stats(name, path, box=None):
    a = lin(path, box)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # WARM: red channel above blue by a margin, over pixels bright enough to
    # have a hue at all. Below 0.002 linear a byte is 0 or 1 and its chroma is
    # quantisation.
    vis = lum > 0.002
    warm = (r > b * 1.15) & vis
    cool = (b > r * 1.15) & vis
    print(f"{name:34s} {path}")
    print(f"   mean linear rgb   {r.mean():.4f} {g.mean():.4f} {b.mean():.4f}"
          f"   R/B {r.mean() / max(b.mean(), 1e-9):.3f}")
    print(f"   visible px        {100 * vis.mean():5.1f}%"
          f"   warm {100 * warm.mean():5.1f}%   cool {100 * cool.mean():5.1f}%"
          f"   warm/cool {warm.sum() / max(cool.sum(), 1):.3f}")
    return dict(r=r.mean(), g=g.mean(), b=b.mean(),
                warm=warm.mean(), cool=cool.mean())


if __name__ == "__main__":
    for p in sys.argv[1:]:
        if ":" in p:
            nm, path = p.split(":", 1)
        else:
            nm, path = p, p
        stats(nm, path)
