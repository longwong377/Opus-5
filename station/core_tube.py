"""The station's axis: the core shuttle tube and the hubs at each drum end cap.

`interior.py` already builds everything that *points* at the axis -- the three
radial spokes, the three guideway trusses, and an end cap with a 50.1 m aperture
punched through its middle for the axis to pass. The axis itself was a hole.

Three things are sourced and are not invention here:

  * **There is an axial structure and it is named.** The Security Manual
    sectional schematic (authority 3) draws a slender centreline duct running
    the whole length of the drum and on forward through Red and Blue, labelled
    **"CORE TRANSFER SHUTTLE"**. It is the only source that shows the axis in
    section, and it is the only source that gives the tube a *thickness*.
  * **The tube is articulated, not extruded.** `Babylon_5_2-22_33a` (authority 1)
    shows smooth grey barrel sections separated by tight groups of fine raised
    rings, several of them warm-coloured -- rust and orange bands round an
    otherwise grey tube -- and one open lattice cage bay.
    `09-garden-core-and-transit/garden.png` shows the same barrel-and-collar
    signature on a tube of the same family from the drum floor.
  * **The hub is a flanged cone with radial fins.** `Babylon_5_2-22_34b` looks
    down the drum at the fore cap: a stepped conical bell wrapped round the tube
    at the cap's centre, a cog of fine radial teeth round it, heavy bevelled
    fairings and a cranked bright brace landing on it, and grey conduits leaving
    it with collar bands.

What the footage does **not** settle is which tube is which. `33a`/`34b` show a
banded tube running to the cap hub, and that is consistent with the axis *and*
with a radial spoke seen end-on -- `interior.py:spoke()` already reads it as the
spoke. The signature is the same either way, which is why both use it; the
ambiguity is recorded rather than resolved.

Coordinates and winding: this geometry is seen from **outside**, because the
viewer is out in the drum looking in at the axis. That is the opposite of
`interior.py:drum_interior()`, whose faces point at the axis because the viewer
is inside the drum shell. Getting it wrong here renders black rather than
erroring, so `_outward_fraction()` measures it and the builders refuse to return
geometry that would vanish -- the same guard, mirrored.
"""
import math

import interior as it

# ---------------------------------------------------------------------------
# Tube radius -- the one dimension that is measured rather than chosen.
#
# The sectional schematic draws the core transfer shuttle as a duct with two
# walls and a centreline. Measured off the original 1080x339 webp at seven
# columns through the drum, the walls sit at y = 165-166 and 171-172 with the
# centreline at 168-169, against the drum's innermost long deck lines at 121-122
# and 215-216. That gives
#
#     tube half-thickness  3.0 px (wall centres) to 3.5 px (outer edges)
#     drum half-height     47.0 px
#     ratio                0.064 to 0.075
#
# The ruling that applies is `00-MASTER.md` "Radial spacing" and CONFLICTS.md's
# C-004 UPDATE item 3: this sheet's **vertical** scale is exaggerated ~2x (the
# drum reads L/D 1.46 where the framework gives ~3.1), so no radial dimension
# may be measured off it. (Not C-005, which this comment originally cited and
# which is a different defect entirely -- a horizontal splice in the scale bar,
# 127.7 px/km on the left group against 125.7 on the right. Corrected after an
# adversarial review caught the misattribution; the argument below was always
# aimed at the vertical ruling, but citing the wrong entry would have let a
# future reader check the wrong thing and conclude the defence held.)
#
# A uniform vertical exaggeration cancels in a *ratio* of two vertical
# quantities, which is why a ratio is what is taken here and why the ruling does
# not bite. What does bite is resolution: a 7 px duct on a 339 px scan is three
# or four pen widths, so this is a coarse reading and it is quoted as a range.
#
# 0.070 of the canon 278.3 m floor radius is 19.5 m.
CORE_TUBE_R_FRAC = 0.070
CORE_TUBE_R_M = 19.5

TUBE_SIDES = 16               # 3.8 m facets at 19.5 m radius

# Articulation, from 33a. Collar groups sit at what read as section joints, with
# smooth barrel between. The frame shows groups of six to nine fine rings spaced
# one and a half to three tube diameters apart; four rings at 130 m (3.3
# diameters) is what the drum's triangle budget affords across 2.8 km of tube.
SECTION_M = 130.0
COLLAR_RINGS = 4
COLLAR_RING_W_M = 3.2         # one fine ring, crest to crest
COLLAR_RING_RISE_M = 1.4
COLLAR_GAP_M = 2.0            # flat between two rings of a group
COLLAR_BASE_RISE_M = 0.7      # the whole group stands slightly proud

# The open cage bay. 33a shows one: a section where the skin gives way to a
# lattice with square voids and a pale frame. Sparse, because it is one instance
# in one frame and `interior.py:spoke()` already uses the same motif.
LATTICE_EVERY = 8             # one bay every N sections
LATTICE_LEN_M = 26.0
LATTICE_RIBS = 8
LATTICE_DIP_M = 3.0           # how far the skin steps in under the cage

# The hub. `34b` gives the form -- stepped conical bell, cog of fine radial
# teeth -- and no scale whatever, so every number here is extrapolation.
HUB_FLANGES = 4               # stepped rings between tube and aperture
HUB_LEN_M = 60.0              # axial run of the flare
HUB_NOSE_M = 18.0             # collar carried on past the cap plane
HUB_FINS = 24                 # half the end cap's 48-fold symmetry
HUB_FIN_W_M = 1.8
HUB_PORT_R_M = 27.0           # spoke port reach; see _spoke_reach()
HUB_LAMP_R_M = 1.5

# Where a spoke meets the tube away from a cap: 34b's bell-and-spar node, out in
# the middle of the drum with the tube running through its centre.
NODE_FLANGES = 3
NODE_SPARS = 12
NODE_BODY_R_M = 40.5
NODE_PAD_R_M = 45.0

# Groups whose faces form the axis's outer envelope. Everything else is either a
# closed box (checked by signed volume) or a bore that legitimately faces the
# axis, so a blanket "all normals point outward" test would be wrong.
ENVELOPE_GROUPS = ("core_tube_barrel", "core_tube_collar", "core_tube_band",
                   "core_tube_band_warm", "core_hub_bell", "core_node_bell")


def _fnv1a(key):
    """64-bit FNV-1a over a stable key.

    Written out rather than using `hash()`: Python salts `str.__hash__` per
    process, so the tube's warm bands would land in different places on every
    regeneration and the OBJ would never be byte-identical twice.
    """
    h = 0xcbf29ce484222325
    for b in key.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


# ---------------------------------------------------------------------------
# Where the axis has to fit
# ---------------------------------------------------------------------------

def aperture(schema, profile, sector, end="fore"):
    """The hole `interior.py:drum_end_cap()` leaves for the axis.

    Radius and axial position both come from the cap builder rather than from a
    constant here, so a change to the cap's dish or core radius moves the hub
    with it instead of silently opening a gap round the tube.
    """
    r0 = it.sector_radius(schema, profile, sector)
    core_u = schema["interior_topology"]["provisional_rings"][-1]["r_outer"]
    ex = schema["sectors"]["extents_m"][sector]
    z_base = ex["z1"] if end == "fore" else ex["z0"]
    out = 1.0 if end == "fore" else -1.0
    # Same dish as drum_end_cap(): sagitta * (1 - u^2), measured outward.
    dish = it.ENDCAP_DISH * r0 * (1.0 - core_u * core_u)
    return {
        "end": end,
        "radius_m": core_u * r0,
        "z_m": z_base + out * dish,
        "out": out,
        "dish_m": dish,
        "drum_r_m": r0,
    }


def _spoke_reach(schema, profile, sector):
    """How far in toward the axis `interior.py`'s spokes actually come.

    `drum_spokes()` runs a spoke from the sub-floor stack to the *mid-radius* of
    the core ring, which is 25.0 m -- it stops short of the axis rather than
    reaching it. Anything the tube presents to a spoke therefore has to reach
    out past that number or the two subsystems leave a hole between them.
    """
    rings = it.ring_radii(schema, profile, sector)
    core = next(i for i, r in enumerate(rings) if r["kind"] == "core")
    return rings[core]["r_mid"]


def spoke_z(schema, sector):
    """The z `interior.py:drum_spokes()` puts its spokes at by default."""
    ex = schema["sectors"]["extents_m"][sector]
    return (ex["z0"] + ex["z1"]) / 2.0


def tube_span(schema, profile, sector, overhang_m=40.0):
    """Aft and fore ends of the tube.

    The tube has to be *through* each cap, not up against it: the cap dishes
    outward by 48 m at the aperture, so a tube stopping at the sector extent
    would stop 48 m short of the hole it is meant to pass through and leave the
    drum open to space down the middle.
    """
    a = aperture(schema, profile, sector, "aft")
    f = aperture(schema, profile, sector, "fore")
    return (a["z_m"] - overhang_m, f["z_m"] + overhang_m)


# ---------------------------------------------------------------------------
# Primitives. Every one emits a closed solid, so watertightness is a property of
# construction and the self-test only has to confirm it has not been lost.
# ---------------------------------------------------------------------------

def _ring_pts(r, z, sides):
    return [(r * math.cos(2 * math.pi * k / sides),
             r * math.sin(2 * math.pi * k / sides), z) for k in range(sides)]


def _band(verts, tris, groups, z0, r0, z1, r1, sides, group):
    """One revolved band between two (z, r) stations.

    Wound so the normal points away from the axis when the stations run in
    increasing z along the outer surface of the solid. Every other revolved
    piece in this module is built from this, which is why the winding argument
    only has to be made once.
    """
    b = len(verts)
    verts.extend(_ring_pts(r0, z0, sides))
    verts.extend(_ring_pts(r1, z1, sides))
    for k in range(sides):
        k2 = (k + 1) % sides
        tris.append((b + k, b + k2, b + sides + k2))
        tris.append((b + k, b + sides + k2, b + sides + k))
        groups.extend([group, group])


def _disc(verts, tris, groups, z, r, sides, facing, group):
    """Flat cap closing a revolved run. `facing` is +1 for +z, -1 for -z."""
    b = len(verts)
    verts.append((0.0, 0.0, z))
    verts.extend(_ring_pts(r, z, sides))
    for k in range(sides):
        k2 = (k + 1) % sides
        if facing > 0:
            tris.append((b, b + 1 + k, b + 1 + k2))
        else:
            tris.append((b, b + 1 + k2, b + 1 + k))
        groups.append(group)


def _revolve_open(verts, tris, groups, stations, band_groups, sides, cap_group):
    """A run of stations revolved and closed with a disc at each end."""
    for i in range(len(stations) - 1):
        (z0, r0), (z1, r1) = stations[i], stations[i + 1]
        _band(verts, tris, groups, z0, r0, z1, r1, sides, band_groups[i])
    _disc(verts, tris, groups, stations[0][0], stations[0][1], sides, -1,
          cap_group)
    _disc(verts, tris, groups, stations[-1][0], stations[-1][1], sides, +1,
          cap_group)


def _revolve_loop(verts, tris, groups, loop, sides):
    """A closed (z, r, group) polygon revolved into a closed surface.

    Used for the hub bell and the node body, which wrap round the tube and have
    a bore rather than a solid centre. Each point carries the group of the band
    that *starts* at it, so the group travels with the band through the
    normalisation below instead of being a parallel list that has to be
    re-indexed by hand -- which is how the hub's bore first came out tagged as
    envelope and tripped `_guard`.

    The loop is normalised to the winding `_band` expects, so an aft hub --
    whose loop is the fore one mirrored in z, and therefore traversed the other
    way round -- comes out facing outward without the caller having to think
    about it. That mirroring is exactly the mistake this exists to make
    impossible.
    """
    n = len(loop)
    area2 = sum(loop[i][0] * loop[(i + 1) % n][1]
                - loop[(i + 1) % n][0] * loop[i][1] for i in range(n))
    if area2 > 0:
        # Reversed band j runs loop[n-1-j] -> loop[n-2-j], i.e. it is the old
        # band n-2-j walked backwards, so it inherits that band's group.
        loop = [(loop[n - 1 - j][0], loop[n - 1 - j][1],
                 loop[(n - 2 - j) % n][2]) for j in range(n)]
    for i in range(n):
        z0, r0, g = loop[i]
        z1, r1, _ = loop[(i + 1) % n]
        _band(verts, tris, groups, z0, r0, z1, r1, sides, g)


def _box(verts, tris, groups, front, back, group):
    """A closed hexahedron. `front` is four corners CCW seen from outside the
    front face; `back[i]` sits behind `front[i]`."""
    b = len(verts)
    verts.extend(front)
    verts.extend(back)
    tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3),
                 (b + 4, b + 6, b + 5), (b + 4, b + 7, b + 6)])
    for i in range(4):
        j = (i + 1) % 4
        tris.append((b + i, b + 4 + i, b + 4 + j))
        tris.append((b + i, b + 4 + j, b + j))
    groups.extend([group] * 12)


def _beam(verts, tris, groups, p0, p1, w, h, group):
    """A box section from p0 to p1. The hub's braces are not axis-aligned, so
    they cannot be built from axis-aligned boxes."""
    ax = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in ax)) or 1.0
    ax = [c / L for c in ax]
    ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = [ax[1] * ref[2] - ax[2] * ref[1],
         ax[2] * ref[0] - ax[0] * ref[2],
         ax[0] * ref[1] - ax[1] * ref[0]]
    ul = math.sqrt(sum(c * c for c in u)) or 1.0
    u = [c / ul for c in u]
    v = [ax[1] * u[2] - ax[2] * u[1],
         ax[2] * u[0] - ax[0] * u[2],
         ax[0] * u[1] - ax[1] * u[0]]
    front = [tuple(p1[i] + su * u[i] * w / 2 + sv * v[i] * h / 2
                   for i in range(3))
             for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    back = [tuple(p0[i] + su * u[i] * w / 2 + sv * v[i] * h / 2
                  for i in range(3))
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    _box(verts, tris, groups, front, back, group)


def _radial_slab(verts, tris, groups, angle_deg, r0, r1, z0, z1, half_w, group):
    """A fin or pad standing radially off the axis at one angle."""
    a = math.radians(angle_deg)
    er = (math.cos(a), math.sin(a), 0.0)
    et = (-math.sin(a), math.cos(a), 0.0)

    def pt(r, t, z):
        return (er[0] * r + et[0] * t, er[1] * r + et[1] * t, z)

    front = [pt(r1, -half_w, z0), pt(r1, half_w, z0),
             pt(r1, half_w, z1), pt(r1, -half_w, z1)]
    back = [pt(r0, -half_w, z0), pt(r0, half_w, z0),
            pt(r0, half_w, z1), pt(r0, -half_w, z1)]
    _box(verts, tris, groups, front, back, group)


# ---------------------------------------------------------------------------
# The tube
# ---------------------------------------------------------------------------

def tube_stations(z0, z1):
    """The tube's (z, r) profile and the group of each band between stations.

    All the articulation lives here rather than in separate collar solids, so
    the tube is a single closed surface of revolution: no interior faces for a
    depth-sorted renderer to draw over the barrel in front, and watertightness
    is not something the caller has to maintain.
    """
    length = z1 - z0
    n = max(1, int(round(length / SECTION_M)))
    seg = length / n
    collar_len = (COLLAR_RINGS * COLLAR_RING_W_M
                  + (COLLAR_RINGS - 1) * COLLAR_GAP_M)

    st = [(z0, CORE_TUBE_R_M)]
    grp = []
    collars, cages = [], []

    def add(z, r, g):
        st.append((z, r))
        grp.append(g)

    for i in range(n):
        za = z0 + seg * i
        zc = za + seg - collar_len          # where this section's collar starts

        if i % LATTICE_EVERY == LATTICE_EVERY // 2 and zc - za > 3 * LATTICE_LEN_M:
            # An open cage bay: the skin steps in and a separate frame is built
            # over the dip by cage_frames(). Keeping the dip in the lathe means
            # the pressure envelope stays closed even where the fairing is open.
            zl = za + (zc - za - LATTICE_LEN_M) / 2.0
            add(zl, CORE_TUBE_R_M, "core_tube_barrel")
            add(zl, CORE_TUBE_R_M - LATTICE_DIP_M, "core_tube_collar")
            add(zl + LATTICE_LEN_M, CORE_TUBE_R_M - LATTICE_DIP_M,
                "core_tube_barrel")
            add(zl + LATTICE_LEN_M, CORE_TUBE_R_M, "core_tube_collar")
            cages.append(zl)

        add(zc, CORE_TUBE_R_M, "core_tube_barrel")

        base = CORE_TUBE_R_M + COLLAR_BASE_RISE_M
        add(zc, base, "core_tube_collar")
        z = zc
        for k in range(COLLAR_RINGS):
            # Warm rings are the rust and orange bands of 33a. Which rings are
            # warm is keyed through FNV-1a rather than a Python hash so the mesh
            # regenerates byte-identically.
            warm = _fnv1a(f"corering|{i}|{k}") % 3 == 0
            g = "core_tube_band_warm" if warm else "core_tube_band"
            add(z + COLLAR_RING_W_M / 2.0, base + COLLAR_RING_RISE_M, g)
            z += COLLAR_RING_W_M
            add(z, base, g)
            if k < COLLAR_RINGS - 1:
                z += COLLAR_GAP_M
                add(z, base, "core_tube_collar")
        add(z, CORE_TUBE_R_M, "core_tube_collar")
        collars.append(zc)

    return st, grp, collars, cages


def core_tube(schema, profile, sector, z_span=None):
    """The axial tube over the drum's length, through both cap apertures."""
    z0, z1 = z_span if z_span else tube_span(schema, profile, sector)
    st, grp, collars, cages = tube_stations(z0, z1)

    verts, tris, groups = [], [], []
    parts = []
    _revolve_open(verts, tris, groups, st, grp, TUBE_SIDES, "core_tube_end")
    parts.append(("tube", 0, len(tris)))

    # The cage frames. Two ring frames and a set of longitudinal ribs over each
    # dip, so the bay reads as an open structure rather than as a waist.
    for zl in cages:
        for zf in (zl, zl + LATTICE_LEN_M):
            b = len(tris)
            r_i, r_o = CORE_TUBE_R_M - LATTICE_DIP_M, CORE_TUBE_R_M + 0.4
            loop = [(zf - 1.1, r_o, "core_tube_cage"),
                    (zf + 1.1, r_o, "core_tube_cage"),
                    (zf + 1.1, r_i, "core_tube_cage"),
                    (zf - 1.1, r_i, "core_tube_cage")]
            _revolve_loop(verts, tris, groups, loop, TUBE_SIDES)
            parts.append(("cage_frame", b, len(tris)))
        for k in range(LATTICE_RIBS):
            a = 360.0 * k / LATTICE_RIBS
            b = len(tris)
            _radial_slab(verts, tris, groups, a,
                         CORE_TUBE_R_M - LATTICE_DIP_M, CORE_TUBE_R_M,
                         zl + 1.1, zl + LATTICE_LEN_M - 1.1, 0.8,
                         "core_tube_cage")
            parts.append(("cage_rib", b, len(tris)))

    _guard(verts, tris, groups, "core_tube")
    return verts, tris, {
        "sector": sector,
        "z0": round(z0, 1), "z1": round(z1, 1),
        "length_m": round(z1 - z0, 1),
        "radius_m": CORE_TUBE_R_M,
        "sections": len(collars),
        "collar_z": collars,
        "cage_bays": len(cages),
        "triangles": len(tris),
        "groups": groups,
        "parts": parts,
    }


# ---------------------------------------------------------------------------
# The hub at each cap
# ---------------------------------------------------------------------------

def core_hub(schema, profile, sector, end="fore"):
    """The structure where the tube passes through one drum end cap.

    Four things, all of them in `34b`:

      * a **stepped conical bell** flaring from the tube out to the cap's
        aperture, so the hub closes the hole rather than leaving an annular slot
        round the tube;
      * a **cog of fine radial fins** round the widest flange;
      * three **truss saddles** with cranked braces reaching out to where
        `interior.py`'s guideway truss chords end. This is what makes "the hub
        receives the trusses" a geometric fact rather than a caption: the brace
        tip is asserted against `TRUSS_RADIUS_FRAC`, so if either number moves
        the two stop meeting and the self-test says so;
      * three **spoke ports** on the collar inboard of the flare.

    The brace runs from the aperture out to the truss chord, and the cap dishes
    outward faster than the brace does, so the brace stays on the drum side of
    the cap the whole way. That is checked rather than assumed.

    Not built: the grey conduits `34b` shows leaving the hub with collar bands.
    Whatever they carry -- power, coolant, atmosphere -- belongs to a services
    pass that does not exist yet, and guessing three of them here would be
    decoration standing where real routing has to go.
    """
    ap = aperture(schema, profile, sector, end)
    out = ap["out"]
    r_ap = ap["radius_m"]
    z_ap = ap["z_m"]
    r0 = ap["drum_r_m"]

    verts, tris, groups = [], [], []
    parts = []

    # --- the bell ----------------------------------------------------------
    # Local coordinates run outboard-positive; mapping through `out` mirrors the
    # aft hub, and _revolve_loop re-normalises the winding that mirroring flips.
    step = HUB_LEN_M / HUB_FLANGES
    r_bore = CORE_TUBE_R_M - 0.6         # sleeves over the tube, no z-fighting
    outer = [(-HUB_LEN_M, CORE_TUBE_R_M, "core_hub_bell")]
    for k in range(HUB_FLANGES):
        r = CORE_TUBE_R_M + (r_ap - CORE_TUBE_R_M) * (k + 1) / HUB_FLANGES
        outer.append((-HUB_LEN_M + k * step, r, "core_hub_bell"))
        outer.append((-HUB_LEN_M + (k + 1) * step, r, "core_hub_bell"))
    outer.append((HUB_NOSE_M, r_ap, "core_hub_bell"))
    # The bore: the one surface of the hub that faces the axis on purpose, and
    # therefore the one that must be kept out of the envelope test.
    outer.append((HUB_NOSE_M, r_bore, "core_hub_bore"))
    outer.append((-HUB_LEN_M, r_bore, "core_hub_bell"))
    loop = [(z_ap + out * lz, lr, g) for lz, lr, g in outer]
    b = len(tris)
    _revolve_loop(verts, tris, groups, loop, TUBE_SIDES)
    parts.append(("hub_bell", b, len(tris)))

    # --- the cog of fins ---------------------------------------------------
    r_fin_in = CORE_TUBE_R_M + (r_ap - CORE_TUBE_R_M) * (HUB_FLANGES - 1) / HUB_FLANGES
    for k in range(HUB_FINS):
        a = 360.0 * (k + 0.5) / HUB_FINS
        za, zb = sorted((z_ap + out * (-step * 0.9), z_ap + out * HUB_NOSE_M))
        b = len(tris)
        _radial_slab(verts, tris, groups, a, r_fin_in, r_ap + 0.8, za, zb,
                     HUB_FIN_W_M / 2.0, "core_hub_fin")
        parts.append(("hub_fin", b, len(tris)))

    # --- truss saddles, braces and their light runs ------------------------
    r_truss = r0 * it.TRUSS_RADIUS_FRAC
    ex = schema["sectors"]["extents_m"][sector]
    z_truss = ex["z1"] if end == "fore" else ex["z0"]
    saddles, braces = [], []
    for i in range(it.TRUSS_COUNT):
        a = 360.0 * i / it.TRUSS_COUNT
        ar = math.radians(a)
        b = len(tris)
        # A buttress standing on the middle flanges and running out to the
        # aperture lip, which is where the brace roots. It stops AT r_ap rather
        # than proud of it: anything wider is inside the cap's innermost course,
        # and the drum's open volume is authority 1 -- the axis does not get to
        # grow into it.
        _radial_slab(verts, tris, groups, a, r_ap - 17.0, r_ap,
                     *sorted((z_ap + out * -step * 2.13,
                              z_ap + out * -step * 0.4)), half_w=8.0,
                     group="core_hub_saddle")
        parts.append(("hub_saddle", b, len(tris)))
        saddles.append(a)

        root = (r_ap * math.cos(ar), r_ap * math.sin(ar), z_ap)
        tip = (r_truss * math.cos(ar), r_truss * math.sin(ar), z_truss)
        for lat in (-it.TRUSS_CHORD_M, it.TRUSS_CHORD_M):
            off = (-math.sin(ar) * lat, math.cos(ar) * lat, 0.0)
            p0 = tuple(root[j] + off[j] for j in range(3))
            p1 = tuple(tip[j] + off[j] for j in range(3))
            b = len(tris)
            _beam(verts, tris, groups, p0, p1, 4.4, 4.4, "core_hub_brace")
            parts.append(("hub_brace", b, len(tris)))
        # The light run 34b shows beside the truss, carried on down the brace.
        # Emissive rather than a fitting: it has to spill onto the cap.
        lat = it.TRUSS_CHORD_M + 3.0
        off = (-math.sin(ar) * lat, math.cos(ar) * lat, 0.0)
        b = len(tris)
        _beam(verts, tris, groups,
              tuple(root[j] + off[j] for j in range(3)),
              tuple(tip[j] + off[j] for j in range(3)),
              HUB_LAMP_R_M * 2, HUB_LAMP_R_M * 2, "core_hub_lamp")
        parts.append(("hub_lamp", b, len(tris)))
        braces.append((a, r_truss, z_truss))

    # --- spoke ports -------------------------------------------------------
    ports = []
    for i in range(it.SPOKE_COUNT):
        a = 360.0 * i / it.SPOKE_COUNT
        za, zb = sorted((z_ap + out * -HUB_LEN_M * 0.92,
                         z_ap + out * -HUB_LEN_M * 0.55))
        b = len(tris)
        _radial_slab(verts, tris, groups, a, CORE_TUBE_R_M - 1.0,
                     HUB_PORT_R_M, za, zb, 5.5, "core_hub_port")
        parts.append(("hub_port", b, len(tris)))
        ports.append(a)

    _guard(verts, tris, groups, f"core_hub[{end}]")
    return verts, tris, {
        "sector": sector,
        "end": end,
        "aperture_r_m": round(r_ap, 2),
        "aperture_z_m": round(z_ap, 1),
        "bell_max_r_m": round(r_ap, 2),
        "saddle_angles": saddles,
        "port_angles": ports,
        "port_r_m": HUB_PORT_R_M,
        "brace_tips": braces,
        "fins": HUB_FINS,
        "triangles": len(tris),
        "groups": groups,
        "parts": parts,
    }


# ---------------------------------------------------------------------------
# The mid-span node
# ---------------------------------------------------------------------------

def spoke_node(schema, profile, sector, z=None):
    """The bell-and-spar node where a spoke meets the tube away from a cap.

    `34b` shows one out in the middle of the drum: a stepped bell wrapped round
    the tube with thin spars radiating from it. `interior.py:drum_spokes()`
    places its spokes at the sector's mid-z by default, so that is where this
    goes unless a caller says otherwise -- and the node's body is wider than the
    spokes' inner ends, so the two overlap rather than meeting at a plane where
    a millimetre of drift would open a hole.
    """
    zc = spoke_z(schema, sector) if z is None else z
    verts, tris, groups = [], [], []
    parts = []

    r_bore = CORE_TUBE_R_M - 0.6
    bell = "core_node_bell"
    loop = [(zc - 34.0, r_bore, bell), (zc - 34.0, CORE_TUBE_R_M + 3.0, bell)]
    zz = -26.0
    for k in range(NODE_FLANGES):
        r = CORE_TUBE_R_M + 3.0 + (NODE_BODY_R_M - CORE_TUBE_R_M - 3.0) \
            * (k + 1) / NODE_FLANGES
        loop.append((zc + zz, loop[-1][1], bell))
        loop.append((zc + zz, r, bell))
        zz += 6.0
    loop.append((zc + 14.0, NODE_BODY_R_M, bell))
    loop.append((zc + 14.0, CORE_TUBE_R_M + 5.0, bell))
    loop.append((zc + 24.0, CORE_TUBE_R_M + 5.0, bell))
    loop.append((zc + 24.0, r_bore, "core_node_bore"))
    b = len(tris)
    _revolve_loop(verts, tris, groups, loop, TUBE_SIDES)
    parts.append(("node_bell", b, len(tris)))

    for k in range(NODE_SPARS):
        a = 360.0 * (k + 0.5) / NODE_SPARS
        b = len(tris)
        # Long and thin, as 34b shows them: blades standing well clear of the
        # body rather than fins flush with it. At NODE_BODY_R_M + 2.5 they were
        # invisible against the body in every render.
        _radial_slab(verts, tris, groups, a, NODE_BODY_R_M - 4.0,
                     NODE_BODY_R_M + 7.5, zc - 2.0, zc + 12.0, 0.7,
                     "core_node_spar")
        parts.append(("node_spar", b, len(tris)))

    ports = []
    for i in range(it.SPOKE_COUNT):
        a = 360.0 * i / it.SPOKE_COUNT
        b = len(tris)
        _radial_slab(verts, tris, groups, a, NODE_BODY_R_M - 6.0,
                     NODE_PAD_R_M, zc - 8.0, zc + 12.0, 7.0, "core_node_port")
        parts.append(("node_port", b, len(tris)))
        ports.append(a)

    _guard(verts, tris, groups, "spoke_node")
    return verts, tris, {
        "sector": sector,
        "z_m": round(zc, 1),
        "body_r_m": NODE_BODY_R_M,
        "pad_r_m": NODE_PAD_R_M,
        "port_angles": ports,
        "spars": NODE_SPARS,
        "triangles": len(tris),
        "groups": groups,
        "parts": parts,
    }


def core_axis(schema, profile, sector, z_span=None):
    """Tube, both hubs and the mid-span node, as one mesh."""
    verts, tris, groups, parts = [], [], [], []

    def merge(v, t, m):
        o = len(verts)
        base = len(tris)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(m["groups"])
        parts.extend((n, s + base, e + base) for n, s, e in m["parts"])

    tv, tt, tm = core_tube(schema, profile, sector, z_span)
    merge(tv, tt, tm)
    hubs = []
    for end in ("aft", "fore"):
        hv, ht, hm = core_hub(schema, profile, sector, end)
        merge(hv, ht, hm)
        hubs.append(hm)
    nv, nt, nm = spoke_node(schema, profile, sector)
    merge(nv, nt, nm)

    return verts, tris, {
        "sector": sector,
        "tube": tm, "hubs": hubs, "node": nm,
        "triangles": len(tris),
        "groups": groups,
        "parts": parts,
    }


# ---------------------------------------------------------------------------
# Winding, closure and the guard that refuses to emit invisible geometry
# ---------------------------------------------------------------------------

def _outward_fraction(verts, tris, groups, min_radial=0.25):
    """Fraction of envelope faces whose normal points away from the spin axis.

    The mirror of `interior.py:_inward_fraction()`. Restricted to the groups
    that form the outer envelope and to faces with a real radial component: a
    flat annulus on a collar step points along +/-z and says nothing about
    winding, and the bore inside a hub *should* face the axis.
    """
    good = total = 0
    for i, (a, b, c) in enumerate(tris):
        if groups[i] not in ENVELOPE_GROUPS:
            continue
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = tuple(p1[j] - p0[j] for j in range(3))
        v = tuple(p2[j] - p0[j] for j in range(3))
        n = (u[1] * v[2] - u[2] * v[1],
             u[2] * v[0] - u[0] * v[2],
             u[0] * v[1] - u[1] * v[0])
        nl = math.sqrt(sum(x * x for x in n))
        if nl < 1e-12:
            continue
        cx = (p0[0] + p1[0] + p2[0]) / 3.0
        cy = (p0[1] + p1[1] + p2[1]) / 3.0
        rl = math.hypot(cx, cy)
        if rl < 1e-9:
            continue
        radial = (n[0] * cx + n[1] * cy) / (nl * rl)
        if abs(radial) < min_radial:
            continue
        total += 1
        good += radial > 0
    return good / max(1, total), total


def _guard(verts, tris, groups, who):
    """Refuse to return geometry that would be culled away to nothing.

    The drum taught this the expensive way: an inverted surface does not error,
    it renders black, and a black frame reads as a badly placed camera rather
    than as a bug. Measuring it at build time is the only thing that turns a
    silent failure into a loud one.
    """
    frac, n = _outward_fraction(verts, tris, groups)
    if n and frac < 1.0:
        raise AssertionError(
            f"{who}: {(1 - frac) * 100:.1f}% of {n} envelope faces point toward "
            "the axis; they will be backface-culled for a viewer out in the drum")


def signed_volume(verts, tris):
    """Six times the signed volume. Positive means outward winding."""
    s = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0


def closure_report(verts, tris):
    """Boundary and orientation faults in a mesh that ought to be closed.

    Vertices are welded by rounded position first: a lathe emits its two rings
    per band independently, so the same corner exists several times and an
    index-only test would report every band as a hole.
    """
    ids, key_of = {}, []
    for x, y, z in verts:
        k = (round(x, 3), round(y, 3), round(z, 3))
        if k not in ids:
            ids[k] = len(ids)
        key_of.append(ids[k])
    seen = {}
    for a, b, c in tris:
        ia, ib, ic = key_of[a], key_of[b], key_of[c]
        for e in ((ia, ib), (ib, ic), (ic, ia)):
            if e[0] == e[1]:
                continue
            seen[e] = seen.get(e, 0) + 1
    boundary = sum(1 for e in seen if (e[1], e[0]) not in seen)
    duplicated = sum(1 for e, n in seen.items() if n > 1)
    return {"directed_edges": len(seen), "boundary_edges": boundary,
            "duplicate_directed_edges": duplicated}


def aperture_clearance(schema, profile, sector, z_span=None):
    """Gap between the tube skin and each cap aperture edge.

    Computed rather than asserted, per the brief: the interesting number is how
    much room the tube actually has where it crosses a cap, and a change to the
    collar rise or to the cap's core radius should move it rather than trip a
    constant.

    Measured off the tube's own (z, r) profile rather than off its vertices. The
    lathe only carries a station every few metres of articulation and there is
    no reason for one to land on a cap plane, so a vertex scan through a window
    at the aperture found nothing at all and reported no clearance -- which is
    the wrong answer, not a missing one.

    Two numbers, because they fail differently. `at_plane` is what the tube is
    doing where it crosses; `worst` is its largest radius anywhere, which is
    what matters if a later edit moves the collar pitch and slides a collar onto
    a cap. Clearance is quoted against `worst`, so it holds however the
    articulation shifts.
    """
    z0, z1 = z_span if z_span else tube_span(schema, profile, sector)
    st, _grp, _c, _cg = tube_stations(z0, z1)
    worst = max(r for _z, r in st)

    def r_at(z):
        for i in range(len(st) - 1):
            (za, ra), (zb, rb) = st[i], st[i + 1]
            if za <= z <= zb:
                if zb - za < 1e-9:
                    return max(ra, rb)
                f = (z - za) / (zb - za)
                return ra + (rb - ra) * f
        return st[0][1] if z < st[0][0] else st[-1][1]

    out = {}
    for end in ("aft", "fore"):
        ap = aperture(schema, profile, sector, end)
        out[end] = {
            "aperture_r_m": round(ap["radius_m"], 2),
            "tube_r_at_plane_m": round(r_at(ap["z_m"]), 2),
            "tube_max_r_m": round(worst, 2),
            "clearance_m": round(ap["radius_m"] - worst, 2),
            "inside_span": z0 < ap["z_m"] < z1,
        }
    return out


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    r_drum = it.sector_radius(schema, profile, sector)

    # --- primitives --------------------------------------------------------
    # Every solid in this module is a box or a revolve. Both were wrong at least
    # once elsewhere in this repository and the failure is invisible outdoors,
    # so gate them before anything built from them.
    v, t, g = [], [], []
    _box(v, t, g, [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
         [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], "x")
    check("_box winds outward", abs(signed_volume(v, t) - 1.0) < 1e-9,
          f"volume {signed_volume(v, t):.4f}, want +1")
    check("_box is closed", closure_report(v, t)["boundary_edges"] == 0)

    v, t, g = [], [], []
    _revolve_open(v, t, g, [(0.0, 2.0), (10.0, 2.0)], ["core_tube_barrel"],
                  32, "core_tube_end")
    vol = signed_volume(v, t)
    check("_revolve_open winds outward and closes",
          vol > 0 and closure_report(v, t)["boundary_edges"] == 0,
          f"volume {vol:.2f} vs pi r^2 h = {math.pi * 4 * 10:.2f}")

    # A loop and its mirror in z must BOTH come out outward-facing. This is the
    # aft hub in miniature, and it is the one thing about mirroring that fails
    # silently rather than loudly.
    for sgn in (1.0, -1.0):
        v, t, g = [], [], []
        loop = [(sgn * 0.0, 3.0, "core_hub_bell"),
                (sgn * 5.0, 3.0, "core_hub_bell"),
                (sgn * 5.0, 1.0, "core_hub_bore"),
                (sgn * 0.0, 1.0, "core_hub_bell")]
        _revolve_loop(v, t, g, loop, 24)
        frac, n = _outward_fraction(v, t, g)
        check(f"_revolve_loop faces outward mirrored z={sgn:+.0f}",
              signed_volume(v, t) > 0
              and closure_report(v, t)["boundary_edges"] == 0
              and frac == 1.0 and n > 0,
              f"volume {signed_volume(v, t):.2f}, outward {frac:.2f}/{n}")
        # The group has to travel with its band through the reversal, or the
        # mirrored hub tags its bore as envelope and the guard fires on
        # geometry that is in fact correct.
        bore = {i for i, gg in enumerate(g) if gg == "core_hub_bore"}
        check(f"_revolve_loop keeps groups on their bands, z={sgn:+.0f}",
              len(bore) == 48 and all(
                  abs(math.hypot(*v[t[i][0]][:2]) - 1.0) < 1e-9 for i in bore),
              f"{len(bore)} bore faces")

    # --- the tube ----------------------------------------------------------
    tv, tt, tm = core_tube(schema, profile, sector)
    check("tube radius matches the sectional schematic's ratio",
          0.064 <= CORE_TUBE_R_M / r_drum <= 0.075,
          f"r/R = {CORE_TUBE_R_M / r_drum:.4f}")
    z0, z1 = tm["z0"], tm["z1"]
    ex = schema["sectors"]["extents_m"][sector]
    check("tube spans the whole drum", z0 < ex["z0"] and z1 > ex["z1"],
          f"{z0} .. {z1} against sector {ex['z0']} .. {ex['z1']}")
    for end in ("aft", "fore"):
        ap = aperture(schema, profile, sector, end)
        check(f"tube passes right through the {end} cap",
              z0 < ap["z_m"] < z1, f"aperture at z={ap['z_m']:.1f}")

    rep = closure_report(tv, tt)
    check("tube is watertight", rep["boundary_edges"] == 0, str(rep))
    check("tube is consistently oriented",
          rep["duplicate_directed_edges"] == 0, str(rep))
    check("tube encloses positive volume", signed_volume(tv, tt) > 0,
          f"{signed_volume(tv, tt):,.0f} m^3")
    frac, n = _outward_fraction(tv, tt, tm["groups"])
    check("every tube envelope face points away from the axis",
          frac == 1.0 and n > 0, f"{frac:.3f} over {n} faces")
    check("every tube triangle carries a group",
          len(tm["groups"]) == len(tt) and all(tm["groups"]))

    # The lathe must march forward. A profile that backtracks in z folds a band
    # over the one before it: still closed, still outward, and garbage on
    # screen -- so closure and winding do not cover it.
    st = tube_stations(z0, z1)[0]
    check("tube stations never go backwards in z",
          all(st[i + 1][0] >= st[i][0] - 1e-9 for i in range(len(st) - 1)))
    check("no tube band is degenerate",
          all(abs(st[i + 1][0] - st[i][0]) > 1e-6
              or abs(st[i + 1][1] - st[i][1]) > 1e-6
              for i in range(len(st) - 1)))
    check("tube radius is positive everywhere",
          all(r > 1.0 for _z, r in st), f"min {min(r for _z, r in st):.2f} m")

    # Articulation. A plain cylinder would pass every test above, so assert the
    # thing the reference is actually about.
    radii = sorted({round(r, 2) for _z, r in st})
    check("the tube is articulated, not a plain cylinder", len(radii) >= 4,
          f"distinct radii {radii}")
    check("collar groups at every section joint",
          tm["sections"] >= 18, f"{tm['sections']} sections")
    pitches = [tm["collar_z"][i + 1] - tm["collar_z"][i]
               for i in range(len(tm["collar_z"]) - 1)]
    check("collar pitch is uniform",
          max(pitches) - min(pitches) < 1e-6, f"{sorted(set(pitches))[:3]}")
    check("collar pitch is 1.5-4 tube diameters, as 33a shows",
          1.5 <= pitches[0] / (2 * CORE_TUBE_R_M) <= 4.0,
          f"{pitches[0] / (2 * CORE_TUBE_R_M):.2f} diameters")
    check("the tube carries warm bands and cool ones",
          "core_tube_band_warm" in tm["groups"]
          and "core_tube_band" in tm["groups"])
    check("the tube carries at least one open cage bay", tm["cage_bays"] >= 1,
          str(tm["cage_bays"]))

    # Determinism. The warm-band choice is the only data-dependent decision in
    # the module and it is keyed through FNV-1a precisely so this holds.
    again = core_tube(schema, profile, sector)
    check("regeneration is byte-identical",
          again[0] == tv and again[1] == tt and again[2]["groups"] == tm["groups"])
    # Checked against the published FNV-1a test vector, not against our own
    # output: comparing a hash to what it printed last time proves nothing.
    check("FNV-1a matches the published test vector",
          _fnv1a("foobar") == 0x85944171f73967e8, f"{_fnv1a('foobar'):#x}")

    # --- clearance through the aperture ------------------------------------
    cl = aperture_clearance(schema, profile, sector)
    for end, c in cl.items():
        check(f"{end} cap: the aperture is inside the tube's run",
              c["inside_span"])
        check(f"{end} cap: tube passes through with clearance",
              c["clearance_m"] > 5.0,
              f"tube {c['tube_max_r_m']} m (at the plane "
              f"{c['tube_r_at_plane_m']} m) in a {c['aperture_r_m']} m "
              f"aperture -> {c['clearance_m']} m")
    check("both apertures give the same clearance",
          abs(cl["fore"]["clearance_m"] - cl["aft"]["clearance_m"]) < 0.5,
          f"{cl['fore']['clearance_m']} vs {cl['aft']['clearance_m']}")

    # --- the hubs ----------------------------------------------------------
    for end in ("fore", "aft"):
        hv, ht, hm = core_hub(schema, profile, sector, end)
        ap = aperture(schema, profile, sector, end)

        check(f"{end} hub: closes the cap aperture",
              abs(hm["bell_max_r_m"] - ap["radius_m"]) < 0.5,
              f"bell {hm['bell_max_r_m']} m vs aperture {ap['radius_m']:.2f} m")
        check(f"{end} hub: nothing reaches the drum floor",
              max(math.hypot(x, y) for x, y, _z in hv) < r_drum - 20.0,
              f"{max(math.hypot(x, y) for x, y, _z in hv):.1f} m of "
              f"{r_drum:.1f} m")

        # Receives exactly the structure interior.py builds -- count and angle.
        want = [360.0 * i / it.TRUSS_COUNT for i in range(it.TRUSS_COUNT)]
        check(f"{end} hub: receives exactly TRUSS_COUNT trusses",
              hm["saddle_angles"] == want,
              f"{hm['saddle_angles']} vs {want}")
        want = [360.0 * i / it.SPOKE_COUNT for i in range(it.SPOKE_COUNT)]
        check(f"{end} hub: receives exactly SPOKE_COUNT spokes",
              hm["port_angles"] == want, f"{hm['port_angles']} vs {want}")
        check(f"{end} hub: spoke ports reach the spokes",
              hm["port_r_m"] > _spoke_reach(schema, profile, sector),
              f"port {hm['port_r_m']} m vs spoke inner end "
              f"{_spoke_reach(schema, profile, sector):.2f} m")

        # The brace tip has to land on the truss, not near it. This is the
        # assertion that ties the hub to interior.py rather than to a number
        # copied out of it.
        r_truss = r_drum * it.TRUSS_RADIUS_FRAC
        z_truss = ex["z1"] if end == "fore" else ex["z0"]
        tips_ok = all(abs(r - r_truss) < 1e-6 and abs(z - z_truss) < 1e-6
                      for _a, r, z in hm["brace_tips"])
        check(f"{end} hub: brace tips land on the truss chords", tips_ok,
              f"{hm['brace_tips'][0]} vs r={r_truss:.1f} z={z_truss}")

        # The cap dishes outward faster than the brace does, so the brace must
        # stay on the drum side of it over its whole run. Sampled, because the
        # two curves are not parallel and only the interior can fail.
        worst = None
        for k in range(21):
            f = k / 20.0
            r = ap["radius_m"] + (r_truss - ap["radius_m"]) * f
            z_brace = ap["z_m"] + (z_truss - ap["z_m"]) * f
            u = r / r_drum
            z_cap = (ex["z1"] if end == "fore" else ex["z0"]) \
                + ap["out"] * it.ENDCAP_DISH * r_drum * (1.0 - u * u)
            gap = (z_cap - z_brace) * ap["out"]
            worst = gap if worst is None else min(worst, gap)
        check(f"{end} hub: brace stays inboard of the cap", worst >= -1e-6,
              f"worst gap {worst:.2f} m")
        check(f"{end} hub: has a cog of radial fins", hm["fins"] == HUB_FINS
              and "core_hub_fin" in hm["groups"])
        check(f"{end} hub: carries the light run 34b shows",
              "core_hub_lamp" in hm["groups"])

        frac, n = _outward_fraction(hv, ht, hm["groups"])
        check(f"{end} hub: bell faces away from the axis",
              frac == 1.0 and n > 0, f"{frac:.3f} over {n} faces")
        bad = [nm for nm, s, e in hm["parts"]
               if closure_report(hv, ht[s:e])["boundary_edges"]
               or signed_volume(hv, ht[s:e]) <= 0]
        check(f"{end} hub: every part is a closed outward solid", not bad,
              str(sorted(set(bad))))

    # The two hubs must be mirror images about the drum's mid-plane, or one end
    # of the station has quietly become a different design from the other.
    fz = core_hub(schema, profile, sector, "fore")[2]["aperture_z_m"]
    az = core_hub(schema, profile, sector, "aft")[2]["aperture_z_m"]
    mid = (ex["z0"] + ex["z1"]) / 2.0
    check("hubs sit symmetrically about the drum mid-plane",
          abs((fz - mid) + (az - mid)) < 0.05, f"{fz} and {az} about {mid}")

    # --- the node ----------------------------------------------------------
    nv, nt, nm = spoke_node(schema, profile, sector)
    check("node sits where drum_spokes() puts its spokes",
          abs(nm["z_m"] - spoke_z(schema, sector)) < 0.05,
          f"{nm['z_m']} vs {spoke_z(schema, sector)}")
    check("node overlaps the spokes rather than abutting them",
          nm["body_r_m"] > _spoke_reach(schema, profile, sector) + 1.0,
          f"body {nm['body_r_m']} m vs spoke inner end "
          f"{_spoke_reach(schema, profile, sector):.2f} m")
    check("node has a port per spoke",
          nm["port_angles"] == [360.0 * i / it.SPOKE_COUNT
                                for i in range(it.SPOKE_COUNT)])
    frac, n = _outward_fraction(nv, nt, nm["groups"])
    check("node faces away from the axis", frac == 1.0 and n > 0,
          f"{frac:.3f} over {n} faces")
    bad = [nme for nme, s, e in nm["parts"]
           if closure_report(nv, nt[s:e])["boundary_edges"]
           or signed_volume(nv, nt[s:e]) <= 0]
    check("node: every part is a closed outward solid", not bad,
          str(sorted(set(bad))))

    # --- the assembly ------------------------------------------------------
    av, at, am = core_axis(schema, profile, sector)
    check("assembly indexes are in range",
          all(0 <= i < len(av) for tri in at for i in tri))
    check("assembly parts cover every triangle",
          sum(e - s for _n, s, e in am["parts"]) == len(at),
          f"{sum(e - s for _n, s, e in am['parts'])} of {len(at)}")

    # The drum is hollow and that is authority 1. Nothing on the axis may reach
    # out into the open volume except the three braces, which are meant to.
    core_r = aperture(schema, profile, sector, "fore")["radius_m"]
    reach = {}
    for i, gname in enumerate(am["groups"]):
        for vi in at[i]:
            r = math.hypot(av[vi][0], av[vi][1])
            reach[gname] = max(reach.get(gname, 0.0), r)
    spill = {g: round(r, 1) for g, r in reach.items()
             if r > core_r + 1.0 and not g.startswith("core_hub_brace")
             and not g.startswith("core_hub_lamp")}
    check("only the truss braces leave the core zone", not spill, str(spill))
    check("nothing on the axis touches the drum floor",
          max(reach.values()) < r_drum - 20.0,
          f"max reach {max(reach.values()):.1f} m of {r_drum:.1f} m")

    # Budget. The drum gate is a visible-set gate and everything on the axis is
    # visible from everywhere in the drum, so it all counts at once.
    check("axis fits the drum's visible-set headroom", len(at) < 30_000,
          f"{len(at):,} triangles")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
