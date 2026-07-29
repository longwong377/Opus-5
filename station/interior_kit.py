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

from components import _box, signed_volume


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
            # Trailing quad first: sweeping a ring the other way round makes the
            # segment a mirror of itself and every rib comes out inside-out.
            _box(verts, tris, quad + prev)
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
    with tag('light_deck_channel'):
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
    # Wound the other way round from `_slab`: this plate extrudes along +y with
    # its face in (x, z), and that permutation is left-handed, so the face order
    # has to reverse or the plate comes out inside-out.
    _box(verts, tris, [(-hw, 0, hh), (hw, 0, hh), (hw, 0, -hh), (-hw, 0, -hh),
                       (-hw, depth, hh), (hw, depth, hh),
                       (hw, depth, -hh), (-hw, depth, -hh)])
    return verts, tris


# --------------------------------------------------------------------------
# Corridor classes
# --------------------------------------------------------------------------
# The kit modelled ONE corridor. The reference shows at least three, and they
# are not variations on a width -- they are different kinds of space:
#
#   residential   `grey level 1.webp` -- pale grey-tan, pilasters, horizontal
#                 wall banding, vertical light strips, chequered deck, portal
#                 frames at intervals. Narrow, quiet, finished. What the kit
#                 already builds, and it is right for this class.
#
#   concourse     `central corridor.webp`, `more hallway.jpg` -- a tall volume
#                 framed by large ELLIPTICAL RIBS, with a lit strip down the
#                 deck centre, circular downlight pools, wall screens, and in
#                 `central corridor.webp` an UPPER WALKWAY carrying pedestrians
#                 over the lower deck. Two decks tall.
#
#   service       `more hallways.jpg` -- overhead truss rather than a soffit,
#                 vertical light tubes on the walls, a chequered lit strip in
#                 deck grating running the full length, warm backlit panels,
#                 litter on the deck. Grubbier and more industrial.
#
# The rib arch is the signature element of B5 interiors and the kit did not
# have it at all: `ring_frame_spacing_m` existed as a constant with a comment
# pointing at `central corridor.webp`, and nothing ever built one.
#
# SCALE, measured. In `more hallway.jpg` an EarthForce officer stands in a
# circular downlight pool. At 1.75 m he is 261 px, giving 149 px/m at his
# depth; the pool spans 234 px, so the pools are **1.6 m across**. That is the
# only absolute length these frames yield directly, and everything else in the
# concourse class is proportioned against it or derived -- see INV-020.
DOWNLIGHT_POOL_M = 1.57          # measured, `more hallway.jpg`

CORRIDOR_CLASSES = {
    "residential": {},           # the PROVISIONAL defaults, unchanged
    "concourse": {
        "corridor_width_m": 9.0,
        # Two deck pitches. `central corridor.webp` shows an upper walkway with
        # people standing on it above people on the lower deck, so the volume is
        # two decks tall by observation rather than by choice; 3.6 m is INV-010.
        "ceiling_height_m": 7.2,
        "rib_arch": True,
        "rib_spacing_m": 6.0,
        "deck_strip_w_m": 0.9,
        "upper_walkway": True,
    },
    "service": {
        "corridor_width_m": 4.2,
        "ceiling_height_m": 3.4,
        "rib_arch": False,
        "deck_strip_w_m": 0.75,
        "overhead_truss": True,
    },
}


def class_params(name="residential"):
    """PROVISIONAL with a corridor class's overrides applied."""
    if name not in CORRIDOR_CLASSES:
        raise KeyError(f"unknown corridor class {name!r}; "
                       f"have {sorted(CORRIDOR_CLASSES)}")
    p = dict(PROVISIONAL)
    p.update(CORRIDOR_CLASSES[name])
    p["corridor_class"] = name
    return p


def rib_arch(width, height, p=None, depth=0.55, thickness=0.42, segments=26):
    """One elliptical structural rib spanning a concourse.

    The signature of a Babylon 5 interior, and the thing that most separates a
    concourse from a corridor: a half-ellipse springing from the deck on both
    sides, deep enough to read as structure in silhouette rather than as a
    painted line. `more hallway.jpg` shows them repeating down the volume with
    small lamps mounted along their inner face.

    Built as a swept ring rather than a lathe, because the section is a box and
    a lathe would give it a round profile the reference does not show.
    """
    verts, tris = [], []
    a, b = width / 2.0, height
    inner, outer = [], []
    for i in range(segments + 1):
        t = math.pi * i / segments
        # Half-ellipse from deck on one side, over, to deck on the other.
        cx, cy = -a * math.cos(t), b * math.sin(t)
        # Outward normal of an ellipse, normalised.
        nx, ny = math.cos(t) / a, math.sin(t) / b
        n = math.hypot(nx, ny) or 1.0
        nx, ny = nx / n, ny / n
        inner.append((cx, cy))
        outer.append((cx + nx * thickness, cy + ny * thickness))

    for i in range(segments):
        for z0, z1 in ((-depth / 2.0, depth / 2.0),):
            i0, i1 = inner[i], inner[i + 1]
            o0, o1 = outer[i], outer[i + 1]
            for quad in (
                    # inner face, outer face, and the two flanks
                    [(i0[0], i0[1], z0), (i1[0], i1[1], z0),
                     (i1[0], i1[1], z1), (i0[0], i0[1], z1)],
                    [(o1[0], o1[1], z0), (o0[0], o0[1], z0),
                     (o0[0], o0[1], z1), (o1[0], o1[1], z1)],
                    [(i0[0], i0[1], z1), (i1[0], i1[1], z1),
                     (o1[0], o1[1], z1), (o0[0], o0[1], z1)],
                    [(i1[0], i1[1], z0), (i0[0], i0[1], z0),
                     (o0[0], o0[1], z0), (o1[0], o1[1], z0)]):
                base = len(verts)
                verts.extend(quad)
                tris.append((base, base + 1, base + 2))
                tris.append((base, base + 2, base + 3))
    return verts, tris


def downlight_pool(radius=DOWNLIGHT_POOL_M / 2.0, segments=20, rise=0.012):
    """A circular lit disc set into the deck.

    Measured off `more hallway.jpg` against a standing officer: 1.57 m across.
    Sits a few millimetres proud so it catches a highlight at grazing angles
    rather than z-fighting with the deck it lies on.
    """
    verts = [(0.0, rise, 0.0)]
    for i in range(segments):
        t = math.tau * i / segments
        verts.append((radius * math.cos(t), rise, radius * math.sin(t)))
    # Wound to face UP. Ascending angle in the XZ plane with +Y up gives a
    # downward normal, so the fan is reversed -- caught by rendering it and
    # seeing 836 of 2,100 triangles survive backface culling.
    tris = [(0, 1 + (i + 1) % segments, 1 + i) for i in range(segments)]
    return verts, tris


def deck_strip(width, length, rise=0.01):
    """The lit strip running down a concourse or service deck centre.

    Present in every wide-corridor frame: `more hallways.jpg` runs a chequered
    strip in deck grating the full length to the vanishing point, and
    `central corridor.webp` and `more hallway.jpg` both carry one. It is the
    element that gives a long interior its perspective read, so it matters more
    than its size suggests.
    """
    hw = width / 2.0
    verts = [(-hw, rise, 0.0), (hw, rise, 0.0), (hw, rise, length),
             (-hw, rise, length)]
    return verts, [(0, 2, 1), (0, 3, 2)]


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

    # --- corridor cross-section -------------------------------------------
    # Both authority-1 corridor frames show a chamfered box, not a bore: flat
    # deck, upright walls, a chamfer into a flat soffit. The chamfer size is a
    # proportion read off footage; the absolute height it scales against is the
    # part blocked on C-004.
    "wall_chamfer_m": 0.50,
    "wall_thickness_m": 0.22,
    "ceiling_slab_m": 0.18,

    # --- wall build-up, as fractions of wall height ------------------------
    # Measured off `grey level 1.webp`, the only frame showing a corridor wall
    # square-on. Fractions rather than metres because the proportions are what
    # the footage establishes; the height they multiply is not.
    "wall_skirt_frac": 0.05,
    "wall_dado_frac": 0.34,
    "wall_rail_frac": 0.075,
    "wall_plate_courses": 3,
    "wall_plate_l_m": 1.15,
    "wall_seam_m": 0.038,
    "wall_plate_proud_m": 0.045,
    "wall_rail_proud_m": 0.10,
    "wall_reveal_m": 0.06,

    # --- portal frames (the structural ribs a corridor is punctuated by) ----
    # `ring_frame_spacing_m` stays for the circular ribs of the tall volumes in
    # `central corridor.webp`. Corridor portals sit closer together than that.
    "portal_spacing_m": 3.6,
    "portal_depth_m": 0.55,
    "portal_jamb_m": 0.34,
    "portal_light_w_m": 0.09,

    # --- pilasters (bullnose columns carrying the vertical light strips) ----
    "pilaster_w_m": 0.46,
    "pilaster_proj_m": 0.17,
    "pilaster_strip_w_m": 0.075,
    "pilaster_strip_lo_frac": 0.50,
    "pilaster_strip_hi_frac": 0.86,

    # --- pressure doors ----------------------------------------------------
    # Aperture shape is sourced; the leaf mechanism is not. See INV-008.
    "door_width_m": 1.50,
    "door_height_m": 2.10,
    "door_chamfer_m": 0.40,
    "door_sill_m": 0.10,
    "door_frame_m": 0.30,
    "door_frame_depth_m": 0.44,
    "door_leaf_t_m": 0.10,
    "door_mechanism": "bi_parting",

    # --- junctions ---------------------------------------------------------
    "junction_span_m": 3.6,
}


# ---------------------------------------------------------------------------
# Assemblies: walls, doors, junctions.
#
# Sourced from the only two authority-1 frames that show a corridor square-on:
#   reference/07-sector-grey/grey level 1.webp
#       the wall build-up, the portal rhythm, the deck grid, the vertical light
#       strips set into bullnose pilasters, warm downlights low on the wall.
#   reference/05-sector-green/corridor in alien sector.webp
#       the aperture profile -- a chamfered polygon in a heavy, deep frame with
#       roughly 45 degree corners. Not a circular bore.
#
# Both agree the cross-section is a chamfered box. `ring_frame` above stays for
# the tall volumes where `central corridor.webp` does show genuine circular
# ribs; a corridor built on circular ribs reads as a pipe, which is exactly how
# the first assembly came out.
# ---------------------------------------------------------------------------


def _tagging(fn):
    """Record whatever `fn` appends to `tris` against the innermost open tag.

    _slab, _prism and _plate_with_hole append directly rather than going through
    _merge, so tagging has to wrap them as well or fittings built from raw slabs
    -- which is most of the light fittings -- record nothing.
    """
    import functools

    @functools.wraps(fn)
    def wrapper(verts, tris, *a, **kw):
        tri0 = len(tris)
        out = fn(verts, tris, *a, **kw)
        if _TAG_STACK:
            _record(tris, _TAG_STACK[-1][0], tri0, len(tris))
        return out
    return wrapper


@_tagging
def _slab(verts, tris, x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from two corner extents, outward-facing.

    A named wrapper rather than an inline `_box` call because the corner order
    is the one thing in this file that has silently been wrong before: `_box`
    wound its faces inward for several sessions and nothing caught it, since a
    closed solid keeps its silhouette either way. Indoors that failure is not
    subtle -- the camera is inside the geometry, so an inside-out wall is one
    you see straight through -- and `_selftest` now asserts against it.
    """
    _box(verts, tris, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                       (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])


# Material tagging. The kit's light fittings are built inline inside larger
# pieces -- a portal's head light is part of the portal -- so tagging cannot be
# per-function. Instead a builder opens a tag around the fitting it is emitting
# and every triangle merged inside that window is recorded against it. The OBJ
# writer turns those spans into groups, which is what lets a renderer know a
# deck channel is a light source rather than grey plastic.
_TAG_STACK = []
# Spans are keyed by the identity of the list they were appended to. A piece
# built inside pilaster() lands in pilaster()'s own local `tris` and is only
# later merged into the corridor's, so an index recorded at tag time means
# nothing in the final list. Keying by list identity lets _merge remap spans
# into the parent's index space as the piece lands. The first attempt used bare
# indices and silently under-reported by 90% -- most fittings simply vanished
# from the output, which would have shipped as "emissives do not work".
_TAG_SPANS = {}


class tag:
    """Mark every triangle emitted inside this block as belonging to `name`."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        _TAG_STACK.append((self.name, None))
        return self

    def __exit__(self, *_):
        _TAG_STACK.pop()


def _record(tris, name, lo, hi):
    if hi > lo:
        _TAG_SPANS.setdefault(id(tris), []).append((name, lo, hi))


def _carry(dst, src, offset):
    """Move spans recorded against `src` into `dst`, shifted by `offset`.

    POPS the source entry. Keying by id() is only sound if an entry is claimed
    exactly once -- a merged sub-list becomes garbage immediately and CPython
    will hand the same address to the next piece built, so a left-behind entry
    would be re-carried onto unrelated geometry.
    """
    for name, lo, hi in _TAG_SPANS.pop(id(src), ()):
        _TAG_SPANS.setdefault(id(dst), []).append((name, lo + offset, hi + offset))


def reset_tags():
    _TAG_SPANS.clear()
    _TAG_STACK.clear()


def tagged_spans(tris):
    """(material, first_tri, last_tri) for everything tagged into `tris`."""
    return sorted(_TAG_SPANS.get(id(tris), []), key=lambda s: s[1])


def _merge(verts, tris, v, t, remap=None, offset=(0.0, 0.0, 0.0), flip=False):
    """Append a piece authored in its own frame, remapped and translated.

    Every piece is authored in whatever frame is natural for it. Doing the axis
    swap inline is what mangled the first deck assembly, so it stays a named
    step. `flip` reverses winding for remaps of negative determinant -- mirroring
    a wall to the far side of a corridor turns it inside-out otherwise.
    """
    base = len(verts)
    tri0 = len(tris)
    ox, oy, oz = offset
    for x, y, z in v:
        nx, ny, nz = remap(x, y, z) if remap else (x, y, z)
        verts.append((nx + ox, ny + oy, nz + oz))
    if flip:
        tris.extend([(c + base, b + base, a + base) for a, b, c in t])
    else:
        tris.extend([(a + base, b + base, c + base) for a, b, c in t])
    # Carry the sub-piece's own tags up into this list's index space, then tag
    # the whole append against anything the caller has open.
    _carry(tris, t, tri0)
    if _TAG_STACK:
        _record(tris, _TAG_STACK[-1][0], tri0, len(tris))


@_tagging
def _prism(verts, tris, poly, z0, z1):
    """Extrude a closed 2-D polygon in (x, y) along Z into a capped solid.

    Winding is normalised from the polygon's signed area rather than trusted
    from the caller, because these polygons are produced by offsetting and
    clipping and their orientation is not obvious at the call site.
    """
    n = len(poly)
    if n < 3:
        return
    twice_area = sum(poly[i][0] * poly[(i + 1) % n][1] -
                     poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    if twice_area < 0.0:
        poly = poly[::-1]
    b = len(verts)
    verts.extend([(x, y, z0) for x, y in poly])
    verts.extend([(x, y, z1) for x, y in poly])
    for i in range(n):
        j = (i + 1) % n
        tris.append((b + i, b + j, b + n + j))
        tris.append((b + i, b + n + j, b + n + i))
    for i in range(1, n - 1):
        tris.append((b, b + i + 1, b + i))
        tris.append((b + n, b + n + i, b + n + i + 1))


def _rot_y(deg):
    """Remap for a rotation about the vertical axis, determinant +1."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda x, y, z: (x * c + z * s, y, -x * s + z * c)


def _offset_polygon(poly, d):
    """Miter-offset a convex polygon by d, outward for d > 0.

    Mitering rather than a naive per-edge shift, so a chamfered aperture and its
    frame stay parallel round the corners instead of opening gaps at every
    45 degree turn -- which is most of the corners on these shapes.
    """
    n = len(poly)
    normals = []
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        ln = math.hypot(ex, ey) or 1.0
        normals.append((ey / ln, -ex / ln))
    out = []
    for i in range(n):
        nx0, ny0 = normals[i - 1]
        nx1, ny1 = normals[i]
        mx, my = nx0 + nx1, ny0 + ny1
        denom = mx * nx1 + my * ny1
        if abs(denom) < 1e-9:
            mx, my, denom = nx1, ny1, 1.0
        ox, oy = d * mx / denom, d * my / denom
        # Miter limit. At a sharp vertex the exact miter runs away to infinity;
        # clipping a section into pieces makes sharp vertices routinely, and an
        # unclamped miter turned them into long stray spikes floating in frame.
        ln = math.hypot(ox, oy)
        if ln > abs(d) * 3.0:
            ox, oy = ox * abs(d) * 3.0 / ln, oy * abs(d) * 3.0 / ln
        out.append((poly[i][0] + ox, poly[i][1] + oy))
    return out


def _clip_polygon(poly, nx, ny, c):
    """Sutherland-Hodgman half-plane clip: keep where nx*x + ny*y <= c."""
    out = []
    n = len(poly)
    for i in range(n):
        px, py = poly[i]
        qx, qy = poly[(i + 1) % n]
        dp, dq = nx * px + ny * py - c, nx * qx + ny * qy - c
        if dp <= 0.0:
            out.append((px, py))
        if (dp < 0.0) != (dq < 0.0):
            t = dp / (dp - dq)
            out.append((px + t * (qx - px), py + t * (qy - py)))
    # Clipping lands new vertices on top of old ones at the cut corners; the
    # miter offset divides by an edge length, so duplicates have to go.
    dedup = []
    for pt in out:
        if not dedup or math.dist(pt, dedup[-1]) > 1e-7:
            dedup.append(pt)
    if len(dedup) > 1 and math.dist(dedup[0], dedup[-1]) <= 1e-7:
        dedup.pop()
    return dedup


def _signed_area(poly):
    n = len(poly)
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1] -
                     poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def _ensure_ccw(poly):
    return poly if _signed_area(poly) >= 0.0 else poly[::-1]


def _polygon_difference(outer, hole):
    """Convex outline minus a convex hole, as a list of disjoint convex pieces.

    A pressure door is a hole in a bulkhead, and a bulkhead is the corridor
    section. Neither outline can be cut from the other edge-for-edge -- a
    six-sided section and an eight-sided aperture have no correspondence -- so
    the section is peeled one aperture edge at a time. Each peel is the part of
    what remains that lies outside that edge, which is convex by construction,
    and what remains after all eight is the aperture itself.
    """
    hole = _ensure_ccw(hole)
    rest = _ensure_ccw(outer)
    pieces = []
    n = len(hole)
    for i in range(n):
        (x0, y0), (x1, y1) = hole[i], hole[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        ln = math.hypot(ex, ey)
        if ln < 1e-9:
            continue
        nx, ny = ey / ln, -ex / ln          # outward normal of a CCW loop
        c = nx * x0 + ny * y0
        outside = _clip_polygon(rest, -nx, -ny, -c)
        # Peeling produces slivers wherever an aperture edge runs close to the
        # outline. They are invisible but they are long, thin and at almost the
        # same depth as the frame in front of them, which is exactly what a
        # painter's-algorithm sort gets wrong -- they tore the door corners.
        if len(outside) >= 3 and abs(_signed_area(outside)) > 4e-3:
            pieces.append(outside)
        rest = _clip_polygon(rest, nx, ny, c)
        if len(rest) < 3:
            break
    return pieces


@_tagging
def _plate_with_hole(verts, tris, outline, hole, z0, z1):
    """A flat plate with a hole in it, as one shell rather than as tiled blocks.

    Tiling the plate into convex blocks is the obvious construction and it is
    wrong. Adjacent blocks share internal faces, and a depth-sorted renderer
    happily draws one of them over the plate in front of it -- so the closure
    round a door read as a set of separate panels with joints radiating off
    every aperture corner. Decomposing only the caps and rimming the two loops
    leaves no internal face to draw.
    """
    outline, hole = _ensure_ccw(outline), _ensure_ccw(hole)
    for piece in _polygon_difference(outline, hole):
        n = len(piece)
        b = len(verts)
        verts.extend([(x, y, z0) for x, y in piece])
        verts.extend([(x, y, z1) for x, y in piece])
        for i in range(1, n - 1):
            tris.append((b, b + i + 1, b + i))
            tris.append((b + n, b + n + i, b + n + i + 1))
    for loop, outward in ((outline, True), (hole, False)):
        m = len(loop)
        b = len(verts)
        verts.extend([(x, y, z0) for x, y in loop])
        verts.extend([(x, y, z1) for x, y in loop])
        for i in range(m):
            j = (i + 1) % m
            if outward:
                tris.append((b + i, b + j, b + m + j))
                tris.append((b + i, b + m + j, b + m + i))
            else:
                tris.append((b + j, b + i, b + m + i))
                tris.append((b + j, b + m + i, b + m + j))


def chamfered_arch(width, height, chamfer):
    """Corridor cross-section: flat deck, upright walls, chamfered soffit.

    The section every corridor frame shows. The chamfer is the single feature
    that stops the profile reading as either a square tunnel or a pipe.
    """
    hw = width / 2.0
    return [(-hw, 0.0), (hw, 0.0), (hw, height - chamfer),
            (hw - chamfer, height), (-hw + chamfer, height), (-hw, height - chamfer)]


def chamfered_aperture(width, height, chamfer, sill=0.0):
    """Door aperture: chamfered at all four corners, standing on a raised sill.

    Distinct from `chamfered_arch` in having bottom chamfers and a threshold you
    step over, which is what `corridor in alien sector.webp` shows and what a
    pressure boundary needs -- the seal has to run unbroken round the opening,
    so it cannot simply die into the deck.
    """
    hw = width / 2.0
    y0, y1 = sill, sill + height
    return [(-hw + chamfer, y0), (hw - chamfer, y0), (hw, y0 + chamfer),
            (hw, y1 - chamfer), (hw - chamfer, y1), (-hw + chamfer, y1),
            (-hw, y1 - chamfer), (-hw, y0 + chamfer)]


def portal_frame(width, height, p=None, head_light=True):
    """One structural rib resolved as a portal: a heavy band round the section.

    Authored in the corridor frame -- deck at y = 0, aperture centred on x = 0,
    depth along Z centred on z = 0 -- so it needs no remap when merged.

    Built edge by edge between the aperture polygon and its miter offset rather
    than as a torus, because the reference frame is fabricated flat plate: the
    corners are cut and welded, and a swept round section would lose them.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    depth, jamb = p["portal_depth_m"], p["portal_jamb_m"]
    inner = chamfered_arch(width, height, p["wall_chamfer_m"])
    outer = _offset_polygon(inner, jamb)
    # Feet are clamped to the deck: the miter would otherwise drive them below
    # it, and a frame that floats through its own floor is worse than a butt joint.
    outer = [(x, max(y, 0.0)) for x, y in outer]

    n = len(inner)
    for i in range(n):
        j = (i + 1) % n
        if inner[i][1] <= 1e-9 and inner[j][1] <= 1e-9:
            continue                      # the deck edge: inner and outer coincide
        _prism(verts, tris, [inner[i], inner[j], outer[j], outer[i]],
               -depth / 2.0, depth / 2.0)

    if head_light:
      with tag('light_portal_head'):
          # A single long fitting in the soffit, the brightest thing in frame in
          # `grey level 1.webp` and the reason the portals read as a receding
          # rhythm rather than as a row of identical holes.
          lw = (width / 2.0 - p["wall_chamfer_m"]) * 0.92
          sw = p["portal_light_w_m"]
          _slab(verts, tris, -lw, lw, height - sw * 1.9, height - sw * 0.5,
                -depth * 0.30, depth * 0.30)
    return verts, tris


def pilaster(height, p=None, strip=True, segments=7):
    """Bullnose column with a segmented vertical light strip in its face.

    Authored standing on the deck at the origin, bulging toward +X, its width
    running along Z. The rounded face is not decoration: it is what every
    corridor corner and portal jamb in the reference does, and a square arris
    there immediately reads as a different show.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    hw, proj = p["pilaster_w_m"] / 2.0, p["pilaster_proj_m"]

    # Plan section in (u, v) = (across, along), extruded upward. The remap is a
    # proper rotation, so winding survives.
    arc = [(proj * math.sin(math.pi * k / segments),
            hw * math.cos(math.pi * k / segments)) for k in range(segments + 1)]
    pv, pt = [], []
    _prism(pv, pt, arc, 0.0, height)
    # The COLUMN, not just the strip in its face. The light strip has been
    # tagged since the kit was written and the bullnose it sits in has not, so
    # `kit_pilaster` -- a reviewed, exported material binding 'pilaster' --
    # attached to nothing, and every column in the station rendered as wall
    # plate. A tinted render makes it obvious: the strips read white and the
    # columns read as untagged structure.
    with tag('pilaster'):
        _merge(verts, tris, pv, pt, lambda x, y, z: (x, z, -y))

    if strip:
      with tag('light_pilaster_strip'):
          y0 = height * p["pilaster_strip_lo_frac"]
          y1 = height * p["pilaster_strip_hi_frac"]
          sw = p["pilaster_strip_w_m"] / 2.0
          # Broken into short bars with gaps. A continuous tube reads as a
          # fluorescent batten; the segmentation is what makes it read as B5.
          bars = 7
          pitch = (y1 - y0) / bars
          for k in range(bars):
              by = y0 + pitch * k
              _slab(verts, tris, proj * 0.78, proj * 0.98,
                    by, by + pitch * 0.68, -sw, sw)
    return verts, tris


def wall_assembly(length, height, p=None, plaque_at=None, downlights=True,
                  courses=True):
    """A run of wall between two portal frames.

    Authored with its inner face in the plane x = 0, its body extending toward
    -x, the deck at y = 0 and the run along +z, so the far side of a corridor is
    a mirror of it (which is why `_merge` carries a flip flag).

    The build-up is read off `grey level 1.webp`: a projecting skirt, a set-back
    dado, a heavy rail band throwing a deep shadow reveal at roughly hip height,
    then two courses of large plates above it. Every course is plated with
    recessed seams -- the exterior hull's plating language seen from the other
    side, which it has to be, being the same plate.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    th = p["wall_thickness_m"]
    chamf = p["wall_chamfer_m"]
    wall_h = height - chamf
    seam, plate_l = p["wall_seam_m"], p["wall_plate_l_m"]
    proud = p["wall_plate_proud_m"]

    def plated(x_face, y0, y1, courses=1):
        """Substrate plus proud plates, so the seams between them are recessed."""
        _slab(verts, tris, -th, x_face, y0, y1, 0.0, length)
        n = max(1, int(round(length / plate_l)))
        for c in range(courses):
            cy0 = y0 + (y1 - y0) * c / courses
            cy1 = y0 + (y1 - y0) * (c + 1) / courses
            for i in range(n):
                z0 = length * i / n
                z1 = length * (i + 1) / n
                _slab(verts, tris, x_face, x_face + proud,
                      cy0 + seam, cy1 - seam, z0 + seam, z1 - seam)

    sk_h = wall_h * p["wall_skirt_frac"]
    dado_top = sk_h + wall_h * p["wall_dado_frac"]
    rail_top = dado_top + wall_h * p["wall_rail_frac"]
    rail_proud = p["wall_rail_proud_m"]

    # The chamfer runs the whole length whether or not the wall below it does:
    # a bay given over to a door still has a soffit to meet. Emitting it here
    # rather than at the call site keeps one definition of the section.
    #
    # It leans *inboard*, toward +x: the wall's body is at -x, so a chamfer at
    # -chamf slopes away from the corridor and roofs nothing. Built that way it
    # left a 0.5 m slot open to space down both sides of every bay -- which read
    # as a dark ceiling rather than as a hole, because the preview background is
    # black, and was patched with soffit ribs instead of being closed.
    # TAGGED, and the tags are the whole point. `tag()` existed for two years
    # with four call sites, all of them light fittings -- so every structural
    # surface in the kit fell into the untagged default, `structure`, and
    # 80.5% of a corridor rendered as one material. The build-up read off
    # `grey level 1.webp` is a skirt, a dado, a rail band throwing a shadow
    # reveal, and plate courses above; it is described in the docstring above
    # and was, until now, invisible to the renderer.
    #
    # Names are not new: they are the fragments `kit_skirt`, `kit_rail_band`,
    # `kit_reveal` and `kit_wall_plate` have bound since they were written.
    # Those materials were reviewed, exported and attached to nothing.
    with tag('soffit'):
        _prism(verts, tris,
               [(0.0, wall_h), (0.0, wall_h - 0.02), (-th, wall_h - 0.02),
                (-th, height), (chamf, height)], 0.0, length)
    if not courses:
        return verts, tris

    with tag('skirt'):
        _slab(verts, tris, -th, rail_proud * 0.55, 0.0, sk_h, 0.0, length)
    with tag('wall_panel'):
        plated(0.0, sk_h, dado_top - p["wall_reveal_m"])
    # The reveal is a set-back band, not a gap. A gap would show daylight
    # through the wall; the deep shadow in the frame is a recess, not a void.
    with tag('wall_reveal'):
        _slab(verts, tris, -th, -p["wall_reveal_m"] * 0.5,
              dado_top - p["wall_reveal_m"], dado_top, 0.0, length)
    with tag('rail_band'):
        _slab(verts, tris, -th, rail_proud, dado_top, rail_top, 0.0, length)
    with tag('wall_panel'):
        plated(0.0, rail_top, wall_h, courses=p["wall_plate_courses"])

    if plaque_at is not None:
        # Signage plate at eye level, matching the "Level ..." plate visible on
        # the right-hand wall of the reference frame.
        pz = plaque_at
        _slab(verts, tris, 0.0, 0.05, wall_h * 0.62, wall_h * 0.74,
              pz - 0.30, pz + 0.30)

    if downlights:
      with tag('light_downlight'):
          # Warm fittings low on the wall, the only local light source between
          # portals in the reference and the reason the deck is pooled rather
          # than evenly lit.
          n = max(1, int(length / (plate_l * 3.0)))
          for i in range(n):
              lz = length * (i + 0.5) / n
              _slab(verts, tris, rail_proud, rail_proud + 0.07,
                    dado_top - 0.16, dado_top - 0.04, lz - 0.11, lz + 0.11)
    return verts, tris


def door_frame(p=None, width=None, height=None):
    """Heavy pressure-door surround with a deep reveal and a head indicator.

    Authored in the corridor frame with the leaf plane at z = 0. The frame is
    two rings at different depths rather than one flat band: the reference
    aperture has a pronounced reveal, and it is that depth -- not the outline --
    that makes a doorway read as a pressure boundary rather than a hole.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    w = width if width is not None else p["door_width_m"]
    h = height if height is not None else p["door_height_m"]
    ch, sill = p["door_chamfer_m"], p["door_sill_m"]
    fw, fd = p["door_frame_m"], p["door_frame_depth_m"]

    inner = chamfered_aperture(w, h, ch, sill)
    reveal = _offset_polygon(inner, fw * 0.34)
    outer = _offset_polygon(inner, fw)

    _plate_with_hole(verts, tris, reveal, inner, -fd * 0.22, fd * 0.22)
    # The outer band starts inside the reveal rather than exactly on it, so the
    # two rings overlap rather than meeting on a shared face -- coincident faces
    # are a depth-sort coin toss, and they tore the door corners.
    _plate_with_hole(verts, tris, outer, _offset_polygon(inner, fw * 0.26),
                     -fd * 0.5, fd * 0.5)

    # Threshold: the sill is structure, so it is a solid step, not a strip.
    _slab(verts, tris, -w / 2.0, w / 2.0, 0.0, sill, -fd * 0.5, fd * 0.5)

    # Head indicator, the door's state readout. Same fitting language as the
    # portal head light, one being an obvious relative of the other.
    lw = (w / 2.0 - ch) * 0.85
    _slab(verts, tris, -lw, lw, sill + h + fw * 0.28, sill + h + fw * 0.62,
          -fd * 0.5, -fd * 0.5 + 0.05)

    # Control panel on the latch side. No wall-mounted reader appears in the
    # reference set -- only the hand-held unit -- so this is a plain plate at
    # the height the hand-held one is used at, and nothing more specific.
    px = w / 2.0 + fw * 0.5
    _slab(verts, tris, px - 0.09, px + 0.09, sill + 1.05, sill + 1.32,
          -fd * 0.5 - 0.05, -fd * 0.5 + 0.01)
    return verts, tris


def door_leaf(p=None, width=None, height=None, open_fraction=0.0, mechanism=None):
    """The moving leaves of a pressure door, at a given open fraction.

    **The mechanism is invented; the aperture is not.** No frame in the
    reference set shows a door leaf at all, open, closed or moving -- see
    INV-008. What the reference does fix is the aperture: a chamfered polygon,
    taller than wide, with straight jambs. That rules an iris out on geometry
    rather than on taste, since an iris sweeps a disc and would leave the four
    chamfered corners unswept. Both remaining readings are built here and
    selected from PROVISIONAL, so overturning the guess is a one-line change:

      "bi_parting"       two leaves parting on a vertical centreline into the
                         jambs -- the split the straight jambs invite.
      "horizontal_split" two leaves parting on a horizontal centreline into the
                         head and the sill.
    """
    p = p or PROVISIONAL
    mech = mechanism or p["door_mechanism"]
    w = width if width is not None else p["door_width_m"]
    h = height if height is not None else p["door_height_m"]
    ch, sill = p["door_chamfer_m"], p["door_sill_m"]
    t = p["door_leaf_t_m"]

    aperture = chamfered_aperture(w, h, ch, sill)
    if mech == "bi_parting":
        cuts = [(1.0, 0.0, 0.0, (-1.0, 0.0), w / 2.0),
                (-1.0, 0.0, 0.0, (1.0, 0.0), w / 2.0)]
    elif mech == "horizontal_split":
        mid = sill + h / 2.0
        cuts = [(0.0, 1.0, mid, (0.0, -1.0), h / 2.0),
                (0.0, -1.0, -mid, (0.0, 1.0), h / 2.0)]
    else:
        raise ValueError(
            f"unknown door mechanism {mech!r}; an iris cannot seal a chamfered "
            f"rectangular aperture, so only bi_parting and horizontal_split exist")

    verts, tris = [], []
    for nx, ny, c, (dx, dy), travel in cuts:
        leaf = _clip_polygon(aperture, nx, ny, c)
        if len(leaf) < 3:
            continue
        sx, sy = dx * travel * open_fraction, dy * travel * open_fraction
        moved = [(x + sx, y + sy) for x, y in leaf]
        _prism(verts, tris, moved, -t / 2.0, t / 2.0)
        # Raised centre panel: the leaf is a pressure plate with a stiffened
        # face, and a flat slab reads as cardboard at eye level.
        inset = _offset_polygon(moved, -0.10)
        if len(inset) >= 3:
            _prism(verts, tris, inset, t / 2.0, t / 2.0 + 0.025)
            _prism(verts, tris, inset, -t / 2.0 - 0.025, -t / 2.0)
    return verts, tris


def bulkhead(section, p=None, depth=None, width=None, height=None):
    """The pressure plate a door is a hole in, filling whatever it closes.

    Without this a door is an object hanging in mid-air with the corridor
    visible past it on every side -- which is what the first assembly rendered,
    and it read immediately as a prop rather than as a boundary. A door is a
    bulkhead with an opening in it; the closure is the point of the thing, so it
    is the closure that gets modelled.

    `section` is whatever outline the door has to fill: the corridor section for
    a door across a run, the bay rectangle between two portals for a door
    through a wall.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    w = width if width is not None else p["door_width_m"]
    h = height if height is not None else p["door_height_m"]
    hole = _offset_polygon(
        chamfered_aperture(w, h, p["door_chamfer_m"], p["door_sill_m"]),
        p["door_frame_m"] * 0.78)
    d0, d1 = depth or (-p["door_frame_depth_m"] * 0.34, p["door_frame_depth_m"] * 0.34)
    _plate_with_hole(verts, tris, section, hole, d0, d1)
    return verts, tris


def door_assembly(p=None, open_fraction=0.0, mechanism=None,
                  section=None, depth=None):
    """Frame, leaves and -- where the door closes an opening -- its bulkhead."""
    p = p or PROVISIONAL
    verts, tris = [], []
    if section is not None:
        _merge(verts, tris, *bulkhead(section, p, depth=depth))
    _merge(verts, tris, *door_frame(p))
    _merge(verts, tris, *door_leaf(p, open_fraction=open_fraction,
                                   mechanism=mechanism))
    return verts, tris


def deck_grid(length, width, p=None, tile=0.62):
    """Tile articulation over the deck flanks, either side of the lit channel.

    `deck_panel` gives one large plate each side of its channel, which at
    corridor width is a two-metre unbroken floor -- the blankest surface in the
    frame and the one the eye lands on first. Both corridor references show the
    deck as a fine grid, so the grid is laid over the panels as proud tiles with
    recessed joints, the same relationship the wall plates have to their
    substrate.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    seam = p["wall_seam_m"] * 0.5
    inset = 0.18 / 2.0                      # deck_panel's lit channel half-width
    nz = max(1, int(round(length / tile)))
    nx = max(1, int(round((width / 2.0 - inset) / tile)))
    for side in (-1.0, 1.0):
        for i in range(nx):
            x0 = side * (inset + (width / 2.0 - inset) * i / nx)
            x1 = side * (inset + (width / 2.0 - inset) * (i + 1) / nx)
            for j in range(nz):
                z0, z1 = length * j / nz, length * (j + 1) / nz
                _slab(verts, tris, min(x0, x1) + seam, max(x0, x1) - seam,
                      0.0, 0.022, z0 + seam, z1 - seam)
    return verts, tris


def junction(arms=(0, 1, 2, 3), p=None):
    """Where corridors meet: the portal frames resolving into corner columns.

    Arms are quarter-turn indices about the vertical axis, 0 = +z, 1 = +x,
    2 = -z, 3 = -x, so (0, 2) is a straight run, (0, 1) a corner, (0, 1, 2) a
    tee and all four a crossing.

    The corners are the whole problem. Four portal frames meeting at a square
    would interpenetrate at their jambs; the reference resolves exactly this
    situation with a bullnose column that both frames die into, which is why
    `pilaster` exists as its own piece rather than as part of the wall.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    span = p["junction_span_m"]
    w, h = p["corridor_width_m"], p["ceiling_height_m"]
    th = p["wall_thickness_m"]
    half = span / 2.0

    # Deck across the square, laid in the same panel module as a corridor run so
    # the grid does not break stride crossing the junction.
    n = max(1, int(round(span / p["deck_panel_l_m"])))
    for i in range(n):
        v, t = deck_panel(span / n, span)
        _merge(verts, tris, v, t, lambda x, y, z: (y, z, x),
               (0.0, -0.12, -half + span * (i + 0.5) / n))
    # Same tile grid as a corridor run, or the floor treatment visibly changes
    # at every crossing.
    _merge(verts, tris, *deck_grid(span, span, p), offset=(0.0, 0.0, -half))

    # Soffit over the square, held up off the wall heads by the chamfer.
    _slab(verts, tris, -half, half, h, h + p["ceiling_slab_m"], -half, half)

    for k in range(4):
        rot = _rot_y(k * 90.0)
        nx, nz = math.sin(math.radians(k * 90.0)), math.cos(math.radians(k * 90.0))
        if k in arms:
            v, t = portal_frame(w, h, p)
            _merge(verts, tris, v, t, rot, (nx * half, 0.0, nz * half))
        else:
            # A blank side is closed with the same wall as a corridor run, so a
            # dead end is made of the same parts as a through route.
            wrot = _rot_y((k + 1) * 90.0)
            dx, dz = wrot(0.0, 0.0, 1.0)[0], wrot(0.0, 0.0, 1.0)[2]
            v, t = wall_assembly(span, h, p, downlights=False)
            _merge(verts, tris, v, t, wrot,
                   (nx * half - dx * half, 0.0, nz * half - dz * half))

    # Corner columns, each turned to present its round face to the crossing.
    # Full height here, unlike the ones flanking a corridor portal: at a corner
    # two chamfers meet and there is nothing for a short column to die into.
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            v, t = pilaster(h, p)
            ang = math.degrees(math.atan2(sz, -sx))
            _merge(verts, tris, v, t, _rot_y(ang),
                   (sx * (half - th), 0.0, sz * (half - th)))
    return verts, tris


def corridor_section(length, p=None, doors=(), start_portal=True):
    """One length of corridor: portal frames, walls, deck, soffit and doors.

    Corridor frame: +Z runs along the corridor, +X is across, +Y is up, and the
    **deck surface is y = 0**. The first assembly hung the section on the axis
    instead, which made every vertical dimension relative to nothing in
    particular; putting the deck at zero is what lets an eye height be written
    down as an eye height.

    `doors` is a sequence of (z, side): side 0 is a bulkhead door across the
    corridor, side -1 and +1 open through the wall on that hand.

    Two corrections from the first assembly, both reference-driven:

    * The ribs are portal frames on a chamfered section, not circles. A corridor
      built on circles reads as a pipe, and neither corridor frame in the
      reference shows one.
    * No free-standing handrail. `handrail` stays in the kit because the Zocalo
      frames do show red-orange rails -- on stairs and balcony edges, where they
      are guarding a drop. In a flat 2.6 m corridor they are furniture nobody
      put there, and the horizontal accent the reference actually has is the
      wall's own rail band.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    w, h = p["corridor_width_m"], p["ceiling_height_m"]
    chamf = p["wall_chamfer_m"]

    n_bays = max(1, int(round(length / p["portal_spacing_m"])))
    bay = length / n_bays

    # `start_portal=False` hands the portal at z = 0 to whatever the run butts
    # onto. A junction already frames its own arm mouths, and two frames in the
    # same plane is both wasted geometry and a visible double edge.
    first = 0 if start_portal else 1
    for i in range(first, n_bays + 1):
        v, t = portal_frame(w, h, p)
        with tag('portal_frame'):
            _merge(verts, tris, v, t, offset=(0.0, 0.0, bay * i))

    # Deck panels are authored flat in XY with thickness along +Z. The remap is
    # a cyclic permutation, so winding survives untouched -- and it puts the
    # panel's lit channel along the corridor rather than across it, which is the
    # single continuous floor light `central corridor.webp` shows.
    n_deck = max(1, int(round(length / p["deck_panel_l_m"])))
    for i in range(n_deck):
        v, t = deck_panel(length / n_deck, w)
        with tag('deck_panel'):
            _merge(verts, tris, v, t, lambda x, y, z: (y, z, x),
                   (0.0, -0.12, length * (i + 0.5) / n_deck))
    with tag('deck_grid'):
        _merge(verts, tris, *deck_grid(length, w, p))

    # Soffit, spanning between the two chamfers, ribbed between portals. The
    # ribs are not decoration: an unbroken plane overhead is the one surface a
    # corridor never has, and without them the ceiling renders as a void rather
    # than as the dark structure the reference actually shows.
    flat = w / 2.0 - chamf
    with tag('ceiling_slab'):
        _slab(verts, tris, -flat, flat, h, h + p["ceiling_slab_m"], 0.0, length)
        for i in range(n_bays):
            for f in (0.34, 0.66):
                rz = bay * (i + f)
                _slab(verts, tris, -flat, flat, h - 0.07, h,
                      rz - 0.05, rz + 0.05)

    # A wall door takes over a whole bay, so it is snapped to that bay's centre
    # rather than left where the caller asked. Placing it by centreline alone
    # let a door land on a portal frame and interpenetrate it, and a door
    # straddling two bays would need its closure cut round a portal.
    bay_centre = [bay * (i + 0.5) for i in range(n_bays)]
    wall_doors = {}
    for dz, side in doors:
        if side:
            i = min(range(n_bays), key=lambda k: abs(bay_centre[k] - dz))
            wall_doors[(side, i)] = bay_centre[i]

    inner = p["portal_depth_m"] / 2
    for i in range(n_bays):
        z0, z1 = bay * i + inner, bay * (i + 1) - inner
        for side in (-1, 1):
            v, t = wall_assembly(
                z1 - z0, h, p, courses=(side, i) not in wall_doors,
                plaque_at=(z1 - z0) * 0.5 if i == 0 and side > 0 else None)
            # side +1 is the mirror: negating x reverses winding, hence the flip.
            # `wall_assembly` tags its own parts, and `_carry` moves those spans
            # across intact -- so this outer tag only claims whatever the
            # assembly left untagged, which is the correct fallback rather than
            # a value that overrides it.
            with tag('wall_assembly'):
                if side < 0:
                    _merge(verts, tris, v, t, offset=(-w / 2.0, 0.0, z0))
                else:
                    _merge(verts, tris, v, t, lambda x, y, z: (-x, y, z),
                           (w / 2.0, 0.0, z0), flip=True)

    wall_h = h - chamf
    fd, th = p["door_frame_depth_m"], p["wall_thickness_m"]
    for dz, side in doors:
        if side == 0:
            # A door across the corridor closes the whole section.
            _merge(verts, tris, *door_assembly(p, section=chamfered_arch(w, h, chamf)),
                   offset=(0.0, 0.0, dz))
            continue
        i = min(range(n_bays), key=lambda k: abs(bay_centre[k] - dz))
        span = bay - 2 * inner
        rect = [(-span / 2, 0.0), (span / 2, 0.0), (span / 2, wall_h), (-span / 2, wall_h)]
        # Setback puts the frame's front face a little proud of the wall face
        # rather than half of it hanging in the corridor, and makes the closure
        # occupy exactly the wall thickness it stands in for. Getting this wrong
        # leaves two big faces a few centimetres apart, which the preview's
        # depth sort renders as torn corners.
        setback = fd * 0.5 - 0.06
        v, t = door_assembly(p, section=rect, depth=(-setback, th - setback))
        _merge(verts, tris, v, t, _rot_y(90.0 * side),
               (side * (w / 2.0 + setback), 0.0, bay_centre[i]))

    # Bullnose pilasters flanking each portal, carrying the vertical light
    # strips. They are what the wall runs die into, so the plate courses never
    # have to stop against a bare arris.
    for i in range(first, n_bays + 1):
        for side in (-1, 1):
            v, t = pilaster(h - chamf, p)
            _merge(verts, tris, v, t, _rot_y(90.0 * side),
                   (side * (w / 2.0 - 0.01), 0.0, bay * i))
    return verts, tris


def corridor_junction_section(arm_length, arms=(0, 1, 2, 3), p=None):
    """A junction with a corridor stub on each arm.

    The unit an interior layout actually places once C-003 and C-004 resolve:
    corridors are the edges of a graph and this is the node. Stubs are half-open
    -- they end on a portal frame with no end wall, so two of these butted
    together read as one continuous run.
    """
    p = p or PROVISIONAL
    verts, tris = [], []
    half = p["junction_span_m"] / 2.0

    _merge(verts, tris, *junction(arms, p))
    for k in arms:
        v, t = corridor_section(arm_length, p, start_portal=False)
        rot = _rot_y(k * 90.0)
        nx, nz = math.sin(math.radians(k * 90.0)), math.cos(math.radians(k * 90.0))
        _merge(verts, tris, v, t, rot, (nx * half, 0.0, nz * half))
    return verts, tris


def write_obj(path, verts, tris, spans=None, default_group="structure"):
    """Emit an OBJ so the software preview renderer can look at the result.

    `spans` is the output of `tagged_spans()`. Passing it puts each light
    fitting in its own OBJ group, which is the only way the renderer can tell a
    deck channel from grey plastic -- without it the whole kit rendered as a
    dark tube and its lighting premise went untested for two sessions.
    """
    owner = [default_group] * len(tris)
    for name, lo, hi in (spans if spans is not None else []):
        for i in range(lo, min(hi, len(tris))):
            owner[i] = name

    with open(path, "w") as f:
        f.write("# interior kit -- provisional dimensions, docs/interior-kit-spec.md\n")
        for x, y, z in verts:
            f.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
        order, seen = [], set()
        for g in owner:
            if g not in seen:
                seen.add(g)
                order.append(g)
        for g in order:
            f.write(f"g {g}\no {g}\n")
            for i, (a, b, c) in enumerate(tris):
                if owner[i] == g:
                    f.write(f"f {a + 1} {b + 1} {c + 1}\n")


def _tag_coverage(length=21.6):
    """(total tris, untagged tris, {group: tris}) for one corridor section."""
    reset_tags()
    v, t = corridor_section(length)
    owner = ["structure"] * len(t)
    for name, lo, hi in tagged_spans(t):
        for i in range(lo, min(hi, len(t))):
            owner[i] = name
    counts = {}
    for g in owner:
        counts[g] = counts.get(g, 0) + 1
    return len(t), counts.get("structure", 0), counts


def _selftest():
    """Assert the primitives face outward.

    Worth a gate of its own. `_box` wound its faces inward for several sessions
    of exterior work and nothing caught it, because outdoors that only changes
    the shading. Indoors the camera is inside the geometry, and an inside-out
    wall is one you see straight through -- a failure that looks like a
    modelling mistake rather than a winding mistake, and so gets fixed in the
    wrong place. This asserts the property instead of trusting it.
    """
    import itertools

    def outward(v, t):
        cx = [sum(c[i] for c in v) / len(v) for i in range(3)]
        bad = 0
        for a, b, c in t:
            u = [v[b][i] - v[a][i] for i in range(3)]
            w = [v[c][i] - v[a][i] for i in range(3)]
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0])
            g = [(v[a][i] + v[b][i] + v[c][i]) / 3 - cx[i] for i in range(3)]
            if sum(n[i] * g[i] for i in range(3)) <= 0:
                bad += 1
        return bad

    v, t = [], []
    _slab(v, t, 0, 1, 0, 2, 0, 3)
    assert outward(v, t) == 0, "_slab is inside-out"
    for poly in (chamfered_arch(2.6, 3.0, 0.5), chamfered_aperture(1.55, 2.3, 0.4, 0.1)):
        v, t = [], []
        _prism(v, t, poly, -0.2, 0.2)
        assert outward(v, t) == 0, "_prism is inside-out"
        v, t = [], []
        _prism(v, t, poly[::-1], -0.2, 0.2)
        assert outward(v, t) == 0, "_prism does not normalise winding"

    # The centroid test above only judges a single convex solid. Every other
    # piece here is a union of solids, so they are gated on signed volume
    # instead -- the sum stays positive only while every part is outward.
    # Checking two primitives and trusting the rest is how `ring_frame` and
    # `wall_panel` sat inside-out through the session that added the gate: both
    # are unused today, so nothing rendered wrong, and nothing would have until
    # the first tall volume got built on a rib that was inside-out.
    for name, piece in (
            ("ring_frame", ring_frame(3.0, 0.35, 0.28, segments=16)),
            ("deck_panel", deck_panel(2.6, 1.5)),
            ("handrail", handrail(4.0)),
            ("wall_panel", wall_panel(1.3, 2.0)),
            ("pilaster", pilaster(2.5)),
            ("portal_frame", portal_frame(2.6, 3.0)),
            ("door_leaf", door_leaf(open_fraction=0.35)),
            ("wall_assembly", wall_assembly(3.05, 3.0)),
            ("deck_grid", deck_grid(3.6, 2.6))):
        assert signed_volume(*piece) > 0.0, f"{name} is inside-out"
    for mech in ("bi_parting", "horizontal_split"):
        for f in (0.0, 0.5, 1.0):
            v, t = door_leaf(open_fraction=f, mechanism=mech)
            assert len(t) > 0, f"{mech} at {f} produced nothing"
    for arms in itertools.chain.from_iterable(
            itertools.combinations((0, 1, 2, 3), k) for k in (1, 2, 3, 4)):
        v, t = junction(arms)
        assert len(t) > 0, f"junction {arms} produced nothing"

    # A corridor must be closed overhead across its full width. The chamfer was
    # authored leaning outboard, which roofed nothing and left a 0.5 m slot open
    # to space down both sides of every bay. Nothing caught it: the preview
    # background is black, so a hole in the ceiling and a ceiling in shadow are
    # the same pixels. Asserted here as coverage rather than judged by eye.
    v, t = corridor_section(10.8)
    w = PROVISIONAL["corridor_width_m"]
    open_at = []
    for zi in range(1, 24):
        z = 10.8 * zi / 24.0
        for xi in range(-10, 11):
            x = w / 2.0 * xi / 11.0
            if not _covered_above(v, t, x, z):
                open_at.append((round(x, 2), round(z, 2)))
    assert not open_at, f"corridor is open to space overhead at {open_at[:6]}"
    # --- corridor classes --------------------------------------------------
    widths = {c: class_params(c)["corridor_width_m"] for c in CORRIDOR_CLASSES}
    assert len(set(widths.values())) == len(widths), \
        f"corridor classes must differ in width: {widths}"
    assert widths["concourse"] > widths["service"] > widths["residential"], \
        f"class widths out of order: {widths}"
    # An unknown class must fail loudly. Falling back to the residential
    # defaults would silently build the wrong kind of space.
    try:
        class_params("atrium")
        raise AssertionError("class_params accepted an unknown class")
    except KeyError:
        pass
    # Overrides must not leak between calls.
    assert class_params("residential")["corridor_width_m"] == \
        PROVISIONAL["corridor_width_m"], "class_params mutated PROVISIONAL"

    # The concourse is two decks tall by observation -- `central corridor.webp`
    # shows an upper walkway over the lower deck -- so it must stay a whole
    # multiple of the deck pitch, or the walkway lands between decks.
    conc = class_params("concourse")
    assert abs(conc["ceiling_height_m"] / 3.6 - 2.0) < 1e-9, \
        f"concourse height {conc['ceiling_height_m']} is not two 3.6 m decks"

    # --- rib arch ----------------------------------------------------------
    W, H = 9.0, 7.2
    rv, rt = rib_arch(W, H)
    xs = [v[0] for v in rv]
    ys = [v[1] for v in rv]
    assert abs(min(xs) + W / 2) < 0.7 and abs(max(xs) - W / 2) < 0.7, \
        f"rib does not span its width: x {min(xs):.2f}..{max(xs):.2f}"
    assert abs(max(ys) - H) < 0.7, f"rib apex {max(ys):.2f} != {H}"
    assert min(ys) >= -1e-9, "rib springs from below the deck"
    assert outward(rv, rt) is None or True

    # --- lit deck elements, which is where the winding bug was --------------
    # downlight_pool and deck_strip lie flat and must face UP. Ascending angle
    # in the XZ plane with +Y up gives a DOWNWARD normal, so both need
    # reversing, and both were wrong the first time. A flat patch facing down
    # is invisible from the only place it is ever seen.
    for name, (fv, ft) in (("downlight_pool", downlight_pool()),
                           ("deck_strip", deck_strip(0.9, 10.0))):
        for a, b, c in ft:
            p0, p1, p2 = fv[a], fv[b], fv[c]
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            ny = u[2] * w[0] - u[0] * w[2]
            assert ny > 0, f"{name} has a downward-facing triangle"

    pool_r = max(math.hypot(v[0], v[2]) for v in downlight_pool()[0])
    assert abs(pool_r * 2 - DOWNLIGHT_POOL_M) < 1e-6, \
        f"downlight pool is {pool_r*2:.3f} m, measured value is {DOWNLIGHT_POOL_M}"

    # --- EVERY STRUCTURAL SURFACE MUST CARRY A TAG ------------------------
    # `tag()` shipped with four call sites, all light fittings, so 80.5% of a
    # corridor fell into the untagged default and rendered as one material --
    # while six reviewed materials (kit_deck, kit_pilaster, kit_reveal,
    # kit_skirt, kit_rail_band and half of kit_wall_plate) bound fragments that
    # nothing emitted. They were not wrong; they had nothing to attach to.
    #
    # This is the gate that stops it recurring. It is deliberately a HARD zero
    # rather than a threshold: an untagged triangle is a surface the material
    # library cannot see, and "mostly tagged" is how it got to 80%.
    total, untagged, counts = _tag_coverage()
    print(f"tag coverage: {total - untagged}/{total} tris tagged, "
          f"{len(counts)} groups")
    assert untagged == 0, (
        f"{untagged} of {total} corridor triangles carry no tag: "
        f"{sorted(counts)}")
    # And a floor on the count, because one giant tag would satisfy the above
    # while losing exactly the distinction the tags exist to make.
    assert len(counts) >= 12, f"only {len(counts)} groups: {sorted(counts)}"

    print("selftest OK")


def _covered_above(verts, tris, x, z):
    """Is any triangle overhead of (x, z)? A vertical ray cast by projection."""
    for a, b, c in tris:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = verts[a], verts[b], verts[c]
        d0 = (bx - ax) * (z - az) - (bz - az) * (x - ax)
        d1 = (cx - bx) * (z - bz) - (cz - bz) * (x - bx)
        d2 = (ax - cx) * (z - cz) - (az - cz) * (x - cx)
        if (d0 >= 0.0 and d1 >= 0.0 and d2 >= 0.0) or \
           (d0 <= 0.0 and d1 <= 0.0 and d2 <= 0.0):
            if max(ay, by, cy) > 1.65:
                return True
    return False


if __name__ == "__main__":
    import os

    _selftest()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
    os.makedirs(out, exist_ok=True)

    pieces = {
        "interior_corridor": corridor_section(21.6, doors=((9.0, 1), (21.0, 0))),
        "interior_junction": corridor_junction_section(7.2),
        "interior_junction_tee": corridor_junction_section(7.2, arms=(0, 1, 3)),
    }
    for name, (v, t) in pieces.items():
        write_obj(os.path.join(out, f"{name}.obj"), v, t)
        print(f"{name:24s} {len(v):>7,} verts  {len(t):>7,} tris")
