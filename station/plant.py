"""The plant zone: tankage, deep frames and catwalks in Grey's outer stack.

WHY THIS MODULE EXISTS
----------------------
`interior.py` splits every deck in the station on `HABITABLE_G_MAX = 1.25`
(INV-027). Grey's outer 34 decks come out above it -- 350.4 m to 471.2 m,
**1.26 g to 1.69 g** -- and are tagged `plant`. Until now the streaming manifest
priced all 34 with the corridor kit: **62.3 M triangles, 26% of the station's
entire interior**, for volume that is not rooms. `budget.py` flags it as
"priced with the corridor kit as a placeholder". This is the kit that replaces
the placeholder.

`docs/gazetteer/LIFE-SUPPORT-AND-INDUSTRY.md` sized the problem and the answer
is emphatic. The plant zone is **139.8 million m3, 559 m3 per resident**, and a
thirty-day water reserve for all 250,000 people is **397,500 m3 -- 0.3% of it**.
Life support does not need 34 decks. It needs about one. So the plant zone is
predominantly **structure, tankage and void**, with a thin walkable skeleton
threaded through it, and any kit that fills it with floors is building
something absurd.

THE ONE STRUCTURAL DECISION HERE
--------------------------------
**Plant space is not decked at `DECK_PITCH_M`.** A 3.6 m floor-to-floor pitch
is a corridor's pitch; a tank farm wants height. So the 34 plant decks are
regrouped into `BAY_DECKS`-deck **bays**, and the bay -- not the deck -- is the
unit this module builds. That is why `plant_bay()` takes a bay index and not a
deck index, and it is the whole reason the kit is cheap: one bay carries a few
large objects where the corridor kit would have carried five decks of wall.

The decks themselves are NOT deleted from the manifest. They still exist as
addresses and as gravity, because Downbelow is addressed by deck and a lurker
squatting at 1.4 g is on a numbered deck. What changes is what is built there.

DOWNBELOW LIVES HERE, AND THAT IS NOT A COMPLICATION
----------------------------------------------------
`interior.py` is explicit that `use == "plant"` means UNASSIGNED, not
uninhabited. `docs/gazetteer/LOCATIONS.md` puts Downbelow "near the outer hull,
around the waste recycling system, the air compressors and the water
reclamation facility" -- outermost rings, highest gravity in the sector,
"corridors and chambers, not rooms".

Those are these decks. So this kit is Downbelow's architecture as well as the
plant's, and it is deliberately built to be squatted in: the catwalk network is
continuous, the frames make alcoves, and nothing here is finished the way a
corridor is finished. One kit, two readings, which is the cheapest possible way
to get the station's most characterful district.

SOURCING
--------
Nothing in the show establishes a tank, a frame or a catwalk dimension. Every
number below is an extrapolation and is logged as **INV-028**. What they are
constrained BY is real and is stated per constant: the deck stack they must fit
inside, the gravity they carry, the reserve volume they must hold, and the
triangle budget they must come in under.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402

# ---------------------------------------------------------------------------
# The bay
# ---------------------------------------------------------------------------
# Five decks to a bay. Constrained from both sides: fewer than four and a bay
# is too short for a tank worth plumbing, more than six and the 34 decks stop
# dividing into a whole number of bays without a runt. 34 / 5 leaves 4 decks
# over, which become a shallower top bay rather than being dropped -- a runt
# bay is still real volume and pretending otherwise is how a hole gets shipped.
BAY_DECKS = 5

# Structural frames. These carry a 1.7 g load path, which is why they are deep:
# at the plant's outermost radius a tonne of water weighs 1.69 tonnes, and the
# frames are the reason the outer stack can hold tankage at all.
FRAME_DEPTH_M = 2.4        # radial depth of a frame member
FRAME_WIDTH_M = 1.1        # section across
FRAME_PITCH_DEG = 2.5      # circumferential spacing between radial frames
FRAME_PITCH_Z_M = 36.0     # longitudinal spacing between frame rings

# Tanks. Axis RADIAL, because in spin gravity "vertical" means radial -- a tank
# stands on its outer end and its contents settle outward. Sized to sit inside
# a bay with clearance for the catwalk and the frames.
TANK_R_M = 4.5             # radius of a tank cylinder
TANK_CLEAR_M = 1.6         # clearance from tank wall to frame face
TANK_SEG = 14              # facets round a tank -- it is seen at 5-30 m, never closer
TANK_CAP_RISE = 0.35       # domed end, as a fraction of tank radius

# Tanks come in FARMS, not as a wall-to-wall tiling of the annulus. The first
# attempt tiled, and the self-test caught it: 65.1 million m3 of tankage
# against a 397,500 m3 requirement -- 164x over, and 46.6% of the plant zone
# filled in. That is exactly the error LIFE-SUPPORT-AND-INDUSTRY.md warns
# against. The zone is 559 m3 per resident and ~100x what life support needs;
# a kit that fills it has misread the finding that produced it.
#
# So: a farm every FARM_PITCH_DEG round and every FARM_PITCH_Z_M along, each
# holding a small block of tanks, and structure-and-void between them. The
# reserve assertion stays real because the farm SPACING could be too sparse to
# hold thirty days of water -- it is not derived from the volume it must meet.
FARM_PITCH_DEG = 30.0
FARM_PITCH_Z_M = 100.0
FARM_TANKS_A = 2           # tanks across a farm, circumferentially
FARM_TANKS_Z = 2           # tanks along a farm, longitudinally

# The walkable skeleton. One catwalk per bay, running ALONG the arc -- the
# direction a person actually travels in a ring -- and 1.8 m wide across, in z.
#
# The first version spanned the full arc AND the full z extent, which is not a
# catwalk but a 158 m x 120 m plate, and it used CATWALK_W_M as a radial offset
# rather than as a width. Both wrong, and both obvious the moment it was
# rendered from standing height.
CATWALK_W_M = 1.8          # across the walkway, in z
CATWALK_CLEAR_M = 2.4      # deck to the bay's inner face -- this is HEADROOM
# 1.8 m was the first value and it is a crawl space: a 1.7 m person had 100 mm
# of clearance. The assertion guarding it read `>= 1.8`, which is the value
# itself, so it could not object. Both fixed.
CATWALK_T_M = 0.14
RAIL_H_M = 1.05
RAIL_R_M = 0.045
RAIL_POST_PITCH_M = 2.2

# Pipe runs, clamped along the frames. The single most legible feature in the
# volume, for the same reason the exterior's conduit runs are (session 2n): one
# long line reads at any distance where fifty scattered boxes read as noise.
PIPE_R_M = 0.45
PIPE_SEG = 8
# Articulation runs -- INV-073's rule in a cylindrical hall. All long, all thin.
SERVICE_RUNS = 6
SERVICE_OFFSET_M = 2.2
CONDUIT_R_M = 0.11
TRAYS = 3
TRAY_W_M = 0.42
TRAY_D_M = 0.14
SECONDARY_TIE_M = 7.0
TIE_D_M = 0.22
TIE_W_M = 0.30
RAIL_T_M = 0.06
PIPES_PER_FRAME = 3

# ---------------------------------------------------------------------------
# Light fittings
# ---------------------------------------------------------------------------
# LAYER 4. This module built no light of any kind, and the first interior frame
# of a plant bay was 85% black -- two tanks in the dark. That is not a lighting
# defect, it is a missing object, in exactly the way `rooms.FIXTURES` was.
#
# The measured family is the SERVICE CORRIDOR in docs/layer4-lighting/
# corridor_kit.json, whose finding is the whole character of this space: its
# balanced median luminance is 0.060 against a residential corridor's 0.265,
# and "its walls are black except where a panel or the deck strip reaches
# them". A plant bay should be lit exactly that much and no more -- and
# Downbelow squats in these frames, which is the same argument twice.
#
# TWO FITTINGS, and the split matters:
#
#   light_service_tube  MEASURED EMISSIVE ONLY. Cold blue vertical tubes on
#                       the frames, flanking the catwalk. The measurement is
#                       explicit that they flank a service corridor in pairs
#                       and that they light nothing -- they are the thing you
#                       see, not the thing that lets you see. Aspect ~13:1 for
#                       the lower run, which at 0.11 m across is 1.43 m tall.
#   light_plant_flood   The docking bay's flood, and it transfers WITHOUT
#                       SCALING for once: `bay_flood` was measured at 30 m
#                       range in an 18 m bay, and a five-deck plant bay is
#                       5 x DECK_PITCH_M = 18 m. The one number in this file
#                       that did not have to be argued.
#
# Both are hung off the CATWALK, because that is where a person is. Everything
# outboard of it is tankage that nobody stands in, and lighting the tank farm
# evenly would read as a warehouse rather than as a thin walkable skeleton
# threaded through 139.8 million cubic metres of machinery.
#
# INV-037 records the archetype-to-fitting mapping this follows.
TUBE_W_M = 0.11            # across the tube -- gives 13:1 at TUBE_H_M
TUBE_H_M = 1.43            # measured aspect for the lower run
TUBE_SILL_M = 0.60         # deck to the bottom of the tube, so it reads at
                           # head height rather than as a skirting light
TUBE_PITCH_M = 7.2         # two deck frames apart along the catwalk: the
                           # measurement gives no pitch, only "they flank the
                           # corridor in pairs", and a pair every other frame
                           # is what leaves the walls between them dark
TUBE_PROUD_M = 0.12        # clear of the catwalk edge, on the frame face
FLOOD_M = 0.80             # a flood housing, square
FLOOD_DROP_M = 0.34
FLOOD_PITCH_M = 11.0       # MEASURED: bay_flood's own spacing, and the bay it
                           # was measured in is the same 18 m deep as this one

# What the tankage has to hold, from LIFE-SUPPORT-AND-INDUSTRY.md L-04:
# 13,250 m3/day of water throughput, thirty days of reserve.
RESERVE_M3 = 397_500.0


def _cyl(verts, tris, groups, name, cx, cy, z0, z1, r, seg=TANK_SEG,
         cap_lo=True, cap_hi=True, face_out=True, cap_rise=TANK_CAP_RISE):
    """A cylinder with its axis along +Z, optionally capped.

    `cap_rise` IS A FLAT CAP AT 0.0, and a pipe wants one. A domed head is a
    pressure vessel's end and a tank has two of them; a pipe that runs on into
    the next cell is cut off square where the cell ends. The module's own
    `_selftest` is what said so: capping the pipes to close 192 open edges put
    a 0.157 m dome 0.157 m PAST z1, and "the bay stays inside the sector
    longitudinally" fired on the overshoot -- a gate written for a different
    reason catching a change nobody thought touched it.

    `face_out` exists because this module builds both containers seen from
    outside (tanks) and nothing seen from inside, so getting it wrong is a
    silent black object rather than an error. Asserted in `_selftest`.
    """
    n0 = len(verts)
    for k in range(seg):
        a = math.tau * k / seg
        verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z0))
        verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z1))
    t0 = len(tris)
    for k in range(seg):
        a0, b0 = n0 + 2 * k, n0 + 2 * ((k + 1) % seg)
        a1, b1 = a0 + 1, b0 + 1
        if face_out:
            tris += [(a0, b0, b1), (a0, b1, a1)]
        else:
            tris += [(a0, b1, b0), (a0, a1, b1)]
    for cap, zc, up in ((cap_lo, z0, False), (cap_hi, z1, True)):
        if not cap:
            continue
        c = len(verts)
        verts.append((cx, cy, zc + (cap_rise * r if up else -cap_rise * r)))
        for k in range(seg):
            a = n0 + 2 * k + (1 if up else 0)
            b = n0 + 2 * ((k + 1) % seg) + (1 if up else 0)
            tris.append((c, a, b) if up else (c, b, a))
    groups.append((name, t0, len(tris)))


def _box(verts, tris, groups, name, lo, hi):
    """An axis-aligned box, wound outward. Corners (x0,y0,z0)-(x1,y1,z1)."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(verts)
    verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(tris)
    f = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3))
    for a, b, c, d in f:
        tris += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    groups.append((name, t0, len(tris)))
    return verts, tris, groups


def _arc_band(verts, tris, groups, name, r0, r1, z0, z1, start_deg, arc_deg,
              seg=None):
    """A closed box bent round the axis: an arc segment of an annulus.

    Built directly in world coordinates because it is inherently circumferential
    -- there is no flat authoring frame for it that `_place` could map without
    distorting the arc. Wound outward.
    """
    seg = seg or max(2, int(arc_deg / 2.0))
    n0 = len(verts)
    for k in range(seg + 1):
        a = math.radians(start_deg + arc_deg * k / seg)
        ca, sa = math.cos(a), math.sin(a)
        for r in (r0, r1):
            for z in (z0, z1):
                verts.append((r * ca, r * sa, z))
    t0 = len(tris)

    def idx(k, ri, zi):
        return n0 + k * 4 + ri * 2 + zi

    for k in range(seg):
        # four longitudinal faces of the bent box
        for (ra, za), (rb, zb) in (((0, 0), (1, 0)), ((1, 1), (0, 1)),
                                   ((1, 0), (1, 1)), ((0, 1), (0, 0))):
            a0, b0 = idx(k, ra, za), idx(k, rb, zb)
            a1, b1 = idx(k + 1, ra, za), idx(k + 1, rb, zb)
            tris += [(a0, b0, b1), (a0, b1, a1)]
    # end caps
    for k, flip in ((0, True), (seg, False)):
        q = [idx(k, 0, 0), idx(k, 1, 0), idx(k, 1, 1), idx(k, 0, 1)]
        tri = [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
        tris += [(a, c, b) for a, b, c in tri] if flip else tri
    groups.append((name, t0, len(tris)))
    return verts, tris, groups


def _place(verts, angle_deg, radius_shift=0.0):
    """Take geometry authored in a local frame -- x across, y radial, z along
    the station axis -- and set it on the drum at an angle.

    **THIS MAP REVERSES WINDING AND CALLERS MUST FLIP.** Its Jacobian is
    d/dx = (-sin, cos, 0), d/dy = (cos, sin, 0), d/dz = (0, 0, 1), whose
    determinant is -1: local +x becomes tangential and local +y becomes radial,
    which is a left-handed pair. Everything through it comes out inside-out.

    Found by rendering the catwalk and seeing the magenta background THROUGH
    the floor I was standing on. `CONTRIBUTING.md` records this exact defect
    twice already -- `_box` emitting inward-wound solids, and `corridor_section`
    laying its deck through a negative-determinant remap with no reversal. It
    is the third time, so `_absorb` now takes the flip and `_selftest` asserts
    that placed solids still enclose positive volume.

    Authoring flat and placing by rotation is the same discipline the interior
    kit uses. Building directly in cylindrical coordinates is how the docking
    bay ended up 0.9 m outside the pressure hull: a bay cut into a rotating
    hull follows an ARC, and the arc has to be applied once, in one place.
    """
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y, z in verts:
        r = y + radius_shift
        # local +x is tangential, so it becomes an arc offset at radius r
        t = x / max(r, 1e-9)
        rr, aa = r, a + t
        out.append((rr * math.cos(aa), rr * math.sin(aa), z))
    return out


def plant_decks(schema, profile, sector=None):
    """Every deck in a sector tagged `plant`, outermost first."""
    if sector is None:
        sector = "grey"
    out = []
    for ri, ring in enumerate(it.ring_radii(schema, profile, sector)):
        if ring["kind"] != "deck_stack":
            continue
        out += [d for d in it.decks_in_ring(schema, profile, sector, ri)
                if d["use"] == "plant"]
    return out


def bays(schema, profile, sector=None):
    """Group the plant decks into bays, outermost first.

    The last bay is allowed to be shallower than `BAY_DECKS` rather than being
    dropped. 34 decks in fives leaves four over, and four decks of real volume
    silently vanishing is exactly the class of hole this project has shipped
    before -- the drum end cap was "done" for four sessions and was 4,064 open
    edges.
    """
    d = plant_decks(schema, profile, sector)
    out = []
    for i in range(0, len(d), BAY_DECKS):
        chunk = d[i:i + BAY_DECKS]
        out.append({
            "bay_index": len(out),
            "decks": len(chunk),
            # Floors are at the LARGER radius; the stack runs inward as index
            # rises, so the bay's outer face is its first deck's floor.
            "r_outer": chunk[0]["floor_r_m"],
            "r_inner": chunk[-1]["ceiling_r_m"],
            "height_m": chunk[0]["floor_r_m"] - chunk[-1]["ceiling_r_m"],
            "floor_g": chunk[0]["floor_g"],
            "deck_indices": [c["deck_index"] for c in chunk],
        })
    return out


def tanks_in_bay(bay):
    """How many tanks fit across a bay, and at what radius they stand.

    Derived from the bay's own height rather than chosen: a tank stands on the
    bay's outer face and must clear the catwalk at the inner face. If a bay is
    too shallow for a tank it gets none, and that is a real answer -- the runt
    bay at the top of the stack is structure and pipe, not tankage.
    """
    usable = bay["height_m"] - CATWALK_W_M - 2 * TANK_CLEAR_M
    if usable < 2.0 * TANK_R_M:
        return {"count": 0, "height_m": 0.0, "r_base": bay["r_outer"]}
    return {"count": 1, "height_m": usable, "r_base": bay["r_outer"] - TANK_CLEAR_M}


def bay_for_deck(schema, profile, place):
    """The bay a gazetteer place's own deck index falls in.

    `bespoke.BESPOKE_GEOMETRY` took `bays(...)[0]` for all five plant places,
    so `water_reclamation` (deck 5, 1.63 g), `air_compressors` (deck 10,
    1.56 g) and `downbelow_arch` (deck 20, 1.40 g) all rendered the OUTERMOST
    bay -- one room repeated four times at the wrong gravity. A bay's radius is
    the only thing that distinguishes these places from each other physically,
    and the register already records which deck each is on.

    Matched on `deck_indices` rather than by `deck // BAY_DECKS`, because the
    plant decks are a FILTERED subset of the ring's decks (`plant_decks` keeps
    only those above `HABITABLE_G_MAX`) and the arithmetic would only be right
    if the filter kept a prefix. Falls back to the outermost bay for a deck the
    filter does not name, which is the behaviour every caller had before.
    """
    want = place["deck"]
    for b in bays(schema, profile, place.get("sector")):
        if want in b["deck_indices"]:
            return b
    return bays(schema, profile, place.get("sector"))[0]


def room_cell(schema, profile, place):
    """A plant bay the size of the ROOM the register addresses. INV-231.

    THE PLACEMENT DECISION `bespoke.NEAR_END_UNKNOWN` ASKED FOR, and it turns
    out not to be a near-end question at all. That entry says plant "needs a
    placement decision, not a near-end declaration", on the measurement that
    the catwalk's floor band is 82.2 x 1.80 m inside a 92 x 442 m bay -- so
    recentring it onto a ring deck "would lay 442 m of tank farm along the
    station's axis, through every other z-cluster on that deck". That is
    correct about the geometry and the cause is one argument, not the module:
    `plant_bay` was being called with `arc_deg=10.0` and NO `z_span`, so it
    defaulted to the whole GREY SECTOR, 442 m of it. The bay was the size of
    the sector because it was asked for the size of the sector.

    Asked for the size of the room instead, it builds one. Three numbers, all
    of them read off the register rather than chosen:

      * **the arc** is the collision shell's own width. `deck.room_shell_for`
        sizes what a player walks inside from `rooms.room_extent_m` clamped by
        `rooms.bay_span_m`, and it does NOT look at the module's mesh -- so a
        composed room wider than that is render geometry outside its own
        collision. `plant_zone`'s shell is 13.5 m across; a 10-degree bay is
        82.2 m. Taking the angle that subtends 13.5 m at the catwalk's radius
        makes the two agree by construction.
      * **the axis** is `min(l_full, bay_l) / 2` either side of the place's own
        `z_m` -- the same expression `deck.room_interior_half_m` uses, computed
        from `rooms` directly so this module does not have to import the
        assembler that imports it.
      * **the walkway** goes hard against the near face, which is the maximum-z
        end, because that is the end the ring corridor is on. See `plant_bay`'s
        own docstring for why the middle of the cell does not work.

    Returns what every other `BESPOKE_GEOMETRY` entry returns: (verts, tris,
    groups) in STATION coordinates. `bespoke.UNROLL` flattens the arc.
    """
    import rooms as _R                                          # noqa: PLC0415
    bay = bay_for_deck(schema, profile, place)
    w_full, l_full, _r = _R.room_extent_m(schema, profile, place)
    bw, bl = _R.bay_span_m(place)
    half_w = min(w_full, bw) / 2.0
    half_l = min(l_full, bl) / 2.0

    # THE WALKWAY IS THE ADDRESSED DECK'S OWN FLOOR. Every one of the five
    # plant places is addressed to the OUTERMOST deck of its bay -- plant_zone
    # and downbelow to deck 0, water_reclamation to 5, air_compressors to 10,
    # downbelow_arch to 20, and `bays()` starts a bay at every fifth deck -- so
    # `bay["r_outer"]` IS that deck's floor radius to within 50 mm. Standing
    # there is what makes the room continuous with the corridor that serves it,
    # which is `deck.build_deck`'s own rule: "a step between a corridor and a
    # room is a trip hazard the walk test would find and a player would feel".
    #
    # It is also the only choice that keeps the room inside the station. The
    # module's own gantry sits at `r_inner + CATWALK_CLEAR_M`, 15.6 m inboard
    # of the outer face; `room_shell` puts the walkable floor at y = 0 and
    # `_place_local` puts y = 0 at the corridor's radius, so the other 15.6 m
    # of bay would land OUTBOARD of the corridor floor -- and deck 0's floor is
    # the outermost radius in the whole stack. plant_zone's tank farm would
    # hang through the pressure hull.
    r_walk = bay["r_outer"]
    # The angle that subtends the shell's width AT THE WALKWAY, not at the
    # bay's outer face -- the two coincide here and the expression is written
    # against the walkway anyway, because that is the surface the width has to
    # be right on and a future bay choice may separate them again.
    # BUILT TO THE INSIDE OF ITS OWN EDGE MEMBERS, because the pieces at a
    # cell's boundary are CENTRED on it. An edge frame is FRAME_WIDTH_M across,
    # so half of it (0.55 m) hangs outside on each side; the far-side service
    # tube stands TUBE_PROUD_M past the rail line and is TUBE_W_M across, so
    # 0.175 m of it hangs past the far face. Both are outside the collision
    # shell `deck.room_shell_for` sizes from `bay_span_m` -- geometry a body
    # has to walk through a wall to reach -- and `_selftest` measures it.
    #
    # Only the FAR z face is pulled in: `room_shell` translates the mesh so its
    # maximum z lands on the assembler's plane, so shrinking the near face
    # would not make the room smaller, it would move it and leave the walkway
    # short of the doorway.
    # ...and the frame's half width has to be measured AFTER the unroll, not
    # before it. `bespoke.unroll_to_local` maps angle to arc length at the
    # geometry's LARGEST radius, and a radial frame spans the bay's whole 18 m
    # of depth -- so its inner end, drawn 0.55 m across at r_inner, comes out
    # 0.55 * r_outer / r_inner wide. 22 mm a side, and the fit gate is at 20.
    edge_x = FRAME_WIDTH_M / 2.0 * bay["r_outer"] / bay["r_inner"]
    edge_z = TUBE_PROUD_M + TUBE_W_M / 2.0
    arc_deg = math.degrees(2.0 * (half_w - edge_x) / r_walk)
    start_deg = place["angle_deg"] - arc_deg / 2.0
    z0, z1 = place["z_m"] - half_l + edge_z, place["z_m"] + half_l

    # HOW MANY TANKS FIT, derived from the cell rather than chosen. A tank is
    # `2 * TANK_R_M + TANK_CLEAR_M` on centres, and `plant_bay` additionally
    # refuses any whose centre is within TANK_R_M of an end -- so a 9.96 m cell
    # holds exactly one along the axis and asking for the exterior's two puts
    # both of them outside the window and builds none at all. That is how the
    # reclamation facility came out empty even with the farm anchored on it.
    # AND WHETHER ONE FITS AT ALL, WHICH IS A REAL ANSWER AND IS *NO*.
    #
    # THE RENDER IS WHAT SETTLED THIS and no assertion would have. The first
    # version asked only whether the tank's 9.0 m diameter fitted inside the
    # cell, which `plant_zone` and `water_reclamation` pass at 13.56 x 9.65 m --
    # and `docs/x-plant-inside.png`, taken from the player camera standing in
    # the middle of the composed room, is the inside of a tank wall filling the
    # frame. A tank that fits a room is not the same claim as a room you can
    # walk round a tank in.
    #
    # So the test is FIT PLUS AISLE, and the aisle is `rooms.WALK_M` -- this
    # project's own clear-path constant, the one `rooms.build` falls through
    # `DRESS_DENSITIES` to protect. A tank needs `2 * TANK_R_M + 2 * WALK_M` =
    # 10.8 m in both directions.
    #
    # Measured across all five plant places, NOT ONE PASSES:
    #
    #     plant_zone         13.56 x  9.65   depth 1.15 m short
    #     downbelow          10.15 x 11.55   width 0.65 m short
    #     downbelow_arch      7.72 x 10.80   width 3.08 m short
    #     water_reclamation  13.56 x  9.65   depth 1.15 m short
    #     air_compressors     9.91 x  5.70   both short
    #
    # That is not a failure and it is not a number to soften. TANK_R_M is a
    # BAY-scale object -- INV-028 sizes it against an 18 m bay -- and the five
    # addressed places are DECK-scale rooms, because `rooms.bay_span_m` clamps
    # each of them to one representative bay. The gazetteer already says what
    # goes in the rest: "the plant zone is predominantly structure, tankage and
    # void", and "life support does not need 34 decks, it needs about one". A
    # room-sized cell of it is structure. The tank farms are the same bay, past
    # the frames, and a cell that happens to be sited on one is what `farm_at =
    # None` still builds for every streaming cell in the outer stack.
    #
    # The mechanism stays because it is what MEASURES this rather than what
    # asserts it: widen a place's footprint or raise `bay_span_m` and a room
    # that can hold a tank gets one, here, without anything else changing.
    import rooms as _RW                                          # noqa: PLC0415
    step = 2 * TANK_R_M + TANK_CLEAR_M
    need = 2 * TANK_R_M + 2 * _RW.WALK_M
    fits = (2.0 * half_w >= need) and ((z1 - z0) >= need)
    n_a = int(2.0 * half_w / (2 * TANK_R_M)) if fits else 0
    n_z = max(1, int(max(0.0, (z1 - z0) - 2 * TANK_R_M) / step) or 1)
    farm_at = [place["angle_deg"]] if n_a >= 1 else []
    return plant_bay(schema, profile, bay, arc_deg, start_deg=start_deg,
                     z_span=(z0, z1), sector=place.get("sector"),
                     # THE FARM IS ON THE PLACE, not on the station lattice --
                     # the register addressing a water reclamation facility IS
                     # the statement that the tankage is here.
                     farm_at=farm_at, farm_tanks=(max(1, n_a), n_z),
                     # THE FLOOR IS THE CELL. 1.8 m of gantry is what the
                     # streaming volume wants and it is not a room: it leaves
                     # `near_face_opening` no floor at the door, and it hands
                     # `dressing.dress` a 1.8 x 14 m strip, which furnishes a
                     # corridor. An addressed machine room is a room.
                     walk_r=r_walk, walk_w=(z1 - z0),
                     walk_z=(z0 + z1) / 2.0,
                     # THE FRAMES ARE THE ROOM'S SIDE WALLS. One frame in the
                     # middle of a 13.5 m room is an 18 m column where the
                     # furniture and the people go.
                     frame_at=[start_deg, start_deg + arc_deg],
                     # ...and the rail and the service tubes go on the FAR side
                     # only: the near side is the wall the corridor's door is
                     # in, and a tube stands TUBE_PROUD_M past the rail line.
                     walk_sides=(-1,))


def plant_bay(schema, profile, bay, arc_deg, start_deg=0.0, z_span=None,
              sector=None, walk_z=None, walk_w=None, walk_r=None,
              walk_sides=(-1, 1), farm_at=None, farm_tanks=None,
              frame_at=None):
    """One bay of plant over an arc: frames, tankage, catwalk and pipe runs.

    THE FOUR `walk_*` ARGUMENTS ARE THE PLACEMENT DECISION, and they exist
    because a plant cell has two entirely different jobs. INV-231. All four
    default to what this module has always built, so the streaming cells and
    the exterior are unchanged; `plant.room_cell` is the only caller that sets
    them, and its docstring is where the reasoning for each value lives.

    As a STREAMING CELL of the outer stack -- which is all this module built
    until now -- the walkable skeleton is a 1.8 m catwalk down the middle of
    the cell at the bay's INNER face, a gantry over the tank farm. That is
    right for 442 m of axis with no door anywhere in it, and it is what the
    gazetteer's "thin walkable skeleton threaded through it" describes.

    As a ROOM ON A RING DECK none of those three choices survives contact with
    the corridor, and each fails for its own measurable reason:

      * `walk_z` -- a walkway down the middle of a 9.96 m cell is 2.1 m short
        of `bespoke.APPROACH_DEPTH_M`, so `near_face_opening` finds no floor at
        the door and the room is not enterable.
      * `walk_r` -- the catwalk sits at `r_inner + CATWALK_CLEAR_M`, 15.6 m
        inboard of the bay's outer face. `bespoke.room_shell` puts the walkable
        floor at y = 0 and `deck._place_local` puts y = 0 at the CORRIDOR's own
        radius, so the bay's other 15.6 m lands OUTBOARD of the corridor floor
        -- and `plant_zone` and `downbelow` are addressed to deck 0, whose
        floor is the outermost radius in the stack. Their tank farm would hang
        through the pressure hull.
      * `walk_w` -- 1.8 m of floor is a gantry, and `dressing.dress` handed
        1.8 m by 14 m furnishes a corridor. An addressed machine room is a room
        you stand in, and its floor is the cell's floor.

    `walk_sides` follows from the others rather than being a fourth decision:
    the rail and the service tubes are built per side of the walkway, and the
    side against the doorway wall may carry neither. A walkway along a bulkhead
    is railed on its open side only -- a 1.05 m rail across the aperture is
    exactly what `deck._mouth_clear`'s 0.735 m probe calls a wall, and a
    service tube stands `TUBE_PROUD_M` past the rail line, which on a full-cell
    floor is 0.12 m PAST the near face and silently moves the whole room up the
    axis when `room_shell` recentres on it.
    """
    if sector is None:
        sector = "grey"
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = z_span if z_span else (ex["z0"], ex["z1"])
    verts, tris, groups = [], [], []

    r_out, r_in = bay["r_outer"], bay["r_inner"]
    spec = tanks_in_bay(bay)
    # The walkable surface, resolved BEFORE the tankage because the tanks are
    # seated on it. See the four `walk_*` paragraphs in the docstring.
    r_walk = r_in + CATWALK_CLEAR_M if walk_r is None else float(walk_r)
    walk_w = CATWALK_W_M if walk_w is None else float(walk_w)
    zc_walk = (z0 + z1) / 2.0 if walk_z is None else float(walk_z)

    # --- deep frames ------------------------------------------------------
    # Radial members at FRAME_PITCH_DEG round, tied by circumferential rings at
    # FRAME_PITCH_Z_M along. These are the 1.7 g load path.
    # `frame_at` PUTS THE FRAMES ON THE CELL'S EDGES, and the default puts them
    # on its lattice. A streaming cell is an arbitrary slice of a continuous
    # annulus, so its frames belong at FRAME_PITCH_DEG intervals inside it and
    # a cell narrower than one pitch gets a single frame at its middle. A ROOM
    # is not an arbitrary slice: its two ends are its side walls, and a 1.1 m
    # by 18 m column standing in the middle of a 13.5 m room is the one place
    # nothing should be. `docs/x-plant-inside.png` was taken from the player
    # camera at the place's own angle and is the inside of that column.
    if frame_at is not None:
        angles = list(frame_at)
    else:
        n_rad = max(1, int(arc_deg / FRAME_PITCH_DEG))
        angles = [start_deg + (i + 0.5) * arc_deg / n_rad for i in range(n_rad)]
    for a in angles:
        local, lt, lg = [], [], []
        _box(local, lt, lg, "plant_frame",
             (-FRAME_WIDTH_M / 2, r_in, z0), (FRAME_WIDTH_M / 2, r_out, z1))
        _absorb(verts, tris, groups, _place(local, a), lt, lg, flip=True)

    # Circumferential ties, ARC-LIMITED to the cell.
    #
    # These were built with `_cyl(..., 0, 0, ..., r_out - FRAME_DEPTH_M/2)`,
    # which is a full 360-degree cylinder of 470 m radius -- every cell
    # carrying a complete ring round the entire station. Same family as the
    # pipe bug below: a radius used where an extent was meant. It filled the
    # frame with a grey plane and the render is what found it.
    #
    # The size gate did NOT catch it, and the reason is worth keeping: the gate
    # measures VERTEX radii, and every vertex of a coarse polygon sits at the
    # same radius even though its edges cut far inside. Gates that sample
    # vertices cannot see chords.
    n_ring = max(1, int((z1 - z0) / FRAME_PITCH_Z_M))
    for j in range(n_ring):
        zc = z0 + (j + 0.5) * (z1 - z0) / n_ring
        _arc_band(verts, tris, groups, "plant_frame_ring",
                  r_out - FRAME_DEPTH_M, r_out,
                  zc - FRAME_WIDTH_M / 2, zc + FRAME_WIDTH_M / 2,
                  start_deg, arc_deg)

    # --- tankage ----------------------------------------------------------
    # `farm_at` OVERRIDES THE LATTICE, and the reason is `rooms.FIXTURES`'
    # lesson in this module's costume: the register addresses a place called
    # "Water reclamation facility", and the station-wide farm lattice is
    # FARM_PITCH_DEG = 30 degrees apart, so a 1.7-degree room-sized cell lands
    # between two farms about 94 times in a hundred and the reclamation
    # facility contains no tank. "Fabrication furnaces was a grey box holding
    # two control podiums and no furnace" is the same sentence.
    #
    # The lattice is right for a STREAMING CELL -- it is anchored to absolute
    # angle precisely so two neighbours cannot each put a farm just inside
    # their shared seam -- and it is the wrong question for an ADDRESSED PLACE,
    # where the register has already said where the machinery is. So the caller
    # may name the farm centres; `None` keeps the lattice and the exterior
    # build is unchanged.
    if spec["count"]:
        step = 2 * TANK_R_M + TANK_CLEAR_M
        step_deg = math.degrees(step / max(r_out, 1e-9))
        n_a, n_z = farm_tanks or (FARM_TANKS_A, FARM_TANKS_Z)
        # A TANK STANDS ON THE FLOOR THE CALLER NOMINATED. `tanks_in_bay` seats
        # it `TANK_CLEAR_M` inboard of the bay's outer face, which is right
        # while the walkway is a gantry at the bay's INNER face and wrong the
        # moment `walk_r` puts the walkable surface at the outer face -- there
        # the same tank hangs 1.6 m in the air over the deck a body is standing
        # on. Seated on `r_walk` with its top left where it was, so the fit test
        # in `tanks_in_bay` still governs whether there is one at all.
        r_base = spec["r_base"]
        t_height = spec["height_m"]
        if walk_r is not None:
            top = r_base - t_height
            r_base = r_walk
            t_height = max(1.0, r_base - top)
        centres = (list(farm_at) if farm_at is not None
                   else _farm_angles(start_deg, arc_deg))
        for fa in centres:
            for fz in _farm_zs(z0, z1):
                for i in range(n_a):
                    a = fa + (i - (n_a - 1) / 2.0) * step_deg
                    for j in range(n_z):
                        zc = fz + (j - (n_z - 1) / 2.0) * step
                        if not (z0 + TANK_R_M <= zc <= z1 - TANK_R_M):
                            continue
                        local, lt, lg = [], [], []
                        _tank_radial(local, lt, lg, zc, r_base,
                                     r_base - t_height)
                        _absorb(verts, tris, groups, _place(local, a), lt, lg,
                                flip=True)

    # --- the walkable skeleton -------------------------------------------
    # Runs ALONG the arc -- the direction a person travels in a ring -- and is
    # CATWALK_W_M wide across, in z. The deck surface is at `r_walk`, and a
    # person standing on it has their head at a SMALLER radius, because down is
    # outward.
    #
    # The first version spanned the full arc AND the full z extent, which is
    # not a catwalk but a 158 m x 120 m plate, and it used CATWALK_W_M as a
    # radial offset rather than as a width. Both obvious the moment it was
    # rendered from standing height, and neither visible to any assertion.
    mid = start_deg + arc_deg / 2
    half_len = arc_length(r_walk, arc_deg) / 2

    local, lt, lg = [], [], []
    _box(local, lt, lg, "plant_catwalk",
         (-half_len, r_walk, zc_walk - walk_w / 2),
         (half_len, r_walk + CATWALK_T_M, zc_walk + walk_w / 2))
    _absorb(verts, tris, groups, _place(local, mid), lt, lg, flip=True)

    # Posts along both long edges, then one top rail per side. Rail height is
    # measured INWARD from the deck, because inward is up.
    n_post = max(2, int(2 * half_len / RAIL_POST_PITCH_M))
    for side in walk_sides:
        zr = zc_walk + side * walk_w / 2
        for j in range(n_post):
            xw = (-half_len + RAIL_R_M
                  + j * (2 * half_len - 2 * RAIL_R_M) / max(n_post - 1, 1))
            local, lt, lg = [], [], []
            _box(local, lt, lg, "plant_rail",
                 (xw - RAIL_R_M, r_walk - RAIL_H_M, zr - RAIL_R_M),
                 (xw + RAIL_R_M, r_walk, zr + RAIL_R_M))
            _absorb(verts, tris, groups, _place(local, mid), lt, lg, flip=True)
        local, lt, lg = [], [], []
        _box(local, lt, lg, "plant_rail",
             (-half_len, r_walk - RAIL_H_M - RAIL_R_M, zr - RAIL_R_M),
             (half_len, r_walk - RAIL_H_M + RAIL_R_M, zr + RAIL_R_M))
        _absorb(verts, tris, groups, _place(local, mid), lt, lg, flip=True)

    # --- light fittings ---------------------------------------------------
    # See the LIGHT FITTINGS block above. Hung off the catwalk, in the
    # catwalk's own frame, so they cannot drift away from the walkway they
    # light: `half_len`, `r_walk` and `zc_walk` are the same three values the
    # deck and its rails were built from a few lines up.
    n_tube = max(2, int(2 * half_len / TUBE_PITCH_M))
    for side in walk_sides:
        # Just outboard of the rail line, on the frame face. Inward is up, so
        # the tube runs from r_walk - TUBE_SILL_M to a SMALLER radius.
        #
        # AND IT IS `walk_sides`, NOT `(-1, 1)`, FOR A SECOND REASON BEYOND
        # THE DOORWAY: the tube stands TUBE_PROUD_M past the rail line, so on a
        # walkway hard against the cell's near face it would be the one piece
        # of geometry OUTSIDE the plane `bespoke.room_shell` recentres on --
        # which does not fail, it silently moves the whole room 0.12 m up the
        # axis and puts the tubes in the corridor.
        zr = zc_walk + side * (walk_w / 2 + TUBE_PROUD_M)
        for j in range(n_tube):
            xw = (-half_len + TUBE_W_M
                  + j * (2 * half_len - 2 * TUBE_W_M) / max(n_tube - 1, 1))
            local, lt, lg = [], [], []
            _box(local, lt, lg, "light_service_tube",
                 (xw - TUBE_W_M / 2, r_walk - TUBE_SILL_M - TUBE_H_M,
                  zr - TUBE_W_M / 2),
                 (xw + TUBE_W_M / 2, r_walk - TUBE_SILL_M,
                  zr + TUBE_W_M / 2))
            _absorb(verts, tris, groups, _place(local, mid), lt, lg, flip=True)

    # Floods on the bay's inner face, over the catwalk, throwing outward --
    # which under spin is down. They are the only thing in a plant bay that
    # lights anything.
    n_flood = max(1, int(2 * half_len / FLOOD_PITCH_M))
    for j in range(n_flood):
        xw = (-half_len + FLOOD_M
              + j * (2 * half_len - 2 * FLOOD_M) / max(n_flood - 1, 1))
        local, lt, lg = [], [], []
        _box(local, lt, lg, "light_plant_flood",
             (xw - FLOOD_M / 2, r_in, zc_walk - FLOOD_M / 2),
             (xw + FLOOD_M / 2, r_in + FLOOD_DROP_M, zc_walk + FLOOD_M / 2))
        _absorb(verts, tris, groups, _place(local, mid), lt, lg, flip=True)

    # --- pipe runs --------------------------------------------------------
    # Pipes run along the axis, clamped at three radii between the bay faces.
    #
    # The first version read `_cyl(..., 0.0, 0.0, z0, z1, rr)` -- passing the
    # pipe's RADIAL POSITION as its RADIUS. That built a 457 m cylinder shell
    # spanning the whole station instead of a 0.45 m pipe, and it filled the
    # entire frame with its inside surface. Invisible to every assertion in the
    # module and unmissable the moment it was rendered.
    #
    # CAPPED, AND THEY WERE NOT. `cap_lo=False, cap_hi=False` was this module's
    # copy of `dressing._cyl`'s session-3x defect -- a lathe open at both ends,
    # reasoned about the same way ("the end is against the next cell, so nobody
    # sees it"). Measured: 48 open edges on the pipes and 144 on the conduits,
    # every one of `plant`'s 192, and the reasoning was already false for the
    # exterior (the two ends of a whole-sector cell face the sector bulkheads)
    # and is plainly false now that a room-sized cell is composed onto a ring
    # deck -- there the pipe ends face the wall a player walks up to.
    for k in range(PIPES_PER_FRAME):
        rr = r_in + (k + 1) * (r_out - r_in) / (PIPES_PER_FRAME + 1)
        local, lt, lg = [], [], []
        _cyl(local, lt, lg, "plant_pipe", 0.0, rr, z0, z1, PIPE_R_M,
             seg=PIPE_SEG, cap_rise=0.0)
        _absorb(verts, tris, groups,
                _place(local, start_deg + arc_deg / 2), lt, lg, flip=True)

    # --- ARTICULATION (INV-073's rule, applied to a cylindrical hall) -------
    # 31.1% of its detail floor over 594,000 m2. A plant hall is the easiest
    # volume on the station to earn line in and the hardest to earn it the
    # naive way: the surfaces are enormous, so panel relief is hopeless, but
    # everything a real plant room has -- pipe, tray, rail, grating -- is a
    # LONG THIN RUN, which is the highest yield geometry there is (INV-072:
    # ~20 m of line per triangle against panel relief's 0.17).
    #
    # Longitudinal service runs at every frame bay, not just three radii.
    for k in range(SERVICE_RUNS):
        rr = r_in + 0.6 + k * (r_out - r_in - 1.2) / max(1, SERVICE_RUNS - 1)
        for side in (-1, 1):
            local, lt, lg = [], [], []
            _cyl(local, lt, lg, "plant_conduit",
                 side * SERVICE_OFFSET_M, rr, z0, z1, CONDUIT_R_M,
                 seg=6, cap_rise=0.0)
            _absorb(verts, tris, groups,
                    _place(local, start_deg + arc_deg / 2), lt, lg, flip=True)
    # Cable tray beside them: a channel section is four long lines.
    for k in range(TRAYS):
        rr = r_in + 1.2 + k * (r_out - r_in - 2.4) / max(1, TRAYS - 1)
        local, lt, lg = [], [], []
        _box(local, lt, lg, "plant_tray",
             (-TRAY_W_M / 2, rr, z0), (TRAY_W_M / 2, rr + TRAY_D_M, z1))
        _absorb(verts, tris, groups,
                _place(local, start_deg + arc_deg / 2), lt, lg, flip=True)
    # Circumferential ties at a working pitch rather than a structural one:
    # a 36 m ring spacing is right for the load path and leaves 36 m of blank
    # frame between rings, which is what reads as a placeholder.
    n_sec = max(1, int((z1 - z0) / SECONDARY_TIE_M))
    for j in range(1, n_sec):
        zz = z0 + j * (z1 - z0) / n_sec
        _arc_band(verts, tris, groups, "plant_tie_secondary",
                  r_in + 0.35, r_in + 0.35 + TIE_D_M, zz, zz + TIE_W_M,
                  start_deg, arc_deg)
        _arc_band(verts, tris, groups, "plant_tie_secondary",
                  r_out - 0.35 - TIE_D_M, r_out - 0.35, zz, zz + TIE_W_M,
                  start_deg, arc_deg)
    # Catwalk handrail: two long runs and their standards, the length of the
    # bay. A rail is the cheapest line in this module.
    for side in (-1, 1):
        for rk in range(2):
            local, lt, lg = [], [], []
            _box(local, lt, lg, "plant_rail",
                 (side * (CATWALK_W_M / 2) - RAIL_T_M / 2,
                  r_in + CATWALK_CLEAR_M + 0.55 + rk * 0.45, z0),
                 (side * (CATWALK_W_M / 2) + RAIL_T_M / 2,
                  r_in + CATWALK_CLEAR_M + 0.55 + rk * 0.45 + RAIL_T_M, z1))
            _absorb(verts, tris, groups,
                    _place(local, start_deg + arc_deg / 2), lt, lg, flip=True)

    return verts, tris, groups



def _farm_angles(start_deg, arc_deg):
    """Farm centres inside an arc, on the station-wide FARM_PITCH_DEG lattice.

    Anchored to absolute angle rather than to the arc, so two neighbouring
    streaming cells cannot each place a farm just inside their shared boundary
    and end up with two farms 3 m apart across a seam.
    """
    first = math.ceil(start_deg / FARM_PITCH_DEG) * FARM_PITCH_DEG
    out, a = [], first
    while a < start_deg + arc_deg:
        out.append(a)
        a += FARM_PITCH_DEG
    return out


def _farm_zs(z0, z1):
    n = max(1, int((z1 - z0) / FARM_PITCH_Z_M))
    return [z0 + (k + 0.5) * (z1 - z0) / n for k in range(n)]


def _tank_radial(verts, tris, groups, zc, r_base, r_top):
    """A tank standing on the bay's outer face, axis radial.

    Authored in the local frame -- x tangential, y radial, z along the axis --
    as a cylinder about the local Y axis, so `_place` can set it on the drum.
    """
    n0 = len(verts)
    for k in range(TANK_SEG):
        a = math.tau * k / TANK_SEG
        dx, dz = TANK_R_M * math.cos(a), TANK_R_M * math.sin(a)
        verts.append((dx, r_base, zc + dz))
        verts.append((dx, r_top, zc + dz))
    t0 = len(tris)
    for k in range(TANK_SEG):
        a0, b0 = n0 + 2 * k, n0 + 2 * ((k + 1) % TANK_SEG)
        a1, b1 = a0 + 1, b0 + 1
        tris += [(a0, b0, b1), (a0, b1, a1)]
    for r_end, out in ((r_base, True), (r_top, False)):
        c = len(verts)
        verts.append((0.0, r_end + (TANK_CAP_RISE * TANK_R_M * (1 if out else -1)), zc))
        for k in range(TANK_SEG):
            a = n0 + 2 * k + (0 if out else 1)
            b = n0 + 2 * ((k + 1) % TANK_SEG) + (0 if out else 1)
            tris.append((c, b, a) if out else (c, a, b))
    groups.append(("plant_tank", t0, len(tris)))
    return verts, tris, groups


def _absorb(verts, tris, groups, v, t, g, flip=False):
    """Merge a built piece. `flip` reverses winding, and every caller that
    passes geometry through `_place` must set it -- see that function."""
    off = len(verts)
    t0 = len(tris)
    verts.extend(v)
    if flip:
        tris.extend((a + off, c + off, b + off) for a, b, c in t)
    else:
        tris.extend((a + off, b + off, c + off) for a, b, c in t)
    groups.extend((name, lo + t0, hi + t0) for name, lo, hi in g)


def arc_length(r, degrees):
    return 2.0 * math.pi * r * (degrees / 360.0)


def tank_volume_m3(bay):
    """Volume of one tank in a bay, cylinder plus two domed ends."""
    spec = tanks_in_bay(bay)
    if not spec["count"]:
        return 0.0
    h = spec["height_m"]
    cyl = math.pi * TANK_R_M ** 2 * h
    # Two spherical-ish caps of rise TANK_CAP_RISE * r.
    rise = TANK_CAP_RISE * TANK_R_M
    cap = 2 * (math.pi * rise / 6.0) * (3 * TANK_R_M ** 2 + rise ** 2)
    return cyl + cap


def zone_tank_volume_m3(schema, profile, sector=None):
    """Total tankage across the whole plant zone.

    This is the number that has to clear the reserve, and it is NOT set by
    picking a tank count. It falls out of the bay layout: how many tanks fit
    round the circumference and along the sector at the pitch the tank radius
    and clearance imply. If the layout cannot hold thirty days of water, the
    assertion fails and the LAYOUT has to change -- which is a real check,
    where deriving the count from the volume would have been an identity.
    """
    if sector is None:
        sector = "grey"
    ex = schema["sectors"]["extents_m"][sector]
    length = ex["z1"] - ex["z0"]
    total = 0.0
    for bay in bays(schema, profile, sector):
        spec = tanks_in_bay(bay)
        if not spec["count"]:
            continue
        n_farm_a = int(360.0 / FARM_PITCH_DEG)
        n_farm_z = max(1, int(length / FARM_PITCH_Z_M))
        n = n_farm_a * n_farm_z * FARM_TANKS_A * FARM_TANKS_Z
        total += n * tank_volume_m3(bay)
    return total


def _signed_volume(verts, tris):
    v = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        v += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return v / 6.0


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
    decks = plant_decks(schema, profile)
    bs = bays(schema, profile)

    # --- the zone this kit is for -----------------------------------------
    check("the plant zone is the 34 decks interior.py tags",
          len(decks) == 34, f"{len(decks)}")
    check("every plant deck is above the habitable ceiling",
          all(d["floor_g"] > it.HABITABLE_G_MAX for d in decks),
          f"lightest {min(d['floor_g'] for d in decks):.3f} g")
    check("no plant deck is in a sector that should have none",
          all(not [x for x in plant_decks(schema, profile, s)]
              for s in schema["sectors"]["extents_m"] if s != "grey"),
          "only grey reaches above 1.25 g")

    # --- bays --------------------------------------------------------------
    check("bays cover every plant deck with none dropped",
          sum(b["decks"] for b in bs) == len(decks),
          f"{sum(b['decks'] for b in bs)} of {len(decks)}")
    check("bays are taller than a corridor deck",
          all(b["height_m"] > it.DECK_PITCH_M for b in bs),
          f"shortest {min(b['height_m'] for b in bs):.1f} m vs "
          f"{it.DECK_PITCH_M} m")
    check("bays descend inward and do not overlap",
          all(bs[i]["r_inner"] >= bs[i + 1]["r_outer"] - 1e-6
              for i in range(len(bs) - 1)),
          str([round(b["r_outer"], 1) for b in bs]))
    check("the runt bay is kept, not dropped",
          bs[-1]["decks"] == len(decks) % BAY_DECKS or
          len(decks) % BAY_DECKS == 0,
          f"last bay has {bs[-1]['decks']} decks, "
          f"{len(decks)} % {BAY_DECKS} = {len(decks) % BAY_DECKS}")

    # --- the reserve, which is the load-bearing check ----------------------
    vol = zone_tank_volume_m3(schema, profile)
    check("the tank layout holds the thirty-day water reserve",
          vol >= RESERVE_M3,
          f"{vol:,.0f} m3 laid out vs {RESERVE_M3:,.0f} m3 required "
          f"(LIFE-SUPPORT-AND-INDUSTRY.md L-04)")
    # And that it is not absurdly over -- the gazetteer's whole point is that
    # the zone is mostly void. If tankage ever exceeds a few percent of the
    # 139.8 M m3 plant volume, this kit has started filling it in.
    check("tankage is a small fraction of the plant zone, as the volume says",
          vol < 0.10 * 139.8e6,
          f"{vol / 139.8e6:.2%} of the plant zone")

    # --- geometry ----------------------------------------------------------
    bay = bs[0]
    v, t, g = plant_bay(schema, profile, bay, arc_deg=20.0)
    check("a bay builds", len(t) > 200, f"{len(t)} triangles")
    check("every triangle is in a group",
          sum(hi - lo for _n, lo, hi in g) == len(t),
          f"{sum(hi - lo for _n, lo, hi in g)} of {len(t)}")

    radii = [math.hypot(p[0], p[1]) for p in v]
    check("the bay stays inside its own radial band",
          max(radii) <= bay["r_outer"] + TANK_CAP_RISE * TANK_R_M + 1e-6,
          f"max {max(radii):.1f} m vs bay outer {bay['r_outer']:.1f} m")
    check("nothing reaches inboard of the bay's inner face",
          min(radii) >= bay["r_inner"] - TANK_CAP_RISE * TANK_R_M - 1e-6,
          f"min {min(radii):.1f} m vs bay inner {bay['r_inner']:.1f} m")

    ex = schema["sectors"]["extents_m"]["grey"]
    zs = [p[2] for p in v]
    check("the bay stays inside the sector longitudinally",
          ex["z0"] - 1e-6 <= min(zs) and max(zs) <= ex["z1"] + 1e-6,
          f"z {min(zs):.1f}-{max(zs):.1f} vs {ex['z0']}-{ex['z1']}")

    # A tank is a closed solid, so its signed volume must be positive -- the
    # winding test that has caught four defects in this project. Checked on a
    # tank alone rather than on the bay, because the bay contains open shells
    # (pipe rings, frame rings) by design and their contribution is not a
    # volume.
    tv, tt, tg = [], [], []
    _tank_radial(tv, tt, tg, 0.0, 100.0, 84.0)
    check("a tank is wound outward", _signed_volume(tv, tt) > 0,
          f"signed volume {_signed_volume(tv, tt):,.0f}")
    check("the winding test can fail",
          _signed_volume(tv, [(a, c, b) for a, b, c in tt]) < 0)

    # --- the catwalk is the thing a person uses ---------------------------
    walk = [p for p, (name, lo, hi) in
            ((p, grp) for grp in g for p in [None]) if False]  # placeholder
    cat = [i for name, lo, hi in g if name == "plant_catwalk"
           for i in range(lo, hi)]
    check("the bay has a catwalk", len(cat) > 0)
    cat_r = [math.hypot(v[i][0], v[i][1]) for tri in
             (t[i] for i in cat) for i in tri]
    check("the catwalk is at the bay's inner face, where a person arrives",
          abs(min(cat_r) - (bay["r_inner"] + CATWALK_CLEAR_M)) < 0.5,
          f"catwalk at {min(cat_r):.1f} m, bay inner {bay['r_inner']:.1f} m")
    # Headroom is measured INWARD from the deck, because up is toward the axis
    # and the bay's inner face is the ceiling.
    check("there is standing headroom above the catwalk",
          CATWALK_CLEAR_M >= 2.1,
          f"{CATWALK_CLEAR_M:.1f} m from deck to the bay's inner face")

    # No piece may be radially larger than the bay holding it. This is what
    # would have caught the 457 m "pipe": its group spanned the whole station
    # radius while every other assertion in the module passed.
    over = []
    for name, lo, hi in g:
        rs = [math.hypot(v[i][0], v[i][1]) for tri in t[lo:hi] for i in tri]
        if rs and (max(rs) - min(rs)) > bay["height_m"] + 2 * TANK_CAP_RISE * TANK_R_M:
            over.append((name, round(max(rs) - min(rs), 1)))
    check("no piece is radially larger than its own bay",
          not over, f"{over[:3]} against a {bay['height_m']:.1f} m bay")

    # --- the winding gate for _place --------------------------------------
    # _place has a determinant of -1, so anything through it is inside-out
    # unless the caller flips. Assert on a PLACED solid, not a local one: the
    # local test passes either way and is what let this ship.
    lv, ltri, lg2 = [], [], []
    _box(lv, ltri, lg2, "probe", (-2.0, 400.0, 0.0), (2.0, 404.0, 4.0))
    placed = _place(lv, 12.0)
    flipped = [(a, c, b) for a, b, c in ltri]
    check("a solid placed through _place and flipped encloses positive volume",
          _signed_volume(placed, flipped) > 0,
          f"{_signed_volume(placed, flipped):,.1f}")
    check("and NOT flipping it is inside-out, so the gate can fail",
          _signed_volume(placed, ltri) < 0,
          f"{_signed_volume(placed, ltri):,.1f}")

    # --- cost, which is the entire point ----------------------------------
    # The corridor kit runs 285 tri/m along a run. A plant bay covers five
    # decks, so the honest comparison is per deck-equivalent.
    per_deck = len(t) / bay["decks"]
    check("a plant bay is far cheaper per deck than corridor",
          per_deck < 20_000,
          f"{per_deck:,.0f} tri per deck-equivalent")

    # Whole-zone estimate against what the manifest currently budgets.
    cells = it.ring_cells(schema, profile, "grey", 0, 0)["cells"]
    zone = 0
    for b in bs:
        vb, tb, _gb = plant_bay(schema, profile, b, arc_deg=360.0 / cells)
        zone += len(tb) * cells
    check("the plant zone costs far less than the corridor placeholder",
          zone < 62_273_664 * 0.5,
          f"{zone:,} tri vs the manifest's 62,273,664 placeholder "
          f"({zone / 62_273_664:.1%})")

    # --- THE ROOM CELL, which is a different thing from a streaming cell ---
    # A gate belongs in the module that builds the thing (CLAUDE.md, 3x), and
    # `room_cell` is what session 4b added. It must build the HARD case, so it
    # runs on all five addressed places rather than on one bay.
    import directory as _dr                                     # noqa: PLC0415
    import interior_kit as _K                                   # noqa: PLC0415
    import rooms as _R                                          # noqa: PLC0415
    import bespoke as _B                                        # noqa: PLC0415
    qs = [q for q in _dr.PLACES if q.get("module") == "plant"]
    check("the register still owns five plant places", len(qs) == 5, str(len(qs)))
    leaks, offdeck, oversize, tanked = [], [], [], []
    for q in qs:
        v, t, g = room_cell(schema, profile, q)
        op, _nm = _K.boundary_edges(v, t)
        if op:
            leaks.append((q["key"], len(op)))
        # THE WALKWAY IS AT THE ADDRESSED DECK'S FLOOR. Measured off the
        # geometry through the same unroll `bespoke` uses, not read back off
        # the argument that set it -- an assertion that checks its own input is
        # the failure mode this project has already paid for twice.
        fl = _B.unroll_to_local(v)
        r_ref = max(math.hypot(p[0], p[1]) for p in v)
        walk = r_ref - _B.floor_y(fl, t, g, "plant")
        want = _R.room_extent_m(schema, profile, q)[2]
        if abs(walk - want) > 0.10:
            offdeck.append((q["key"], round(walk, 2), round(want, 2)))
        # ...and the cell is no wider or deeper than the collision shell a
        # player is actually inside. `deck.room_shell_for` sizes that from
        # `bay_span_m` and never looks at this mesh, so render geometry outside
        # it is geometry a body walks through a wall to reach.
        w_full, l_full, _r = _R.room_extent_m(schema, profile, q)
        bw, bl = _R.bay_span_m(q)
        xs = [p[0] for p in fl]
        zs = [p[2] for p in fl]
        if (max(xs) - min(xs) > min(w_full, bw) + 0.02
                or max(zs) - min(zs) > min(l_full, bl) + 0.02):
            oversize.append((q["key"], round(max(xs) - min(xs), 2),
                             round(max(zs) - min(zs), 2),
                             round(min(w_full, bw), 2), round(min(l_full, bl), 2)))
        if any("tank" in n for n, _lo, _hi in _B._spans(g, len(t))):
            tanked.append(q["key"])
    check("every composed plant cell is closed", not leaks, str(leaks))
    check("...and its walkway is the addressed deck's own floor radius",
          not offdeck, f"{offdeck} -- a step between a corridor and the room "
                       f"it serves is what deck.build_deck forbids")
    check("...and it fits inside the collision shell a body is in",
          not oversize, str(oversize))
    # NOT ONE OF THE FIVE HOLDS A TANK, and that is asserted rather than left
    # to be rediscovered: TANK_R_M is a bay-scale object and `bay_span_m`
    # clamps every one of these places to a deck-scale room, so `2*TANK_R_M +
    # 2*WALK_M` = 10.8 m does not fit in any of them. Widen a footprint and
    # this fires, which is the direction it should fire in.
    check("no deck-scale plant room pretends to hold a bay-scale tank",
          not tanked,
          f"{tanked} got a tank in a room too small to walk round one -- "
          f"needs {2 * TANK_R_M + 2 * _R.WALK_M:.1f} m each way")

    # NEGATIVE CONTROL -- uncap one pipe and the closure gate has to fire. The
    # 192 open edges this session closed were exactly this, so the control is
    # the defect itself rather than an analogue of it.
    _real = globals()["_cyl"]

    def _open_pipe(verts, tris, groups, name, *a, **kw):
        if name == "plant_pipe":
            kw["cap_lo"] = kw["cap_hi"] = False
        return _real(verts, tris, groups, name, *a, **kw)

    globals()["_cyl"] = _open_pipe
    try:
        cv, ct, _cg = room_cell(schema, profile, qs[0])
        cop, _cnm = _K.boundary_edges(cv, ct)
    finally:
        globals()["_cyl"] = _real
    check("...and uncapping one pipe run re-opens it",
          len(cop) > 0,
          f"{qs[0]['key']} stayed closed with its pipes open at both ends -- "
          f"the closure gate is not measuring the pipes")
    print(f"  room cells: {len(qs)} places, 0 open edges, walkway on the "
          f"addressed deck; control reopens {len(cop)} edges")

    print(f"\nplant zone: {len(bs)} bays over {len(decks)} decks, "
          f"{bs[-1]['r_inner']:.1f}-{bs[0]['r_outer']:.1f} m, "
          f"{bs[-1]['floor_g']:.2f}-{bs[0]['floor_g']:.2f} g")
    print(f"tankage {vol:,.0f} m3 laid out against a {RESERVE_M3:,.0f} m3 "
          f"reserve ({vol / RESERVE_M3:.1f}x)")
    print(f"zone cost {zone:,} tri against a 62,273,664 placeholder "
          f"({zone / 62_273_664:.1%})")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
