# Session 4r — patches for files this agent does not own

Owned and already edited: `godot/scenes/interior.tscn` (**not touched — see note 0**),
`godot/scripts/render_shot.gd`, and the new files `station/vista.py`,
`godot/scripts/vista.gd`, `scratchpad/vista_measure.py`.

Everything below is a change to a file this agent does not own. Applied by nobody yet.
Ordered by how much they matter.

---

## 0. `godot/scenes/interior.tscn` — DELIBERATELY UNCHANGED

I own this file and did not edit it, which is worth saying because the obvious fix is in
it. `background_mode = 1` (COLOR at 0.010,0.012,0.018) and
`reflected_light_source = 1` (DISABLED) are two of the three reasons the panes render
black, and switching them to SKY would light every window in the project in one line.

It would also change the ambient and the specular response of **every interior frame**, and
23 of them are gated on their distribution by `tools/measure_frame.py` §4b. It would also
destroy the diagnostic the file's own comment defends: *"pure black let two structural
holes survive four sessions of renders, because a hole and an unlit surface were the same
pixels."*

So the view is geometry on its own visual layer instead, and a windowless room is
byte-untouched. Verified: `--shot interior --room corridor` prints *"vista: no view for
'corridor'"*, mounts nothing, masks no lights and does not widen the far plane.

---

## 1. `tools/render_godot.sh` — forward the vista flags

`render_shot.gd` accepts `--no-vista`, `--vista-gain=N` and `--vista-phase=DEG`, and the
shell script cannot pass them: anything it does not recognise goes to `export_scene.py`,
whose argparse rejects them. The negative control in this session had to be run by moving
`station/generated/scene/vista/cnc.json` aside instead, which works and is clumsy.

In the argument loop, beside `--warmup` and `--light-gain`:

```diff
     --light-gain) LIGHT_GAIN="$2"; shift 2 ;;
+    --no-vista)   VISTA_ARGS+=("--no-vista"); shift ;;
+    --vista-gain) VISTA_ARGS+=("--vista-gain=$2"); shift 2 ;;
+    --vista-phase) VISTA_ARGS+=("--vista-phase=$2"); shift 2 ;;
     --no-export)  EXPORT=0; shift ;;
```

with `VISTA_ARGS=()` beside `PASS=()`, and where `USER_ARGS` is assembled:

```diff
 [ -n "$LIGHT_GAIN" ] && USER_ARGS+=("--light-gain=$LIGHT_GAIN")
+USER_ARGS+=(${VISTA_ARGS[@]+"${VISTA_ARGS[@]}"})
```

---

## 2. `station/materials.py` — the library has no way to say "this is glass"

`Material.__slots__` has no transparency field, so `viewport_glazing` is opaque and there
is nowhere in the library to fix it. `godot/scripts/vista.gd::glaze()` currently duplicates
the bound material at load and sets `albedo_color.a = 1 - 0.840` (INV-531). That shim is
labelled as a shim and prints on every run; it should retire.

Two changes, and the second is the one that matters:

```diff
     __slots__ = ("name", "title", "albedo", "roughness", "metallic", "specular",
+                 "transmittance",
                  "emission", "emission_energy", "emission_texture",
```

```diff
     def __init__(self, name, title, albedo, roughness, metallic=0.0,
-                 specular=0.5, emission=None, emission_energy=0.0,
+                 specular=0.5, transmittance=0.0, emission=None,
+                 emission_energy=0.0,
```

with `self.transmittance = transmittance`, and in `tres()`:

```diff
     body.append(f"roughness = {_num(m.roughness)}")
+    if m.transmittance > 0.0:
+        # Godot gates transparency behind an enum; setting albedo alpha alone
+        # is a silent no-op, which is the failure this file already carries
+        # three scars from.
+        body.append("transparency = 1")
+        body.append("depth_draw_mode = 1")
```

and `emitted_albedo()`/`_c()` must write the fourth component as `1 - transmittance`
rather than 1. Then, on `viewport_glazing`:

```diff
         albedo=(0.040, 0.042, 0.046), roughness=0.07, metallic=0,
-        specular=0.92,
+        specular=0.92, transmittance=0.840,
```

**Do not split `cc_glazing` off `prop_viewport` while doing this.** That split is the one
the entry's own comment says is blocked on C-003, and transmittance does not need it: a
transmissive pane shows whatever is behind it, so a drum-facing window and a space-facing
window differ by their *vista* and not by their glass. This change makes that split
unnecessary rather than urgent.

---

## 3. `docs/gazetteer/LOCATIONS.md` + `station/directory.py` — C&C is not where its dome is

**The largest finding of the session, and it is five failing gates pointing at one row.**
`station/vista.py --selftest` reports:

```
[FAIL] cnc:        register r 207.9 m, hull r 118.4 m at z 7968 -> +55.5 m outside the hull
[FAIL] obs_dome_1: register r 209.9 m, hull r 116.5 m at z 7959 -> +59.5 m outside the hull
[FAIL] obs_dome_2: register r 209.9 m, hull r 116.5 m at z 7959 -> +59.5 m outside the hull
[FAIL] obs_dome_1: register 0 deg z 7960; nearest built dome 90 deg z 7180; off by 90 deg and 780 m
[FAIL] obs_dome_2: register 90 deg z 7960; nearest built dome 90 deg z 7180; off by  0 deg and 780 m
```

`command_control.py`'s own docstring predicted this exactly: *"C&C's window is that dome's
glazing seen from inside … the two must agree or the station has a window that looks out at
nothing."* Nobody had checked, because until this session nothing could.

The schema (`components`, `observation_dome`, authority 3, Contract 5) puts two domes at
**phase 90°**, z **7060** and **7180**, radius 46 m, height 34 m. `components.domes()`
builds `count // rows` domes per row, so with `count = 2, rows = 2` both land on the same
meridian. The register puts `obs_dome_1` at 0°/z 7960 and `obs_dome_2` at 90°/z 7960.

Three ways to close it and they are not equivalent:

* **(a) move the register to the schema.** `obs_dome_1` → 90°, z 7060; `obs_dome_2` → 90°,
  z 7180; `cnc` follows dome 1. Cheapest, and it makes the exterior the authority — which
  is what hard rule 4 says. It moves three rows of `LOCATIONS.md` and whatever
  `deck.py --sweep` clusters them into, so it is not free.
* **(b) move the schema to the register.** Wrong: Contract 5 is authority 3 and the
  register's z is authority 5.
* **(c) split the difference by giving the domes `rows: 1, count: 2`** so they sit at 0°
  and 180° at one z. That matches the register's *angles* better and still moves z by
  780 m, and it changes the exterior silhouette. Needs a reference read.

**Recommend (a), and it is a real decision rather than a tidy-up** — the register's radius
of 209.9 m at z 7960 is 90 m outside a hull that is 116.5 m there, so this row is wrong in
the build as well as in the view.

**And the underlying cause is one line in `station/deck.py`:** `_ring_cells` calls
`interior.ring_cells(...)`, which is **z-blind** and returns Blue ring 0's widest radius,
211.55 m, for every z in the sector. `interior.ring_radii(schema, profile, 'blue',
z_m=7960)` — the z-aware form that already exists — reports that **ring_1 does not exist at
that z at all**; the outermost ring there is ring_3 at 80.4–110.9 m. Every place on
blue/0/0 forward of about z 7700 is therefore assembled outside its own hull. That is a
deck-assembly defect, not a window defect, and it is worth its own session.

---

## 4. The shipped build does not mount the vista — instance ten if it is left

`godot/scripts/vista.gd` is mounted by `render_shot.gd`, which is the **render** path.
`main.gd::_build_station` → `walk.gd` (streamed cells) is the path a player launches, and it
mounts nothing. This is exactly the shape of the nine defects `CLAUDE.md` lists, and it is
said here rather than discovered later.

It is not a one-line patch, because `--shot interior` builds one room in a ROOM-local frame
and the shipped build is in station world coordinates. The manifest already carries
everything needed: `aperture.p` and `aperture.basis` are in station coordinates. The shape
is:

```gdscript
# in main.gd, after _build_station()
var v = load("res://scripts/vista.gd").mount(w, place_key, vista_dir)
v.global_transform = Transform3D(basis_from(man.aperture.basis),
                                 v3(man.aperture.p))
```

with `vista.gd` growing a `world: bool` argument that skips the room-local offset. Then the
gate is not a render — it is walking a body to the window and grepping the loader's line,
per `CLAUDE.md`: *"a static scan can tell you a caller exists; only running the thing tells
you the caller runs."*

---

## 5. `.github/workflows/validate.yml` — the gate does not run in CI

```yaml
      - name: What is outside a window
        id: svista
        continue-on-error: true
        run: python3 station/vista.py --selftest
```

placed with the other `s*` steps, and its outcome added to the final roll-up. It takes
about 90 s cold (the aperture cache makes re-runs seconds) and needs no engine and no GPU.
**It currently FAILS 5 of 38**, all of them item 3 above, and that is the point: it should
go into CI red and stay red until the register is fixed.

---

## 6. `station/command_control.py` (or `station/deck.py`) — the room faces the wrong way

Measured (INV-539): facing along its built +Z normal, C&C's window has the station filling
**0.000** of it — it looks forward past the nose at empty space. Half-turned about the
room's vertical it fills **0.740**.

`station/vista.py` applies the half turn to the *view* and reports it (`yaw_deg: 180`), so
the frames in `docs/craft-4r-*` show the room as this patch would place it. The build still
faces it forward.

The turn is `(x, y, z) -> (-x, y, -z)`, which is the transform `deck.door_sign` already
applies for the side of the corridor a plaque is on — a rotation, so winding is preserved.
It belongs either in `command_control.command_control()` (author the room aft-facing) or in
whatever places bespoke rooms on the ring. Whichever, `deck.py --degeneracy` and
`walkable.py` should be re-run after it, because it moves the room's door.

---

## 7. FOUND WHILE FIXING THE WINDOW: the window's own frame is unlit

Not a patch, a finding, and it is the next thing to do to this room.

| | show | ours, before | ours, after |
|---|---|---|---|
| pane / bulkhead | **×2.27** | ×0.11 | **×1.99** |
| pane / mullion | **×0.48** | ×0.57 | **×6.96** |

The show's mullions are *brighter* than the glass — they are lit structure in front of a
mid-dark view. Ours measure linear Y **0.0078** against a 0.0543 view, so the window now
reads as a **silhouette**: a bright hole with a black wheel over it. The mullions measured
0.0051 before the vista existed, so this is not a regression — it is a pre-existing hole in
the room's lighting that a black window was hiding. Nothing in `command_control.py` puts a
fitting where it would rake the window's frame; `cc_light_strip` is four wall courses at
the sides.
