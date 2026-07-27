#!/usr/bin/env python3
"""Generate the interior kit: the modular pieces most interior surface is made of.

Driven by docs/interior-kit-spec.md, which is sourced from authority-1 footage
and deliberately takes no position on level topology. That is what makes this
buildable while C-003 and C-004 are still blocking: these are *pieces*, not a
*layout*. Nothing here assumes where a level sits or how sectors nest.

The defining motif is that the hull's circular ring frames are exposed rather
than clad -- they arch overhead and frame views down corridors, and they are
the single most identifiable thing about a Babylon 5 interior.

Dimensions that would require level topology (corridor width, ceiling height,
deck spacing) are PARAMETERS with placeholder defaults, not constants. They are
marked provisional so that resolving C-004 changes one call rather than a
hundred hard-coded numbers.
"""
import math

from components import _box


def ring_frame(radius, depth, thickness, segments=48, arc=math.tau, start=0.0):
    """One exposed structural rib: a partial torus of rectangular section.

    Built as a swept box rather than a smooth torus because the reference shows
    a fabricated frame with flat faces, not a machined ring.
    """
    verts, tris = [], []
    ri, ro = radius - thickness / 2, radius + thickness / 2
    hd = depth / 2
    prev = None
    for i in range(segments + 1):
        a = start + arc * i / segments
        c, s = math.cos(a), math.sin(a)
        quad = [(ri * c, ri * s, -hd), (ro * c, ro * s, -hd),
                (ro * c, ro * s, hd), (ri * c, ri * s, hd)]
        if prev is not None:
            _box(verts, tris, prev + quad)
        prev = quad
    return verts, tris


def deck_panel(width, length, thickness=0.12, lit_inset=0.18):
    """A floor plate with a recessed channel for the illuminated strip.

    The reference shows floor lighting as inset panels that are themselves the
    light source. Modelling the recess means the emissive material has somewhere
    to live instead of being painted onto a flat plane.
    """
    verts, tris = [], []
    hw, hl, t = width / 2, length / 2, thickness
    inset = lit_inset / 2
    # Two plates flanking a central channel.
    for sign in (1, -1):
        y0 = sign * inset
        y1 = sign * hl
        lo, hi = (min(y0, y1), max(y0, y1))
        _box(verts, tris, [
            (-hw, lo, 0), (hw, lo, 0), (hw, hi, 0), (-hw, hi, 0),
            (-hw, lo, t), (hw, lo, t), (hw, hi, t), (-hw, hi, t)])
    # Channel floor, dropped so the strip sits recessed.
    _box(verts, tris, [
        (-hw, -inset, 0), (hw, -inset, 0), (hw, inset, 0), (-hw, inset, 0),
        (-hw, -inset, t * 0.45), (hw, -inset, t * 0.45),
        (hw, inset, t * 0.45), (-hw, inset, t * 0.45)])
    return verts, tris


def handrail(length, height=1.05, post_spacing=1.8, rail_r=0.045, post_r=0.035):
    """Red-orange handrail: top rail plus posts.

    The dominant warm accent in every interior frame, so it carries more visual
    weight than its size suggests and is worth building properly.
    """
    verts, tris = [], []

    def bar(x0, x1, y0, y1, z0, z1):
        _box(verts, tris, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                           (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])

    bar(0, length, -rail_r, rail_r, height - rail_r, height + rail_r)
    bar(0, length, -rail_r * 0.7, rail_r * 0.7,
        height * 0.55 - rail_r * 0.6, height * 0.55 + rail_r * 0.6)
    n = max(2, int(length / post_spacing) + 1)
    for i in range(n):
        x = length * i / (n - 1)
        bar(x - post_r, x + post_r, -post_r, post_r, 0.0, height)
    return verts, tris


def wall_panel(width, height, depth=0.09, seam=0.035):
    """A single wall plate with a recessed seam border.

    Matches the exterior plating language deliberately -- it is the same hull
    seen from the other side, and interior and exterior surfacing disagreeing
    would be exactly the inconsistency the single-schema approach exists to
    prevent.
    """
    verts, tris = [], []
    hw, hh = width / 2 - seam, height / 2 - seam
    _box(verts, tris, [(-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh),
                       (-hw, depth, -hh), (hw, depth, -hh),
                       (hw, depth, hh), (-hw, depth, hh)])
    return verts, tris


# Provisional dimensions. NOT canon -- see docs/interior-kit-spec.md section 6.
# These exist so the kit can be built and looked at; resolving C-004 should
# change these values, not the code that uses them.
PROVISIONAL = {
    "corridor_width_m": 2.6,
    "ceiling_height_m": 3.0,
    "ring_frame_spacing_m": 4.5,
    "ring_frame_depth_m": 0.35,
    "ring_frame_thickness_m": 0.28,
    "wall_panel_w_m": 1.3,
    "deck_panel_w_m": 2.6,
    "deck_panel_l_m": 1.5,
}


def corridor_section(length, p=None):
    """One length of corridor: ring frames, walls, deck, handrails.

    Assembled purely from the pieces above at provisional dimensions, so the
    kit can be rendered and judged before the topology that would fix those
    dimensions is known.
    """
    p = p or PROVISIONAL
    verts, tris = [], []

    # Corridor frame: +Z runs along the corridor, +Y is up, +X is across.
    # Each piece is authored in its own natural frame, so merging takes an
    # explicit remap rather than inline tuple juggling -- the first attempt did
    # the swapping inline and silently produced a mangled deck.
    def merge(v, t, remap, offset=(0.0, 0.0, 0.0)):
        base = len(verts)
        ox, oy, oz = offset
        for x, y, z in v:
            nx, ny, nz = remap(x, y, z)
            verts.append((nx + ox, ny + oy, nz + oz))
        tris.extend([(a + base, b + base, c + base) for a, b, c in t])

    ident = lambda x, y, z: (x, y, z)

    # Ring frames are authored in XY with thickness along Z -- already correct.
    r = p["corridor_width_m"] / 2 + 0.45
    n_frames = max(2, int(length / p["ring_frame_spacing_m"]) + 1)
    for i in range(n_frames):
        v, t = ring_frame(r, p["ring_frame_depth_m"], p["ring_frame_thickness_m"])
        merge(v, t, ident, (0.0, 0.0, length * i / (n_frames - 1)))

    # Deck panels are authored flat in XY with thickness along +Z. Lay them
    # down: panel X stays across, panel Y becomes corridor Z, panel Z becomes up.
    floor_y = -p["corridor_width_m"] / 2 - 0.15
    n_deck = max(1, int(length / p["deck_panel_l_m"]))
    for i in range(n_deck):
        v, t = deck_panel(p["deck_panel_w_m"], p["deck_panel_l_m"])
        merge(v, t, lambda x, y, z: (x, z, y),
              (0.0, floor_y, p["deck_panel_l_m"] * (i + 0.5)))

    # Handrails are authored along +X with height in +Z. Turn them to run along
    # the corridor: rail X becomes corridor Z, rail Z becomes up.
    for side in (-1, 1):
        v, t = handrail(length)
        merge(v, t, lambda x, y, z: (y, z, x),
              (side * (p["corridor_width_m"] / 2 - 0.12), floor_y, 0.0))

    return verts, tris
