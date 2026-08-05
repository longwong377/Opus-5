# PATCHES FOR FILES P2 DOES NOT OWN — session 4r, the arrest chain

> **BEFORE ANYTHING ELSE — `git add -A` SWEPT THIS AGENT'S FILES AGAIN.** At 20:33:04 the commit
> `0d9e94a "WIP SNAPSHOT 6 -- three agents mid-flight, NOTHING HERE IS VERIFIED"` picked up
> `godot/scripts/enforcement.gd` and `godot/scripts/interact.gd` **while they were mid-edit** —
> `enforcement.gd` still had the pre-fix `_verdict`, and the engine gate had not yet been run
> against either. Nothing was lost (the working tree is ahead of that commit and the final files
> are verified), but this is the exact failure CLAUDE.md already records from session 4e: *"File
> lists were disjoint; the staging command was not. Stage the paths you changed."* It has now
> happened twice. The verified state is the WORKING TREE, not `0d9e94a`.
>
> Also live in this tree while P2 worked: another agent's till/economy work
> (`scratchpad/till-*`, `station/vista.py`). Their snapshots use their own copies, but **P2's gate
> writes `station/generated/economy.json`** — it took the shipped purse from 420.50 to 372.40 cr
> across five runs before the gate was made hermetic. The shipped purse now reads **372.40 cr with
> five convictions on the record and 48.10 cr in the Ombuds court's till** — every credit of it
> genuinely earned by an arrest that happened. If a till measurement taken this afternoon shows
> money appearing in `law_courts` and a player 48 cr poorer, that is P2's arrest gate and not a
> bug in theirs. `economy.json` is gitignored and regenerable (`dockwork.py --loop --days 14
> --role lurker --seed downbelow --save station/generated/economy.json`); it was left as it stands
> because a played session that has been arrested five times is a truer save than a reset one.

P2 owns `station/consequence.py`, `godot/scripts/interact.gd`, and the two new files
`station/enforcement.py` and `godot/scripts/enforcement.gd`. Everything below touches a file on
the do-not-touch list and is therefore **reported, not applied**. In priority order.

---

## 1. `station/player.py` — `from_state` DOES NOT ROUND-TRIP A CHOSEN ROLE, and the rung flips

**This is a real defect, it is in the shipped save, and it decides the whole of this session's
subject.** Measured on the purse this repository actually ships
(`station/generated/economy.json`, `player:downbelow`):

| | role | rung |
|---|---|---|
| what `economy.json` stores (and `interact.gd::set_purse` hands the body) | `lurker` | **0 no_status** |
| what `player.from_state(st)` returns | `service` | **4 citizen** |

`from_state` regenerates the card from `(npc_id, species)` alone — deliberately, and its docstring
gives the right reason: *"a save file cannot describe a player the station's own machinery would
not produce"*. But `player_from(choices, seed)` mints a card with a **chosen** role through
`_rederive`, and that choice is not recoverable from the id. So the engine and every Python caller
that reloads the purse disagree about the player's rung.

It is not cosmetic here. `consequence._dispose` at rung 0 says *"already at the floor; 4.3 step 6's
next disposal is transfer off-station"*; at rung 4 it says *"EA citizenship is not revocable by an
Ombuds"*. Two different games, decided by which loader you went through.

**The patch** (`from_state`, ~line 493):

```python
def from_state(st: dict) -> Player:
    nid, sp = st["npc_id"], st["species"]
    card = RES.resident(nid, sp)
    # A CHOSEN ROLE IS NOT IN THE ID. `player_from` mints a card through
    # `_rederive`, so a save made that way comes back as a different person --
    # and the rung with it, which is the field the whole law layer turns on.
    role = st.get("role")
    if role and card.role != role:
        card = _rederive(nid, sp, role)
    pl = Player(card=card).restore(st)
    if "tier" in st and int(st["tier"]) != int(pl.tier):
        raise ValueError(f"{nid}: the purse says rung {st['tier']} and the "
                         f"rebuilt card says {pl.tier}")
    return pl
```

The raise matters as much as the fix: `state()` writes `tier` for the engine, so the two halves
can be compared, and a silent disagreement is what let this live.

**Until it lands**, `station/enforcement.py::player_from_ledger` works around it — it rebuilds
through `player_from` with the stored role and **asserts** the rung matches what the engine holds,
raising rather than papering over. That function's docstring carries the whole finding.

---

## 2. `station/coldstart.py` — G8, and it is the only thing missing to make this a coldstart gate

The gate is written and runs (`python3 station/enforcement.py --gate`), and it has G4's exact
shape. It lives in `enforcement.py` only because `coldstart.py` is not P2's file. Fold it in:

**a. Module docstring**, after the G7 block:

```
G8 SOMEBODY COMES
    The fourth instance of the same failure and the half G4 named as open.
    `consequence.arrest` has run respond -> escort -> brig -> hold -> court ->
    fine -> release since P1-G2, on the graph a resident commutes on, and the
    game could not reach a line of it: a refused player was TOLD they were
    refused and walked away unharmed. A refusal you can walk away from is a
    sign, not a rule.

    G8 walks a body across a real boundary in the shipped scene until the card
    is refused, and asserts that a NAMED PAIR arrives on `security`'s own
    routed response time, covers ground getting there, and that what they do
    reaches the purse: the fine leaves the ledger a drink moves through, the
    station clock advances by the routed custody total, the conviction is
    written into the save, and the player is put outside the room.

    Four controls, and the first is this repository yesterday.
```

**b. Run line**, in the `Run:` block:

```
    python3 station/coldstart.py --g8       # a refusal is answered
```

**c. The function**, beside `g7`:

```python
def g8(verbose=False):
    """G8 -- somebody comes. Delegated to the module that owns the subject.

    NOT RE-IMPLEMENTED HERE. `station/enforcement.py` bakes the table this
    gate's verdict is checked against, so a second copy of the launch, the
    parse and the control list would be two descriptions of one gate -- which
    is the defect `_walk_gate` was factored out to stop inside this very file.
    """
    for probe in (lambda: built_deck("checks"), purse_ledger):
        good, why = probe()
        if not good:
            print("G8 SKIP -- %s" % why)
            return {"ok": True, "skipped": why}
    sys.path.insert(0, HERE)
    import enforcement as EN                                  # noqa: PLC0415
    return EN.gate(verbose)
```

**d. argparse + dispatch**, mirroring `--g7`:

```python
    ap.add_argument("--g8", action="store_true",
                    help="a refusal is answered -- somebody comes")
    ...
    run_all = not (a.g1 or a.g3 or a.g4 or a.g5 or a.g6 or a.g7 or a.g8 ...)
    ...
    if a.g8 or run_all:
        if not g8(a.verbose).get("ok"):
            rc = 1
```

**e. And correct G4's own docstring**, which currently ends:

> *What it does NOT claim: the arrest chain behind a refusal is still Python. A refused player is
> TOLD they are refused and is not yet detained. P2 owns closing that.*

Replace with: *"What a refusal leads to is G8's, not this gate's: G4 asserts the reading, G8
asserts the answer."* Leaving the old sentence is how a doc goes stale in the costly direction —
`docs/PLAYTEST.md` had four rows saying ABSENT about things that worked.

**Same edit in `godot/scripts/hud.gd::_boundary`'s header comment and `main.gd::_check_gate`'s**,
both of which carry the same "P2 owns closing it" sentence.

---

## 3. `.github/workflows/validate.yml` — two steps

`tools/wiring.py --selftest` already lists `scene/enforcement.json` under **"on disk but not
rebuilt by CI"** (4 paths, up from 3). That is the tool doing its job: an engine data path with no
CI producer survives only because somebody once ran the builder by hand — which is the Starfury
defect verbatim. Add, next to `sconsequence`:

```yaml
      # WHAT HAPPENS AFTER A REFUSAL -- P2. ~90 s, of which ~40 s is
      # `navigation.build_graph()`: the escort and court legs ARE paths on it.
      # `--bake` must run BEFORE the engine gate and before `wiring.py`, since
      # it is what writes `scene/enforcement.json`.
      - name: A refusal is answered -- the arrest chain, baked
        id: senforcement
        continue-on-error: true
        run: |
          python3 station/enforcement.py --selftest
          python3 station/enforcement.py --bake
```

The engine half (`--gate`) needs a built deck and a Godot binary, neither of which CI has — the
same reason `coldstart.py`'s G1/G4/G5 SKIP there. Fold it into whatever step runs `coldstart.py`
once G8 lands, rather than adding a second engine step.

**And add `senforcement` to the `Every gate ran` roll-up at line ~910**, or the step joins the
thirty-four that did not run and nobody notices.

---

## 4. `godot/scripts/hud.gd::Face::_check` — the custody plate draws CYAN, which means "admitted"

One line, cosmetic, and wrong in the direction that misleads. `_check` picks its colour like this:

```gdscript
	var col: Color = CYAN
	if String(lines[0]).begins_with("IDENTICARD REFUSED"):
		col = AMBER
```

`enforcement.gd` writes five more plates into the same field — `SECURITY NOTIFIED`, `MOVED ON`,
`DETAINED`, `IN CUSTODY`, `RELEASED` — and every one of them renders in the colour this HUD uses
for *your card is good*. **The patch is a rule, not a list:**

```gdscript
	# CYAN IS THE EXCEPTION, NOT THE DEFAULT. Every plate above the reticle is
	# about the player rather than about the world, and all of them but one are
	# bad news -- refused, the pair on their way, custody, release. Keying on
	# the single ADMISSION is a rule; keying on a list of the others is a list
	# that goes stale the day `enforcement.gd` gains a sentence.
	var col: Color = (CYAN if String(lines[0]).begins_with(
		"IDENTICARD ACCEPTED") else AMBER)
```

Byte-identical behaviour for both plates that exist today (`IDENTICARD ACCEPTED` → cyan,
`IDENTICARD REFUSED` → amber); correct for the five new ones.

---

## 5. `godot/scripts/interact.gd::_save_ledger` — Godot's JSON widens every integer, each save

Pre-existing, found while checking that the fine had landed, and not fixed here because it is not
this session's subject. Godot parses every JSON number as a float, so `JSON.stringify` writes back
`"day": 13.0`, `"n": 1.0`, `"tier": 0.0` for values Python wrote as ints — and the widening is
**cumulative across saves**: after two engine sessions the same `sales` array holds one row with
`"day": 13.0` and one with `"day": 13`.

Nothing breaks today (every Python reader coerces), so this is a note rather than a patch. If it
is ever worth fixing, the place is `_save_ledger`, and the fix is to snap the known-integer keys
before stringifying rather than to teach every reader to coerce.

---

## 6. `station/boot.py` — nothing required, one thing worth considering

`_checks()` bakes `certain_check`'s result into `boot.json`; `enforcement.json` is a separate
sidecar because it needs a ledger and a routed graph that `boot.py --bake` does not want to pay
for (~40 s). If a future session wants one file, the call is
`enforcement.table(boot_rooms())["places"]` and the cost is the graph build.

What IS worth doing: `coldstart.py::built_deck` takes a list of required keys so a stale
`boot.json` cannot masquerade as a content failure. The equivalent precondition for G8 is
`os.path.exists(enforcement.OUT_JSON)`, which `enforcement.gate()` already checks and reports as
`ARREST SKIP` with the command that fixes it.
