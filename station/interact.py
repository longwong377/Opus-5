#!/usr/bin/env python3
"""What a player can USE, derived from the register instead of invented.

THE DATA WAS ALREADY THERE AND NOTHING READ IT. `station/directory.py` has given
every one of the 128 register places an `interacts` field since layer 1 -- it is
literally the column headed *what a player can use in this room* -- and
`STATE.md`'s open-findings list still says "Nothing is interactable except the
door." Both are true at once because `interacts` had exactly two consumers:
`rooms.lateral_stack`, which reads it to decide how much WALL a room needs, and
`rooms.build`, which reads it to decide where to STAND a box. Neither of those is
a player using anything.

So this module does the one thing that turns a declared list into a mechanic:

  1. it derives a BOUNDED VERB SET from the register's own strings,
  2. it says which emitted mesh group provides each declared interactable, and
  3. it asserts that every declared interactable resolves to a group that some
     room actually emits.

WHAT THAT ASSERTION FOUND, AND WHAT THE SHAPE OF IT MEANT. On the session it was
written it failed on 84 of 357, and the split was TOTAL: `built generic 273/275`,
`built bespoke 0/82`. Not a content gap and not 23 modules each forgetting the
same thing -- ONE placement rule, living inside the body of `rooms.build`, that
only one caller could reach. Every place composed by its own module got its true
shape and none of its declared uses: the Zocalo, C&C, all four quarters, the
three bars, customs, the alien sector.

A number that fails evenly is a list of jobs. A number that fails 100% on one
side of a line and 1% on the other is a structural fact, and reading it that way
is what turned 84 separate props into one extraction (`rooms.place_interacts`)
plus one resolution rule (`alias_for`, for the 26 that WERE built under the
module's own name for the object).

WHY THE VERB SET IS DERIVED AND NOT CHOSEN. `docs/MASTER-PLAN.md` §3.2 is blunt
about the cost of getting this backwards -- *"Building 71 prop behaviours before
knowing the verb set is how you build the wrong 71."* A verb set written from
imagination would be a fourth vocabulary in a project that already has three
(the register's `interacts`, `rooms.PROPS`, `rooms.PROP_KIND`), and a fourth
vocabulary is a fourth thing to drift. So both tables below are keyed on
something this repository already computes:

  `_KIND_VERB`   16 entries, one per value of `rooms.PROP_KIND` -- the project's
                 own classification of the same 99 tokens, written for
                 `dressing.machine()`. It says what SHAPE the thing is.
  `_HEAD_VERB`   22 entries, keyed on the token's HEAD NOUN -- the last
                 underscore field, which is the register's own word for what the
                 object IS. It overrides the shape where the two disagree: a
                 `valve` is a `wallpanel` by shape and a control by name.

Both are asserted TOTAL (every one of the 99 tokens resolves) and MINIMAL
(deleting any single override changes at least one token's verb, so a dead or
redundant entry cannot accumulate). That pair of assertions is what stops the
tables becoming a place to write opinions: an entry has to earn its row.

WHAT THE HEAD-NOUN COLLISIONS SAY. Four head nouns are shared by tokens the
shape rule classifies differently -- `bench` covers a `bench` you sit on and a
`lab_bench` you work at; `lamp` covers a status lamp you read and a pendant lamp
you switch. `--verbs` prints them. They are the places where one override cannot
be right for both tokens, and they are reported rather than smoothed over,
because a vocabulary that needs a per-token exception is telling you something.

Run: python3 station/interact.py --verbs        # the verb set and its derivation
     python3 station/interact.py --audit        # does every declared use RESOLVE
     python3 station/interact.py --selftest     # with negative controls
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import directory as dr                                           # noqa: E402
import rooms as R                                                # noqa: E402

# ---------------------------------------------------------------------------
# The verb set
# ---------------------------------------------------------------------------
# Eight verbs, each a different thing a pair of hands does. The count is an
# OUTPUT of the two tables below, not an input to them -- `verb_set()` derives
# it -- and `VERBS` exists to give each one a written definition, because a verb
# named and not defined is how `read` quietly grows to mean everything.
#
# `tread` is the honest bucket and it is stated as such: a catwalk, a path, a
# handhold and a kerb are things you get about ON, not things you press. They
# are in the register's `interacts` because the register is a list of what a
# player MEETS, and it would be a lie to give them a prompt and a keypress.
VERBS = {
    "open":    "a leaf parts and you pass through it",
    "operate": "work a control, and something in the world changes",
    "read":    "look at it and it tells you something",
    "sit":     "take a seat at it",
    "rest":    "stop and stay a while -- a bunk, a shrine, a brazier",
    "store":   "open it, and take something out or put something in",
    "serve":   "be served across it; you are talking to whoever is behind it",
    "tread":   "underfoot or in the hand -- you walk on it, climb it or hold "
               "it. NO KEYPRESS: this verb deliberately has no prompt",
}

# Verbs a player actually presses a key for. `tread` is excluded on purpose --
# see above -- and the split is data the runtime reads, so a prompt cannot
# appear on a floor marking without this line changing.
PRESSABLE = tuple(v for v in VERBS if v != "tread")

# Verbs where the OBJECT is what responds, so a keypress has somewhere to go
# with the geometry that exists today. A door leaf parts, a lever throws, a
# drawer runs out, a screen changes -- all of them are the prop moving or
# changing, and the prop is built.
#
# `sit` and `rest` are deliberately NOT here, and the reason is worth keeping:
# what responds to those is a BODY, not a prop. Sitting needs the player's own
# animation -- `npc/animation.py` has `sit_clip` and the player has no rig.
# Listing them as responding would make `use()` return true and nothing happen,
# which is the failure that looks like success, so the runtime reads this and
# reports `response=none` for them instead.
#
# `serve` WAS IN THAT LIST UNTIL SESSION 4e, excluded because "being served
# needs whoever is behind the counter to turn round and talk, which needs
# dialogue". `station/dialogue.py` is that dialogue: `serve_response()` puts a
# named person behind 29 counters across 27 register places, each drawn from
# that room's own regulars, saying something derived from the hour, their
# species rhythm, their trade and what the port is doing. So the exclusion is
# lifted, and it is lifted because the thing it was waiting for arrived.
RESPONDS = ("open", "operate", "read", "store", "serve")

# The SHAPE rule. One row per distinct value of `rooms.PROP_KIND`, which is the
# classification `dressing.machine()` already builds these objects from.
_KIND_VERB = {
    "leaf":      "open",
    "seat":      "sit",
    "bed":       "rest",
    "cabinet":   "store",
    "crate":     "store",
    "rack":      "store",
    "counter":   "serve",
    "console":   "operate",
    "crane":     "operate",
    "skid":      "operate",
    "gantry":    "operate",
    "vessel":    "operate",
    "wallpanel": "read",
    "screen":    "read",
    "kerb":      "tread",
    "post":      "tread",
}

# The NAME rule, and it wins. Keyed on the head noun -- the last underscore
# field of the register's own token -- for the cases where what a thing is
# called settles what you do with it and what shape it is does not.
#
# Every row here is justified by a token the shape rule gets wrong, and
# `_check_minimal` proves it: delete any single row and at least one of the 99
# tokens changes verb. The comment on each row names that token.
_HEAD_VERB = {
    "valve":     "operate",   # wallpanel by shape; you turn it
    "lever":     "operate",   # breaker_lever
    "call":      "operate",   # lift_call -- a button, not a sign
    "control":   "operate",   # irrigation_control is a wallpanel by shape
    "reader":    "operate",   # identicard_reader -- you present a card
    "intercom":  "operate",   # you speak into it
    "terminal":  "operate",   # babcom_terminal is a wallpanel by shape
    "dartboard": "operate",   # wallpanel by shape; it is a game
    "shower":    "operate",   # cabinet by shape
    "standpipe": "operate",   # post by shape; it is a water outlet
    "stall":     "serve",     # market_stall is a `screen` by shape
    "shopfront": "serve",     # screen by shape
    "booth":     "serve",     # bay_control_booth -- somebody is inside it
    "ladder":    "tread",     # service_ladder is a `screen` by shape
    "rail":      "tread",     # gallery_rail -- you lean on it
    "barrier":   "tread",     # screen by shape; you go round it
    "drawer":    "store",     # cold_drawer is a `bed` by shape and is not one
    "table":     "sit",       # counter by shape; you sit at a table
    "gallery":   "sit",       # public_gallery -- you sit in it
    "lamp":      "read",      # pendant_lamp is a `post` by shape
    "shrine":    "rest",      # cabinet by shape
    "brazier":   "rest",      # post by shape
}

# The two prefixes `rooms._fixture` emits under. `prop_` is a declared
# interactable placed from `place["interacts"]`; `fix_` is a fixture the room is
# NAMED for, from `rooms.FIXTURES` / `PLACE_FIXTURES`. Both can provide a
# declared use and both are searched.
PREFIXES = ("prop_", "fix_")

# `rooms._MACH` marks a nested machine PART -- `prop_mp_plant_rail` is a rail
# inside a machine, not an interactable called `mp_plant_rail`. Imported rather
# than spelled again.
_PART = R._MACH.lstrip("_")

# The separator `deck.build_deck` puts between a place key and the room's own
# group name in an assembled deck: `docking_bays__prop_bay_door`.
PLACE_SEP = "__"


def tokens():
    """Every distinct interactable the register declares, sorted."""
    return sorted({i for p in dr.PLACES for i in (p.get("interacts") or ())})


def head_noun(token):
    """The register's own word for what the thing is: the last field."""
    return token.rsplit("_", 1)[-1]


def verb_of(token):
    """The verb for one declared interactable. Name beats shape."""
    h = head_noun(token)
    if h in _HEAD_VERB:
        return _HEAD_VERB[h]
    kind = R.PROP_KIND.get(token)
    if kind is None:
        raise KeyError(f"{token!r} has no rooms.PROP_KIND and no head-noun rule")
    if kind not in _KIND_VERB:
        raise KeyError(f"PROP_KIND {kind!r} ({token}) has no verb")
    return _KIND_VERB[kind]


def verb_set():
    """The verbs actually reached by the 99 tokens, in VERBS order.

    DERIVED, not declared. If a row of `VERBS` is never reached it is a verb
    nobody can perform, and `_selftest` fails for it.
    """
    used = {verb_of(t) for t in tokens()}
    return tuple(v for v in VERBS if v in used)


def by_verb():
    """verb -> the tokens that carry it."""
    out = {v: [] for v in VERBS}
    for t in tokens():
        out[verb_of(t)].append(t)
    return {k: v for k, v in out.items() if v}


def groups_for(token):
    """The mesh group names that would provide this interactable.

    A ROOM'S OWN FRAME, not the deck's. `rooms._fixture` emits
    `prop_<token>` or `fix_<token>`; `deck.build_deck` later prefixes the place
    key and `PLACE_SEP`. Both forms are recognised by `provides`.
    """
    return tuple(p + token for p in PREFIXES)


def provides(group):
    """(place_key, token, verb) for a mesh group, or None if it is not one.

    Accepts both the room's own `prop_<token>` and the deck's
    `<place>__prop_<token>`. A machine PART -- `prop_mp_plant_rail` -- is not an
    interactable and returns None, which is why `_PART` is imported from
    `rooms` rather than written here.
    """
    place = ""
    body = group
    if PLACE_SEP in group:
        place, _, body = group.partition(PLACE_SEP)
    for p in PREFIXES:
        if not body.startswith(p):
            continue
        tok = body[len(p):]
        if tok.startswith(_PART):
            return None
        if tok in _TOKENS:
            return place, tok, verb_of(tok)
    return None


# ---------------------------------------------------------------------------
# Does a declared use RESOLVE to something a room emits?
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# WHAT A READ ACTUALLY SAYS
# ---------------------------------------------------------------------------
# THE VERB WAS A WIGGLE AND THIS IS THE HALF THAT MAKES ONE OF THEM REAL.
# `interact.gd::_press` increments a counter, depresses the prop for a few
# frames and prints a log line -- for EVERY verb, identically. So `read` on an
# arrivals board showed a player exactly what `open` on a locker showed them:
# nothing. The module's own header set out to end "357 declarations, 0 verbs";
# it ended the DECLARATION gap, and the 357/357 statistic measures the half that
# was closed.
#
# NOT ONE LINE HERE IS WRITTEN. Every string is a READING of a module that
# already had the content and no consumer:
#
#   info_board / arrivals   `signage.arrivals_lines(hour, day)` -- the real
#                           board, the same one the mesh letters are cut from
#   monitor_wall,           `broadcast.day(day_n)` -- ISN bulletins era-keyed
#   public_information_*,   through `costume.ERA_EVENTS`, MiniPax notices, the
#   comms_channel           PA calls, all of which existed and were audible-only
#   menu_display            `economy` stock and price at THIS counter
#   level_plaque            the place's own address out of `directory`
#   station_schematic_*     where you are, and what is adjacent
#   atmosphere_status_lamp  the place's atmosphere number
#   neon_sign, sign         the place's own name
#
# A token with nothing derivable returns "" and the runtime falls back to the
# label, which is what it did before. That is deliberate: a `read` that invents
# a line would be exactly the unmarked invention hard rule 1 forbids.
# Tokens whose text is a FUNCTION OF THE HOUR. The sidecar is baked, so their
# string is a snapshot taken at the bake hour and is flagged `live` -- a runtime
# that wants a board to change through the day refreshes these and leaves the
# rest alone. Saying which is which here is cheaper than the runtime guessing,
# and it is the difference between a board that is WRONG at 03:00 and one that
# is merely not yet refreshed.
LIVE_READ = ("info_board", "arrivals_board", "departure_board", "monitor_wall",
             "public_information_monitor", "comms_channel", "babcom_terminal",
             "isn_screen", "menu_display", "price_board")

_READ_CACHE = {}


def read_text(place_key, token, hour=13.0, day=0):
    """What this readable prop says right now, derived. "" if nothing is."""
    key = (place_key, token, round(float(hour), 2), int(day))
    if key in _READ_CACHE:
        return _READ_CACHE[key]
    out = ""
    try:
        q = dr.by_key(place_key)
    except Exception:
        q = None
    t = token or ""
    try:
        if t in ("info_board", "arrivals_board", "departure_board"):
            import signage                                      # noqa: PLC0415
            rows = signage.arrivals_lines(hour=hour, day=day)
            out = "\n".join(str(r) for r in rows[:6])
        elif t in ("monitor_wall", "public_information_monitor",
                   "comms_channel", "babcom_terminal", "isn_screen"):
            import broadcast                                    # noqa: PLC0415
            calls = broadcast.day(day)
            near = [c for c in calls
                    if abs(float(c.get("hour", -99)) - float(hour)) <= 3.0]
            pick = (near or calls)[:2]
            out = "\n".join(str(c.get("text", "")) for c in pick)
        elif t in ("menu_display", "price_board") and q is not None:
            import economy                                      # noqa: PLC0415
            lines = []
            for ln in economy.lines_at(place_key)[:5] \
                    if hasattr(economy, "lines_at") else []:
                lines.append(str(ln))
            out = "\n".join(lines)
        elif t == "level_plaque" and q is not None:
            out = ("%s\n%s ring %d deck %d" % (q["name"], q["sector"].upper(),
                                                q["ring"], q["deck"]))
        elif t in ("station_schematic_screen", "wayfinding_sign") and q is not None:
            adj = ", ".join(q.get("adjacent", ())[:4]) or "no marked neighbour"
            out = "YOU ARE HERE -- %s\nadjacent: %s" % (q["name"], adj)
        elif t == "atmosphere_status_lamp" and q is not None:
            fns = set(q.get("functions", ()))
            if "sealed_volume" in fns:
                out = "%s\nATMOSPHERE MAINTAINED -- SEALED, NO ENTRY" % q["name"]
            elif "multi_environ" in fns or "sealed_environment" in fns:
                out = "%s\nNON-STANDARD ATMOSPHERE -- BREATHER REQUIRED" % q["name"]
            else:
                out = "%s\nATMOSPHERE 02 -- STANDARD OXYGEN/NITROGEN" % q["name"]
        elif t in ("neon_sign", "sign", "shop_sign") and q is not None:
            out = q["name"]
    except Exception:
        out = ""
    _READ_CACHE[key] = out
    return out


def emitted_tokens(names):
    """The interactables a set of emitted group names actually provides."""
    out = set()
    for n in names:
        r = provides(n)
        if r is not None:
            out.add(r[1])
    return out


def _segments(name):
    return tuple(s for s in name.split("_") if s)


def near_miss(token, names):
    """Group names that are PROBABLY this interactable under another name.

    Reported separately from a plain miss because the two need different fixes.
    `customs_north` is composed by `customs.py`, which emits `customs_desk` for
    the declared `customs_desk` and `customs_screen_schematic` for the declared
    `station_schematic_screen` -- the first is the same word in the same order
    and the second is the same words in a different one. A count that lumps
    those together says "the module built nothing", which is false and would
    send the next context to rewrite a module that is already right.

    The test is on underscore SEGMENTS, never substrings: `npc_seated_4`
    contains the letters of `seat` and is a person.
    """
    seg = set(_segments(token))
    if not seg:
        return ()
    out = []
    for n in names:
        s = set(_segments(n))
        if seg <= s:
            out.append(n)
    return tuple(sorted(out))


# Segments a group name may carry that make it unusable as an alias, whatever
# else it is called. `mp` is `rooms._MACH`'s marker for a nested machine PART --
# `dress_mp_prop_locker` is a drawer front inside a locker, not the locker --
# and `npc`/`light` are the two negative controls `provides` already carries: a
# prompt on a person or on a lamp is the failure this rule could introduce.
_ALIAS_NEVER = ("mp", "npc", "light")


def weights(spans):
    """group -> how many triangles carry that name. The tiebreak, measured.

    A MODULE'S OBJECT AND ITS PARTS SHARE A PREFIX and the name cannot tell
    them apart: `cnc` emits `cc_console_face` and `cc_console_leg`, both three
    segments, both containing `console`. Ranking on the NAME picks whichever
    word is shorter, which is a coin toss dressed as a rule.

    So the tiebreak asks the mesh how big each one is, on the same principle as
    measuring the corridor profile by ray casting rather than writing it down:
    the thing being described is geometry, so ask the geometry. Measured on
    `cnc`, `cc_console_leg` is 120 triangles over five instances against
    `cc_console_face`'s 60 -- the "leg" is the console's 24-triangle BODY and
    the "face" is a 12-triangle panel on it, so size anchors the prompt to the
    cabinet rather than to one plate of it. What the player reads is the
    register's own token either way (`label` is `token`, never the group name);
    what this decides is which volume they have to be standing near.
    """
    out = {}
    for n, lo, hi in spans:
        out[n] = out.get(n, 0) + max(0, hi - lo)
    return out


def alias_for(token, names, claimed=(), size=None):
    """The group a module built this interactable under, when it used its OWN
    name for it -- or None.

    26 OF THE 84 UNRESOLVED DECLARATIONS ARE NOT MISSING CONTENT. `earharts`
    builds `bar_table` for the declared `table`, `cnc` builds `cc_console_face`
    for `console`, `customs_north` builds `customs_desk` for `customs_desk`.
    The object is there, articulated, materialled and lit; what is missing is
    that `provides()` -- which knows only a name -- cannot see it, so the
    runtime puts no prompt on it and `--audit` calls it absent.

    The rule is `near_miss`'s, which is the segment-superset test this module
    already had and already tests: a group provides a token when its underscore
    segments CONTAIN all of the token's. That is strict enough to be safe on
    the multi-word tokens (`bar_counter` needs both `bar` and `counter`) and it
    is the single-word ones -- `seat`, `door`, `table` -- that do the work, so
    the exclusions above are load-bearing rather than decorative.

    WHY IT IS NOT A WRITTEN ALIAS TABLE. That would be a fourth vocabulary in a
    module whose whole first page is about not creating one, and it would go
    stale the first time a module renamed a span. This reads the mesh.

    Ties are broken by fewest EXTRA segments, then by SIZE when `size` is given
    -- see `weights` -- then by length and alphabetically. So `bar_table` wins
    over `bar_table_stem` on segments, and `cc_console_face` over
    `cc_console_leg` on triangles.
    """
    seg = set(_segments(token))
    size = size or {}
    best = None
    for n in near_miss(token, names):
        if n in claimed:
            continue
        body = n.partition(PLACE_SEP)[2] or n
        s = _segments(body)
        if any(x in _ALIAS_NEVER for x in s):
            continue
        key = (len(set(s) - seg), -size.get(n, 0), len(n), n)
        if best is None or key < best[0]:
            best = (key, n)
    return None if best is None else best[1]


def resolve(declared, names, spans=None):
    """token -> the group that provides it, for one place's emitted mesh.

    Exact first, over EVERY token, then aliases -- so a module that builds both
    `prop_table` and `bar_table` gives the prompt to the one the register named,
    and an alias can never steal a group an exact match already owns.

    `spans` is the room's `(name, tri_lo, tri_hi)` list. Passing it is what
    makes an alias land on the console rather than on its leg; without it the
    tiebreak falls back to the name, which is how this got that wrong once.
    """
    out = {}
    have = emitted_tokens(names)
    for k in declared:
        if k in have:
            for p in PREFIXES:
                for n in names:
                    if n == p + k or n.endswith(PLACE_SEP + p + k):
                        out[k] = n
                        break
                if k in out:
                    break
    claimed = set(out.values())
    size = weights(spans) if spans else None
    for k in declared:
        if k in out:
            continue
        a = alias_for(k, names, claimed, size)
        if a is not None:
            out[k] = a
            claimed.add(a)
    return out


def resolve_place(schema, profile, place, geom=None):
    """Which of one place's declared interactables its own mesh provides.

    Builds through `deck.room_geometry`, which is the SAME entry point the
    assembler and the collision builder use -- so this cannot report on a room
    that is not the one that ships. Calling `rooms.build` directly here would
    have said the Zocalo emits nothing, which is true of `rooms.build` and not
    of the Zocalo.
    """
    import deck as D                                             # noqa: PLC0415
    want = tuple(place.get("interacts") or ())
    if geom is None:
        v, t, g, used = D.room_geometry(schema, profile, place)
    else:
        v, t, g, used = geom
    names = sorted({n for n, _lo, _hi in g})
    got = resolve(want, names, g)
    exact = emitted_tokens(names)
    hit = tuple(k for k in want if k in got)
    miss = tuple(k for k in want if k not in got)
    return {
        "key": place["key"],
        "module": place.get("module") or "",
        "built": used,
        "declared": want,
        "resolved": hit,
        # HOW it resolved, not just that it did. An alias is content the module
        # built under its own name; an exact hit is content built to the
        # register's. Collapsing the two would hide the 26 that were only ever
        # a naming mismatch behind the 61 that were genuinely absent.
        "alias": {k: v for k, v in got.items() if k not in exact},
        "unresolved": miss,
        "near": {k: near_miss(k, names)[:3] for k in miss
                 if near_miss(k, names)},
        "groups": len(names),
    }


def audit(keys=None, progress=None):
    """Resolve every declared interactable on every place. Slow and honest."""
    import interior as it                                        # noqa: PLC0415
    schema, profile = it.load()
    rows = []
    places = [p for p in dr.PLACES
              if keys is None or p["key"] in keys]
    for i, p in enumerate(places):
        try:
            rows.append(resolve_place(schema, profile, p))
        except Exception as e:                                   # noqa: BLE001
            rows.append({"key": p["key"], "module": p.get("module") or "",
                         "built": "ERROR", "declared":
                         tuple(p.get("interacts") or ()), "resolved": (),
                         "unresolved": tuple(p.get("interacts") or ()),
                         "near": {}, "groups": 0,
                         "error": f"{type(e).__name__}: {str(e)[:90]}"})
        if progress:
            progress(i + 1, len(places), rows[-1])
    return rows


CACHE = os.path.join(ROOT, "docs", "interact-audit.json")

# What the audit read when it was last rebuilt, and what CI holds the line at.
#
# THE BASELINE IS NOW THE BAR. It was a ratchet -- 259 of 357, recorded as a
# shortfall CI could watch so it stayed a number instead of becoming a paragraph
# in STATE.md that nobody recomputes. In session 4d it closed: every one of the
# 357 declared interactables resolves to a group the place actually emits, on
# all 125 places that declare any, bespoke-composed and generic alike.
#
# So a drop here is a REGRESSION rather than an unfinished job, and `--audit`
# -- the assertion that was written to fail -- passes. Keep it that way: a new
# register row with no prop is now the only way to move this number, and it
# should fail the moment it is added.
#
# `--gate --rebuild` re-runs the whole audit, because a gate that reads a
# committed artefact and cannot rebuild it can only say whether the FILE passes,
# never whether the file still describes the code.
BASELINE = {"declared": 357, "resolved": 357, "places_all": 125,
            "places_none": 0}


def load_audit(path=CACHE):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def tally(rows):
    """The four numbers `BASELINE` holds, plus the near/absent split."""
    near = absent = 0
    for r in rows:
        for k in r["unresolved"]:
            if (r.get("near") or {}).get(k):
                near += 1
            else:
                absent += 1
    have = [r for r in rows if r["declared"]]
    return {
        "declared": sum(len(r["declared"]) for r in rows),
        "resolved": sum(len(r["resolved"]) for r in rows),
        "places_all": sum(1 for r in have if not r["unresolved"]),
        "places_none": sum(1 for r in have if not r["resolved"]),
        "alias": sum(len(r.get("alias") or {}) for r in rows),
        "near": near, "absent": absent, "places": len(have),
    }


# ---------------------------------------------------------------------------
# The sidecar the runtime reads
# ---------------------------------------------------------------------------
def sidecar(names, spans=None, hour=13.0, day=0):
    """`godot/scripts/interact.gd`'s half of the contract, as plain data.

    ONE SOURCE FOR THE VERB. The alternative is a copy of the two tables above
    in GDScript, which is the exact defect this repository has now paid for
    three times -- the door decision made in the render and again in the shell,
    the corridor profile written down instead of measured. The engine gets a
    list of `{group, place, token, verb, pressable}` derived here and reads no
    tables of its own.
    """
    names = sorted(set(names))
    out = []
    seen = set()
    for n in names:
        r = provides(n)
        if r is None:
            continue
        place, tok, verb = r
        seen.add(n)
        out.append({"group": n, "place": place, "token": tok, "verb": verb,
                    "pressable": verb in PRESSABLE,
                    "responds": verb in RESPONDS,
                    "label": tok.replace("_", " "),
                    "text": read_text(place, tok, hour, day),
                    "live": tok in LIVE_READ})
    # AND THE ONES THE MODULES NAMED THEMSELVES. `alias_for` needs to know what
    # a place DECLARED, which a group name alone does not carry -- so the names
    # are grouped by the place prefix `deck.build_deck` puts on them and the
    # register is asked. A room's own unprefixed mesh has no place to look up
    # and gets exact matching only, which is what `resolve_place` wants and
    # what the self-test's round-trip asserts.
    byplace = {}
    for n in names:
        if PLACE_SEP in n:
            byplace.setdefault(n.partition(PLACE_SEP)[0], []).append(n)
    decl = {p["key"]: tuple(p.get("interacts") or ()) for p in dr.PLACES}
    for key, group in sorted(byplace.items()):
        for tok, n in sorted(resolve(decl.get(key, ()), group,
                                     spans).items()):
            if n in seen:
                continue
            seen.add(n)
            verb = verb_of(tok)
            out.append({"group": n, "place": key, "token": tok, "verb": verb,
                        "pressable": verb in PRESSABLE,
                        "responds": verb in RESPONDS,
                        "label": tok.replace("_", " "),
                        "text": read_text(key, tok, hour, day),
                        "live": tok in LIVE_READ})
    return out


# ---------------------------------------------------------------------------
_TOKENS = frozenset(tokens())


def _check_total():
    """Every declared interactable gets a verb, through a named rule."""
    bad = []
    for t in tokens():
        try:
            v = verb_of(t)
        except KeyError as e:
            bad.append(f"{t}: {e}")
            continue
        if v not in VERBS:
            bad.append(f"{t}: verb {v!r} is not in VERBS")
    return bad


def _check_minimal():
    """No override may be redundant, and none may be dead.

    THE ASSERTION THAT KEEPS THE TABLE HONEST. Without it `_HEAD_VERB` is a
    place to write opinions: an entry that changes nothing costs nothing to add
    and reads like a decision. With it, an entry has to change at least one of
    the 99 tokens' verbs or the self-test names it.
    """
    bad = []
    base = {t: verb_of(t) for t in tokens()}
    heads = {head_noun(t) for t in tokens()}
    for h in sorted(_HEAD_VERB):
        if h not in heads:
            bad.append(f"_HEAD_VERB[{h!r}] names a head noun no place declares")
            continue
        keep = _HEAD_VERB.pop(h)
        try:
            changed = [t for t in tokens() if verb_of(t) != base[t]]
        finally:
            _HEAD_VERB[h] = keep
        if not changed:
            bad.append(f"_HEAD_VERB[{h!r}] = {keep!r} is redundant -- the shape "
                       f"rule already gives every token that verb")
    for k in sorted(_KIND_VERB):
        if k not in set(R.PROP_KIND.values()):
            bad.append(f"_KIND_VERB[{k!r}] names a rooms.PROP_KIND nothing uses")
    for k in sorted(set(R.PROP_KIND[t] for t in tokens())):
        if k not in _KIND_VERB:
            bad.append(f"rooms.PROP_KIND {k!r} has no row in _KIND_VERB")
    return bad


def head_collisions():
    """Head nouns whose tokens the SHAPE rule classifies differently.

    These are the places one override cannot be right for both tokens: `bench`
    is a `seat` on a `bench` and a `counter` on a `lab_bench`. Reported rather
    than resolved, because the register's vocabulary is the thing being
    described and smoothing it over would hide that.
    """
    by_head = {}
    for t in tokens():
        by_head.setdefault(head_noun(t), []).append(t)
    out = {}
    for h, ts in sorted(by_head.items()):
        kinds = {R.PROP_KIND[t] for t in ts}
        if len(kinds) > 1:
            out[h] = tuple(sorted(ts))
    return out


def _selftest():
    fails = []

    fails += _check_total()
    fails += _check_minimal()

    # Every verb in VERBS is reached by at least one token. A verb nobody can
    # perform is a row of documentation pretending to be a mechanic.
    reached = set(verb_set())
    for v in VERBS:
        if v not in reached:
            fails.append(f"VERBS[{v!r}] is reached by none of the 99 tokens")

    # -- `provides` round-trips, and REJECTS the things it must -------------
    for t in tokens():
        for g in groups_for(t):
            r = provides(g)
            if r is None or r[1] != t:
                fails.append(f"provides({g!r}) did not round-trip to {t!r}")
            r2 = provides(f"docking_bays{PLACE_SEP}{g}")
            if r2 is None or r2 != ("docking_bays", t, verb_of(t)):
                fails.append(f"provides on the deck form of {g!r} failed")

    # NEGATIVE CONTROLS, each one a thing that has actually appeared in an
    # emitted group list. If any of these returns an interactable the runtime
    # would put a prompt on a person, a light or a machine part.
    for bad in ("docking_bays__npc_seated_4_npc_skin",
                "docking_bays__prop_mp_plant_rail",
                "docking_bays__fix_mp_hazard_frame",
                "bay_elevators__light_deck_channel",
                "customs_north__customs_desk",
                "cc_console_face",
                "prop_", "fix_", "", "prop_not_a_thing"):
        if provides(bad) is not None:
            fails.append(f"provides({bad!r}) returned an interactable and must "
                         f"not -- the runtime would prompt on it")
    # ... and the last of those is the control ON the control: a name that
    # SHOULD resolve must, or the loop above is passing because nothing does.
    if provides("docking_bays__prop_bay_door") is None:
        fails.append("provides() rejects a real interactable -- the negative "
                     "controls above prove nothing")

    # -- ALIASING: the module's own name for a declared interactable --------
    # Each of these is a real emitted group name, and the pair of them is the
    # whole risk: a rule loose enough to see `bar_table` as the declared
    # `table` is loose enough to see `npc_seated` as a seat.
    if alias_for("table", ["bar_table", "bar_table_stem"]) != "bar_table":
        fails.append("alias_for picked the stem over the table -- the "
                     "fewest-extra-segments rank is not working")
    if alias_for("locker", ["dress_mp_prop_locker"]) is not None:
        fails.append("alias_for accepted a MACHINE PART as the object -- a "
                     "prompt would land on a drawer front inside a locker")
    if alias_for("lamp", ["light_pendant_lamp"]) is not None:
        fails.append("alias_for accepted a LIGHT FITTING -- the prompt would "
                     "be on a lamp housing")
    if alias_for("seat", ["npc_seated_4_npc_skin"]) is not None:
        fails.append("alias_for accepted a PERSON as furniture")
    if alias_for("catwalk", ["plant_catwalk", "dress_mp_plant_catwalk"]) \
            != "plant_catwalk":
        fails.append("alias_for did not prefer the real catwalk over the "
                     "machine part of the same name")
    # ... and the control ON those: a name that SHOULD alias must, or the four
    # rejections above prove only that the function returns None.
    if alias_for("customs_desk", ["customs_desk"]) != "customs_desk":
        fails.append("alias_for rejects an exact segment match -- the "
                     "rejections above prove nothing")

    # THE SIZE TIEBREAK FIRES, and it is tested by flipping it. Two names the
    # segment rank cannot separate: whichever carries more triangles wins, and
    # swapping the weights swaps the answer. Without the second half this
    # asserts only that some deterministic order exists.
    _tie = ["cc_console_face", "cc_console_leg"]
    _a = alias_for("console", _tie, size={"cc_console_face": 60,
                                          "cc_console_leg": 120})
    _b = alias_for("console", _tie, size={"cc_console_face": 200,
                                          "cc_console_leg": 120})
    if _a != "cc_console_leg" or _b != "cc_console_face":
        fails.append(f"the size tiebreak does not fire: {_a} / {_b} -- an "
                     f"alias tie is being settled by the name")
    if weights([("a", 0, 10), ("a", 10, 30), ("b", 30, 31)]) != {"a": 30,
                                                                 "b": 1}:
        fails.append("weights() does not total a name's spans")

    # AN ALIAS MAY NEVER STEAL A GROUP AN EXACT MATCH OWNS, and two tokens may
    # never share one group -- either would put two prompts on one object or
    # move a prompt off the thing the register named.
    _r = resolve(("table", "bar_table"), ["prop_table", "bar_table"])
    if _r.get("table") != "prop_table" or _r.get("bar_table") != "bar_table":
        fails.append(f"resolve let an alias take an exact match's group: {_r}")
    _r2 = resolve(("table", "stool"), ["bar_table"])
    if len(set(_r2.values())) != len(_r2):
        fails.append(f"resolve gave one group to two tokens: {_r2}")

    # -- `near_miss` matches on SEGMENTS, not substrings --------------------
    if near_miss("seat", ["npc_seated_4_npc_skin"]):
        fails.append("near_miss matched `seat` inside `seated` -- it is "
                     "substring matching and will report people as furniture")
    if not near_miss("customs_desk", ["customs_desk"]):
        fails.append("near_miss missed an exact segment match")
    if not near_miss("console", ["cc_console_face"]):
        fails.append("near_miss missed `console` inside `cc_console_face`")

    # -- the sidecar carries every pressable verb and no unpressable one ----
    side = sidecar([f"docking_bays{PLACE_SEP}prop_{t}" for t in tokens()])
    if len(side) != len(tokens()):
        fails.append(f"sidecar dropped {len(tokens()) - len(side)} tokens")
    for row in side:
        if row["pressable"] != (row["verb"] in PRESSABLE):
            fails.append(f"sidecar pressable disagrees for {row['token']}")
        if row["verb"] == "tread" and row["pressable"]:
            fails.append("a `tread` row is pressable -- a floor marking would "
                         "get a prompt")
        if row["responds"] and not row["pressable"]:
            fails.append(f"{row['token']} responds and is not pressable -- "
                         f"nothing could ever trigger it")
    for v in RESPONDS:
        if v not in VERBS:
            fails.append(f"RESPONDS names {v!r}, which is not a verb")
        if v not in PRESSABLE:
            fails.append(f"RESPONDS names {v!r}, which nobody can press")

    print(f"interact: {len(tokens())} declared interactables over "
          f"{sum(1 for p in dr.PLACES if p.get('interacts'))} places, "
          f"{len(verb_set())} verbs, {len(_HEAD_VERB)} name overrides")
    coll = head_collisions()
    if coll:
        print(f"          {len(coll)} head-noun collisions (one override "
              f"cannot be right for both): "
              + "; ".join(f"{h}: {'/'.join(v)}" for h, v in coll.items()))
    if fails:
        for f in fails:
            print("  FAIL " + f)
        return 1
    print("          totality, minimality and the negative controls all hold")
    return 0


def _cli(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbs", action="store_true",
                    help="the verb set, its derivation and its collisions")
    ap.add_argument("--audit", action="store_true",
                    help="build every place and report which declared "
                         "interactables resolve to a group it emits (slow)")
    ap.add_argument("--keys", default="",
                    help="comma-separated place keys, for --audit")
    ap.add_argument("--write", action="store_true",
                    help="write the audit to docs/interact-audit.json")
    ap.add_argument("--gate", action="store_true",
                    help="hold the line at BASELINE, from the committed audit")
    ap.add_argument("--rebuild", action="store_true",
                    help="with --gate: re-run the audit instead of reading the "
                         "committed one, so the gate cannot go stale")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.gate:
        if a.rebuild:
            rows = audit()
            with open(CACHE, "w") as f:
                json.dump(rows, f, indent=1)
        else:
            rows = load_audit()
            if rows is None:
                print(f"FAIL  no {CACHE} -- run --audit --write")
                return 1
        got = tally(rows)
        bad = []
        for k, want in BASELINE.items():
            have = got[k]
            worse = have < want if k in ("resolved", "places_all") \
                else have > want
            if have != want:
                bad.append(f"{k}: {have} vs baseline {want}"
                           + ("  WORSE" if worse else "  better -- update "
                              "BASELINE"))
        print(f"interact --gate: {got['resolved']}/{got['declared']} declared "
              f"interactables resolve; {got['places_all']}/{got['places']} "
              f"places resolve all of theirs, {got['places_none']} none")
        print(f"                 {got['alias']} of them under the module's own "
              f"name for the object rather than the register's")
        if got["declared"] > got["resolved"]:
            print(f"                 of the {got['declared'] - got['resolved']}"
                  f" that do not, {got['near']} look like something the room "
                  f"emits and {got['absent']} were never built at all")
        if not a.rebuild:
            print("                 (read from the committed audit; "
                  "--rebuild re-runs it)")
        for b in bad:
            print("  FAIL " + b)
        return 1 if bad else 0

    if a.verbs:
        print(f"{len(tokens())} declared interactables -> {len(verb_set())} "
              f"verbs\n")
        for v, ts in by_verb().items():
            print(f"  {v:8s} {VERBS[v]}")
            print(f"           {len(ts):2d}: " + ", ".join(ts))
        coll = head_collisions()
        print(f"\n  {len(coll)} head nouns whose tokens differ in shape:")
        for h, ts in coll.items():
            print(f"    {h:10s} " + ", ".join(
                f"{t} ({R.PROP_KIND[t]} -> {verb_of(t)})" for t in ts))
        return 0

    if a.audit:
        keys = set(a.keys.split(",")) if a.keys else None

        def prog(i, n, row):
            u = len(row["unresolved"])
            print(f"  [{i:3d}/{n}] {row['key']:26s} {row['built']:8s} "
                  f"{len(row['resolved'])}/{len(row['declared'])} resolved"
                  + (f"  MISSING {', '.join(row['unresolved'])}" if u else ""),
                  flush=True)

        rows = audit(keys, progress=prog)
        got = tally(rows)
        print(f"\n{got['resolved']}/{got['declared']} declared interactables "
              f"resolve to a group the place actually emits")
        print(f"{got['places_all']}/{got['places']} places resolve ALL of "
              f"theirs; {got['places_none']} resolve NONE of theirs")
        print(f"of the {got['declared'] - got['resolved']} that do not, "
              f"{got['near']} ARE built and carry the module's own name "
              f"instead of the register's, and {got['absent']} were never "
              f"built")
        byb = {}
        for r in rows:
            byb.setdefault(r["built"], [0, 0])
            byb[r["built"]][0] += len(r["resolved"])
            byb[r["built"]][1] += len(r["declared"])
        for b, (g, d) in sorted(byb.items()):
            print(f"  built {b:8s} {g:3d}/{d:3d}")
        if a.write:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE, "w") as f:
                json.dump(rows, f, indent=1)
            print(f"wrote {CACHE}")
        # THE ASSERTION, AND IT FAILS. `--audit` is the honest form of the
        # question -- does every declared use resolve -- and the answer today is
        # no, on 98 of 357. `--gate` is the form CI can hold green while that is
        # true; this one is meant to go red until the shortfall is built.
        if got["resolved"] < got["declared"]:
            print(f"\nFAIL  {got['declared'] - got['resolved']} declared "
                  f"interactables resolve to nothing a room emits. A player "
                  f"cannot use what the register says is there.")
            return 1
        return 0

    return _selftest()


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
