# Reference values — measured luminance and colour relationships in the show's interiors

Session 3x. Written to answer one question with numbers instead of taste: **our corridor
renders as one value from deck to soffit, and the show's does not — what, exactly, is the show
doing that we are not?**

Everything below is a measurement of an authority-1 reference frame, or of one of our own
committed renders, by code that reproduces this project's existing methods exactly. No value
here is invented. Where a question cannot be answered from the reference set, it says so and
names the frame that would settle it.

**This document changes nothing in the build.** Section 10 holds the only proposals, and they
are marked as such.

---

## 0. Method, and its controls

Two statistics are used and they must not be confused.

| symbol | what it is | why |
|---|---|---|
| **Y** | Rec. 709 luminance computed on **linearised sRGB** of the **raw** pixels: `LUMA @ srgb_to_linear(rgb)` | identical to `tools/measure_frame.py`. This is what a renderer produces and what a render must match |
| **balV / balS / balH** | HSV of the pixel **after** the frame's grey-world gains | identical to `station/materials.py`. This is the space every albedo in `materials.py` was derived in |

Grey-world gains are recomputed per frame by `materials._selftest`'s own method — mean over
pixels with `0.04 < V < 0.95`, `V = max(R,G,B)` on sRGB bytes, gains = `mean.mean() / mean`.

**Control 1 — the gains.** Recomputed here from the images: `grey level 1.webp`
0.970/1.087/0.953, `central corridor.webp` 1.044/1.085/0.892, `more hallway.jpg`
1.118/1.196/0.788, `more hallways.jpg` 0.794/1.145/1.154, `dock.webp` 0.968/1.027/1.007,
`war room.webp` 1.088/1.062/0.877, `corridor in alien sector.webp` 0.772/0.901/1.683,
`comand and contorl.webp` 1.307/1.130/0.741. Every one reproduces `materials.GREY_WORLD_GAINS`
to ±0.002.

**Control 2 — the published readings.** Eight of `materials.PROVENANCE`'s recorded balanced-V
values for `grey level 1.webp` are reproduced here *exactly* from the same boxes: soffit 0.162,
wall plate 0.295, rail nosing 0.340, rail reveal 0.160, pilaster face 0.301, dado 0.247, skirt
0.141, deck 0.471, pilaster light strip 0.609. `dock.webp` bay wall 0.268 and stepped ledge
0.328, and `war room.webp` console rail 0.529 and control face 0.290, also reproduce exactly.
`central corridor.webp`'s wall panel comes back 0.224 against a recorded 0.234 — 4% apart, the
only reading that does not reproduce to three figures.

**Control 3 — the balanced-saturation validity test.** `materials.NEGATIVE_RESULTS` records
that `Doug's Dugout.webp` balances to mid-tone S median 0.370, p90 0.870, a third above S 0.5,
and that `grey level 1.webp` gives 0.105 / 0.194 / nothing above 0.5. Recomputed here:
**0.370 / 0.870 / 33.0%** and **0.105 / 0.194 / 0.0%**. Exact on both.

### THE UNITS TRAP, and it is worth stating before any number below

**`materials.PROVENANCE`'s entire value ladder is in balanced-V space. A render matches in
linear-luminance space. A ratio of *R* in V is roughly *R*^2.2 in luminance.** Measured on the
anchor frame:

| element | balV | V / V(wall) | linear Y | **Y / Y(wall)** | (V ratio)^2.2 |
|---|---|---|---|---|---|
| soffit / ceiling | 0.162 | 0.548 | 0.0198 | **0.321** | 0.267 |
| upper wall plate (anchor) | 0.295 | 1.000 | 0.0615 | **1.000** | 1.000 |
| rail nosing, proud | 0.340 | 1.152 | 0.0806 | **1.309** | 1.365 |
| rail band reveal, dark | 0.160 | 0.541 | 0.0183 | **0.298** | 0.259 |
| dado panel | 0.247 | 0.838 | 0.0447 | **0.726** | 0.677 |
| skirt | 0.141 | 0.477 | 0.0150 | **0.243** | 0.196 |
| deck tile field | 0.471 | 1.595 | 0.1530 | **2.486** | 2.793 |
| pilaster face | 0.301 | 1.018 | 0.0626 | **1.016** | 1.040 |
| pilaster light strip | 0.609 | 2.063 | 0.2890 | **4.696** | 4.921 |

`materials.kit_deck`'s note says *"the deck measures 1.6x the wall's value"*. In V, yes. **In
the luminance a renderer produces, it measures 2.49x.** Any contrast target read off the
V column and applied to a render is under-stated by roughly a power of 2.2.

---

## 1. THE TONAL LADDER OF A CORRIDOR

**Frame: `reference/10-interiors-generic-kit/grey level 1.webp`** (1000×556; byte-identical to
`07-sector-grey/grey level 1.webp`). Authority 1. This frame defines 1.00 for the project.

**Anchor: the upper wall plate course, `(0.019,0.236)-(0.125,0.293)`, linear Y = 0.0615.** That
is `ALBEDO_ANCHOR`'s own region, so the ladder is anchored on the number the whole library
already hangs from. Every rung below is `Y(element) / 0.0615`, median over the box.

| # | element | region (L,T)-(R,B) | linear Y | **× wall** |
|---|---|---|---|---|
| 1 | ceiling void, above the soffit | (0.019,0.000)-(0.130,0.012) | 0.0060 | **0.098** |
| 2 | soffit / ceiling, left-wall column | (0.019,0.020)-(0.130,0.090) | 0.0140 | **0.228** |
| 3 | soffit / ceiling, wide box | (0.019,0.020)-(0.300,0.090) | 0.0198 | **0.321** |
| 4 | skirt / plinth | (0.019,0.771)-(0.134,0.793) | 0.0150 | **0.243** |
| 5 | rail band, dark reveal | (0.019,0.501)-(0.134,0.526) | 0.0183 | **0.298** |
| 6 | deck beside the left wall, unlit | (0.030,0.800)-(0.130,0.860) | 0.0323 | **0.525** |
| 7 | upper wall, top of the course | (0.019,0.150)-(0.125,0.200) | 0.0400 | **0.650** |
| 8 | amber sign plaque | (0.084,0.309)-(0.111,0.360) | 0.0435 | **0.707** |
| 9 | dado panel | (0.019,0.563)-(0.134,0.731) | 0.0447 | **0.726** |
| 10 | **upper wall plate course — ANCHOR** | (0.019,0.236)-(0.125,0.293) | 0.0615 | **1.000** |
| 11 | pilaster bullnose face | (0.188,0.394)-(0.206,0.731) | 0.0626 | **1.016** |
| 12 | rail band, lit lower lip | (0.019,0.523)-(0.134,0.534) | 0.0610 | **0.991** |
| 13 | right-wall upper plate | (0.600,0.100)-(0.700,0.220) | 0.0717 | **1.165** |
| 14 | rail nosing, proud lit edge | (0.019,0.470)-(0.134,0.492) | 0.0806 | **1.309** |
| 15 | wall below the plaque | (0.019,0.400)-(0.125,0.455) | 0.0802 | **1.304** |
| 16 | **deck tile field, under the pool** | (0.300,0.750)-(0.500,0.950) | 0.1530 | **2.486** |
| 17 | pilaster light strip — FITTING | (0.183,0.214)-(0.197,0.366) | 0.2890 | **4.696** |
| 18 | ceiling light strip — FITTING | (0.270,0.179)-(0.440,0.196) | 0.4748 | **7.715** |
| 19 | far hatch, lit end of the corridor | (0.316,0.340)-(0.385,0.420) | 0.6990 | **11.357** |
| — | LEVEL wayfinding plaque | (0.935,0.180)-(0.999,0.300) | 0.0141 | **0.230** |

**The ladder spans ×0.098 to ×11.36 — a range of 116:1 — and the surfaces a player touches
span ×0.24 to ×2.49, a range of 10:1.**

### Four things in that table that a builder would not guess

1. **The ceiling is one of the darkest things in the frame** (×0.23–0.32), not one of the
   brightest. Same result in two other frames — see §7.
2. **The deck is 2.5× the wall**, and it is 2.5× because it faces the fittings, not because
   its albedo is higher. `materials.kit_deck` already sets deck albedo *below* wall albedo and
   says why. The 2.5× must come from lighting.
3. **The dark horizontals — reveal and skirt — sit at ×0.24–0.30**, and *the same deck varies
   ×4.7 across one frame* (rung 6 at ×0.53 against rung 16 at ×2.49). The corridor's contrast
   is spatial, not material.
4. **The wall is not one number.** Down the left wall from y 0.15 to y 0.46 the same plate
   course runs Y 0.040 → 0.088, a factor of **2.2**, purely from the light falloff. Any
   single-value "wall" target is wrong by that much before it starts.

### The dark horizontals are SHIELDED RECESSES, not dark paint — and this is a test, not an opinion

Nine x-bins across the left wall, each measuring the wall above the band (y 0.38–0.45), the
band's own minimum (y 0.47–0.55) and the dado (y 0.60–0.70):

| x bin | wall Y | band Y | band/wall | dado Y | dado/wall |
|---|---|---|---|---|---|
| 0.010–0.029 | 0.0380 | 0.0068 | 0.179 | 0.0250 | 0.657 |
| 0.029–0.048 | 0.0480 | 0.0085 | 0.177 | 0.0342 | 0.713 |
| 0.048–0.067 | 0.0655 | 0.0098 | 0.150 | 0.0385 | 0.587 |
| 0.067–0.086 | 0.0836 | 0.0096 | 0.115 | 0.0463 | 0.554 |
| 0.086–0.105 | 0.0971 | 0.0103 | 0.106 | 0.0505 | 0.520 |
| 0.105–0.124 | 0.1140 | 0.0126 | 0.110 | 0.0569 | 0.500 |
| 0.124–0.143 | 0.1114 | 0.0106 | 0.095 | 0.0568 | 0.510 |

The wall triples across those seven bins; the band moves by 1.85×; the **ratio is not
constant** and falls from 0.179 to 0.095. A multiplicative (albedo) relationship holds the
ratio. Least squares on the seven points:

```
dark band   affine  Y = 0.0543 * wall + 0.00542    r = 0.909   rms 0.00070
            through the origin  Y = 0.1149 * wall              rms 0.00192   (2.8x worse)
dado        affine  Y = 0.3951 * wall + 0.01255    r = 0.991   rms 0.00146
            through the origin  Y = 0.5355 * wall              rms 0.00440   (3.0x worse)
```

**MEASURED:** the affine fit beats the multiplicative one by ~3× on both. The dark band
receives about **5%** of the key the flat wall beside it receives, plus an ambient floor of
Y ≈ 0.0054. The dado receives about **40%** plus a floor of Y ≈ 0.0126.

**INFERRED** (marked): the recess is therefore geometrically shielded to a degree ordinary
short-range AO will not produce — 5% transmission is a deep, narrow reveal with an occluding
lip, not a 20 mm groove. It does *not* follow that the reveal has no dark paint;
`materials.kit_reveal` assigns 0.140 (= 0.30× the wall's albedo) and marks the paint as
extrapolated. What the test rules out is the *opposite* conclusion — that the band could be
reproduced by albedo alone. **It cannot: no albedo produces a ratio that varies with the light.**

This is the same arithmetic `materials.PROVENANCE` uses to declare the hull neutral ("*a blue
albedo holds the ratio; an additive blue holds the difference*"), run on value instead of
colour, and it gives the same kind of answer.

---

## 2. THE DOOR QUESTION

### 2.1 The reference set contains no station door leaf in the corridor kit

`reference/00-INDEX.md` line 192, on `corridor in alien sector.webp`, already records it:
*"**Does not show a door leaf** — open, closed or moving. Nor does any other frame in the set."*
I surveyed `10-interiors-generic-kit/`, `03-sector-blue/`, `05-sector-green/`,
`09-garden-core-and-transit/`, `04-sector-red/` and `07-sector-grey/` and agree **for the
corridor kit**. `INV-008` is right that the leaf is invented.

**One correction to that index line.** `reference/15-races-and-makeup/Vorlon and captain.webp`
(authority 1, 1440×1080) *does* show a large framed rectangular leaf set in a wall — the index's
own entry for it calls it *"a large portal/door frame with a chamfered dark outline"*, and at
6× the thing inside the frame is a closed panel carrying the same slat panelling as the wall.
It is an ambassadorial/alien-sector set under a lavender key, not the grey corridor kit, and
nothing in the frame proves it opens. **Caveats: S1 costume in shot (set reference only, per
the index's own era note); heavy lavender key.** With those stated it is the only door-in-a-wall
in the set and it is worth measuring.

### 2.2 What separates a door from its wall — `Vorlon and captain.webp`

Horizontal profile of the door head, two independent height bands, ratios to the wall slat
immediately outboard of the frame. Read **RAW** — see §4 for why.

| element | x range | Y (y .030–.075) | × wall | Y (y .090–.135) | × wall |
|---|---|---|---|---|---|
| wall slat, 0.06 W from the door | 0.100–0.160 | 0.0453 | 0.81 | 0.0404 | 0.75 |
| **wall slat, adjacent — REF** | 0.175–0.203 | 0.0561 | **1.00** | 0.0542 | **1.00** |
| dark reveal, outer | 0.2069–0.2139 | 0.0177 | **0.32** | 0.0088 | **0.16** |
| narrow pale band | 0.2160–0.2250 | 0.0564 | 1.01 | 0.0514 | 0.95 |
| dark reveal, inner | 0.2278–0.2347 | 0.0159 | **0.28** | 0.0118 | **0.22** |
| **pale frame band** | 0.2375–0.2542 | 0.1363 | **2.43** | 0.1338 | **2.47** |
| door leaf, adjacent to frame | 0.2570–0.2850 | 0.0769 | 1.37 | 0.0705 | 1.30 |
| door leaf, mid | 0.3200–0.4200 | 0.0988 | 1.76 | 0.0842 | 1.56 |
| far jamb, bright edge | 0.4306–0.4361 | 0.1504 | **2.68** | 0.1526 | **2.82** |
| deep reveal, far jamb | 0.4417–0.4583 | 0.0122 | **0.22** | 0.0136 | **0.25** |
| return beyond the reveal | 0.4620–0.4800 | 0.0313 | 0.56 | 0.0438 | 0.81 |

**MEASURED — the answer to "is the door darker, lighter or the same":** *slightly lighter*, at
**×1.30–1.76** of the wall immediately beside it. But the wall itself moves ×0.75 → ×1.00 over
0.06 of frame width along the same gradient, so **a large fraction of that 1.3–1.8 is the room's
own light, and the frame does not separate the two.** Treat "the leaf is the same value as the
wall, ±50%" as the honest reading.

**MEASURED — what actually separates it:** a **pale frame band at ×2.4–2.5** and a **jamb edge
at ×2.7–2.8**, each flanked by a **near-black reveal at ×0.16–0.32**. Local contrast across the
boundary is **×8.5 to ×17** over a band 7–24 px wide (0.007–0.017 W).

**Fitting proportions** (all in the door's own plane, so foreshortening cancels):

| fitting | width (frac of frame W) | as % of the leaf's visible width (0.1764 W) |
|---|---|---|
| pale frame band, near jamb | 0.0167 | **9.5%** |
| dark reveal, inner | 0.0069 | 3.9% |
| narrow pale band | 0.0090 | 5.1% |
| dark reveal, outer | 0.0070 | 4.0% |
| whole near-jamb assembly | 0.0473 | **26.8%** |
| bright edge, far jamb | 0.0055 | 3.1% |
| deep reveal, far jamb | 0.0166 | **9.4%** |

Both jambs read at roughly **a tenth of the leaf's width**. Caveat: the door is seen obliquely,
so the near jamb is less foreshortened than the far one; 9.5% is an upper bound on the near
side and 9.4% is a lower bound on the far side. They agree, which is reassuring but partly
coincidental — they are different elements.

**Signage on the leaf: none legible.** The "angular hooked graphic motif" the index describes
is a **stepped chamfer in the frame band itself**, at source (0.246,0.141)-(0.296,0.183) — a
shape in the architrave, not applied graphics. There is a recessed panel in the head of the
leaf at (0.257,0.041)-(0.431,0.102) reading slightly greyer than the leaf around it.

### 2.3 The corridor kit's own jamb — `grey level 1.webp`, and this is the load-bearing one

`materials.kit_pilaster` is 0.469 against `kit_wall_plate`'s 0.460 — 2% apart, and STATE.md
flags that as suspicious. **It is correct.** Measured here in luminance as well as V: pilaster
face Y 0.0626 against wall plate Y 0.0615, **×1.016**. The two really are the same surface.

What separates them is a profile. Horizontal cut at y 0.400–0.460, x 0.130–0.320:

| x | Y | × the adjacent wall (Y 0.085 at x 0.140–0.166) | what it is |
|---|---|---|---|
| 0.130–0.166 | 0.121 → 0.070 | 1.42 → 0.82 | wall plate, falling with the key |
| **0.171** | **0.0542** | **0.64** | shadow groove at the wall's outer edge |
| **0.178** | **0.1082** | **1.27** | proud lit nosing |
| 0.188–0.198 | 0.059–0.071 | 0.69–0.84 | pilaster bullnose face |
| **0.204** | **0.0317** | **0.37** | dark groove |
| **0.220** | **0.1036** | **1.22** | second bullnose, lit |
| **0.247** | **0.0227** | **0.27** | deep reveal into the next bay |
| 0.313–0.319 | 0.114 → 0.551 | 1.3 → 6.5 | the lit far hatch |

**MEASURED: the assembly runs ×0.27 to ×1.27 of the adjacent wall — a ×4.7 spread inside 0.077
of the frame's width — at an albedo that is flat to 2%.** Every bit of that contrast is
geometry: proud nosings catching the key, grooves and reveals not catching it.

### 2.4 The aperture as a hole — `corridor in alien sector.webp`

The wall around the aperture reads Y 0.0093–0.0115 at x 0.02–0.13 and x 0.84–0.93 (y 0.30–0.60);
the lit window in the right wall reads Y 0.126 at x 0.931–0.961; the illuminated floor grating
inside the aperture reads Y 0.118 at (0.300,0.820)-(0.520,0.950). **The surround-to-interior
contrast is ×11–13.** The frame is a near-black silhouette against a lit volume.

`grey level 1.webp` does the same thing in reverse at its far end: wall at Y 0.030–0.067
immediately around the hatch, hatch at Y 0.55–0.70. **×8 to ×18.**

### 2.5 Signage is DARKER than the wall, not brighter

| plaque | region | Y | × anchor wall | × the wall *beside it* | internal p95/p5 |
|---|---|---|---|---|---|
| LEVEL plaque, right wall | (0.935,0.180)-(0.999,0.300) | 0.0141 | 0.23 | **0.28** | ×2.9 |
| amber plaque, left wall | (0.084,0.309)-(0.111,0.360) | 0.0435 | 0.71 | **0.59** | ×1.8 |
| wall beside the LEVEL plaque | (0.880,0.180)-(0.925,0.300) | 0.0506 | 0.82 | — | ×1.3 |
| wall beside the amber plaque | (0.070,0.309)-(0.082,0.360) | 0.0741 | 1.20 | — | ×1.2 |

**MEASURED: both plaques are darker than their own wall (×0.28 and ×0.59), and the letters on
the LEVEL plaque only reach ×0.5 of the anchor wall.** The plaque reads because its *field*
goes dark, not because its *letters* go bright. Its internal contrast is only ×2.9 — less than
the ×4.7 the pilaster profile gets from geometry alone.

### 2.6 The answer, stated plainly

**The show does not separate a door from its wall by albedo.** It separates it by a *fitting*:
a proud, lit band at **×1.2–2.8** of the wall, immediately beside a reveal at **×0.16–0.37**,
producing a **local luminance contrast of ×4.7 (corridor pilaster) to ×17 (Vorlon door frame)**
across a boundary a few pixels wide. Signage is dark-field, and adds ×2.9 at most.

Our 2%-apart albedos are not the defect. The missing thing is the ×5–17 local contrast, and it
is produced by geometry and occlusion.

---

## 3. IS THE FLOOR MODULATED?

**Short answer: yes, but not as a two-value checkerboard, and its pitch is not establishable
from this frame.** This corroborates a correction `reference/00-INDEX.md` already carries.

The index's re-examination of `grey level 1.webp` records: *"the 'deck is a fine tile grid,
roughly 0.5–0.7 m module' claim is not supported… peak spacings of 4–47 px… no stable
periodicity at any row… What the eye reads as a tile grid is a **dapple of specular
highlights**… **No deck module may be cited to this file.**"* Everything I measured is
consistent with that, and adds three things.

**(a) The modulation is real and it is bigger than a wall's.** Local (max − min) over a sliding
17 px window, divided by the local mean:

| surface | region | median Y | relative modulation |
|---|---|---|---|
| near floor, in the pool | (0.30,0.86)-(0.52,0.98) | 0.1677 | **0.219** |
| mid floor, in the pool | (0.30,0.74)-(0.50,0.82) | 0.1395 | **0.277** |
| near floor, left of the pool | (0.13,0.88)-(0.27,0.99) | 0.0764 | **0.208** |
| near floor, right of the pool | (0.56,0.80)-(0.72,0.95) | 0.0682 | **0.260** |
| near floor, far right | (0.60,0.88)-(0.80,0.99) | 0.0520 | **0.348** |
| CONTROL — upper wall plate | (0.019,0.236)-(0.125,0.293) | 0.0615 | 0.199 |
| CONTROL — dado panel | (0.019,0.600)-(0.134,0.700) | 0.0463 | 0.132 |

At comparable luminance the deck is **1.6–2.6× more modulated than a wall panel**. As local
max/min over the same window: deck median ×1.25 (near) / ×1.30 (mid) / ×1.50 (far), against
wall ×1.10–1.22.

**(b) It does not collapse outside the light pool.** Relative modulation is 0.219 inside and
0.208–0.348 outside. **INFERRED** (marked): that is more consistent with a reflectance or
relief texture than with a gobo cast by one fitting — but it is *not* decisive, because the
fittings are a distributed array and a semi-gloss deck will dapple wherever any of them reaches.

**(c) The periodicity scales with depth but is not significant.** Row autocorrelation on
cubic-detrended rows, first peak after the central lobe: 32 px (y .62–.67), 35 px (y .70–.75),
47 px (y .78–.84), 56 px (y .86–.92), 64 px (y .92–.99). The lag scales monotonically with
depth exactly as a real repeating module would — but every peak amplitude is under 0.10 in
magnitude (+0.058, −0.084, +0.038, +0.003, −0.099), which is not a detection.

**So: the floor is modulated at roughly ±10–17% about its local mean. It is NOT two values.
The tile pitch is not establishable from this frame** — and `materials.zoc_deck_tile`'s own
negative measurement on `more zocalo.png`, a frame that *does* resolve tiles, found tile-to-tile
variation of **sd 2.4%**, which is far too small to read as a checkerboard.

**What would settle it:** one frame of a station deck, lit flat, with a person or a known-width
door in shot. `more zocalo.png` has the deck and the scale but its tiles are 2.4% apart;
`sleeping-in-light-05.jpg` (already flagged as S5, outside the era lock) shows a
"dead-and-live checkerboard".

**The floor's real relationship to the wall is a level, not a texture, and it is large:**
Y 0.1530 under the pool against Y 0.0323 beside the wall — **the same deck varies ×4.73 across
one frame** — and the lit field sits at **×2.49 the upper wall**.

---

## 4. COLOUR — where the saturation lives, and which frames must be read raw

### 4.1 The lit surfaces are neutral; the colour is in the dark

`grey level 1.webp`, balanced, banded by **raw linear luminance**:

| Y band | n | balS median | balS p90 | balH median |
|---|---|---|---|---|
| 0.000–0.010 | 12,493 | **0.157** | 0.290 | **70.3** (warm) |
| 0.010–0.020 | 50,645 | **0.183** | 0.274 | **76.8** (warm) |
| 0.020–0.035 | 105,320 | 0.144 | 0.245 | 71.0 (warm) |
| 0.035–0.055 | 125,895 | 0.093 | 0.172 | 161.7 |
| 0.055–0.080 | 120,044 | **0.096** | 0.161 | **212.1** (cool) |
| 0.080–0.120 | 86,945 | 0.104 | 0.152 | 225.7 (cool) |
| 0.120–0.200 | 33,869 | **0.089** | 0.131 | 293.7 |
| 0.200–0.400 | 12,951 | **0.075** | 0.138 | 276.5 |
| 0.400–1.010 | 7,838 | 0.098 | 0.128 | 65.9 |

**MEASURED: saturation runs 0.15–0.18 at the bottom of the range and 0.075–0.10 through the lit
body, and the hue flips from warm (H 70–77) below Y 0.035 to cool (H 210–294) above it.** The
corridor's colour separation lives in the shadows and the low-lit surfaces, not on the lit
walls. That is exactly what `materials.NEGATIVE_RESULTS` concluded about the "ochre dado" —
*"the warmth is on the wall that has warm downlights low on it"* — and this generalises it to
the whole frame as a monotone trend rather than a two-region comparison.

Per-element, balanced, from the same frame:

| element | balH | balS | reading |
|---|---|---|---|
| upper wall plate | 204.0 | **0.046** | neutral |
| mid wall below plaque | 226.1 | 0.059 | neutral |
| rail nosing, proud | 254.7 | 0.060 | neutral |
| rail band, lit lower lip | 262.4 | 0.033 | neutral |
| dado, brightest part | 222.8 | 0.055 | neutral |
| deck tile field | 295.1 | 0.077 | near-neutral |
| right-wall waist band | 158.7 | 0.037 | neutral |
| right-wall upper plate | 220.1 | **0.157** | slightly cool |
| rail band, dark reveal | 49.8 | **0.209** | warm |
| skirt | 52.7 | **0.257** | warm |
| deck beside the left wall | 40.2 | **0.221** | warm |
| amber sign plaque | 54.2 | 0.184 | warm (a real amber plaque) |

**Walls: neutral.** S 0.033–0.077 on every lit structural surface. **Do not paint the corridor
warm or cool.** All the warmth belongs to the deck-level practicals and all the coolness to the
upper fittings.

### 4.2 Which frames must be read raw — and the gain-vector test is NOT sufficient

Two validity tests. `station/npc/costume.GREY_WORLD_LIMITS` accepts gains in 0.80–1.30. The
`materials.NEGATIVE_RESULTS` test is the balanced mid-tone (0.15 < V < 0.85) saturation
distribution, whose bar is set by the anchor frame at median 0.105, p90 0.194, nothing above 0.5.

| frame | gains R/G/B | gain test | balS median | balS p90 | > 0.5 | verdict |
|---|---|---|---|---|---|---|
| `grey level 1.webp` | 0.970/1.087/0.953 | pass | **0.105** | **0.194** | 0.0% | **ALBEDO-SAFE** |
| `dock.webp` | 0.968/1.027/1.007 | pass | **0.130** | **0.272** | 2.7% | **ALBEDO-SAFE** |
| `council chambers.webp` | 0.998/1.082/0.932 | pass | 0.151 | 0.350 | 2.2% | borderline |
| `more zocalo.png` | 0.936/1.137/0.950 | pass | 0.209 | 0.437 | 6.6% | borderline |
| `Vorlon and captain.webp` | 1.015/1.279/0.811 | **pass** | 0.207 | 0.453 | 5.9% | borderline |
| `war room.webp` | 1.088/1.062/0.877 | pass | 0.213 | 0.390 | 0.9% | borderline |
| `central corridor.webp` | 1.044/1.085/0.892 | pass | 0.224 | 0.461 | 7.5% | borderline |
| `zocalo.webp` | 0.906/1.185/0.950 | **pass** | **0.264** | **0.590** | **18.9%** | **READ RAW** |
| `more hallway.jpg` | 1.118/1.196/0.788 | fail | 0.255 | 0.514 | 11.3% | **READ RAW** |
| `more hallways.jpg` | 0.794/1.145/1.154 | fail | 0.261 | 0.574 | 15.2% | **READ RAW** |
| `corridor in alien sector.webp` | 0.772/0.901/1.683 | fail | 0.333 | 0.690 | 24.5% | **READ RAW** |
| `Doug's Dugout.webp` | 0.723/1.279/1.196 | fail | 0.370 | 0.870 | 33.0% | **READ RAW** |
| `comand and contorl.webp` | 1.307/1.130/0.741 | fail | 0.421 | 0.890 | 33.2% | **READ RAW** |

**NEW FINDING, and it is a methodological one: the gain-vector test passes on 8 of 13 frames;
the saturation test passes on 2.** `zocalo.webp` passes the gain test at 0.906/1.185/0.950 and
then balances 18.9% of its mid-tones above S 0.5 — worse than `more hallway.jpg`, which the
gain test rejects. **A gain vector inside 0.80–1.30 is necessary and not sufficient.**

`materials.py` currently draws albedo from `zocalo.webp` (`zoc_wall`, `zoc_handrail`). Both
entries are defensible on their own terms — `zoc_handrail`'s note runs the flat-saturation tint
test explicitly and passes it, which is the right test for that object. But the frame should
carry the raw-only flag alongside the others so nobody mines it casually.

Only **`grey level 1.webp`** and **`dock.webp`** are albedo-safe by this project's own bar.
`ALBEDO_ANCHOR`'s corroboration set is therefore thinner than it looks: five of its seven
readings come from frames that are borderline or worse.

### 4.3 `dock.webp` carries a real cool cast on its structure

Same value-banded read: from Y 0.010 upward, balS holds at 0.104–0.142 and **balH holds at
194–216 across the Y 0.010 → 0.400 bands, a 20× range of luminance.** Constant hue with roughly constant saturation across
a large value range is the *multiplicative* signature — the same test `materials.dock_bay_disc`
and `zoc_handrail` use to certify a real tint. But `materials.shell_deck_industrial`, derived
from the *deck* of the same frame, finds it "dead neutral" at H 50 S 0.017.

**So `dock.webp` shows a neutral deck under a cool-blue wall wash. Two surfaces, one frame,
different answers — which means the blue is on the walls, not in the paint.** Recorded as an
observation; it changes nothing, because `dock.webp` was only ever used for level.

---

## 5. THE DARKEST THING, AND HOW DARK

### 5.1 In the anchor frame

`grey level 1.webp`, whole frame, linear Y:

```
min 0.00490   p1 0.00805   p5 0.01298   median 0.05214   p95 0.17295   max 0.81580
fraction below Y 0.010 : 2.25%      below 0.015 : 6.98%      below 0.020 : 11.36%
```

Against the anchor wall at Y 0.0615:

| | Y | × wall |
|---|---|---|
| frame minimum | 0.0049 | **0.080** |
| p1 | 0.0081 | **0.131** |
| p5 | 0.0130 | **0.211** |
| median | 0.0521 | 0.847 |
| p95 | 0.1730 | 2.810 |
| **p99** | 0.5680 | **9.234** |

The darkest *named structural* surfaces are the ceiling void (×0.098), the LEVEL plaque field
(×0.23), the rail-band reveal (×0.30) and the skirt (×0.24). An 8×8 grid of per-cell p1 finds
the darkest cells at the top of the frame (0.0058–0.0079) and at the far right below the wall's
lower steps (0.0063–0.0074) — i.e. **×0.09–0.13 of the wall, and there is a population of them
everywhere.**

### 5.2 Across nine interior frames

Each ratio uses a lit structural region whose provenance is stated. Where `materials.py` already
publishes a region for that frame, its region is used unchanged.

| frame | lit region (provenance) | wall Y | min/wall | p1/wall | **p5/wall** | p95/wall | < 0.010 |
|---|---|---|---|---|---|---|---|
| `grey level 1.webp` | wall plate, `ALBEDO_ANCHOR`'s own | 0.0615 | 0.080 | 0.131 | **0.211** | 2.81 | 2.25% |
| `war room.webp` | arch face, `ALBEDO_…CORROBORATION` | 0.0506 | 0.061 | 0.128 | **0.150** | 7.90 | 9.64% |
| `more hallway.jpg` | lit deck pool (my pick) | 0.0135 | 0.000 | 0.048 | **0.090** | 9.48 | 68.13% |
| `central corridor.webp` | wall panel, `…CORROBORATION` | 0.0366 | 0.000 | 0.038 | **0.077** | 3.11 | 37.28% |
| `corridor in alien sector.webp` | floor grating (raw) | 0.1179 | 0.053 | 0.067 | **0.074** | 0.97 | 14.51% |
| `dock.webp` | bay wall, `…CORROBORATION` | 0.0502 | 0.000 | 0.027 | **0.040** | 3.13 | 45.90% |
| `more hallways.jpg` | lit deck (my pick) | 0.0460 | 0.000 | 0.003 | **0.008** | 4.75 | 61.48% |
| `more zocalo.png` | concourse deck tile | 0.3022 | 0.001 | 0.005 | **0.005** | 1.03 | 54.90% |
| `comand and contorl.webp` | dais apron, lit plateau (raw) | 0.2738 | 0.000 | 0.002 | **0.003** | 0.68 | 49.82% |

**MEASURED: p5 sits between ×0.003 and ×0.211 of a lit structural surface. `grey level 1.webp`
is the brightest-shadowed frame in the set** — `measure_frame.py`'s docstring already warns that
it is "the one BRIGHT residential corridor in the set" and that generalising from it is a known
trap. **Seven of nine frames reach literal zero.**

The right way to state the target: **a show interior puts its 5th percentile at a fifth of a lit
wall or below, and usually far below.**

### 5.3 And the top end matters more than the bottom, which nothing currently measures

Same frames, fraction above multiples of the frame's own median:

| frame | p75/p25 | within ±20% of median | > 2× median | > 4× median |
|---|---|---|---|---|
| SHOW `grey level 1.webp` | 2.60 | 22.7% | 13.8% | 3.4% |
| SHOW `corridor in alien sector.webp` | 2.40 | 26.2% | 17.9% | 9.6% |
| SHOW `central corridor.webp` | 4.25 | 15.7% | 29.4% | 13.3% |
| SHOW `dock.webp` | 9.05 | 8.8% | 38.0% | 22.1% |

Normalised to its lit wall, `grey level 1.webp` reaches **×2.81 at p95 and ×9.23 at p99** without
clipping, because its lit wall sits at only 6% of full scale. **A show corridor keeps roughly a
16× headroom above its walls, and it spends it.**

---

## 6. THE SAME MEASUREMENTS ON OUR OWN FRAMES

Read-only, on committed PNGs, by the same code. This section is the A/B and it changes the
diagnosis materially.

### 6.1 Our corridor is not one thing — the shipped rig and the ad-hoc rig give opposite answers

`tools/measure_frame.py --against "reference/10-interiors-generic-kit/grey level 1.webp"`:

| our frame | rig | median × ref | p5 × ref (band ×1.29) | verdict |
|---|---|---|---|---|
| `judge3w-corridor-wall-1m.png` | shipped | **×1.27** | **×1.03** | **PASSES EVERY BAND** |
| `judge3w-corridor-10m.png` | shipped | ×1.68 | ×1.41 | fails p5 only, marginally |
| `judge3w-corridor-20m-materials.png` | shipped | ×1.70 | ×1.46 | fails p5 only, marginally |
| `judge3w-corridor-sightline.png` | shipped | ×2.36 | ×1.88 | fails p5, 9.56% clipped |
| `judge3w-corridor-20m.png` | shipped, **fallback materials** | ×5.77 | ×12.58 | fails p5, ratio, crushed |
| `judge3x-corridor-5m.png` | **ad-hoc** | **×9.78** | **×11.09** | fails p5, p95, crushed, clipped |
| `judge3x-door-4m.png` | ad-hoc (inferred) | ×6.91 | ×5.30 | fails p5 |
| `judge3x-door-2m2.png` | ad-hoc (inferred) | ×5.67 | ×8.00 | fails p5 |

**`docs/judge3w-corridor-wall-1m.png` passes the whole distribution gate — p5 ×1.03, p95 ×1.59,
crushed ×7.69, 0.02% clipped.** It is the only interior frame in the project that does. It is
the shipped corridor kit, the shipped materials and the shipped fixtures.

STATE.md already carries the caveat that `judge3x-corridor-5m.png` was lit by an ad-hoc rig
("four omni lights at energy 5.0 and ambient 0.34… not by the shipped corridor fixtures").
**That caveat is correct and this measurement makes it quantitative.** The two door frames were
rendered in the same session and are not flagged; **INFERRED** from their statistics that they
share the rig — all three 3x frames have **0.0% of the frame above 4× their own median**, and
none of the four 3w frames does.

### 6.2 Flatness, ours against the show

| | frame | p75/p25 | ±20% of median | > 2× median | > 4× median |
|---|---|---|---|---|---|
| SHOW | `grey level 1.webp` | 2.60 | 22.7% | 13.8% | 3.4% |
| SHOW | `corridor in alien sector.webp` | 2.40 | 26.2% | 17.9% | 9.6% |
| SHOW | `central corridor.webp` | 4.25 | 15.7% | 29.4% | 13.3% |
| SHOW | `dock.webp` | 9.05 | 8.8% | 38.0% | 22.1% |
| OURS | `judge3w-corridor-wall-1m.png` | 2.51 | 30.5% | 18.5% | **7.9%** |
| OURS | `judge3w-corridor-10m.png` | 3.32 | 17.6% | 24.7% | **10.8%** |
| OURS | `judge3w-corridor-20m-materials.png` | 3.41 | 16.5% | 25.0% | **10.9%** |
| OURS | `judge3w-corridor-sightline.png` | 4.36 | 14.8% | 28.0% | **13.8%** |
| OURS | **`judge3x-corridor-5m.png`** | **1.62** | **42.2%** | **0.0%** | **0.0%** |
| OURS | **`judge3x-door-4m.png`** | **1.78** | **36.9%** | 4.5% | **0.0%** |
| OURS | **`judge3x-door-2m2.png`** | **1.75** | **39.3%** | 8.3% | **0.0%** |

**The four shipped-rig frames sit inside the show's range on every column. The three ad-hoc-rig
frames sit outside it on every column.** "One value from deck to soffit" is a true and measured
description of the 3x frames, and a false description of the 3w frames — and both are our
corridor.

### 6.3 Local contrast at the wall

Sliding 0.077 W window, max/min, on a horizontal wall strip:

| | median | p90 |
|---|---|---|
| SHOW `grey level 1.webp`, pilaster / portal jamb | **×4.56** | ×4.77 |
| SHOW `grey level 1.webp`, blank wall control (no fitting) | ×1.94 | ×2.28 |
| OURS `judge3w-corridor-10m.png` | ×4.83 | ×9.06 |
| OURS `judge3w-corridor-20m-materials.png` | ×3.44 | ×8.54 |
| OURS `judge3w-corridor-wall-1m.png` | ×1.32 | ×2.26 |
| OURS `judge3x-door-4m.png` | ×2.15 | ×3.47 |
| OURS **`judge3x-corridor-5m.png`** | **×1.15** | ×2.20 |

**`judge3x-corridor-5m.png` produces less local contrast on an articulated wall (×1.15) than
the show's *blank* wall does (×1.94).** At 1.12 m the shipped rig also under-delivers (×1.32) —
which is `judge-3w`'s own finding, in different units: *"the wall panels are completely blank…
one flat value across a 2 m × 2 m field"*. The 10 m and 20 m frames are fine.

### 6.4 Our ladder against the show's

> **CORRECTED, session 4a. Two things in the original table were wrong and one of them was wrong
> in a way that *looked* corroborated.** Read the correction before the table.
>
> **1. The "ceiling / soffit … OURS 1.12" row was not measured on the overhead.** It was measured
> on a **near-field pilaster face**. `export_scene.SOFT_FILL_LADDER_BOXES`' own comment records
> the same discovery independently — its first soffit box, `(0.230,0.120)-(0.320,0.200)`, "landed
> on a near-field PILASTER FACE rather than on the overhead, and read ×0.89 — which reproduced
> section 6.4's own 'ceiling / soffit … OURS 1.12' and so looked corroborated." Measured here,
> that box reads **×1.23** on `judge3x-corridor-5m.png`, ×1.00 on `engine-corridor.png` and
> ×0.89 on `engine-deck-corridor.png`. It tracks the wall in every frame, because it *is* wall.
>
> **2. The OURS column recorded no regions at all**, while the SHOW table in §1 gives coordinates
> for every rung — so the OURS side could not be recomputed by anyone who came after, and the
> pilaster mistake was undetectable from the page. Every OURS number below now names its box.
> The boxes are `export_scene.SOFT_FILL_LADDER_BOXES`, as data, so the two documents cannot drift.
>
> **3. The stated anchor does not reproduce either.** §1's anchor box `(0.019,0.236)-(0.125,0.293)`
> applied to `judge3x-corridor-5m.png` gives Y **0.6358**, not the 0.678 written above it — 6.6%
> apart. The conclusions it carries are not sensitive to 6.6%, but the number is not recomputable
> and is corrected here rather than left.
>
> **4. And the frame itself is the wrong frame to draw a conclusion from.** §6.1, on this same
> page, already establishes that `judge3x-corridor-5m.png` is the **ad-hoc rig** — four hand-placed
> omnis and a scratch ambient — and that it fails every band while the shipped rig passes. Its
> anchor wall sits at Y 0.652 against the shipped corridor's 0.060, i.e. **10.9× hotter**, so
> every rung above it is compressed against the top of the scale by construction. The table below
> keeps it because the original conclusions were drawn from it, and adds the shipped rig beside it.

Ratios to each frame's own lit wall plate, `SOFT_FILL_LADDER_BOXES["lit wall plate (ANCHOR)"]`
`(0.320,0.355)-(0.400,0.430)`. `judge3x` is the ad-hoc rig; the other two are the shipped
fixtures, the shipped soft fill and the shipped materials.

| element | box | SHOW × wall | `judge3x-5m` **ad-hoc** | `engine-corridor` **stale** | corridor **re-rendered 4a** |
|---|---|---|---|---|---|
| ceiling / soffit | `(0.400,0.115)-(0.600,0.190)` | **0.23 – 0.32** | 0.99 | **1.82** | **0.214** |
| floor field | `(0.430,0.800)-(0.570,0.900)` | **2.49** | 0.59 | **0.29** | **2.59** |
| deck beside the wall | `(0.330,0.745)-(0.410,0.770)` | — | 1.31 | 0.67 | 1.78 |
| lit wall plate, opposite | `(0.610,0.355)-(0.690,0.430)` | — | 0.19 | 0.73 | 0.98 |
| — *the pilaster face the 1.12 came from* | `(0.230,0.120)-(0.320,0.200)` | — | 1.23 | 1.00 | 0.99 |

Rows the original table carried that have no recorded box and therefore cannot be re-measured —
dark band, dado, skirt, wall fitting, ceiling strip, far end, deck spread — are **withdrawn**
rather than reprinted. They may well have been right; there is no way to tell, and that is the
point of the correction.

**What survives, and what does not:**

* **On the ad-hoc frame the original diagnosis stands** — everything is pulled toward the wall,
  the ceiling ~3–4× too bright and the floor ~4× too dark. `judge3x` really is that frame.
* **On the build that ships it is refuted, on both rungs, in opposite directions to the
  original claim.** The re-rendered corridor puts the soffit at **×0.214** against a show band of
  0.23–0.32 (7% under the bottom of it — slightly *too dark*, not 4× too bright) and the deck at
  **×2.59** against the show's ×2.49 (4% over). Both are the soft fill's doing:
  `export_scene.SOFT_FILL_CALIBRATION` predicts deck ×2.59 and soffit ×0.20 at the shipped energy
  and that is what a fresh render measures.
* **`docs/engine-corridor.png` — the ANCHOR frame, the one that defines ×1.00 for this whole
  project — was the evidence for neither, because it is stale.** It reads soffit ×1.82 and deck
  ×0.29: the show's ladder upside down. Re-rendered from the same command against the same code
  it reads ×0.214 and ×2.59. See §6.5.

The same comparison, done without picking boxes by eye — the *whole* left-wall column, normalised
to each frame's own wall plate:

| | darkest row-mean | 1st percentile of the column | absolute minimum |
|---|---|---|---|
| SHOW `grey level 1.webp`, x 0.019–0.134 | **×0.096** | **×0.102** | ×0.082 |
| OURS `judge3x-corridor-5m.png`, x 0.05–0.20 | **×0.457** | **×0.384** | ×0.058 |

**Our wall's darks are 3.8× too bright at the column's 1st percentile.** Isolated pixels do reach
×0.058 — darker than anything in the show's column — so the defect is not "no black exists", it is
that **the population of dark pixels is missing**: the show has a whole recessed course sitting at
a tenth of the wall, and we have a few pixels.

**MEASURED cause of the magnitude:** that frame's lit wall sits at Y 0.6358 — **×10.3 the show's
0.0615** — so there is only ×1.5 of headroom left above it before clipping, against the show's
×16. The top of the ladder physically cannot exist in that frame. *(The 0.678 originally printed
here does not reproduce from §1's anchor box; corrected 4a, see the note at the head of §6.4.)*

**And the current gate cannot see it.** `measure_frame.DIST_BAND["bright_p95"]` is ×3.27, which
its own docstring calls "nearly inert". Normalised to the lit wall, our p95 is 0.48× the show's
and our p99 is 0.16× the show's — **and the p95 band admits it (|ln 0.48| = 0.73 < 1.18). p99 is
not measured at all.**

### 6.5 THE ANCHOR FRAME WAS STALE, AND EVERY VERDICT IN §6 INHERITED IT

Session 4a, and it is the largest single finding on this page.

`docs/engine-corridor.png` is `EXPOSURE_FRAMES["ANCHOR"]["corridor"]` — the frame against which
`RENDER_OFFSET = 1.40` is defined, which is the number every other room in the station is
calibrated to. It was last written by **9884b23, 2026-07-29**. Two things landed after it and
neither re-took it:

* **c05a877**, the lens fix — `light_pilaster_strip` and `light_portal_head` stopped blowing.
* **7cf9404**, the soft fill — the corridor got the off-camera key it never had.

Re-rendered today with the recorded command and no other change:

```
tools/render_godot.sh --shot interior --room corridor --res 1280x720 \
    --out docs/engine-corridor.png
```

| | committed `engine-corridor.png` | re-rendered, same command | show |
|---|---|---|---|
| median × `grey level 1.webp` | ×1.39 | ×1.43 | — |
| **p5 × ref-at-offset** (band ×1.29) | **×1.64 FAIL** | **×0.80 PASS** | — |
| clipped | **1.76%** | **0.00%** | — |
| soffit × wall | **×1.82** | **×0.214** | 0.23 – 0.32 |
| deck × wall | **×0.29** | **×2.59** | 2.49 |
| distribution verdict | **FAIL** | **PASS, every band** | — |

**The two frames disagree about which way up the show's ladder goes.** The committed one has a
bright ceiling over a dark floor; the current build has a dark ceiling over a lit floor, which is
the show. CLAUDE.md's headline — *"p5 is the discriminator and fails 13 of 17, bright on 11 —
including the corridor anchor that defines 1.00 for the entire project (p5 ×1.64)"* — was
measured on this file and is a description of code that no longer exists.

**The general form, and it is the reason this section exists rather than a one-line fix.** Every
frame that fails the distribution verdict was committed on 2026-07-29 or 07-30. Every frame
committed on 07-31 — `engine-deck-corridor.png`, `engine-deck-door.png`,
`engine-corridor-softfill.png` — passes. A committed PNG is a *cache of a measurement*, and this
repository had no gate that could tell a stale cache from a fresh one: `--gate-frames` re-measures
the file, never the code. `export_scene.EXPOSURE_FRAMES` now records the **shot that produces each
frame**, so `--gate-frames --rerender` can re-take them and a stale frame becomes a diff instead of
a belief.

---

## 7. WHERE FRAMES DISAGREE

Stated rather than averaged.

1. **The ceiling.** `grey level 1.webp` ×0.23–0.32, `central corridor.webp` ×0.25
   ((0.250,0.005)-(0.600,0.050) vs its wall panel), `dock.webp` overhead girders ×0.107. Three
   frames, three sectors, one answer: **the overhead is 0.1–0.3× the lit wall.** My `war room.webp`
   box at (0.300,0.010)-(0.600,0.060) comes back ×1.77, which is **not** a counter-example — that
   box lands on the room's backlit upper structure, not on a soffit. It does not corroborate and
   must not be cited as though it does.

2. **The floor.** Under a light: `grey level 1.webp` ×2.49, `dock.webp` ×4.71 (deck under the
   flood). Away from one: `central corridor.webp` ×0.21, `dock.webp` ×0.20,
   `grey level 1.webp` ×0.53, `war room.webp` ×0.17. **The show's deck spans ×0.17 to ×4.71 of
   its wall depending only on where the lights are.** These are not disagreeing frames; they are
   the same rule sampled at both ends.

3. **`p5` in `grey level 1.webp` is an outlier and must not be generalised.** Its p5/wall of
   0.211 is 2.4–70× higher than every other frame in §5.2. `measure_frame.py`'s docstring already
   records this trap for the crushed fraction; it applies to p5 too.

4. **`dock.webp` reads cool on its walls and neutral on its deck** — §4.3. One frame, two
   answers, and the resolution is that the blue is the light.

5. **`materials.py`'s `central corridor.webp` wall-panel reading does not reproduce exactly**
   (0.224 here against a recorded 0.234, 4% apart) while eleven other published readings do.
   Small, and worth someone re-deriving before that value is leaned on.

---

## 8. WHAT COULD NOT BE ESTABLISHED

| question | status | what would settle it |
|---|---|---|
| Albedo of a **corridor door leaf** relative to its wall | **Not establishable from the reference set.** No frame shows a corridor-kit leaf; `00-INDEX` line 192 already says so and I agree | any frame of a station corridor door, open or closed |
| Whether the corridor **rail-band reveal** is dark *paint* or only dark *shadow* | **Not separable.** The affine fit proves it is not albedo *alone*; it cannot bound how much paint is present. `materials.kit_reveal` already marks the paint as extrapolated | a frame showing the same reveal under a second, brighter light |
| **Deck tile pitch** | **Not establishable from `grey level 1.webp`** — `00-INDEX` already carries the retraction, and my autocorrelation agrees (every peak under 0.10 in magnitude) | a deck frame with a person or a known-width aperture in shot, tiles resolved |
| Whether the deck's modulation is **reflectance or specular dapple** | **Inconclusive.** It survives outside the light pool, which argues for reflectance, but the fittings are a distributed array | a deck frame with one isolated light source |
| Absolute **corridor width** in `grey level 1.webp` | not attempted — no scale reference in frame; nothing here depends on it | a standing figure in that corridor |
| Whether `judge3x-door-2m2/4m` used the **ad-hoc rig** | **Inferred, not read.** Their distribution statistics match `corridor-5m` and no 3w frame | re-render either door camera with the shipped fixtures |
| Anything about `reference/17-lighting-and-color/` | **The directory is empty** — `.gitkeep` only. The task listed it as a source; there is nothing in it | — |

`reference/16-signage-typography-ui/` holds three files, all logos/symbols on flat grounds
(`babylon 5 shield.webp`, `earthforce logo.webp`, `faction symbols.png`). **None is an in-situ
frame**, so no signage-against-wall luminance ratio can be taken from that folder. The two
signage measurements in §2.5 come from `grey level 1.webp` itself.

---

## 9. THE SHORT VERSION

1. **The show's corridor ladder, in linear luminance, against its lit wall:** ceiling ×0.23–0.32,
   dark reveal ×0.30, skirt ×0.24, dado ×0.73, wall 1.00, proud nosing ×1.31, **floor ×2.49**,
   **wall fitting ×4.70**, **ceiling fitting ×7.72**, lit far hatch ×11.36. Frame p5 ×0.21,
   p99 ×9.23.
2. **A door is separated by a fitting, not by paint.** Proud band ×1.2–2.8, reveal ×0.16–0.37,
   local contrast **×4.7 to ×17**, at an albedo flat to 2%. Signage plaques are *darker* than
   their wall (×0.28, ×0.59).
3. **Our shipped-rig corridor already achieves this** (`judge3w-corridor-wall-1m.png` passes every
   band of `measure_frame.py`). **Our ad-hoc-rig judging frames do not**, and they are the frames
   the door verdict was written from.

---

## 10. PROPOSED, REQUIRES INTEGRATION

*The main agent applies these, or declines them. Each carries its derivation. Nothing here is a
material albedo change, because §1–§6 found no albedo that is wrong.*

### P1 — Re-render the doorway with the shipped fixtures before acting on the door verdict

**Derivation:** §6.1–6.3. The three frames the "pale slab" verdict rests on are the only three
in the project with 0.0% above 4× their own median, and `judge3w-corridor-wall-1m.png` — same
kit, same materials, shipped rig — passes the full distribution gate at p5 ×1.03. STATE.md
already names `export_scene --shot deck` as the prerequisite. **Until that exists, "the door is a
pale slab" is a statement about a scratch lighting rig.** This is the cheapest item on the list
and it may retire the rest.

### P2 — Do not change `kit_pilaster`, `kit_wall_plate` or `door_leaf_painted`

**Derivation:** §2.3. The pilaster face measures ×1.016 of the wall plate in linear luminance
and ×1.018 in balanced V. `materials.kit_pilaster`'s note is already correct: *"at 1.02× the
wall's value it cannot be doing it with albedo."* The 2% is the show's own number. `door_leaf_painted`
at 0.82× the frame is the only value with no frame behind it, and §2.2's one measurable leaf
reads ×1.30–1.76 of its wall — i.e. **if anything the leaf is not darker at all** — but that
frame's own light gradient covers the difference, so **it does not overturn 0.385 and should not
be used to.**

### P3 — Add a **p99 / lit-wall** check to `tools/measure_frame.py`

**Derivation:** §6.4. Our p95 is 0.48× the show's, which the existing ×3.27 p95 band admits;
our p99 is 0.16× the show's, which nothing measures. The show's frames put 3.4–22.1% of the
frame above 4× their own median; our 3x frames put **0.0%** there. A "fraction above 4× median"
check would have fired on all three and on none of the 3w frames. **The band must be derived from
the 33-frame corpus by `--derive`, exactly as the existing bands are — the numbers in §5.3 and
§6.2 are four frames and are an illustration, not a tolerance.**

### P4 — Record the units trap next to `materials.PROVENANCE`

**Derivation:** §0. `kit_deck`'s note says the deck is 1.6× the wall; in the linear space a
renderer works in it is **2.49×**. Every ratio in `PROVENANCE` is in balanced-V. One sentence
saying so, and `ratio_luminance ≈ ratio_V^2.2`, prevents the next reader from setting a lighting
target 1.6× too low.

### P5 — Flag `zocalo.webp` as raw-only in `materials.GREY_WORLD_GAINS`

**Derivation:** §4.2. It passes the gain-vector test (0.906/1.185/0.950) and puts **18.9% of its
balanced mid-tones above S 0.5** — worse than two frames the gain test rejects. Its two existing
uses are defensible on their own evidence; the flag is so nobody mines it casually. The same
table shows the gain-vector test is necessary and not sufficient, which is worth recording next
to `costume.GREY_WORLD_LIMITS`.

### P6 — When the corridor is re-lit, aim at these four rungs, in linear luminance

**Derivation:** §1, §6.4. Not albedo targets — lighting targets, and they are what the ladder
says.

| rung | target × the lit wall | ours now (`judge3x-corridor-5m`) |
|---|---|---|
| soffit / ceiling | **0.23 – 0.32** | 1.12 |
| the dark horizontals (reveal, skirt) | **0.24 – 0.30** | 0.86 – 1.05 |
| deck under a downlight | **2.5** (and ×0.2–0.5 away from one) | 0.69, spread ×1.99 |
| light fittings | **4.7 – 7.7** | 1.30 – 1.46 |

And the constraint that makes them reachable: **the lit wall must sit low enough to leave the
headroom.** In `grey level 1.webp` the lit wall is at Y 0.0615, the frame's own maximum is
0.8158 — **×13.3 of real range above the wall, ×16.3 to full scale.** In
`judge3x-corridor-5m.png` the lit wall is at Y 0.678, which leaves **×1.47** to full scale, and
the top of the ladder physically will not fit. `judge3w-corridor-wall-1m.png` is already in the
right register.
