"""SUR rows: the nine surface programmes, against the filed scorecard.

WHY THIS FAMILY IS DIFFERENT FROM EVERY OTHER ONE HERE. A SUR row is a claim
about how the station LOOKS and SOUNDS, and no static check can settle that --
`docs/AAA-STANDARD.md` says so in its own words, and CLAUDE.md's rule is that
every craft claim cites an engine frame at the rubric's half distance. So
`SUFFICIENT = False`, and it is not close: SUR-02's verdicts are explicitly
*"filed by the NEXT session's reviewer, never the builder"*, and a harness that
promoted a row here would be the builder scoring themselves.

BUT TWO OF THE NINE ROWS QUOTE A NUMBER OUT OF A FILE THAT IS IN THE REPOSITORY,
and that number can be read. `docs/aaa-scorecard.json` is the panel's memory --
SUR-01 says so: *"per-kit craft scores in `docs/aaa-scorecard.json`"*, and
SUR-01's own check adds *"no kit regresses below 4 after any change (the
scorecard is the memory)"*. Reading a filed score against a stated bar is not
judging a frame; it is asking whether the judgement that HAS been filed says
what the row says it says. That is the whole of what this module claims to do.

WHAT IT FOUND, and all three are live:

  SUR-01  *"corridor (already 4)"* -- the filed scorecard has **no corridor
          entry at craft 4**. `interior_kit` 3, `concourse_central_corridor` 3,
          `walkable_deck` 3, and the generous reading (best of the three) is
          still 3. Of the five kits the row names, **two have no scorecard
          entry at all** -- there is no lift-interior row and no
          doorway-assembly row -- and **none of the three that exist is at the
          row's own bar of 4**.
  SUR-02  eight named rooms, **two of which (Earhart's, medlab_one) have no
          panel history at all**, and of the six that do the best craft is 3
          (`zocalo_interior`, `customs_arrival`, `garden_townscape`); `C&C` and
          `council_chamber` are at **1**. The row's bar is 4.
  SUR-05  its harness line names `tools/measure_frame.py --gate-frames
          --rerender`. **`measure_frame.py` has no such flags** -- running it
          exits 2 with *"unrecognized arguments: --gate-frames"*. Both flags
          belong to `tools/export_scene.py`. A harness line that names a
          command which cannot run is this project's oldest defect wearing a
          spec row's clothes, and it is caught by resolving the file and
          grepping it for the literal flag.

WHAT THIS MODULE DELIBERATELY DOES NOT DO. It does not fail SUR-07 on the
register carrying four places with an `observation`/`viewport` function against
the row's *"≥10 viewpoints"*, because a viewpoint is not defined anywhere as a
register row -- `obs_rotundas` is a class row that tiles to four rotundas by
itself. The count is REPORTED in the note and left for whoever defines the
term. Inventing a definition and then failing a row against it would be a
finding about this file.

BOTH DIRECTIONS WERE RUN. Filing craft 4 for all five of SUR-01's kits in a
patched copy of the scorecard turns the row GREEN with `5 of 5 kits at craft
>=4`, and resolving SUR-05's two flags against `tools/export_scene.py` -- the
tool that has them -- turns that row's failure off. Neither check is a
constant.

COST: 0.023 s for all nine rows in one process. It reads two files.

THE SHARED MACHINERY IS `spec_harness.sys`'s and is imported rather than copied:
the format law, the citation resolver, the id/INV/conflict references and the
tool-and-flag check are the same questions for both families, and two copies of
them would drift. (`spec_harness.sys` is this package's SYS module. The stdlib
`sys` is not involved and is not imported here.)
"""
import json
import os
import re
import sys as _stdlib                       # the real one; see the note above

# `station/` on the path BEFORE the sibling import, so this file can be run as
# well as imported. Through `spec_check.py` the path is already set; run
# directly it is not, and the `spec_harness` package hangs off `station/`.
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in _stdlib.path:                # pragma: no cover
    _stdlib.path.insert(0, os.path.dirname(_HERE))

from spec_harness.sys import (_FIELD, _HARNESS, _REQUIRED, _ROOT,  # noqa: E402
                              _count, _find_py, _flat, _ids_in, _num,
                              _registry_ids, check_tools)

SUFFICIENT = False

_INV = re.compile(r"\bINV-(\d+)(?:\.\.(\d+))?")

# WHICH FILED SUBSYSTEM ANSWERS FOR WHICH NAME THE ROW USES, and the mapping is
# declared rather than fuzzy-matched for one reason: a fuzzy matcher that found
# nothing would report "no panel history" for a row that has one, which is the
# expensive direction of the error. Where more than one filed subsystem could
# answer, ALL of them are listed and the BEST craft among them is taken -- the
# generous reading, so that a failure cannot be argued down to "you looked at
# the wrong entry".
_SUBJECT = {
    # SUR-01's five kits
    "corridor": ("interior_kit", "concourse_central_corridor",
                 "walkable_deck"),
    "lift interior": ("lift", "lift_interior"),
    "tram car": ("tram", "tram_car"),
    "doorway assembly": ("doorway_assembly", "door_assembly", "portal_frame"),
    "drum ground": ("drum_ground",),
    # SUR-02's eight landmarks
    "zocalo": ("zocalo_interior",),
    "customs hall": ("customs_arrival",),
    "council chamber": ("council_chamber",),
    "c&c": ("command_control",),
    "garden vista": ("garden_townscape", "drum_interior_engine"),
    "earhart's": ("earharts", "earhart"),
    "medlab_one": ("medlab_one", "medlab"),
    "a docking bay interior": ("docking_bay_interior",),
}

_CARD = None


def _scorecard():
    global _CARD
    if _CARD is None:
        with open(os.path.join(_ROOT, "docs", "aaa-scorecard.json"),
                  encoding="utf-8") as f:
            _CARD = json.load(f)
    return _CARD


def _craft(key):
    """(last filed craft, best ever filed) for a subsystem, or (None, None).

    Both, because SUR-01's check is two claims: a bar (`craft >=4`) and a
    ratchet (`no kit regresses below 4 after any change`). The ratchet can only
    be asked of a subsystem whose history is in the file, which is exactly what
    the row means by "the scorecard is the memory".
    """
    subs = _scorecard().get("subsystems", {})
    if key not in subs:
        return None, None
    rounds = subs[key].get("rounds") or []
    got = [r.get("scores", {}).get("craft") for r in rounds]
    got = [g for g in got if isinstance(g, int)]
    if not got:
        return None, None
    return got[-1], max(got)


def _subjects(t, bad, what):
    """The list of things the row's State field names, before its em-dash.

    Both SUR-01 and SUR-02 write the same shape -- a comma list, then an
    em-dash, then what the list IS ("per-kit craft scores in ...", "eight named
    rooms, panel history per room"). Parsed from the row rather than restated
    here so the harness cannot drift from the row it checks.
    """
    m = re.search(r"\*\*State:\*\*(.+?)—", t)
    if not m:
        bad.append("MALFORMED: cannot read the %s list out of the State field"
                   % what)
        return []
    out = []
    for part in m.group(1).split(","):
        part = re.sub(r"\([^)]*\)", " ", part)
        part = part.replace("*", "").strip().strip(".").strip()
        if part:
            out.append(part)
    return out


def _score_row(t, bad, note, what, count_pat):
    """The shared body of SUR-01 and SUR-02: a named set against a filed bar.

    The bar and the set size are BOTH read out of the row -- `craft >=4` and
    `The five kits` / `eight named rooms` -- so that raising or lowering either
    in the annex moves this check with it.
    """
    names = _subjects(t, bad, what)
    want_n = _count(t, count_pat, "the %s count" % what, bad)
    if want_n is not None and len(names) != want_n:
        bad.append("the row says %d %s and its State field lists %d (%s)"
                   % (want_n, what, len(names), names))
    bar = _num(t, r"craft ≥\s*(\d)", "the craft bar", bad)
    if bar is None:
        return
    unmapped, missing, under, ok = [], [], [], []
    for n in names:
        keys = _SUBJECT.get(n.lower())
        if keys is None:
            unmapped.append(n)
            continue
        best, ever = None, None
        for k in keys:
            last, mx = _craft(k)
            if last is not None and (best is None or last > best):
                best, ever = last, mx
        if best is None:
            missing.append(n)
        elif best < bar:
            under.append("%s %d" % (n, best))
        else:
            ok.append("%s %d" % (n, best))
        if ever is not None and best is not None and ever > best:
            bad.append("%s has REGRESSED: the scorecard's memory holds craft "
                       "%d and its last round is %d" % (n, ever, best))
    if unmapped:
        bad.append("MALFORMED: %s name(s) this harness cannot map to a "
                   "scorecard subsystem: %s" % (what, unmapped))
    if missing:
        bad.append("no panel history filed at all for %s" % missing)
    if under:
        bad.append("below the row's own bar of craft %d: %s" % (bar, under))
    note.append("%d of %d %s at craft >=%d (%s)"
                % (len(ok), len(names), what, bar, ok or "none"))


def _c_sur01(t, bad, note):
    _score_row(t, bad, note, "kits", r"The (\w+) kits")


def _c_sur02(t, bad, note):
    _score_row(t, bad, note, "rooms", r"(\w+) named rooms")


def _c_sur03(t, bad, note):
    """The hull union counts itself, and the manifest says how far it is."""
    import traffic as tr                                        # noqa: PLC0415
    want = _count(t, r"— (\w+) hulls plus the Starfury", "the hull count", bad)
    m = re.search(r"checks name\*\*:(.+?)—", t)
    if not m:
        bad.append("MALFORMED: cannot read the hull union out of the row")
        return
    items = [x.strip() for x in m.group(1).split("·") if x.strip()]
    leaves = sum(len(x.split("+")) for x in items)
    if want is not None and leaves != want:
        bad.append("the row says %d hulls and its own union lists %d (%s)"
                   % (want, leaves, items))
    sf = _find_py("starfury_geometry.py")
    if sf is None:
        bad.append("the row says the Starfury is the only hull geometry and "
                   "there is no starfury_geometry.py")
    note.append("%d hulls named against %d manifest ship classes; ONE hull "
                "generator exists (starfury_geometry.py) and the asset union "
                "assert is tool-to-build, so nothing here checks the other %d"
                % (leaves, len(tr.MANIFEST), leaves))


def _c_sur04(t, bad, note):
    """The two flight numbers, against the filed run they came out of.

    A pilot run is not a smoke-tier check and this does not attempt one. What
    it does is refuse to let the row quote a speed no filed artefact carries:
    `docs/starfury-flight.md` is the run report, and the numbers in the row are
    its numbers.
    """
    v = _num(t, r"mains ([\d.]+) m/s", "the mains speed", bad)
    k = _num(t, r"kill-velocity ([\d.]+) m/s", "the kill velocity", bad)
    path = os.path.join(_ROOT, "docs", "starfury-flight.md")
    if not os.path.exists(path):
        bad.append("quotes flight numbers and docs/starfury-flight.md, the "
                   "filed run they come from, does not exist")
        return
    rep = open(path, encoding="utf-8").read()
    for val, name in ((v, "mains"), (k, "kill-velocity")):
        if val is None:
            continue
        if not re.search(r"\b%s\b" % re.escape("%g" % val), rep):
            bad.append("%s: the row quotes %g m/s and docs/starfury-flight.md "
                       "does not carry that figure" % (name, val))
    note.append("mains %g m/s and kill-velocity %g m/s both appear in the "
                "filed run; the shipped-build pilot cycle is tool-to-build"
                % (v or 0, k or 0))


def _c_sur05(t, bad, note):
    n = _num(t, r"\((\d+)/(\d+) today\)", "the lighting window score", bad)
    if n is not None:
        note.append("the row states %d of %d rooms in window -- a measurement "
                    "over committed frames, which is the render tier and is "
                    "NOT checked here" % (n[0], n[1]))


def _c_sur06(t, bad, note):
    m = re.search(r"Event→sound table[^:]*:\*\*(.+?)\*\*Check", t)
    if not m:
        bad.append("MALFORMED: cannot read the event→sound table out of the "
                   "row")
        return
    rows = [x.strip() for x in m.group(1).split("·") if x.strip()]
    if len(rows) < 2:
        bad.append("the event→sound table enumerates %d emitters" % len(rows))
    note.append("%d enumerated emitters; whether each SOUNDS is an in-engine "
                "capture and is not checked here" % len(rows))


def _c_sur07(t, bad, note):
    """The viewpoint count is REPORTED, not asserted -- see the header."""
    import directory as dr                                      # noqa: PLC0415
    want = _num(t, r"≥(\d+) viewpoints", "the viewpoint floor", bad)
    n = sum(1 for p in dr.PLACES
            if {"observation", "viewport"} & set(p.get("functions") or ()))
    note.append("the row asks for >=%g viewpoints; %d register places carry an "
                "observation/viewport function, but a viewpoint is nowhere "
                "defined as a register row (obs_rotundas is a class row for "
                "four), so this is reported and NOT asserted" % (want or 0, n))


def _c_sur08(t, bad, note):
    """`body.py --silhouette` is named as an existing gate; it must be one."""
    note.append("the silhouette gate and the wardrobe module both resolve; "
                "per-role work loops and the LOD chain are render-tier")


def _c_sur09(t, bad, note):
    note.append("NO CONTENT CLAIM: no UI panel exists in the project, so every "
                "claim in this row is a state-diff against a screen that is "
                "not built")


CLAIMS = {
    "SUR-001": _c_sur01, "SUR-002": _c_sur02, "SUR-003": _c_sur03,
    "SUR-004": _c_sur04, "SUR-005": _c_sur05, "SUR-006": _c_sur06,
    "SUR-007": _c_sur07, "SUR-008": _c_sur08, "SUR-009": _c_sur09,
}


def check(row):
    from spec_harness import spec_text                          # noqa: PLC0415
    rid = row.get("id", "")
    raw = spec_text(row.get("at", ""), lines=140)
    if not raw:
        return False, "cannot read the row's own text from %r" % row.get("at")
    head = raw.splitlines()[0].strip()
    if not re.match(r"^#+\s*SUR-\d+", head):
        return False, "%s: the heading at %s is %r, which is not a SUR row" % (
            rid, row.get("at"), head[:60])
    t = _flat(raw)
    bad, note = [], []

    # -- the annex's own format law, which binds SUR as well as SYS --------
    labels = {m.group("lab").strip().lower() for m in _FIELD.finditer(raw)}
    miss = [f for f in _REQUIRED if f not in labels]
    if miss:
        bad.append("format law: no %s field (has %s)"
                   % (", ".join(miss), sorted(labels)))
    if not _HARNESS.search(raw):
        bad.append("format law: no harness line")

    # -- every id, invention and file the row names ------------------------
    reg = _registry_ids()
    dangling = sorted({i for i in _ids_in(t) if i != rid and i not in reg
                       and not i.startswith("INC-")})
    if dangling:
        bad.append("couples to %s, which the registry has no row for" % dangling)
    inv = None
    for m in _INV.finditer(t):
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if inv is None:
            inv = open(os.path.join(_ROOT, "canon", "INVENTIONS.md"),
                       encoding="utf-8").read()
        for k in range(lo, hi + 1):
            if "INV-%03d" % k not in inv:
                bad.append("names INV-%03d and canon/INVENTIONS.md has no such "
                           "entry" % k)
    check_tools(t, bad, note)

    fn = CLAIMS.get(rid)
    if fn is not None:
        fn(t, bad, note)
    else:
        note.append("NO CONTENT CLAIM for this row")

    if bad:
        return False, "%s: %s" % (rid, "; ".join(bad))
    return True, "%s: %s" % (rid, "; ".join(note) if note else "address only")


# ===========================================================================
# The controls. Same two halves as `sys.py`: corrupt the ROW in a copy of the
# annex, and corrupt the FILED ARTEFACT the row points at. The second half is
# the one that matters here, because a scorecard reader that returned the same
# answer whatever the scorecard said would be indistinguishable from a
# hard-coded verdict.
# ===========================================================================

# Each control is a LIST of (find, replace) pairs, because two of them need
# more than one edit to be honest. Lowering SUR-02's bar to 1 on its own does
# NOT turn the row green -- Earhart's and medlab_one have no panel history at
# any bar -- and a control that half-moved would have been recorded as dead.
# The bar is edited in the HEADING, which is where the row states it first and
# therefore where `craft ≥(\d)` reads it.
_SPEC_CONTROLS = (
    # The rows that FAIL on the live repository, corrected: the harness must
    # stop failing when the disagreement goes away.
    ("bar+set", "SUR-001",
     (("The five kits at craft ≥4", "The three kits at craft ≥3"),
      ("corridor (already 4), lift interior, tram car, doorway assembly, "
       "drum ground —", "corridor (already 4), tram car, drum ground —")),
     True),
    ("bar+set", "SUR-002",
     (("The landmark set at craft ≥4", "The landmark set at craft ≥1"),
      ("Earhart's,\nmedlab_one, a docking bay interior — eight named rooms",
       "a docking bay interior — six named rooms")),
     True),
    # And the harness line pointed at the tool that HAS those two flags,
    # which is also the proposed fix.
    ("harness", "SUR-005",
     (("tools/measure_frame.py --gate-frames --rerender",
       "tools/export_scene.py --gate-frames --rerender"),), True),
    # The rows that pass, broken.
    ("count", "SUR-001", ((", lift interior", ", lift interior, lift exterior"),
                          ), False),
    ("hulls", "SUR-003", (("— ten hulls plus the Starfury",
                           "— eleven hulls plus the Starfury"),), False),
    ("flight", "SUR-004", (("mains 55.14 m/s", "mains 55.99 m/s"),), False),
    ("reference", "SUR-006", (("(PLC-014)", "(PLC-914)"),), False),
    ("invention", "SUR-006", (("(INV-260..264", "(INV-260..999"),), False),
    ("file", "SUR-008", (("`body.py --silhouette`", "`body.py --silhouettes`"),
                         ), False),
)


def _code_controls():
    card = _scorecard()
    import copy                                                 # noqa: PLC0415
    orig = copy.deepcopy(card)

    def _all_four():
        """File craft 4 for every kit SUR-01 names, including the two that
        have no entry at all. The row must go from FAIL to PASS."""
        subs = card["subsystems"]
        for k in ("interior_kit", "tram", "drum_ground"):
            for r in subs[k]["rounds"]:
                r.setdefault("scores", {})["craft"] = 4
        for k in ("lift_interior", "doorway_assembly"):
            subs[k] = {"rounds": [{"scores": {"craft": 4}}]}

    def _restore():
        card.clear()
        card.update(copy.deepcopy(orig))

    return (("aaa-scorecard.json: all five kits filed at craft 4", "SUR-001",
             _all_four, _restore, True),)


def _selftest(out=print):                                    # pragma: no cover
    import tempfile
    from spec_harness.sys import _rows                        # noqa: PLC0415
    rows = _rows("SUR")
    out("THE NINE SURFACE PROGRAMMES -- docs/spec/SYSTEMS.md SUR against "
        "the filed scorecard")
    npass = 0
    for row in rows:
        ok, note = check(row)
        npass += ok
        out("  %s %s" % ("PASS" if ok else "FAIL", note[:200]))
    out("  -- %d of %d rows agree with what is filed" % (npass, len(rows)))

    base = open(os.path.join(_ROOT, "docs/spec/SYSTEMS.md"),
                encoding="utf-8").read()
    at_of = {r["id"]: r["at"] for r in rows}
    tmp = os.path.join(tempfile.mkdtemp(prefix="sur-controls-"), "SYSTEMS.md")
    dead = []
    out("\nSPEC-SIDE CONTROLS")
    for label, rid, pairs, want_pass in _SPEC_CONTROLS:
        body, bust = base, False
        for old, new in pairs:
            if body.count(old) != 1:
                dead.append("%s: its anchor %r appears %d times in the annex"
                            % (label, old, body.count(old)))
                bust = True
                break
            body = body.replace(old, new)
        if bust:
            continue
        open(tmp, "w", encoding="utf-8").write(body)
        ok, note = check({"id": rid, "at": "%s:%s"
                          % (tmp, at_of[rid].split(":")[1])})
        fired = ok if want_pass else (not ok)
        out("  %-10s %s %-14s %s" % (label, rid,
                                     "MOVES" if fired else "DOES NOT MOVE",
                                     note[:110]))
        if not fired:
            dead.append("%s on %s did not move the answer" % (label, rid))

    out("\nARTEFACT-SIDE CONTROLS -- the filed scorecard itself")
    for label, rid, patch, unpatch, want_pass in _code_controls():
        row = {"id": rid, "at": at_of[rid]}
        before = check(row)[0]
        patch()
        try:
            after = check(row)
        finally:
            unpatch()
        fired = after[0] if want_pass else (before and not after[0])
        out("  %s %-46s %s" % (rid, label[:46], "FIRES" if fired else "DEAD"))
        out("      %s" % after[1][:150])
        if not fired:
            dead.append("%s: %s did not move the answer" % (rid, label))
    for d in dead:
        out("  DEAD CONTROL %s" % d)
    n = len(_SPEC_CONTROLS) + len(_code_controls())
    out("\n%d of %d controls move the answer" % (n - len(dead), n))
    return not dead


if __name__ == "__main__":                                   # pragma: no cover
    _stdlib.exit(0 if _selftest() else 1)
