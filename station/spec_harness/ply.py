"""PLY-001..008: the player chapters, against what the project actually has.

THESE EIGHT ROWS ARE DIFFERENT FROM EVERY OTHER FAMILY AND THE DIFFERENCE
DECIDES WHAT THIS FILE CAN BE. A PLC row describes a place, an SHB row is a
sum, a GDS row is a table -- all three have a subject that exists offline. A
PLY row describes **something a person does over time**: arrive and be
processed, sleep and wake at 05:15, buy a coat and be read differently in
Downbelow, learn a name and find it in a journal. Not one of those is decidable
without a running game, and `--smoke` is by definition a tier with no engine in
it. So the honest scope is stated once, here:

    A PLY claim asks whether the MACHINERY the row names exists, is reachable
    from Python, and carries the specific numbers the row quotes. It never
    claims the chapter is playable.

`SUFFICIENT = False`, and unlike the other families that is not a formality --
it is the whole verdict. Even a row where every claim passes has only been
shown to have its parts; THE-STATION Sec 2b's own words for these rows are "these
eight rows put a person in it", and a person in it is exactly what a static
scan cannot see. This project has been burned nine times by machinery that
exists and is never called, and every one of those nine would pass a
machinery-exists check.

WHAT THAT SCOPE STILL CATCHES, and it is more than it sounds:

  * A NUMBER THE ROW QUOTES THAT THE CODE DISAGREES WITH. PLY-01 says a
    ten-station customs pipeline and a nine-field card; `arrival.checks()` and
    `npc/resident.CARD` are both countable. PLY-03 quotes a rent ladder of
    4-8 / 10-15 / hotel-business; `economy.LADDER` has rows for two of those
    three. PLY-08 quotes a 6,544-line floor; `dialogue.py` carries floors.
  * A NAMED MODULE THAT DOES NOT EXIST, or exists and cannot do the thing the
    row hangs on it. PLY-04's whole mechanic is "what the player wears is the
    marked-out input" and `npc/security.hostility` takes `(place_key, hour)`;
    there is no clothing parameter to read.
  * A ROW WHOSE SUBJECT IS ABSENT ENTIRELY -- no condition model (PLY-06), no
    journal (PLY-07), no `player_placements` save class (PLY-03). Those come
    back RED with the string that was searched for, which is a more useful RED
    than "not implemented".

THE SEARCH NEEDS A POSITIVE CONTROL, for `shc.py`'s reason one level down: a
corpus reader that silently read nothing would report every subject absent and
look exactly like a finding. `_corpus()` proves itself against `ROLE_WEIGHTS`,
which is certainly in the tree, and every absence claim says so before it says
"absent". `station/spec_harness/` is excluded -- a harness may not be its own
evidence, and this file names all of the strings it looks for.
"""
import os
import re

SUFFICIENT = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}

_CONTROL = "ROLE_WEIGHTS"
_PLC_KEYLINE = re.compile(r"^#+\s*PLC-(\d+)\s*`([a-z0-9_]+)`")
_PLC_REF = re.compile(r"PLC-(\d+)")


# ---------------------------------------------------------------------------
def _flat(text):
    return re.sub(r"\s+", " ", text)


def _row_text(row):
    from spec_harness import spec_text                            # noqa: PLC0415
    return spec_text(row.get("at", ""), lines=60)


def _corpus():
    """[(path, source)] for every Python and GDScript file that could hold it."""
    if "corpus" in _CACHE:
        return _CACHE["corpus"]
    out = []
    for top in ("station", "godot", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(ROOT, top)):
            if ("__pycache__" in dp or os.sep + "scene" in dp
                    or "spec_harness" in dp):
                continue
            for f in fn:
                if not f.endswith((".py", ".gd", ".tscn")):
                    continue
                p = os.path.join(dp, f)
                try:
                    if os.path.getsize(p) > 4_000_000:
                        continue
                    out.append((p, _decomment(
                        open(p, encoding="utf-8",
                             errors="replace").read())))
                except OSError:                                   # noqa: PERF203
                    continue
    _CACHE["corpus"] = out
    return out


def _decomment(src):
    """Source with whole-line `#` comments removed.

    A COMMENT IS NOT CONTENT, and this file proved it the hard way: the third
    draft still passed PLY-06's condition-model claim because `interior.py`
    line 1946 contains the English word CONDITION in a comment about something
    else. `shc.py` learned the same thing one level down and answered it with
    `ast`; the cheap form is enough here because every needle below is an
    identifier rather than a word -- and the two that are not (`hunger`,
    `fatigue`) appear nowhere in the tree at all, in code OR comment.

    RESIDUAL RISK, STATED: docstrings survive this, so a module that discusses
    a subject in prose could still satisfy an absence claim. Any needle added
    here must be identifier-shaped for that reason.
    """
    return "\n".join("" if ln.lstrip().startswith("#") else ln
                      for ln in src.splitlines())


def _where(needle):
    """The first file containing `needle` AS A WHOLE IDENTIFIER, or ''.

    SUBSTRING SEARCH LIED TWICE IN THE FIRST DRAFT AND BOTH LIES WERE PASSES.
    `"CONDITION" in body` matched `CONDITIONAL = cq.TRANSIT` in `incident.py`
    and reported PLY-06's condition model as present; `"journal" in body`
    matched the word "journalism" in `broadcast.py` and reported PLY-07's
    journal as present. Both are the shape of defect this project keeps
    producing -- a check that cannot fail for the thing it is named after --
    and both were introduced by ME while writing the harness whose whole job is
    to catch them. Identifier boundaries, in both directions.
    """
    pat = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(needle))
    for p, body in _corpus():
        if pat.search(body):
            return os.path.relpath(p, ROOT)
    return ""


def _corpus_ok():
    return bool(_where(_CONTROL))


def _absent(name, *needles):
    """(ok, note) for "this subject is nowhere in the project".

    Always returns ok=False when the subject is missing -- the point is the
    note, which names what was searched for so the next session can either
    build it or correct the search.
    """
    if not _corpus_ok():
        return False, ("corpus unreadable (%r not found in it), so absence "
                       "proves nothing about %s" % (_CONTROL, name))
    hits = [(n, _where(n)) for n in needles]
    live = [(n, w) for n, w in hits if w]
    if not live:
        return False, ("%s exists nowhere in station/, godot/ or tools/ -- "
                       "searched for %s" % (name, ", ".join(repr(n) for n in
                                                            needles)))
    return True, "%s: %s in %s" % (name, live[0][0], live[0][1])


def _places_md():
    if "md" not in _CACHE:
        _CACHE["md"] = open(os.path.join(ROOT, "docs/spec/PLACES.md"),
                            encoding="utf-8").read()
    return _CACHE["md"]


def _people_md():
    if "people" not in _CACHE:
        _CACHE["people"] = open(os.path.join(ROOT, "docs/spec/PEOPLE.md"),
                                encoding="utf-8").read()
    return _CACHE["people"]


def _plc_keys():
    if "plc" not in _CACHE:
        out = {}
        for ln in _places_md().splitlines():
            m = _PLC_KEYLINE.match(ln.strip())
            if m:
                out[int(m.group(1))] = m.group(2)
        _CACHE["plc"] = out
    return _CACHE["plc"]


def _claim_anchors(text):
    """Every PLC the chapter names is a place the register carries."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                       # noqa: PLC0415
    keys, bad, seen = _plc_keys(), [], []
    for n in sorted({int(x) for x in _PLC_REF.findall(text)}):
        k = keys.get(n)
        if not k:
            bad.append("PLC-%03d names no place in PLACES.md" % n)
            continue
        try:
            DIR.by_key(k)
        except KeyError:
            bad.append("PLC-%03d `%s` is in no register row" % (n, k))
            continue
        seen.append(k)
    if bad:
        return False, "; ".join(bad)
    return True, ("%d anchor(s): %s" % (len(seen), ", ".join(seen))
                  if seen else "names no PLC anchor")


# ---------------------------------------------------------------------------
# per-chapter claims
# ---------------------------------------------------------------------------
def _ply01(text):
    """Arrival: the gate, the pipeline's length, the card's field count."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import arrival as AR                                          # noqa: PLC0415
    import npc.resident as RES                                    # noqa: PLC0415
    flat = _flat(text)
    out = []

    # the gate the row's own harness field names.
    cs = os.path.join(ROOT, "station/coldstart.py")
    src = open(cs, encoding="utf-8").read() if os.path.exists(cs) else ""
    if '"--g1"' not in src and "'--g1'" not in src:
        out.append((False, "coldstart.py declares no --g1 flag"))
    else:
        out.append((True, "coldstart.py --g1 exists (it launches Godot, so it "
                          "is NOT run in this tier)"))

    # `the full 10-station customs pipeline`
    m = re.search(r"(\d+)-station customs pipeline", flat)
    if not m:
        out.append((False, "the row quotes no pipeline length"))
    else:
        want = int(m.group(1))
        rows = AR.checks(_a_traveller(AR, RES))
        ns = sorted({r["n"] for r in rows})
        if max(ns) != want:
            out.append((False, "the row says a %d-station pipeline and "
                               "arrival.checks() numbers stations %s"
                        % (want, ns)))
        else:
            out.append((True, "arrival.checks() runs stations 1..%d" % max(ns)))

    # `the player's card renders all 9 fields`
    m = re.search(r"card renders all (\d+) fields", flat)
    if not m:
        out.append((False, "the row quotes no card field count"))
    else:
        want, got = int(m.group(1)), len(RES.CARD)
        if got != want:
            out.append((False, "the row says %d card fields and resident.CARD "
                               "has %d: %s" % (want, got, list(RES.CARD))))
        else:
            out.append((True, "resident.CARD is %d fields" % got))

    # the numbered unit the first night is spent in
    out.append(_absent("a numbered transient unit label",
                       "UNITS_PER_BLOCK", "unit_label"))
    return out


def _a_traveller(AR, RES):
    """One arriving person, built the way `arrival.py` itself builds them.

    `checks()` wants a player, not a card, and `arrival.sequence` gets one from
    `player.random_player`. Going through that same call means this cannot
    process a stand-in the real pipeline would never see -- and it is the one
    place in this file that runs game code rather than reading it, which is why
    it is one construction and not a loop over travellers.
    """
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import player as PL                                           # noqa: PLC0415
    return PL.random_player("spec-harness")


def _ply02(text):
    """The per-ROLE visa gating table: 12 rows, and the five EA-gated ones."""
    flat = _flat(text)
    body = _people_md()
    # PEOPLE.md writes `### ROLE-01 ...`, TWO digits, and the registry
    # canonicalises to three. Looking the body up by the canonical form found
    # nothing for all twelve rows and reported "12 ROLE rows name no card
    # state", which is the shape of failure this package calls a reader defect:
    # it is 100% on one side of a line, so it is structural, not twelve
    # authors each forgetting the same thing.
    roles = [(int(m.group(1)), m.group(0)) for m in
             re.finditer(r"(?m)^###\s+ROLE-(\d+)", body)]
    out = []
    if len(roles) != 12:
        out.append((False, "the row says 12 ROLE rows and PEOPLE.md defines %d"
                    % len(roles)))
    else:
        out.append((True, "12 ROLE rows defined"))

    # every ROLE row must name the card state it requires.
    # WORD BOUNDARIES, and the finding survived them -- which is the order
    # these two things must happen in. The loose form `card|cert` also matches
    # "concert" and "discard"; tightening it left exactly the same five rows
    # failing, so the number is about PEOPLE.md and not about the regex.
    want = re.compile(r"\b(?:visas?|sponsorship|(?:identi)?card(?:s|ed)?|"
                      r"certs?|EA[_ ]CITIZEN)\b", re.I)
    empty = []
    for n, head in roles:
        m = re.search(r"(?ms)^%s\b(.*?)(?=^###\s|\Z)" % re.escape(head), body)
        if not m or not want.search(m.group(1)):
            empty.append("ROLE-%02d" % n)
    if empty:
        # AND THE SHARPEST FORM OF IT: which of the roles THIS ROW calls
        # EA-gated are among the unfilled? A gate the annex names and the
        # annex does not define is the one case that is not merely a hole.
        gated_empty = [x for x in empty
                       if int(x.split("-")[1]) in (1, 2, 6, 11, 12)]
        out.append((False, "%d of %d ROLE row(s) name no card/visa state: %s%s"
                    % (len(empty), len(roles), ", ".join(empty),
                       ("" if not gated_empty else
                        " -- and %s is one PLY-02 itself names as EA-gated, so "
                        "the gate it says is \"normative NOW\" has no card "
                        "state to gate on" % ", ".join(gated_empty)))))
    else:
        out.append((True, "all %d ROLE rows name a card state" % len(roles)))

    # the five the row itself names as EA-gated must be among them.
    # `ROLE-01/02` is a LIST, and a plain `ROLE-(\d+)` reads the first and
    # drops the second -- the same slash-list trap the SHB totals cell has.
    named = set()
    for tok in re.findall(r"ROLE-([\d/]+)", flat):
        named |= {int(x) for x in tok.split("/") if x.isdigit()}
    named = sorted(named)
    m = re.search(r"the (\w+) a SANCTUARY-visa character cannot hold", flat)
    words = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
    if m and m.group(1).lower() in words:
        want_n = words[m.group(1).lower()]
        gated = [n for n in named if n in (1, 2, 6, 11, 12)]
        if len(gated) != want_n:
            out.append((False, "the row says %d EA-gated roles and names %d "
                               "of the gated set: %s"
                        % (want_n, len(gated), gated)))
        else:
            out.append((True, "%d EA-gated roles named: %s" % (want_n, gated)))

    # and the visa classes must be real states the pipeline can issue.
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import arrival as AR                                          # noqa: PLC0415
    miss = [v for v in ("SANCTUARY", "EA_CITIZEN")
            if not hasattr(AR, v)]
    if miss:
        out.append((False, "arrival.py has no %s visa constant"
                    % ", ".join(miss)))
    else:
        out.append((True, "arrival.SANCTUARY and arrival.EA_CITIZEN exist"))
    return out


def _ply03(text):
    """Quarters as home: the rent ladder's three tiers, and the save class."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import economy as EC                                          # noqa: PLC0415
    flat = _flat(text)
    out = []
    m = re.search(r"transient\s*(\d+)[–-](\d+)\s*cr/wk\s*→\s*civilian\s*"
                  r"(\d+)[–-](\d+)\s*→\s*([a-z/ ]+)", flat)
    if not m:
        out.append((False, "the rent ladder did not parse from the row"))
    else:
        t_lo, t_hi, c_lo, c_hi, top = (float(m.group(1)), float(m.group(2)),
                                       float(m.group(3)), float(m.group(4)),
                                       m.group(5).strip())
        bad = []
        for key, want in (("room_transient", (t_lo, t_hi)),
                          ("quarters_personnel", (c_lo, c_hi))):
            try:
                got = EC.ladder(key)
            except KeyError:
                bad.append("economy.py has no `%s` ladder row" % key)
                continue
            if tuple(got) != want:
                bad.append("the row prices %s at %g–%g and economy.%s is %g–%g"
                           % (key, want[0], want[1], key, got[0], got[1]))
        names = {r.key if hasattr(r, "key") else r[0] for r in EC.LADDER}
        if not any("hotel" in n or "business" in n for n in names):
            bad.append("the ladder's top tier is %r and economy.LADDER has no "
                       "hotel/business row (%s)" % (top, ", ".join(sorted(names))))
        if bad:
            out.append((False, "; ".join(bad)))
        else:
            out.append((True, "the three rent tiers resolve in economy.LADDER"))

    out.append(_absent("the SYS-13 `player_placements` save-delta class",
                       "player_placements", "PLAYER_PLACEMENTS"))
    out.append(_absent("a household-goods vendor",
                       "household_goods", "household-goods", "furnisher"))
    return out


def _ply04(text):
    """Wardrobe: the catalogue, the clothier's stall, and the reader of it."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import inspect                                                # noqa: PLC0415
    import npc.costume as CO                                      # noqa: PLC0415
    import npc.security as SE                                     # noqa: PLC0415
    flat = _flat(text)
    out = []
    if not getattr(CO, "ERA_EVENTS", None):
        out.append((False, "costume.py carries no era catalogue"))
    else:
        out.append((True, "costume.ERA_EVENTS has %d events at datum %s"
                    % (len(CO.ERA_EVENTS), CO.ERA_DATUM)))

    # `the named clothier among PLC-011's 44 stalls`
    m = re.search(r"PLC-(\d+)'s (\d+) stalls", flat)
    if m:
        n, want = int(m.group(1)), int(m.group(2))
        blk = re.search(r"^###\s+PLC-%03d\b(.*?)(?=^###\s|\Z)" % n,
                        _places_md(), re.M | re.S)
        got = re.search(r"\*\*(\d+) market stalls", _flat(blk.group(1))) if blk else None
        if not got:
            out.append((False, "PLC-%03d's row states no market-stall count "
                               "to check %d against" % (n, want)))
        elif int(got.group(1)) != want:
            out.append((False, "this row says PLC-%03d has %d stalls and that "
                               "row says %s" % (n, want, got.group(1))))
        else:
            out.append((True, "PLC-%03d carries the %d stalls this row cites"
                        % (n, want)))
    out.append(_absent("a named clothier", "clothier", "outfitter", "tailor",
                       "draper", "clothes_stall"))

    # THE MECHANIC ITSELF: does the contact model take what you wear?
    sig = inspect.signature(SE.hostility)
    params = list(sig.parameters)
    if not any(p in ("costume", "wearing", "clothing", "garb", "set_key")
               for p in params):
        out.append((False, "PLY-04's mechanic is \"what the player wears is "
                           "the marked-out input\" and security.hostility%s "
                           "takes no clothing argument -- the model reads "
                           "place and hour only" % sig))
    else:
        out.append((True, "security.hostility reads clothing: %s" % params))

    # INC-CONTACT, the event whose rate the row says clothing moves.
    import incident as IN                                         # noqa: PLC0415
    ids = {getattr(c, 'cid', None) or (c[0] if isinstance(c, tuple) else '')
           for c in IN.CLASSES}
    if "INC-CONTACT" not in ids:
        out.append((False, "the row cites INC-CONTACT and incident.py has no "
                           "such class"))
    else:
        out.append((True, "INC-CONTACT is one of incident.py's %d classes"
                    % len(ids)))
    return out


def _ply05(text):
    """SLEEP and WAIT: the verbs, the clock, and the muster it must make."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import interact as IA                                         # noqa: PLC0415
    out = []
    verbs = set(getattr(IA, "VERBS", {}))
    for want, why in (("rest", "SLEEP in any bunk/bed"),
                      ("sit", "WAIT on any sittable seat")):
        if want not in verbs:
            out.append((False, "interact.VERBS has no `%s` for \"%s\" (%s)"
                        % (want, why, ", ".join(sorted(verbs)))))
        else:
            out.append((True, "`%s` is one of interact.py's %d verbs"
                        % (want, len(verbs))))
    # TIME COMPRESSION IS EXERCISED, NOT SEARCHED FOR -- the same upgrade
    # `_ply06` made when the condition model landed, and for the reason its own
    # note gives: better needles fix a false POSITIVE and leave the deeper
    # problem, which is that the moment a symbol with one of those names
    # appears the search passes whatever that symbol does.
    #
    # PLY-05's requirement is the word THROUGH -- *"advance the station clock
    # at compressed rate through the running simulation: events still fire,
    # stocks still move, the world does not pause"*. So the checkable claim is
    # not that a compression knob exists, it is that a JUMP and a RUN are
    # DISTINGUISHABLE, which in this build they are in exactly one place:
    # `godot/scripts/life.gd`'s Director is deliberately pure in the hour and
    # reads identically after either, so the discrimination has to come from
    # something that accumulates.
    out += _compression_claims()
    # the row's own scenario numbers must be times the schedule can express.
    flat = _flat(text)
    for hh in re.findall(r"\b(\d{2}):(\d{2})\b", flat):
        h, mm = int(hh[0]), int(hh[1])
        if not (0 <= h < 24 and 0 <= mm < 60):
            out.append((False, "the row names an impossible clock time %s:%s"
                        % hh))
            break
    else:
        out.append((True, "every clock time in the row is a real station hour"))
    return out


def _ply06(text):
    """Needs: the five-state table, and the species windows it must read."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import npc.schedule as SC                                     # noqa: PLC0415
    out = []
    states = re.findall(r"^\|\s*([a-z—-]+)\s*\|", text, re.M)
    states = [s for s in states if s not in ("state", "---")]
    want = {"fed", "rested", "hungry", "tired"}
    got = {s for s in states if s in want}
    if got != want:
        out.append((False, "the row's effect table names %s and the ruling "
                           "enumerates %s" % (sorted(got), sorted(want))))
    else:
        out.append((True, "the effect table carries all four states plus the "
                          "closed `anything worse` row"))

    # "the species windows come from npc/schedule.py, not from a constant"
    miss = [s for s in ("human", "narn", "centauri", "minbari")
            if s not in getattr(SC, "RHYTHMS", {})]
    if miss:
        out.append((False, "npc/schedule.RHYTHMS has no rhythm for %s"
                    % ", ".join(miss)))
    else:
        n = len(SC.RHYTHMS)
        meals = {s: len(r.meals) for s, r in list(SC.RHYTHMS.items())[:3]}
        out.append((True, "schedule.RHYTHMS carries %d species' meal and sleep "
                          "windows (%s)" % (n, meals)))

    # THE CONDITION MODEL IS RUN, NOT SEARCHED FOR, and that is the upgrade
    # this row needed most. The previous version was `_absent("...", "hunger",
    # "fatigue", ...)` with a note explaining that the needles were picked so a
    # near-miss could not satisfy them -- an earlier draft had matched
    # `CONDITIONAL = cq.TRANSIT` in incident.py and reported a condition model
    # that did not exist. Better needles fix the false POSITIVE and leave the
    # deeper problem: the moment a file called `condition.py` appears with the
    # word "fatigue" in it, the search passes whatever that file does.
    #
    # PLY-06's CHECK is a whole-state diff -- "two station-days with no food and
    # no sleep produce EXACTLY the two declared penalties and nothing else,
    # asserted as a whole-state diff against a fed-and-rested control run, so an
    # undeclared effect fails" -- so this runs that diff and reads its shape.
    # A static scan can tell you a caller exists; only running the thing tells
    # you the caller runs.
    try:
        import condition as CD                                   # noqa: PLC0415
        kept = CD.run("human", 8.0, 2.0, feed=True, rest=True)
        starved = CD.run("human", 8.0, 2.0, feed=False, rest=False)
        diff = CD.whole_state_diff(kept, starved)
        fields = sorted({d[0].split(" ", 1)[1] for d in diff if " " in d[0]})
        declared = {"states", "warmth_band", "pay_bonus"}
        extra = sorted(set(fields) - declared)
        reached = {d[0].rsplit(" ", 1)[-1] for d in diff}
        out.append((bool(diff) and not extra,
                    "the two-day starved/fed whole-state diff is %d differences "
                    "over %s%s" % (len(diff), fields,
                                   "" if not extra else
                                   " -- UNDECLARED EFFECT %s" % extra)))
        out.append(("warmth_band" in reached and "pay_bonus" in reached,
                    "both declared penalties are reached by the starved run "
                    "(%s)" % sorted(reached & {"warmth_band", "pay_bonus"})))
        worst = CD.Condition("human", last_meal_h=0.0, last_sleep_h=0.0,
                             last_sleep_len_h=0.0)
        eff = worst.effects(1000.0)
        out.append((sorted(eff) == sorted(CD.DECLARED_EFFECT_KEYS)
                    and eff["warmth_band"] == -1 and eff["pay_bonus"] is False,
                    "41 days with no food and no sleep is still exactly %s -- "
                    "no damage, no spiral" % (eff,)))
        # THE WINDOWS COME FROM schedule.py, WHICH THE ROW REQUIRES BY NAME.
        # Checked by DISCRIMINATION rather than by import: two species whose
        # RHYTHMS differ must get different intervals, which a constant in the
        # condition model cannot produce.
        two = [sp for sp, r in SC.RHYTHMS.items() if len(r.meals) == 2]
        three = [sp for sp, r in SC.RHYTHMS.items() if len(r.meals) == 3]
        out.append((bool(two) and bool(three) and
                    CD.meal_interval_h(two[0]) > CD.meal_interval_h(three[0]),
                    "the meal interval tracks RHYTHMS: %s %.2f h against %s "
                    "%.2f h" % (two[0] if two else "-",
                                CD.meal_interval_h(two[0]) if two else 0.0,
                                three[0] if three else "-",
                                CD.meal_interval_h(three[0]) if three else 0.0)))
    except Exception as exc:                       # pragma: no cover - reported
        out.append((False, "the condition model does not run: %s: %s"
                    % (type(exc).__name__, exc)))
    return out


def _ply07(text):                                                # noqa: C901
    """The journal: RUN, with the row's own three entries and its own control.

    THE ROW'S CHECK IS EXECUTED HERE RATHER THAN LOOKED FOR. PLY-07 says:
    *"learn Delgado's name, the brooch tell, and one porter shortcut -- all
    three appear as journal entries whose text names the source event; a fact
    NOT learned is absent (the control); reload -- the journal is intact."*
    Three of those four clauses are decidable offline against
    `station/journal.py`, and the fourth -- the reload -- is decidable only in
    the engine, which is what `python3 station/journal.py --gate` is for and
    which this claim says plainly rather than pretending to cover.

    The previous version was three `_absent()` searches. They were correct when
    written and they are the wrong shape now, for the reason `_ply06` records
    one screen up: an absence search passes the moment a symbol of that name
    appears, whatever it does.
    """
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    out = []
    try:
        import journal as J                                       # noqa: PLC0415
    except Exception as exc:                                      # noqa: BLE001
        return [(False, "the journal does not import: %s: %s"
                 % (type(exc).__name__, exc))]

    # -- the vocabulary is SYS-16's, and the row's three entry types are in it
    want = {"name_given", "tell_learned", "route_time"}
    missing = sorted(want - set(J.KINDS))
    out.append((not missing,
                "SYS-16's kinds are %d and the three PLY-07 names are%s there "
                "(%s)" % (len(J.KINDS), "" if not missing else " NOT",
                          ", ".join(sorted(want)))))

    # -- the three entries, MINTED, each from its own real source ------------
    j = J.Journal()
    made = {}
    try:
        made["name_given"] = J.mint_name_given(
            j, {"group": "customs_north__npc_standing_0",
                "who": {"id": "res:ply07", "name": "Delgado, Ruth"}},
            "customs_north", 0, 5.67)
    except Exception as exc:                                      # noqa: BLE001
        out.append((False, "a name cannot be learned: %s" % exc))
    marks = J.faction_marks()
    if marks:
        k = "rangers_aboard" if "rangers_aboard" in marks else sorted(marks)[0]
        try:
            made["tell_learned"] = J.mint_tell_learned(j, k, marks[k],
                                                       "zocalo", 0, 19.0)
        except Exception as exc:                                  # noqa: BLE001
            out.append((False, "FAC-28's tell cannot be learned: %s" % exc))
    else:
        out.append((False, "npc/faction.py exposed no mark table, so there is "
                           "no brooch tell to learn"))
    rs = []
    try:
        rs = J.derived_routes()
    except Exception:                                             # noqa: BLE001
        pass
    if rs:
        try:
            made["route_time"] = J.mint_route_time(
                j, rs[0]["a"], rs[0]["b"], 0, 9.0,
                claimed_min=rs[0]["minutes"])
        except Exception as exc:                                  # noqa: BLE001
            out.append((False, "a porter shortcut cannot be learned: %s" % exc))
    else:
        out.append((False, "transit.py derived no route, so there is no "
                           "shortcut to time"))

    got = sorted(made)
    out.append((len(made) == 3,
                "all three of the row's entries are minted (%s)" % ", ".join(got)
                if len(made) == 3 else
                "only %d of the row's three entries mint (%s)"
                % (len(made), ", ".join(got) or "none")))

    # -- "whose text NAMES THE SOURCE EVENT" is the row's own wording --------
    unsourced = []
    for kind, fid in made.items():
        f = j.get(fid)
        if f is None or not f.source.strip() or f.source_kind == "":
            unsourced.append(kind)
    out.append((not unsourced,
                "each entry names its source event -- e.g. %r"
                % (j.get(made[got[0]]).source[:96] if got else "")
                if not unsourced else
                "these entries carry no source event: %s"
                % ", ".join(unsourced)))

    # -- THE ROW'S OWN CONTROL: "a fact NOT learned is absent" ---------------
    never = J.fact_id("name_given", "res:never", "dialogue", "res:never")
    out.append((not j.has(never),
                "a fact that was never learned is absent (%s)" % never[:8]))

    # -- and the refusals, because "minted ONLY by real events" is the rule --
    refused = 0
    for bad, why in (
            (lambda: J.mint_name_given(j, {"group": "g", "who": {}}, "x"),
             "an actor row with nobody in it"),
            (lambda: J.mint_incident_seen(j, {"who": "x", "place": "y"}),
             "an incident with no cid"),
            (lambda: J.mint_route_time(j, rs[0]["a"], rs[0]["b"], 0, 9.0,
                                       claimed_min=rs[0]["minutes"] + 10.0)
             if rs else J.mint_rumour(j, "", "x", "k"),
             "a route time transit.py contradicts")):
        try:
            bad()
        except J.Refused:                                         # noqa: PERF203
            refused += 1
        except Exception:                                         # noqa: BLE001
            pass
        del why
    out.append((refused == 3,
                "%d of 3 unsourced mints are REFUSED -- SYS-16's \"facts are "
                "minted ONLY by real events\" with teeth on it" % refused))

    # -- CAST-05's two stages, and the second is GIVEN ----------------------
    j.see("res:stranger")
    out.append((j.name_given("res:ply07") and not j.name_given("res:stranger"),
                "CAST-05's two stages are distinct: a face seen is not a name "
                "given"))

    # -- the reload, and this claim says what it CANNOT settle --------------
    st = j.state()
    back = J.Journal.from_state(st)
    intact = all(back.has(f) for f in made.values())
    out.append((intact and len(back) == len(j),
                "the journal round-trips %d facts, %d people and %d ledgers "
                "through its saved state -- the ENGINE reload is "
                "`python3 station/journal.py --gate` and no static tier can "
                "settle it" % (len(back), len(back.people),
                               len(back.standing))))
    return out


def _compression_claims():
    """PLY-05's compression, exercised: can a JUMP be told from a RUN?

    THE MACHINERY IS IN GDSCRIPT AND THIS TIER HAS NO ENGINE, so what is
    checked here is the pair of things a static tier CAN settle and which
    together decide whether the runtime's answer means anything:

      1. the discriminator exists in the shipped file and is reachable from the
         shipped path -- `journal.gd` is loaded by `main.gd::_start_journal`,
         not by a gate flag, which is this project's ninth-defect check;
      2. the thing it discriminates ON is real -- `broadcast.py` produces timed
         calls at hours, and the count in the slept window is what the runtime
         floor was derived from.

    What it does NOT claim is that the run passed. That is
    `python3 station/journal.py --gate`, and it is named in the note.
    """
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    out = []
    gd = os.path.join(ROOT, "godot", "scripts", "journal.gd")
    if not os.path.exists(gd):
        return [(False, "godot/scripts/journal.gd does not exist, so nothing "
                        "compresses time through anything")]
    src = open(gd, encoding="utf-8").read()
    for needle, why in (("_continuous", "the jump/run discriminator"),
                        ("_witness_span", "what a lived hour produces"),
                        ("SLEEP_H", "PLY-05's own 22:00 -> 05:15 window")):
        out.append((needle in src, "%s: `%s` is in journal.gd" % (why, needle)))

    # THE CALLER, AND IT MUST NOT BE A GATE. `tools/wiring.py` catches the
    # static form of this and MASTER-PLAN R6 gives the rule it cannot reach --
    # so the specific thing asserted is that the node is built in `_ready`'s
    # own path and not inside a `--journal-gate` branch.
    main = open(os.path.join(ROOT, "godot", "scripts", "main.gd"),
                encoding="utf-8").read()
    started = "_start_journal()" in main and "JOURNAL_SCRIPT" in main
    in_subjects = re.search(r'out\["journal"\]\s*=', main) is not None
    out.append((started and in_subjects,
                "journal.gd is instantiated by main.gd::_start_journal and "
                "offered to save.gd::_subjects -- so the compression runs on "
                "the shipped path rather than under a gate flag"
                if started and in_subjects else
                "journal.gd is NOT on main.gd's shipped path (started=%s, "
                "in _subjects=%s)" % (started, in_subjects)))

    # AND THE THING IT DISCRIMINATES ON IS REAL.
    try:
        import journal as J                                       # noqa: PLC0415
        calls = J.timed_calls(0)
        m = re.search(r"const SLEEP_H := ([0-9.]+)", src)
        window = float(m.group(1)) if m else 7.25
        rooms = ("customs_north", "arrival_concourse", "customs_south")
        here = [c for c in calls
                if any(r in c["places"] for r in rooms)]
        per_h = len(here) / 24.0
        out.append((len(here) > 0 and per_h * window >= 4.0,
                    "broadcast.py puts %d timed calls in the day, %d of them "
                    "audible on the boot deck -- %.1f in PLY-05's %.2f h "
                    "window, against journal.gd's floor of 4"
                    % (len(calls), len(here), per_h * window, window)))
    except Exception as exc:                                      # noqa: BLE001
        out.append((False, "broadcast.py produced no timed calls: %s: %s"
                    % (type(exc).__name__, exc)))
    return out


def _ply08(text):
    """Dialogue modality: the two modules, the line floor, the DLG-06 rule."""
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import audio as AU                                            # noqa: PLC0415
    import dialogue as DG                                         # noqa: PLC0415
    flat = _flat(text)
    out = [(True, "dialogue.py and audio.py both import (%d/%d public names)"
            % (len([n for n in dir(DG) if not n.startswith("_")]),
               len([n for n in dir(AU) if not n.startswith("_")])))]

    m = re.search(r"([\d,]+)-line floor", flat)
    if m:
        want = int(m.group(1).replace(",", ""))
        src = open(os.path.join(ROOT, "docs/spec/PEOPLE.md"),
                   encoding="utf-8").read()
        ms = re.search(r"Grand floor:([^\n]*?)=\s*([\d,]+) distinct lines", src)
        if not ms:
            out.append((False, "PEOPLE.md states no grand line floor to check "
                               "%d against" % want))
        else:
            got = int(ms.group(2).replace(",", ""))
            parts = [int(x.replace(",", ""))
                     for x in re.findall(r"[\d,]+", ms.group(1))]
            if got != want:
                out.append((False, "PLY-08 quotes a %s-line floor and DLG's "
                                   "grand floor is %s" % (m.group(1),
                                                          ms.group(2))))
            elif sum(parts) != got:
                out.append((False, "the grand floor's own components %s sum to "
                                   "%d, not %d" % (parts, sum(parts), got)))
            else:
                out.append((True, "the %s-line floor = DLG's own components %s"
                            % (m.group(1), parts)))

    # `no Brakiri personal name ever renders` -- DLG-06's office-designate rule
    if "brakiri" not in _flat(open(os.path.join(ROOT, "station/dialogue.py"),
                                  encoding="utf-8").read()).lower():
        out.append((False, "dialogue.py never mentions Brakiri, so DLG-06's "
                           "office-designate rule (no Brakiri personal name "
                           "ever renders) is enforced nowhere in it"))
    else:
        out.append((True, "dialogue.py knows about the Brakiri rule"))

    out.append(_absent("per-species phoneme beds over audio.py's voice layer",
                       "phoneme", "voice_bed", "VOICE_LAYER"))
    return out


_CHAPTERS = {1: _ply01, 2: _ply02, 3: _ply03, 4: _ply04,
             5: _ply05, 6: _ply06, 7: _ply07, 8: _ply08}


# ---------------------------------------------------------------------------
def check(row):
    rid = row.get("id", "")
    text = _row_text(row)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    head = text.splitlines()[0].strip()
    n = int(rid.split("-")[1])
    if "PLY-%02d" % n not in head:
        return False, ("the registry points %s at a heading reading %r"
                       % (rid, head[:60]))
    results = [("anchors",) + _claim_anchors(text)]
    fn = _CHAPTERS.get(n)
    if fn is None:
        return False, "no chapter claim written for %s" % rid
    for i, (ok, note) in enumerate(fn(text)):
        results.append(("c%d" % (i + 1), ok, note))
    bad = [(a, t) for a, ok, t in results if not ok]
    good = [(a, t) for a, ok, t in results if ok]
    if bad:
        return False, "; ".join(t for _a, t in bad)
    return True, ("every part PLY-%02d names exists [%s] -- and a chapter is a "
                  "thing a player DOES, which no static tier can settle"
                  % (n, "; ".join(t for _a, t in good)))


# ---------------------------------------------------------------------------
def _selftest(out=print):
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    at = {1: 147, 2: 159, 3: 172, 4: 185, 5: 198, 6: 209, 7: 235, 8: 245}
    fails = 0
    for n in range(1, 9):
        rid = "PLY-%03d" % n
        ok, note = check({"id": rid, "at": "docs/THE-STATION.md:%d" % at[n]})
        fails += 0 if ok else 1
        out("%-9s %-4s" % (rid, "PASS" if ok else "FAIL"))
        for part in note.split("; "):
            out("     " + part[:170])
    out("")
    out("%d of 8 PLY rows fail" % fails)

    out("")
    out("-- negative controls --")
    body = _corpus()

    # 1. THE READER. With the control string gone every absence claim must say
    #    "unreadable", never "absent".
    _CACHE["corpus"] = [(p, t.replace(_CONTROL, "XXXX")) for p, t in body]
    out("corpus control removed -> %s" % _absent("x", "brooch")[1][:120])
    _CACHE["corpus"] = body

    # 2. AN ABSENCE CLAIM CAN GO THE OTHER WAY. Plant the string PLY-07 looks
    #    for and watch the journal claim flip.
    import tempfile                                               # noqa: PLC0415
    fd, tmp = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("journal = {}\n")
    _CACHE["corpus"] = body + [(tmp, open(tmp, encoding="utf-8").read())]
    out("`journal` planted -> %s" % _absent("a journal", "journal",
                                            "JOURNAL")[1][:120])
    _CACHE["corpus"] = body
    os.unlink(tmp)

    # 3. A QUOTED NUMBER IS COMPARED, NOT ASSUMED: bend resident.CARD and the
    #    nine-field claim must move.
    import npc.resident as RES                                    # noqa: PLC0415
    keep = RES.CARD
    RES.CARD = tuple(RES.CARD)[:-1]
    ok, note = check({"id": "PLY-001", "at": "docs/THE-STATION.md:147"})
    out("resident.CARD cut to %d -> %s" % (len(RES.CARD),
                                           [t for t in note.split("; ")
                                            if "card field" in t][:1]))
    RES.CARD = keep

    # 4. and an economy number: move the transient rent band.
    import economy as EC                                          # noqa: PLC0415
    # `ladder()` reads LADDER_BY_KEY, not LADDER -- bending the tuple the
    # module derives from would have been a control that fires against
    # nothing, which is worse than no control.
    keepl = EC.LADDER_BY_KEY["room_transient"]
    EC.LADDER_BY_KEY["room_transient"] = (keepl[0], 5.0, 9.0) + keepl[3:]
    _ok, note = check({"id": "PLY-003", "at": "docs/THE-STATION.md:172"})
    hit = [t for t in note.split("; ") if "room_transient" in t]
    out("room_transient -> 5–9 cr  -> %s"
        % (hit[0][:130] if hit else
           "CONTROL DID NOT FIRE -- ladder() is not reading LADDER_BY_KEY"))
    EC.LADDER_BY_KEY["room_transient"] = keepl
    return fails


if __name__ == "__main__":                                        # pragma: no cover
    import sys
    sys.path.insert(0, os.path.join(ROOT, "station"))
    _selftest()
