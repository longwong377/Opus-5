#!/usr/bin/env python3
"""C&C AS A WATCH FLOOR -- nine desks that read the station and can act on it.

THE COMPLAINT THIS CLOSES is `station/plant_systems.py`'s own opening sentence,
quoted there from `docs/MASTER-PLAN.md` P4a A4a-3: *"C&C has a watch roster and
controls nothing that can break."* Half of that was fixed in 4q -- the plant now
has capacity, load, wear and a way to lose them, and `incident.py` imports it, so
the station CAN break. The other half was not: **nothing in the room did
anything about it.** Checked rather than assumed before this file was written:

    grep -n 'cnc\\|command_control' station/plant_systems.py
    8:drops and lights go out. C&C has a watch roster and controls nothing that

-- one hit, in the complaint. `plant_systems.control_rooms()` reads the
register's `monitoring`/`control` function tags and returns `atmos_monitor` for
air and `waste_control` for waste and **nothing at all for power, water, food or
rotation**; `cnc` is not a control room of any system by that test, because its
declared functions are `station_ops`, `traffic_control` and `defence_command`.
The bridge of the station was outside the plant model entirely.

WHAT A DESK IS, AND WHY THERE ARE NINE
--------------------------------------
A desk is a position on the watch floor with four things: something it WATCHES,
a READING taken from the module that already computes it, a STATE, and an ORDER
it can give. The set is derived, not chosen:

    six   `plant_systems.SYSTEM_KEYS`      power air water food waste rotation
    three `directory.by_key("cnc")` own    station_ops traffic_control
          declared functions                defence_command

and `station/command_control.py` builds **five dais consoles and four pit
consoles**. 6 + 3 = 5 + 4, and that is asserted rather than admired: if a
seventh system is added or the register re-tags the room, the gate fails and
says a desk has no console. A desk with no console is this project's signature
defect (finished machinery nothing reaches) in miniature, so it is made
impossible instead of watched for.

WHERE A DESK SITS IS DERIVED TOO, AND THE DERIVATION IS "HOW LONG HAVE YOU GOT"
------------------------------------------------------------------------------
`TIME_TO_CONSEQUENCE` is, for every desk, the hours between the thing going
wrong and somebody noticing, taken from the module that owns the number:

    power     `plant_systems.survives_h`      0.00 h   no store; a gigawatt
                                                       cannot be put in a tank
    ops       24 / `incident.visible_faults_per_day`   the interval between the
                                                       faults the floor logs
    defence   `npc/security.beat('blue')['period_s']`  a patrol passes a given
                                                       point this often
    traffic   1 / `traffic.rate_per_hour`      the gap to the next arrival
    air       `plant_systems.survives_h`       5.77 h  CO2, not oxygen
    waste     ...                             24.00 h
    water     ...                            720.00 h  L-04's 30-day reserve
    food      ...                            720.00 h
    rotation  ...                                inf   INV-427: not derivable

The five shortest take the dais, fastest at the arc's centre where the reference
frame puts the standing officer, alternating outward; the four longest take the
pit. Nothing about that ordering is a preference and the whole thing falls out
of numbers six other modules already publish. INV-460.

THE THREE STATES ARE `wear_at`'s OWN THREE STATES, SO THERE IS NO NEW THRESHOLD
-------------------------------------------------------------------------------
`plant_systems.wear_at` already distinguishes exactly three plant conditions and
gives each a derived multiplier: spares in hand (1.0), spares gone
(1/CORRECTIVE_SHARE), demand unmet (the roster ceiling). Those are the board's
three lamps:

    NORMAL   the redundancy the station was built with is intact
    CAUTION  `spares < design_spares` -- a margin has been spent
    ALARM    `deficit > 0` -- the plant cannot meet the load NOW

A threshold nobody chose cannot be tuned to make a board look calm. The three
non-plant desks get the same shape from their own modules' boundaries -- no free
berth is ALARM because a ship with nowhere to go is `INC-HOLD` (`traffic`), the
last patrol pair on shift is ALARM because `unpoliced` reaches 1.0.

WHAT THE ROOM DOES WITH IT -- AND THIS IS THE HALF THE OWNER ASKED FOR
-----------------------------------------------------------------------
Four orders, each of which CALLS the function that already implements it. Not
one of them re-derives anything:

    isolate/restore   `plant_systems.set_offline`  -- and because `set_offline`
                      clears `incident._LAM`, the incident rates for the whole
                      station move on the next tick. This is the order that has
                      an effect a player meets: `--effect` measures it.
    shed              `plant_systems.shed_plan`    -- which places go dark, how
                      many stops of light, how many dBA of machinery, how many
                      people standing in them
    dispatch          `plant_systems.repair_day`   -- the corrective queue, and
                      whether it closes

AND THE ORDER IS A STATION FACT, NOT A FUNCTION CALL. `station/generated/cnc/
orders.json` is the standing-order log: what C&C has done that has not been
undone. `station/command_control.py` reads it when it builds the room, so the
console registers, the annunciator over the window and the pit's alarm bar all
show the state the orders produced -- which is what makes the picture change
when the station breaks. `--engine-gate` renders both frames and diffs them.

THE COST -- AND THE FIRST DRAFT OF THIS PARAGRAPH SAID "FREE" AND WAS WRONG
----------------------------------------------------------------------------
It was written as *"the nominal path is free"* before it was measured. Measured,
in a cold process: **`command_control.command_control()` goes from 0.03 s to
14.85 s on its first call**, and the split is

    plant_systems.survives_h('power')   6.83 s   the demand model warming up
    incident.visible_faults_per_day     3.46 s   walks machine_instances over
                                                 the whole register
    npc/security.beat('blue')           2.67 s   memoised here; it is not
                                                 memoised upstream and was
                                                 being asked twice
    imports, traffic, directory         ~1.9 s

Subsequent builds in the same process are 0.03 s, so the cost is **once per
process**, and it lands on `deck.py --sweep`, `rooms.py --footprint` (23 min),
`variety.py`, `test_materials_layer3.py` and every render of this room. On the
long gates that is under 2%; on the short ones it is not nothing, and it is
recorded here rather than left to be rediscovered as "the room got slow".

What IS free is the STATE at nominal. With no standing order every plant desk is
NORMAL by construction -- `spares == design_spares` is the definition of nominal
-- so `state_of_room()` short-circuits the six plant desks instead of asking
them. `--gate` asserts that shortcut equals the long way round at 03, 08, 13 and
20, with a control that isolates the station's only water plant and watches the
shortcut NOT be taken. A fast path with no check on it is a second copy of a
computed number; this one has the check.

The remaining 14.85 s buys the three register desks, which genuinely change
through the day, and the seat map. Making it free would mean either freezing the
seat map on disk (a second copy of a computed number) or choosing the seating
derivation for its speed, which is choosing a number for convenience. Neither is
worth 14 s.

Run: python3 station/cnc_ops.py --board          the nine desks, now
     python3 station/cnc_ops.py --board --hour 3
     python3 station/cnc_ops.py --order isolate:fusion_core,reactor_hall
     python3 station/cnc_ops.py --order restore
     python3 station/cnc_ops.py --effect          what the order did, measured
     python3 station/cnc_ops.py --gate            THE GATE
     python3 station/cnc_ops.py --engine-gate     THE ENGINE A/B
"""

import json
import math
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_ROOT = os.path.dirname(_HERE)

# THE SAME GUARD `plant_systems` CARRIES, AND FOR THE SAME REASON. Run as a
# script this module is `__main__`, so anything that does `import cnc_ops`
# during the run would build a SECOND COPY with its own order cache -- which is
# exactly the defect that made `plant_systems`' first patch appear not to work
# ("two copies of a state that has to be one"). `command_control` imports this
# module by name, and `--engine-gate` runs `command_control`.
if __name__ == "__main__":                                   # pragma: no cover
    sys.modules.setdefault("cnc_ops", sys.modules["__main__"])

ORDERS = os.path.join(_ROOT, "station", "generated", "cnc", "orders.json")

NORMAL, CAUTION, ALARM = "NORMAL", "CAUTION", "ALARM"
RUNG = {NORMAL: 0, CAUTION: 1, ALARM: 2}

# The register's own three function tags for this room, in the order the
# register lists them, mapped to the desk key each becomes. The mapping is
# 1:1 and exists only so a desk key is a word rather than a tag.
REGISTER_DESKS = {
    "station_ops": "ops",
    "traffic_control": "traffic",
    "defence_command": "defence",
}

_ONCE = {}


def _memo(key, fn):
    if key not in _ONCE:
        _ONCE[key] = fn()
    return _ONCE[key]


def _ps():
    import plant_systems as ps                                # noqa: PLC0415
    return ps


def _dr():
    import directory as dr                                    # noqa: PLC0415
    return dr


# ===========================================================================
# 1.  THE DESK SET, AND WHERE EACH ONE SITS
# ===========================================================================
def desk_keys():
    """Every desk on the floor. Derived; never written down.

    Order is `plant_systems.SYSTEM_KEYS` then the register's own function list,
    so it is stable without being sorted -- a sort would hide a register change
    that reordered the tags, and the seating derivation below is what decides
    position anyway.
    """
    q = _dr().by_key("cnc")
    reg = [REGISTER_DESKS[f] for f in q["functions"] if f in REGISTER_DESKS]
    return tuple(_ps().SYSTEM_KEYS) + tuple(reg)


def watches(desk):
    """What this desk watches: the places whose state it is responsible for."""
    ps = _ps()
    if desk in ps.SYSTEM_KEYS:
        return tuple(ps.units(desk)) + tuple(ps.control_rooms(desk))
    if desk == "traffic":
        return tuple(p["key"] for p in _dr().PLACES
                     if {"docking", "traffic_control", "berthing"}
                     & set(p["functions"]))
    if desk == "defence":
        return tuple(p["key"] for p in _dr().PLACES
                     if {"law_enforcement", "defence_command", "fire_control"}
                     & set(p["functions"]))
    return ("cnc",)


def time_to_consequence_h(desk):
    """Hours between this desk's subject going wrong and somebody noticing.

    THE SEATING RULE, and every value is another module's published number.
    Memoised per desk because `visible_faults_per_day` is ~3.5 s and the answer
    does not depend on the hour: it is a property of the plant and the roster,
    not of the clock. `traffic` is the one that genuinely varies through the day
    and is taken at the ARRIVAL PEAK, because a berth plan is made for the busy
    hour and not for 03:00.
    """
    def compute():
        ps = _ps()
        if desk in ps.SYSTEM_KEYS:
            # The buffer with the plant stopped. `survives_h(None)` means "all
            # of its units offline", which is the question the seating asks.
            return float(ps.survives_h(desk, 13.0))
        if desk == "ops":
            import incident as ic                             # noqa: PLC0415
            return 24.0 / max(1e-9, ic.visible_faults_per_day())
        if desk == "defence":
            return float(_beat()["period_s"]) / 3600.0
        if desk == "traffic":
            import traffic as tr                              # noqa: PLC0415
            peak = max(tr.rate_per_hour(float(h)) for h in range(24))
            return 1.0 / max(1e-9, peak)
        raise KeyError(desk)                                  # pragma: no cover
    return _memo(("ttc", desk), compute)


def seating():
    """(dais, pit) -- which desk sits at which console index.

    `dais` is indexed the way `command_control.command_control` walks its arc,
    k = 0 at one end and k = CONSOLE_N-1 at the other, so the CENTRE index is
    the officer's own position in the reference frame. The fastest desk takes
    it and the rest alternate outward, which puts the two slowest of the five at
    the ends of the arc where a standing officer has to turn to read them.

    `pit` is indexed in the order `command_control` emits its pit consoles:
    (sx, j) for sx in (-1, +1) and j in range(PIT_CONSOLE_N // 2).
    """
    def compute():
        import command_control as cc                          # noqa: PLC0415
        keys = sorted(desk_keys(), key=lambda d: (time_to_consequence_h(d), d))
        n_dais, n_pit = cc.CONSOLE_N, cc.PIT_CONSOLE_N
        if len(keys) != n_dais + n_pit:                       # pragma: no cover
            raise SystemExit(
                "cnc_ops: %d desks against %d consoles -- a desk with no "
                "console is machinery with no caller. Desks: %s"
                % (len(keys), n_dais + n_pit, ", ".join(keys)))
        fast, slow = keys[:n_dais], keys[n_dais:]
        mid = n_dais // 2
        # centre-out: 0 -> mid, 1 -> mid-1, 2 -> mid+1, 3 -> mid-2, ...
        order = [mid]
        for s in range(1, n_dais):
            j = mid - (s + 1) // 2 if s % 2 else mid + s // 2
            order.append(j)
        order = [j for j in order if 0 <= j < n_dais]
        dais = [None] * n_dais
        for d, j in zip(fast, order):
            dais[j] = d
        # Any index the walk above missed (only possible for an even
        # CONSOLE_N) is filled left to right, so the mapping is total.
        spare = [d for d in fast if d not in dais]
        for j in range(n_dais):                               # pragma: no cover
            if dais[j] is None and spare:
                dais[j] = spare.pop(0)
        return tuple(dais), tuple(slow)
    return _memo("seating", compute)


def desk_at(where, index):
    """`where` is "dais" or "pit"; `index` is the console's own index."""
    dais, pit = seating()
    return (dais if where == "dais" else pit)[index]


# ===========================================================================
# 2.  THE STANDING ORDERS -- what C&C has done that has not been undone
# ===========================================================================
def read_orders(path=None):
    """The standing-order log. `{}` when there is none, which is nominal.

    NAMED, NOT SWALLOWED, on a malformed file: a board that quietly reverted to
    nominal because the log would not parse is a bridge whose alarms are off
    for a reason nobody can see -- the same class as `boot._collapses`' empty
    schedule looking like a quiet day on the station.
    """
    p = path or ORDERS
    if not os.path.exists(p):
        return {}
    try:
        with open(p) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception as e:                                     # noqa: BLE001
        print("cnc_ops: standing orders unreadable (%s: %s) -- the board is "
              "showing NOMINAL and should not be trusted"
              % (type(e).__name__, e), file=sys.stderr)
        return {}


def write_orders(d, path=None):
    p = path or ORDERS
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(d, f, indent=1, sort_keys=True)
    return p


def offline_units(path=None):
    """The plant units C&C has isolated. A tuple, sorted, possibly empty."""
    o = read_orders(path)
    return tuple(sorted(str(u) for u in (o.get("isolate") or ()) if u))


def apply_orders(path=None):
    """Push the standing orders into `plant_systems`. Returns what went down.

    THE ONE WRITER'S ONE CALLER. `plant_systems.set_offline` says of itself
    "THIS IS THE ONLY WRITER" and had exactly two callers before this file, both
    inside its own gate. This is the caller on the path a build takes.
    """
    off = offline_units(path)
    _ps().set_offline(*off)
    return off


def order_isolate(units, path=None):
    """C&C takes plant units out of service. The order that has consequences."""
    ps = _ps()
    known = {u for s in ps.SYSTEM_KEYS for u in ps.units(s)}
    bad = [u for u in units if u not in known]
    if bad:
        raise SystemExit("cnc_ops: no such plant unit: %s (known: %s)"
                         % (", ".join(bad), ", ".join(sorted(known))))
    o = read_orders(path)
    o["isolate"] = sorted(set(o.get("isolate") or ()) | set(units))
    write_orders(o, path)
    return apply_orders(path)


def order_restore(path=None):
    o = read_orders(path)
    o["isolate"] = []
    write_orders(o, path)
    return apply_orders(path)


def order_shed(hour, path=None):
    """The load-shed order. Rows of (place, share, stops, dBA, heads)."""
    apply_orders(path)
    return _ps().shed_plan(float(hour), limit=0)


def order_dispatch(hours=24, path=None):
    """Send the corrective crews at the standing order's state for a day.

    Returns (peak_backlog, end_backlog) -- and the property that matters is
    whether it CLOSES, which `plant_systems.repair_day` states as its own.
    """
    off = apply_orders(path)
    peak, end, _series = _ps().repair_day(offline=list(off), hours=hours)
    return peak, end


# ===========================================================================
# 3.  THE READING -- every line carries the module that computed it
# ===========================================================================
class _with_offline:
    """Hold `plant_systems.OFFLINE` at a stated value for the duration.

    THE BOARD READS THE PLANT STATE, NOT A COPY OF IT, and the first version of
    this file got that wrong in a way worth recording: `deficit`, `capacity` and
    `spares` all take an explicit `offline`, so the six plant desks honoured the
    standing order -- and `wear_at`, `fault_arrivals_per_hour` and
    `corrective_capacity_per_hour` do NOT, they read the module global. So with
    two generating units isolated the POWER desk read ALARM and the OPS desk on
    the next console read `WEAR x1.00`. **Two consoles in one room disagreeing
    about whether the station was broken.**

    The cure is not to pass `off` further down -- `plant_systems`' own docstring
    explains why the global exists (27 of 30 incident classes ignore a world
    parameter). It is to make "the plant state" one thing while the board is
    being read, which is what a real watch floor is looking at.
    """

    def __init__(self, off):
        self.off = tuple(off)

    def __enter__(self):
        ps = _ps()
        self.saved = tuple(sorted(ps.OFFLINE))
        ps.set_offline(*self.off)
        return self

    def __exit__(self, *_):
        _ps().set_offline(*self.saved)
        return False


def _plant_state(desk, hour, off):
    ps = _ps()
    if ps.deficit(desk, hour, off) > 0.0:
        return ALARM
    if ps.spares(desk, hour, off) < ps.design_spares(desk):
        return CAUTION
    return NORMAL


def _plant_lines(desk, hour, off):
    ps = _ps()
    s = ps.BY_KEY[desk]
    d = ps.demand(desk, hour)
    cap = ps.capacity(desk, off)
    up = [u for u in ps.units(desk) if u not in set(off)]
    # THE BUFFER IS THIS SYSTEM'S OWN PLANT STOPPED, always -- `survives_h`
    # with the standing order instead would answer "how long does AIR last if
    # the two REACTORS are down", which is `inf` and is a true answer to a
    # question no watch officer asks. The desk shows the constant it is
    # responsible for; the deficit line below shows what is happening now.
    buf = ps.survives_h(desk, hour, None)
    lines = [
        "LOAD %.4g %s   CAP %.4g   MARGIN %+.1f%%"
        % (d, s.unit, cap, 100.0 * ps.margin(desk, hour, off)),
        "UNITS %d/%d up   SPARES %+d (design %+d)"
        % (len(up), len(ps.units(desk)), ps.spares(desk, hour, off),
           ps.design_spares(desk)),
    ]
    if ps.deficit(desk, hour, off) > 0.0:
        lines.append("DEFICIT %.1f%%   BUFFER %s"
                     % (100.0 * ps.deficit(desk, hour, off), _hfmt(buf)))
    else:
        lines.append("BUFFER %s with its own plant stopped" % _hfmt(buf))
    return lines


def _hfmt(h):
    if h == float("inf"):
        return "indefinite"
    if h >= 48.0:
        return "%.0f d" % (h / 24.0)
    return "%.2f h" % h


def _traffic_reading(hour):
    import traffic as tr                                       # noqa: PLC0415
    b = tr.berths_in_use(float(hour))
    bays = tr.bay_count()
    used = int(b.get("bay", 0))
    free = bays - used
    rate = tr.rate_per_hour(float(hour))
    st = ALARM if free <= 0 else (CAUTION if free * 1.0 < rate else NORMAL)
    return st, [
        "BERTHS %d/%d in use, %d free   STANDOFF %d   MOORED %d"
        % (used, bays, free, int(b.get("standoff", 0)), int(b.get("moored", 0))),
        "ARRIVALS %.2f/h   MEAN STAY %.1f h" % (rate, tr.mean_stay_h()),
        ("NO FREE BERTH -- the stack forms (INC-HOLD)" if free <= 0 else
         "%.1f h of berth cover at this arrival rate" % (free / max(1e-9, rate))),
    ]


def _beat():
    """`security.beat('blue')`, once. IT IS 2.67 s AND IT IS NOT MEMOISED
    UPSTREAM -- called from both the seating derivation and the defence desk's
    reading, it was a third of this module's cold-start cost on its own. The
    beat is a property of the ring's circumference and the officer's mass; it
    does not change with the hour, so nothing is lost by asking once."""
    from npc import security as sec                            # noqa: PLC0415
    return _memo("beat", lambda: sec.beat("blue"))


def _defence_reading(hour):
    from npc import security as sec                            # noqa: PLC0415
    import incident as ic                                      # noqa: PLC0415
    on = sec.on_duty(float(hour))
    pairs = sec.roving_pairs(float(hour))
    beat = _beat()
    unp = ic.unpoliced("cnc", float(hour))
    st = ALARM if pairs <= 0 else (CAUTION if unp >= 0.5 else NORMAL)
    return st, [
        "FORCE %d of %d on duty   ROVING %d pairs   POSTED %d"
        % (on, sec.force_total(), pairs, sec.posted_officers()),
        "BLUE BEAT %.1f m, a pair passes every %.0f s"
        % (beat["circumference_m"], beat["period_s"]),
        "UNPOLICED SHARE HERE %.2f" % unp,
    ]


def _ops_reading(hour, off):
    """The watch's own desk: who is on it, and what the floor is logging."""
    ps = _ps()
    from npc import schedule as sch                            # noqa: PLC0415
    import incident as ic                                      # noqa: PLC0415
    watch = sch.role_on_duty("command", float(hour))
    faults = ps.fault_arrivals_per_hour(float(hour))
    cap = ps.corrective_capacity_per_hour(float(hour))
    wear = max(ps.wear_at(k, float(hour)) for k in ps.plant_places()) \
        if ps.plant_places() else 1.0
    st = ALARM if faults > cap else (CAUTION if wear > 1.0 else NORMAL)
    return st, [
        "WATCH %d on the floor (schedule.role_on_duty, three watches)" % watch,
        "FAULTS %.1f/h arriving   CREWS %.1f/h closing   WEAR x%.2f"
        % (faults, cap, wear),
        "REGISTER %d faults/day at design (incident.visible_faults_per_day)"
        % round(_memo("vfpd", ic.visible_faults_per_day)),
    ]


def desk_reading(desk, hour, off=None, path=None):
    """(state, lines) for one desk. Nothing here computes a station fact."""
    ps = _ps()
    off = tuple(offline_units(path)) if off is None else tuple(off)
    with _with_offline(off):
        if desk in ps.SYSTEM_KEYS:
            return _plant_state(desk, float(hour), off), \
                _plant_lines(desk, float(hour), off)
        if desk == "traffic":
            return _traffic_reading(hour)
        if desk == "defence":
            return _defence_reading(hour)
        return _ops_reading(hour, off)


def board(hour=13.0, off=None, path=None):
    """The whole floor: an ordered list of desk rows, dais first.

    Each row is a dict a console can be built from and a `read` verb can be
    printed from -- `{desk, where, index, state, title, lines, ttc_h}`.

    `path` NAMES THE ORDER LOG, and it is here because its absence was a bug
    the gate caught: `--gate` writes its orders to a temp file so it cannot
    disturb the station's real ones, `room_layout(hour, tmp)` honoured that and
    `board(hour)` did not -- so the same run had `room_layout` reporting ALARM
    and `board` reporting NORMAL on the identical plant state, and four checks
    failed with the two answers printed side by side. A test fixture that only
    reaches half the readers is worse than no fixture, because the half it
    misses reads the REAL state and looks like a disagreement about the model.
    """
    dais, pit = seating()
    off = tuple(offline_units(path)) if off is None else tuple(off)
    rows = []
    with _with_offline(off):
        for where, seq in (("dais", dais), ("pit", pit)):
            for i, d in enumerate(seq):
                st, lines = desk_reading(d, hour, off)
                rows.append({"desk": d, "where": where, "index": i,
                             "state": st, "title": d.upper(), "lines": lines,
                             "ttc_h": time_to_consequence_h(d)})
    return rows


def board_text(hour=13.0, off=None, desk=None, path=None):
    """What the `tactical_display` in this room SAYS -- the `read` verb's text.

    `cnc` declares `("console", "comms_channel", "tactical_display",
    "blast_door")` in `directory.PLACES`, and `interact.read_text` returns ""
    for `tactical_display` and `console` today, so a player pressing E on the
    bridge's own tactical display gets the label and nothing else. This is the
    string that closes it; the four-line patch that calls it is in
    `--patch`, because `station/interact.py` is not this module's to edit.
    """
    rows = board(hour, off, path)
    if desk:
        rows = [r for r in rows if r["desk"] == desk]
    out = ["BABYLON 5 -- COMMAND AND CONTROL   %02d:%02d STATION"
           % (int(hour) % 24, int(round((float(hour) % 1.0) * 60)) % 60)]
    worst = worst_state(rows)
    out.append("BOARD %s" % worst)
    for r in rows:
        out.append("%-8s %-7s %s" % (r["title"], r["state"], r["lines"][0]))
    return "\n".join(out)


def worst_state(rows=None, hour=13.0, off=None, path=None):
    rows = board(hour, off, path) if rows is None else rows
    return max((r["state"] for r in rows), key=lambda s: RUNG[s],
               default=NORMAL)


# ===========================================================================
# 4.  WHAT THE ROOM IS BUILT FROM -- the cheap path, and its check
# ===========================================================================
def state_of_room(hour=13.0, path=None):
    """`{desk: state}` for `command_control.py` to build the consoles from.

    THE SHORTCUT AND WHY IT IS SAFE. With no standing order every plant desk is
    NORMAL by the definition of nominal (`spares == design_spares`), so the
    board cannot be anything else -- and computing it anyway would put ~4 s of
    `incident` import into every `deck.py --sweep`, `rooms.py --footprint` and
    `variety.py` run that builds this room. The three register desks are NOT
    shortcut: `traffic` genuinely changes through the day and `defence` changes
    with the watch, and those are cheap.

    `--gate` asserts this function equals `board()` desk for desk at four hours,
    so the shortcut is checked rather than believed.
    """
    off = offline_units(path)
    if not off:
        ps_keys = ("power", "air", "water", "food", "waste", "rotation")
        out = {k: NORMAL for k in ps_keys}
        for d in ("traffic", "defence", "ops"):
            try:
                out[d] = desk_reading(d, hour, ())[0]
            except Exception:                                  # noqa: BLE001
                out[d] = NORMAL
        return out
    return {r["desk"]: r["state"] for r in board(hour, off, path)}


def room_layout(hour=13.0, path=None):
    """Everything `command_control.py` needs: seat map + state, one call.

    Returns `{"dais": (desk, ...), "pit": (desk, ...), "state": {...},
              "worst": STATE, "offline": (unit, ...)}`.

    FAILS SOFT AND SAYS SO. A geometry builder that raised because the plant
    model would not import would take the whole station's build down for a
    board; it returns the nominal layout and prints which of the two it is,
    so a frame can never silently be the wrong one.
    """
    off = offline_units(path)
    try:
        dais, pit = seating()
        st = state_of_room(hour, path)
    except Exception as e:                                     # noqa: BLE001
        print("cnc_ops: no board (%s: %s) -- C&C is being built with every "
              "desk dark, which is NOT the same as every desk normal"
              % (type(e).__name__, e), file=sys.stderr)
        return {"dais": (), "pit": (), "state": {}, "worst": None,
                "offline": off}
    worst = max((st[d] for d in list(dais) + list(pit)),
                key=lambda s: RUNG[s], default=NORMAL)
    return {"dais": dais, "pit": pit, "state": st, "worst": worst,
            "offline": off}


# ===========================================================================
# 5.  THE PATCH `station/interact.py` NEEDS -- printed, not applied
# ===========================================================================
PATCH = '''\
--- station/interact.py
+++ station/interact.py
@@ LIVE_READ
 LIVE_READ = ("info_board", "arrivals_board", "departure_board", "monitor_wall",
              "public_information_monitor", "comms_channel", "babcom_terminal",
-             "isn_screen", "menu_display", "price_board")
+             "isn_screen", "menu_display", "price_board",
+             # The bridge's own board. It is a function of the hour AND of the
+             # standing orders, which is the strongest `live` case in the set.
+             "tactical_display", "console")
@@ read_text -- INSERTED ABOVE the `level_plaque` branch, not below it
+        elif t in ("tactical_display", "console") and place_key == "cnc":
+            # WHAT THE WATCH FLOOR IS SHOWING. Derived in
+            # `station/cnc_ops.py::board_text` from `plant_systems`,
+            # `traffic`, `npc/security` and `npc/schedule`; not one line of it
+            # is written here, and with no standing order every plant desk
+            # reads NORMAL because that is what nominal means.
+            import cnc_ops                                     # noqa: PLC0415
+            out = cnc_ops.board_text(hour=hour)
         elif t == "level_plaque" and q is not None:
             out = ("%s\\n%s ring %d deck %d" % (q["name"], q["sector"].upper(),
                                                 q["ring"], q["deck"]))

AND ONE CAVEAT THIS PATCH CANNOT CARRY ITSELF: `interact.sidecar()` bakes the
string at export time, so the board a player reads is the board at the bake
hour and at the bake's standing orders. `LIVE_READ` is exactly the flag that
says which strings a runtime should refresh, which is why the token is added to
it -- but nothing refreshes any of the ten tokens already in that tuple either.
'''


# ===========================================================================
# 6.  REPORT
# ===========================================================================
def report(out=print, hour=13.0):
    rows = board(hour)
    off = offline_units()
    out("C&C WATCH FLOOR -- %02d:00 station, standing orders: %s"
        % (int(hour) % 24, ", ".join(off) if off else "none"))
    out("BOARD %s" % worst_state(rows))
    out("")
    out("  %-4s %-2s %-8s %-8s %-10s %s"
        % ("pos", "#", "desk", "state", "t-to-cons", "reading"))
    for r in rows:
        out("  %-4s %-2d %-8s %-8s %-10s %s"
            % (r["where"], r["index"], r["desk"], r["state"],
               _hfmt(r["ttc_h"]), r["lines"][0]))
        for ln in r["lines"][1:]:
            out("  %-4s %-2s %-8s %-8s %-10s %s" % ("", "", "", "", "", ln))
    out("")
    ps = _ps()
    plan = ps.shed_plan(float(hour), limit=6)
    if plan:
        heads, n = ps.affected_heads(float(hour))
        out("SHED ORDER STANDING -- %d places, %s people in them" % (n, f"{heads:,}"))
        for k, f, st, db, hd in plan:
            out("  %-22s %5.1f%% of fittings  %-22s %6.1f dBA  %6d present"
                % (k, 100.0 * f, ps._stopfmt(st), db, hd))
    else:
        out("SHED ORDER -- none; the power desk meets its load at this hour")


# ===========================================================================
# 7.  THE GATE
# ===========================================================================
_FAILED = []


def check(cond, what, detail="", out=print):
    if cond:
        out("  ok   %s" % what)
    else:
        _FAILED.append(what)
        out("  FAIL %s%s" % (what, ("  -- " + detail) if detail else ""))
    return bool(cond)


def gate(out=print):                                          # noqa: C901
    """Everything this module claims, measured, with the controls that fire."""
    del _FAILED[:]
    ps = _ps()
    tmp = os.path.join(_ROOT, "station", "generated", "cnc", "gate_orders.json")
    if os.path.exists(tmp):
        os.remove(tmp)

    out("--- 1. the desk set is derived and every desk has a console ---")
    keys = desk_keys()
    import command_control as cc
    check(len(keys) == cc.CONSOLE_N + cc.PIT_CONSOLE_N,
          "%d desks for %d consoles" % (len(keys),
                                        cc.CONSOLE_N + cc.PIT_CONSOLE_N),
          ", ".join(keys), out)
    check(set(ps.SYSTEM_KEYS) <= set(keys),
          "every plant system has a desk", "", out)
    q = _dr().by_key("cnc")
    check(all(REGISTER_DESKS[f] in keys for f in q["functions"]
              if f in REGISTER_DESKS),
          "every function the register declares for this room has a desk",
          str(q["functions"]), out)
    dais, pit = seating()
    check(len(set(dais) | set(pit)) == len(keys)
          and None not in dais and None not in pit,
          "the seat map is total and one-to-one",
          "dais %s pit %s" % (dais, pit), out)

    out("--- 2. the seating is TIME TO CONSEQUENCE, and it is measured ---")
    ttc = {d: time_to_consequence_h(d) for d in keys}
    for d in sorted(ttc, key=lambda k: ttc[k]):
        out("       %-8s %s" % (d, _hfmt(ttc[d])))
    check(max(ttc[d] for d in dais) <= min(ttc[d] for d in pit),
          "the dais holds the five fastest desks, the pit the four slowest",
          "dais max %s, pit min %s" % (_hfmt(max(ttc[d] for d in dais)),
                                       _hfmt(min(ttc[d] for d in pit))), out)
    mid = cc.CONSOLE_N // 2
    check(ttc[dais[mid]] == min(ttc.values()),
          "the officer's own console is the fastest desk on the station",
          "%s at %s" % (dais[mid], _hfmt(ttc[dais[mid]])), out)
    # A DERIVATION IS NOT A DERIVATION IF ITS INPUT CANNOT MOVE IT. Rebuild the
    # order with power's buffer taken to a day and the seat must change hands.
    _saved = dict(_ONCE)
    try:
        _ONCE.clear()
        _ONCE[("ttc", "power")] = 999.0
        _ONCE.update({k: v for k, v in _saved.items()
                      if k != "seating" and k != ("ttc", "power")})
        d2, p2 = seating.__wrapped__() if hasattr(seating, "__wrapped__") \
            else _reseat()
        check("power" in p2 and dais[mid] != d2[cc.CONSOLE_N // 2],
              "CONTROL: give power a day of buffer and it loses the centre seat",
              "dais %s pit %s" % (d2, p2), out)
    finally:
        _ONCE.clear()
        _ONCE.update(_saved)

    out("--- 3. NOMINAL: every plant desk reads NORMAL, because that is what "
        "nominal means ---")
    rows = board(13.0, ())
    st = {r["desk"]: r["state"] for r in rows}
    check(all(st[d] == NORMAL for d in ps.SYSTEM_KEYS),
          "six plant desks NORMAL at 13:00 with nothing isolated",
          str({d: st[d] for d in ps.SYSTEM_KEYS}), out)
    check(worst_state(rows) in (NORMAL, CAUTION),
          "the board is not crying wolf on a station where nothing is wrong",
          worst_state(rows), out)

    out("--- 4. THE ORDER HAS AN EFFECT, and it is measured in incident.py ---")
    import incident as ic
    base_r = ic._r_brownout(ic.Ctx(day=1, seed="b5"), "reactor_hall", 13.0)
    base_f = ps.fault_arrivals_per_hour(13.0)
    order_isolate(("fusion_core", "reactor_hall"), tmp)
    hot_r = ic._r_brownout(ic.Ctx(day=1, seed="b5"), "reactor_hall", 13.0)
    hot_f = ps.fault_arrivals_per_hour(13.0)
    rows2 = board(13.0, path=tmp)
    st2 = {r["desk"]: r["state"] for r in rows2}
    check(hot_r > base_r,
          "isolating two generating units raises INC-BROWNOUT's rate",
          "%.6g -> %.6g (x%.0f)" % (base_r, hot_r, hot_r / max(1e-12, base_r)),
          out)
    check(hot_f > base_f,
          "...and the station's fault arrivals with it",
          "%.3f/h -> %.3f/h" % (base_f, hot_f), out)
    check(st2["power"] in (CAUTION, ALARM),
          "the POWER desk is off NORMAL", st2["power"], out)
    check(worst_state(rows2) != worst_state(rows),
          "the whole board changes rung", "%s -> %s"
          % (worst_state(rows), worst_state(rows2)), out)
    plan = ps.shed_plan(13.0, limit=0)
    heads, nplaces = ps.affected_heads(13.0)
    out("       shed plan: %d places, %s people standing in them"
        % (nplaces, f"{heads:,}"))
    for k, f, s2, db, hd in plan[:4]:
        out("         %-22s %5.1f%%  %-22s %6.1f dBA  %5d present"
            % (k, 100.0 * f, ps._stopfmt(s2), db, hd))
    check(bool(plan) == (ps.deficit("power", 13.0, offline_units(tmp)) > 0.0),
          "a shed plan exists exactly when the power desk is in deficit",
          "%d rows, deficit %.3f" % (len(plan),
                                     ps.deficit("power", 13.0,
                                                offline_units(tmp))), out)

    out("--- 5. the room is built from it ---")
    lay = room_layout(13.0, tmp)
    check(lay["state"]["power"] == st2["power"],
          "room_layout carries the same power state the board reports",
          "%s / %s" % (lay["state"]["power"], st2["power"]), out)
    check(lay["worst"] == worst_state(rows2),
          "...and the same worst rung", "%s / %s"
          % (lay["worst"], worst_state(rows2)), out)
    import importlib
    cc2 = importlib.reload(cc)
    v_hot, t_hot, g_hot = cc2.command_control(state=lay)
    lay0 = {"dais": lay["dais"], "pit": lay["pit"],
            "state": {d: NORMAL for d in desk_keys()}, "worst": NORMAL,
            "offline": ()}
    v_ok, t_ok, g_ok = cc2.command_control(state=lay0)
    from collections import Counter
    c_hot, c_ok = Counter(g_hot), Counter(g_ok)
    changed = {k: (c_ok.get(k, 0), c_hot.get(k, 0))
               for k in set(c_hot) | set(c_ok)
               if c_hot.get(k, 0) != c_ok.get(k, 0)}
    check(bool(changed),
          "the ROOM's own geometry differs between a well station and a "
          "broken one", str(sorted(changed.items()))[:220], out)
    red = cc2.CELL_RED
    check(c_hot.get(red, 0) > c_ok.get(red, 0),
          "...and the difference is MORE RED on the boards",
          "%d -> %d triangles of %s" % (c_ok.get(red, 0), c_hot.get(red, 0),
                                        red), out)
    # NEGATIVE CONTROL -- the same state twice must be identical, or the diff
    # above is measuring nondeterminism rather than the plant.
    v_a, t_a, g_a = cc2.command_control(state=lay0)
    check((v_a, t_a, g_a) == (v_ok, t_ok, g_ok),
          "CONTROL: the same board builds the same room, vertex for vertex",
          "", out)

    out("--- 6. the shortcut equals the long way round ---")
    order_restore(tmp)
    bad = []
    for h in (3.0, 8.0, 13.0, 20.0):
        fast = state_of_room(h, tmp)
        slow = {r["desk"]: r["state"] for r in board(h, ())}
        for d in fast:
            if fast[d] != slow[d]:
                bad.append("%s@%02d %s/%s" % (d, int(h), fast[d], slow[d]))
    check(not bad, "state_of_room agrees with board() at 03, 08, 13, 20",
          "; ".join(bad), out)
    # ...AND THE SHORTCUT MUST NOT BE TAKEN WHEN THERE IS AN ORDER.
    order_isolate(("water_reclamation",), tmp)
    check(state_of_room(13.0, tmp)["water"] != NORMAL,
          "CONTROL: with the only water plant isolated the shortcut is NOT "
          "taken and the water desk is off NORMAL",
          state_of_room(13.0, tmp)["water"], out)
    order_restore(tmp)

    out("--- 7. the orders survive the process boundary ---")
    order_isolate(("fusion_core",), tmp)
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r); import cnc_ops; "
         "print(cnc_ops.offline_units(%r))" % (_HERE, tmp)],
        capture_output=True, text=True)
    check("fusion_core" in r.stdout,
          "a second process reads the order this one gave",
          r.stdout.strip() + r.stderr.strip()[-160:], out)
    order_restore(tmp)
    if os.path.exists(tmp):
        os.remove(tmp)

    out("")
    out("cnc_ops gate: %s" % ("PASS" if not _FAILED else
                              "FAIL (%d)" % len(_FAILED)))
    return 1 if _FAILED else 0


def _reseat():
    """`seating()`'s body with the memo bypassed -- the control in gate() §2."""
    _ONCE.pop("seating", None)
    return seating()


# ===========================================================================
# 8.  THE ENGINE A/B -- the board is in the picture, or it is not real
# ===========================================================================
def engine_gate(out=print, res="960x540", outdir=None):
    """Render C&C well and C&C broken, in Godot, and diff the two frames.

    A GATE THAT SCANS SOURCE CANNOT ANSWER THIS. `--gate` proves the geometry
    changes; only the engine proves the change survives export, materials,
    lighting and the camera -- and CLAUDE.md's own rule is that "a static scan
    can tell you a caller exists; only running the thing tells you the caller
    runs". Three renders, two controls:

        nominal  A   the station is well
        broken   B   fusion_core and reactor_hall isolated by standing order
        nominal  A'  the control: A' against A must be 0.000% different, or
                     the A/B is measuring the renderer

    The renderer names its own mode on every run and this refuses a frame that
    came out of OpenGL 3 Compatibility, because session 4e judged ten of them.
    """
    outdir = outdir or os.path.join(_ROOT, "docs")
    os.makedirs(outdir, exist_ok=True)
    sh = os.path.join(_ROOT, "tools", "render_godot.sh")
    shots = []
    saved = read_orders()

    def shot(name, units):
        if units:
            order_isolate(units)
        else:
            order_restore()
        p = os.path.join(outdir, name)
        r = subprocess.run(
            [sh, "--shot", "interior", "--room", "cnc",
             "--eye", "0,1.75,-4.6", "--target", "0,3.0,8.4",
             "--res", res, "--out", p],
            capture_output=True, text=True, cwd=_ROOT)
        blob = r.stdout + r.stderr
        if "switching to OpenGL 3" in blob or not os.path.exists(p):
            raise SystemExit("cnc_ops: render did not produce a Forward+ "
                             "frame:\n" + blob[-1200:])
        mode = [ln for ln in blob.splitlines() if ln.startswith("renderer:")]
        out("  %-28s %s" % (name, mode[0] if mode else "renderer: UNSTATED"))
        shots.append(p)
        return p

    try:
        a = shot("craft-4q-cnc-board-normal.png", ())
        b = shot("craft-4q-cnc-board-alarm.png",
                 ("fusion_core", "reactor_hall"))
        a2 = shot("craft-4q-cnc-board-control.png", ())
    finally:
        write_orders(saved)
        apply_orders()

    px = _pixel_diff(a, b)
    ctl = _pixel_diff(a, a2)
    out("  A vs B  %.3f%% of pixels differ" % (100.0 * px))
    out("  A vs A' %.3f%% of pixels differ   <- the control" % (100.0 * ctl))
    ok = px > 0.001 and ctl == 0.0
    out("ENGINE gate=%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def _pixel_diff(p, q):
    """Fraction of pixels that differ between two PNGs. No PIL dependency."""
    import zlib                                                # noqa: PLC0415
    a, wa, ha = _png_rgb(p)
    b, wb, hb = _png_rgb(q)
    del zlib
    if (wa, ha) != (wb, hb):                                   # pragma: no cover
        return 1.0
    n = sum(1 for i in range(0, len(a), 3)
            if a[i:i + 3] != b[i:i + 3])
    return n / float(wa * ha)


def _png_rgb(path):
    """Decode a PNG to raw RGB. Enough of the format for a truecolour frame."""
    import struct                                              # noqa: PLC0415
    import zlib                                                # noqa: PLC0415
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    i, idat, w = 8, b"", None
    while i < len(data):
        ln = struct.unpack(">I", data[i:i + 4])[0]
        typ = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, colour = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and colour in (2, 6), (depth, colour)
            ch = 3 if colour == 2 else 4
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    prev = bytearray(stride)
    outb = bytearray()
    pos = 0
    for _y in range(h):
        f = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            bq = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + bq) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + bq) >> 1)) & 255
            elif f == 4:
                p = a + bq - c
                pa, pb, pc = abs(p - a), abs(p - bq), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (bq if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        prev = line
        if ch == 3:
            outb += line
        else:
            for x in range(0, stride, 4):
                outb += line[x:x + 3]
    return bytes(outb), w, h


# ===========================================================================
def main(argv=None):                                        # pragma: no cover
    argv = list(sys.argv[1:] if argv is None else argv)
    hour = 13.0
    if "--hour" in argv:
        hour = float(argv[argv.index("--hour") + 1])
    if "--patch" in argv:
        print(PATCH)
        return 0
    if "--order" in argv:
        spec = argv[argv.index("--order") + 1]
        if spec.startswith("isolate:"):
            units = tuple(u for u in spec.split(":", 1)[1].split(",") if u)
            print("isolated:", order_isolate(units))
        elif spec.startswith("restore"):
            print("restored, offline now:", order_restore())
        elif spec.startswith("shed"):
            for row in order_shed(hour):
                print("  %-24s %5.1f%%" % (row[0], 100.0 * row[1]))
        elif spec.startswith("dispatch"):
            print("repair backlog peak/end: %.1f / %.1f" % order_dispatch())
        else:
            raise SystemExit("--order isolate:UNIT[,UNIT] | restore | shed | "
                             "dispatch")
        return 0
    if "--effect" in argv:
        import incident as ic
        ps = _ps()
        off = offline_units()
        print("standing orders: %s" % (", ".join(off) or "none"))
        print("  %-14s %-24s %-24s" % ("", "NOMINAL", "under this order"))
        c = ic.Ctx(day=1, seed="b5")
        for place in ("reactor_hall", "plant_zone", "zocalo", "downbelow"):
            with _with_offline(()):
                b0 = ic._r_brownout(c, place, 13.0)
                f0 = ic._r_fault(c, place, 13.0)
            with _with_offline(off):
                b1 = ic._r_brownout(c, place, 13.0)
                f1 = ic._r_fault(c, place, 13.0)
            print("  %-14s brownout %-10.6g fault %-10.6g -> "
                  "brownout %-10.6g fault %-10.6g  (x%.0f / x%.1f)"
                  % (place, b0, f0, b1, f1,
                     b1 / max(1e-15, b0), f1 / max(1e-15, f0)))
        with _with_offline(()):
            fa0 = ps.fault_arrivals_per_hour(13.0)
        with _with_offline(off):
            fa1 = ps.fault_arrivals_per_hour(13.0)
            plan = ps.shed_plan(13.0, limit=0)
            heads, n = ps.affected_heads(13.0)
        print("  faults arriving %.3f/h -> %.3f/h, crews closing %.3f/h"
              % (fa0, fa1, ps.corrective_capacity_per_hour(13.0)))
        print("  shed: %d places, %s people standing in them" % (n, f"{heads:,}"))
        for k, f, st, db, hd in plan[:6]:
            print("    %-24s %5.1f%%  %-22s %6.1f dBA  %6d present"
                  % (k, 100.0 * f, ps._stopfmt(st), db, hd))
        return 0
    if "--engine-gate" in argv:
        return engine_gate()
    if "--gate" in argv:
        return gate()
    if "--board" in argv or not argv:
        report(hour=hour)
        return 0
    raise SystemExit(__doc__.strip().splitlines()[-8:])


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
