# Exact patches for files I do not own — session 4r, A4b-3

I own `station/economy.py`, `station/dockwork.py`, `station/player.py` and new files
under `station/`. Everything below is a change somebody else must apply, with the
reason and the evidence.

---

## 1. `station/interact.py` — `container_holds` must read GOODS, not the whole counter

**Why.** `economy.stock_list(place)` is now goods **plus services** — it is the one
function `interact.counter_offer` reaches, and services had to arrive through it or
they could never cross the one-way bridge into `interact.gd`. But `container_holds`
reads the same function for the `store` verb, and **a service is not a thing in a
box**: with no change, a crate in Downbelow offers you *"a bunk for the night"* and a
tray dispenser in the mess hall offers you *"a hot meal"*. The second is arguably
right; the first is not, and one rule has to decide both.

`economy.goods_list(place, seed)` is the old `stock_list` under its old behaviour,
kept for exactly this caller.

```diff
@@ station/interact.py  (function container_holds, ~line 468)
 def container_holds(place_key, seed="b5"):
     """What a container in this place has in it. The place's own lines."""
     if place_key not in _HOLDS_CACHE:
         try:
             import economy as EC                              # noqa: PLC0415
-            _HOLDS_CACHE[place_key] = list(EC.stock_list(place_key, seed))
+            # GOODS, not the whole counter. `stock_list` gained services in 4r
+            # so they could reach `counter_offer` and therefore the engine; a
+            # crate is not where you keep a berth on somebody else's ship.
+            _HOLDS_CACHE[place_key] = list(EC.goods_list(place_key, seed))
         except Exception:                                     # noqa: BLE001
             _HOLDS_CACHE[place_key] = []
     return list(_HOLDS_CACHE[place_key])
```

Also update the comment block at ~line 418 which cites `economy.stock_list(place)`
for `store`: it is `economy.goods_list(place)` now. Its worked example
(*"a tray dispenser in the mess hall holds nothing, because `mess_hall` is
("catering", "crew_social") and sells no line"*) stays TRUE under `goods_list` —
`goods_list("mess_hall")` is `()`.

**Verified here:** `goods_list("mess_hall") == ()`,
`goods_list("black_market")[:3] == ('orchard fruit', 'salvage lots', 'identicard blanks')`,
`'a bunk for the night' in goods_list('downbelow') == False`.

---

## 2. `station/interact.py::_selftest` — the negative control has to be re-aimed

**Why.** The control is legitimate and its *purpose* survives; only its *subject* has
stopped being a non-counter. `docking_bays` declares `ship_departure`, which is now
where a berth is bought — the one transaction LAW-CRIME §7.1 calls the load-bearing
number of the underclass, at the only place on the station a hull leaves from. The
control needs a subject that will never be a shop.

`security_central` is that subject: it has a `serve`-verb prop (`duty_desk`), so
`counter_offer` is meaningful there, and `law_enforcement, dispatch, surveillance,
detention` contains nothing a counter could hang off.

```diff
@@ station/interact.py::_selftest  (~line 1146)
     # A REAL COUNTER SELLS AND A NON-COUNTER SAYS WHY IT DOES NOT. Both halves,
     # because one alone proves nothing: if `sells` were always False the first
     # would pass silently, and if it were always True the second would.
+    #
+    # THE SUBJECT MOVED IN 4r AND THE CONTROL DID NOT WEAKEN. `docking_bays`
+    # was the non-counter here and it now sells `passage home` (economy.SERVICES
+    # -- `ship_departure` is the only function on the station a berth can be
+    # bought against). `security_central` replaces it: a `duty_desk` carrying a
+    # `serve` verb at a place whose functions are law_enforcement / dispatch /
+    # surveillance / detention, so `counter_offer` is meaningful there and no
+    # reading of the register makes it a shop.
     _bar = counter_offer("dark_star")
-    _not = counter_offer("docking_bays")
+    _not = counter_offer("security_central")
     if not _bar["sells"] or not _bar["goods"]:
         fails.append("dark_star -- a hospitality place in economy.vendors() -- "
                      "sells nothing; the serve verb has no counter anywhere")
     if _not["sells"]:
-        fails.append("docking_bays sells things, and it is a cargo dock")
+        fails.append("security_central sells things, and it is a police post")
     if "not a counter" not in _not["tier"].get("4", ["", ""])[1]:
         fails.append(f"a non-counter gives no reason: {_not['tier'].get('4')}")
```

**Verified here:** `counter_offer("security_central")` gives
`sells=False, tier4=[False, 'security_central is not a counter']`.

---

## 3. `station/interact.py::_selftest` — the mess-hall container check

Fixed for free by patch 1 (`goods_list("mess_hall") == ()`), so the assertion at
~line 1176 needs **no edit**. Only its comment is now imprecise — it says
`container_holds` reads `economy.stock_list`; it will read `economy.goods_list`.

---

## 4. `station/interact.py` — `LIVE_READ` and the menu board (INFORMATIONAL, no edit)

`read_text`'s `menu_display` / `price_board` branch reads
`economy.lines_at(place_key)` behind `if hasattr(economy, "lines_at") else []`.
**`lines_at` did not exist**, so that branch has returned `""` for every board on the
station since it was written — a caller with no callee, degraded silently by its own
guard. `economy.lines_at` now exists and the branch works with no edit to this file.

`lines_at` deliberately carries only what is deterministic in `(place, seed)` — the
lines and their prices — and NOT how many are left, because `sidecar()` bakes this
string and nothing in the runtime refreshes a `LIVE_READ` token. A baked count would
be a board lying with a number on it.

**Suggested (not required):** the `hasattr` guard can go now, and probably should —
it is the thing that turned a missing function into an empty string instead of an
error.

---

## 5. `station/coldstart.py` — a new G8, if the shipped-scene purchase is wanted in the
gate suite

`station/till.py --engine` is standalone and needs no coldstart change. If G8 is
wanted, the shape is `_walk_gate`'s, and the driver already exists — `walk.gd`'s
`--visit --use-group=<group>` walks a body through a door to a named interactable and
presses it, twice. No `main.gd` change is needed.

```python
def g8(verbose=False):
    """G8 -- a counter takes the player's money, in the shipped scene."""
    import till
    return {"ok": till.engine_gate(verbose=verbose)}
```

and in `main()`:

```python
    ap.add_argument("--g8", action="store_true",
                    help="a counter takes the money, in the shipped scene")
    ...
    if a.g8 or run_all:
        if not g8(a.verbose).get("ok"):
            bad.append("G8")
```

---

## 6. `.github/workflows/validate.yml` — the CI step for the new gate

Cheap: no engine, no build, ~40 s. Fails today, honestly, on the stale sidecar (item 7).

```yaml
      - name: Where a credit changes hands
        id: still
        continue-on-error: true
        run: python3 station/till.py --gate
```

Follow the file's existing pattern of recording each step's outcome so one red step does not
blind the rest (the session-4e fix).

---

## 7. THE SHIPPED SIDECARS ARE THREE DAYS OLD AND PREDATE TWO SESSIONS OF VERB WORK

Not a patch — a finding, and the biggest one I did not go looking for.

Every `station/generated/scene/deck/*_interact.json` in this container is dated
**2026-08-02 04:44**, and **not one of them carries a `counter`, `holds`, `kind`, `text` or
`live` field.** Those are session 4p's `read_text` and session 4q's `verb_payload`. So in the
build this container launches:

| verb | what `interact.gd` needs from the row | present |
|---|---|---|
| `read` | `text` | **no** |
| `sit` / `rest` | `kind` | **no** |
| `store` | `holds` | **no** |
| `serve` | `counter` | **no** |

`interact.gd::_verb_serve` returns `""` the instant `it.counter.is_empty()`, and `_verb_store`
falls to its "put something in it" branch. **Four verbs' payloads are missing from every
artefact the engine reads**, and nothing says so: `tools/bootstrap.py`'s "deck geometry" step
checks only `*.glb` count > 0 and its "boot manifest" step checks `_boot_has("checks")`.
Neither can see a sidecar that is stale rather than absent.

The baker is fine — `walkable.interact_rows` calls `interact.sidecar()`, which does write the
payloads. **Proven empirically:** `till.rebake_sidecar()` re-derives the same deck's rows from
the group names in the committed file, in about a second and with no geometry, and the engine
run then sells at the counter. So the fix is a re-bake, and the *structural* fix is a
freshness check in `bootstrap.py` — the sidecar's field set against
`interact.sidecar([...])`'s, which needs no build.

*A gate that reads a committed artefact must be able to rebuild it. This is that rule one level
out: a **tool** that restores a container must be able to tell a stale artefact from a present
one.*

---

## 8. `station/generated/economy.json` was regenerated

I re-ran the project's own documented command —
`python3 station/dockwork.py --loop --days 14 --role lurker --seed downbelow --save
station/generated/economy.json` — because the ledger on disk predated `economy.SERVICES` and
carried no `docking_bays` row at all, so the shipped world had no berths on any shelf.

Every number `coldstart.purse_ledger` and G4 read is **unchanged**: purse `player:downbelow`,
420.50 cr, `no_status`, `carrying [identicard, kit_bag]`; wages 172.38; `bar_unnamed` till
3,598.42. Only the stock grew (54,545 units against 51,518), by the four service lines.

`station/till.py --engine` does **not** touch that file: it seeds a ledger of its own in the
working directory and passes `--ledger=` to the scene, because two agents with disjoint source
files are not disjoint in their artefacts.
