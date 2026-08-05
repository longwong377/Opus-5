#!/usr/bin/env python3
"""The Zocalo: the station's social centre, as a parametric bay that repeats.

Sourced from `reference/10-interiors-generic-kit/more zocalo.png` (authority 1,
1440x1080, the best Zocalo frame in the set; the same file is also filed at
`reference/04-sector-red/more zocalo.png`), cross-checked against
`reference/04-sector-red/zocalo.webp` (authority 1, a different camera on the
same set) and against `canon/00-MASTER.md` section 3.1, which puts the Zocalo in
the commercial sector.

WHAT THE FRAME ESTABLISHES, and it is more than it looks

The frame is a perspective shot with no scale bar, so the honest move is to
solve the camera from the frame itself and then measure everything in metres.
Four image measurements do it, because they are two pairs, each pair at one
depth, and each pair holding one point on the deck plane and one at 0.75 m:

    deck at the left chair's near foot        y = 1057 px
    that chair's top rail (0.75 m)            y =  650 px
    deck under the mid-ground tables          y =  610 px
    a mid-ground table top (0.75 m)           y =  468 px

Equating the two (height / distance) ratios fixes the horizon at y = 370.5 px,
and from there the camera's eye height is 1.265 m -- a SEATED eye height, which
is a result and not an assumption, and which independently confirms that this is
ordinary human furniture. The ellipse aspect of the foreground table top
(58 / 367 px) then gives its distance, 3.26 m, and hence the focal length,
2517 px: a 32 degree horizontal field of view, an unremarkable television lens.

Every furniture dimension below falls out of that solve, and three of them are
cross-checks that could have failed and did not:

    chair frame tube                0.025 m   -- a real furniture tube size
    chair overall width             0.48 m    -- a real cafe chair width
    the chrome shaker on the table  0.093 m   -- a real cocktail shaker

Nothing in the derivation knew any of those three sizes. A solve that lands on
all of them is not a fit to noise. `REF_*` below carries it so a later session
can measure anything else in the same frame without redoing the work.

WHAT IS DELIBERATELY NOT TAKEN FROM THE FRAME

The same solve puts the upper gallery's walking surface **2.6 to 2.8 m** above
the lower deck. That is a stage, not a station: it is below the interior kit's
own 3.0 m corridor ceiling, and it contradicts INV-010's 3.6 m deck pitch that
every other volume in this project is built on. The gallery here is built at
3.6 m, which makes the Zocalo exactly two decks tall and agrees with
`class_params("concourse")["ceiling_height_m"] = 7.2`, itself derived by
observation from a different frame. The measurement is recorded rather than
used.

STRUCTURE

One bay is 21.6 m wide by 10.8 m long by 7.2 m tall -- 6 x 3 x 2 deck pitches,
so the bay closes on the station's own structural module and repeats without a
seam. The central 12.6 m is open the full height; the 4.5 m either side carries
an upper gallery at 3.6 m over a colonnade of vendor stalls. The elliptical rib
springs from the lower deck at the gallery's edge line and arches over the well.

The "5" roundel on the chair backs is a MATERIAL, not geometry: one group name,
one decal, no glyph triangles. Same for the Zocalo wordmark, the deck's tile
pattern and chevron band, and the 22 mm service port on the table pedestal.

RUN IT

    python3 station/zocalo.py              # self-test
    python3 station/zocalo.py --budget     # triangle budget report
    python3 station/zocalo.py --obj out.obj 3
"""
import hashlib
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import budget                                          # noqa: E402
import interior as it                                  # noqa: E402
import interior_kit as kit                             # noqa: E402
from components import _box, signed_volume             # noqa: E402
import bespoke as _bsp                                 # noqa: E402


# ---------------------------------------------------------------------------
# The camera solve. Everything measured off `more zocalo.png` goes through it.
# ---------------------------------------------------------------------------
REF_IMAGE = "reference/10-interiors-generic-kit/more zocalo.png"
REF_W_PX, REF_H_PX = 1440, 1080
REF_HORIZON_PX = 370.5      # solved: two 0.75 m features at two depths
REF_EYE_M = 1.265           # solved from the same pair -- a seated eye height
REF_FOCAL_PX = 2517.0       # from the table-top ellipse aspect, 58/367 px


def ref_scale_px_per_m(y_px):
    """Pixels per metre for a feature standing on the deck at image row `y_px`.

    A deck point at row y is at horizontal distance d = f * eye / (y - horizon),
    and a length there subtends f / d pixels. Both fall out of the pinhole
    model, and this is the function every figure in `MEASURED` was read through.
    """
    if y_px <= REF_HORIZON_PX:
        raise ValueError(f"row {y_px} is at or above the horizon, so it is not "
                         f"a point on the deck and has no scale")
    return (y_px - REF_HORIZON_PX) / REF_EYE_M


def ref_distance_m(y_px):
    """Horizontal distance from the reference camera to a deck point at `y_px`."""
    return REF_FOCAL_PX / ref_scale_px_per_m(y_px)


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
# MEASURED: read off `more zocalo.png` through the solve above. The comment is
# the pixel figure, so the arithmetic is checkable without re-measuring.
MEASURED = {
    # Furniture, at 543 px/m (the left-hand chair, 4.64 m out).
    "chair_w_m": 0.48,             # 260 px of top rail, partly occluded
    "chair_back_h_m": 0.276,       # 150 px from the seat line to the rail
    "chair_tube_d_m": 0.025,       # 12.5 px -- cross-check, a real tube size
    # Furniture, at 772 px/m (the foreground table, 3.26 m out).
    "table_top_d_m": 0.475,        # 367 px across the pale disc
    "table_top_t_m": 0.023,        # 18 px of metal edge band
    "table_col_d_m": 0.177,        # 137 px of pale pedestal below the top
    "table_port_d_m": 0.022,       # 17 px dark circular service port
    "shaker_d_m": 0.093,           # 72 px -- cross-check, a real shaker
    # Signage, at 119 px/m (the gallery, ~21 m out).
    "neon_w_m": 1.9,               # 227 px of sign face
    "neon_h_m": 0.84,              # 100 px
    # The gallery, at the same depth. RECORDED AND NOT USED -- see the module
    # docstring. This is the set's height, not a station deck pitch.
    "set_gallery_y_m": (2.6, 2.8),
    # Deck. Two joint families rectify to 0.52 m and 0.40 m; the frame is too
    # noisy to separate them, so this is a range and TILE_M is chosen inside it
    # on the structural module.
    "deck_tile_m_range": (0.40, 0.52),
    # The arch. A circle fitted to five points on the bright rib gives radius
    # 645 px about (-8, 335) px; at the depth its springing implies, that is a
    # 12.7 m span rising 6.6 m. It is why the well is 12.6 m and not the
    # concourse class's 9.0 m corridor width.
    "arch_span_m": 12.7,
}

# The two anchors the task supplies. The solve above reproduces both, which is
# why they are quoted here as confirmations rather than as free parameters.
TABLE_H_M = 0.75
CHAIR_SEAT_H_M = 0.45

DECK_PITCH_M = it.DECK_PITCH_M          # 3.6, INV-010

BAY_WIDTH_M = 6 * DECK_PITCH_M          # 21.6
BAY_LENGTH_M = 3 * DECK_PITCH_M         # 10.8
WELL_WIDTH_M = 3.5 * DECK_PITCH_M       # 12.6 -- measured arch span 12.7 m
GALLERY_DEPTH_M = (BAY_WIDTH_M - WELL_WIDTH_M) / 2.0     # 4.5
GALLERY_Y_M = DECK_PITCH_M              # 3.6, not the set's measured 2.6-2.8
RIB_SPACING_M = BAY_LENGTH_M / 2.0      # 5.4 -- two ribs a bay
TILE_M = DECK_PITCH_M / 8.0             # 0.45, inside the measured range

# Abutting solids are given this much overlap instead of an exact shared face.
# Two boxes that meet exactly share an EDGE, and a shared edge is used by four
# triangles once vertices are welded -- a non-manifold edge that renders
# perfectly and is a modelling error everywhere else. Overlapping by 2 mm
# inside opaque structure is invisible and leaves every shell manifold.
WELD_M = 0.002

# The deck's own body and the soffit's. Both were zero, which is the same
# statement as "this surface has a boundary" -- see `tiled_deck` and the
# soffit call in `zocalo_bay`. 0.14 m matches the end-cap slabs `zocalo_run`
# already lays at the two ends of a capped run, so the deck does not change
# thickness where it meets its own bulkhead. INV-171.
DECK_SLAB_M = 0.14
SOFFIT_T_M = 0.14

# The provisional table. A better frame or a resolved C-004 should change values
# here, never the code that reads them.
PROVISIONAL = {
    "bay_width_m": BAY_WIDTH_M,
    "bay_length_m": BAY_LENGTH_M,
    "well_width_m": WELL_WIDTH_M,
    "gallery_depth_m": GALLERY_DEPTH_M,
    "gallery_y_m": GALLERY_Y_M,
    "gallery_slab_m": 0.35,
    "gallery_rail_h_m": 1.05,           # kit.handrail's own default
    "gallery_fascia_top_m": 0.35,       # below the deck: where the band starts
    "gallery_fascia_bot_m": 1.00,       # and ends, leaving 2.6 m of headroom
    "rib_spacing_m": RIB_SPACING_M,
    "rib_depth_m": 0.55,                # kit.rib_arch's default
    "rib_thickness_m": 0.42,            # kit.rib_arch's default
    "tile_m": TILE_M,
    # Stair. 18 risers of 0.200 m at a 0.25 m going is steeper than a
    # terrestrial public building would allow, and is what fits between ribs at
    # 5.4 m centres. The station's answer for anyone who cannot use it is the
    # lift, not a shallower flight.
    "stair_risers": 18,
    "stair_going_m": 0.25,
    "stair_width_m": 1.40,
    # Seating. The cluster radius is the table plus a chair plus its pull-back;
    # the outer zone limit is set so a cluster cannot overhang the well edge.
    "seat_ring_m": 0.58,
    "cluster_r_m": 0.86,
    "cluster_gap_m": 2.00,
    "seat_zone_in_m": 2.60,
    "seat_zone_out_m": 5.35,
    # Stalls sit in the colonnade under the gallery.
    "stall_x_m": 9.00,
    "gallery_stall_x_m": 9.20,
    "stall_w_m": 2.40,
    "stall_d_m": 1.20,
    "stall_counter_h_m": 1.00,
    "stall_eave_h_m": 2.40,
    "stall_ridge_h_m": 2.85,
    "stall_awning_w_m": 3.00,
    "stall_awning_d_m": 2.20,
    "downlights_per_bay": 8,
    # The index entry for this frame reads the "5" onto table pedestals as well
    # as chair backs. In THIS frame the only pedestal visible square-on is plain
    # pale grey with a service port, and the "5" beside it is on the foreground
    # chair's back panel. Both readings are one edit apart.
    "table_pedestal_five": False,
}


def params(**overrides):
    """PROVISIONAL merged onto the concourse corridor class, then overrides.

    The Zocalo is a concourse: `class_params("concourse")` carries the 7.2 m
    two-deck height, the rib-arch flag and the deck strip width, and this module
    supplies what a plaza needs beyond a corridor.
    """
    p = kit.class_params("concourse")
    p.update(PROVISIONAL)
    p.update(overrides)
    p["corridor_class"] = "zocalo"
    return p


# ---------------------------------------------------------------------------
# Mesh accumulation
# ---------------------------------------------------------------------------
class Mesh:
    """Vertices, triangles, and the material group of every triangle.

    A per-triangle group list rather than interior_kit's tag machinery, because
    that machinery keys spans on `id(list)` and POPS them on merge. Correct for
    a piece built once and placed once; the Zocalo places one chair mesh twenty
    times, and every placement after the first would silently lose its material.
    """

    def __init__(self):
        self.v, self.t, self.g = [], [], []

    def add(self, verts, tris, group, remap=None, offset=(0.0, 0.0, 0.0),
            flip=False, groups=None):
        """Append a piece authored in its own frame.

        `flip` reverses winding and is REQUIRED for any remap of negative
        determinant -- mirroring to the far side of the concourse turns a piece
        inside-out otherwise, and an inside-out interior is one you see straight
        through.
        """
        base = len(self.v)
        ox, oy, oz = offset
        for x, y, z in verts:
            nx, ny, nz = remap(x, y, z) if remap else (x, y, z)
            self.v.append((nx + ox, ny + oy, nz + oz))
        if flip:
            self.t.extend([(c + base, b + base, a + base) for a, b, c in tris])
        else:
            self.t.extend([(a + base, b + base, c + base) for a, b, c in tris])
        if groups is not None:
            if len(groups) != len(tris):
                raise ValueError("groups must be one per triangle")
            self.g.extend(groups)
        else:
            self.g.extend([group] * len(tris))
        return self

    def merge(self, other, remap=None, offset=(0.0, 0.0, 0.0), flip=False):
        return self.add(other.v, other.t, None, remap, offset, flip,
                        groups=list(other.g))

    def solid(self, corners, group):
        """One closed box from 8 corners in interior_kit's `_slab` order."""
        v, t = [], []
        _box(v, t, corners)
        return self.add(v, t, group)

    def slab(self, x0, x1, y0, y1, z0, z1, group):
        return self.solid([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                           (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
                          group)

    def quad(self, a, b, c, d, group):
        """Two triangles a-b-c and a-c-d. The normal is (b - a) x (c - a)."""
        base = len(self.v)
        self.v.extend([a, b, c, d])
        self.t.extend([(base, base + 1, base + 2), (base, base + 2, base + 3)])
        self.g.extend([group, group])
        return self

    def as_tuple(self):
        return self.v, self.t, self.g

    def __len__(self):
        return len(self.t)


def _from_kit(tris, spans, default):
    """Turn interior_kit tag spans into a per-triangle group list."""
    groups = [default] * len(tris)
    for name, lo, hi in spans:
        for i in range(lo, min(hi, len(tris))):
            groups[i] = name
    return groups


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def _u01(*parts):
    """Uniform in [0, 1) from blake2b over the parts.

    Never `random` and never the builtin string hash: the latter is salted per
    process and would have produced a different Zocalo every run (session 2n).
    """
    key = "|".join(str(p) for p in parts).encode()
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(),
                          "big") / 2.0 ** 64


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
def _cylinder(mesh, cx, cz, r, y0, y1, seg, side_group, cap_group=None,
              cap_lo=True, cap_hi=True):
    """A vertical cylinder wound OUTWARD, with optional caps.

    Caps and side take separate groups because a table top is a pale slab with a
    metal edge band and that is one object, not two.
    """
    cap_group = cap_group or side_group
    base = len(mesh.v)
    for i in range(seg):
        a = math.tau * i / seg
        mesh.v.append((cx + r * math.cos(a), y0, cz + r * math.sin(a)))
    for i in range(seg):
        a = math.tau * i / seg
        mesh.v.append((cx + r * math.cos(a), y1, cz + r * math.sin(a)))
    for i in range(seg):
        j = (i + 1) % seg
        # (i, hi_j, j) and (i, hi_i, hi_j). The obvious ordering -- (i, j, hi_j)
        # -- gives an INWARD normal; caught by signed_volume coming out at
        # -0.0134 on the table.
        mesh.t.append((base + i, base + seg + j, base + j))
        mesh.t.append((base + i, base + seg + i, base + seg + j))
        mesh.g.extend([side_group, side_group])
    if cap_hi:
        c = len(mesh.v)
        mesh.v.append((cx, y1, cz))
        for i in range(seg):
            j = (i + 1) % seg
            # Faces UP. An ascending angle in the XZ plane with +Y up gives a
            # DOWNWARD normal, so the fan runs backwards. That exact bug has
            # occurred three times in this project.
            mesh.t.append((c, base + seg + j, base + seg + i))
            mesh.g.append(cap_group)
    if cap_lo:
        c = len(mesh.v)
        mesh.v.append((cx, y0, cz))
        for i in range(seg):
            j = (i + 1) % seg
            mesh.t.append((c, base + i, base + j))
            mesh.g.append(cap_group)
    return mesh


def _arc_panel(mesh, r, thick, y0, y1, a0, a1, seg, group):
    """A vertical panel bent on a cylinder: the chair back, and its top rail.

    A genuine sweep -- four faces a segment plus two end caps -- rather than a
    string of closed boxes. A box per segment double-emits every shared face and
    leaves the whole panel non-manifold: 56 edges used by four triangles on the
    first attempt, which renders perfectly and is wrong.
    """
    ri, ro = r, r + thick
    base = len(mesh.v)
    for i in range(seg + 1):
        a = a0 + (a1 - a0) * i / seg
        c, s = math.cos(a), math.sin(a)
        mesh.v.extend([(ri * c, y0, ri * s), (ro * c, y0, ro * s),
                       (ro * c, y1, ro * s), (ri * c, y1, ri * s)])

    def q(p0, p1, p2, p3):
        mesh.t.append((p0, p1, p2))
        mesh.t.append((p0, p2, p3))
        mesh.g.extend([group, group])

    for i in range(seg):
        a, b = base + 4 * i, base + 4 * (i + 1)
        q(a + 0, b + 0, b + 3, a + 3)          # intrados, faces the axis
        q(a + 1, a + 2, b + 2, b + 1)          # extrados, faces away
        q(a + 0, a + 1, b + 1, b + 0)          # underside, faces down
        q(a + 3, b + 3, b + 2, a + 2)          # top, faces up
    e = base + 4 * seg
    q(base + 3, base + 2, base + 1, base + 0)  # start cap
    q(e + 0, e + 1, e + 2, e + 3)              # end cap
    return mesh


def rib_profile(p, y):
    """(intrados_x, extrados_x) of the rib's right limb at height `y`.

    Exposed because every clearance assertion in this module is written against
    it. It describes the REPAIRED rib -- the extrados outboard of the intrados,
    the section perpendicular to the arc -- so it and the geometry agree, and
    the self-test checks that they do rather than assuming it.
    """
    a = p["well_width_m"] / 2.0
    b = p["ceiling_height_m"] - p["rib_thickness_m"]
    if not -1e-9 <= y <= b + 1e-9:
        raise ValueError(f"y={y} is outside the rib's springing-to-crown range "
                         f"[0, {b}]")
    s = min(1.0, max(0.0, y / b))
    c = math.sqrt(max(0.0, 1.0 - s * s))       # right limb: cos t = -c
    inner = a * c
    nx, ny = c / a, s / b                      # outward normal, corrected sign
    n = math.hypot(nx, ny) or 1.0
    return inner, inner + p["rib_thickness_m"] * (nx / n)


RIB_SEGMENTS = 26        # kit.rib_arch's own default; named because the repair
#                          below indexes the vertex block it emits per segment.


def rib_arch_repaired(width, height, depth, thickness, segments=RIB_SEGMENTS):
    """`kit.rib_arch`'s mesh with the extrados put back on the outside.

    THE DEFECT, found here and reported for the kit's owner. `rib_arch`
    parameterises the ellipse as (-a cos t, b sin t) and then takes its outward
    normal as (+cos t / a, sin t / b). The x sign does not match the point. The
    consequence is not cosmetic: the offset direction ends up almost PARALLEL to
    the tangent over the middle of each limb -- at t = 45 degrees the dot
    product is 0.997 -- so consecutive segments lie on top of one another and
    the arch pinches to nothing at the haunches. The emitted solid's signed
    volume is -0.41 m3 where the swept section is +4.7 m3: negative, meaning
    inside-out, and an eighth of the magnitude, meaning folded. The signature
    element of every Babylon 5 interior in this project is a folded ribbon that
    happens to have the right silhouette, which is why nothing caught it.

    THE REPAIR. `rib_arch` emits exactly sixteen vertices per segment in a fixed
    order -- four inner, four outer, then two inner and two outer twice -- so
    the eight outer ones can be recomputed from the same parameterisation with
    the sign corrected. This is not a reimplementation: the arc, the segment
    count, the section and the winding all still come from the kit.

    It is also SELF-DELETING. The function probes one vertex to decide which
    form the kit emitted; when the kit is fixed at source, the probe matches the
    corrected form and the mesh passes through untouched.
    """
    v, t = kit.rib_arch(width, height, depth=depth, thickness=thickness,
                        segments=segments)
    a, b = width / 2.0, height
    if len(v) != 16 * segments:
        raise AssertionError(
            f"rib_arch emitted {len(v)} vertices for {segments} segments, not "
            f"the 16 per segment this repair indexes. Re-derive the mapping "
            f"before trusting it.")

    def outer_at(tt, sign_x):
        nx, ny = sign_x * math.cos(tt) / a, math.sin(tt) / b
        n = math.hypot(nx, ny) or 1.0
        return (-a * math.cos(tt) + nx / n * thickness,
                b * math.sin(tt) + ny / n * thickness)

    # Vertex 5 of segment 0 is the outer point at t = 0, where the two candidate
    # offsets differ by 2 * thickness. Nothing subtle to get wrong.
    probe = v[5][:2]
    good, bad = outer_at(0.0, -1.0), outer_at(0.0, +1.0)
    if math.dist(probe, good) < 1e-9:
        return v, t                                   # upstream already fixed
    if math.dist(probe, bad) > 1e-9:
        raise AssertionError(
            f"rib_arch's outer curve at t=0 is {probe}, which is neither the "
            f"correct offset {good} nor the known-bad one {bad}. The repair no "
            f"longer describes the function it repairs.")

    # (vertex offset within the segment, which end of the segment it came from)
    for i in range(segments):
        for off, which in ((4, 1), (5, 0), (6, 0), (7, 1),
                           (10, 1), (11, 0), (14, 0), (15, 1)):
            k = 16 * i + off
            x, y = outer_at(math.pi * (i + which) / segments, -1.0)
            v[k] = (x, y, v[k][2])
    return v, t


# `zoc_rib_arch`, not `zoc_rib`: the cap and the lamp are
# `zoc_rib_cap` and `zoc_rib_lamp`, so a bare `zoc_rib` is a PREFIX of
# both. Under substring/longest-wins resolution a material binding it
# also matches its own siblings -- harmless for which material wins,
# and a genuine ambiguity for the gate that asks how many materials
# claim a group. Three siblings with a common stem and no containment
# is the shape that stays unambiguous as more ribs are added.
def _rib(mesh, p, z, group="zoc_rib_arch"):
    """One elliptical rib, with its springings capped.

    `kit.rib_arch` is the project's rib and is reused rather than
    reimplemented -- through `rib_arch_repaired`, which corrects one sign in the
    emitted outer curve and explains why.

    It also leaves the two sweep ends open -- 8 boundary edges -- which is
    invisible in a corridor because they are buried in the deck, and is still a
    hole. The two cap quads below close it, computed from the same formulas so
    they weld.
    """
    w, t_rib, d = p["well_width_m"], p["rib_thickness_m"], p["rib_depth_m"]
    b = p["ceiling_height_m"] - t_rib          # extrados meets the soffit exactly
    v, t = rib_arch_repaired(w, b, d, t_rib)
    mesh.add(v, t, group, offset=(0.0, 0.0, z))

    a = w / 2.0
    lo, hi = z - d / 2.0, z + d / 2.0
    for tt in (0.0, math.pi):
        cx = -a * math.cos(tt)
        nx = -math.cos(tt) / a          # the corrected sign, as in the repair
        ox = cx + (nx / abs(nx)) * t_rib
        # The sole of the springing, sitting on the deck: must face DOWN. The
        # ordering depends on which side of the arch we are on, because the
        # outer curve is inboard of the inner one on both limbs.
        if ox < cx:
            mesh.quad((cx, 0.0, lo), (cx, 0.0, hi), (ox, 0.0, hi), (ox, 0.0, lo),
                      "zoc_rib_cap")
        else:
            mesh.quad((ox, 0.0, lo), (ox, 0.0, hi), (cx, 0.0, hi), (cx, 0.0, lo),
                      "zoc_rib_cap")
    return mesh


# ---------------------------------------------------------------------------
# Deck
# ---------------------------------------------------------------------------
def tiled_deck(p, index=0, seed="zocalo"):
    """The lower deck: large pale square tiles on a darker grid.

    One quad per tile, not one quad per bay, for ONE reason worth the 2,304
    triangles: tiles vary individually. The reference deck is scuffed in the
    traffic lanes, clean under the tables and chevron-banded at the thresholds,
    and a per-tile quad is what lets a material differ tile to tile.

    It is NOT for the preview render, and an earlier version of this comment
    claimed it was. Coplanar quads shade identically under a flat-shaded
    rasteriser, so the tile joints do not appear at all -- only the three
    material groups do. Checked, not assumed.

    The chevron band and the tile pattern itself are MATERIALS on those groups,
    not geometry. Three groups, three draw calls.
    """
    m = Mesh()
    w, l, tile = p["bay_width_m"], p["bay_length_m"], p["tile_m"]
    nx, nz = int(round(w / tile)), int(round(l / tile))
    for ix in range(nx):
        x0, x1 = -w / 2 + ix * tile, -w / 2 + (ix + 1) * tile
        for iz in range(nz):
            z0, z1 = iz * tile, (iz + 1) * tile
            # The stripe direction reverses about the centreline, so the band
            # reads as a V pointing along the concourse rather than as a plain
            # diagonal. Bands sit at both ends of the bay, as thresholds.
            in_band = iz < 3 or iz >= nz - 3
            k = (ix if ix < nx // 2 else nx - 1 - ix) + iz
            if in_band and k % 6 < 2:
                g = "zoc_deck_chevron"
            elif _u01(seed, "wear", index, ix, iz) < 0.07:
                g = "zoc_deck_worn"
            else:
                g = "zoc_deck_tile"
            # Faces UP: (x0,z0) -> (x0,z1) -> (x1,z1) is the order that gives
            # +Y. Ascending angle in XZ with +Y up gives a DOWNWARD normal.
            m.quad((x0, 0.0, z0), (x0, 0.0, z1), (x1, 0.0, z1), (x1, 0.0, z0), g)

    # --- AND THE FIELD IS A SLAB, NOT A SHEET -----------------------------
    # Adjacent tiles weld to each other -- they are laid on an exact grid, so
    # their shared edges have identical coordinates -- but the field's own
    # PERIMETER was open all the way round: 240 edges on a three-bay run, the
    # largest remaining hole in the Zocalo once the downlight pools were
    # rimmed. `_selftest` had declared them, which is honest bookkeeping and
    # not closure: a declared hole is still a hole in the deck this room
    # composes onto, and the deck asserts watertightness.
    #
    # The skirt is subdivided at the TILE JOINTS, because that is where the
    # field's boundary vertices already are; a plain rectangle round it would
    # leave a T-junction at every joint and close nothing. The underside is a
    # fan from one centre point, which needs no interior lattice -- nobody
    # ever sees it -- but must carry every perimeter vertex, or the skirt has
    # nothing to meet at its foot.
    ring = ([(-w / 2 + ix * tile, 0.0) for ix in range(nx)]
            + [(w / 2, iz * tile) for iz in range(nz)]
            + [(w / 2 - ix * tile, l) for ix in range(nx)]
            + [(-w / 2, l - iz * tile) for iz in range(nz)])
    base = len(m.v)
    for x, z in ring:
        m.v.append((x, 0.0, z))
        m.v.append((x, -DECK_SLAB_M, z))
    hub = len(m.v)
    m.v.append((0.0, -DECK_SLAB_M, l / 2.0))
    t0 = len(m.t)
    for k in range(len(ring)):
        a, b = base + 2 * k, base + 2 * ((k + 1) % len(ring))
        m.t += [(a, a + 1, b + 1), (a, b + 1, b)]              # skirt, outward
        m.t.append((hub, b + 1, a + 1))                        # underside
    m.g.extend(["zoc_deck_tile"] * (len(m.t) - t0))
    return m


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------
def gallery(p, side=1, rail=True):
    """One side's upper gallery: slab, edge beam, raking fascia, handrail.

    `more zocalo.png` shows people standing at the gallery edge looking down,
    with a band of raking struts between the deck line and the shopfront heads
    below. The rail is the kit's red-orange handrail, the dominant warm accent
    in every Zocalo frame (`zocalo.webp`, authority 1).

    The fascia band stops 2.5 m above the lower deck. It is over the colonnade
    the crowd walks through, and a decorative truss at head height is a thing
    people walk into.
    """
    m = Mesh()
    l = p["bay_length_m"]
    x_in = p["well_width_m"] / 2.0
    x_out = p["bay_width_m"] / 2.0
    y = p["gallery_y_m"]
    slab = p["gallery_slab_m"]
    f_top, f_bot = y - p["gallery_fascia_top_m"], y - p["gallery_fascia_bot_m"]

    m.slab(x_in, x_out, y - slab, y, 0.0, l, "zoc_gallery_slab")
    # Edge beam. Overlapped into the slab by WELD_M rather than butted: two
    # boxes meeting exactly share an edge, and a shared edge is non-manifold.
    m.slab(x_in, x_in + 0.45, f_bot, f_top + WELD_M, 0.0, l, "zoc_gallery_beam")
    n = max(2, int(round(l / 1.8)))
    for i in range(n):
        za, zb = l * i / n, l * (i + 1) / n
        p0, p1 = (za, zb) if i % 2 == 0 else (zb, za)
        # Run each strut 0.05 m PAST its node at both ends. Two struts meeting
        # exactly at a node share a face, and a shared face is five non-manifold
        # edges; overlapping past it is invisible and leaves both shells clean.
        d = 0.05 if p1 > p0 else -0.05
        p0, p1 = p0 - d, p1 + d
        m.solid([(x_in + 0.46, f_top, p0 - 0.09),
                 (x_in + 0.72, f_top, p0 - 0.09),
                 (x_in + 0.72, f_top, p0 + 0.09),
                 (x_in + 0.46, f_top, p0 + 0.09),
                 (x_in + 0.46, f_bot, p1 - 0.09),
                 (x_in + 0.72, f_bot, p1 - 0.09),
                 (x_in + 0.72, f_bot, p1 + 0.09),
                 (x_in + 0.46, f_bot, p1 + 0.09)], "zoc_gallery_strut")
    if rail:
        rv, rt = kit.handrail(l, height=p["gallery_rail_h_m"])
        # handrail() is authored with its run along +x and UP along +z. The
        # remap is a cyclic permutation, determinant +1, so no winding flip.
        m.add(rv, rt, "zoc_rail", remap=lambda x, yy, z: (yy, z, x),
              offset=(x_in + 0.12, y, 0.0))
    if side < 0:
        mm = Mesh()
        # Mirroring in x has determinant -1. Without the flip the entire gallery
        # is inside-out and reads as a hole in the frame.
        mm.merge(m, remap=lambda x, yy, z: (-x, yy, z), flip=True)
        return mm
    return m


# ---------------------------------------------------------------------------
# Stair
# ---------------------------------------------------------------------------
def stair_outline(p):
    """The flight's profile in (z along the run, y up), anticlockwise.

    Vertex 0 is the BOTTOM OF THE BACK -- the corner every other vertex is
    visible from. The region under a staircase is not star-shaped from its
    bottom-front corner, so a triangle fan anchored there produces triangles
    OUTSIDE the solid, which render as spikes while still reporting a correct
    closed volume: fan triangulation gets the signed area right whether or not
    the triangles are inside the polygon.
    """
    n, go = p["stair_risers"], p["stair_going_m"]
    riser = p["gallery_y_m"] / n
    run = n * go
    out = [(run, 0.0), (run, n * riser)]
    for i in range(n - 1, -1, -1):
        out.append((i * go, (i + 1) * riser))
        out.append((i * go, i * riser))
    return out


def stair_flight(p, group="zoc_stair"):
    """A straight flight from the lower deck to the gallery, as one solid.

    Built as one closed solid rather than as a stack of step boxes: two boxes
    sharing a partial face leave every non-shared edge used exactly once, so a
    stacked staircase reports well over a hundred boundary edges and is a
    surface with holes in it.
    """
    m = Mesh()
    hw = p["stair_width_m"] / 2.0
    out = stair_outline(p)
    n = len(out)

    # Caps. The outline is anticlockwise in (z, y), which for a plane at
    # constant x gives a -x normal; the +x cap is the same fan reversed.
    for i in range(1, n - 1):
        (z0, y0), (z1, y1), (z2, y2) = out[0], out[i], out[i + 1]
        m.t.extend([(len(m.v), len(m.v) + 1, len(m.v) + 2)])
        m.v.extend([(-hw, y0, z0), (-hw, y1, z1), (-hw, y2, z2)])
        m.g.append(group)
        m.t.extend([(len(m.v), len(m.v) + 1, len(m.v) + 2)])
        m.v.extend([(hw, y0, z0), (hw, y2, z2), (hw, y1, z1)])
        m.g.append(group)
    # Skirt: one quad per outline edge, wound outward.
    for i in range(n):
        (z0, y0), (z1, y1) = out[i], out[(i + 1) % n]
        tread = abs(y1 - y0) < 1e-12 and i > 1
        m.quad((-hw, y0, z0), (hw, y0, z0), (hw, y1, z1), (-hw, y1, z1),
               "zoc_stair_tread" if tread else group)

    riser = p["gallery_y_m"] / p["stair_risers"]
    rv, rt = kit.handrail(p["stair_risers"] * p["stair_going_m"], height=1.05)
    for s in (-1, 1):
        # handrail() is authored flat; shearing its local up-axis with the run
        # gives it the flight's pitch, so the rail follows the nosing line.
        sheared = [(x, y, z + x * riser / p["stair_going_m"]) for x, y, z in rv]
        m.add(sheared, rt, "zoc_rail", remap=lambda x, yy, z: (yy, z, x),
              offset=(s * (hw - 0.08), 0.0, 0.0))
    return m


def stair_x(p):
    """Lateral centre of the flight: its outer stringer flush with the well edge.

    Flush, not merely near: the top tread has to abut the gallery deck or there
    is a gap at 3.6 m for a player to step into.
    """
    return p["well_width_m"] / 2.0 - p["stair_width_m"] / 2.0


def stair_z0(p):
    """Where the flight starts: centred in the gap between two ribs."""
    run = p["stair_risers"] * p["stair_going_m"]
    return (p["rib_spacing_m"] - run) / 2.0


# ---------------------------------------------------------------------------
# Furniture
# ---------------------------------------------------------------------------
def pedestal_table(p=None, seg=16):
    """The Zocalo cafe table: pale disc, metal edge band, single pedestal.

    Every dimension is from `more zocalo.png` through the camera solve. The top
    is 0.475 m across, which is small for a table and is what the frame says:
    the chrome shaker standing on it measures 0.093 m by the same scale, and a
    cocktail shaker is 90 mm.

    The 22 mm service port the frame shows on the pedestal is a MATERIAL detail,
    not geometry -- at any distance a player sees it from it is a normal-map
    dimple, and its measured diameter is in `MEASURED` for whoever authors it.
    """
    p = p or params()
    m = Mesh()
    r = MEASURED["table_top_d_m"] / 2.0
    t = MEASURED["table_top_t_m"]
    rc = MEASURED["table_col_d_m"] / 2.0
    _cylinder(m, 0, 0, r, TABLE_H_M - t, TABLE_H_M, seg,
              "zoc_table_edge", cap_group="zoc_table_top")
    _cylinder(m, 0, 0, rc, 0.09 - WELD_M, TABLE_H_M - t + WELD_M,
              max(8, seg // 2),
              "zoc_table_five" if p["table_pedestal_five"] else "zoc_table_col")
    # The foot is wider than the column or a 0.475 m top tips it. Not visible in
    # the frame -- the near chair occludes it -- so it is twice the column, the
    # smallest that is stable.
    _cylinder(m, 0, 0, rc * 2.0, 0.0, 0.09, max(8, seg // 2), "zoc_table_foot")
    return m


def cafe_chair(p=None, seg=8):
    """The "5" chair: tubular frame, curved back panel, four splayed legs.

    The "5" is a MATERIAL on `zoc_chair_five`, not geometry. It is the same
    glyph as the station shield patch and the floor inlay in
    `05-sector-green/conference aerea.webp`, so it is built once as a decal.

    Authored facing +z, so a chair placed round a table is rotated to its
    bearing plus 180 degrees and its back panel lands on the outside.
    """
    p = p or params()
    m = Mesh()
    w = MEASURED["chair_w_m"]
    tube = MEASURED["chair_tube_d_m"]
    bh = MEASURED["chair_back_h_m"]
    r_back = w / 2.0 - tube
    seat = CHAIR_SEAT_H_M

    _cylinder(m, 0, 0, r_back * 0.92, seat - 0.035, seat, seg + 4,
              "zoc_chair_seat")
    a0, a1 = math.radians(-10.0), math.radians(190.0)
    _arc_panel(m, r_back, 0.018, seat, seat + bh, a0, a1, seg, "zoc_chair_five")
    _arc_panel(m, r_back - 0.004, tube, seat + bh, seat + bh + tube,
               a0 - 0.06, a1 + 0.06, seg, "zoc_chair_frame")
    # Four legs, splayed: the foot ring is wider than the seat ring, which is
    # what the frame shows and what stops a light chair tipping.
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        ct, st = math.cos(a), math.sin(a)
        rt, rb = r_back * 0.86, r_back * 1.12
        m.solid([(rt * ct - tube / 2, seat, rt * st - tube / 2),
                 (rt * ct + tube / 2, seat, rt * st - tube / 2),
                 (rt * ct + tube / 2, seat, rt * st + tube / 2),
                 (rt * ct - tube / 2, seat, rt * st + tube / 2),
                 (rb * ct - tube / 2, 0.0, rb * st - tube / 2),
                 (rb * ct + tube / 2, 0.0, rb * st - tube / 2),
                 (rb * ct + tube / 2, 0.0, rb * st + tube / 2),
                 (rb * ct - tube / 2, 0.0, rb * st + tube / 2)],
                "zoc_chair_frame")
    return m


def drinks_service(seg=12):
    """The chrome service on the table: domed shaker and a cluster of tumblers.

    0.093 m across the shaker, measured -- the single strongest confirmation
    that the camera solve is right, because a cocktail shaker is 90 mm and
    nothing in the derivation knew that.
    """
    m = Mesh()
    r = MEASURED["shaker_d_m"] / 2.0
    # No top cap: the dome closes it. Two coincident discs would leave every rim
    # edge used by three triangles.
    _cylinder(m, 0.0, 0.0, r, 0.0, 0.115, seg, "zoc_service_chrome",
              cap_hi=False)
    base = len(m.v)
    for i in range(seg):
        a = math.tau * i / seg
        m.v.append((r * math.cos(a), 0.115, r * math.sin(a)))
    apex = len(m.v)
    m.v.append((0.0, 0.115 + r * 1.15, 0.0))
    for i in range(seg):
        j = (i + 1) % seg
        m.t.append((base + i, base + j, apex))
        m.g.append("zoc_service_chrome")
    for dx, dz in ((-0.024, -0.024), (0.024, -0.024),
                   (-0.024, 0.024), (0.024, 0.024)):
        _cylinder(m, 0.085 + dx, dz, 0.022, 0.0, 0.10, 8, "zoc_service_chrome")
    return m


# ---------------------------------------------------------------------------
# Vendor stalls
# ---------------------------------------------------------------------------
def vendor_stall(p=None, variant=0, seed="zocalo"):
    """A market stall: counter, posts, fabric awning on radiating spars, sign.

    `zocalo.webp` and `more zocalo.png` agree: lightweight temporary-looking
    structures against permanent architecture, fabric canopies on spars, string
    lighting along the eaves, a disc sign on a braced pole. The awning is a
    closed hipped solid rather than a shell, so it has thickness in silhouette
    and no boundary edges.

    `variant` drives every difference between one stall and the next, so a run
    of stalls does not read as one stall stamped repeatedly.
    """
    p = p or params()
    m = Mesh()
    w, d = p["stall_w_m"], p["stall_d_m"]
    ch = p["stall_counter_h_m"]
    eave, ridge = p["stall_eave_h_m"], p["stall_ridge_h_m"]
    aw, ad = p["stall_awning_w_m"], p["stall_awning_d_m"]
    hw, hd = w / 2.0, d / 2.0

    m.slab(-hw, hw, ch - 0.09, ch, -hd, hd, "zoc_stall_counter")
    for sx in (-1, 1):
        m.slab(sx * hw - 0.20 if sx > 0 else -hw + 0.05,
               sx * hw - 0.05 if sx > 0 else -hw + 0.20,
               0.0, ch - 0.09 + WELD_M, -hd + 0.05, hd - 0.05,
               "zoc_stall_post")
    n_goods = 2 + variant % 3
    for i in range(n_goods):
        u = _u01(seed, "goods", variant, i)
        gw = 0.16 + 0.14 * u
        gx = -hw + 0.25 + (w - 0.5) * (i + 0.5) / n_goods
        m.slab(gx - gw / 2, gx + gw / 2, ch - WELD_M, ch + 0.12 + 0.2 * u,
               -0.16, 0.16, "zoc_stall_goods")

    for sx in (-1, 1):
        for sz in (-1, 1):
            m.slab(sx * hw - 0.045, sx * hw + 0.045, 0.0, eave,
                   sz * hd - 0.045, sz * hd + 0.045, "zoc_stall_post")

    # Awning: four eave corners and a ridge, closed underneath. Eight triangles
    # and a real silhouette, where a shell would be paper from below.
    haw, had = aw / 2.0, ad / 2.0
    e = [(-haw, eave, -had), (haw, eave, -had), (haw, eave, had), (-haw, eave, had)]
    rg = [(-haw * 0.35, ridge, 0.0), (haw * 0.35, ridge, 0.0)]
    base = len(m.v)
    m.v.extend(e + rg)
    for tri in ((0, 4, 1), (1, 4, 5), (1, 5, 2), (2, 5, 3), (3, 5, 4), (3, 4, 0),
                (0, 1, 2), (0, 2, 3)):
        m.t.append(tuple(base + i for i in tri))
        m.g.append("zoc_stall_awning")
    # Spars. The canopy is fabric on radiating spars, and the spars are what
    # makes it read as a parasol rather than as a folded plate. Each pair that
    # meets at a ridge point is landed 0.055 m either side of it rather than on
    # it: two spars ending on the same point share a face, which is five
    # non-manifold edges apiece, and the offset reads as a short ridge bar.
    for corner, ridge_pt in ((e[0], rg[0]), (e[1], rg[1]),
                             (e[2], rg[1]), (e[3], rg[0])):
        rz = 0.055 if corner[2] > 0 else -0.055
        m.solid([(corner[0], corner[1] - 0.05, corner[2] - 0.03),
                 (corner[0], corner[1] - 0.05, corner[2] + 0.03),
                 (corner[0], corner[1] + 0.01, corner[2] + 0.03),
                 (corner[0], corner[1] + 0.01, corner[2] - 0.03),
                 (ridge_pt[0], ridge_pt[1] - 0.05, rz - 0.03),
                 (ridge_pt[0], ridge_pt[1] - 0.05, rz + 0.03),
                 (ridge_pt[0], ridge_pt[1] + 0.01, rz + 0.03),
                 (ridge_pt[0], ridge_pt[1] + 0.01, rz - 0.03)],
                "zoc_stall_spar")

    # String lights along the front eave. Signage and practicals ARE the light
    # in this space; there is no ambient fill anywhere in the reference.
    n_lamp = 6 + variant % 3
    for i in range(n_lamp):
        lx = -haw + aw * (i + 0.5) / n_lamp
        m.slab(lx - 0.028, lx + 0.028, eave - 0.14, eave - 0.08,
               had - 0.03, had + 0.03, "zoc_stall_light")

    if variant % 2 == 0:
        sx = hw + 0.35
        _cylinder(m, sx, 0.0, 0.34, eave + 0.15, eave + 0.23, 12,
                  "zoc_stall_sign")
        m.slab(sx - 0.05, sx + 0.05, ch, eave + 0.19, -0.05, 0.05,
               "zoc_stall_mast")
        m.solid([(sx - 0.04, ch + 0.55, -0.04), (sx + 0.04, ch + 0.55, -0.04),
                 (sx + 0.04, ch + 0.55, 0.04), (sx - 0.04, ch + 0.55, 0.04),
                 (hw - 0.10, ch, -0.04), (hw - 0.02, ch, -0.04),
                 (hw - 0.02, ch, 0.04), (hw - 0.10, ch, 0.04)],
                "zoc_stall_mast")
    return m


def neon_sign(p=None):
    """The Zocalo wordmark: a lit face on a dark backing plate.

    1.9 x 0.84 m, measured at the gallery's depth. The wordmark is Latin, not
    alien script -- corrected in session 2q and confirmed square-on here -- and
    it is attested orange-red in this frame and cyan in
    `11-props-and-technology/Zocalo neon signage in background.jpg`. Both are
    recorded; the choice is a material, and the six glyphs are a decal on
    `zoc_neon_face`, not geometry.
    """
    p = p or params()
    m = Mesh()
    w, h = MEASURED["neon_w_m"], MEASURED["neon_h_m"]
    m.slab(-w / 2, w / 2, 0.0, h, -0.10, 0.0, "zoc_neon_back")
    m.slab(-w / 2 + 0.06, w / 2 - 0.06, 0.06, h - 0.06, -0.14, -0.10 + WELD_M,
           "zoc_neon_face")
    for sx in (-1, 1):
        m.slab(sx * (w / 2 - 0.10) - 0.03, sx * (w / 2 - 0.10) + 0.03,
               -0.10, WELD_M, -0.05, 0.01, "zoc_stall_mast")
    return m


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------
def blocked_rects(p, stair_side):
    """Plan rectangles the seating must not overlap: the rib feet, the stair."""
    out = []
    d = p["rib_depth_m"]
    inner, outer = rib_profile(p, 0.0)
    lo, hi = min(inner, outer), max(inner, outer)
    for k in range(2):
        z = k * p["rib_spacing_m"]
        for s in (-1, 1):
            x0, x1 = sorted((s * lo, s * hi))
            out.append((x0, x1, z - d / 2, z + d / 2))
    if stair_side:
        z0 = stair_z0(p)
        run = p["stair_risers"] * p["stair_going_m"]
        cx = stair_x(p) * stair_side
        hwid = p["stair_width_m"] / 2 + 0.30
        out.append((cx - hwid, cx + hwid, z0 - 0.3, z0 + run + 0.9))
    return out


def seating_plan(p=None, index=0, seed="zocalo", stair_side=0, candidates=60):
    """Deterministic table positions that clear each other and the structure.

    Rejection sampling over a fixed blake2b-derived candidate sequence: the same
    (seed, index) gives the same plan on any machine and any Python, and the
    result does not depend on iteration order because the candidate order is
    fixed before anything is accepted.

    Returns [(x, z, chairs, phase_deg, service)].
    """
    p = p or params()
    blocked = blocked_rects(p, stair_side)
    r_cl, gap = p["cluster_r_m"], p["cluster_gap_m"]
    zi, zo = p["seat_zone_in_m"], p["seat_zone_out_m"]
    l = p["bay_length_m"]
    out = []
    for k in range(candidates):
        side = 1 if _u01(seed, index, k, "side") < 0.5 else -1
        x = side * (zi + (zo - zi) * _u01(seed, index, k, "x"))
        z = r_cl + (l - 2 * r_cl) * _u01(seed, index, k, "z")
        if any(x + r_cl > bx0 and x - r_cl < bx1
               and z + r_cl > bz0 and z - r_cl < bz1
               for bx0, bx1, bz0, bz1 in blocked):
            continue
        if any(math.hypot(x - ox, z - oz) < gap for ox, oz, _, _, _ in out):
            continue
        n_ch = 2 + int(_u01(seed, index, k, "n") * 3.0)      # 2, 3 or 4
        phase = 360.0 * _u01(seed, index, k, "phase")
        service = _u01(seed, index, k, "svc") < 0.4
        out.append((x, z, n_ch, phase, service))
    return out


# ---------------------------------------------------------------------------
# The bay
# ---------------------------------------------------------------------------
## THE RIBS IN ONE BAY, AND THE LAMPS SET INTO EACH RIB'S INTRADOS. Named
## because `tools/export_scene.py`'s self-test has to derive its expected lamp
## count from this module instead of pinning it: the pinned 30 was written when
## `BESPOKE_GEOMETRY` called `zocalo_run(3)` and survived unchanged when
## `bays_for` took the room to six bays, so the assertion said 30 against a
## measured 60 for four sessions.
RIBS_PER_BAY = 2
RIB_LAMP_F = (0.16, 0.32, 0.50, 0.68, 0.84)


def zocalo_bay(p=None, index=0, seed="zocalo", stair_side=None,
               furniture=True, stalls=True, sign=None):
    """One Zocalo bay, authored at z in [0, bay_length].

    x is lateral with 0 on the concourse centreline, y is up from the lower
    deck, z runs along the concourse -- the same frame `interior_kit`'s wall and
    corridor pieces are authored in, so they drop straight in.

    Returns (verts, tris, groups), one group name per triangle, which is what
    `interior.write_grouped_obj` consumes.
    """
    p = p or params()
    if stair_side is None:
        stair_side = (1, 0, -1, 0)[index % 4]
    if sign is None:
        sign = index % 3 == 0
    m = Mesh()
    l, hw = p["bay_length_m"], p["bay_width_m"] / 2.0
    ceil = p["ceiling_height_m"]
    x_in = p["well_width_m"] / 2.0

    m.merge(tiled_deck(p, index, seed))

    # Side walls, full height. wall_assembly is authored with its inner face at
    # x = 0 and its body toward -x, so the +x side is a mirror and needs the
    # winding flip every negative-determinant remap needs.
    for s in (-1, 1):
        kit.reset_tags()
        wv, wt = kit.wall_assembly(l, ceil, p)
        wg = _from_kit(wt, kit.tagged_spans(wt), "zoc_wall")
        if s < 0:
            m.add(wv, wt, None, offset=(-hw, 0.0, 0.0), groups=wg)
        else:
            m.add(wv, wt, None, remap=lambda x, y, z: (-x, y, z), flip=True,
                  offset=(hw, 0.0, 0.0), groups=wg)
    kit.reset_tags()

    # Soffit, the FULL width of the bay. It spanned only the well on the first
    # pass, which left the gallery's upper storey open to the background: a
    # magenta render put 27% of the frame through the hole, and against the
    # black the render is meant to be judged on it read as unlit ceiling.
    # ...and it is a SLAB. As one quad its two long edges at x = +-hw were
    # open, 8 on a three-bay run: the ceiling did not meet the side walls, and
    # a ceiling with no thickness has no soffit line where it does. The seam
    # weld drops its z faces between bays exactly as it does for every other
    # longitudinal member here, so a run stays one continuous solid.
    m.slab(-hw, hw, ceil, ceil + SOFFIT_T_M, 0.0, l, "zoc_soffit")
    # Longitudinal purlins spanning rib to rib. A 233 m2 ceiling with nothing on
    # it reads as a lid, and the reference shows structure overhead in every
    # frame of this set. Five shallow beams, 60 triangles, and the soffit stops
    # being a flat plane.
    for k in range(5):
        px = -8.0 + 4.0 * k
        m.slab(px - 0.16, px + 0.16, ceil - 0.34, ceil - WELD_M, 0.0, l,
               "zoc_purlin")

    a_rib = p["well_width_m"] / 2.0
    b_rib = ceil - p["rib_thickness_m"]
    for k in range(RIBS_PER_BAY):
        z_rib = k * p["rib_spacing_m"]
        _rib(m, p, z_rib)
        # Lamps set into the rib's intrados: `more hallway.jpg` shows them
        # repeating along the ribs, and `more zocalo.png` shows one flaring on
        # the arch above the gallery. Placed by ARC PARAMETER, which already
        # covers both limbs -- the first attempt walked half the arc and
        # mirrored it, which put the 0.30 and 0.70 lamps at the same height and
        # the two crown lamps on top of each other: six pairs of exactly
        # coincident boxes and 108 non-manifold edges.
        for f in RIB_LAMP_F:
            t = math.pi * f
            lx, ly = -a_rib * math.cos(t), b_rib * math.sin(t)
            m.slab(lx - 0.13, lx + 0.13, ly - 0.10, ly + 0.10,
                   z_rib - 0.09, z_rib + 0.09, "zoc_rib_lamp")

    for s in (-1, 1):
        m.merge(gallery(p, side=s))

    # Backlit shopfront panels in the colonnade. Every light in this space has
    # an object behind it; there is no ambient fill in any reference frame.
    for s in (-1, 1):
        for k in range(2):
            z = l * (k + 0.5) / 2.0
            m.slab(s * (hw - 0.24), s * (hw - 0.18), 1.10, 2.60,
                   z - 1.15, z + 1.15, "zoc_screen")

    if stalls:
        for s in (-1, 1):
            for k in range(2):
                z = l * (k + 0.5) / 2.0
                var = (index * 4 + (0 if s < 0 else 2) + k) % 6
                m.merge(vendor_stall(p, variant=var, seed=seed),
                        remap=kit._rot_y(90.0 if s < 0 else -90.0),
                        offset=(s * p["stall_x_m"], 0.0, z))
                # And the same trade on the gallery. Without it the upper deck
                # is a shelf with a rail on it: the render read as one empty
                # pale plane across a third of the frame, and `zocalo.webp`
                # shows the upper level trading exactly as the lower one does.
                # Staggered half a pitch so the two levels do not line up.
                m.merge(vendor_stall(p, variant=(var + 3) % 6, seed=seed),
                        remap=kit._rot_y(90.0 if s < 0 else -90.0),
                        offset=(s * p["gallery_stall_x_m"], p["gallery_y_m"],
                                (z + l * 0.25) % l))

    if stair_side:
        m.merge(stair_flight(p),
                offset=(stair_side * stair_x(p), 0.0, stair_z0(p)))

    if sign:
        m.merge(neon_sign(p), remap=kit._rot_y(-90.0),
                offset=(-(x_in + 0.12), p["gallery_y_m"]
                        + p["gallery_rail_h_m"] + 0.10, l * 0.5))

    # Deck lighting: the lit strip down the centre and the measured 1.57 m
    # downlight pools. Both lie flat and both MUST face up.
    sv, st_ = kit.deck_strip(p["deck_strip_w_m"], l)
    m.add(sv, st_, "zoc_deck_strip")
    nd = p["downlights_per_bay"]
    for k in range(nd // 2):
        z = l * (k + 0.5) / (nd // 2)
        for s in (-1, 1):
            dv, dt = kit.downlight_pool()
            m.add(dv, dt, "zoc_downlight", offset=(s * 4.7, 0.0, z))

    if furniture:
        plan = seating_plan(p, index, seed, stair_side)
        table = pedestal_table(p)
        chair = cafe_chair(p)
        svc = drinks_service()
        for j, (x, z, n_ch, phase, has_svc) in enumerate(plan):
            m.merge(table, offset=(x, 0.0, z))
            if has_svc:
                m.merge(svc, offset=(x + 0.06, TABLE_H_M, z - 0.03))
            for c in range(n_ch):
                a = phase + 360.0 * c / n_ch
                # A little pull-back, so no two chairs sit at the same radius.
                r = p["seat_ring_m"] + 0.10 * _u01(seed, index, j, c, "pull")
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                m.merge(chair, remap=kit._rot_y(a + 180.0),
                        offset=(x + r * sa, 0.0, z + r * ca))
    return m.as_tuple()


def bays_for(place, p=None, cap=6):
    """How many bays the register's own footprint holds, and a per-place seed.

    Returns `(bays, seed)`.

    THE ARGUMENTS EXISTED AND NOBODY PASSED THEM. `bespoke.BESPOKE_GEOMETRY`
    called `zocalo_run(3, cap_ends=True)` with no place at all, so `zocalo` and
    `shops_kiosks` drew the same three bays with the same stall seed --
    identical geometry, which `deck.py --degeneracy` fails on.

    The register separates them: 70 x 120 m against 40 x 100 m, and the Zocalo
    declares `crowd_hub` and `public_social` where the kiosks declare `retail`.
    A bay is `bay_length_m` along the run, so the count is arithmetic rather
    than a choice; the seed is the place key, so two runs of the same length
    still lay their stalls out differently.

    `cap` is a triangle budget, not a layout opinion: 120 m at 10.8 m a bay is
    11 bays, and the Zocalo is already the heaviest interior in the project.
    """
    p = p or params()
    fp = (place or {}).get("footprint")
    key = (place or {}).get("key", "zocalo")
    if not fp:
        return 3, "zocalo"
    n = int(float(fp[1]) // p["bay_length_m"])
    return max(2, min(cap, n)), key


def zocalo_run(bays=3, p=None, seed="zocalo", cap_ends=False, **kw):
    """`bays` bays end to end along +z.

    The tile grid is driven from the run's origin and the bay length is a whole
    number of tiles, so the deck pattern is continuous across every seam -- the
    defect STATE.md records at cell junctions, not repeated here.

    `cap_ends` closes the two ends with a bulkhead. OFF by default, because the
    concourse does continue and a wall there would be a lie about the space; ON
    for a render, where an open end is 27% of the frame showing the background.
    """
    p = p or params()
    m = Mesh()
    for i in range(bays):
        v, t, g = zocalo_bay(p, index=i, seed=seed, **kw)
        m.add(v, t, None, offset=(0.0, 0.0, i * p["bay_length_m"]), groups=g)

    # Weld the seams. Every longitudinal member -- the walls, the rails, the
    # purlins, the gallery slab and its beams -- is emitted per bay as a CLOSED
    # solid, so two adjacent bays meet face to face and every edge around that
    # face is shared by four triangles instead of two. Measured before this
    # existed: +152 non-manifold edges per added bay, 10 for one bay, 466 for
    # four, all of valence exactly 4 and 106 of them lying precisely on the
    # seam plane. In the engine that is a doubled coplanar face on every seam,
    # which z-fights, and the triangles behind it are never visible from
    # anywhere.
    #
    # A face lying ENTIRELY in an interior seam plane is sandwiched between two
    # bays by definition, so it can be dropped without opening anything: the
    # side faces either side of it then meet at the edge and the run becomes one
    # continuous solid. The ribs also sit on seam planes but are 0.55 m deep, so
    # their flanks are never coplanar with one and they survive untouched.
    seams = [i * p["bay_length_m"] for i in range(1, bays)]
    if seams:
        before = len(m.t)
        keep_t, keep_g = [], []
        for tri, grp in zip(m.t, m.g):
            zs = [m.v[i][2] for i in tri]
            interior_face = any(
                all(abs(z - sz) <= WELD_M for z in zs) for sz in seams)
            if not interior_face:
                keep_t.append(tri)
                keep_g.append(grp)
        m.t, m.g = keep_t, keep_g
        m.welded_faces = before - len(m.t)

        # Second seam defect, separate mechanism: the rail is emitted by BOTH
        # bays at a shared boundary, so 24 triangles exist twice over at every
        # seam -- same position, same winding, wholly redundant. A duplicate is
        # not a touching face and the plane test above cannot see it, because
        # the rail straddles the seam rather than lying in it. Dropping the
        # second copy is safe: it is the same surface, and two of them z-fight.
        seen, dedup_t, dedup_g = set(), [], []
        for tri, grp in zip(m.t, m.g):
            pts = [tuple(round(c, 4) for c in m.v[i]) for i in tri]
            # Canonical rotation, so the key preserves WINDING -- an oppositely
            # wound twin is a touching face, not a duplicate, and must survive.
            r = min(range(3), key=lambda i: pts[i])
            key = (pts[r], pts[(r + 1) % 3], pts[(r + 2) % 3], grp)
            if key in seen:
                continue
            seen.add(key)
            dedup_t.append(tri)
            dedup_g.append(grp)
        m.duplicate_faces = len(m.t) - len(dedup_t)
        m.t, m.g = dedup_t, dedup_g

    if cap_ends:
        hw, ceil = p["bay_width_m"] / 2.0, p["ceiling_height_m"]
        # OUTSIDE EVERYTHING THE RUN BUILT, not at the nominal bay boundary.
        # The stalls' awnings, masts and signs overhang the first bay's start by
        # up to 1.89 m, so a cap at z = 0 leaves 1.89 m of concourse furniture
        # standing in FRONT of its own end wall. That is invisible on its own
        # and decisive once the run is placed on a ring: `bespoke.room_shell`
        # puts the extreme z on the corridor's plane, so the near face of the
        # room became a stall sign and the bulkhead sat 1.89 m inside it --
        # where `deck._mouth_clear`, which only looks 1.2 m in, could not see
        # it. The gate would have passed a room sealed two metres past its door.
        zs = [q[2] for q in m.v] or [0.0, bays * p["bay_length_m"]]
        z_lo, z_hi = min(zs) - 0.30, max(zs) + 0.30
        # AND THE DECK RUNS OUT TO MEET THEM. `zoc_deck_tile` is laid per bay,
        # z 0..bays*bay_length, so moving the bulkheads outboard of the stalls'
        # overhang left 2.19 m of concourse at the near end with a wall, a
        # ceiling and NO FLOOR -- which `bespoke.near_face_opening` reported as
        # "no floor under the doorway" and refused to centre the room on. It was
        # right to: a doorway a body steps through into nothing is worse than a
        # sealed one, because the sealed one is visible.
        for z0, z1 in ((z_lo, 0.0), (bays * p["bay_length_m"], z_hi)):
            if z1 - z0 > 1e-6:
                m.slab(-hw, hw, -0.14, 0.0, z0, z1, "zoc_deck_tile")
        # THE NEAR CAP CARRIES A DOORWAY. `cap_ends` exists because an open end
        # is 27% of a render frame showing the background; on an assembled deck
        # it is also 21.6 x 7.2 m of hole into the back of the ring corridor,
        # which `deck.py`'s watertightness gate would fail. But a capped end is
        # a Zocalo nobody can walk into, and that is what `deck.py` was
        # reporting for all four zocalo places. INV-110 sizes the aperture.
        #
        # `min_z` is the near end -- see `bespoke.NEAR_END` -- so the doorway
        # goes in the z_lo cap.
        _bsp.doorway_wall(
            lambda n, lo, hi: m.slab(lo[0], hi[0], lo[1], hi[1],
                                     lo[2], hi[2], n),
            "zoc_bulkhead", -hw, hw, 0.0, ceil, z_lo, z_lo + 0.30)
        m.slab(-hw, hw, 0.0, ceil, z_hi - 0.30, z_hi, "zoc_bulkhead")
    return m.as_tuple()


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------
# Groups whose triangles are DRAWN many times from ONE mesh. The distinction
# matters here for the first time in this project: a bay holds one chair mesh
# about twenty times, so raster cost and VRAM cost stop being the same number.
INSTANCED = ("zoc_table_", "zoc_chair_", "zoc_service_", "zoc_downlight",
             "zoc_stall_")


def budget_report(p=None, seed="zocalo", out=print):
    """Triangle budget against station/budget.py's interior gates."""
    p = p or params()
    v, t, g = zocalo_bay(p, index=0, seed=seed)
    per = {}
    for name in g:
        per[name] = per.get(name, 0) + 1
    drawn = len(t)
    inst_drawn = sum(n for k, n in per.items() if k.startswith(INSTANCED))
    structure = drawn - inst_drawn

    plan = seating_plan(p, 0, seed, (1, 0, -1, 0)[0])
    stall_variants = sorted({v for s in (-1, 1) for k in range(2)
                             for v in ((0 * 4 + (0 if s < 0 else 2) + k) % 6,
                                       ((0 * 4 + (0 if s < 0 else 2) + k) + 3)
                                       % 6)})
    proto = {"table": len(pedestal_table(p).t),
             "chair": len(cafe_chair(p).t),
             "service": len(drinks_service().t),
             "downlight": len(kit.downlight_pool()[1]),
             "stall": len(vendor_stall(p, stall_variants[0]).t)}
    counts = {"table": len(plan),
              "chair": sum(c for _, _, c, _, _ in plan),
              "service": sum(1 for *_, s in plan if s),
              "downlight": p["downlights_per_bay"],
              # Four in the colonnade and four on the gallery.
              "stall": 8}
    # Unique = the bay's one-off structure, plus one copy of each prototype.
    # Stalls carry six variants, so a run resident-set holds six stall meshes.
    unique = structure + sum(proto.values())

    area = p["bay_width_m"] * p["bay_length_m"]
    out(f"\nZocalo bay: {p['bay_width_m']:.1f} x {p['bay_length_m']:.1f} x "
        f"{p['ceiling_height_m']:.1f} m, {area:.0f} m2 of deck")
    out(f"  open well {p['well_width_m']:.1f} m the full height; gallery "
        f"{p['gallery_depth_m']:.1f} m each side at {p['gallery_y_m']:.1f} m\n")
    out(f"  structure             {structure:>7,} tri   "
        f"{structure / area:5.1f} tri/m2")
    out(f"  furniture and stalls  {inst_drawn:>7,} tri drawn from "
        f"{sum(proto.values()):,} unique across {len(proto)} meshes")
    out(f"  BAY TOTAL             {drawn:>7,} tri drawn, {unique:,} unique")
    out("")
    for k in sorted(proto):
        out(f"    {k:<10} {proto[k]:>5,} tri x {counts[k]:>3} = "
            f"{proto[k] * counts[k]:>6,} drawn")
    out("\n  largest groups:")
    for name in sorted(per, key=lambda n: -per[n])[:8]:
        out(f"    {name:<24} {per[name]:>7,}")

    gate = budget.INTERIOR["visible_set_tris"]
    out(f"\nAgainst station/budget.py INTERIOR['visible_set_tris'] = {gate:,}")
    out("(structure only, 5% of a 1.2 M frame -- props, NPCs and signage come\n"
        " out of the rest, and in the Zocalo the NPCs ARE the subsystem):\n")
    n_bays = gate // drawn
    out(f"  {drawn:,} drawn tri/bay -> {n_bays} bays inside the gate "
        f"({n_bays * p['bay_length_m']:.0f} m of concourse)")

    # The concourse's own sight line, from the station's curvature rather than
    # from an assumption -- the derivation budget.py already uses for corridors.
    schema, profile = it.load()
    sight, where = max(
        (it.sight_line(r["r_outer"], p["bay_width_m"]), f"{sec} {r['id']}")
        for sec in schema["sectors"]["extents_m"]
        for r in it.ring_radii(schema, profile, sec)
        if r["kind"] == "deck_stack")
    full = int(math.ceil(sight / p["bay_length_m"]))
    out(f"  curvature sight line {sight:.0f} m ({where}) = {full} bays = "
        f"{full * drawn:,} tri")
    out(f"  that is {full * drawn / gate:.1f}x the gate. The Zocalo CANNOT be "
        f"drawn at full detail\n  down its own sight line; it needs a LOD chain,"
        f" and here is where it switches.")

    # Switch distances from a MEASURABLE error, not chosen: the chair frame is
    # 25 mm of tube, and below 1.5 px that is shading noise rather than form.
    # Same criterion lod.py uses for greeble relief, applied to furniture.
    f_px = (1440 / 2) / math.tan(math.radians(40.0) / 2)
    d_tube = MEASURED["chair_tube_d_m"] * f_px / 1.5
    d_chair = MEASURED["chair_w_m"] * f_px / 12.0
    d_rib = p["rib_thickness_m"] * f_px / 1.5
    out(f"\n  at 1440p and a 40 deg horizontal FOV, f = {f_px:.0f} px:")
    out(f"    the 25 mm chair tube drops under 1.5 px at {d_tube:.0f} m "
        f"({d_tube / p['bay_length_m']:.1f} bays)")
    out(f"    the 0.48 m chair drops under 12 px at {d_chair:.0f} m "
        f"({d_chair / p['bay_length_m']:.1f} bays)")
    out(f"    the 0.42 m rib holds relief to {d_rib:.0f} m, so STRUCTURE "
        f"outlives furniture by {d_rib / d_tube:.0f}x")
    out(f"  -> full chairs to {d_tube:.0f} m; a billboard to {d_chair:.0f} m; "
        f"nothing beyond.")

    out("\n  GPU instancing, over the full sight line:")
    total = 0
    for k in sorted(proto):
        n = counts[k] * full
        total += n
        out(f"    {k:<10} {proto[k]:>5,} tri x {n:>5} instances")
    out(f"    {total:,} instances from {len(proto)} MultiMeshes = "
        f"{len(proto)} draw calls,")
    out(f"    {sum(proto.values()):,} triangles resident. Placed as individual "
        f"objects that is")
    out(f"    {full * len(per):,} draw calls, against budget.py's whole-exterior "
        f"ceiling of {budget.BUDGETS['exterior_draw_calls']}.")
    # Structure materials are shared across bays, so they cost one draw call
    # each however long the run is. There is no interior draw-call gate in
    # budget.py -- only an exterior one -- and this is the number that would
    # need one.
    struct_groups = [k for k in per if not k.startswith(INSTANCED)]
    out(f"\n  draw calls for a run of ANY length: {len(struct_groups)} "
        f"structure materials + {len(proto)} MultiMeshes = "
        f"{len(struct_groups) + len(proto)}.")
    out(f"  budget.py gates draw calls for the exterior "
        f"({budget.BUDGETS['exterior_draw_calls']}) and NOT for interiors. "
        f"That gap is worth closing.")
    return {"structure": structure, "drawn": drawn, "unique": unique,
            "per_group": per, "prototypes": proto, "counts": counts,
            "bays_in_gate": n_bays, "sight_bays": full,
            "lod_switch_m": d_tube, "area_m2": area,
            "draw_calls": len(struct_groups) + len(proto)}


# ---------------------------------------------------------------------------
# Measurements no render can make
# ---------------------------------------------------------------------------
def facing_fraction(verts, tris, groups, prefix, axis, plane=None):
    """Fraction of a group's triangles whose normal points along `axis`.

    The deck, the soffit and every flat element here have exactly one correct
    facing and are invisible if it is wrong -- and invisible reads as a badly
    placed camera, not as a bug. This is a count, not a look.

    `plane` restricts the count to triangles lying at that height, which is
    what the question means once these surfaces are solids rather than sheets.
    `None` means the group's own topmost plane -- right for a pad, whose rise
    is a property of the primitive rather than something this file knows.
    """
    ax, ay, az = axis
    ks = [i for i in range(len(tris)) if groups[i].startswith(prefix)]
    if plane is None and ks:
        plane = max(verts[i][1] for k in ks for i in tris[k])
    good = total = 0
    for i, (a, b, c) in enumerate(tris):
        if not groups[i].startswith(prefix):
            continue
        if plane is not None and any(abs(verts[j][1] - plane) > 1e-9
                                     for j in (a, b, c)):
            continue
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        w = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0])
        total += 1
        if n[0] * ax + n[1] * ay + n[2] * az > 0:
            good += 1
    return good / max(1, total), total


def group_mesh(verts, tris, groups, prefix):
    """Sub-mesh of every triangle whose group starts with `prefix`."""
    idx, out_v, out_t = {}, [], []
    for i, gname in enumerate(groups):
        if not gname.startswith(prefix):
            continue
        tri = []
        for vi in tris[i]:
            if vi not in idx:
                idx[vi] = len(out_v)
                out_v.append(verts[vi])
            tri.append(idx[vi])
        out_t.append(tuple(tri))
    return out_v, out_t


def clearances(p=None):
    """Every place two systems occupy the same space, as a metre figure.

    The tram spent a session 6.43 m inside a structural spoke with both modules'
    self-tests passing, because neither asserted anything about the other. These
    are the pairs this module can get wrong, and each one is measured off the
    geometry rather than restated from the constant that produced it.
    """
    p = p or params()
    y_g, x_edge = p["gallery_y_m"], p["well_width_m"] / 2.0
    slab, f_top, f_bot = (p["gallery_slab_m"],
                          y_g - p["gallery_fascia_top_m"],
                          y_g - p["gallery_fascia_bot_m"])
    out = {}

    rib = Mesh()
    _rib(rib, p, 0.0)
    out["rib_crown_m"] = max(q[1] for q in rib.v)
    out["rib_widest_m"] = max(abs(q[0]) for q in rib.v)
    # Point-in-volume over actual vertices, against every box the gallery
    # occupies. A plan check would say the rib crosses the gallery's edge line
    # -- it does, at deck level, where the gallery is 3.6 m overhead and there
    # is nothing there. The question is whether any rib vertex is INSIDE the
    # gallery, and that is three boxes and a loop.
    boxes = ((x_edge, p["bay_width_m"] / 2, y_g - slab, y_g),      # slab
             (x_edge, x_edge + 0.45, f_bot, f_top),                # edge beam
             (x_edge + 0.46, x_edge + 0.72, f_bot, f_top))         # fascia band
    worst = -99.0
    for x, y, _z in rib.v:
        ax = abs(x)
        for x0, x1, y0, y1 in boxes:
            if x0 < ax < x1 and y0 < y < y1:
                worst = max(worst, min(ax - x0, x1 - ax, y - y0, y1 - y))
    out["rib_into_gallery_m"] = worst
    # And the clearance that matters visually: how far inboard the rib is where
    # it passes the gallery deck.
    out["rib_to_gallery_edge_m"] = x_edge - max(
        rib_profile(p, y)[1] for y in (y_g - slab, y_g))

    st = stair_flight(p)
    sv, _ = group_mesh(st.v, st.t, st.g, "zoc_stair")
    out["stair_top_y_m"] = max(q[1] for q in sv)
    out["stair_outer_x_m"] = stair_x(p) + max(q[0] for q in sv)
    out["stair_gap_to_gallery_m"] = x_edge - out["stair_outer_x_m"]
    out["stair_to_rib_m"] = stair_z0(p) - p["rib_depth_m"] / 2.0

    stall = vendor_stall(p, 0)
    out["awning_top_m"] = max(q[1] for q in stall.v)
    # LATERAL half-extent, which is the stall's own DEPTH: every stall is
    # rotated 90 degrees to face the well, so its local z becomes world x. The
    # first version measured local x and passed the well-clearance test for the
    # wrong reason while failing the wall test by 0.29 m.
    out["awning_half_w_m"] = max(abs(q[2]) for q in stall.v)
    out["awning_to_gallery_soffit_m"] = (y_g - p["gallery_slab_m"]
                                         - out["awning_top_m"])
    out["stall_awning_to_well_m"] = (p["stall_x_m"] - out["awning_half_w_m"]
                                     - x_edge)
    # The gallery-level stall has a ceiling above it and a drop beside it.
    out["gallery_stall_headroom_m"] = (p["ceiling_height_m"] - y_g
                                       - out["awning_top_m"])
    out["gallery_stall_to_edge_m"] = (p["gallery_stall_x_m"]
                                      - out["awning_half_w_m"] - x_edge)
    out["gallery_stall_to_wall_m"] = (p["bay_width_m"] / 2.0
                                      - p["gallery_stall_x_m"]
                                      - out["awning_half_w_m"])

    gal = gallery(p, 1)
    out["colonnade_headroom_m"] = min(q[1] for q in gal.v)
    return out


# ---------------------------------------------------------------------------
def write_bay(path, p=None, **kw):
    v, t, g = zocalo_bay(p, **kw)
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


def write_run(path, bays=3, p=None, **kw):
    v, t, g = zocalo_run(bays, p, **kw)
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


# ---------------------------------------------------------------------------
def _raises(fn, *a):
    try:
        fn(*a)
    except Exception:
        return True
    return False


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    p = params()

    # --- the camera solve ---------------------------------------------------
    s_chair = ref_scale_px_per_m(1057.0)
    check("solve: the chair's depth scales at the measured 543 px/m",
          abs(s_chair - 543.0) < 3.0, f"{s_chair:.1f} px/m")
    y_rail = REF_HORIZON_PX + s_chair * (REF_EYE_M - 0.75)
    check("solve: a 0.75 m feature lands on its measured row 650",
          abs(y_rail - 650.0) < 3.0, f"{y_rail:.1f} px")
    y_mid = REF_HORIZON_PX + ref_scale_px_per_m(610.0) * (REF_EYE_M - 0.75)
    check("solve: the same at the mid-ground table's depth, row 468",
          abs(y_mid - 468.0) < 4.0, f"{y_mid:.1f} px")
    fov = 2 * math.degrees(math.atan((REF_W_PX / 2) / REF_FOCAL_PX))
    check("solve: the focal length is a real television lens (25-45 deg)",
          25.0 < fov < 45.0, f"{fov:.1f} deg horizontal")
    check("solve: the eye is at a SEATED height, not standing",
          1.10 < REF_EYE_M < 1.35, f"{REF_EYE_M} m")
    d_table = REF_FOCAL_PX / (367.0 / MEASURED["table_top_d_m"])
    check("solve: the table's ellipse aspect agrees with its solved distance",
          abs(58.0 / 367.0 - (REF_EYE_M - TABLE_H_M) / d_table) < 0.012,
          f"aspect {58.0 / 367.0:.4f} vs "
          f"{(REF_EYE_M - TABLE_H_M) / d_table:.4f}")
    # Three objects whose real sizes the derivation never used.
    check("cross-check: the chair tube is a real furniture tube (20-32 mm)",
          0.020 <= MEASURED["chair_tube_d_m"] <= 0.032)
    check("cross-check: the chair is a real chair width (0.40-0.55 m)",
          0.40 <= MEASURED["chair_w_m"] <= 0.55)
    check("cross-check: the shaker is a real shaker (80-110 mm)",
          0.080 <= MEASURED["shaker_d_m"] <= 0.110)
    check("ref_scale_px_per_m refuses a row above the horizon",
          _raises(ref_scale_px_per_m, REF_HORIZON_PX - 1.0))
    check("the set's measured gallery height is recorded and NOT built",
          not (MEASURED["set_gallery_y_m"][0] <= p["gallery_y_m"]
               <= MEASURED["set_gallery_y_m"][1]),
          f"built {p['gallery_y_m']} m vs set {MEASURED['set_gallery_y_m']}")

    # --- the module's dimensions --------------------------------------------
    check("the bay is a whole number of deck pitches, all three ways",
          all(abs(x / DECK_PITCH_M - round(x / DECK_PITCH_M)) < 1e-9
              for x in (p["bay_width_m"], p["bay_length_m"],
                        p["ceiling_height_m"])),
          f"{p['bay_width_m']} x {p['bay_length_m']} x {p['ceiling_height_m']}")
    check("the height comes from class_params and is exactly two decks",
          abs(kit.class_params("concourse")["ceiling_height_m"]
              - 2 * DECK_PITCH_M) < 1e-9)
    check("the galleries and the well tile the bay's width exactly",
          abs(p["well_width_m"] + 2 * p["gallery_depth_m"]
              - p["bay_width_m"]) < 1e-9)
    check("the tile grid closes on the bay in both directions",
          abs(p["bay_length_m"] / p["tile_m"]
              - round(p["bay_length_m"] / p["tile_m"])) < 1e-9
          and abs(p["bay_width_m"] / p["tile_m"]
                  - round(p["bay_width_m"] / p["tile_m"])) < 1e-9)
    lo, hi = MEASURED["deck_tile_m_range"]
    check("the tile size is inside the range measured off the deck joints",
          lo <= p["tile_m"] <= hi, f"{p['tile_m']} m vs {lo}-{hi} m")
    check("the well matches the measured arch span within 0.2 m",
          abs(p["well_width_m"] - MEASURED["arch_span_m"]) < 0.2,
          f"{p['well_width_m']} vs {MEASURED['arch_span_m']} m")

    # --- determinism --------------------------------------------------------
    a = seating_plan(p, 3, "zocalo", 1)
    check("the seating plan is reproducible", a == seating_plan(p, 3, "zocalo", 1))
    check("a different bay gets a different plan",
          a != seating_plan(p, 4, "zocalo", 1))
    check("a different seed gets a different plan",
          a != seating_plan(p, 3, "other", 1))
    check("_u01 is in range and not degenerate",
          all(0.0 <= _u01("x", i) < 1.0 for i in range(200))
          and len({round(_u01("x", i), 12) for i in range(200)}) == 200)
    # Needles built at runtime: spelling them literally would make this
    # assertion find itself in its own source and always fail.
    src = open(os.path.abspath(__file__)).read()
    needles = ("import " + "random", "random." + "random", "str." + "__hash__")
    check("no `random` and no salted builtin hash anywhere in this module",
          not any(n in src for n in needles))

    # --- placement is legal -------------------------------------------------
    plan = seating_plan(p, 0, "zocalo", 1)
    check("the bay actually gets seating", len(plan) >= 4, str(len(plan)))
    worst = min((math.hypot(x1 - x2, z1 - z2)
                 for i, (x1, z1, *_) in enumerate(plan)
                 for (x2, z2, *_) in plan[i + 1:]), default=99.0)
    check("no two seating clusters are closer than the stated gap",
          worst >= p["cluster_gap_m"] - 1e-9, f"{worst:.3f} m")
    r_cl = p["cluster_r_m"]
    blocked = blocked_rects(p, 1)
    bad_struct = [(x, z) for x, z, *_ in plan
                  if any(x + r_cl > b0 and x - r_cl < b1
                         and z + r_cl > c0 and z - r_cl < c1
                         for b0, b1, c0, c1 in blocked)]
    check("no cluster overlaps a rib foot or the stair", not bad_struct,
          str(bad_struct[:3]))
    bad_well = [x for x, *_ in plan if abs(x) + r_cl >= p["well_width_m"] / 2.0]
    check("no cluster overhangs the open well", not bad_well,
          str([round(x, 2) for x in bad_well[:3]]))
    bad_z = [z for _, z, *_ in plan
             if not r_cl <= z <= p["bay_length_m"] - r_cl]
    check("no cluster overhangs the bay's ends", not bad_z, str(bad_z[:3]))

    # --- clearance between subsystems, measured off the built geometry ------
    cl = clearances(p)
    check("the rib's crown reaches the soffit and no further",
          abs(cl["rib_crown_m"] - p["ceiling_height_m"]) < 1e-9,
          f"{cl['rib_crown_m']:.6f} vs {p['ceiling_height_m']} m")
    check("no rib vertex is inside the gallery slab, beam or fascia",
          cl["rib_into_gallery_m"] < 0.0,
          f"deepest penetration {cl['rib_into_gallery_m']:.4f} m")
    check("the rib passes the gallery deck well clear of its edge",
          cl["rib_to_gallery_edge_m"] > 0.30,
          f"{cl['rib_to_gallery_edge_m']:.3f} m")
    # --- the rib repair, verified by the property the bug destroyed ---------
    a_r = p["well_width_m"] / 2.0
    b_r = p["ceiling_height_m"] - p["rib_thickness_m"]
    T, D = p["rib_thickness_m"], p["rib_depth_m"]
    rv, rt = rib_arch_repaired(p["well_width_m"], b_r, D, T)
    # Every vertex must lie ON or OUTSIDE the intrados ellipse. The unrepaired
    # kit offsets almost along the TANGENT, which puts most of its outer curve
    # INSIDE -- this is the direct test of that, and it needs no knowledge of
    # the emission order.
    inside = [q for q in rv
              if (q[0] / a_r) ** 2 + (q[1] / b_r) ** 2 < 1.0 - 1e-6]
    check("no rib vertex falls inside its own intrados", not inside,
          f"{len(inside)} inside, first {inside[:1]}")
    # And the volume of a section swept perpendicular to the arc, computed from
    # the ellipse rather than from the mesh: L*T + pi*T^2/2, times the depth.
    pts = [(-a_r * math.cos(math.pi * i / RIB_SEGMENTS),
            b_r * math.sin(math.pi * i / RIB_SEGMENTS))
           for i in range(RIB_SEGMENTS + 1)]
    arc = sum(math.dist(pts[i], pts[i + 1]) for i in range(RIB_SEGMENTS))
    want_vol = (arc * T + math.pi * T * T / 2.0) * D
    got_vol = signed_volume(rv, rt)
    check("the rib's volume is a section swept across the arc, not along it",
          abs(got_vol - want_vol) / want_vol < 0.10,
          f"{got_vol:+.3f} m3 vs {want_vol:.3f} expected "
          f"(the unrepaired kit gives -0.413)")
    # The formula the clearances are written against has to be the same rib.
    check("rib_profile matches the built springing exactly",
          abs(rib_profile(p, 0.0)[1] - (a_r + T)) < 1e-9,
          f"{rib_profile(p, 0.0)[1]:.6f} vs {a_r + T}")
    check("rib_profile's intrados is the ellipse at every sampled height",
          all(abs(rib_profile(p, y)[0] - a_r * math.sqrt(1 - (y / b_r) ** 2))
              < 1e-9 for y in (0.0, 1.5, 3.6, 5.5, b_r)))
    check("the stair arrives exactly at the gallery deck",
          abs(cl["stair_top_y_m"] - p["gallery_y_m"]) < 1e-9,
          f"{cl['stair_top_y_m']:.6f} m")
    check("there is no gap to step over between stair and gallery",
          abs(cl["stair_gap_to_gallery_m"]) < 1e-9,
          f"{cl['stair_gap_to_gallery_m']:.4f} m")
    check("the flight starts clear of the rib beside it",
          cl["stair_to_rib_m"] > 0.15, f"{cl['stair_to_rib_m']:.3f} m")
    check("the flight fits between two ribs",
          p["stair_risers"] * p["stair_going_m"] + p["rib_depth_m"]
          < p["rib_spacing_m"],
          f"{p['stair_risers'] * p['stair_going_m']:.2f} m run in "
          f"{p['rib_spacing_m']} m")
    check("the stall awning clears the gallery soffit above it",
          cl["awning_to_gallery_soffit_m"] > 0.15,
          f"{cl['awning_to_gallery_soffit_m']:.3f} m")
    check("no stall awning overhangs the open well",
          cl["stall_awning_to_well_m"] > 0.0,
          f"{cl['stall_awning_to_well_m']:.3f} m")
    check("the gallery-level stall fits under the soffit",
          cl["gallery_stall_headroom_m"] > 0.30,
          f"{cl['gallery_stall_headroom_m']:.3f} m")
    check("no gallery stall overhangs the well or fouls the side wall",
          cl["gallery_stall_to_edge_m"] > 0.0
          and cl["gallery_stall_to_wall_m"] > 0.0,
          f"edge {cl['gallery_stall_to_edge_m']:.3f} m, "
          f"wall {cl['gallery_stall_to_wall_m']:.3f} m")
    check("nothing the gallery hangs is at head height in the colonnade",
          cl["colonnade_headroom_m"] >= 2.4,
          f"{cl['colonnade_headroom_m']:.2f} m")

    # --- geometry -----------------------------------------------------------
    v, t, g = zocalo_bay(p, index=0)
    check("there is one group name per triangle", len(g) == len(t))
    check("no triangle index is out of range",
          all(0 <= i < len(v) for tri in t for i in tri))
    check("no degenerate triangles", all(len(set(tri)) == 3 for tri in t))

    # MEASURED ON THE FACE YOU CAN SEE. Every one of these is a closed solid
    # now -- the deck a slab, the pools and the lit strip `deck_pad`s, the
    # soffit a slab -- so their undersides face the other way and must. The
    # question worth asking is whether the surface a player looks at faces
    # them, so each is restricted to its own visible plane; measured over the
    # whole solid the test says "89% of the deck faces up", which is a true
    # statement about a correct deck and a useless one.
    for prefix, axis, what, plane in (
            ("zoc_deck_", (0, 1, 0), "the tiled deck", 0.0),
            ("zoc_downlight", (0, 1, 0), "the downlights", None),
            ("zoc_soffit", (0, -1, 0), "the soffit", p["ceiling_height_m"]),
            ("zoc_rib_cap", (0, -1, 0), "the rib springings", None)):
        frac, n = facing_fraction(v, t, g, prefix, axis, plane=plane)
        check(f"{what} faces the right way ({n} tri)", frac > 0.999,
              f"{frac:.3f} of {n}")

    closed = ("table", "chair", "service", "stall", "stair", "neon sign", "rib")
    rib_mesh = Mesh()
    _rib(rib_mesh, p, 0.0)
    for name, mesh in (("table", pedestal_table(p)),
                       ("chair", cafe_chair(p)),
                       ("service", drinks_service()),
                       ("stall", vendor_stall(p, 0)),
                       ("stall variant 3", vendor_stall(p, 3)),
                       ("stair", stair_flight(p)),
                       ("neon sign", neon_sign(p)),
                       ("rib", rib_mesh),
                       ("gallery +x", gallery(p, 1)),
                       ("gallery -x", gallery(p, -1))):
        vol = signed_volume(mesh.v, mesh.t)
        check(f"{name} is not inside-out", vol > 0.0, f"volume {vol:+.5f}")
        bnd, nm = it.boundary_edges(mesh.v, mesh.t)
        if name.split(" variant")[0] in closed:
            check(f"{name} is closed", len(bnd) == 0, f"{len(bnd)} open edges")
        check(f"{name} has no non-manifold edges", len(nm) == 0,
              f"{len(nm)} edges used by three or more triangles")

    # The stair's cap triangulation. A fan anchored at the wrong vertex still
    # reports the right volume AND the right closure AND the right signed area,
    # because fan triangulation cancels: triangles that fall outside come out
    # negative and net to the correct total. What does NOT cancel is the sum of
    # their ABSOLUTE areas, so that is what this compares -- unsigned fan area
    # against the outline's shoelace area, equal only if every triangle is
    # inside the profile and none overlaps another.
    #
    # A centroid-in-profile test was tried first and did NOT catch it: with the
    # fan anchored at the bottom-front corner the worst triangle's centroid
    # lands exactly ON the profile, at 2.400 m against a 2.400 m limit.
    sm = stair_flight(p)
    hw = p["stair_width_m"] / 2.0
    out = stair_outline(p)
    shoelace = abs(sum(out[i][0] * out[(i + 1) % len(out)][1]
                       - out[(i + 1) % len(out)][0] * out[i][1]
                       for i in range(len(out)))) / 2.0
    fan = 0.0
    for tri in sm.t:
        q = [sm.v[k] for k in tri]
        if not all(abs(qq[0] - hw) < 1e-9 for qq in q):
            continue                                   # the +x cap only
        fan += abs((q[1][2] - q[0][2]) * (q[2][1] - q[0][1])
                   - (q[2][2] - q[0][2]) * (q[1][1] - q[0][1])) / 2.0
    check("the stair cap tiles its outline without spilling outside it",
          abs(fan - shoelace) < 1e-9,
          f"fan area {fan:.6f} m2 vs outline {shoelace:.6f} m2")

    # --- the bay's open edges, reconciled against a declared list ------------
    bnd, nm = it.boundary_edges(v, t)
    nx = int(round(p["bay_width_m"] / p["tile_m"]))
    nz = int(round(p["bay_length_m"] / p["tile_m"]))
    n_down = p["downlights_per_bay"]
    # WHAT THIS USED TO DECLARE, and why declaring it was not enough. The bay
    # carried 2*(nx+nz) edges round the tiled deck, 4 round the lit strip,
    # 20 round every one of the eight downlight pools and 4 on the soffit --
    # 464 in all, every one of them reconciled against a written list and every
    # one of them still a hole in whatever deck this room is composed onto. A
    # declared hole shows the background exactly as an undeclared one does.
    #
    # The list is kept as the negative control: strip the deck slab's skirt and
    # underside back off and the count has to come back to the perimeter.
    check("the bay is a closed surface", not bnd,
          f"{len(bnd)} open edges, first at {bnd[:1]}")
    bare = [tri for k, tri in enumerate(t)
            if not (g[k] == "zoc_deck_tile"
                    and min(v[i][1] for i in tri) < -1e-6)]
    check("...and taking the deck slab's skirt away brings the hole back",
          len(it.boundary_edges(v, bare)[0]) == 2 * (nx + nz),
          f"{len(it.boundary_edges(v, bare)[0])} open with the skirt removed, "
          f"against the {2 * (nx + nz)} tile joints round the field")
    check("...and the pools and the strip are closed too, not just declared",
          len(kit.boundary_edges(*kit.downlight_pool())[0]) == 0
          and len(kit.boundary_edges(*kit.deck_strip(0.9, 10.0))[0]) == 0,
          f"they used to contribute {n_down * 20 + 4} of the 464")
    # Non-manifold edges in the assembled bay must be exactly the ones the KIT
    # brings with it. wall_assembly lays proud plates whose edges coincide with
    # the substrate's, and interior_kit.py is not this module's to edit -- so
    # the assertion is against the measured inherited count rather than zero,
    # and it still fails the moment this module introduces one of its own.
    kit.reset_tags()
    wv, wt = kit.wall_assembly(p["bay_length_m"], p["ceiling_height_m"], p)
    inherited = 2 * len(it.boundary_edges(wv, wt)[1])
    kit.reset_tags()
    check("the bay adds no non-manifold edge of its own",
          len(nm) == inherited,
          f"{len(nm)} in the bay, {inherited} inherited from "
          f"interior_kit.wall_assembly")

    # --- the seam between bays ----------------------------------------------
    v2, t2, g2 = zocalo_run(2, p)
    l = p["bay_length_m"]
    dv1, _ = group_mesh(v, t, g, "zoc_deck_")
    dv2, _ = group_mesh(v2, t2, g2, "zoc_deck_")
    face1 = sorted({round(q[0], 6) for q in dv1 if abs(q[2] - l) < 1e-9})
    face2 = sorted({round(q[0], 6) for q in dv2 if abs(q[2] - l) < 1e-9})
    mismatch = [q for q in face1 if q not in face2][:3]
    check("the deck's tile joints are continuous across the bay seam",
          face1 == face2 and len(face1) == nx + 1,
          f"{len(face1)} joints vs {len(face2)}, expected {nx + 1}; "
          f"not shared: {mismatch}")
    expect = [round(-p["bay_width_m"] / 2 + i * p["tile_m"], 6)
              for i in range(nx + 1)]
    check("the seam's joints sit on the tile grid, not near it",
          face1 == expect, f"{face1[:3]} vs {expect[:3]}")
    # Ribs must stay on one pitch across the seam, with none doubled.
    rib_z = sorted(round(k * p["rib_spacing_m"] + i * l, 6)
                   for i in range(2) for k in range(2))
    gaps = {round(rib_z[i + 1] - rib_z[i], 6) for i in range(len(rib_z) - 1)}
    check("rib spacing is uniform across the bay seam",
          gaps == {round(p["rib_spacing_m"], 6)}, str(sorted(gaps)))
    check("no rib is emitted twice at the seam", len(rib_z) == len(set(rib_z)))

    # --- budget -------------------------------------------------------------
    rep = budget_report(p, out=lambda *a: None)
    gate = budget.INTERIOR["visible_set_tris"]
    check("a bay's structure fits the interior visible-set gate",
          rep["structure"] < gate, f"{rep['structure']:,} vs {gate:,}")
    check("instancing is worth doing: drawn well exceeds unique",
          rep["drawn"] > rep["unique"] * 1.15,
          f"{rep['drawn']:,} drawn vs {rep['unique']:,} unique")
    check("the LOD switch distance is derived and lands inside the run",
          5.0 < rep["lod_switch_m"] < 60.0, f"{rep['lod_switch_m']:.1f} m")
    check("the sight line demands more bays than the gate affords",
          rep["sight_bays"] > rep["bays_in_gate"],
          f"{rep['sight_bays']} vs {rep['bays_in_gate']}")

    # --- seams -------------------------------------------------------------
    # A run of bays must cost no more non-manifold geometry than the same bays
    # standing alone: the seam itself must contribute NOTHING. Before the weld
    # in zocalo_run() it contributed 152 edges per seam -- every longitudinal
    # member is emitted per bay as a closed solid, so adjacent bays met face to
    # face and every edge around that face was shared by four triangles, and
    # the rail was emitted twice over. Both are invisible in a render and both
    # z-fight in the engine.
    import interior as _it
    per_bay = None
    for n in (1, 2, 3, 4):
        rv, rt, _rg = zocalo_run(n)
        _b, nm = _it.boundary_edges(rv, rt)
        if per_bay is None:
            per_bay = len(nm)
        check(f"run of {n} bays adds nothing non-manifold at its seams",
              len(nm) == per_bay * n,
              f"{len(nm)} against {per_bay} x {n} = {per_bay * n}")
    # The weld must CLOSE, not open. A standalone bay has two open ends; joining
    # two bays should retire one end from each, so the marginal cost of a bay in
    # a run is strictly less than a bay on its own, and constant.
    bounds = [len(_it.boundary_edges(*zocalo_run(n)[:2])[0]) for n in (1, 2, 3, 4)]
    steps = [bounds[i + 1] - bounds[i] for i in range(3)]
    check("each added bay costs the same boundary, so seams are uniform",
          len(set(steps)) == 1, str(steps))
    # A standalone bay used to have two open ends, so joining two retired one
    # from each and the marginal cost of a bay was strictly less than a bay on
    # its own. Both numbers are ZERO now -- the bay is a closed solid and a run
    # of them is one closed solid -- so the strict inequality has nothing left
    # to say and the property worth asserting is the stronger one it was a
    # proxy for: a run of any length is closed, and adding a bay keeps it that
    # way. `steps` above already asserts uniformity.
    check("joining bays closes boundary rather than opening it",
          bounds == [0, 0, 0, 0], f"open edges for 1..4 bays: {bounds}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    if "--budget" in sys.argv:
        budget_report()
        sys.exit(0)
    if "--obj" in sys.argv:
        i = sys.argv.index("--obj")
        n = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 1
        print(write_run(sys.argv[i + 1], bays=n))
        sys.exit(0)
    sys.exit(_selftest())
