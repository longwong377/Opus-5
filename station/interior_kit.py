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
    "wall_seam_m": 0.055,
    "wall_plate_proud_m": 0.035,
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
    # Aperture shape is sourced; the leaf mechanism is not. See INV-005.
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


def _slab(verts, tris, x0, x1, y0, y1, z0, z1):
    """Axis-aligned box with outward-facing normals.

    `_box` treats its first quad as wound the other way, so a box given corners
    in the obvious order comes out inside-out. That is invisible on an exterior
    silhouette and fatal indoors: the surface the camera needs is the one facing
    back at it, and an inside-out wall is a wall you can see straight through.
    """
    _box(verts, tris, [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0),
                       (x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)])


def _merge(verts, tris, v, t, remap=None, offset=(0.0, 0.0, 0.0), flip=False):
    """Append a piece authored in its own frame, remapped and translated.

    Every piece is authored in whatever frame is natural for it. Doing the axis
    swap inline is what mangled the first deck assembly, so it stays a named
    step. `flip` reverses winding for remaps of negative determinant -- mirroring
    a wall to the far side of a corridor turns it inside-out otherwise.
    """
    base = len(verts)
    ox, oy, oz = offset
    for x, y, z in v:
        nx, ny, nz = remap(x, y, z) if remap else (x, y, z)
        verts.append((nx + ox, ny + oy, nz + oz))
    if flip:
        tris.extend([(c + base, b + base, a + base) for a, b, c in t])
    else:
        tris.extend([(a + base, b + base, c + base) for a, b, c in t])


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
        out.append((poly[i][0] + d * mx / denom, poly[i][1] + d * my / denom))
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


def _ensure_ccw(poly):
    n = len(poly)
    twice_area = sum(poly[i][0] * poly[(i + 1) % n][1] -
                     poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    return poly if twice_area >= 0.0 else poly[::-1]


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
        if len(outside) >= 3:
            pieces.append(outside)
        rest = _clip_polygon(rest, nx, ny, c)
        if len(rest) < 3:
            break
    return pieces


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
    _merge(verts, tris, pv, pt, lambda x, y, z: (x, z, -y))

    if strip:
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
    _prism(verts, tris,
           [(0.0, wall_h), (0.0, wall_h - 0.02), (-th, wall_h - 0.02),
            (-th, height), (-chamf, height)], 0.0, length)
    if not courses:
        return verts, tris

    _slab(verts, tris, -th, rail_proud * 0.55, 0.0, sk_h, 0.0, length)
    plated(0.0, sk_h, dado_top - p["wall_reveal_m"])
    # The reveal is a set-back band, not a gap. A gap would show daylight
    # through the wall; the deep shadow in the frame is a recess, not a void.
    _slab(verts, tris, -th, -p["wall_reveal_m"] * 0.5,
          dado_top - p["wall_reveal_m"], dado_top, 0.0, length)
    _slab(verts, tris, -th, rail_proud, dado_top, rail_top, 0.0, length)
    plated(0.0, rail_top, wall_h, courses=p["wall_plate_courses"])

    if plaque_at is not None:
        # Signage plate at eye level, matching the "Level ..." plate visible on
        # the right-hand wall of the reference frame.
        pz = plaque_at
        _slab(verts, tris, 0.0, 0.05, wall_h * 0.62, wall_h * 0.74,
              pz - 0.30, pz + 0.30)

    if downlights:
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

    def band(a, b, z0, z1):
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            _prism(verts, tris, [a[i], a[j], b[j], b[i]], z0, z1)

    band(inner, reveal, -fd * 0.22, fd * 0.22)     # the reveal, set back
    band(reveal, outer, -fd * 0.5, fd * 0.5)       # the outer frame, proud

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
    INV-005. What the reference does fix is the aperture: a chamfered polygon,
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
    for piece in _polygon_difference(section, hole):
        _prism(verts, tris, piece, d0, d1)
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
    chamf, th = p["wall_chamfer_m"], p["wall_thickness_m"]
    half = span / 2.0

    # Deck across the square, laid in the same panel module as a corridor run so
    # the grid does not break stride crossing the junction.
    n = max(1, int(round(span / p["deck_panel_l_m"])))
    for i in range(n):
        v, t = deck_panel(span / n, span)
        _merge(verts, tris, v, t, lambda x, y, z: (y, z, x),
               (0.0, -0.12, -half + span * (i + 0.5) / n))

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
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            v, t = pilaster(h, p)
            ang = math.degrees(math.atan2(sz, -sx))
            _merge(verts, tris, v, t, _rot_y(ang),
                   (sx * (half - th), 0.0, sz * (half - th)))
    return verts, tris


def corridor_section(length, p=None, doors=()):
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

    for i in range(n_bays + 1):
        v, t = portal_frame(w, h, p)
        _merge(verts, tris, v, t, offset=(0.0, 0.0, bay * i))

    # Deck panels are authored flat in XY with thickness along +Z. The remap is
    # a cyclic permutation, so winding survives untouched -- and it puts the
    # panel's lit channel along the corridor rather than across it, which is the
    # single continuous floor light `central corridor.webp` shows.
    n_deck = max(1, int(round(length / p["deck_panel_l_m"])))
    for i in range(n_deck):
        v, t = deck_panel(length / n_deck, w)
        _merge(verts, tris, v, t, lambda x, y, z: (y, z, x),
               (0.0, -0.12, length * (i + 0.5) / n_deck))
    _merge(verts, tris, *deck_grid(length, w, p))

    # Soffit, spanning between the two chamfers, ribbed between portals. The
    # ribs are not decoration: an unbroken plane overhead is the one surface a
    # corridor never has, and without them the ceiling renders as a void rather
    # than as the dark structure the reference actually shows.
    flat = w / 2.0 - chamf
    _slab(verts, tris, -flat, flat, h, h + p["ceiling_slab_m"], 0.0, length)
    for i in range(n_bays):
        for f in (0.34, 0.66):
            rz = bay * (i + f)
            _slab(verts, tris, -flat, flat, h - 0.07, h, rz - 0.05, rz + 0.05)

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
        # Set back so the frame stands a little proud of the wall face rather
        # than half of it hanging in the corridor, and the closure fills the
        # thickness the wall courses would have occupied.
        v, t = door_assembly(p, section=rect, depth=(-0.06, th + 0.10))
        _merge(verts, tris, v, t, _rot_y(90.0 * side),
               (side * (w / 2.0 + 0.16), 0.0, bay_centre[i]))

    # Bullnose pilasters flanking each portal, carrying the vertical light
    # strips. They are what the wall runs die into, so the plate courses never
    # have to stop against a bare arris.
    for i in range(n_bays + 1):
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
        v, t = corridor_section(arm_length, p)
        rot = _rot_y(k * 90.0)
        nx, nz = math.sin(math.radians(k * 90.0)), math.cos(math.radians(k * 90.0))
        _merge(verts, tris, v, t, rot, (nx * half, 0.0, nz * half))
    return verts, tris


def write_obj(path, verts, tris):
    """Emit an OBJ so the software preview renderer can look at the result."""
    with open(path, "w") as f:
        for x, y, z in verts:
            f.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
        for a, b, c in tris:
            f.write(f"f {a + 1} {b + 1} {c + 1}\n")


def _selftest():
    """Assert the primitives face outward.

    Worth a gate of its own: `_box` in components.py takes its corners wound the
    other way, so the natural corner order produces solids that are inside-out.
    Outdoors that only changes the shading. Indoors the camera is inside the
    geometry, and an inside-out wall is one you see straight through -- which is
    a failure that looks like a modelling mistake, not a winding mistake.
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
    for mech in ("bi_parting", "horizontal_split"):
        for f in (0.0, 0.5, 1.0):
            v, t = door_leaf(open_fraction=f, mechanism=mech)
            assert len(t) > 0, f"{mech} at {f} produced nothing"
    for arms in itertools.chain.from_iterable(
            itertools.combinations((0, 1, 2, 3), k) for k in (1, 2, 3, 4)):
        v, t = junction(arms)
        assert len(t) > 0, f"junction {arms} produced nothing"
    print("selftest OK")


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
