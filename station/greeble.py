"""Procedural surface detail -- greebling -- for the exterior hull.

The lathe gives the hull its form and the plating pass gives it panel breakup,
but a real orbital structure wears its machinery on the outside: vents, grilles,
access hatches, conduit runs, antenna stubs, sensor blisters, mooring cleats and
marker lights. Per docs/adr/0002-geometry-representation.md that detail is
scattered by rule rather than modelled by hand, which is the only approach that
covers 12.7 km^2 of hull without an art team.

Two properties matter more than any individual shape.

**Determinism.** Every instance is keyed on (seed, zone id, cell indices) and on
nothing else -- not on call order, and never on Python's built-in ``hash``, which
is salted per process and would make two runs of the same generator disagree.
Regeneration is byte-identical, which is the only thing that makes the CI
geometry check mean anything.

**Reading as machinery rather than as noise.** Boxes at random sizes and angles
read as dirt on the lens. The rules that avoid it, all visible in the
orthographic production sheet (``reference/01-station-exterior/exterior
more.jpg``):

* Everything aligns to the hull's axial and circumferential directions. There
  are no arbitrary rotations anywhere in this module.
* Panels and vents come in short aligned rows, not singly. Machinery is
  installed in banks.
* Conduits run hundreds of metres in straight lines with regularly spaced
  clamps. That long linear motif -- the clamped run down the flank of the
  habitat drum in the side view -- is the single most legible piece of surface
  detail on the reference model, and one run is worth fifty scattered boxes.
* Density is a property of what a hull section is *for*. The drum skin is
  finished and nearly bare; the reactor spine is covered in plant.
"""
import math
from bisect import bisect_left

from components import dome_mesh

# ---------------------------------------------------------------------------
# Deterministic value source
# ---------------------------------------------------------------------------
# FNV-1a, written out rather than taken from the standard library because
# Python's str.__hash__ is randomised per process by PYTHONHASHSEED. Using it
# here would give a different hull on every run and silently destroy the point
# of committing generated geometry.
_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3
_M64 = 0xFFFFFFFFFFFFFFFF


def _fnv1a(*parts):
    h = _FNV_OFFSET
    for part in parts:
        blob = part.encode("utf-8") if isinstance(part, str) else str(part).encode()
        for byte in blob + b"\x1f":          # separator: ("a", "bc") != ("ab", "c")
            h = ((h ^ byte) * _FNV_PRIME) & _M64
    return h


class Seeded:
    """A random stream whose whole state is a key, not a global sequence.

    Each greeble cell makes its own stream from (seed, zone, cell indices), so a
    cell's contents depend only on where that cell is. Adding a zone, or
    changing the order zones are visited, cannot perturb geometry elsewhere --
    which keeps the diff of a tuning change readable.
    """

    def __init__(self, *key):
        self._h = _fnv1a(*key)

    def _mix(self):                          # splitmix64 finaliser
        self._h = (self._h + 0x9E3779B97F4A7C15) & _M64
        z = self._h
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _M64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _M64
        return z ^ (z >> 31)

    def unit(self):
        """Uniform in [0, 1) with 53 bits of mantissa."""
        return (self._mix() >> 11) / float(1 << 53)

    def span(self, lo, hi):
        return lo + (hi - lo) * self.unit()

    def count(self, lo, hi):
        """Inclusive integer range."""
        return lo + int(self.unit() * (hi - lo + 1))

    def chance(self, p):
        return self.unit() < p

    def pick(self, weights):
        """Weighted choice over {name: weight}, order-independent."""
        names = sorted(weights)
        x = self.unit() * sum(weights.values())
        for name in names:
            x -= weights[name]
            if x < 0.0:
                return name
        return names[-1]


# ---------------------------------------------------------------------------
# The hull as a surface, rather than as a list of rings
# ---------------------------------------------------------------------------
class HullSurface:
    """Interpolated radius, local slope and a tangent frame at any (z, theta).

    ``components.radius_at`` answers "what radius does a component attach at",
    for which the nearest sample is fine at component scale. Greebles need more:
    they must sit flush on a surface that is up to 23:1 steep at section
    transitions, so they need the radius *interpolated* and the local slope, and
    those come from one lookup here.

    Slope is taken over a window rather than between adjacent samples. The
    profile was traced from a drawing at 4.07 m spacing and carries single-sample
    noise; differencing neighbours amplifies it into greebles that tilt at
    random, which is exactly the noise this module exists to avoid.
    """

    SLOPE_WINDOW = 3                          # +/- samples, ~24 m of hull

    def __init__(self, profile):
        self.z = [p["z_m"] for p in profile]
        self.r = [p["radius_m"] for p in profile]
        n = len(self.z)
        w = self.SLOPE_WINDOW
        self.slope = []
        for i in range(n):
            a, b = max(0, i - w), min(n - 1, i + w)
            dz = self.z[b] - self.z[a]
            self.slope.append((self.r[b] - self.r[a]) / dz if dz > 1e-9 else 0.0)

    def _bracket(self, z):
        i = bisect_left(self.z, z)
        if i <= 0:
            return 0, 0, 0.0
        if i >= len(self.z):
            return len(self.z) - 1, len(self.z) - 1, 0.0
        z0, z1 = self.z[i - 1], self.z[i]
        return i - 1, i, (z - z0) / (z1 - z0) if z1 > z0 else 0.0

    def radius(self, z):
        a, b, t = self._bracket(z)
        return self.r[a] + (self.r[b] - self.r[a]) * t

    def slope_at(self, z):
        a, b, t = self._bracket(z)
        return self.slope[a] + (self.slope[b] - self.slope[a]) * t

    def frame(self, z, theta):
        """Orthonormal (origin, U, V, N) on the surface, plus the local radius.

        U is circumferential (spinward), V is axial toward fore, N is the true
        outward normal including the profile's slope -- so a greeble on the
        forward taper lies against the cone instead of standing off it.
        U x V = N, so slabs built in this frame come out wound outward.
        """
        r = self.radius(z)
        dr = self.slope_at(z)
        k = 1.0 / math.sqrt(1.0 + dr * dr)
        ct, st = math.cos(theta), math.sin(theta)
        origin = (r * ct, r * st, z)
        u = (-st, ct, 0.0)
        v = (dr * ct * k, dr * st * k, k)
        n = (ct * k, st * k, -dr * k)
        return (origin, u, v, n), r


# ---------------------------------------------------------------------------
# Primitives, all authored in a surface frame
# ---------------------------------------------------------------------------
# The lathe is faceted at 64 segments, the plating pass modulates radius by
# +/- depth, and a greeble's own footprint chords across the curve. A greeble
# placed exactly at r(z) would therefore float over some facets and sink into
# others. Everything is buried by the sum of those three terms instead.
PLATE_DEPTH_M = 1.3
FACET_SAG_FRACTION = 0.0012                   # r*(1-cos(pi/64)) at 64 segments
BURY_MARGIN_M = 1.5


def _bury(half_width, radius):
    return half_width * half_width / (2.0 * radius) + \
        radius * FACET_SAG_FRACTION + PLATE_DEPTH_M + BURY_MARGIN_M


def _at(frame, du, dv, dw):
    (ox, oy, oz), u, v, n = frame
    return (ox + u[0] * du + v[0] * dv + n[0] * dw,
            oy + u[1] * du + v[1] * dv + n[1] * dw,
            oz + u[2] * du + v[2] * dv + n[2] * dw)


def _slab(verts, tris, frame, cu, cv, hu, hv, w0, w1, taper=1.0):
    """A box with an optional draft angle, open on its buried underside.

    The bottom face is omitted: it sits inside the hull, is never visible, and
    at ~3,000 instances the six triangles it would cost are worth more spent on
    a slat or a clamp. Draft is not decoration -- a slight taper catches the
    light differently on each face, which is what separates a machined block
    from a flat sticker under a directional key light.
    """
    b = len(verts)
    for w, s in ((w0, 1.0), (w1, taper)):
        for du, dv in ((-hu, -hv), (hu, -hv), (hu, hv), (-hu, hv)):
            verts.append(_at(frame, cu + du * s, cv + dv * s, w))
    tris.extend([
        (b + 4, b + 5, b + 6), (b + 4, b + 6, b + 7),          # top
        (b + 0, b + 1, b + 5), (b + 0, b + 5, b + 4),          # -V
        (b + 2, b + 3, b + 7), (b + 2, b + 7, b + 6),          # +V
        (b + 1, b + 2, b + 6), (b + 1, b + 6, b + 5),          # +U
        (b + 3, b + 0, b + 4), (b + 3, b + 4, b + 7),          # -U
    ])


def _prism(verts, tris, frame, cu, cv, radius, w0, w1, sides=8, taper=0.82):
    """A regular prism, capped on top and open underneath, like ``_slab``."""
    b = len(verts)
    for w, rr in ((w0, radius), (w1, radius * taper)):
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            verts.append(_at(frame, cu + math.cos(a) * rr, cv + math.sin(a) * rr, w))
    for i in range(sides):
        j = (i + 1) % sides
        tris.append((b + i, b + j, b + sides + j))
        tris.append((b + i, b + sides + j, b + sides + i))
    for i in range(1, sides - 1):
        tris.append((b + sides, b + sides + i, b + sides + i + 1))


# ---------------------------------------------------------------------------
# Greeble kinds
# ---------------------------------------------------------------------------
# Sizes are absolute metres against a hull whose plating pass lays down 65 m
# plates. The first attempt at this module used 10-20 m fittings and they read
# as dirt on the lens from anywhere further out than a hundred metres: at 8 km
# scale a lone 15 m box is sub-pixel. What reads is a 40-80 m installation with
# its own internal detail, which is also what the orthographic sheet shows on
# the drum flank. Every kind therefore takes a `scale`, and assemblies pair one
# full-size primary with small satellites -- a size hierarchy, so the same
# geometry reads at 200 m and at 20 km.
#
# Heights are generous for their footprint. Under a directional key light,
# relief is the only thing separating a fitting from a decal.

def _access_panel(verts, tris, frame, r, rng, scale=1.0):
    """A row of raised plates along the axis -- hull access panels."""
    n = rng.count(2, 4)
    hu = min(rng.span(11.0, 20.0) * scale, r * 0.16)
    hv = rng.span(8.0, 15.0) * scale
    h = rng.span(3.5, 7.0) * scale
    pitch = hv * 2.0 + rng.span(3.0, 7.0) * scale
    v0 = -pitch * (n - 1) / 2.0
    w0 = -_bury(hu, r)
    for i in range(n):
        _slab(verts, tris, frame, 0.0, v0 + i * pitch, hu, hv, w0, h, taper=0.93)


def _vent_grille(verts, tris, frame, r, rng, scale=1.0):
    """A louvred bank: a low base plate carrying parallel slats.

    The comb of fine parallel ribs is the most distinctive piece of surface
    machinery on the orthographic sheet, appearing on the reactor housing and
    again on the forward structure. Slats run circumferentially and are stepped
    well above their base so the shadow between them reads at distance.
    """
    slats = rng.count(3, 5)
    hu = min(rng.span(14.0, 24.0) * scale, r * 0.18)
    pitch = rng.span(7.0, 11.0) * scale
    hv = pitch * slats / 2.0 + 4.0 * scale
    w0 = -_bury(hu, r)
    _slab(verts, tris, frame, 0.0, 0.0, hu, hv, w0, rng.span(1.4, 2.6) * scale)
    v0 = -pitch * (slats - 1) / 2.0
    h = rng.span(6.5, 11.0) * scale
    for i in range(slats):
        _slab(verts, tris, frame, 0.0, v0 + i * pitch, hu * 0.88, pitch * 0.28,
              w0, h, taper=0.8)


def _hatch(verts, tris, frame, r, rng, scale=1.0):
    """An octagonal access hatch with a raised rim."""
    rad = min(rng.span(9.0, 16.0) * scale, r * 0.14)
    _prism(verts, tris, frame, 0.0, 0.0, rad, -_bury(rad, r),
           rng.span(4.0, 8.0) * scale)


def _blister(verts, tris, frame, r, rng, scale=1.0):
    """A sensor blister: a half-ellipsoid seated on an octagonal plinth.

    The plinth is not decoration. A bare dome on a curved hull reads as a pebble
    -- soft, organic and wrong for a design language of thin hard edges (ADR
    0002). Standing it on a hard-edged base makes it read as equipment that was
    bolted on.
    """
    (origin, _u, _v, n) = frame
    rad = min(rng.span(8.0, 15.0) * scale, r * 0.13)
    plinth = rng.span(1.6, 3.2) * scale
    _prism(verts, tris, frame, 0.0, 0.0, rad * 1.22, -_bury(rad, r), plinth,
           taper=0.92)
    base = (origin[0] + n[0] * plinth, origin[1] + n[1] * plinth,
            origin[2] + n[2] * plinth)
    dome_mesh(verts, tris, base[0], base[1], base[2], n,
              rad, rng.span(6.0, 14.0) * scale, rings=2, segs=8)


def _antenna_stub(verts, tris, frame, r, rng, scale=1.0):
    """A mast normal to the hull with a crossbar near its tip."""
    hgt = rng.span(32.0, 72.0) * scale
    th = rng.span(3.0, 5.0) * scale
    _slab(verts, tris, frame, 0.0, 0.0, th, th, -_bury(th, r), hgt, taper=0.55)
    bar = rng.span(12.0, 24.0) * scale
    _slab(verts, tris, frame, 0.0, 0.0, bar, th * 0.7, hgt * 0.78, hgt * 0.88)


def _docking_cleat(verts, tris, frame, r, rng, scale=1.0):
    """A magnetic attachment point: a splayed pad carrying a raised bar.

    Canon lists both "cargo modules and magnetic attachment points" and
    retractable hard-docking mooring clamps (00-MASTER.md section 2), so these
    belong wherever something is expected to make fast to the hull.
    """
    hu = min(rng.span(9.0, 15.0) * scale, r * 0.12)
    hv = rng.span(7.0, 12.0) * scale
    pad = rng.span(3.0, 5.0) * scale
    # Only a slight splay on the pad. A strong draft angle turns it into a
    # pyramid, which at grazing incidence reads as a shard rather than a fitting.
    _slab(verts, tris, frame, 0.0, 0.0, hu, hv, -_bury(hu, r), pad, taper=0.86)
    _slab(verts, tris, frame, 0.0, 0.0, hu * 0.32, hv * 1.12, pad,
          pad + rng.span(5.0, 9.0) * scale)


def _marker_light(verts, tris, frame, r, rng, scale, lens, base, stand):
    """A light housing: a shallow pedestal carrying a proud lens block.

    Split into two pieces so the lens can take an emissive material on its own
    group while the pedestal stays hull-coloured. That is the whole reason nav
    and hazard lights are separate mesh groups rather than one.
    """
    lens, base, stand = lens * scale, base * scale, stand * scale
    _slab(verts, tris, frame, 0.0, 0.0, base, base, -_bury(base, r), stand, taper=0.7)
    _slab(verts, tris, frame, 0.0, 0.0, lens, lens, stand, stand + lens * 1.2)


def _nav_light(verts, tris, frame, r, rng, scale=1.0):
    _marker_light(verts, tris, frame, r, rng, scale, 3.0, 5.4, rng.span(3.0, 5.0))


def _hazard_light(verts, tris, frame, r, rng, scale=1.0):
    _marker_light(verts, tris, frame, r, rng, scale, 2.4, 4.4, rng.span(2.6, 4.2))


# kind -> (builder, mesh group). Grouping by kind rather than by hull feature is
# what makes each kind one draw call and one material in the engine.
KINDS = {
    "access_panel": (_access_panel, "greeble_panel"),
    "vent_grille": (_vent_grille, "greeble_vent"),
    "hatch": (_hatch, "greeble_hatch"),
    "blister": (_blister, "greeble_blister"),
    "antenna": (_antenna_stub, "greeble_antenna"),
    "cleat": (_docking_cleat, "greeble_cleat"),
    "nav_light": (_nav_light, "greeble_nav_light"),
    "hazard_light": (_hazard_light, "greeble_hazard_light"),
}

GROUPS = [g for _f, g in KINDS.values()] + ["greeble_conduit"]

# What each density tier is made of. The tier's rate per km^2 lives in the
# schema because it is a dial; the mixture lives here because it is a
# description of what a kind of machinery deck looks like.
#
# Read off the orthographic sheet: the reactor and spine sections are grilles
# and plant, the finished drum skin is panels and the occasional hatch, and the
# forward structure adds sensor and docking hardware. `satellite` holds only the
# small hardware that plausibly surrounds a bigger installation -- an antenna or
# a vent bank is never somebody else's accessory.
TIERS = {
    "minimal": {
        "primary": {"access_panel": 5, "hatch": 2, "nav_light": 2, "blister": 1},
        "satellite": {"hatch": 2, "nav_light": 3, "access_panel": 2},
        "satellites": (0, 1), "spread_m": 40.0,
    },
    "clean": {
        "primary": {"access_panel": 7, "hatch": 3, "blister": 2, "nav_light": 1,
                    "cleat": 1},
        "satellite": {"access_panel": 4, "hatch": 3, "nav_light": 2, "cleat": 1},
        "satellites": (1, 2), "spread_m": 46.0,
    },
    "standard": {
        "primary": {"access_panel": 6, "hatch": 3, "vent_grille": 3, "blister": 2,
                    "cleat": 2, "antenna": 1, "nav_light": 1},
        "satellite": {"access_panel": 4, "hatch": 3, "nav_light": 2, "cleat": 2,
                      "blister": 1},
        "satellites": (1, 2), "spread_m": 52.0,
    },
    "cluttered": {
        "primary": {"access_panel": 6, "vent_grille": 5, "hatch": 3, "cleat": 4,
                    "blister": 2, "hazard_light": 2, "antenna": 1},
        "satellite": {"access_panel": 4, "hatch": 3, "cleat": 3, "hazard_light": 2,
                      "blister": 1},
        "satellites": (1, 3), "spread_m": 58.0,
    },
    "industrial": {
        "primary": {"vent_grille": 6, "access_panel": 5, "hatch": 3, "cleat": 3,
                    "antenna": 2, "blister": 2, "hazard_light": 2},
        "satellite": {"access_panel": 4, "hatch": 3, "cleat": 3, "hazard_light": 3,
                      "blister": 1},
        "satellites": (1, 3), "spread_m": 56.0,
    },
}

SATELLITE_SCALE = 0.45


def _place(out, surface, z, theta, rng, kind, scale, stats, min_radius):
    """Build one fitting flush on the hull at (z, theta)."""
    frame, r = surface.frame(z, theta)
    if r < min_radius:
        return
    builder, group = KINDS[kind]
    verts, tris = out[group]
    builder(verts, tris, frame, r, rng, scale)
    stats[kind] = stats.get(kind, 0) + 1


SATELLITE_CUTOFF = 0.9                        # detail below which satellites go


def _assembly(out, surface, z, theta, rng, tier, stats, min_radius, detail):
    """One installation: a full-size primary fitting with satellite hardware.

    Machinery clusters. A vent bank has access panels beside it and a marker
    light on its corner; it does not sit alone in the middle of a bare plate.
    Even scatter of single objects is precisely what makes procedural detail
    read as noise, and clustering is the cheapest available fix.

    Satellites get their own surface frame rather than being offset in the
    primary's tangent plane, so a cluster straddling a curved section still
    sits flush all the way across.

    The keep-test is drawn first and unconditionally, so a lower detail level
    yields a strict subset of the same instances rather than a reshuffle. That
    is what stops greebles swapping places when an LOD switches.
    """
    if rng.unit() > detail:
        return
    spec = TIERS[tier]
    _place(out, surface, z, theta, rng, rng.pick(spec["primary"]), 1.0, stats,
           min_radius)
    stats["assembly"] = stats.get("assembly", 0) + 1
    if detail < SATELLITE_CUTOFF:
        return
    spread = spec["spread_m"]
    r = max(surface.radius(z), 1.0)
    for _ in range(rng.count(*spec["satellites"])):
        _place(out, surface,
               z + rng.span(-spread, spread),
               theta + rng.span(-spread, spread) / r,
               rng, rng.pick(spec["satellite"]), SATELLITE_SCALE, stats,
               min_radius)


# ---------------------------------------------------------------------------
# Conduit runs
# ---------------------------------------------------------------------------
CONDUIT_SIDES = 6
# A pipe is straight for hundreds of metres at a time, so ring spacing is driven
# by how far the hull has moved under it rather than by a fixed step. Uniform
# 34 m stations cost three times the triangles for identical silhouette on the
# drum, and are still too coarse across the forward taper.
CONDUIT_STEP_MIN_M = 30.0
CONDUIT_STEP_MAX_M = 150.0
CONDUIT_SAG_TOLERANCE_M = 2.0                 # allowed radius drift between rings
CLAMP_SPACING_M = 110.0


def _conduit_stations(surface, z0, z1):
    """Sample positions along a run, closer together where the hull curves."""
    zs, z = [z0], z0
    while z < z1:
        r0 = surface.radius(z)
        step = CONDUIT_STEP_MIN_M
        while step < CONDUIT_STEP_MAX_M and z + step < z1:
            if abs(surface.radius(z + step) - r0) > CONDUIT_SAG_TOLERANCE_M:
                break
            step += CONDUIT_STEP_MIN_M
        z = min(z + step, z1)
        zs.append(z)
    return zs


def _conduit_run(out, surface, zone_id, z0, z1, theta, rng, min_radius):
    """One bundle of pipes following the long axis, clamped at intervals.

    Canon lists secondary power distribution conduits and a fuel delivery and
    emergency venting system among the exterior systems, and the side view shows
    a clamped run down the flank of the habitat drum for its entire length. The
    run is what makes the hull read as plumbed rather than as decorated.

    A run stops and restarts across a step in the profile rather than flying
    over it -- a real conduit dives into the hull at a bulkhead. Runs also never
    cross a zone boundary, which happens to be structurally correct at the
    bearing neck: nothing can be plumbed straight across a rotating joint.
    """
    verts, tris = out["greeble_conduit"]
    pipes = rng.count(1, 3)
    prad = rng.span(2.2, 3.6)
    spread = prad * 3.0
    stations = _conduit_stations(surface, z0, z1)

    def runnable(z):
        # A run stops at a bulkhead rather than flying over it; steepness is the
        # profile's way of saying "section transition".
        return surface.radius(z) >= min_radius and abs(surface.slope_at(z)) <= 1.0

    for p in range(pipes):
        # Offset each pipe of a bundle by arc length, so bundles stay parallel
        # instead of fanning out where the hull is narrow.
        dtheta = (p - (pipes - 1) / 2.0) * spread / max(surface.radius((z0 + z1) / 2.0), 1.0)
        segment = []
        for z in stations:
            if not runnable(z):
                _emit_pipe(verts, tris, segment, prad)
                segment = []
                continue
            segment.append(surface.frame(z, theta + dtheta)[0])
        _emit_pipe(verts, tris, segment, prad)

    # Clamps straddle the whole bundle, so they are laid out once per run at a
    # fixed spacing in metres -- the regular tick of supports down a long pipe is
    # most of what makes it read as plumbing rather than as a painted stripe.
    # The collar is sized from the pipe it holds and stops just above it: given
    # its own height it stops reading as a support and starts reading as a fin.
    half = (pipes - 1) * spread / 2.0 + prad * 2.4
    top = prad + _clearance(prad) + prad * 1.1
    nclamp = max(1, int((z1 - z0) / CLAMP_SPACING_M))
    for c in range(nclamp + 1):
        z = z0 + (z1 - z0) * c / nclamp
        if not runnable(z):
            continue
        frame, r = surface.frame(z, theta)
        _slab(verts, tris, frame, 0.0, 0.0, half, prad * 0.85,
              -_bury(half, r), top, taper=0.72)


def _emit_pipe(verts, tris, frames, prad):
    """Skin a chain of surface frames as a hexagonal tube, capped at both ends."""
    if len(frames) < 2:
        return
    base = len(verts)
    for frame in frames:
        (_o, u, _v, n) = frame
        # The ring lies in the (U, N) plane, which is exactly perpendicular to
        # the pipe's axial direction V, so the tube keeps a circular section
        # even where the hull slopes.
        for i in range(CONDUIT_SIDES):
            a = 2.0 * math.pi * i / CONDUIT_SIDES
            du, dw = math.cos(a) * prad, math.sin(a) * prad
            verts.append(_at(frame, du, 0.0, dw + prad + _clearance(prad)))
    rings = len(frames)
    for k in range(rings - 1):
        for i in range(CONDUIT_SIDES):
            j = (i + 1) % CONDUIT_SIDES
            a = base + k * CONDUIT_SIDES + i
            b = base + k * CONDUIT_SIDES + j
            c = base + (k + 1) * CONDUIT_SIDES + j
            d = base + (k + 1) * CONDUIT_SIDES + i
            tris.append((a, d, c))
            tris.append((a, c, b))
    for k, flip in ((0, True), (rings - 1, False)):
        o = base + k * CONDUIT_SIDES
        for i in range(1, CONDUIT_SIDES - 1):
            tris.append((o, o + i + 1, o + i) if flip else (o, o + i, o + i + 1))


def _clearance(prad):
    """Standoff of the pipe's underside from the nominal hull surface."""
    return PLATE_DEPTH_M + 2.0 + prad * 0.4


# ---------------------------------------------------------------------------
# Passes
# ---------------------------------------------------------------------------
def _scatter(out, surface, zone, cfg, stats, detail):
    """Lay greebles on a jittered lattice over (z, theta) within one zone.

    A lattice rather than free scatter for two reasons: coverage is even without
    a rejection loop, and the cell indices give each instance a stable key, so
    an instance's identity survives a density change elsewhere on the hull.
    """
    zone_id = zone["id"]
    # Greebles have length of their own -- a panel row is ~40 m end to end -- so
    # the lattice is inset from the zone's own ends. Without this the last row on
    # the deflector spike hangs 3 m past the nose and the hull stops being
    # 8,047 m long, which the canon assertions catch.
    pad = min(cfg["edge_pad_m"], (zone["z1"] - zone["z0"]) * 0.2)
    z0, z1 = zone["z0"] + pad, zone["z1"] - pad
    tier = zone["tier"]
    rate = cfg["tiers"][tier]["per_km2"]
    cell = cfg["cell_m"]
    min_r = cfg["min_radius_m"]
    max_slope = cfg["max_slope"]

    nz = max(1, int(round((z1 - z0) / cell)))
    for iz in range(nz):
        zc = z0 + (z1 - z0) * (iz + 0.5) / nz
        r = surface.radius(zc)
        # Section transitions are near-vertical walls in the profile. A hatch
        # laid on one would stand out sideways from the hull, so they are left
        # bare -- which is also where the lathe's own detail is busiest.
        if r < min_r or abs(surface.slope_at(zc)) > max_slope:
            continue
        ncirc = max(4, int(2.0 * math.pi * r / cell))
        cell_area = (z1 - z0) / nz * 2.0 * math.pi * r / ncirc
        expected = rate * cell_area / 1e6
        for it in range(ncirc):
            rng = Seeded(cfg["seed"], zone_id, iz, it)
            # Fractional expectation, so a rate finer than one per cell still
            # produces the right average instead of silently rounding to zero.
            n = int(expected) + (1 if rng.unit() < expected - int(expected) else 0)
            for k in range(n):
                z = zc + rng.span(-0.38, 0.38) * (z1 - z0) / nz
                theta = 2.0 * math.pi * (it + 0.5 + rng.span(-0.38, 0.38)) / ncirc
                # Each assembly gets its own stream so that culling one at a
                # lower detail level cannot shift the contents of its neighbours.
                _assembly(out, surface, z, theta,
                          Seeded(cfg["seed"], zone_id, iz, it, k),
                          tier, stats, min_r, detail)


def _beacon_ring(out, surface, z, cfg, stats, key):
    """A ring of marker lights at a structural boundary.

    Section joints are the one place on a hull where regular, obviously
    deliberate lighting belongs: they are what a pilot needs to see to judge
    where one part of an 8 km structure ends and the next begins. Regularity is
    the point here, so these are placed on an exact ring rather than scattered.
    """
    n = cfg["beacon_ring_count"]
    if surface.radius(z) < cfg["min_radius_m"]:
        return
    for i in range(n):
        rng = Seeded(cfg["seed"], "beacon", key, i)
        _place(out, surface, z, 2.0 * math.pi * i / n, rng, "nav_light", 1.0,
               stats, cfg["min_radius_m"])


def zone_extents(features):
    """Map every feature and subfeature id to its z range.

    Greeble zones name a feature rather than carrying their own z values, so
    that retuning the longitudinal framework moves the greebles with it. There
    is no second set of coordinates to drift.
    """
    ext = {}
    for f in features:
        ext[f["id"]] = (f["z0"], f["z1"])
        for sub in f.get("subfeatures", []):
            ext[sub["id"]] = (sub["z0"], sub["z1"])
    return ext


def build_all(cfg, features, profile, detail=1.0):
    """Return ({group: (verts, tris)}, stats) for the whole greeble pass.

    ``detail`` is the fraction of instances to keep, for the LOD chain. Surface
    detail is the first thing distance takes away -- a 20 m fitting subtends
    1.3 px at 24 km -- and it does not decimate the way the lathe does, so
    without this it becomes a fixed triangle floor that dominates every distant
    level. Culling is by stable per-instance keep-test, so each level is a
    subset of the one above it and nothing pops sideways at a switch.
    """
    stats = {}
    if not cfg or not cfg.get("enabled") or detail <= 0.0:
        return {}, stats

    surface = HullSurface(profile)
    extents = zone_extents(features)
    out = {g: ([], []) for g in GROUPS}

    for entry in cfg["zones"]:
        fid = entry["feature"]
        if fid not in extents:
            raise ValueError(f"greeble zone names unknown feature: {fid}")
        z0, z1 = extents[fid]
        zone = {"id": fid, "z0": z0, "z1": z1, "tier": entry["tier"]}
        if entry["tier"] not in TIERS:
            raise ValueError(f"greeble zone {fid} names unknown tier: {entry['tier']}")
        _scatter(out, surface, zone, cfg, stats, detail)

        # Conduits survive further out than scattered fittings -- a 900 m line is
        # legible long after a 20 m box is not -- so they thin more slowly. The
        # kept runs are a spread subset of the full set and each keeps the
        # meridian it had at full detail, so thinning never rotates a pipe.
        runs = entry.get("conduit_runs", 0)
        keep = int(math.ceil(runs * min(1.0, detail * 1.6)))
        pad = min(cfg["conduit_end_pad_m"], (z1 - z0) * 0.15)
        for i in range(keep):
            run = i * runs // keep
            rng = Seeded(cfg["seed"], fid, "conduit", run)
            # Evenly spaced meridians with a small deterministic offset, so runs
            # on adjacent sections do not all line up on the same longitude.
            theta = 2.0 * math.pi * (run + rng.span(-0.18, 0.18)) / runs
            _conduit_run(out, surface, fid, z0 + pad, z1 - pad, theta, rng,
                         cfg["min_radius_m"])
            stats["conduit_run"] = stats.get("conduit_run", 0) + 1

    # Marker lights are metres across. Past the first LOD switch they are well
    # under a pixel and only cost bandwidth.
    if cfg.get("beacon_ring_count") and detail >= SATELLITE_CUTOFF:
        for i, f in enumerate(features[:-1]):
            _beacon_ring(out, surface, f["z1"], cfg, stats, i)

    return {g: v for g, v in out.items() if v[1]}, stats
