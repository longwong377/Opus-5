"""PLC rows: a place's ADDRESS, field by field, against `directory.PLACES`.

WHAT THIS CHECKS AND WHY IT IS NOT ENOUGH. Every PLC row opens with an address
line the spec authored independently of the register:

    `blue/0/0 0° z7115 · 360°×140 m · docking_bay/generic* · auth 3` · TILING 1 → **1,092**

Nine facts, all of them checkable: sector, ring, deck, angle, z, angular
footprint, axial footprint, module, authority. The previous harness compared
NONE of them -- it resolved `PLC-nnn` to `PLACES[nnn-1]` and returned that
place's key, so its only failure mode was an index past the end of a list and
it passed 129 of 129 by arithmetic.

`SUFFICIENT = False` and that is not modesty. A place standing at the address
the spec cites says nothing about whether it contains the program, fixtures,
interacts, staff and schedule the row goes on to describe. Those are separate
harnesses and they land per-family as they are built; until then a PLC row is
RED with its address verified, which `spec_check.py` reports as a different
kind of red from "nothing checked this at all".

THE UNITS ARE THE TRAP, and they are worth stating because the first version of
this got one wrong. `footprint` in `directory.py` is `(angular_span_deg,
axial_span_m)` -- the first number is DEGREES and the second METRES, so the
spec's `360°×140 m` maps to `(360.0, 140.0)` and a reader who assumes both are
metres finds a 360 m room. The register's own `_P` signature is the authority.
"""
import re

SUFFICIENT = False

# `blue/0/0 0° z7115 · 360°×140 m · docking_bay/generic* · auth 3`
# `-` IS A REAL VALUE IN THE MODULE SLOT AND IT IS THE COMMONEST ONE. 73 of
# the 129 rows read `-/generic`, meaning "no bespoke builder, the generic room
# maker does it"; 21 read `<module>/<kind>` and 20 `<module>/<kind>*`, the star
# marking a builder that exists but is not wired. A regex demanding a lowercase
# module name parsed 50 rows and reported the other 79 as MALFORMED -- which is
# the failure mode a harness must not have, because "I cannot read this" and
# "this disagrees" are opposite findings and only one of them is about the
# station. Measured the shapes before widening it rather than loosening until
# the number went up.
_ADDR = re.compile(
    r"`(?P<sector>[a-z]+)/(?P<ring>\d+)/(?P<deck>\d+)\s+"
    r"(?P<angle>-?[\d.]+)°\s*z(?P<z>-?[\d.]+)\s*·\s*"
    r"(?P<fdeg>[\d.]+)°×(?P<fm>[\d.]+)\s*m\s*·\s*"
    r"(?P<module>[a-z_]+|-)/(?P<kind>[a-z]+)\*?\s*·\s*auth\s*(?P<auth>\d)")
# `· TILING 1 → **1,092**` or `· TILING **1 → 24 (one room)**`
_TILING = re.compile(r"TILING\s*\**\s*(\d+)\s*(?:→|->)\s*\**\s*([\d,]+)")
_KEY = re.compile(r"^#+\s*PLC-\d+\s*`([a-z0-9_]+)`")


def _tol(name):
    """How close counts as equal, per field, and why.

    Angles and z are quoted in the spec to the nearest degree and metre, so a
    register value of 7115.0 against a spec `z7115` must pass while 7960 vs
    3250 must not. The footprint is quoted exactly. Authority, ring and deck
    are integers and are compared as such.
    """
    return {"angle": 0.51, "z": 0.51, "fdeg": 0.01, "fm": 0.01}.get(name, 0.0)


def check(row):
    import directory as DIR                                      # noqa: PLC0415
    from spec_harness import spec_text                           # noqa: PLC0415
    text = spec_text(row.get("at", ""), lines=3)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    head = text.splitlines()[0].strip()
    mk = _KEY.match(head)
    if not mk:
        return False, "heading names no place key: %r" % head[:60]
    key = mk.group(1)
    try:
        place = DIR.by_key(key)
    except KeyError:
        return False, "spec names `%s`, which directory.PLACES has no row for" % key

    ma = _ADDR.search(text)
    if not ma:
        return False, "`%s`: no parsable address line under the heading" % key
    g = ma.groupdict()
    got = {
        "sector": place["sector"], "ring": place["ring"], "deck": place["deck"],
        "angle": place["angle_deg"], "z": place["z_m"],
        "fdeg": place["footprint"][0], "fm": place["footprint"][1],
        "module": place.get("module") or "", "auth": place["auth"],
    }
    bad = []
    for f in ("sector", "ring", "deck", "angle", "z", "fdeg", "fm", "auth"):
        want = g[f]
        if f in ("ring", "deck", "auth"):
            same = int(want) == int(got[f])
        elif f == "sector":
            same = want == got[f]
        else:
            same = abs(float(want) - float(got[f])) <= _tol(f)
        if not same:
            bad.append("%s spec=%s register=%s" % (f, want, got[f]))
    # THE MODULE IS COMPARED LENIENTLY AND THE REASON IS IN THE REGISTER.
    # `directory._P` leaves `module=None` for a place the generic room builder
    # makes, and the spec writes the builder it EXPECTS -- so `module=None`
    # against a named module is a statement about what is built, not about the
    # address, and belongs to a content harness. Only a DISAGREEMENT between
    # two named modules is an address defect.
    if got["module"] and g["module"] != "-" and g["module"] != got["module"]:
        bad.append("module spec=%s register=%s" % (g["module"], got["module"]))
    if bad:
        return False, "`%s`: %s" % (key, "; ".join(bad))
    return True, "%s @ %s/%d/%d %.0f° z%.0f %.0f°×%.0f m auth %s" % (
        key, got["sector"], got["ring"], got["deck"], got["angle"],
        got["z"], got["fdeg"], got["fm"], got["auth"])
