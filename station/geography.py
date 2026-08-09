"""The station's geography: ONE description of where every place is.

WHY THIS EXISTS
---------------
Hard rule 4 says "inside and outside come from the same schema. Never
hand-author hull geometry that duplicates interior geometry. Consistency is by
construction, not by discipline." The station broke that rule at the largest
scale it is possible to break it at, and no gate could see it, because every
gate here measures a PART against a standard and this is a defect BETWEEN two
parts.

Two tables described where things are on an 8,047 m station:

  * `station.yaml sectors.extents_m` -- five longitudinal bands. `directory.py`
    addresses all 129 places against these, and `interior.py` derives every
    ring radius, deck stack and streaming cell from them.
  * `station.yaml longitudinal.features` -- fifteen hull features. The exterior
    mesh, the greebles, the apertures, the components and `radius_profile.json`
    are all generated against these.

They came from different sheets, by different methods, and **they do not
overlap**. Measured at session 4t, over the 24 landmarks a viewer knows by
name, **4** sat inside a structure consistent with their own sector name:

    cnc / obs_dome_1        addressed blue    physically in forward_deflector_spike
    zocalo / casino         addressed red     physically in forward_taper (a cone)
    council_chamber         addressed green   physically in aft_hull_block
    fresh_air / earharts    addressed green   physically in bearing_neck
    all 20 Grey rows        addressed grey    physically in green_section

`red_section` (6035-6465) and the Red band (6425-6794) share **40 m of 430 --
9.3%**. **100% of Grey Sector is inside the feature named `green_section`.**
Command & Control -- canon-placed in Observation Dome 1, which `components`
builds at z 7000-7240 from Contract 5 -- was addressed at z 7960, **674 m
forward of the docking sphere's fore face**, inside the navigation spike. The
Fresh Air Restaurant, whose ceiling is authority-1 established as the far side
of the drum, was inside the liquid-helium bearing race.

WHICH TABLE IS AUTHORITATIVE, AND THE EVIDENCE
----------------------------------------------
**The hull.** Not because it is older or bigger, but because it is the one that
was MEASURED and the one everything physical is made of:

 1. `longitudinal.features` carries a recorded calibration -- `other map 4.jpg`
    at 2100x1275, tail 71 px, nose 2048 px, `px_per_miller_m 0.6361`,
    `real_m_per_px 4.070`, rescaled by `k = 8047/3108 = 2.5891`. Every number
    can be re-derived from the sheet.
 2. It is cross-checked against a SECOND, independent quantity -- Miller's
    printed specification table -- on the two sections where both exist:
    red_section drawn 430 m against table 445.3 m (**3.5%**), red envelope
    diameter 692.0 against table 654.9 (**5.7%**), green envelope 618.6 against
    595.5 (**3.9%**). Two unrelated methods agreeing to a few per cent.
 3. `radius_profile.json` -- 1,978 samples at 4.07 m -- is traced from the same
    drawing, with a stated extraction method, a stated rejection of label
    leader lines, and a visual verification. The exterior hull mesh IS that
    trace.
 4. `sectors.extents_m` is read from bracket ticks on a sheet that **has no
    scale bar** ("absolute values come from applying those fractions to the
    canon 8,047 m"), and the schema marks it `assignment_status:
    OPEN_BLOCKING` and says in its own comment: *"Do not build interior layout
    against them until C-003's assignment question closes."* It was built
    against anyway.

AND THE CROSS-CHECK THAT WAS SUPPOSED TO CATCH THIS COMPARED THE WRONG THING.
`sectors:` claims it was "cross-checked independently against the Miller-derived
longitudinal framework: Green agrees to 11.7%, Red to 14.1%". Both figures are
correct and both are about **length only**:

    green band 2586 m vs green_section 2928 m  ->  -11.7%   position: 732 m apart
    red   band  369 m vs red_section    430 m  ->  -14.2%   position: 390 m apart

A cross-check that compares two magnitudes and never compares their offsets
cannot see a 732 m translation. *When two tables are validated against each
other, check the quantity the failure would show up in.*

THE REGISTER'S OWN z VALUES ARE THE TELL. `directory.PLACES` puts `comms_grid`
at z 7900; `components.comms_grid_pylon` builds the deep space communications
grid at z 2515-2988. **5,000 m apart, in the same schema.** `obs_dome_1` at
7960 against `components.observation_dome` at 7000-7240. `proximity_arrays` at
7900 against `space_traffic_prox_array` at 7320-7420. The register's z was laid
out by spreading places evenly across the *sector bands*; the components' z was
read off the *hull*. That is hard rule 4's failure mode stated in one sentence:
two descriptions of one station.

WHAT THIS MODULE DOES
---------------------
`SECTOR_FEATURES` maps each sector to the whole hull features it is made of, so
a sector boundary IS a hull feature boundary and cannot drift from it. Every
band, radius, gravity and address below is derived from that map plus the
profile. Nothing here is hand-authored except the mapping itself, which is the
one claim this module makes and which is argued for on each entry.

`python3 station/geography.py --gate` asks five questions of the SHIPPED state
and three of the wiring. `--legacy` re-asks them against the frozen pre-4t
schema, which is the negative control and fails on all five. `--proposed`
applies this module's own reconciliation in memory and re-asks -- that is the
A/B partner, and the register patch it simulates is printed by `--patch`.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# THE NEGATIVE CONTROL. Frozen, and it must never be re-read from the schema.
# ---------------------------------------------------------------------------
# `station.yaml sectors.extents_m` exactly as it stood before this session.
# A gate whose "before" is read from the file it is about to change can only
# ever compare a thing with itself -- this file's own record of the vacuous-A/B
# defect, from 4d and again from 4r. So the before is a literal.
LEGACY_EXTENTS = {
    "yellow": (0.0, 3397.0),
    "grey":   (3397.0, 3839.0),
    "green":  (3839.0, 6425.0),
    "red":    (6425.0, 6794.0),
    "blue":   (6794.0, 8047.0),
}


# ---------------------------------------------------------------------------
# THE ONE CLAIM: which hull features each sector is made of.
# ---------------------------------------------------------------------------
# Read aft -> fore, in the canon order `sectors.order_aft_to_fore`. Every
# sector is a union of WHOLE features, so a sector edge is a hull edge and the
# two descriptions cannot drift apart by construction rather than by care.
#
# The argument for each row is on the row. Where a row disagrees with Miller's
# printed table the disagreement is stated with its size, not smoothed over.
SECTOR_FEATURES = {
    # Zero-G storage (other map 2.jpg, auth 4). The whole non-rotating aft
    # assembly: `green_section` is `kind: rotating_assembly` and starts at
    # 3107, so everything aft of 3107 does not spin and every point in it is at
    # zero g. THAT IS WHY CANON CALLS IT ZERO-G STORAGE -- the sector name is a
    # statement about rotation, and this is the only band on the station that
    # satisfies it. Yellow's rosette facilities corroborate it one by one:
    # power transfer core, cooling fins (`reactor_cooling_fin` z 1315-1655),
    # coolant transfer tubes, inspection access -- all four are features in
    # this band and none is anywhere else.
    "yellow": ("aft_terminus", "primary_fusion_reactor", "reactor_spine",
               "generator_torus_housing", "main_truss_spine",
               "explosive_disconnect_neck", "hull_flare_aft"),

    # Industrial zones, manufacturing, construction (other map 2.jpg, auth 4).
    # The aft hull block: 1,100 m, core hull 474.5 m, **the widest structure on
    # the station and the one Miller's table does not name at all** -- which is
    # exactly the shape of a sector the table omits. `radius_profile.finding`
    # says so in the schema already. It sits immediately aft of the drum, which
    # is where the Sectional Schematic's bracket order puts Grey.
    #
    # AND IT IS THE STRONGEST AGREEMENT BETWEEN THE TWO SHEETS: the Schematic's
    # Grey bracket has midpoint 3618 m; this band's midpoint is 3657 m. **39 m
    # apart on an 8 km station, 0.5% of length.** Green's is 11 m. The two
    # sheets agree about the aft half and disagree about the fore half, which
    # is a registration error in the fore half rather than a different station.
    "grey": ("aft_hull_block",),

    # Diplomatic zones, the Garden (other map 2.jpg, auth 4). The drum: the
    # bearing race where non-rotating structure meets the rotating cylinder,
    # plus the cylinder. `habitat_hull_radius()` measures 310.79 m over
    # `habitat_cylinder`; the longest near-constant core-hull run inside this
    # band is 314.3 m over 805.9 m of axis. 2.5 m apart on a 315 m radius from
    # two derivations that share no arithmetic -- and `drum_sector()` picks
    # this band by that match, so the band has to exclude the 474 m aft block
    # or the drum identification itself moves to Grey.
    "green": ("bearing_neck", "habitat_cylinder"),

    # Commercial zones, residential, the Zocalo (other map 2.jpg, auth 4).
    # `red_section` is the single best-attested feature on the station: drawn
    # 430 m against table 445.3 m, which the schema calls "the strongest
    # cross-check between Miller's drawing and his table". Its core hull runs
    # 337.9 m over 301 m of axis against the table's 327.45 m -- **3.2%**.
    #
    # THE OLD BAND TOOK RED'S RADIUS FROM THE FORE CONE. `sector_shell_radius`
    # returned 274.05 m for Red, which is the near-constant run at z
    # 6479.9-6626.4 -- inside `forward_taper`, not inside the Red Section.
    # Against the table that is **-16.3%**; against this band it is +3.2%.
    "red": ("red_section",),

    # Docking sphere, crew quarters, C&C (other map 2.jpg, auth 4). Everything
    # forward of the Red Section. It MUST contain the docking sphere, because
    # `components.observation_dome` builds Dome 1 -- which IS Command &
    # Control, Contract 5, auth 3 -- at z 7000-7240, and `components.cobra_bay`
    # builds the 28 launch bays at 6980-7250.
    #
    # THE DISAGREEMENT, STATED: this band is 1,582 m and Miller's table gives
    # the Blue Section as 921.7 m. The table figure is the PRESSURISED SECTION;
    # the band also carries the 761 m forward deflector spike, which is
    # instrument structure and pressurises nothing. Taper + waist + sphere
    # alone is 821 m, -10.9% against the table -- but a sector model that does
    # not partition the station leaves the spike unaddressable, and
    # `nav_beacon` is a place in the register. So the spike is inside Blue and
    # the pressurised part of Blue is 821 m of it. INV-995.
    "blue": ("forward_taper", "forward_waist", "docking_sphere",
             "forward_deflector_spike"),
}

# Canon order, aft -> fore. `sectors.order_aft_to_fore`, Sectional Schematic,
# auth 3. This is NOT derived -- it is the one thing the Schematic is good for,
# and the reconciliation preserves it exactly.
ORDER_AFT_TO_FORE = ("yellow", "grey", "green", "red", "blue")

# The rotating assembly, from `longitudinal.features`: the feature whose `kind`
# is `rotating_assembly` starts at 3107, and everything forward of it is
# carried on the same bearing. Derived rather than listed -- see `rotating()`.
ROTATING_ASSEMBLY_KIND = "rotating_assembly"


# ---------------------------------------------------------------------------
# Places whose z is fixed by something else the schema already builds.
# ---------------------------------------------------------------------------
# An anchored place does not get the affine remap. Its z comes from the
# component or feature that IS the thing, so the register and the mesh cannot
# disagree about where it is. Each entry names its source.
#
# This is the half of the reconciliation that is not arithmetic: a place tied
# to a built structure must move to the structure, not to the same fraction of
# a moved band.
ANCHORS = {
    # Contract 5: "OB. DOME 1 (COMMAND & CONTROL)". `components.observation_dome`
    # z0 7000 z1 7240. C&C is inside Dome 1, so all three share the anchor.
    "cnc":               ("component", "observation_dome"),
    "obs_dome_1":        ("component", "observation_dome"),
    "obs_dome_2":        ("component", "observation_dome"),
    # Contract 5 "COBRA BAYS (28)"; `components.cobra_bay` z 6980-7250.
    "cobra_bays":        ("component", "cobra_bay"),
    # Contract 5 "Deep Space Communications Grid (2)"; `components.
    # comms_grid_pylon` z 2515-2988. The register had this at z 7900 -- 5,000 m
    # and three sectors away from the structure it names.
    "comms_grid":        ("component", "comms_grid_pylon"),
    # `components.space_traffic_prox_array` z 7320-7420.
    "proximity_arrays":  ("component", "space_traffic_prox_array"),
    # Contract 5 "OBSERVATION ROTUNDA (4)"; `components.observation_rotunda`
    # z 6180-6360. This lands them in the Red Section, which is a third answer
    # to a question the gazetteer already records as open (Contract 5 says
    # Blue, the interior frame says Green). The anchor states where the
    # geometry IS; it does not close the conflict.
    "obs_rotundas":      ("component", "observation_rotunda"),
    # `components.cargo_module` z 4870-6010 -- the six dorsal modules the
    # transfer deck sits under. INV-100 put the deck under them; the anchor
    # keeps it there when the band moves.
    "cargo_transfer_deck": ("component", "cargo_module"),
    # `components.heat_exchange_solar_array` z 2020-2330.
    "heat_exchanger_hall": ("component", "heat_exchange_solar_array"),
    # `components.generator_torus_housing` is a hull feature, z 1095-1295.
    "generator_hall":    ("feature", "generator_torus_housing"),
    # The reactor jettison boundary, `explosive_disconnect_neck` z 2680-3016.
    "disconnect_point":  ("feature", "explosive_disconnect_neck"),
    # The primary fusion reactor hull feature, z 39-331.
    "reactor_hall":      ("feature", "primary_fusion_reactor"),
    # THE 24 ROTATING BAYS ARE THE DOCKING SPHERE. Nothing else on the station
    # is; `docking.docking_bay.count: 24` and the sphere's `contains:` list
    # (spacecraft fuel storage, bay exhaust vents, cobra launch support arms)
    # describe one structure. An affine remap put them 70 m aft into
    # `forward_waist` -- the 114 m neck -- which is the failure mode an
    # unanchored remap has: it is right about proportion and blind to what a
    # thing IS.
    "docking_bays":      ("feature", "docking_sphere"),
    # The arrival path off the bays. `arrival_concourse` is `adjacent` to
    # `customs_north` and `customs_north` to `docking_bays`; the whole point of
    # the sequence is that a passenger WALKS bay -> customs -> concourse, which
    # a 20 m-into-the-instrument-spike address does not support. Authority 1
    # on the halls themselves.
    "customs_north":     ("feature", "docking_sphere"),
    "customs_south":     ("feature", "docking_sphere"),
    "arrival_concourse": ("feature", "docking_sphere"),
    # "Micro-gravity maintenance bays (2) ... ON THE SPINE" -- gazetteer row,
    # Contract 5, the schematic's "zero-G maintenance fac.". The spine is
    # `main_truss_spine`, and it is 164.8 m of core hull against the 34 m the
    # rotating/non-rotating interface leaves -- a bay you can get a Starfury
    # into rather than one you cannot.
    "micro_g_bays":      ("feature", "main_truss_spine"),
    # "Low-g / zero-g docking bays: NON-ROTATING bays for craft too large for
    # the rotating section" -- gazetteer, Security Manual "LOW-G DOCKING BAYS",
    # auth 3. The register had them at r=211.6 m inside the ROTATING docking
    # sphere, at 0.7602 g, `within` the rotating bays -- which is the one place
    # a bay for a craft that cannot match rotation cannot be. The station's
    # only non-rotating structure is Yellow and its only berth-sized run is the
    # spine.
    #
    # **A RESIDUAL CONFLICT IS LEFT STANDING RATHER THAN PICKED.** The
    # gazetteer says these bays are "forward"; under `sections.blue.rotating:
    # true` there is no forward non-rotating structure to put them on. One of
    # those two statements is wrong and this module does not have the evidence
    # to say which. INV-998, and it wants a CONFLICTS.md row.
    "lowg_bays":         ("feature", "main_truss_spine"),
}

# Places pinned to the fore or aft EDGE of a band rather than its middle,
# because that edge is what they are. Value is ("aft"|"fore", sector).
EDGE_ANCHORS = {
    # The machinery that spins the carousel sits ON the rotating/non-rotating
    # interface -- gazetteer row, Security Manual callout, auth 3. That
    # interface is Yellow's fore edge, z 3107.
    "rotation_drivers":  ("fore", "yellow"),
    # "Zero-g maintenance ... at the rotating/non-rotating interface" --
    # gazetteer, Security Manual callout. Same edge, and it is what makes the
    # facility zero-g at all.
    "zerog_maint":       ("fore", "yellow"),
    # The nose. `primary_navigation_beacon` is the forwardmost exterior system
    # and the spike's fore terminus is the station's fore terminus.
    "nav_beacon":        ("fore", "blue"),
    # The drum's aft end cap is the aft face of the drum band.
    "drum_endcaps":      ("aft", "green"),
}

# Places whose SECTOR changes, because the structure they name is in a
# different band from the one the register wrote down. Each is a consequence of
# an anchor above, not an independent decision.
SECTOR_MOVES = {
    "comms_grid":       "yellow",   # the pylons are at z 2515-2988
    "obs_rotundas":     "red",      # the rotundas are at z 6180-6360
    "zerog_maint":      "yellow",   # zero g requires the non-rotating band
    "micro_g_bays":     "yellow",   # micro g requires the non-rotating band
    "lowg_bays":        "yellow",   # ditto -- and it leaves the rotating bays
}

# THE AXIAL RUN. `core_shuttle` has a 4,650 m footprint -- longer than any
# sector band on the station -- because it is not a room, it is the tube. Its
# extent is the rotating assembly's, derived rather than written down.
#
# IT STAYS IN YELLOW, WHICH LOOKS WRONG AND IS NOT. Yellow is the
# non-rotating band, and a shuttle that runs the axis of a spinning station
# cannot be spinning -- that is what makes an axial transit an axial transit.
# `interior_topology.core_on_axis` lists `core_shuttle` beside `power_core`
# for the same reason. Addressing it to the band its midpoint happens to fall
# in (green) was tried and is worse in a way only the hull gate shows: green
# is the drum, the drum's only deck stack is the SUB-FLOOR, and the tube came
# out at **278.3 m radius** -- the Garden's floor -- instead of 98.7 m.
#
# `directory.py` prints two FAILs about this place and will keep printing them
# until its "fits inside its sector longitudinally" assertion learns that an
# axial run is not a room. That edit is named in this session's report; it is
# one line and it is not in a file this module owns.
AXIAL = ("core_shuttle", "shuttle_car")


# ---------------------------------------------------------------------------
# Functions and what they permit
# ---------------------------------------------------------------------------
# A place may sit above `interior.HABITABLE_G_MAX` only if what it is FOR is
# something the station does in its own basement. This is not a licence list:
# it is INV-027's distinction made checkable. `use == "plant"` means UNASSIGNED,
# not uninhabited -- Downbelow is people living where nobody can be billeted,
# and that is the point of Downbelow.
#
# Everything NOT in this set is an assigned function: a roster, a shift, a
# shop, a bed the station allocates. Those have a ceiling.
HEAVY_PERMITTED = frozenset((
    "informal_residence",       # Downbelow. The whole reason the band is characterful
    "black_market", "crime", "organised_crime", "black_market_fringe",
    "water_storage", "water_reclamation", "waste_processing", "air_handling",
    "power_distribution", "fabrication", "industry", "storage",
    "microgravity_handling", "repair", "sealed_volume", "structure",
    "monitoring", "control", "transit", "variable_gravity",
))


def _permits_heavy(place):
    """EVERY declared function must be a basement function, not just one.

    ANY-match was the first rule written here and it is the wrong quantifier,
    which the content proved within one run: `happy_daze` is a BAR, and it
    passed an any-match on `black_market_fringe` while declaring `hospitality`
    and `recreation`. A place that does one thing the station rosters people
    for is a place the station rosters people for. Under all-match the four
    that fail are exactly the four an assigned/unassigned reading predicts:
    happy_daze, black_market, research_labs, gravity_torus.
    """
    fns = set(place.get("functions", ()))
    return bool(fns) and fns <= HEAVY_PERMITTED

# A function that NAMES a gravity regime, and what the regime means. Derived,
# not chosen:
#   zero / micro -- the station has exactly one volume at zero g, and it is the
#       non-rotating assembly. There is no threshold to argue about: either a
#       place is on the bearing or it is not.
#   low          -- below the habitat floor, which the rotation rate is solved
#       to put at exactly 1.000 g. "Low" against the station's own design point.
MICRO_G_FUNCTIONS = frozenset(("microgravity_handling",))
LOW_G_FUNCTIONS = frozenset(("low_gravity",))
LOW_G_CEILING = 1.0                 # the habitat floor, by construction


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------
def load():
    return it.load()


def leaf_features(schema):
    """Every hull feature that is not a container, as (id, z0, z1).

    A parent with subfeatures is not itself a leaf: `green_section` spans
    3107-6035 and its three subfeatures tile that span exactly, so counting
    both would double-cover 2,928 m of station.
    """
    out = []
    for f in schema["longitudinal"]["features"]:
        subs = list(f.get("subfeatures", ()))
        for g in (subs or [f]):
            out.append((g["id"], float(g["z0"]), float(g["z1"])))
    return out


def feature_span(schema, fid):
    for f in schema["longitudinal"]["features"]:
        for g in [f] + list(f.get("subfeatures", ())):
            if g["id"] == fid:
                return float(g["z0"]), float(g["z1"])
    raise KeyError(f"no longitudinal feature {fid!r}")


def component_span(schema, cid):
    for c in schema["components"]:
        if c["id"] == cid:
            return float(c["z0"]), float(c["z1"])
    raise KeyError(f"no component {cid!r}")


def axial_run(schema, place, bands=None):
    """The rotating assembly's extent, if this place rides the axis.

    True for `core_shuttle` -- which IS the tube -- and for anything declared
    `within` it, because a car inside a 4,940 m run is at whatever z the run
    reaches and no band contains it either. Anything else gets None and is
    judged by band containment like a room.
    """
    if place["key"] in AXIAL or place.get("within") in AXIAL:
        return rotating_assembly(schema, bands)
    return None


def anchor_span(schema, key):
    """(z0, z1) of the structure a place is anchored to, or None.

    THE TEST A FEATURE-CONTAINMENT CHECK CANNOT MAKE. "Is `cnc` inside a
    feature Blue is made of" answers yes for the 761 m navigation spike,
    because the spike is in Blue. "Is `cnc` inside Observation Dome 1" answers
    the question a viewer actually asks. Only the 18 places the schema
    independently builds a structure for can be asked it -- for the rest, the
    band is the strongest statement available -- but those 18 include every
    landmark whose position is canon rather than inferred.
    """
    if key in ANCHORS:
        kind, ident = ANCHORS[key]
        return (component_span(schema, ident) if kind == "component"
                else feature_span(schema, ident))
    return None


def feature_at(schema, z):
    for fid, z0, z1 in leaf_features(schema):
        if z0 <= z <= z1:
            return fid
    return "unassigned"


def sector_bands(schema):
    """Every sector's band, derived from the hull features it is made of.

    This is the function `station.yaml sectors.extents_m` must equal. It is the
    whole of hard rule 4 for the longitudinal axis: there is one description,
    and the schema's copy of it is a cache that the gate checks.
    """
    spans = {fid: (z0, z1) for fid, z0, z1 in leaf_features(schema)}
    out = {}
    for sector, fids in SECTOR_FEATURES.items():
        zs = []
        for fid in fids:
            if fid not in spans:
                raise KeyError(f"{sector}: no leaf feature {fid!r}")
            zs.extend(spans[fid])
        # Contiguity is asserted rather than assumed: a sector made of features
        # with a hole in it would still produce a plausible (min, max).
        chosen = sorted((spans[f] for f in fids), key=lambda p: p[0])
        for a, b in zip(chosen, chosen[1:]):
            if abs(a[1] - b[0]) > 1e-9:
                raise ValueError(
                    f"{sector}: features are not contiguous, "
                    f"{a[1]} -> {b[0]}")
        out[sector] = (min(zs), max(zs))
    return out


def rotating(schema, sector):
    """Does this sector spin? Derived from the rotating_assembly feature."""
    z0 = None
    for f in schema["longitudinal"]["features"]:
        if f.get("kind") == ROTATING_ASSEMBLY_KIND:
            z0 = float(f["z0"])
    if z0 is None:
        raise KeyError("no feature of kind rotating_assembly")
    b0, _b1 = sector_bands(schema)[sector]
    return b0 >= z0 - 1e-9


def rotating_assembly(schema, bands=None):
    """(z0, z1) of everything that spins. The axial run's own extent."""
    bands = bands or sector_bands(schema)
    spin = [b for s, b in bands.items() if rotating(schema, s)]
    return min(b[0] for b in spin), max(b[1] for b in spin)


def drum_length_m(schema):
    """ONE number for the habitat drum, and it is the Green band.

    THERE WERE FIVE. `bio_habitat.interior_length_m` said 2739.3 (Miller's
    table); `habitat_cylinder` said 1209 (his drawing); `interior.drum_interior`
    and `drum_end_cap` defaulted to the Green sector extent, 2586;
    `LOCATIONS.md` says "~2,000 m"; `directory.the_garden`'s note says "2.6 km
    long". Five numbers, one drum, and the widest pair differ by **2.3x**.

    The reconciled figure is the Green band: bearing race to the fore face of
    the habitat cylinder, 4207 -> 6035 = **1828.0 m**. It is the only one of
    the five derived from the structure the drum is made of.

    THE DISAGREEMENT WITH THE TABLE IS 33% AND IS NOT SWEPT UP. Miller's
    "Green Section" of 2739.3 m spans, on his own drawing, z 3107-6035 -- it
    INCLUDES the 1,100 m aft hull block. This reconciliation gives that block
    to Grey, because it is 948.9 m across and Miller's own table names no
    pressurised section wider than Red's 654.9 m, and because the drum
    identification in `interior.drum_sector()` matches on hull radius and moves
    to Grey if the block stays in Green. So: Miller's Green SECTION is this
    project's Grey band plus Green band, 3107-6035 = 2928 m, and the drum
    proper is the 1828 m of it that is actually at drum radius. INV-996.
    """
    b = sector_bands(schema)["green"]
    return b[1] - b[0]


def declared_hull_diameter(schema, sector):
    """The pressurised diameter `sections:` declares for a sector, or None."""
    sec = schema.get("sections", {}).get(sector) or {}
    for k in ("diameter_m", "outer_diameter_m"):
        if k in sec:
            return float(sec[k]["value"])
    return None


def shell_radius(schema, profile, sector):
    """A sector's principal pressurised shell, in the reconciled geography.

    Delegates to `interior.sector_shell_radius`, which finds the longest run of
    near-constant core-hull radius inside the band. That function is correct
    and is not duplicated here; what this adds is the band it runs over, which
    now comes from the hull.
    """
    return it.sector_shell_radius(schema, profile, sector)


class _Reconciled:
    """Context manager: the schema and register as this module reconciles them.

    IT IS A SHIM AND IT IS MEANT TO BE DELETED. `interior.sector_shell_radius`
    and `directory.PLACES` read `sectors.extents_m` and their own literals; the
    reconciliation lives here. Until the two consumers read this module, a gate
    that wants to measure the reconciled station has to substitute. The wiring
    checks below report exactly that, so the substitution cannot quietly become
    the permanent arrangement -- which is this project's most-repeated defect,
    machinery with no caller on the shipped path.
    """

    def __init__(self, schema, profile, bands=None, places=None):
        self.schema, self.profile = schema, profile
        self.bands = bands
        self.places = places
        self._old_ex = None
        self._old_places = None

    def __enter__(self):
        import directory as dr
        if self.bands is not None:
            self._old_ex = self.schema["sectors"]["extents_m"]
            self.schema["sectors"]["extents_m"] = {
                s: {"z0": z0, "z1": z1} for s, (z0, z1) in self.bands.items()}
            it._CORE_HULL_CACHE.clear()
        if self.places is not None:
            self._old_places = dr.PLACES
            dr.PLACES = tuple(self.places)
        return self

    def __exit__(self, *exc):
        import directory as dr
        if self._old_ex is not None:
            self.schema["sectors"]["extents_m"] = self._old_ex
            it._CORE_HULL_CACHE.clear()
        if self._old_places is not None:
            dr.PLACES = self._old_places
        return False


# ---------------------------------------------------------------------------
# The reconciliation of the register
# ---------------------------------------------------------------------------
def _affine(z, src, dst):
    """Keep a place at the same fraction along its sector as it was.

    The minimal transform: it preserves order, relative spacing and every
    adjacency inside a sector, and it moves nothing relative to its neighbours.
    Anything cleverer would be re-authoring the register, which is a different
    job from reconciling two tables.
    """
    if src[1] - src[0] <= 0:
        return dst[0] + (dst[1] - dst[0]) / 2.0
    f = (z - src[0]) / (src[1] - src[0])
    return dst[0] + f * (dst[1] - dst[0])


def reconcile_place(schema, place, bands=None):
    """Where a place goes once the bands come from the hull.

    Returns (sector, z_m, why). `why` names the rule that decided it, so a
    reader of the patch can see which of the four applied.
    """
    bands = bands or sector_bands(schema)
    key = place["key"]
    sector = SECTOR_MOVES.get(key, place["sector"])
    span = float((place.get("footprint") or (0.0, 0.0))[1])

    if key in AXIAL and span > max(b[1] - b[0] for b in bands.values()):
        z0, z1 = rotating_assembly(schema, bands)
        return sector, round((z0 + z1) / 2.0, 1), \
            "axial: spans the rotating assembly, %.0f-%.0f" % (z0, z1)

    if key in ANCHORS:
        kind, ident = ANCHORS[key]
        a0, a1 = (component_span(schema, ident) if kind == "component"
                  else feature_span(schema, ident))
        # SPREAD ACROSS THE ANCHOR, NOT STACKED AT ITS MIDDLE. Placing every
        # anchored place at the centre of its structure collapsed the whole
        # fore cluster onto one z and produced **19 collisions** where
        # `directory.collisions()` had reported none for the life of the
        # register -- `docking_bays` is a 360-degree footprint, so anything
        # sharing its deck and its z is inside it. Mapping the place's own
        # position in its old band into the anchor keeps the order a reader
        # expects (cobra bays aft of the bays, customs fore of them) and keeps
        # them apart.
        z = _affine(float(place["z_m"]), LEGACY_EXTENTS[place["sector"]],
                    (a0, a1))
        lo, hi = a0 + span / 2.0, a1 - span / 2.0
        z = (a0 + a1) / 2.0 if lo > hi else min(max(z, lo), hi)
        sector = SECTOR_MOVES.get(key, sector)
        if not (bands[sector][0] <= z <= bands[sector][1]):
            sector = next((s for s, b in bands.items() if b[0] <= z <= b[1]),
                          sector)
        return sector, round(z, 1), "anchored to %s %s (%.0f-%.0f)" % (kind, ident, a0, a1)

    if key in EDGE_ANCHORS:
        side, sec = EDGE_ANCHORS[key]
        b = bands[sec]
        z = (b[1] - span / 2.0) if side == "fore" else (b[0] + span / 2.0)
        return sec, round(z, 1), "pinned to the %s edge of %s" % (side, sec)

    # AFTER the two anchor rules, not before. `lowg_bays` is
    # `within="docking_bays"` AND has to be non-rotating, and containment
    # would drag it back into the rotating sphere it must leave. An explicit
    # anchor outranks an inherited one.
    parent = place.get("within")
    if parent and (parent in ANCHORS or parent in EDGE_ANCHORS
                   or parent in AXIAL):
        # A PLACE INSIDE AN ANCHORED PLACE FOLLOWS IT. `bay_elevators`,
        # `mooring_clamps`, `plantroom_bay` and `vorlon_berth` are all
        # `within="docking_bays"` and all sat at the same z as it in the
        # register; remapping them independently would take the bays to the
        # docking sphere and leave their own fittings 70 m behind, in a
        # different hull feature. Containment is a stated relation in the
        # register and this is the only rule that honours it.
        import directory as dr
        pq = next((x for x in dr.PLACES if x["key"] == parent), None)
        if pq is not None:
            psec, pz, _pw = reconcile_place(schema, pq, bands)
            return psec, round(pz, 1), "follows its container %s" % parent

    z = _affine(float(place["z_m"]), LEGACY_EXTENTS[place["sector"]],
                bands[sector])
    lo, hi = bands[sector][0] + span / 2.0, bands[sector][1] - span / 2.0
    if lo > hi:                      # footprint longer than the band
        z, why = (bands[sector][0] + bands[sector][1]) / 2.0, \
            "affine, then centred: footprint %.0f m exceeds the %.0f m band" % (
                span, bands[sector][1] - bands[sector][0])
    else:
        zc = min(max(z, lo), hi)
        why = "affine %s -> %s" % (place["sector"], sector)
        if abs(zc - z) > 1e-6:
            why += ", clamped so the footprint stays inside"
        z = zc
    return sector, round(z, 1), why


def reconciled_places(schema, profile, places=None):
    """`directory.PLACES` with the reconciliation applied. The proposed state."""
    import directory as dr
    src = places if places is not None else dr.PLACES
    bands = sector_bands(schema)
    out = []
    for q in src:
        p = dict(q)
        if q.get("z_m") is None or q.get("sector") is None:
            out.append(p)
            continue
        sec, z, _why = reconcile_place(schema, q, bands)
        p["sector"], p["z_m"] = sec, z
        span = float((q.get("footprint") or (0.0, 0.0))[1])
        if q["key"] in AXIAL and span > max(b[1] - b[0] for b in bands.values()):
            # The tube's footprint IS the rotating assembly. Leaving it at
            # 4,650 m -- a number from the old bands -- would keep a place
            # whose declared length is not the length of the thing it is.
            a0, a1 = rotating_assembly(schema, bands)
            p["footprint"] = (q["footprint"][0], round(a1 - a0, 1))
        out.append(p)
    # THE HULL GETS THE LAST WORD ON z, and it has to, because a band is not a
    # cylinder. Yellow's fore end is the reactor-jettison waist, where the core
    # hull closes to **12.3 m** -- narrower than a corridor. An affine remap and
    # an edge pin both land places there quite happily, and `interior.hull_fit`
    # then reports them outside the ship. This pass slides a place along its own
    # band until the hull over its whole footprint can hold it.
    _shift_into_hull(schema, profile, out, bands)
    # And no two places may end up in one volume. Moving 128 addresses at once
    # is exactly the operation that creates collisions the register has never
    # had, and `directory.collisions()` is the assertion that would go red for
    # it -- so it is asked here, before the patch is written.
    _resolve_collisions(schema, profile, out, bands)
    # The radial half: an assigned-function place over the habitability ceiling
    # is moved INBOARD until it is under it. Longitudinal reconciliation cannot
    # fix a gravity, because gravity is a radius.
    _relieve_gravity(schema, profile, out, bands)
    _drop_broken_containment(out)
    return out


def _drop_broken_containment(places):
    """Clear `within` where the container ended up in another sector.

    A CONTAINMENT THAT CROSSES A SECTOR BOUNDARY IS NOT A CONTAINMENT. Most
    contained places follow their container by the rule in `reconcile_place`,
    so this is empty for them. It fires for the ones whose own anchor
    deliberately OUTRANKS containment: `lowg_bays` is `within="docking_bays"`
    and must be non-rotating, so it leaves for the truss spine while the bays
    stay in the docking sphere -- and it cannot still be inside them.

    Found because `directory.py` asserts it: "its container is in the same
    sector -- yellow vs blue" was the register's last standing FAIL after the
    reconciliation, and it was right. The relation was true of the old
    geography and the move falsified it; nothing had been responsible for
    noticing.

    `within_broken` records what it used to be, so the loss is legible rather
    than silent -- a place that quietly forgets its container reads as a place
    that never had one.
    """
    by_key = {p["key"]: p for p in places}
    for p in places:
        parent = p.get("within")
        if not parent:
            continue
        pq = by_key.get(parent)
        if pq is None or pq.get("sector") == p.get("sector"):
            continue
        p["within"] = None
        p["within_broken"] = parent
        p["note"] = ((p.get("note") or "") + " Was `within=%s`; the "
                     "reconciliation put the two in different sectors (%s vs "
                     "%s) and a containment cannot cross a sector boundary."
                     % (parent, p.get("sector"), pq.get("sector"))).strip()


def _fits_hull(schema, profile, place):
    """Is this place inside the pressure hull over its WHOLE footprint?

    The same limit `interior.rings_fitting_at` applies and `interior.hull_fit`
    reports on -- `core_hull_radius_at(narrowest_z) - HULL_SKIN_M`. Not a new
    standard: the existing one, asked before a place is written down rather
    than after it is built.
    """
    r, _ri, _di, _d = it.place_floor_radius(schema, profile, place)
    if r is None:
        return False
    span = float((place.get("footprint") or (0.0, 0.0))[1])
    zw = it.narrowest_z(profile, place["z_m"], span)
    lim = min(it.core_hull_radius_at(profile, place["z_m"]),
              it.core_hull_radius_at(profile, zw)) - it.HULL_SKIN_M
    return r <= lim


# How far a place may be nudged to clear a waist. A NUDGE, NOT A RELOCATION:
# unbounded, this slid `fusion_core` **1,680 m** out of the reactor and into
# the middle of the truss spine, because its clearance at z 400 is 48.27 m
# against a 48.90 m limit -- 0.63 m -- and any re-rank of Yellow ring 0's deck
# labels flips it. A search with no bound will always find somewhere better
# and will happily take the reactor with it. 250 m is one hull feature's worth
# of slack at this station's scale; a place that cannot be fitted inside that
# is a place whose ADDRESS is wrong, and `interior.hull_fit` is where that
# belongs rather than here.
MAX_NUDGE_M = 250.0


def _shift_into_hull(schema, profile, places, bands, step_m=20.0):
    """Slide any place the hull cannot hold along its own band until it fits.

    Searched outward from the wanted z in both directions, nearest first, so a
    place that already fits does not move and one that does not moves as little
    as the hull allows. Bounded by the band, so a shift can never take a place
    out of the sector the reconciliation just put it in.

    THREE PLACES NEEDED THIS AND ALL THREE FAILED THE SAME WAY: `zerog_maint`
    and `rotation_drivers` pinned to Yellow's fore edge, and `mainstage_node`
    remapped to 2972 -- all inside the explosive-disconnect waist, all built at
    155.4 m against a 12.3 m limit. `hull_fit`'s own docstring records
    `mainstage_node` being moved out of an 18.3 m waist once already; an affine
    remap with no hull in it put it straight back. *A reconciliation that only
    knows about z is a reconciliation that will re-create the defect it was
    written to remove.*
    """
    with _Reconciled(schema, profile, bands=bands, places=places):
        for p in places:
            if p.get("z_m") is None:
                continue
            lo, hi = _z_window(schema, p, bands)
            if lo > hi:                       # axial run; nothing to slide
                continue
            try:
                if _fits_hull(schema, profile, p):
                    continue
            except ValueError:
                continue
            want, found = p["z_m"], None
            lo, hi = max(lo, want - MAX_NUDGE_M), min(hi, want + MAX_NUDGE_M)
            n = int(max(0.0, hi - lo) / step_m) + 2
            for k in range(1, n + 1):
                for cand in (want + k * step_m, want - k * step_m):
                    if not (lo - 1e-6 <= cand <= hi + 1e-6):
                        continue
                    p["z_m"] = round(cand, 1)
                    try:
                        if _fits_hull(schema, profile, p):
                            found = p["z_m"]
                            break
                    except ValueError:
                        continue
                if found is not None:
                    break
            p["z_m"] = found if found is not None else want


def _place_g(schema, profile, place):
    r, _ri, _di, _d = it.place_floor_radius(schema, profile, place)
    return (None if r is None else it.gravity_at(schema, r)), r


def _z_window(schema, place, bands):
    """The z range a place may be slid within, and why it is that range.

    An anchored place may move inside the structure it names and nowhere else
    -- sliding C&C out of Observation Dome 1 to avoid a collision would trade
    a checkable defect for an uncheckable one. Everything else may move inside
    its own sector band. Both are narrowed so the footprint stays inside.
    """
    span = float((place.get("footprint") or (0.0, 0.0))[1])
    asp = anchor_span(schema, place["key"])
    lo, hi = asp if asp else bands[place["sector"]]
    return lo + span / 2.0, hi - span / 2.0


def _resolve_collisions(schema, profile, places, bands, step_m=10.0,
                        passes=6):
    """Slide any place that has landed inside another one, in place.

    Same rule as `directory.collisions()`: same (sector, ring, deck), arcs
    overlapping, z ranges overlapping, declared containment exempt. Searched
    nearest-first from the reconciled z, inside `_z_window`, and every
    candidate must still satisfy the hull -- otherwise this pass would undo
    `_shift_into_hull`'s work to buy space.

    IT ITERATES, AND ONE PASS PROVABLY IS NOT ENOUGH. A single sweep left
    `docking_bays` sitting on `cobra_bays`: the bays are processed after the
    cobra bays, so when they slid to clear a third place they landed on one
    that had already been checked and would not be looked at again. Bounded at
    `passes` and stopped early when a sweep moves nothing, so it terminates
    whether or not the constraint is satisfiable.
    """
    for _ in range(passes):
        if not _resolve_pass(schema, profile, places, bands, step_m):
            return


def _resolve_pass(schema, profile, places, bands, step_m):
    moved = False
    with _Reconciled(schema, profile, bands=bands, places=places):
        for p in places:
            if p.get("z_m") is None or axial_run(schema, p, bands):
                continue
            if not _collides(p, places):
                continue
            want, lo, hi = p["z_m"], *_z_window(schema, p, bands)
            if lo > hi:
                continue
            # BOUNDED FOR THE SAME REASON `_shift_into_hull` IS. Unbounded,
            # this took `fusion_core` 1,680 m up the truss spine to get out of
            # `power_transfer`'s way -- a collision resolved by deleting the
            # reactor from the reactor. When z cannot separate two places
            # inside a nudge, the answer is a deck, not a different sector.
            lo, hi = max(lo, want - MAX_NUDGE_M), min(hi, want + MAX_NUDGE_M)
            found, n = None, int(max(0.0, hi - lo) / step_m) + 2
            for k in range(1, n + 1):
                for cand in (want + k * step_m, want - k * step_m):
                    if not (lo - 1e-6 <= cand <= hi + 1e-6):
                        continue
                    p["z_m"] = round(cand, 1)
                    try:
                        if not _collides(p, places) and \
                                _fits_hull(schema, profile, p):
                            found = p["z_m"]
                            break
                    except ValueError:
                        continue
                if found is not None:
                    break
            p["z_m"] = found if found is not None else want
            if found is None:
                found = _step_off_deck(schema, profile, p, places)
            moved = moved or found is not None
    return moved


def _step_off_deck(schema, profile, p, places):
    """Last resort: move a place one deck in, when z cannot separate it.

    TWO FULL-CIRCLE FOOTPRINTS ON ONE DECK CANNOT BE SEPARATED IN z AT ALL if
    the structure is shorter than the pair. `docking_bays` (360 degrees,
    140 m) and `cobra_bays` (360 degrees, 120 m) are both anchored into the
    docking sphere's 347 m, and the four fittings that live `within` the bays
    are exempt from the bays and not from the cobra bays -- so every z inside
    the sphere collides with something. That is not a placement failure, it is
    the register modelling two interleaved rim systems as two solid rings; the
    show has 28 cobra tubes BETWEEN 24 bay mouths, and C-002 is explicit that
    they are different systems.

    Moving one of them a deck in is the smallest statement that keeps both
    true. It is an invention -- INV-999 -- and it is reported by `--patch` as a
    ring/deck change rather than buried in a z.
    """
    home = p["deck"]
    for deck in range(p["deck"] + 1, p["deck"] + 6):
        p["deck"] = deck
        try:
            if not _collides(p, places) and _fits_hull(schema, profile, p):
                return deck
        except ValueError:
            continue
    p["deck"] = home
    return None


def _relieve_gravity(schema, profile, places, bands):
    """Move an over-heavy ASSIGNED place inboard, mutating it in place.

    Longitudinal reconciliation cannot fix a gravity, because gravity is a
    radius. Four places in Grey declare functions the station rosters people
    for and sit at 1.41-1.64 g, and no deck of Grey ring 0 is under the
    ceiling at all -- ring 0 spans 391-477 m, which is 1.41-1.72 g end to end.
    So the ring has to change, not the deck.

    IT SEARCHES (ring, deck) AND NOT ring ALONE, and the first version of this
    function searched ring alone and could not work. `deck_index_for` derives a
    ring's index mapping from the deck NUMBERS the register puts on that ring;
    move a place to an empty ring and it is the only label there, so it ranks
    to index 0 -- the OUTERMOST deck of the new ring, which on Grey ring 1 is
    391 m and still over the ceiling. A place is only relieved by landing on a
    deck deep enough, and that is a number the search has to find.

    The mutation is deliberate and visible: `deck_index_for` reads the live
    register, so a trial has to be IN the register to be evaluated honestly.
    The cost is that removing a label re-ranks the ring it left -- Grey ring 0
    loses four of its nineteen labels here, so the six places above them each
    move out one rung. That is the property `deck_index_for`'s own docstring
    warns about, it is reported by `--patch`, and it is why this runs once
    rather than iterating to a fixed point: a second pass would chase its own
    tail.
    """
    with _Reconciled(schema, profile, bands=bands, places=places):
        for p in places:
            if p.get("z_m") is None or _permits_heavy(p):
                continue
            try:
                g0, _r0 = _place_g(schema, profile, p)
            except ValueError:
                continue
            if g0 is None or g0 <= it.HABITABLE_G_MAX:
                continue
            home, found = (p["ring"], p["deck"]), None
            for ring in range(p["ring"], 5):
                for deck in range(0, 40):
                    p["ring"], p["deck"] = ring, deck
                    try:
                        g, _r = _place_g(schema, profile, p)
                    except ValueError:
                        continue
                    if g is None or g > it.HABITABLE_G_MAX:
                        continue
                    if _collides(p, places):
                        continue
                    found = (ring, deck)
                    break
                if found:
                    break
            p["ring"], p["deck"] = found or home


def _collides(p, places):
    """Would this address land `p` on top of an existing place?

    `directory.overlaps()`'s rule, asked BEFORE the address is written rather
    than after -- same deck, arcs overlapping, z ranges overlapping, and
    declared containment exempt. The first version of `_relieve_gravity` had
    no such test and put `gravity_torus` (220 deg +/- 15), `black_market`
    (230 +/- 15) and `happy_daze` (240 +/- 2.5) all on Grey ring 1 deck 11 at
    the same z. Three rooms in one volume: the gravity gate would have gone
    green and the register's oldest assertion would have gone red, which is
    the shape of every defect this file exists to stop.
    """
    def arcs_overlap(a0, s0, a1, s1):
        if s0 >= 360.0 or s1 >= 360.0:
            return True
        d = abs((a0 - a1 + 180.0) % 360.0 - 180.0)
        return d < (s0 + s1) / 2.0

    for q in places:
        if q is p or q.get("z_m") is None:
            continue
        if (q["sector"], q["ring"], q["deck"]) != (p["sector"], p["ring"],
                                                   p["deck"]):
            continue
        if q.get("within") == p["key"] or p.get("within") == q["key"]:
            continue
        if not arcs_overlap(p["angle_deg"], p["footprint"][0],
                            q["angle_deg"], q["footprint"][0]):
            continue
        pz = (p["z_m"] - p["footprint"][1] / 2, p["z_m"] + p["footprint"][1] / 2)
        qz = (q["z_m"] - q["footprint"][1] / 2, q["z_m"] + q["footprint"][1] / 2)
        if pz[1] <= qz[0] or qz[1] <= pz[0]:
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
class Gate:
    def __init__(self, label):
        self.label, self.rows, self.n_ok, self.n_bad = label, [], 0, 0

    def check(self, name, ok, detail=""):
        self.rows.append((name, bool(ok), detail))
        if ok:
            self.n_ok += 1
        else:
            self.n_bad += 1
        return ok

    def report(self):
        print("\n%s" % self.label)
        print("-" * len(self.label))
        for name, ok, detail in self.rows:
            print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
            if detail:
                for line in detail.rstrip().split("\n"):
                    print("        %s" % line)
        print("  %d passed, %d FAILED" % (self.n_ok, self.n_bad))
        return self.n_bad == 0


def _band_str(bands):
    return "  ".join("%s %.0f-%.0f" % (s, bands[s][0], bands[s][1])
                     for s in ORDER_AFT_TO_FORE)


def gate(schema, profile, legacy=False, proposed=False, verbose=True):
    """Five questions about the geography, three about its wiring."""
    import directory as dr

    # THE DEFAULT MODE READS THE YAML, NOT THE DERIVATION. A gate that
    # substituted its own answer for the shipped one before measuring would be
    # measuring itself -- and it did, on the first run of this file, which is
    # why G1 came back green on a schema whose five bands were all wrong.
    yaml_bands = {s: (float(schema["sectors"]["extents_m"][s]["z0"]),
                      float(schema["sectors"]["extents_m"][s]["z1"]))
                  for s in ORDER_AFT_TO_FORE}
    bands = ({s: LEGACY_EXTENTS[s] for s in ORDER_AFT_TO_FORE} if legacy
             else sector_bands(schema) if proposed else yaml_bands)
    places = (reconciled_places(schema, profile) if proposed
              else [dict(q) for q in dr.PLACES])
    mode = ("LEGACY -- the pre-4t schema and the register as authored" if legacy
            else "PROPOSED -- this module's reconciliation, applied in memory"
            if proposed else "SHIPPED -- station.yaml and directory.PLACES as they are")
    g = Gate("GEOGRAPHY GATE  [%s]" % mode)
    _DERIVED = sector_bands(schema)
    if verbose:
        print("bands in force: %s" % _band_str(bands))
        print("hull-derived:   %s" % _band_str(_DERIVED))

    with _Reconciled(schema, profile, bands=bands, places=places):
        # -- G1 -------------------------------------------------------------
        # `sector_bands` is evaluated OUTSIDE the substitution, from the
        # features, so it is unaffected by whichever bands are in force.
        derived = _DERIVED
        bad = []
        for s in ORDER_AFT_TO_FORE:
            if abs(bands[s][0] - derived[s][0]) > 0.5 or \
                    abs(bands[s][1] - derived[s][1]) > 0.5:
                bad.append("%-7s band %.0f-%.0f  hull %.0f-%.0f   "
                           "(aft edge off by %+.0f m, fore by %+.0f m; "
                           "overlap %.0f m of %.0f)"
                           % (s, bands[s][0], bands[s][1],
                              derived[s][0], derived[s][1],
                              bands[s][0] - derived[s][0],
                              bands[s][1] - derived[s][1],
                              max(0.0, min(bands[s][1], derived[s][1])
                                  - max(bands[s][0], derived[s][0])),
                              bands[s][1] - bands[s][0]))
        # partition, order, coverage
        L = float(schema["station"]["overall_length_m"]["value"])
        seq = [bands[s] for s in ORDER_AFT_TO_FORE]
        if abs(seq[0][0]) > 1e-6 or abs(seq[-1][1] - L) > 1e-6:
            bad.append("the bands do not cover [0, %.0f]: %.0f - %.0f"
                       % (L, seq[0][0], seq[-1][1]))
        for a, b in zip(seq, seq[1:]):
            if abs(a[1] - b[0]) > 1e-6:
                bad.append("gap or overlap at %.0f / %.0f" % (a[1], b[0]))
        g.check("G1  every sector band is a whole number of hull features",
                not bad, "\n".join(bad))

        # -- G2 -------------------------------------------------------------
        bad, n = [], 0
        for q in places:
            if q.get("z_m") is None or q.get("sector") is None:
                continue
            n += 1
            want = SECTOR_FEATURES[q["sector"]]
            here = feature_at(schema, q["z_m"])
            b = bands[q["sector"]]
            span = float((q.get("footprint") or (0.0, 0.0))[1])
            why = None
            run = axial_run(schema, q, bands)
            if run:
                # AN AXIAL RUN IS EXEMPT FROM BAND CONTAINMENT AND NOT FROM THE
                # GATE. `core_shuttle` is the tube, not a room; it spans four
                # bands by construction, and a car inside it is wherever the
                # tube reaches. Two things are asserted instead: the run's
                # declared length IS the rotating assembly's, and every axial
                # place stays inside the run. A footprint left over from the
                # old bands still fails the first; a car parked outside the
                # tube fails the second.
                if q["key"] in AXIAL and span > max(
                        b[1] - b[0] for b in bands.values()):
                    if abs(span - (run[1] - run[0])) > 1.0:
                        bad.append("%-22s %-6s axial run declares %.0f m; the "
                                   "rotating assembly is %.0f m (%.0f-%.0f)"
                                   % (q["key"], q["sector"], span,
                                      run[1] - run[0], run[0], run[1]))
                elif not (run[0] <= q["z_m"] - span / 2.0
                          and q["z_m"] + span / 2.0 <= run[1]):
                    bad.append("%-22s %-6s rides the axis but sits at %.0f, "
                               "outside the run %.0f-%.0f"
                               % (q["key"], q["sector"], q["z_m"], run[0],
                                  run[1]))
                continue
            asp = anchor_span(schema, q["key"])
            if here not in want:
                why = "is inside %s, which is %s" % (
                    here, next((s for s, f in SECTOR_FEATURES.items()
                                if here in f), "no sector"))
            elif asp and not (asp[0] <= q["z_m"] <= asp[1]):
                why = "is %.0f m from %s (%.0f-%.0f), the structure it names" % (
                    min(abs(q["z_m"] - asp[0]), abs(q["z_m"] - asp[1])),
                    ANCHORS[q["key"]][1], asp[0], asp[1])
            elif not (b[0] - 1e-6 <= q["z_m"] <= b[1] + 1e-6):
                why = "z is outside its own band %.0f-%.0f" % b
            elif span and (q["z_m"] - span / 2.0 < b[0] - 1e-6 or
                           q["z_m"] + span / 2.0 > b[1] + 1e-6):
                why = "its %.0f m footprint leaves the band %.0f-%.0f" % (
                    span, b[0], b[1])
            if why:
                bad.append("%-22s %-6s z=%7.1f  %s" % (q["key"], q["sector"],
                                                      q["z_m"], why))
        g.check("G2  every place is inside a hull feature its sector is made of",
                not bad,
                ("%d of %d places are not:\n" % (len(bad), n)) +
                "\n".join(bad[:40]) +
                ("\n... and %d more" % (len(bad) - 40) if len(bad) > 40 else ""))

        # -- G3 -------------------------------------------------------------
        bad = []
        drum = it.drum_sector(schema, profile)
        want = bands[drum][1] - bands[drum][0]
        claims = [("sectors.extents_m[%s]" % drum, want),
                  ("bio_habitat.interior_length_m",
                   float(schema["bio_habitat"]["interior_length_m"]["value"]))]
        d_int = float(schema["bio_habitat"]["interior_diameter_m"]["value"])
        area = float(schema["bio_habitat"]["interior_surface_m2"]["value"])
        claims.append(("bio_habitat.interior_surface_m2 / (pi*d)",
                       area / (math.pi * d_int)))
        for name, v in claims:
            if abs(v - want) > 1.0:
                bad.append("%-42s = %8.1f m   (the drum band is %.1f m, off by %+.1f)"
                           % (name, v, want, v - want))
        g.check("G3  the habitat drum has exactly one length", not bad,
                ("the drum sector is %s, band %.0f-%.0f = %.1f m\n" %
                 (drum, bands[drum][0], bands[drum][1], want)) + "\n".join(bad))

        # -- G4 -------------------------------------------------------------
        bad, heavy = [], 0
        for q in places:
            if q.get("z_m") is None:
                continue
            r, _ri, _di, _d = it.place_floor_radius(schema, profile, q)
            if r is None:
                continue
            gg = it.gravity_at(schema, r)
            if gg <= it.HABITABLE_G_MAX:
                continue
            heavy += 1
            if _permits_heavy(q):
                continue
            bad.append("%-22s %-6s ring%d deck%-3d r=%7.1f  %6.4f g   "
                       "functions=%s"
                       % (q["key"], q["sector"], q["ring"], q["deck"], r, gg,
                          ",".join(q.get("functions", ())) or "(none)"))
        g.check("G4  no place is above HABITABLE_G_MAX unless its function allows it",
                not bad,
                ("%d places are above %.2f g; %d of them declare no function "
                 "that permits it:\n" % (heavy, it.HABITABLE_G_MAX, len(bad))) +
                "\n".join(bad))

        # -- G5 -------------------------------------------------------------
        bad = []
        for q in places:
            if q.get("z_m") is None:
                continue
            fns = set(q.get("functions", ()))
            r, _ri, _di, _d = it.place_floor_radius(schema, profile, q)
            gg = it.gravity_at(schema, r) if r is not None else float("nan")
            if fns & MICRO_G_FUNCTIONS:
                if rotating(schema, q["sector"]):
                    bad.append("%-22s declares micro-gravity handling and sits "
                               "in %s, which ROTATES: %.4f g at r=%.1f"
                               % (q["key"], q["sector"], gg, r or -1))
            if fns & LOW_G_FUNCTIONS and gg > LOW_G_CEILING:
                bad.append("%-22s declares low gravity and is at %.4f g"
                           % (q["key"], gg))
        g.check("G5  a place naming a gravity regime is built at that regime",
                not bad, "\n".join(bad))

        # -- G6 -------------------------------------------------------------
        # NOT IN THE BRIEF, AND IT IS HERE BECAUSE THIS MODULE BROKE IT.
        # Anchoring every landmark to the structure it names collapsed the
        # whole fore cluster onto one z and produced **19 collisions** where
        # `directory.collisions()` had reported none for the life of the
        # register. Moving 128 addresses at once is exactly the operation that
        # creates them, so the gate that owns the move has to own the
        # consequence rather than leaving it for a 20-minute gate downstream.
        bad = []
        seen = set()
        for p in places:
            if p.get("z_m") is None:
                continue
            if _collides(p, places):
                for q in places:
                    if q is p or q.get("z_m") is None:
                        continue
                    if tuple(sorted((p["key"], q["key"]))) in seen:
                        continue
                    pp = dict(p)
                    if _collides(pp, [q]):
                        seen.add(tuple(sorted((p["key"], q["key"]))))
                        bad.append("%-20s and %-20s share %s ring%d deck%d "
                                   "at z %.0f / %.0f"
                                   % (p["key"], q["key"], p["sector"],
                                      p["ring"], p["deck"], p["z_m"],
                                      q["z_m"]))
        g.check("G6  no two places occupy the same volume", not bad,
                "\n".join(bad[:30]))

    # -- wiring -------------------------------------------------------------
    w = Gate("WIRING  -- does anything on the shipped path read this module?")
    ex = schema["sectors"]["extents_m"]
    derived = sector_bands(schema)
    drift = ["%-7s yaml %.0f-%.0f  derived %.0f-%.0f"
             % (s, ex[s]["z0"], ex[s]["z1"], derived[s][0], derived[s][1])
             for s in ORDER_AFT_TO_FORE
             if abs(ex[s]["z0"] - derived[s][0]) > 0.5
             or abs(ex[s]["z1"] - derived[s][1]) > 0.5]
    w.check("W1  station.yaml sectors.extents_m equals sector_bands()",
            not drift, "\n".join(drift))
    # W2 USED TO COMPARE `dr.PLACES` AGAINST `reconcile_place`, AND THAT CHECK
    # COULD NEVER PASS -- which is the mirror of a gate that cannot fail, and
    # just as useless. `reconcile_place` is the RAW affine mapping;
    # `reconciled_places` then runs `_shift_into_hull`, `_resolve_collisions`
    # and `_relieve_gravity` on top, and those legitimately move places. The
    # two disagree by construction.
    #
    # It is also no longer the right question. The register now DERIVES its
    # addresses from this module instead of carrying a copy of them, so "do the
    # two agree" is answered by construction -- and re-running the mapping over
    # already-mapped places would double-apply the affine and is not idempotent.
    #
    # What remains worth asking, and what actually fails if the wiring breaks:
    # did the register run it? `directory.RECONCILED` is False whenever the
    # import or the reconciliation raised, which is exactly the case where the
    # station silently goes back to putting C&C inside the navigation spike.
    w.check("W2  directory ran the reconciliation (directory.RECONCILED)",
            getattr(dr, "RECONCILED", False) is True,
            "directory.RECONCILED is %r -- the register is on the pre-4u bands. "
            "directory.py prints the reason to stderr on import."
            % (getattr(dr, "RECONCILED", None),))
    src = open(os.path.join(ROOT, "station", "directory.py"),
               encoding="utf-8").read()
    w.check("W3  directory.py imports geography",
            "import geography" in src,
            "it does not. Until it does, the register is a second copy of the "
            "geography and can drift from it again.")

    ok_g = g.report() if verbose else g.n_bad == 0
    ok_w = w.report() if verbose else w.n_bad == 0
    if verbose:
        print("\n%s: geography %s, wiring %s"
              % (mode.split(" --")[0],
                 "GREEN" if ok_g else "RED", "GREEN" if ok_w else "RED"))
    return ok_g and ok_w


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
LANDMARKS = ("cnc", "obs_dome_1", "customs_north", "arrival_concourse",
             "zocalo", "casino", "security_central", "central_corridor",
             "council_chamber", "ambassadorial_suites", "earharts",
             "fresh_air", "alien_sector", "downbelow", "plant_zone",
             "docking_bays", "medlab_one", "the_garden", "happy_daze",
             "micro_g_bays", "zerog_maint", "lowg_bays", "core_shuttle",
             "zen_garden")


def landmark_table(schema, profile, places, bands, title):
    print("\n%s" % title)
    print("%-22s %-7s %9s %-26s %8s %8s %s"
          % ("place", "sector", "z_m", "hull feature at z", "r_m", "g", "ok"))
    by = {q["key"]: q for q in places}
    n_ok = 0
    with _Reconciled(schema, profile, bands=bands, places=places):
        for k in LANDMARKS:
            q = by.get(k)
            if not q or q.get("z_m") is None:
                print("%-22s  -- not in the register --" % k)
                continue
            f = feature_at(schema, q["z_m"])
            r, _ri, _di, _d = it.place_floor_radius(schema, profile, q)
            gg = it.gravity_at(schema, r) if r is not None else float("nan")
            asp = anchor_span(schema, k)
            run = axial_run(schema, q, bands)
            ok = (run[0] <= q["z_m"] <= run[1]) if run \
                else f in SECTOR_FEATURES[q["sector"]]
            if run:
                f += "  [axial run %.0f-%.0f]" % run
            if ok and asp and not (asp[0] <= q["z_m"] <= asp[1]):
                ok = False
                f += "  [%s is at %.0f-%.0f]" % (ANCHORS[k][1], asp[0], asp[1])
            n_ok += bool(ok)
            print("%-22s %-7s %9.1f %-46s %8.1f %8.4f %s"
                  % (k, q["sector"], q["z_m"], f, r or -1, gg,
                     "OK" if ok else "**"))
    print("%d of %d landmarks are inside a structure consistent with their name"
          % (n_ok, len(LANDMARKS)))
    return n_ok


def patch(schema, profile):
    """The exact register edit, for a caller who owns directory.py."""
    import directory as dr
    bands = sector_bands(schema)
    rec = {q["key"]: q for q in reconciled_places(schema, profile)}
    print("# station/directory.py -- PLACES: the reconciled addresses.")
    print("# %-20s %-7s %9s -> %-7s %9s  %8s  %s"
          % ("key", "sector", "z_m", "sector", "z_m", "move_m", "why"))
    # THE PRINTED z IS THE FINAL ONE. An earlier version printed
    # `reconcile_place`'s answer while `reconciled_places` went on to slide
    # three places out of the disconnect waist and four inboard off the
    # gravity ceiling -- so the patch disagreed with the state the gate had
    # just passed. A patch that is not the thing that was measured is a third
    # description of the station.
    moves, sect, radial = [], [], []
    for q in dr.PLACES:
        if q.get("z_m") is None:
            continue
        n = rec[q["key"]]
        _s, _z, why = reconcile_place(schema, q, bands)
        sec, z = n["sector"], n["z_m"]
        d = z - q["z_m"]
        extra = ""
        if (n["ring"], n["deck"]) != (q["ring"], q["deck"]):
            extra += "  ring %d->%d deck %d->%d" % (q["ring"], n["ring"],
                                                    q["deck"], n["deck"])
            radial.append(q["key"])
        if n.get("footprint") != q.get("footprint"):
            extra += "  footprint %s->%s" % (q["footprint"], n["footprint"])
        if abs(_z - z) > 0.05:
            why += ", then shifted %+.0f m so the hull can hold it" % (z - _z)
        if sec == q["sector"] and abs(d) < 0.05 and not extra:
            continue
        if sec != q["sector"]:
            sect.append(q["key"])
        moves.append(abs(d))
        print("  %-20s %-7s %9.1f -> %-7s %9.1f  %+8.1f  %s%s"
              % (q["key"], q["sector"], q["z_m"], sec, z, d, why, extra))
    n_loc = sum(1 for q in dr.PLACES if q.get("z_m") is not None)
    ms = sorted(moves)
    print("\n%d of %d located places move." % (len(moves), n_loc))
    print("  largest %.1f m, mean |move| %.1f m, median %.1f m"
          % (ms[-1] if ms else 0.0, sum(ms) / len(ms) if ms else 0.0,
             ms[len(ms) // 2] if ms else 0.0))
    for lo, hi in ((0, 50), (50, 200), (200, 500), (500, 2000), (2000, 1e9)):
        print("  %6.0f - %-9s %3d"
              % (lo, ("%.0f m" % hi) if hi < 1e9 else "up",
                 sum(1 for m in ms if lo <= m < hi)))
    print("  %d change SECTOR: %s" % (len(sect), ", ".join(sect)))
    print("  %d change ring/deck: %s" % (len(radial), ", ".join(radial)))


def _selftest(schema, profile):
    """Assertions that must hold for the derivation itself to mean anything."""
    b = sector_bands(schema)
    L = float(schema["station"]["overall_length_m"]["value"])
    assert abs(b["yellow"][0]) < 1e-9 and abs(b["blue"][1] - L) < 1e-9
    seq = [b[s] for s in ORDER_AFT_TO_FORE]
    assert all(abs(a[1] - c[0]) < 1e-9 for a, c in zip(seq, seq[1:]))
    # Every leaf feature belongs to exactly one sector: no hull is unaddressed
    # and none is claimed twice. A partition of the FEATURES, not just of z.
    owned = [f for fs in SECTOR_FEATURES.values() for f in fs]
    assert len(owned) == len(set(owned)), "a feature is in two sectors"
    leaves = {f for f, _z0, _z1 in leaf_features(schema)}
    assert set(owned) == leaves, (
        "unassigned: %s / unknown: %s" % (leaves - set(owned),
                                          set(owned) - leaves))
    # The drum identification must survive the new bands, or the reconciliation
    # has moved the Garden into the industrial block.
    with _Reconciled(schema, profile, bands=b):
        assert it.drum_sector(schema, profile) == "green", \
            "drum_sector() no longer picks green"
        assert abs(it.sector_radius(schema, profile, "green") - 278.3) < 1e-6
    # Not rotating, and it is the only one.
    assert not rotating(schema, "yellow")
    assert all(rotating(schema, s) for s in ("grey", "green", "red", "blue"))
    print("geography selftest: OK  (%s)" % _band_str(b))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--legacy", action="store_true",
                    help="the frozen pre-4t bands and the register as authored")
    ap.add_argument("--proposed", action="store_true",
                    help="apply this module's reconciliation in memory first")
    ap.add_argument("--landmarks", action="store_true")
    ap.add_argument("--patch", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    schema, profile = load()
    if a.selftest:
        _selftest(schema, profile)
    if a.landmarks:
        import directory as dr
        if a.legacy:
            landmark_table(schema, profile, [dict(q) for q in dr.PLACES],
                           {s: LEGACY_EXTENTS[s] for s in ORDER_AFT_TO_FORE},
                           "LANDMARKS -- LEGACY (pre-4t bands, register as authored)")
        elif a.proposed:
            landmark_table(schema, profile,
                           reconciled_places(schema, profile),
                           sector_bands(schema),
                           "LANDMARKS -- PROPOSED (hull-derived bands, register reconciled)")
        else:
            landmark_table(schema, profile, [dict(q) for q in dr.PLACES],
                           sector_bands(schema),
                           "LANDMARKS -- SHIPPED")
    if a.patch:
        patch(schema, profile)
    if a.gate:
        ok = gate(schema, profile, legacy=a.legacy, proposed=a.proposed)
        return 0 if ok else 1
    if not any((a.gate, a.landmarks, a.patch, a.selftest)):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
