"""Double precision and floating origin at station scale.

The station is 8,047 m long and a Starfury will fly tens of kilometres out from
it. float32 carries about 7 significant decimal digits, so at 8 km the spacing
between representable values is already ~0.5 mm and at 50 km it is ~4 mm.
That is visible jitter on a stationary object, and it is why the engine is
built with precision=double (ADR 0001).

Double precision alone is not sufficient, though. Rendering happens in float32
on the GPU no matter what the simulation uses, so world positions have to be
rebased near the camera before they are handed over. That is the floating
origin: the simulation keeps true double-precision world coordinates, and the
renderer receives camera-relative offsets small enough for float32 to carry
without visible error.

Proven here numerically before any of it reaches Godot.
"""
import math
import struct

# Distance from the origin at which float32 spacing exceeds this many metres.
JITTER_TOLERANCE_M = 0.001    # 1 mm -- below this, motion reads as solid


def f32(x: float) -> float:
    """Round a Python float through IEEE-754 single precision."""
    return struct.unpack("f", struct.pack("f", x))[0]


def f32_spacing(x: float) -> float:
    """Distance between x and the next representable float32 value.

    This is the real resolution limit at distance x from the origin, and it is
    what determines whether a stationary object appears to shimmer.
    """
    x = abs(f32(x))
    if x == 0.0:
        return struct.unpack("f", struct.pack("I", 1))[0]
    bits = struct.unpack("I", struct.pack("f", x))[0]
    return struct.unpack("f", struct.pack("I", bits + 1))[0] - x


def f32_error_at(x: float) -> float:
    """Absolute error introduced by storing x as float32."""
    return abs(f32(x) - x)


class FloatingOrigin:
    """Rebases world coordinates near the viewer before they reach the GPU.

    The origin is only moved when the viewer has drifted more than `threshold`
    from it, rather than every frame, because each rebase has to be applied to
    every object in the scene. A threshold of a few hundred metres keeps
    rebases rare while holding render-space coordinates small enough that
    float32 spacing stays far below a millimetre.
    """

    def __init__(self, threshold_m: float = 500.0):
        self.threshold = threshold_m
        self.origin = (0.0, 0.0, 0.0)
        self.rebases = 0

    def update(self, viewer_world) -> bool:
        """Move the origin if the viewer has drifted too far. Returns True if
        a rebase happened, which the caller must propagate to the scene."""
        dx = viewer_world[0] - self.origin[0]
        dy = viewer_world[1] - self.origin[1]
        dz = viewer_world[2] - self.origin[2]
        if math.sqrt(dx * dx + dy * dy + dz * dz) <= self.threshold:
            return False
        self.origin = tuple(viewer_world)
        self.rebases += 1
        return True

    def to_render(self, world):
        """World (double) -> render space (small, safe to narrow to float32)."""
        return (world[0] - self.origin[0],
                world[1] - self.origin[1],
                world[2] - self.origin[2])

    def to_world(self, render):
        return (render[0] + self.origin[0],
                render[1] + self.origin[1],
                render[2] + self.origin[2])

    def render_error(self, world) -> float:
        """Positional error this point would suffer once narrowed to float32."""
        r = self.to_render(world)
        return math.sqrt(sum(f32_error_at(c) ** 2 for c in r))


def safe_radius(tolerance_m: float = JITTER_TOLERANCE_M) -> float:
    """Largest distance from the origin at which float32 spacing stays under
    `tolerance_m`. Beyond this, a floating origin is mandatory rather than an
    optimisation."""
    lo, hi = 1.0, 1e9
    for _ in range(200):
        mid = (lo + hi) / 2
        if f32_spacing(mid) < tolerance_m:
            lo = mid
        else:
            hi = mid
    return lo
