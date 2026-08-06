"""VRB rows: the thirteen player verbs, checked against the Python authority
that would have to supply each one's content.

WHAT A VRB ROW IS. One markdown table row, four cells: the ID, the verb, "the
bar", and a CHECK column whose whole job is to NAME CONTENT --

    | VRB-01 | LOOK | every interactable answers with true, specific text
      (T1 rule: no two identical strings in a room class) | 20 sampled
      interactables across 5 rooms yield 20 distinct true strings; PLC-092's
      stencils and PLC-047's drawer tags among them |

So the row is not a wish. It says twenty strings, five rooms, and two named
places, and every one of those is a question `interact.read_text` can be asked
in milliseconds.

THE ROW HAS TWO HALVES AND ONLY ONE IS SETTLEABLE HERE.

  (a) THE CONTENT the check names -- the strings, the prices, the stances, the
      timetable, the ladder, the muster hour. All of it lives in Python, all of
      it is derived rather than authored, and all of it is checkable now. That
      is what this module checks, claim by claim, and it FAILS on most of them.
  (b) THE PLAYER WIRING -- that pressing a key in the shipped, streamed build
      performs the verb. Nothing headless can settle that, and a grep of
      `godot/scripts/*.gd` for a function name is precisely the static scan
      this project has been burned by nine times: `budget.occlusion_chain`
      reported `applied=True` while the shipped build loaded nothing, because a
      source reference cannot say which branch runs.

`SUFFICIENT = False` is (b), stated once. The SYSTEMS.md preamble above these
rows says it in its own words -- *"the per-verb wiring is tool-to-build ⇒ RED
today (no player verbs are shipped)"* -- so a GREEN from this module would be a
claim the spec itself does not make.

WHAT IS DELIBERATELY LEFT OUT OF EVERY CLAIM LIST, and it is reported rather
than hidden: `consequence.arrest` and `enforcement.place_row` are the
authorities VRB-08 and VRB-09 lean on, and each costs **~53 seconds a call** on
this box. `--smoke` is defined as sub-second harnesses, so those two are named
in the row's note as "not run here" instead of being quietly skipped. A tool
that silently substitutes a lesser check for the one asked for is the defect
`render_godot.sh` had.

Every checker returns `(claims, unchecked)`. A claim is (name, ok, note) and the
row passes only when all of them pass; `unchecked` is the part of the row's own
sentence this tier cannot reach, and it is printed on a PASS so a passing note
can never read as "the row is done".
"""
import os
import re

SUFFICIENT = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATION = os.path.join(ROOT, "station")

_CELLS = re.compile(r"^\|(.+)\|\s*$")

# The verb each ID must name. Written out because it is the cross-check that
# the registry's `at:` line still points at the row it thinks it does -- the
# same job `plc.py`'s heading match does. If SYSTEMS.md's table is reordered,
# this fails loudly instead of checking the wrong verb.
_VERB = {
    1: "LOOK", 2: "USE", 3: "TAKE/PLACE", 4: "SIT", 5: "BUY/SELL",
    6: "TALK", 7: "WORK", 8: "SHOW-PAPERS", 9: "FIGHT/RESTRAIN",
    10: "PILOT", 11: "RIDE", 12: "SLEEP", 13: "EAT/DRINK",
}


def _imp(name):
    import importlib                                             # noqa: PLC0415
    import sys                                                   # noqa: PLC0415
    if STATION not in sys.path:
        sys.path.insert(0, STATION)
    return importlib.import_module(name)


def _plc_key(n):
    """PLC-nnn -> the place key its own heading in PLACES.md names."""
    body = open(os.path.join(ROOT, "docs/spec/PLACES.md"), encoding="utf-8").read()
    m = re.search(r"^#+\s*PLC-0*%d\s*`([a-z0-9_]+)`" % n, body, re.M)
    return m.group(1) if m else None


def _src(rel):
    try:
        return open(os.path.join(ROOT, rel), encoding="utf-8").read()
    except OSError:
        return ""


# ===========================================================================
# VRB-01  LOOK
# ===========================================================================
def _v_look():
    """20 interactables, 5 rooms, 20 distinct true strings.

    THE SAMPLE IS NOT RANDOM AND MUST NOT BE. The row names two of the rooms --
    PLC-092's stencils and PLC-047's drawer tags -- so those two are in it by
    construction, and the other three are the three places declaring the most
    interactables, which is deterministic and is the sample most likely to
    PASS. Choosing the easiest three is the honest way round: a failure on the
    most-furnished rooms in the register is a failure everywhere.
    """
    DIR, IA = _imp("directory"), _imp("interact")
    named = [k for k in (_plc_key(92), _plc_key(47)) if k]
    rest = [p["key"] for p in sorted(
        DIR.PLACES, key=lambda q: (-len(q.get("interacts") or ()), q["key"]))
        if p["key"] not in named][:3]
    rooms = named + rest
    pairs = []
    pools = [[(k, t) for t in (DIR.by_key(k).get("interacts") or ())]
             for k in rooms]
    while len(pairs) < 20 and any(pools):
        for pool in pools:
            if pool and len(pairs) < 20:
                pairs.append(pool.pop(0))
    said = [(k, t, IA.read_text(k, t)) for k, t in pairs]
    blank = [(k, t) for k, t, s in said if not s.strip()]
    strings = [s for _k, _t, s in said if s.strip()]
    claims = [
        ("20 across 5 rooms", len(pairs) == 20 and len(rooms) == 5,
         "%d interactable(s) over %d room(s): %s"
         % (len(pairs), len(rooms), ", ".join(rooms))),
        ("20 true strings", not blank,
         "%d of %d answer LOOK with nothing (%s)"
         % (len(blank), len(pairs),
            ", ".join("%s/%s" % kt for kt in blank[:4])) if blank
         else "all %d speak" % len(pairs)),
        ("20 distinct", len(set(strings)) == len(strings),
         "%d distinct of %d non-empty" % (len(set(strings)), len(strings))),
    ]
    for n, k in ((92, _plc_key(92)), (47, _plc_key(47))):
        if not k:
            claims.append(("PLC-%03d named" % n, False,
                           "PLACES.md has no PLC-%03d heading" % n))
            continue
        got = [s for kk, _t, s in said if kk == k and s.strip()]
        claims.append(("PLC-%03d `%s` speaks" % (n, k), bool(got),
                       "%d of its %d declared interactable(s) answer LOOK"
                       % (len(got), len(DIR.by_key(k).get("interacts") or ()))))
    return claims, ["that a player standing in the room sees these strings"]


# ===========================================================================
# VRB-02  USE
# ===========================================================================
def _v_use():
    """own-state (a valve), remote-state (a lift_call), cross-room (PLC-002)."""
    DIR, IA = _imp("directory"), _imp("interact")
    toks = set(IA.tokens())
    claims = []
    for t in ("valve", "lift_call"):
        claims.append(("`%s` is an operable declaration" % t,
                       t in toks and IA.verb_of(t) == "operate",
                       "%s" % ("verb %s" % IA.verb_of(t) if t in toks
                               else "no register row declares it")))
    # REMOTE STATE. `lift.py` is 1,800 lines of shaft, car and collision
    # geometry and holds no car STATE at all -- no queue, no call, no position
    # a press could change. `ride_s` is a duration, not a summons.
    lift = _imp("lift")
    summons = [a for a in dir(lift)
               if re.search(r"call|summon|dispatch|request", a)
               and callable(getattr(lift, a))]
    claims.append(("a lift_call summons a car", bool(summons),
                   "lift.py exposes %s" % (", ".join(summons) if summons
                                           else "no call/summon/dispatch at "
                                                "all -- it is geometry, and no "
                                                "module holds car state")))
    # CROSS-ROOM. PLC-002's spec row adds a shutter master that closes
    # PLC-001's shutters; the register is what a runtime reads.
    k2, k1 = _plc_key(2), _plc_key(1)
    try:
        decl = DIR.by_key(k2).get("interacts") or ()
    except (KeyError, TypeError):
        decl = ()
    shut = [t for t in decl if "shutter" in t or "master" in t]
    claims.append(("PLC-002 `%s` declares a shutter master" % k2, bool(shut),
                   "register `%s`.interacts = %s" % (k2, decl)))
    try:
        far = DIR.by_key(k1).get("interacts") or ()
    except (KeyError, TypeError):
        far = ()
    claims.append(("PLC-001 `%s` has shutters to close" % k1,
                   any("shutter" in t or "blast_door" in t for t in far),
                   "register `%s`.interacts = %s" % (k1, far)))
    return claims, ["that the press moves a shutter in the built C&C"]


# ===========================================================================
# VRB-03  TAKE/PLACE
# ===========================================================================
def _v_take():
    """inventory exists; placement persists across a reload."""
    PL, EC = _imp("player"), _imp("economy")
    p = PL.random_player("vrb03")
    claims = []
    api = all(hasattr(p, a) for a in ("take", "drop", "has", "full"))
    claims.append(("an inventory exists", api,
                   "player.Player carries take/drop/has/full, cap %s"
                   % getattr(p, "carry_cap", "?")))
    goods = list(EC.goods_list("zocalo"))
    claims.append(("a GDS-01 item is on a stall", bool(goods),
                   "zocalo stocks %d good(s), e.g. %s"
                   % (len(goods), goods[0] if goods else "-")))
    took = bool(goods) and p.take(goods[0])
    st = p.state()
    back = PL.from_state(st)
    claims.append(("carrying survives a reload", took and back.has(goods[0]),
                   "took %r, state()->from_state() %s it"
                   % (goods[0] if goods else "-",
                      "keeps" if (took and back.has(goods[0])) else "loses")))
    # PLACEMENT IS THE HALF THAT IS MISSING, and it is a different fact from
    # carrying: the row wants the item PUT ON A SHELF in the player's quarters
    # and still there after a reload. Nothing in the persisted state names a
    # place an object sits in.
    keys = sorted(st.keys())
    placed = [k for k in keys if re.search(r"place[ds]|shelf|stored|deposit", k)]
    claims.append(("placement persists", bool(placed),
                   "player state keys are %s -- none of them records an "
                   "object placed anywhere" % ", ".join(keys)))
    return claims, ["that the engine's own save round-trips the same state"]


# ===========================================================================
# VRB-04  SIT
# ===========================================================================
def _v_sit():
    """seat tokens, `bar_unnamed`, and whether friction governs a seat."""
    DIR, IA, R = _imp("directory"), _imp("interact"), _imp("rooms")
    fr = _imp("npc.friction")
    seats = [t for t in IA.tokens() if IA.verb_of(t) in ("sit", "rest")]
    unkinded = [t for t in seats if t not in R.PROP_KIND]
    claims = [
        ("every seat token has a shape", not unkinded,
         "%d sit/rest token(s), %d with no rooms.PROP_KIND%s"
         % (len(seats), len(unkinded),
            (": " + ", ".join(unkinded[:4])) if unkinded else "")),
    ]
    bar = DIR.by_key("bar_unnamed").get("interacts") or ()
    mine = [t for t in bar if IA.verb_of(t) in ("sit", "rest")]
    claims.append(("`bar_unnamed` has a seat", bool(mine),
                   "declares %s" % (", ".join(mine) or "no sit-family token")))
    refused = not fr.will_share_table("narn", "centauri")
    claims.append(("friction refuses a Centauri table", refused,
                   "will_share_table(narn, centauri) = %s"
                   % fr.will_share_table("narn", "centauri")))
    # DOES ANYTHING SEAT A BODY THROUGH IT? The rule is only worth having if
    # the seat allocator asks. Measured across every module that places a
    # body: `civic_calendar` is the sole caller, and it pairs guests at a
    # banquet -- it does not seat the crowd.
    callers = []
    for dp, _dn, fn in os.walk(STATION):
        if "__pycache__" in dp or "spec_harness" in dp:
            continue
        for f in fn:
            if not f.endswith(".py") or f == "friction.py":
                continue
            if "will_share_table" in _src(os.path.relpath(
                    os.path.join(dp, f), ROOT)):
                callers.append(f)
    seating = [c for c in callers if c in ("populace.py", "crowd.py",
                                           "rooms.py", "dressing.py")]
    claims.append(("the seat allocator consults it", bool(seating),
                   "will_share_table is called from %s -- none of them is the "
                   "code that puts a body on a seat"
                   % (", ".join(sorted(callers)) or "nowhere")))
    return claims, ["that the player's own sit lands on the measured seat top"]


# ===========================================================================
# VRB-05  BUY/SELL
# ===========================================================================
def _v_buy():
    """credits and stock both ways, the 1-2 cr cart meal, and the fence."""
    EC, CQ = _imp("economy"), _imp("consequence")
    claims = []
    lo, hi = EC._MEAL
    claims.append(("the cart meal band is 1-2 cr", (lo, hi) == (1.0, 2.0),
                   "economy._MEAL = %s" % (EC._MEAL,)))
    plate = round(2 * EC.price("drum greens", "zocalo"), 3)
    claims.append(("a Zocalo plate prices into the band", lo <= plate <= hi,
                   "2 x drum greens at the zocalo = %.3f cr" % plate))
    # BOTH WAYS. `consequence.purchase` is the buy side and it is real; there
    # is no sell side anywhere -- no function in `consequence` or `economy`
    # moves a good from a purse to a till in the other direction.
    sells = [a for a in dir(CQ) + dir(EC)
             if re.fullmatch(r"sell|sell_to|fence|dispose_of", a)]
    claims.append(("credits and stock move BOTH ways", bool(sells),
                   "the buy side is consequence.purchase; the sell side is %s"
                   % (", ".join(sells) if sells else "not implemented -- no "
                      "sell/fence entry point exists")))
    cast = _src("docs/spec/PEOPLE.md")
    row41 = [ln for ln in cast.splitlines() if ln.startswith("| 41 |")]
    named = bool(row41) and "Vane" in row41[0]
    claims.append(("CAST row 41 is the fence", named,
                   (row41[0][:96] if row41 else "PEOPLE.md has no CAST row 41")))
    fence_place = re.search(r"`([a-z_]+)`", row41[0].split("|")[5]) if row41 else None
    if fence_place:
        try:
            fns = _imp("directory").by_key(fence_place.group(1))["functions"]
        except KeyError:
            fns = ()
        claims.append(("the fence's place trades", "black_market" in fns,
                       "`%s`.functions = %s" % (fence_place.group(1), fns)))
    return claims, ["that the engine's arithmetic equals consequence.purchase "
                    "(interact.verify_buy replays it, needs a played session)"]


# ===========================================================================
# VRB-06  TALK
# ===========================================================================
def _v_talk():
    """>=2 stances that turn something, and three PERSISTED outcomes."""
    DG, RES = _imp("dialogue"), _imp("npc.resident")
    ex = DG.speak(RES.resident("b5/vrb/6"), "bar_unnamed")
    stances = [c.stance for c in ex.choices]
    scripts = {s: " | ".join(x.text for x in ex.transcript(s)) for s in stances}
    claims = [
        (">=2 stances offered", len(set(stances)) >= 2,
         "topic %r offers %s" % (ex.topic, ", ".join(stances) or "no choice")),
        ("the stances differ", len(set(scripts.values())) == len(stances),
         "%d distinct transcript(s) from %d stance(s)"
         % (len(set(scripts.values())), len(stances))),
    ]
    # PERSISTED. A stance that is forgotten the moment the exchange ends is a
    # flavour, which is exactly what DLG-05 forbids. Nothing in `dialogue.py`,
    # `dialogue.gd` or the player's own state records which one was taken.
    holds = []
    for rel in ("station/dialogue.py", "godot/scripts/dialogue.gd",
                "station/player.py"):
        if re.search(r"remember|memory|recall|stance_taken", _src(rel)):
            holds.append(rel)
    claims.append(("three persisted outcomes", bool(holds),
                   "no module records the stance taken (%s)"
                   % ", ".join(holds) if holds
                   else "neither dialogue.py, dialogue.gd nor player.py holds "
                        "any memory of a stance"))
    return claims, ["the ROLE-05 questioning scene specifically -- there is no "
                    "scene registry to look it up in"]


# ===========================================================================
# VRB-07  WORK
# ===========================================================================
def _v_work():
    """all 12 ROLE shift loops clock on and off with pay."""
    people = _src("docs/spec/PEOPLE.md")
    ids = sorted({int(m) for m in re.findall(r"^### ROLE-(\d+)", people, re.M)})
    claims = [("12 ROLE rows exist", len(ids) == 12,
               "PEOPLE.md heads ROLE-%02d..%02d, %d row(s)"
               % (min(ids or [0]), max(ids or [0]), len(ids)))]
    # WHICH OF THEM HAS A LOOP. A shift loop is clock-on, clock-off and pay;
    # `dockwork.py` has all three and says so in its own first line ("ROLE-03,
    # THE DOCKWORKER -- the first complete job loop, end to end"). Nothing
    # else in station/ carries a clock-on hour at all.
    loops = []
    for dp, _dn, fn in os.walk(STATION):
        if "__pycache__" in dp or "spec_harness" in dp:
            continue
        for f in fn:
            if not f.endswith(".py"):
                continue
            body = _src(os.path.relpath(os.path.join(dp, f), ROOT))
            if re.search(r"CLOCK_ON_H|clock_on", body) and "pay" in body.lower():
                loops.append(f)
    claims.append(("12 shift loops clock on and off with pay",
                   len(loops) >= len(ids) or len(loops) >= 12,
                   "%d of %d ROLEs have a clock-on/clock-off loop (%s)"
                   % (len(loops), len(ids), ", ".join(sorted(loops)) or "none")))
    return claims, ["that each loop passes its own ROLE ACCEPT -- those need a "
                    "played shift"]


# ===========================================================================
# VRB-08  SHOW-PAPERS
# ===========================================================================
def _v_papers():
    """the card is presented, read and reacted to, both directions."""
    PL, CQ = _imp("player"), _imp("consequence")
    p = PL.random_player("vrb08")
    # `Player.identicard()` returns the CARD AS IT READS -- the field rows a
    # reader sees, each with whether it is filled -- not the Resident behind
    # it. That is the right shape for a verb about presenting a card, and the
    # row's "reacts to its visa" needs the VISAS row specifically.
    card = p.identicard()
    fields = {str(f[0]): f[1] for f in (card or ()) if len(f) >= 2}
    claims = [
        ("the player carries a real card", "VISAS" in fields,
         "%d field(s): %s; VISAS=%r, status=%r"
         % (len(fields), fields.get("NAME", "?"), fields.get("VISAS"),
            p.status)),
    ]
    # READ AND REACTED TO. `consequence.admits` is the reader: it takes the
    # card's tier and returns a verdict and the reason a gate would give. Two
    # different tiers must get two different answers or nothing is being read.
    hi = CQ.admits("cnc", CQ.RUNGS[0])
    lo = CQ.admits("cnc", CQ.DETAINED)
    claims.append(("a gate reacts to the card's state", hi[0] != lo[0],
                   "cnc admits rung %s -> %s, rung %s -> %s"
                   % (CQ.RUNGS[0], hi[0], CQ.DETAINED, lo[0])))
    # THE OTHER DIRECTION -- the player AS the officer reading somebody's card.
    # `enforcement.py` decides who gets stopped; nothing anywhere returns what
    # a card looks like to a reader who is the player.
    both = re.search(r"def read_card|def inspect_card|player_reads",
                     _src("station/enforcement.py") + _src("station/player.py")
                     + _src("godot/scripts/enforcement.gd"))
    claims.append(("both directions", bool(both),
                   "no read-a-card-as-officer entry point in enforcement.py, "
                   "player.py or enforcement.gd"))
    return claims, ["the Grey-boundary stop itself: enforcement.place_row is "
                    "the authority and costs ~53 s a call, so it is out of the "
                    "sub-second tier"]


# ===========================================================================
# VRB-09  FIGHT/RESTRAIN
# ===========================================================================
def _v_fight():
    """the 7-rung ladder, and a readable booking record in the brig."""
    DIR, CQ, IA = _imp("directory"), _imp("consequence"), _imp("interact")
    ladder = (CQ.DETAINED,) + tuple(CQ.RUNGS)
    claims = [
        ("the ladder has 7 rungs", len(ladder) == 7,
         "consequence: DETAINED + RUNGS = %s" % (ladder,)),
        ("the brig has cells", getattr(CQ, "BRIG_CELLS", 0) > 0,
         "BRIG_CELLS = %s at `%s`" % (getattr(CQ, "BRIG_CELLS", None),
                                      getattr(CQ, "BRIG", "?"))),
    ]
    k = _plc_key(17)
    decl = DIR.by_key(k).get("interacts") or () if k else ()
    readable = [t for t in decl if IA.read_text(k, t).strip()]
    booking = [t for t in decl if re.search(r"record|booking|charge|log", t)]
    claims.append(("PLC-017 `%s` holds a readable booking record" % k,
                   bool(booking) and bool(readable),
                   "declares %s; %d of them answer LOOK with anything"
                   % (decl, len(readable))))
    return claims, ["the arrest itself: consequence.arrest costs ~53 s a call "
                    "and is out of the sub-second tier"]


# ===========================================================================
# VRB-10  PILOT
# ===========================================================================
def _v_pilot():
    """SUR-04's loop: the ROLE-12 sortie, launch to recovery."""
    claims = []
    phys = os.path.join(STATION, "physics")
    mods = sorted(f for f in os.listdir(phys) if f.endswith(".py")) \
        if os.path.isdir(phys) else []
    claims.append(("a flight model exists", bool(mods),
                   "station/physics/ holds %d module(s)" % len(mods)))
    geom = os.path.exists(os.path.join(STATION, "starfury_geometry.py"))
    claims.append(("an airframe exists", geom,
                   "station/starfury_geometry.py %s"
                   % ("present" if geom else "missing")))
    # THE SORTIE. Launch, patrol, recovery -- one loop, with a state that says
    # which phase it is in. Nothing in station/ names one.
    sortie = []
    for dp, _dn, fn in os.walk(STATION):
        if "__pycache__" in dp or "spec_harness" in dp:
            continue
        for f in fn:
            if f.endswith(".py") and re.search(
                    r"def sortie|def launch_and_recover|RECOVERY_",
                    _src(os.path.relpath(os.path.join(dp, f), ROOT))):
                sortie.append(f)
    claims.append(("a launch-to-recovery loop exists", bool(sortie),
                   "no module in station/ defines a sortie or a recovery phase"
                   if not sortie else ", ".join(sortie)))
    return claims, ["that --mode=starfury is reachable from the shipped "
                    "streamed build (only launching it can say)"]


# ===========================================================================
# VRB-11  RIDE
# ===========================================================================
def _v_ride():
    """every SYS-09 vehicle, timetable-true, and a derived Red->Grey time."""
    IT, TR = _imp("interior"), _imp("transit")
    schema, prof = IT.load()
    lines = {x["key"]: x for x in TR.all_lines(schema, prof)}
    want = {"core_shuttle": ("stops", 13), "guideway_tram": ("stops", 5),
            "ground_tram": ("stops", 3), "spoke_lift": ("lines", 3)}
    bad = []
    for k, (field, n) in want.items():
        got = lines.get(k, {}).get(field)
        if got != n:
            bad.append("%s %s=%s, SYS-09 says %d" % (k, field, got, n))
    claims = [("the four SYS-09 timetables are as stated", not bad,
               "; ".join(bad) if bad else
               "core shuttle 13 stops, drum tram 5, ground tram 3, "
               "spoke lifts 3 lines")]
    # A DERIVED RED->GREY TIME. The core shuttle's stops are even over
    # z 3,397-8,047; Grey and Red are the bands the row names, so the ride is
    # the legs between the stop nearest each.
    cs = lines.get("core_shuttle", {})
    stops = cs.get("stops_z") or []
    DIR = _imp("directory")

    def nearest(sector):
        zs = [p["z_m"] for p in DIR.PLACES if p["sector"] == sector]
        if not zs or not stops:
            return None
        mid = sum(zs) / len(zs)
        return min(stops, key=lambda s: abs(s - mid))
    a, b = nearest("red"), nearest("grey")
    secs = None
    if a is not None and b is not None and a != b:
        secs = TR.leg_time(schema, cs, abs(a - b))
    claims.append(("a Red->Grey shuttle time is derivable", bool(secs),
                   "stop z%.0f -> z%.0f, %.0f m, %.0f s"
                   % (b, a, abs(a - b), secs) if secs
                   else "no core-shuttle stops to ride between"))
    return claims, ["the +/-10% acceptance: it compares a SHIPPED-BUILD ride "
                    "against this timetable and there is no ride to time"]


# ===========================================================================
# VRB-12  SLEEP
# ===========================================================================
def _v_sleep():
    """advances the clock, interruptible: 22:00->05:15 makes the 05:40 muster."""
    DW, SC = _imp("dockwork"), _imp("npc.schedule")
    claims = [
        ("the 05:40 muster is real", abs(DW.MUSTER_H - (5 + 40 / 60.0)) < 1e-6,
         "dockwork.MUSTER_H = %05.2f, clock-on %04.1f" % (DW.MUSTER_H,
                                                          DW.CLOCK_ON_H)),
        ("a sleep window model exists", hasattr(SC, "sleep_window"),
         "npc/schedule.sleep_window %s"
         % ("present" if hasattr(SC, "sleep_window") else "missing")),
    ]
    # ADVANCING THE CLOCK is the verb. `sleep_window` says when an NPC sleeps;
    # nothing takes a player from 22:00 to 05:15 through a running simulation,
    # and nothing can interrupt it.
    adv = []
    for rel in ("station/player.py", "godot/scripts/player.gd",
                "godot/scripts/life.gd", "godot/scripts/main.gd"):
        if re.search(r"def sleep|func sleep|advance_to|skip_to", _src(rel)):
            adv.append(rel)
    claims.append(("sleeping advances the clock", bool(adv),
                   "%s" % (", ".join(adv) if adv else
                           "no sleep/advance entry point in player.py, "
                           "player.gd, life.gd or main.gd")))
    inc = _imp("incident")
    sweeps = [k for k in getattr(inc, "CLASSES", ()) if "SWEEP" in str(k)]
    claims.append(("a sweep event exists to wake the player",
                   bool(sweeps) or "INC-SWEEP" in _src("station/incident.py"),
                   "incident.py carries INC-SWEEP"))
    return claims, ["that the sleep is interruptible in a running sim"]


# ===========================================================================
# VRB-13  EAT/DRINK
# ===========================================================================
def _v_eat():
    """meals debit AND feed, species venues respected, the pak'ma'ra ejection."""
    PL, EC = _imp("player"), _imp("economy")
    inc = _imp("incident")
    p = PL.random_player("vrb13")
    st = p.state()
    fed = [k for k in st if re.search(r"fed|hunger|nourish|sated|meal", k)]
    claims = [
        ("meals debit", hasattr(p, "spend"),
         "player.spend() moves credits"),
        # PLY-06 CALLS IT A *SIGNED* STATE, so it has to be somewhere a save
        # keeps. It is in no key of the player's own persisted state.
        ("meals feed a signed state", bool(fed),
         "player state keys are %s -- none of them is nourishment"
         % ", ".join(sorted(st))),
    ]
    food = list(EC.goods_list("eclipse_cafe"))
    claims.append(("Eclipse serves food", bool(food),
                   "eclipse_cafe stocks %d line(s)" % len(food)))
    meals = getattr(inc, "PAKMA_MEALS", ())
    claims.append(("INC-PAKMA covers 04:00", 4.0 in tuple(meals),
                   "incident.PAKMA_MEALS = %s" % (meals,)))
    return claims, ["that the pak'ma'ra area ejects a player standing in it"]


_CHECKS = {1: _v_look, 2: _v_use, 3: _v_take, 4: _v_sit, 5: _v_buy,
           6: _v_talk, 7: _v_work, 8: _v_papers, 9: _v_fight, 10: _v_pilot,
           11: _v_ride, 12: _v_sleep, 13: _v_eat}


def check(row):
    from spec_harness import spec_text                           # noqa: PLC0415
    rid = row.get("id", "")
    try:
        n = int(rid.split("-")[1])
    except (IndexError, ValueError):
        return False, "not a VRB id: %r" % rid
    text = spec_text(row.get("at", ""), lines=1).strip()
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    m = _CELLS.match(text)
    if not m:
        return False, "not a table row: %r" % text[:60]
    cells = [c.strip() for c in m.group(1).split("|")]
    want_id = "VRB-%02d" % n
    if cells[0].strip("* ") != want_id:
        return False, "registry %s points at a row headed %r" % (rid, cells[0])
    if len(cells) < 4:
        return False, "%s has %d cells, expected 4" % (want_id, len(cells))
    if cells[1] != _VERB.get(n):
        return False, ("%s should be the verb %s and the row says %r"
                       % (want_id, _VERB.get(n), cells[1]))
    fn = _CHECKS.get(n)
    if fn is None:                                               # pragma: no cover
        return False, "no checker for %s" % want_id
    claims, unchecked = fn()
    bad = [(c, note) for c, ok, note in claims if not ok]
    if bad:
        return False, "%s: %s" % (cells[1],
                                  "; ".join("%s -- %s" % b for b in bad))
    good = "; ".join("%s (%s)" % (c, note) for c, _ok, note in claims)
    tail = ("  NOT CHECKED HERE: " + "; ".join(unchecked)) if unchecked else ""
    return True, "%s: %s%s" % (cells[1], good, tail)


# ---------------------------------------------------------------------------
def _selftest(out=print):
    """Run all thirteen, then show each half of the harness moving.

    A harness observed only failing has not been shown to discriminate any more
    than one observed only passing. So every control below flips a claim the
    other way and prints both readings.
    """
    rows = [{"id": "VRB-%03d" % n, "at": "docs/spec/SYSTEMS.md:%d" % (519 + n)}
            for n in range(1, 14)]
    fails = 0
    for r in rows:
        ok, note = check(r)
        fails += 0 if ok else 1
        out("%-8s %-4s %s" % (r["id"], "PASS" if ok else "FAIL", note[:210]))
    out("")
    out("-- controls --")

    # 1. THE ROW-IDENTITY CHECK. Point VRB-01 at VRB-02's line.
    ok, note = check({"id": "VRB-001", "at": "docs/spec/SYSTEMS.md:521"})
    out("VRB-01 aimed at row 521 -> %s: %s" % ("PASS" if ok else "FAIL", note[:100]))

    # 2. A CLAIM THAT PASSES TODAY, BROKEN. VRB-11's timetable is the only
    #    fully-passing content claim in the family; bend one stop count and it
    #    must say so with both numbers.
    TR = _imp("transit")
    real = TR.CORE_SHUTTLE_STOPS
    ok, note = check(rows[10])
    out("VRB-11 as shipped        -> %s: %s" % ("PASS" if ok else "FAIL", note[:150]))
    TR.CORE_SHUTTLE_STOPS = 11
    ok, note = check(rows[10])
    out("VRB-11 with 11 stops     -> %s: %s" % ("PASS" if ok else "FAIL", note[:150]))
    TR.CORE_SHUTTLE_STOPS = real

    # 3. A CLAIM THAT FAILS TODAY, SATISFIED. VRB-13's nourishment key is
    #    absent from the player's persisted state; add one and the claim
    #    flips, which proves the failure is about the content and not about
    #    the harness's ability to see it.
    PL = _imp("player")
    orig = PL.Player.state

    def patched(self):
        st = orig(self)
        st["fed_h"] = 6.0
        return st
    PL.Player.state = patched
    ok, note = check(rows[12])
    out("VRB-13 with a fed state  -> %s: %s" % ("PASS" if ok else "FAIL", note[:150]))
    PL.Player.state = orig
    ok, note = check(rows[12])
    out("VRB-13 restored          -> %s: %s" % ("PASS" if ok else "FAIL", note[:150]))
    out("")
    out("%d of 13 VRB rows fail" % fails)
    return fails


if __name__ == "__main__":                                       # pragma: no cover
    import sys
    sys.path.insert(0, STATION)
    _selftest()
