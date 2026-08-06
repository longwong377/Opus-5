"""INC rows: the thirty incident CLASSES, against `station/incident.py`.

WHAT AN INC ROW IS. Every one of the thirty is a single line of SYS-14's
mechanics table in `docs/spec/SYSTEMS.md`, five columns wide:

    | INC-CONTRA | SYS-03 scan (P=0.01, x4 no-status) | passenger, scanner op,
      posted security | find -> seizure room (PLC-003) -> custody or fine |
      seizure log (item named per GDS-01), custody ledger, SYS-06 supply |

id, trigger, actors, escalation, writes. Four of those five say something a
harness can put a number against, and this module puts one against each:

  places      `Klass.places()` is non-empty and every key it returns is a live
              `directory.PLACES` row. A class that can happen nowhere is a
              class that never happens.
  escalation  the spec's beats against the class's own `beats` tuple, word for
              word and beat for beat. `incident.py`'s docstring says the tuple
              is "SYS-14's own beats, quoted in the row", so a word the row has
              and the tuple has not is drift by the module's own account.
  writes      THE STRONG ONE, and it is the only check here that runs the
              station's own code rather than reading it. Each phrase in the
              writes column maps to one of `incident.ALL_KINDS`; the class's
              real `resolve` is then run over a bounded grid of places, hours,
              casts and stances, and the kinds it actually produces are
              compared against the ones the row declares. It found a branch
              that cannot execute on the live station -- see INC-CONTRA below.
  references  every `PLC-`/`SYS-`/`FAC-`/`GDS-`/`PLY-`/`INC-` id named anywhere
              in the row resolves, against `docs/spec/completion.yaml` for the
              spec families and against `incident.BY_ID` for its own. The
              feeds-into links -- INC-ELEV's "INC-HOLD forms", INC-ACCIDENT's
              "(feeds INC-STRIKE)", INC-SICK's "INC-ARREARS' stopped-earner
              pool" -- are exactly these, and a renamed class breaks them.
  trigger     the parts of it that are facts rather than prose: a constant the
              column names with its value (`DOWNBELOW_CONTACT_PER_HOUR=1.5`,
              `VISA_EXPIRED_P=1/12`) is resolved in `incident` or a module
              `incident` imports and compared; a `<module>.py` the column names
              must be a module `incident` actually imports.
  actors      the part of it that is a fact rather than prose: a SPECIES named
              in the column (Drazi, Narn, Centauri, pak'ma'ra) must be declared
              by the class's cast AND be present in `audio.species_mix` of at
              least one place the class can happen in.

WHY `SUFFICIENT = False`, AND IT IS THE SPEC'S OWN ANSWER RATHER THAN MODESTY.
SYS-14 states the evidence that settles its table, four lines above the table
itself: *"one headless station-day at x1 logs the rate inside the probe volume;
one seeded incident replayed three ways -- player-absent / player-helps /
player-reports -- yields three world states that differ in NAMED facts"*. Both
are simulation-tier and neither runs here. The trigger column's RATE is the
central claim of an INC row and this module does not measure it: `Klass.rate`
is not called at all, because three of the thirty take 0.84 s, 2.2 s and 7.7 s
to evaluate ONCE (INC-SICK, INC-MOVEON, INC-BROWNOUT), which is the smoke
tier's whole budget for the family spent on one number. A GREEN here would
assert a rate this file never looked at.

WHAT IT COSTS, MEASURED, AND THE SHAPE OF THE NUMBER MATTERS MORE THAN ITS SIZE.
4.97 s for all thirty rows in one process -- 0.166 s a row amortised, inside the
smoke tier's bar. But it is not 0.166 s thirty times: **twenty-eight rows cost
one to two MILLISECONDS each** and two of them cost 2.75 s and 2.09 s, and which
two depends only on the order they are run in. The first row to reach
`security.presence_at` warms `interior.ring_radii` through
`navigation.cell_plan`; the first to reach `camp_places` warms
`security.squat_report`. Both are memoised station data, paid once per process.
So `spec_check.py --smoke` pays ~4.8 s for the family and `--id INC-PICK` alone
pays 4.85 s for one row -- the same work, not thirty times the work. Anyone
tempted to "optimise" this file should profile a WARM row first; there is
nothing in it to speed up.

THE PARSE, AND IT HAD TO BE MEASURED BEFORE IT COULD BE WIDENED. Four of the
thirty rows carry `{comply\\|resist\\|flee}` -- an ESCAPED pipe inside a cell of
a pipe-delimited table. Splitting on `|` reads those four rows as seven columns
and the naive harness reports them MALFORMED, which is the failure mode this
package exists to prevent: "I cannot read this" and "this disagrees" are
opposite findings and only one of them is about the station. Split on unescaped
pipes and all thirty rows are five columns.

AND THE ESCALATION COMPARISON IS AT THE GRANULARITY THE SPEC'S OWN NOTATION
USES, which was also measured rather than tuned. `->` separates beats, so the
BEAT COUNT is a claim and is asserted. Word ORDER inside one beat is not --
"a quiet word or a complaint" and "a complaint or a quiet word" are the same
beat, and requiring an ordered subsequence failed INC-NEIGHBOUR for that alone.
A PARENTHETICAL in this table is an annotation and not a beat: measured over the
thirty, every one of them is a cross-reference (`(PLC-003)`, `(feeds
INC-STRIKE)`), a rate for the simulation tier to settle (`(~15/day)`), or a note
on how to verify (`(audio-measurable)`). References are checked as references;
rates belong to the tier that can measure them. Numbers the row puts INSIDE a
beat are still required -- INC-LINER's "8.5 souls/min ~90 min" is checked.

WHAT IT FOUND -- and these are live failures, not a demonstration:

  INC-CONTRA  the row declares a "SYS-06 supply" write. The only `stock` write
              in `_res_contra` is `_stock(w, "black_market", item, +1)` in the
              branch where nobody responded -- and `_responded` is
              `response_s(place, hour) <= window_s`, which at BOTH customs halls
              at EVERY hour is 0.0, because an officer is standing in the room.
              The contraband-slips-through branch cannot execute on this
              station, so the declared write never lands. 72 resolutions.
  INC-BRAWL   the row's escalation ends "RESTRAIN arrests; victims resolve
              {comply|resist|flee} (SYS-05)"; the beats tuple stops at
              "RESTRAIN arrests" -- AND SO DOES THE CODE. `_res_brawl` books
              one or both parties and writes a casualty; there is no victim
              resolution in it, where INC-CONTACT's beat is literally "resolve
              comply|resist|flee" and `_res_contact` branches on it. This one
              is a missing behaviour, not a short string.
  INC-STRIKE  the row says `slowdown/"blue flu"` and "SYS-04 delivery ripple in
              days"; the beats say "slowdown" and "delivery ripple". Here the
              BEHAVIOUR is present -- `_res_strike` writes a work order reading
              "blue flu: muster thins 40%" and news reading "deliveries slip a
              day" -- and only the quoted beats are short. Worth stating,
              because the two failures read identically in the ledger and are
              not the same kind of thing.
  INC-NC      the row chains three beats ("stand-off, no yield" is one); the
              tuple has four. Segmentation only; every word is present.
"""
import re

SUFFICIENT = False

# A pipe INSIDE a cell is written `\|`. Four rows do it and they are the four
# with a {comply|resist|flee} resolution in them.
_SPLIT = re.compile(r"(?<!\\)\|")

# The families `docs/spec/completion.yaml` registers, plus INC itself. The
# registry zero-pads to three digits (`SYS-002`) and the prose does not
# (`SYS-02`, `GDS-01`), so the number is normalised before it is looked up.
# `SYS-03/05` and `SYS-02/10` name two systems in one token.
_ID = re.compile(r"\b(PLC|INC|SYS|FAC|GDS|PLY|SUR|ROLE|SHB|SHC|CAST|DLG|VRB)"
                 r"-([A-Za-z0-9]+(?:/\d+)*)")
_PAREN = re.compile(r"\([^)]*\)")
_CONST = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\s*=\s*"
                    r"([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+(?:\.[0-9]+)?)?)")
_MODPY = re.compile(r"\b([a-z_]+)\.py\b")

_STOP = frozenset("a an the of at in on to for and or is its it by with from "
                  "as into no not one two per".split())

# A write phrase -> the `incident.ALL_KINDS` delta it names. Longest key wins
# where two overlap, and a phrase that matches nothing is REPORTED as unmapped
# rather than silently dropped: "crime ledger", "district heat", "PA advisory"
# and "fixture states" are real writes this vocabulary cannot name, and a row
# whose whole writes column is unmapped (INC-DEBT) has that said in its note.
_WRITE_KW = (
    ("seizure", "seizure"), ("custody", "custody"), ("docket", "docket"),
    ("work order", "work_order"), ("work-order", "work_order"),
    ("standing", "standing"), ("card", "card"),
    ("stock", "stock"), ("inventory", "stock"), ("supply", "stock"),
    ("sales", "stock"), ("takings", "stock"),
    ("casualty", "casualty"), ("medlab", "casualty"), ("morgue", "casualty"),
    ("camp population", "camp"), ("camp state", "camp"),
    ("grievance", "grievance"), ("berth", "berth"), ("rumour", "rumour"),
    ("isn item", "news"), ("unsolved", "unsolved"),
)

# Species a row can name in its actors column, in the spelling the spec uses,
# against the key `audio.species_mix` and `npc/resident.py` use.
_SPECIES = {"drazi": "drazi", "narn": "narn", "centauri": "centauri",
            "pak'ma'ra": "pakmara", "minbari": "minbari", "brakiri": "brakiri",
            "vorlon": "vorlon", "gaim": "gaim", "llort": "llort",
            "abbai": "abbai", "hyach": "hyach"}

_REG_IDS = None
_MODS = None
_PLACE_KEYS = None


def _registry_ids():
    """Every id `docs/spec/completion.yaml` registers, read once.

    Read from the registry rather than restated here, for the same reason
    `spec_text` reads the row from the annex: a list of ids written in this
    file would be a second copy of the registry and would drift from it.
    """
    global _REG_IDS
    if _REG_IDS is None:
        import os                                            # noqa: PLC0415
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        path = os.path.join(root, "docs", "spec", "completion.yaml")
        ids = set()
        try:
            for ln in open(path, encoding="utf-8"):
                if re.match(r"^\s+- id: ", ln):
                    ids.add(ln.split("id:", 1)[1].strip())
        except OSError:                                      # pragma: no cover
            pass
        _REG_IDS = ids
    return _REG_IDS


def _modules():
    """The modules `incident.py` imports, by their bare name.

    Taken from `incident`'s own globals rather than from `sys.modules`, because
    the question the trigger column asks is "does incident.py read
    security.py", and `sys.modules` answers "did anything, anywhere, import
    it" -- which is true of half the repository once one gate has run.
    """
    global _MODS
    if _MODS is None:
        import types                                         # noqa: PLC0415
        import incident as inc                               # noqa: PLC0415
        out = {"incident": inc}
        for v in vars(inc).values():
            if isinstance(v, types.ModuleType):
                out[v.__name__.rsplit(".", 1)[-1]] = v
        _MODS = out
    return _MODS


def _place_keys():
    global _PLACE_KEYS
    if _PLACE_KEYS is None:
        import directory as dr                               # noqa: PLC0415
        _PLACE_KEYS = {p["key"] for p in dr.PLACES}
    return _PLACE_KEYS


def _norm_id(fam, num):
    if fam == "INC":
        return "INC-" + num.upper()
    try:
        return "%s-%03d" % (fam, int(num))
    except ValueError:                                       # pragma: no cover
        return "%s-%s" % (fam, num)


def _ids_in(text):
    out = []
    for m in _ID.finditer(text):
        for part in m.group(2).split("/"):
            out.append(_norm_id(m.group(1), part))
    return out


def _toks(s):
    """Content words, with spec ids removed -- they are checked as references."""
    s = _ID.sub(" ", s.replace("\\|", " "))
    out = []
    for w in re.findall(r"[a-z0-9'’./\-]+", s.lower()):
        w = w.strip("'’./-")
        if w and w not in _STOP:
            out.append(w)
    return out


def _cast_species(k):
    """The species literals the class's own cast lambda names.

    `inspect.getsource` on a lambda, and it is a SOURCE read rather than a run,
    which this file says out loud because the difference matters here: running
    `Klass.cast` goes through `resident.roster`, whose `affiliates` pool costs
    0.5-2.5 s per (place, hour, species) and is what makes `three_ways` a
    2.5 s call. The species a class casts is a literal in the table, so reading
    it is exact; nothing else about the cast is read this way.
    """
    import inspect                                           # noqa: PLC0415
    try:
        src = inspect.getsource(k.cast)
    except (OSError, TypeError):                             # pragma: no cover
        return []
    return re.findall(r"\"([a-z']+)\"", src)


def _cast_for(k, i):
    """A real cast of four `npc.resident.Resident`s, built directly.

    NOT `Klass.cast`, and the reason is the smoke tier's budget: `Klass.cast`
    draws from `resident.roster`, which builds an `affiliates` pool and costs
    up to 2.5 s per class. `resident.resident` is the SAME constructor that
    pool fills itself from and costs 0.1 ms, so these are real people with real
    roles, homes, visas and species -- only the SELECTION differs, and the
    selection is not what the writes column claims. Species come from the
    class's own cast declaration so that a Drazi brawl resolves with Drazi in
    it and a rung-dependent branch sees a plausible card.
    """
    from npc import resident as res                          # noqa: PLC0415
    sp = [s for s in _cast_species(k) if s in
          ("drazi", "narn", "centauri", "pakmara", "minbari", "brakiri",
           "human")]
    out = []
    for j in range(4):
        out.append(res.resident("spec-inc-%d-%d" % (i, j),
                                sp[j] if j < len(sp) else "human"))
    return out


def _observed_writes(k, want):
    """Run the class's REAL resolution and collect the delta kinds it produces.

    THE GRID IS OVER THE VARIABLES THE BRANCHES DEPEND ON, which had to be
    found rather than guessed. `_res_pick`'s `unsolved` branch needs a place
    where `response_s` is None -- `black_market`, the 20th of its 31 places, so
    a grid capped at "the first few places" reports a false drift.
    `_res_lockout`'s `camp` branch needs a person on a CONDITIONAL rung, which
    is a function of the cast's npc_id through `schedule.role_for`.
    `_res_stray`'s `casualty` branch needs a particular seed. So the grid is
    every place the class can happen in, four hours across the station clock,
    three casts and all three stances -- and it STOPS as soon as every declared
    kind has been seen, which is the first iteration for most rows.

    Returns (kinds, n_resolutions).
    """
    import incident as inc                                   # noqa: PLC0415
    got, n = set(), 0
    casts = [_cast_for(k, i) for i in range(3)]
    for place in k.places():
        for hour in (2.0, 8.0, 13.0, 19.0):
            for ci, cast in enumerate(casts):
                for st in inc.STANCES:
                    w = inc.World(day=1)
                    one = inc.Incident(k.cid, place, 1, hour, cast,
                                       k.window_s, "spec-inc-%d" % ci)
                    k.resolve(one, w, st)
                    got |= {f[0] for f in w.facts}
                    n += 1
            if want <= got:
                return got, n
        if want <= got:
            return got, n
    return got, n


def check(row):
    import incident as inc                                   # noqa: PLC0415
    from spec_harness import spec_text                       # noqa: PLC0415

    cid = row.get("id", "")
    line = spec_text(row.get("at", ""), lines=1).strip()
    if not line:
        return False, "cannot read the row's own text from %r" % row.get("at")
    cols = [c.strip() for c in _SPLIT.split(line)]
    while cols and not cols[0]:
        cols.pop(0)
    while cols and not cols[-1]:
        cols.pop()
    if len(cols) != 5:
        return False, ("%s: the row is %d columns, not 5 -- %r" %
                       (cid, len(cols), cols[:3]))
    got_id, trigger, actors, escalation, writes = cols
    if got_id != cid:
        return False, ("registry id %s points at a row whose first column is %r"
                       % (cid, got_id))

    k = inc.BY_ID.get(cid)
    if k is None:
        return False, ("the spec registers %s and incident.py has no class "
                       "for it (it has %d)" % (cid, len(inc.CLASSES)))

    bad = []

    # -- places -------------------------------------------------------------
    places = list(k.places())
    if not places:
        bad.append("the class can happen in no place at all")
    unknown = [p for p in places if p not in _place_keys()]
    if unknown:
        bad.append("places not in directory.PLACES: %s" % sorted(unknown)[:4])

    # -- escalation ---------------------------------------------------------
    spec_beats = [b for b in re.split(r"→|->", _PAREN.sub(" ", escalation))
                  if b.strip()]
    if len(spec_beats) != len(k.beats):
        bad.append("escalation chains %d beats, incident.py's tuple has %d "
                   "(spec %r vs code %r)"
                   % (len(spec_beats), len(k.beats),
                      [b.strip() for b in spec_beats], list(k.beats)))
    code_words = set(_toks(" ".join(k.beats)))
    missing = [w for w in _toks(_PAREN.sub(" ", escalation))
               if w not in code_words]
    if missing:
        bad.append("escalation drift: the row says %s and the beats tuple %r "
                   "carries none of that" % (sorted(set(missing)),
                                             list(k.beats)))

    # -- cross references, which is what the feeds-into links are -----------
    dangling = sorted({i for i in _ids_in(line)
                       if i != cid and i not in _registry_ids()
                       and i not in inc.BY_ID})
    if dangling:
        bad.append("names %s, which neither the registry nor incident.BY_ID "
                   "has" % dangling)

    # -- the checkable half of the trigger column ---------------------------
    mods = _modules()
    for m in _CONST.finditer(trigger):
        name, lit = m.group(1), m.group(2)
        if "/" in lit:
            a, b = lit.split("/")
            want_v = float(a) / float(b)
        else:
            want_v = float(lit)
        holders = [(n, getattr(mo, name)) for n, mo in sorted(mods.items())
                   if hasattr(mo, name)]
        if not holders:
            bad.append("trigger names %s=%s and no module incident.py imports "
                       "defines it" % (name, lit))
        else:
            hn, hv = holders[0]
            try:
                same = abs(float(hv) - want_v) <= 1e-9
            except (TypeError, ValueError):                  # pragma: no cover
                same = False
            if not same:
                bad.append("%s: spec=%s (%.6g), %s.py=%s"
                           % (name, lit, want_v, hn, hv))
    for m in _MODPY.finditer(trigger):
        if m.group(1) not in mods:
            bad.append("trigger names %s.py, which incident.py does not import"
                       % m.group(1))

    # -- the checkable half of the actors column ----------------------------
    import audio as aud                                      # noqa: PLC0415
    declared = _cast_species(k)
    low = actors.lower()
    for word, key in sorted(_SPECIES.items()):
        if word not in low:
            continue
        if key not in declared:
            bad.append("actors name %s and the class's cast declares %s"
                       % (word, declared or "no species"))
        elif not any(aud.species_mix(p).get(key, 0.0) > 0.0 for p in places):
            bad.append("actors name %s and none of the class's %d places "
                       "carries one in audio.species_mix"
                       % (word, len(places)))

    # -- writes, by running the class's own resolution ----------------------
    low_w = writes.lower()
    want = {kind for kw, kind in _WRITE_KW if kw in low_w}
    unmapped = [p.strip() for p in re.split(r",", writes)
                if p.strip() and not any(kw in p.lower()
                                         for kw, _ in _WRITE_KW)]
    n = 0
    if want:
        seen, n = _observed_writes(k, want)
        if not want <= seen:
            bad.append("writes drift: the row declares %s; %d resolutions over "
                       "%d place(s) x 4 hours x 3 casts x 3 stances produced "
                       "%s and never %s"
                       % (sorted(want), n, len(places), sorted(seen),
                          sorted(want - seen)))

    if bad:
        return False, "%s: %s" % (cid, "; ".join(bad))
    note = ("%d beats, %d place(s), writes %s seen in %d resolutions, %d ref(s) "
            "resolve" % (len(k.beats), len(places),
                         "{" + ",".join(sorted(want)) + "}" if want else "{}",
                         n, len(set(_ids_in(line)) - {cid})))
    if not want:
        note += ("; WRITES UNCHECKED -- no phrase in %r names a world-delta "
                 "kind" % writes)
    elif unmapped:
        note += "; unmapped write phrases %s" % unmapped
    return True, note
