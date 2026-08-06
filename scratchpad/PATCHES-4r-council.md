# PATCHES — council chamber, session 4r

Written by the craft agent that owns `station/council_chamber.py`. Everything below is
in a file I do not own. Each entry carries the measurement that justifies it and the
command that reproduces the measurement.

---

## 1. BLOCKING — `deck.room_shell_for` gives this chamber a collision shell HALF its width

**File:** `station/deck.py`, `room_shell_for` (line ~760).

```python
def room_shell_for(schema, profile, meta, place, door_angle_deg):
    w_full, _l, _r = R.room_extent_m(schema, profile, place)
    bw, _bl = R.bay_span_m(place)
    return C.room_shell(meta, place["angle_deg"], min(w_full, bw) / 2.0,
                        room_interior_half_m(schema, profile, place),
                        R.ceiling_m(place), place["z_m"], ...)
```

### The measurement

```
$ python3 - <<'EOF'
import sys; sys.path.insert(0,'station')
import interior as it, rooms as R, directory as dr, deck as D, council_chamber as cc
schema, profile = it.load(); p = dr.by_key('council_chamber')
w_full,_l,_r = R.room_extent_m(schema,profile,p); bw,_bl = R.bay_span_m(p)
hw = min(w_full,bw)/2.0; hl = D.room_interior_half_m(schema,profile,p)
v,t,g = cc.council_chamber()
xs=[q[0] for q in v]; zs=[q[2] for q in v]; ys=[q[1] for q in v]
print(2*hw, max(xs)-min(xs), 2*hl, max(zs)-min(zs), R.ceiling_m(p), max(ys)-min(ys))
EOF
```

| | collision shell | built mesh | |
|---|---|---|---|
| across the ring | **11.808 m** | **22.745 m** | **51.9%** |
| along the axis | 22.751 m | 22.751 m | 100.0% |
| floor-to-ceiling | **3.60 m** | 7.42 m | |

**35.1% of the chamber's own 380 m² mosaic floor is behind an invisible wall** — the two
circular segments of an 11.0 m disc beyond ±5.904 m, 66.7 m² each. A player walking toward
either flank of the room stops 5.5 m short of a wall they can see.

### The shape of the failure is the finding

The **axis is exactly right and the width is exactly the old wrong answer**. That is not two
bugs, it is one: `room_interior_half_m` was fixed in 4k and its own docstring says why —

> This used to read `min(room_extent_m, bay_span_m)` — the one-bay clamp … a shell sized on
> the old expression would put an INVISIBLE wall 10.8 m into a 140 m room a player can see
> the whole length of.

— and the *width* argument three lines above it was left reading `min(w_full, bw) / 2.0`.
A fix applied to one axis and not to the rule. `rooms.built_span_m`'s docstring makes the
same claim for both axes ("THE ONE FUNCTION EVERYTHING THAT PLACES A ROOM MUST ASK") and one
of its two return values never reaches this call site.

### …and `built_span_m[0]` would not fix it either

`R.built_span_m(schema, profile, place)` returns `(11.808, 22.751)` here. `bay_w` is
`bay_span_m`'s prop-derived generic bay width and knows nothing about a bespoke module's
mesh, so substituting it changes nothing. For the 26 places `bespoke.compose` builds, the
width has to come from the module's own geometry, the way the axial half already does.

### Proposed change (owner of `deck.py` / `rooms.py` decides where it lives)

Make `built_span_m` ask the builder for a bespoke place, exactly as it already does for the
axial span, and have `room_shell_for` use it:

```python
# rooms.py
def built_span_m(schema, profile, place):
    if place.get("module") in bespoke.BESPOKE_GEOMETRY:
        v = bespoke.room_shell(schema, profile, place,
                               deck.room_axial_half_m(schema, profile, place))[0]
        xs = [q[0] for q in v]; zs = [q[2] for q in v]
        return max(xs) - min(xs), max(zs) - min(zs)
    plan = tiling(schema, profile, place)
    return plan["bay_w"], plan["built_l"]

# deck.py
def room_shell_for(schema, profile, meta, place, door_angle_deg):
    bw, _bl = R.built_span_m(schema, profile, place)
    return C.room_shell(meta, place["angle_deg"], bw / 2.0, ...)
```

Two cautions from this side of the fence:

* **it will widen 26 rooms at once**, and a wider shell can collide with its neighbour on
  the same deck. `deck_plan`'s arc allocation has to be re-run, not assumed.
* **the ceiling is wrong too** — `R.ceiling_m(place)` gives this chamber 3.60 m against
  `WALL_H_M` 7.00. That is not a hole a player falls through, so it is a separate, smaller
  item, but a shell ceiling 3.4 m below the built one cuts the fin fan in half for physics.

### The assertion this needs

Whatever the fix, the gate is one line and it belongs in `deck.py`, not here: for every
place, the shell's half-width is within a stated tolerance of the built mesh's own
half-extent across the ring. It fails today on `council_chamber` at 51.9% and should be
shown failing before it is made to pass.

---

## 2. MAJOR — `signage_panel` is a backlit sign standing in for a painted wall

**File:** `station/materials.py`. **Group:** `signage_panel__council_field`, chosen by
`council_chamber.screen_wall` because it is the only bound blue in the interior scene.

### The measurement

Balanced with `materials.GREY_WORLD_GAINS["05-sector-green/council chambers.webp"]`
(0.998, 1.082, 0.932):

| | reference | our render | |
|---|---|---|---|
| the wall behind the fan | rgb(0.140, 0.190, 0.241) **V 0.241**, H 210, S 0.42 | **V 0.608**, H 230, S 0.44 | 2.5× |
| the lit fin blade in front of it | V 0.361 | V 0.445 | |
| **field ÷ blade** | **0.67** | **1.37** | **inverted** |

Reference patch: source px (700,120)–(760,190), n = 4200. Ours:
`docs/craft-4r-council-before-half.png` px (120,120)–(300,300).

`docs/AAA-STANDARD.md` asks for colour as a *relationship*. The relationship here is that in
the show **the blue wall is darker than the pale blades standing on it**, and in our render
it is brighter than them, because `signage_panel` carries `emission (0.151, 0.156, 0.434)` at
3.0 — it is the customs board's backlit face, and a wall is not a light.

### What is needed

A `council_field` material bound to `council_field`: **non-emissive**, albedo derived so the
rendered value lands at ~0.67× the lit `council_fin`, hue 210, saturation ~0.42 (or cut for
the single-temperature-key reason `shell_deck_stone` records for this same frame). I searched
every interior-scene material for a non-emissive dark blue and the four nearest are Earthforce
uniform cloths — using one for a wall would be a fidelity error dressed as convenience, so
nothing was substituted.

Once it exists, `council_chamber.screen_wall`'s group name changes from
`signage_panel__council_field` to `council_field` in one line; the same for the speaking
fan's blue slivers, `signage_panel__council_speak_blue`, which should be a bright inlay blue
rather than a backlit sign.

**What this is worth:** the blue field is 5.1% of the normal frame and 7.3% of the half frame
after this session's geometry work (down from 25.9% and 35.7%), against 1.6% in the reference.
The remaining gap is entirely brightness, not area.

---

## 3. MINOR — the perforated sheet wants a texture, and the sheet machinery exists

**File:** `station/materials.py`, `COLOUR_SHEETS` / `TEXTURE_BINDINGS`.

`00-INDEX.md` reads this bench's panel as "a very fine square-hole perforated sheet …
evenly backlit with no visible lamp hotspots". Measured on the frame:

* an FFT of the panel rows gives a clean peak at **4.96–5.07 px** horizontally and
  **4.75–5.0 px** vertically;
* folding the signal on that period shows the profile repeating **five times inside it**,
  which is a pattern near 1 px beating against the frame's own sampling grid;
* the panel is **176–184 px tall** at source x 420–520 for 0.7214 m of panel, i.e.
  **250 px/m** (the note in the module before this session used 88 px/m, which is the
  *horizontal* scale on a nearly edge-on surface, and 88 px/m is what made the built pitch
  42 mm).

So the true pitch is **1.0–1.25 source px = 4–5 mm** and cannot be built: 2,400 columns ×
144 rows over 12.0 m of bench is ~145,000 triangles for a feature that subtends **0.84 px**
at the 5.89 m a player stands at. The geometry now carries the coarse tier at a
budget-derived 30 mm (12,320 triangles, 42% of the room); a `perf_sheet` colour sheet bound
to `council_mesh` at ~0.005 m would carry the rest and is the only way this panel reaches
`docs/AAA-STANDARD.md`'s tiling clause, which no buildable pitch can.

---

## 4. NOTE — the fan's hub may be the medallion, not the floor

Not a patch, a fidelity item for whoever next opens the composition. In
`reference/05-sector-green/council chambers.webp` at 4× the blades **converge on the
medallion**, and the faint outline circle round it fits a circle of radius 96.6 source px
against a bright rim of 33 px — **2.9 rim radii**. This module radiates the fan from a hub on
the floor with the medallion floating 4.60 m up, and at that geometry a 2.9× outline is 3.92 m
of radius under a 7.00 m ceiling, i.e. 1.8 m through the slab; it is built at 1.59× instead.
The two disagreements are one disagreement, and a fan radiating **from** the medallion resolves
both. Against it: `00-INDEX.md`'s own reading of this frame says the medallion is "above the
fins". Settling it needs a second frame of this wall, which the reference set does not hold.
