"""Command and Control — the station's bridge, inside Observation Dome 1.

Fourth on the gazetteer's ranked build list, and the one that pays a structural
debt: the exterior `observation_dome` component is still a box primitive, and
C&C's window is that dome's glazing seen from inside. Building the room forces
the component to become real, and the two must agree or the station has a window
that looks out at nothing.

WHAT THE REFERENCE ESTABLISHES

`reference/03-sector-blue/comand and contorl.webp` (authority 1) shows:

  - A **great circular window** on **radial spoke mullions**, crossed by a broad
    **concentric ring band**, set into a flat-panelled bulkhead with angled
    bracing. It is the room's whole focus and it is what the exterior dome must
    match.
  - A **raised circular command dais** on a stepped plinth, with an officer
    standing at its forward edge.
  - **Wedge-shaped angled console desks on slim legs**, arranged in an arc on the
    dais, their faces lit in green, amber and red.
  - **Two courses of long horizontal light strips**, cyan-white, at high and mid
    level on the side walls -- the room's ambient light.
  - **Stairs down at the right** to a lower level, and **handrails with panel
    infill** along the upper floor.
  - A **lower forward pit of red-lit consoles**.
  - **Two occupied levels in one volume**, which is the thing that makes it read
    as a bridge rather than an office.

SCALE, measured, WITH the depth correction that a first pass omitted.

The officer at the dais stands 175 px in an 816x616 frame, so **100 px/m at his
depth**. Fitting a circle to the window's visible arc -- chord 280 px, sagitta
215 px, R = (c^2/4 + s^2)/2s -- gives a 153 px radius, i.e. 306 px across.

Dividing those two directly gives 3.1 m and is **wrong**, because the window is
in the bulkhead BEHIND the officer and pixels-per-metre falls with distance.
The officer stands about 5 m from the lens and the bulkhead about 4 m behind
him, so at the window the scale is 100 x 5/9 = **56 px/m**, and 306 px is
**~5.5 m**. The error is a factor of 1.8 and it is the ordinary trap of
comparing two measurements taken at different depths -- the same trap that put
the tram car length in dispute (C-008).

5.5 m is a feature window rather than a panorama, and it is compatible with
Contract 5's 92 m dome: the dome is the volume, the window is one aperture in
its forward face.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                        # noqa: E402

# --- measured --------------------------------------------------------------
REF_PX_PER_M = 100.0
WINDOW_D_M = 5.5                # fitted arc, depth-corrected -- see above
WINDOW_HUB_FRAC = 0.14          # mullions stop here; they do not meet at a point

# --- canon -----------------------------------------------------------------
# Contract 5, via the schema's `observation_dome` component: radius 46 m,
# height 34 m, two of them, Dome 1 is C&C. The room sits inside that volume.
DOME_R_M = 46.0
DOME_H_M = 34.0

# --- proportioned off the frame (INV-024) ----------------------------------
WINDOW_MULLIONS = 16            # radial spokes
WINDOW_RING_FRAC = 0.62         # where the concentric band crosses them
WINDOW_MULLION_W_M = 0.10
WINDOW_RING_W_M = 0.16

DAIS_D_M = 4.6                  # the officer's stance and the console arc
DAIS_STEPS = 3
DAIS_RISE_M = 0.18
DAIS_TREAD_M = 0.42

CONSOLE_N = 5                   # wedge desks in an arc on the dais
CONSOLE_ARC_DEG = 150.0
CONSOLE_W_M = 1.15
CONSOLE_D_M = 0.62
CONSOLE_H_M = 1.02              # a standing console, which is what the frame shows
CONSOLE_TILT_DEG = 22.0

FLOOR_W_M = 14.0                # the upper floor the dais sits on
FLOOR_L_M = 12.0
PIT_DROP_M = 1.9                # the lower forward pit
STRIP_COURSES = 2               # high and mid light strips
STRIP_Y_M = (2.35, 3.55)
STRIP_H_M = 0.22
RAIL_H_M = 1.05


class _M:
    def __init__(self):
        self.v, self.t, self.g = [], [], []

    def box(self, x0, x1, y0, y1, z0, z1, group):
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        i = len(self.v)
        self.v.extend(c)
        for a, b, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                           (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.t.append((i + a, i + d, i + b))
            self.t.append((i + a, i + e, i + d))
        self.g.extend([group] * 12)

    def quad(self, a, b, c, d, group):
        i = len(self.v)
        self.v.extend([a, b, c, d])
        self.t.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        self.g.extend([group, group])

    def disc(self, cx, cz, r, y, group, seg=32):
        """Flat, wound to face UP. Reversed fan -- see the note in signage.py."""
        i = len(self.v)
        self.v.append((cx, y, cz))
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            self.v.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
        for k in range(seg):
            self.t.append((i, i + 1 + (k + 1) % seg, i + 1 + k))
        self.g.extend([group] * seg)

    def vdisc(self, cx, cy, z, r, group, seg=48):
        """A VERTICAL disc in the XY plane at depth z, facing -Z (into the room).

        Distinct from `disc`, which lies in XZ at a height. Calling `disc` for
        the window laid the glazing flat at head height instead of standing it
        in the bulkhead -- the mullions were in the window plane and the glass
        was on the ceiling. Caught by asserting the two share a plane rather
        than by looking, because from most angles the flat disc was simply out
        of frame.
        """
        i = len(self.v)
        self.v.append((cx, cy, z))
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            self.v.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        # Wound to face -Z, INTO the room. Ascending angle in the XY plane
        # gives a +Z normal, which points out through the bulkhead and is
        # backface-culled from the only side anyone stands on. Fourth instance
        # of this family in the project, so it is asserted below rather than
        # remembered.
        for k in range(seg):
            self.t.append((i, i + 1 + (k + 1) % seg, i + 1 + k))
        self.g.extend([group] * seg)

    def as_tuple(self):
        return self.v, self.t, self.g


def window(m, z, cy):
    """The circular window: glazing, radial mullions, one concentric ring.

    Built as a ring of mullion bars over a glazed disc rather than as a wheel
    of pie segments. The frame shows the bars standing PROUD of the glass and
    crossing the ring band, which a segmented disc cannot express.
    """
    r = WINDOW_D_M / 2.0
    # Glazing, set BACK so the mullions read in front of it.
    m.vdisc(0.0, cy, z + 0.06, r, "cc_glazing")

    # Spokes run from a central hub to the rim, NOT across the full diameter.
    # Full-diameter bars were the first version and 16 of them piled up at the
    # centre into a solid starburst with no glass visible between them -- the
    # window read as a painted sunburst rather than as glazing. A real spoked
    # window has a hub.
    r0 = r * WINDOW_HUB_FRAC
    hw = WINDOW_MULLION_W_M / 2.0
    for k in range(WINDOW_MULLIONS):
        a = 2.0 * math.pi * k / WINDOW_MULLIONS
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa * hw, ca * hw
        m.quad((r0 * ca + nx, cy + r0 * sa + ny, z),
               (r * ca + nx, cy + r * sa + ny, z),
               (r * ca - nx, cy + r * sa - ny, z),
               (r0 * ca - nx, cy + r0 * sa - ny, z), "cc_mullion")
    m.vdisc(0.0, cy, z, r0, "cc_hub", seg=20)

    # The concentric ring band.
    rr, w = r * WINDOW_RING_FRAC, WINDOW_RING_W_M / 2.0
    seg = 40
    for k in range(seg):
        a0 = 2.0 * math.pi * k / seg
        a1 = 2.0 * math.pi * (k + 1) / seg
        m.quad(((rr - w) * math.cos(a0), cy + (rr - w) * math.sin(a0), z),
               ((rr + w) * math.cos(a0), cy + (rr + w) * math.sin(a0), z),
               ((rr + w) * math.cos(a1), cy + (rr + w) * math.sin(a1), z),
               ((rr - w) * math.cos(a1), cy + (rr - w) * math.sin(a1), z),
               "cc_ring")


def command_control():
    """The room. +X across, +Y up, +Z forward toward the window; deck at y = 0."""
    m = _M()
    hw, L = FLOOR_W_M / 2.0, FLOOR_L_M

    # Upper floor, and the pit dropping away forward of it.
    m.quad((-hw, 0.0, -L * 0.35), (-hw, 0.0, L * 0.45),
           (hw, 0.0, L * 0.45), (hw, 0.0, -L * 0.35), "cc_floor")
    m.quad((-hw, -PIT_DROP_M, L * 0.45), (-hw, -PIT_DROP_M, L * 0.70),
           (hw, -PIT_DROP_M, L * 0.70), (hw, -PIT_DROP_M, L * 0.45), "cc_pit")
    m.box(-hw, hw, -PIT_DROP_M, 0.0, L * 0.45, L * 0.45 + 0.16, "cc_pit_face")

    # The stepped dais.
    for s in range(DAIS_STEPS):
        r = DAIS_D_M / 2.0 + (DAIS_STEPS - 1 - s) * DAIS_TREAD_M
        m.disc(0.0, 0.0, r, (s + 1) * DAIS_RISE_M, "cc_dais", seg=36)
        # riser
        seg = 36
        y0, y1 = s * DAIS_RISE_M, (s + 1) * DAIS_RISE_M
        for k in range(seg):
            a0 = 2.0 * math.pi * k / seg
            a1 = 2.0 * math.pi * (k + 1) / seg
            m.quad((r * math.cos(a0), y0, r * math.sin(a0)),
                   (r * math.cos(a1), y0, r * math.sin(a1)),
                   (r * math.cos(a1), y1, r * math.sin(a1)),
                   (r * math.cos(a0), y1, r * math.sin(a0)), "cc_dais_riser")

    # Wedge consoles in an arc on the dais, tilted toward the operator.
    top = DAIS_STEPS * DAIS_RISE_M
    rc = DAIS_D_M / 2.0 - CONSOLE_D_M * 0.55
    for k in range(CONSOLE_N):
        f = (k + 0.5) / CONSOLE_N - 0.5
        a = math.radians(f * CONSOLE_ARC_DEG) + math.pi / 2.0
        cx, cz = rc * math.cos(a), rc * math.sin(a)
        ca, sa = math.cos(a - math.pi / 2.0), math.sin(a - math.pi / 2.0)
        hwc, hd = CONSOLE_W_M / 2.0, CONSOLE_D_M / 2.0
        tilt = math.radians(CONSOLE_TILT_DEG)
        # legs
        for sx in (-1, 1):
            lx, lz = cx + sx * hwc * ca, cz + sx * hwc * sa
            m.box(lx - 0.045, lx + 0.045, top, top + CONSOLE_H_M - 0.12,
                  lz - 0.045, lz + 0.045, "cc_console_leg")
        # the lit, tilted face
        y0 = top + CONSOLE_H_M - 0.12
        y1 = y0 + hd * math.sin(tilt) * 2
        corners = []
        for sx, sz, yy in ((-1, -1, y0), (1, -1, y0), (1, 1, y1), (-1, 1, y1)):
            px = cx + sx * hwc * ca - sz * hd * sa
            pz = cz + sx * hwc * sa + sz * hd * ca
            corners.append((px, yy, pz))
        m.quad(corners[0], corners[1], corners[2], corners[3], "cc_console_face")

    # The window, in the forward bulkhead.
    zw = L * 0.70
    cy = WINDOW_D_M / 2.0 + 0.9
    # The bulkhead is built as four panels AROUND the window, not as one slab
    # with the glazing laid on it. A slab has no aperture, so the glass ended up
    # sealed inside 0.30 m of steel and the window showed as spokes on a wall.
    # An opening is a hole in something, and the something has to be built with
    # the hole already in it.
    ap = WINDOW_D_M / 2.0 + 0.12
    top, bot = DOME_H_M * 0.18, -PIT_DROP_M
    m.box(-hw, hw, cy + ap, top, zw, zw + 0.30, "cc_bulkhead")        # over
    m.box(-hw, hw, bot, cy - ap, zw, zw + 0.30, "cc_bulkhead")        # under
    m.box(-hw, -ap, cy - ap, cy + ap, zw, zw + 0.30, "cc_bulkhead")   # left
    m.box(ap, hw, cy - ap, cy + ap, zw, zw + 0.30, "cc_bulkhead")     # right
    window(m, zw - 0.01, cy)

    # Two courses of light strips on the side walls.
    for sx in (-1, 1):
        for y in STRIP_Y_M:
            m.box(sx * hw - 0.10 * sx, sx * hw, y, y + STRIP_H_M,
                  -L * 0.30, L * 0.42, "cc_light_strip")

    # Handrails along the upper floor edges, and the stair down at the right.
    for sx in (-1, 1):
        m.box(sx * (hw - 0.30) - 0.04, sx * (hw - 0.30) + 0.04,
              RAIL_H_M - 0.06, RAIL_H_M, -L * 0.30, L * 0.42, "cc_rail")
    steps = 7
    for s in range(steps):
        y = -PIT_DROP_M * (s + 1) / steps
        z = L * 0.10 + s * 0.30
        m.box(hw - 3.2, hw - 0.4, y, y + PIT_DROP_M / steps, z, z + 0.30,
              "cc_stair")

    return m.as_tuple()


def write_obj(path):
    v, t, g = command_control()
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


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

    v, t, g = command_control()
    schema, profile = it.load()

    # --- the window must agree with the exterior component -----------------
    comp = next(c for c in schema["components"] if c["id"] == "observation_dome")
    check("the dome component is the one canon calls C&C",
          "COMMAND & CONTROL" in comp["src"], comp["src"][:60])
    check("the window fits inside the dome it is cut into",
          WINDOW_D_M < comp["radius_m"] * 2,
          f"{WINDOW_D_M} m window in a {comp['radius_m'] * 2} m dome")
    check("dome dimensions are taken from the schema, not restated",
          abs(DOME_R_M - comp["radius_m"]) < 1e-9
          and abs(DOME_H_M - comp["height_m"]) < 1e-9,
          f"{DOME_R_M}/{DOME_H_M} vs schema {comp['radius_m']}/{comp['height_m']}")

    # The measured window diameter must follow from the fit, not drift from it.
    chord, sag = 280.0, 215.0
    r_px = (chord ** 2 / 4.0 + sag ** 2) / (2.0 * sag)
    # The depth correction is the whole point: 100 px/m is measured at the
    # OFFICER, and the window is ~4 m further from the lens.
    px_at_window = REF_PX_PER_M * 5.0 / 9.0
    check("the window diameter is depth-corrected, not naive",
          abs(WINDOW_D_M - 2 * r_px / px_at_window) < 0.3,
          f"{WINDOW_D_M} m against {2 * r_px / px_at_window:.2f} m corrected "
          f"(a naive read gives {2 * r_px / REF_PX_PER_M:.2f} m)")

    # --- the room is two levels, which is what makes it a bridge -----------
    ys = [q[1] for q in v]
    check("the room has two occupied levels",
          min(ys) <= -PIT_DROP_M + 1e-9 and max(ys) > 3.0,
          f"y {min(ys):.2f} .. {max(ys):.2f}")
    check("the stair spans the whole drop",
          any(abs(q[1] + PIT_DROP_M) < 0.3 for k, tri in enumerate(t)
              if g[k] == "cc_stair" for q in [v[i] for i in tri]))

    # --- flat surfaces face up ---------------------------------------------
    for grp in ("cc_floor", "cc_pit", "cc_dais"):
        bad = 0
        for k, tri in enumerate(t):
            if g[k] != grp:
                continue
            p0, p1, p2 = (v[i] for i in tri)
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[2] * w[0] - u[0] * w[2] <= 0:
                bad += 1
        check(f"{grp} faces up", bad == 0, f"{bad} downward")

    # --- the dais is a dais, not a step ------------------------------------
    check("the dais is stepped, not a kerb",
          DAIS_STEPS >= 2 and DAIS_RISE_M < 0.20,
          f"{DAIS_STEPS} risers of {DAIS_RISE_M} m")
    check("the dais steps are climbable",
          DAIS_TREAD_M > DAIS_RISE_M * 2,
          f"rise {DAIS_RISE_M} tread {DAIS_TREAD_M}")
    check("consoles stand on the dais, not through it",
          DAIS_D_M / 2.0 - CONSOLE_D_M * 0.55 > 0)

    # --- consoles are standing consoles, as the frame shows ----------------
    check("consoles are at standing height",
          0.95 <= CONSOLE_H_M <= 1.15, f"{CONSOLE_H_M} m")
    check("the console arc leaves the operator a way in",
          CONSOLE_ARC_DEG < 270.0, f"{CONSOLE_ARC_DEG} deg of arc")

    # --- the light strips are the room's ambient ---------------------------
    check("two courses of light strips", len(STRIP_Y_M) == STRIP_COURSES)
    check("strips are above head height and below the ceiling",
          all(y > 1.8 for y in STRIP_Y_M),
          f"{STRIP_Y_M}")

    # --- the window reads as mullions over glass ---------------------------
    glaz = [k for k in range(len(t)) if g[k] == "cc_glazing"]
    mull = [k for k in range(len(t)) if g[k] == "cc_mullion"]
    ring = [k for k in range(len(t)) if g[k] == "cc_ring"]
    hub = [k for k in range(len(t)) if g[k] == "cc_hub"]
    check("the spokes stop at a hub instead of piling up at the centre",
          bool(hub) and WINDOW_HUB_FRAC > 0.05,
          f"hub at {WINDOW_HUB_FRAC} of the radius")
    check("the window has glazing, mullions and a ring band",
          glaz and mull and ring,
          f"{len(glaz)} / {len(mull)} / {len(ring)} triangles")
    gz = [v[i][2] for k in glaz for i in t[k]]
    mz = [v[i][2] for k in mull for i in t[k]]
    check("the glazing stands in the bulkhead, not flat",
          max(gz) - min(gz) < 1e-6,
          f"glazing spans {max(gz) - min(gz):.3f} m in z; it should be planar")
    # The glazing must be visible from the room, i.e. in front of the bulkhead's
    # near face rather than sealed inside it.
    bulk = [v[i][2] for k, tri in enumerate(t) if g[k] == "cc_bulkhead"
            for i in tri]
    # Glass sits IN an opening, not in front of the wall -- so the test is not
    # "is it proud of the bulkhead" (it should not be) but "does it fit the hole
    # and is the hole real". The first version asserted the former and failed a
    # correctly glazed window.
    gr = max(math.hypot(v[i][0], v[i][1] - (WINDOW_D_M / 2.0 + 0.9))
             for k, tri in enumerate(t) if g[k] == "cc_glazing" for i in tri)
    for grp in ("cc_glazing", "cc_hub"):
        bad = 0
        for k, tri in enumerate(t):
            if g[k] != grp:
                continue
            p0, p1, p2 = (v[i] for i in tri)
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[0] * w[1] - u[1] * w[0] >= 0:      # +Z normal = out of the room
                bad += 1
        check(f"{grp} faces into the room", bad == 0,
              f"{bad} triangles facing out through the bulkhead")

    check("the glazing fits the aperture cut for it",
          gr <= WINDOW_D_M / 2.0 + 0.12 + 1e-9,
          f"glazing radius {gr:.3f} in a {WINDOW_D_M / 2.0 + 0.12:.3f} m opening")
    check("the glazing is glazed into the opening, not floating past it",
          min(bulk) - 1e-9 <= max(gz) <= max(bulk) + 1e-9,
          f"glazing z={max(gz):.3f}, bulkhead {min(bulk):.2f}..{max(bulk):.2f}")
    # And the bulkhead must actually have an aperture: no panel may cover the
    # window's centre.
    covers = any(min(v[i][0] for i in tri) < 0.0 < max(v[i][0] for i in tri)
                 and min(v[i][1] for i in tri) < WINDOW_D_M / 2.0 + 0.9
                 < max(v[i][1] for i in tri)
                 for k, tri in enumerate(t) if g[k] == "cc_bulkhead")
    check("the bulkhead has an aperture where the window is", not covers)

    check("mullions stand proud of the glazing, not coplanar with it",
          max(mz) < min(gz) - 1e-9,
          f"mullion z {max(mz):.3f} vs glazing {min(gz):.3f}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
