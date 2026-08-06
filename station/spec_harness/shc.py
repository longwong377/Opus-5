"""SHC rows: Shell C, the thirteen sealed volumes -- their anchors, their
numbers, and whether their stencils exist anywhere in the station at all.

WHAT AN SHC ROW CLAIMS. Each is one markdown table row with four cells after
the ID -- volume, size, closure + stencil, reason -- and every cell makes a
different KIND of claim:

    | SHC-01 | the Markab quarter (adjoins PLC-023) | one zone arm |
      welded plate, wreath bracket. "SECTION CLOSED BY ORDER — MEDICAL
      AUTHORITY B5 — 2259. NO ENTRY. LET THEM REST." | the only monument ... |

  * the VOLUME cell names things the model must know: `PLC-023`, and feature
    ids like `aft_hull_block`, `bearing_neck`, `red_section`.
  * the SIZE cell is arithmetic: 0.0742 km³, 397,500 m³, "600 of the 745".
    Some of it recomputes from the profile in milliseconds; some of it is
    recorded in `docs/volume-audit.md` or a module's own header; some of it
    only sums against ITSELF, which is still a check and caught SHC-07.
  * the CLOSURE cell contains a stencil in double quotes, and §3's whole-shell
    CHECK says "every sealed face carries its table stencil verbatim, LOOK
    answers with it". A stencil is a LITERAL STRING, so its absence from every
    source and every baked sidecar in the project is conclusive.

WHY `SUFFICIENT = False`, stated precisely rather than as modesty. Three of the
four cells are settleable here and the fourth is not: that a stencil string
EXISTS in the project is necessary and nowhere near sufficient for "the sealed
face carries it and LOOK answers with it", which needs the built deck, the
material, and the player standing in front of it. This project has been burned
nine times by machinery that exists and is never called, and a string found by
grep is exactly that shape of evidence. So a passing row here means: the spec's
anchors resolve, its numbers agree, and its stencil is at least present. GREEN
needs the built station.

THE SEARCH HAS A POSITIVE CONTROL AND IT IS NOT DECORATION. "I cannot read
this" and "this disagrees" are opposite findings and only one is about the
station (`plc.py`'s lesson, one level down). A corpus reader that silently read
nothing would report all thirteen stencils missing and look exactly like a
finding. So `_corpus()` asserts it can find `broadcast.BOARD_VOICE`'s
authority-1 board text, which IS in the tree; if that fails, every stencil claim
returns "corpus unreadable" instead of "stencil missing".

A COMMENT IS NOT CONTENT, AND THE FIRST VERSION OF THIS PASSED ON ONE. Raw text
search reported SHC-13's "Grey 17" present because `interior.py` discusses it in
a comment, and reported SHC-01's stencil present because THIS FILE's own
negative control had planted it. Both are the same defect: the evidence was the
project talking about the thing rather than the project containing it. So a hit
is confirmed to be a STRING LITERAL -- `ast` for Python, a quoted-span scan for
GDScript and JSON -- and `station/spec_harness/` is excluded from the corpus,
because a harness may not be its own evidence.

The confirmation is two-phase so it stays cheap: absence from the raw bytes is
conclusive on its own and costs one 0.17 s scan, and only a file that DOES
contain the string is ever parsed. Thirteen rows, no hits, no parsing.
"""
import ast
import math
import os
import re

SUFFICIENT = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The one string that proves the corpus reader works: `broadcast.BOARD_VOICE`
# is transcribed from reference/01-station-exterior/welcome to babylon 5.webp
# and `interact.read_text` serves it for `welcome_board`.
_CONTROL = "WELCOME TO BABYLON 5"

_CELLS = re.compile(r"^\|(.+)\|\s*$")
_QUOTED = re.compile(r'"([^"]{6,})"')
_PLC = re.compile(r"PLC-(\d+)")
_KEYLINE = re.compile(r"^#+\s*PLC-(\d+)\s*`([a-z0-9_]+)`")
_TILING = re.compile(r"TILING\s*\**\s*(\d+)\s*(?:→|->)\s*\**\s*([\d,]+)")

_CACHE = {}


# ---------------------------------------------------------------------------
# Reading what the project actually contains
# ---------------------------------------------------------------------------
def _norm(s):
    """Uppercase, dashes unified, whitespace collapsed.

    DELIBERATELY WIDE. A stencil written in a Python source with an ASCII
    hyphen where the spec has an em dash is the same stencil, and a search that
    still finds nothing after widening is stronger evidence of absence than one
    that insists on the typography.
    """
    s = s.upper()
    for ch in "—–‒‐−":
        s = s.replace(ch, "-")
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def _corpus():
    """[(path, normalised source)] for every file that could hold a string.

    `station/generated/scene/` is skipped -- it is 5.1 GB of meshes and no
    stencil lives in an OBJ -- but every `.py`, `.gd` and every JSON sidecar
    under 4 MB is read. `station/spec_harness/` is skipped too: this file
    quotes SHC-01's stencil in its own negative control, and a harness that
    counts itself as evidence is a harness that cannot fail.
    """
    if "corpus" in _CACHE:
        return _CACHE["corpus"]
    out = []
    for top in ("station", "godot", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(ROOT, top)):
            if ("__pycache__" in dp or os.sep + "scene" in dp
                    or "spec_harness" in dp):
                continue
            for f in fn:
                if not f.endswith((".py", ".gd", ".json", ".tscn", ".tres")):
                    continue
                p = os.path.join(dp, f)
                try:
                    if os.path.getsize(p) > 4_000_000:
                        continue
                    out.append((p, _norm(open(p, encoding="utf-8",
                                              errors="replace").read())))
                except OSError:                                  # noqa: PERF203
                    continue
    _CACHE["corpus"] = out
    return out


def _literals(path):
    """The normalised string literals one file can emit.

    Python goes through `ast` so a `#` comment cannot masquerade as content;
    module, class and function docstrings are dropped for the same reason --
    prose ABOUT a stencil is not the stencil. GDScript, JSON and scene files
    have no comment form that survives a quoted-span scan, so a regex is
    honest for them.
    """
    if ("lit", path) in _CACHE:
        return _CACHE[("lit", path)]
    got = set()
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        src = ""
    if path.endswith(".py"):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = None
        if tree is not None:
            doc = set()
            for node in ast.walk(tree):
                body = getattr(node, "body", None)
                if isinstance(body, list) and body:
                    first = body[0]
                    if (isinstance(first, ast.Expr)
                            and isinstance(first.value, ast.Constant)
                            and isinstance(first.value.value, str)):
                        doc.add(id(first.value))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant)
                        and isinstance(node.value, str)
                        and id(node) not in doc):
                    got.add(_norm(node.value))
    else:
        for q in re.findall(r'"((?:[^"\\]|\\.)*)"', src):
            got.add(_norm(q))
    _CACHE[("lit", path)] = got
    return got


def _in_content(needle):
    """(found, where). `needle` is already normalised.

    Two phases and the cheap one is conclusive: a string absent from the raw
    bytes of every file cannot be in a literal in any of them, so nothing is
    parsed in the common case. Only a file that DOES contain it is asked
    whether it contains it as something a program could emit.
    """
    for path, body in _corpus():
        if needle not in body:
            continue
        for lit in _literals(path):
            if needle in lit:
                return True, os.path.relpath(path, ROOT)
    return False, ""


def _corpus_ok():
    return _in_content(_CONTROL)[0]


def _places_md():
    if "places_md" not in _CACHE:
        _CACHE["places_md"] = open(
            os.path.join(ROOT, "docs/spec/PLACES.md"), encoding="utf-8").read()
    return _CACHE["places_md"]


def _plc_keys():
    """PLC number -> the place key its own heading names."""
    if "plc" not in _CACHE:
        out = {}
        for ln in _places_md().splitlines():
            m = _KEYLINE.match(ln.strip())
            if m:
                out[int(m.group(1))] = m.group(2)
        _CACHE["plc"] = out
    return _CACHE["plc"]


def _plc_block(n):
    """The spec text of one PLC row, heading to the next heading."""
    src = _places_md().splitlines()
    want = "PLC-%03d" % n
    for i, ln in enumerate(src):
        if ln.startswith("#") and want in ln:
            out = [ln]
            for j in range(i + 1, len(src)):
                if src[j].startswith("#"):
                    break
                out.append(src[j])
            return "\n".join(out)
    return ""


def _profile():
    if "prof" not in _CACHE:
        import json                                              # noqa: PLC0415
        _CACHE["prof"] = json.load(open(
            os.path.join(ROOT, "station/schema/radius_profile.json"),
            encoding="utf-8"))["profile"]
    return _CACHE["prof"]


def _band_volume_km3(z0, z1, shell_m=None):
    """Solid-of-revolution volume of the envelope over [z0, z1), in km³.

    Frustum rule over the 1,978 profile samples -- exact for a
    linearly-interpolated profile, which is what the profile IS, and 18 ms.
    With `shell_m` it integrates the SHELL of that thickness instead, which is
    how `hull_skin` is defined (`interior.HULL_SKIN_M`).
    """
    pr = _profile()
    tot = 0.0
    for a, b in zip(pr, pr[1:]):
        za, ra = a["z_m"], a["radius_m"]
        zb, rb = b["z_m"], b["radius_m"]
        if zb <= z0 or za >= z1:
            continue
        h = zb - za

        def area(r):
            if shell_m is None:
                return math.pi * r * r
            return math.pi * (r * r - max(r - shell_m, 0.0) ** 2)
        fa, fb = area(ra), area(rb)
        tot += h * (fa + fb + math.sqrt(max(fa, 0.0) * max(fb, 0.0))) / 3.0
    return tot / 1e9


def _features():
    """Longitudinal feature id -> (z0, z1), subfeatures included."""
    if "feat" not in _CACHE:
        import sys                                               # noqa: PLC0415
        sys.path.insert(0, os.path.join(ROOT, "station"))
        import interior as IT                                    # noqa: PLC0415
        schema, _p = IT.load()
        out = {}
        for f in schema["longitudinal"]["features"]:
            out[f["id"]] = (float(f["z0"]), float(f["z1"]))
            for s in f.get("subfeatures") or ():
                out[s["id"]] = (float(s["z0"]), float(s["z1"]))
        _CACHE["feat"] = out
    return _CACHE["feat"]


def _src(path):
    if ("src", path) not in _CACHE:
        try:
            _CACHE[("src", path)] = open(os.path.join(ROOT, path),
                                         encoding="utf-8").read()
        except OSError:
            _CACHE[("src", path)] = ""
    return _CACHE[("src", path)]


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------
def _near(got, want, frac=0.05):
    return abs(got - want) <= abs(want) * frac


def _claim_anchor(cells):
    """Every PLC the row names resolves, and every feature id it names exists."""
    keys = _plc_keys()
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    bad, seen = [], []
    row = " ".join(cells)
    for n in sorted({int(x) for x in _PLC.findall(row)}):
        k = keys.get(n)
        if not k:
            bad.append("PLC-%03d names no place in PLACES.md" % n)
            continue
        try:
            DIR.by_key(k)
        except KeyError:
            bad.append("PLC-%03d `%s` is in no register row" % (n, k))
            continue
        seen.append("PLC-%03d=%s" % (n, k))
    feats = _features()
    for fid in sorted(set(re.findall(r"\b[a-z][a-z_]{4,}\b", cells[0]))):
        if fid in feats:
            seen.append("%s z%.0f-%.0f" % (fid, feats[fid][0], feats[fid][1]))
        elif fid in ("plant_zone", "fusion_core", "red_section",
                     "aft_hull_block", "bearing_neck"):
            bad.append("%s is named as a volume and the schema has no such "
                       "feature" % fid)
    if bad:
        return False, "; ".join(bad)
    return True, ", ".join(seen) or "no anchor named"


def _claim_stencil(rid, cells):
    """Does the row's verbatim stencil exist anywhere in the project?

    SHC-13 inverts it: its whole content is that it has NO stencil and no
    registry entry ("the ONE closure with no registry entry visible in-world";
    "SHC-13 alone answers LOOK with nothing at all"). So for that row a quoted
    stencil would be the failure.
    """
    if not _corpus_ok():
        return False, ("stencil corpus unreadable -- the control string %r is "
                       "not in it, so this says nothing about the station"
                       % _CONTROL)
    closure = cells[3] if len(cells) > 3 else ""
    quoted = list(_QUOTED.findall(closure))
    if rid == "SHC-13":
        if quoted:
            return False, ("SHC-13 must be UNSTENCILLED and the row quotes %d "
                           "stencil(s)" % len(quoted))
        return True, "correctly quotes no stencil"
    if not quoted:
        # SHC-02 is the one row that quotes none because it DELEGATES: "12
        # stencils cross-reffed to PLC-092", whose own CHECK is "all 12
        # stencils read distinct real reasons". So the claim is 12 distinct
        # LOOK strings on PLC-092's welded doors, which `interact.read_text` is
        # the authority for.
        if "PLC-092" in closure:
            return _stencils_092(closure)
        return False, "closure cell quotes no stencil to check"
    missing = [(q, _in_content(_norm(q))) for q in quoted]
    gone = [q for q, (ok, _w) in missing if not ok]
    if gone:
        return False, ("%d of %d stencil(s) are in no string literal in "
                       "station/, godot/ or tools/: %r"
                       % (len(gone), len(quoted), gone[0][:56]))
    return True, ("%d stencil(s) present verbatim (%s)"
                  % (len(quoted), missing[0][1][1]))


def _stencils_092(closure):
    """PLC-092's twelve welded-door stencils, as strings a player can read."""
    m = re.search(r"(\d+)\s+stencils", closure)
    want = int(m.group(1)) if m else 12
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    import interact as IA                                        # noqa: PLC0415
    key = _plc_keys().get(92)
    try:
        p = DIR.by_key(key)
    except KeyError:
        return False, "PLC-092 `%s` is in no register row" % key
    texts = {t: IA.read_text(key, t) for t in (p.get("interacts") or ())}
    live = {v for v in texts.values() if v}
    if len(live) < want:
        return False, ("%d stencils cross-reffed to PLC-092 `%s`; its %d "
                       "declared interactable(s) yield %d distinct LOOK "
                       "string(s)" % (want, key, len(texts), len(live)))
    return True, "%d distinct stencil strings on `%s`" % (len(live), key)


# --- per-row numbers -------------------------------------------------------
def _n_markab():
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    try:
        p = DIR.by_key("markab_quarter")
    except KeyError:
        return False, "the register has no `markab_quarter`"
    bad = []
    if "sealed_volume" not in (p.get("functions") or ()):
        bad.append("functions=%s carry no sealed_volume" % (p["functions"],))
    want = _plc_keys().get(23)
    if want not in (p.get("adjacent") or ()):
        bad.append("adjacent=%s does not include PLC-023 `%s`"
                   % (p.get("adjacent"), want))
    if bad:
        return False, "; ".join(bad)
    return True, ("markab_quarter sealed, adjoins %s, %.1f°x%.0f m"
                  % (want, p["footprint"][0], p["footprint"][1]))


def _n_bays_092():
    blk = _plc_block(92)
    m = _TILING.search(blk)
    if not m:
        return False, "PLC-092's row states no TILING total to compare 672 to"
    got = int(m.group(2).replace(",", ""))
    if got != 672:
        return False, ("SHC-02 says a 672-bay volume; PLC-092's TILING says %d"
                       % got)
    return True, "672 = PLC-092's own TILING total"


def _n_reserve():
    src = _src("station/plant.py") + _src("station/plant_systems.py")
    if "397,500" in src or "397500" in src:
        return True, "397,500 m3 is plant.py's own L-04 reserve figure"
    return False, ("397,500 m3 appears in neither plant.py nor "
                   "plant_systems.py")


def _n_plant_void():
    src = _src("station/plant.py")
    m = re.search(r"(\d{2,3}\.\d)\s*million m3", src)
    if not m:
        return False, "plant.py records no plant-zone volume to compare ~139 M m3 to"
    got = float(m.group(1))
    if not _near(got * 1e6, 139e6, 0.05):
        return False, ("SHC-05 says ~139 M m3; plant.py says %.1f M m3" % got)
    return True, "~139 M m3 against plant.py's %.1f M m3" % got


def _n_drum_800():
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    k = _plc_keys().get(29)
    try:
        p = DIR.by_key(k)
    except KeyError:
        return False, "PLC-029 `%s` is in no register row" % k
    axial = float(p["footprint"][1])
    if abs(axial - 800.0) > 1.0:
        return False, ("SHC-06 says an 800 m drum; PLC-029 `%s`'s footprint is "
                       "%.1f m axially" % (k, axial))
    return True, "PLC-029 `%s` is 800 m axially" % k


def _n_aft_flanks():
    """SHC-07's own two components against its own total, then the envelope.

    THE COMPONENTS DO NOT SUM AND THAT IS THE FINDING. 0.1273 + 0.1442 =
    0.2715, not 0.2785. `docs/volume-audit.md` §3.3 explains the 0.0070 km³
    difference -- it is Grey's band, which DOES deck the block out properly and
    is therefore not a flank -- so the total is the whole undescribed block and
    the parenthetical is the flanks only. Two different quantities under one
    number.
    """
    bad = []
    yellow, green, total = 0.1273, 0.1442, 0.2785
    if abs((yellow + green) - total) > 0.0005:
        bad.append("row's own arithmetic: Yellow %.4f + Green %.4f = %.4f, "
                   "row states %.4f (docs/volume-audit.md §3.3 attributes the "
                   "%.4f gap to Grey's decked band, which is not a flank)"
                   % (yellow, green, yellow + green, total,
                      total - yellow - green))
    z = _features().get("aft_hull_block")
    if not z:
        return False, "the schema has no aft_hull_block feature"
    env = _band_volume_km3(*z)
    if not _near(env, 0.7163, 0.02):
        bad.append("aft_hull_block envelope recomputes %.4f km3 against the "
                   "audit's 0.7163" % env)
    if bad:
        return False, "; ".join(bad)
    return True, "envelope %.4f km3 over z%.0f-%.0f" % (env, z[0], z[1])


def _n_bearing():
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import interior as IT                                        # noqa: PLC0415
    import transit as TR                                         # noqa: PLC0415
    z = _features().get("bearing_neck")
    if not z:
        return False, "the schema has no bearing_neck feature"
    schema, prof = IT.load()
    line = [x for x in TR.all_lines(schema, prof) if x["key"] == "spoke_lift"]
    if not line:
        return False, "transit has no spoke_lift line to read Green's stack top from"
    r = float(line[0]["r_outer_m"])
    if abs(r - 310.7) > 0.1:
        return False, ("SHC-08 says Green's stack ends at 310.7 m; the "
                       "outermost deck radius is %.3f m" % r)
    return True, ("bearing_neck z%.0f-%.0f, Green's stack ends %.3f m"
                  % (z[0], z[1], r))


def _n_skin():
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import interior as IT                                        # noqa: PLC0415
    got = _band_volume_km3(-1e9, 1e9, shell_m=IT.HULL_SKIN_M)
    if not _near(got, 0.0742, 0.05):
        return False, ("SHC-09 says 0.0742 km3 of hull skin; the %.1f m shell "
                       "over the profile integrates to %.4f km3"
                       % (IT.HULL_SKIN_M, got))
    return True, "0.0742 km3 against a recomputed %.4f km3" % got


def _n_spike():
    """The spike cap, and the 22 Blue places the row says stay live.

    22 IS NOT "22 OF THE BLUE PLACES" -- the register has 36 in Blue and every
    one of them is below 8,010. It is the 22 that sit inside the
    `forward_deflector_spike` band, which is the set the cap is actually about,
    and it recomputes exactly.
    """
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    z = _features().get("forward_deflector_spike")
    if not z:
        return False, "the schema has no forward_deflector_spike feature"
    if not (z[0] <= 8010.0 <= z[1]):
        return False, ("the cap is at z 8,010 and the spike runs z%.0f-%.0f"
                       % (z[0], z[1]))
    blue = [p for p in DIR.PLACES if p["sector"] == "blue"]
    inband = [p for p in blue if z[0] <= p["z_m"] < 8010.0]
    above = [p for p in DIR.PLACES if p["z_m"] >= 8010.0]
    bad = []
    if len(inband) != 22:
        bad.append("the row says 22 Blue places below 8,010; %d Blue places "
                   "sit in the spike band (%d in Blue altogether)"
                   % (len(inband), len(blue)))
    if above:
        bad.append("%d place(s) sit at or above the cap: %s"
                   % (len(above), ", ".join(p["key"] for p in above[:3])))
    if "forward_deflector_spike" not in _src("station/materials.py"):
        bad.append("materials.py does not name forward_deflector_spike, so it "
                   "cannot be declaring it uninhabited")
    if bad:
        return False, "; ".join(bad)
    return True, ("cap inside the spike z%.0f-%.0f, %d Blue places below it, "
                  "none above" % (z[0], z[1], len(inband)))


def _n_downbelow():
    """600 sealed + 145 open = 745, and 745 is the Downbelow row's own number."""
    if 600 + 145 != 745:                                         # pragma: no cover
        return False, "600 + 145 != 745"
    hits = [ln for ln in _places_md().splitlines()
            if "745 empty outer-ring cells" in ln]
    if not hits:
        return False, ("no PLC row in PLACES.md states the 745 empty "
                       "outer-ring cells SHC-11 seals 600 of")
    return True, "600 sealed + 145 open = 745, cross-stated by the Downbelow row"


def _n_red():
    z = _features().get("red_section")
    if not z:
        return False, "the schema has no red_section feature"
    env = _band_volume_km3(*z)
    if not _near(env, 0.1498, 0.05):
        return False, ("SHC-12 says a residual of 0.1498 km3; the red_section "
                       "envelope z%.0f-%.0f integrates to %.4f km3"
                       % (z[0], z[1], env))
    return True, ("red_section z%.0f-%.0f, envelope %.4f km3 against 0.1498"
                  % (z[0], z[1], env))


def _n_grey17():
    """SHC-13 claims an unnumbered inhabited level: built, seeded, undirectoried.

    "no directory row" is the row's own intent and is therefore NOT a failure.
    "interior built, population seeded" is a claim about content, and it is the
    one this can settle: a seeded population is residents somewhere, and
    nothing in `directory`, `npc/crowd` or `npc/schedule` holds a hidden Grey
    level.
    """
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    if not _corpus_ok():
        return False, "corpus unreadable, so absence proves nothing"
    named = [t for t in ("GREY 17", "GREY_17", "HIDDEN LEVEL", "HIDDEN_LEVEL")
             if _in_content(t)[0]]
    grey = sorted({p["deck"] for p in DIR.PLACES if p["sector"] == "grey"})
    if not named:
        return False, ("no interior and no seeded population: no string "
                       "literal in station/ or godot/ names one -- not a "
                       "directory place, not an npc/crowd.PlaceCrowd, not a "
                       "schedule row (grey decks in the register: %s)"
                       % ",".join(str(d) for d in grey[:8]))
    return True, "named in the project as %s" % ", ".join(named)


# rid -> (claim name, callable). Every entry is a number or an identity the
# row states and the model can be asked about in milliseconds.
_NUMBERS = {
    "SHC-01": ("markab quarter", _n_markab),
    "SHC-02": ("672 bays", _n_bays_092),
    "SHC-03": ("397,500 m3 reserve", _n_reserve),
    "SHC-04": (None, None),
    "SHC-05": ("~139 M m3", _n_plant_void),
    "SHC-06": ("800 m drum", _n_drum_800),
    "SHC-07": ("0.2785 = 0.1273 + 0.1442", _n_aft_flanks),
    "SHC-08": ("0.1084 km3 / 310.7 m", _n_bearing),
    "SHC-09": ("0.0742 km3", _n_skin),
    "SHC-10": ("z 8,010 cap / 22 Blue", _n_spike),
    "SHC-11": ("600 of 745", _n_downbelow),
    "SHC-12": ("0.1498 km3", _n_red),
    "SHC-13": ("built and seeded", _n_grey17),
}


def check(row):
    from spec_harness import spec_text                           # noqa: PLC0415
    rid = row.get("id", "")
    text = spec_text(row.get("at", ""), lines=1).strip()
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    m = _CELLS.match(text)
    if not m:
        return False, "not a table row: %r" % text[:60]
    cells = [c.strip() for c in m.group(1).split("|")]
    got_id = cells[0].strip().strip("*")
    want_id = "SHC-%02d" % int(rid.split("-")[1])
    if got_id != want_id:
        return False, ("registry %s points at a row headed %r" % (rid, got_id))
    if len(cells) < 5:
        return False, "%s has %d cells, expected 5" % (want_id, len(cells))

    results = [("anchor",) + _claim_anchor(cells),
               ("stencil",) + _claim_stencil(want_id, cells)]
    nm, fn = _NUMBERS.get(want_id, (None, None))
    if fn is not None:
        results.append((nm,) + fn())
    bad = [(n, note) for n, ok, note in results if not ok]
    good = [(n, note) for n, ok, note in results if ok]
    if bad:
        return False, "; ".join("%s: %s" % (n, t) for n, t in bad)
    return True, "; ".join("%s: %s" % (n, t) for n, t in good)


# ---------------------------------------------------------------------------
def _selftest(out=print):
    """Negative controls: prove each claim can go the other way.

    A harness whose only observed state is FAIL is as uninformative as one
    whose only observed state is PASS -- neither has been shown to discriminate.
    """
    rows = [{"id": "SHC-%03d" % n, "at": "docs/spec/PLACES.md:%d" % (2053 + n)}
            for n in range(1, 14)]
    fails = 0
    for r in rows:
        ok, note = check(r)
        fails += 0 if ok else 1
        out("%-8s %-4s %s" % (r["id"], "PASS" if ok else "FAIL", note[:160]))

    out("")
    out("-- negative controls --")
    body = _corpus()

    # 1. THE READER ITSELF. With the control string gone every stencil claim
    #    must say "unreadable", never "missing" -- the difference between "I
    #    cannot read this" and "this disagrees".
    _CACHE["corpus"] = [(p, t.replace(_CONTROL, "XXXX")) for p, t in body]
    ok, note = check(rows[2])
    out("corpus control removed -> %s: %s" % ("PASS" if ok else "FAIL", note[:110]))
    _CACHE["corpus"] = body

    # 2. THE CLAIM CAN GO THE OTHER WAY. Plant SHC-03's stencil in a fake file
    #    that really does declare it as a literal, and the row's stencil claim
    #    flips to present. Written to a temp path so `_literals` parses it for
    #    real rather than being told the answer.
    import tempfile                                              # noqa: PLC0415
    fd, tmp = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write('STENCIL = "POTABLE RESERVE - 30 DAY - ENTRY BY WATER '
                 'AUTHORITY PERMIT W-7 ONLY"\n')
    _CACHE["corpus"] = body + [(tmp, _norm(open(tmp, encoding="utf-8").read()))]
    ok, note = check(rows[2])
    out("SHC-03 stencil planted -> %s: %s" % ("PASS" if ok else "FAIL", note[:140]))
    _CACHE["corpus"] = body

    # 3. AND A COMMENT MUST NOT COUNT. Same string, same file, in a `#` line.
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write('# POTABLE RESERVE - 30 DAY - ENTRY BY WATER AUTHORITY '
                 'PERMIT W-7 ONLY\n')
    _CACHE.pop(("lit", tmp), None)
    _CACHE["corpus"] = body + [(tmp, _norm(open(tmp, encoding="utf-8").read()))]
    ok, note = check(rows[2])
    out("SHC-03 stencil in a COMMENT -> %s: %s"
        % ("PASS" if ok else "FAIL", note[:140]))
    _CACHE["corpus"] = body
    os.unlink(tmp)

    # And the number claim can fail on its own: bend the anchor.
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    p = DIR.by_key("markab_quarter")
    keep = p["adjacent"]
    p["adjacent"] = ()
    ok, note = _n_markab()
    out("markab adjacency cut -> %s: %s" % ("PASS" if ok else "FAIL", note[:140]))
    p["adjacent"] = keep
    ok, note = _n_markab()
    out("markab adjacency restored -> %s: %s"
        % ("PASS" if ok else "FAIL", note[:140]))

    # 5. The volume integral is a real measurement and must move when the
    #    quantity does: ask for a band that is not the one the row names.
    ok, note = _n_red()
    out("red_section as specified -> %s: %s" % ("PASS" if ok else "FAIL", note[:120]))
    keepf = _CACHE["feat"]["red_section"]
    _CACHE["feat"]["red_section"] = (6035.0, 6200.0)
    ok, note = _n_red()
    out("red_section band shortened -> %s: %s"
        % ("PASS" if ok else "FAIL", note[:120]))
    _CACHE["feat"]["red_section"] = keepf
    out("")
    out("%d of 13 SHC rows fail" % fails)
    return fails


if __name__ == "__main__":                                       # pragma: no cover
    import sys
    sys.path.insert(0, os.path.join(ROOT, "station"))
    _selftest()
