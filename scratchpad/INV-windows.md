# INV-530..539 — what is outside a window (session 4r)

**DO NOT PASTE INTO `canon/INVENTIONS.md` BLIND.** These are written in that file's
format and reserved to the block INV-530..539 assigned to this agent. `tools/inv_check.py`
gates the register; merge them there once, in one commit, after checking no other agent
has claimed the same numbers.

Everything below is authority 5 (declared extrapolation) unless it says otherwise. The
measurements are of `reference/03-sector-blue/comand and contorl.webp`, **authority 1**,
made with `scratchpad/vista_measure.py` (linear Rec.709 luminance on sRGB-decoded pixels,
the same arithmetic `tools/measure_frame.py` uses).

---

## INV-530 — the station fills 0.852 of C&C's window

**What.** `station/vista.STATION_FRAC_REF = 0.852`, tolerance 0.050. The fraction of the
window's vertical field that the station's own hull occupies, as against sky.

**Why.** The single most important fact about the C&C window is the one no gate in this
project could express before: it is **not a starfield**. At 5× magnification
(`tools/refzoom.py --box 0.33 0.11 0.70 0.45 --scale 5`) it is full of the station — a
large curved mass with a hard limb across the upper part of the aperture, pinpoint running
lights over it, and dark sky only in the narrow band beyond the limb.

**What constrained it.** Read off that crop: the aperture circle spans x 170–1320 px, so
its diameter is 1150 px and its top is y 60; the limb crosses the vertical centreline at
y ≈ 230. (230 − 60)/1150 = 0.148 sky, therefore 0.852 station.

**What would overturn it.** A cleaner frame of the same set. The source is 814×610,
compressed and motion-blurred, and the read is worth about ±0.05 and not better — which is
why the tolerance is stated at 0.05 and why `vista.py` gates on the qualitative claim
(*"the station fills most of the window"*, > 0.5) rather than on the arithmetic. A band
fitted to 0.852 would be a number tuned until the content passed.

---

## INV-531 — a window pane transmits 0.840

**What.** `station/vista.PANE_TRANSMITTANCE = 0.840`, applied as `albedo_color.a = 0.160`
on a duplicate of `materials.viewport_glazing`.

**Why.** `viewport_glazing` is **opaque** — albedo 0.040,0.042,0.046, roughness 0.07,
specular 0.92 — and `materials.py`'s `Material` class has no transparency field at all, so
there is nowhere in the library to say "this surface is glass". A window you cannot see
through is a window rendering black, which is the defect this session exists to close.

**What constrained it.** Fresnel at normal incidence for borosilicate, n = 1.52:
R = ((n−1)/(n+1))² = 0.0426 per air–glass interface. A pressure window is two panes, i.e.
four interfaces: T = (1 − 0.0426)⁴ = **0.840**. The remaining 0.160 is what
`viewport_glazing` actually measured — its own source note says the drum "reads through it
unattenuated" and that its 0.042 albedo came from a region its next clause calls
"near-black vertical MULLIONS with a dark SILL", i.e. the frame around the pane and not the
pane. So the entry keeps every value it measured and gains the transmission it never had.

**What would overturn it.** A reference frame showing the same object through and beside
one pane, which would give T directly. Also: an anti-reflection coating would take T to
~0.98, and a heavy tint would take it below 0.5; nothing in the show settles which.

---

## INV-532 — the view through a window is lit at sun energy 4.2

**What.** `station/vista.VISTA_SUN_ENERGY = 4.2`, the `DirectionalLight3D.light_energy` on
the vista's own sun (cull-masked to the vista's visual layer, so it lights the station
outside and nothing in the room).

**Why.** An absolute level cannot be taken from the reference frame: it is uncalibrated and
heavily blue-cast. What survives the cast is a ratio measured **within** the frame — the
glazing against the bulkhead it is set in, both under the same cast and the same lens.

**What constrained it.** Measured on the reference: four pane samples mean linear Y
**0.0431**, bulkhead **0.0190**, so the view is **×2.27** the wall. Measured the same way
on our own frame at sun energy 1.0: pane 0.0138, wall 0.0257, **×0.54**. A directional
light's contribution to a diffuse surface is linear in its energy and no other light
reaches the vista, so the correction is 1.0 × 2.27/0.54 = **4.2**. Verified:
`docs/craft-4r-cnc-half-window-after.png` measures **×1.99**, inside the ±0.60 band, and
the control `docs/craft-4r-cnc-half-window-before.png` measures **×0.11**.

**What would overturn it.** Any change to `materials.hull_exterior`'s albedo or to
`interior.tscn`'s tonemapper moves this ratio without moving this number. Re-measure with
`station/vista.py --selftest`'s FRAMES block, which re-takes the frame from its own
recorded command; do not re-guess.

---

## INV-533 — on this station the view is upside down against the show

**What.** A window on Babylon 5's hull has **the station above it and space below**. The
show's C&C frame has the mass at the bottom of the window and sky above.

**Why it is not a defect to fix.** The ring spins, so `deck._place_local`'s "up" is
**inward**, toward the axis — the centrifugal floor is the outer wall. From any window on
the hull the station's own body is inward and the only direction that leaves the hull is
outward. Measured: a ray from C&C's window running parallel to the axis stays at r = 118 m
while the hull grows to 234 m going aft, so it is inside the station before it has gone
300 m. Hard rule 4 — inside and outside from one schema — decides the tie in the schema's
favour.

**What constrained it.** `station/vista.station_side()` reports it per window by casting
the two extreme centreline rays; C&C reads `inward`. The full 46° render frame is
compatible with the show's *composition* anyway, because over the wider field the aft flank
at larger radius fills the lower half: measured on
`docs/craft-4r-cnc-half-window-after.png`, the lower pane sample is linear Y 0.106 against
the upper's 0.022.

**What would overturn it.** A canon statement that C&C is in a non-rotating section. The
schema has none; `station.rotation` gives one figure for the whole station.

---

## INV-534 — an observation dome's window is gated on geometry, not on composition

**What.** `obs_dome_1` and `obs_dome_2` are not gated against INV-530's 0.852. They are
gated on facing radially outward (outward component > 0.9) with a station fill < 0.05.

**Why.** `reference/03-sector-blue/comand and contorl.webp` is a frame **of C&C's window**.
No frame in this project shows what an observation dome looks out at. A dome is a blister
on the hull whose viewports face radially outward and whose whole job is to look at space,
so its fill is near zero by construction, and asserting 0.852 of it would be asserting a
number no reference supports.

**What would overturn it.** Any authority-1 frame through a dome viewport.

---

## INV-535 — a window's aperture stands off the hull by its component's height

**What.** `station/vista.PLACE_COMPONENT` maps `cnc`, `obs_dome_1`, `obs_dome_2` →
`observation_dome` (height 34 m) and `obs_rotundas`, `domed_rotunda` →
`observation_rotunda` (height 40 m). The aperture sits at the hull's radius at its z **plus
that height**.

**Why.** A window is an aperture in the pressure boundary, so its radius is the hull's — but
a room inside a blister is not flush with the plate. Observation Dome 1 stands 34 m proud
of the hull and C&C is inside it; the register, the schema's `observation_dome` component
(authority 3, Contract 5, *"OB. DOME 1 (COMMAND & CONTROL)"*) and
`command_control.py`'s docstring all say so in their own words.

**What constrained it.** `height_m` is read out of the schema component, not restated;
`--selftest` fails if a named id is not in the schema. The apex is used rather than a
fraction of it because that is the one point on a blister that is defined without a second
free parameter.

**What would overturn it.** A frame or a plan establishing where in the dome the window
sits. A window halfway up the dome's flank would take the standoff to ~17 m and bring the
near hull closer.

---

## INV-536 — the star field a window shows is the exterior's, lifted rather than copied

**What.** `station/vista.star_shader()` generates
`station/generated/scene/vista/vista_stars.gdshader` by lifting `hash33()` and
`star_layer()` **verbatim** out of `godot/scenes/space_sky.gdshader` and wrapping them in a
spatial shader that runs on a shell mesh.

**Why.** `space_sky.gdshader` is `shader_type sky` and can only be mounted on an
Environment. Mounting one on the interior scene would change the ambient and the
reflections of **every** interior frame in the project, and 23 of them are gated on their
distribution by `tools/measure_frame.py`. A second, hand-written star function would be two
descriptions of one thing — the defect this repository has recorded three times.

**What constrained it.** The lift is by regex over the source and **raises** if either
function is renamed, so it fails loudly rather than emitting an empty sky.

**What would overturn it.** Godot growing a way to sample a sky shader from a spatial one,
at which point the wrapper is unnecessary.

---

## INV-537 — the vista is clipped by three geometric facts and no budget

**What.** `station/vista.visible_hull()` keeps a hull triangle when it is in front of the
window plane, front-facing to the aperture, and inside the LOD band the chain itself
declares for its distance. `VIEW_RANGE_M = 12000`.

**Why.** Every one of the three is a fact rather than a saving: a triangle behind the pane
is inside the room's own wall; the hull is a closed surface, so a triangle facing away is
the far side of the station seen from inside it and can never be seen; and
`station/generated/lod_manifest.json` already says which level is honest at which distance.
12 km reaches the far end of an 8,047 m station from any window on it.

**What it costs, measured.** cnc **96,498** triangles (32.2% of the 300,000 visible-set
budget, 25.3% of `hull_lod0`); obs_dome_1 **29,387** (9.8%); obs_dome_2 **26,660** (8.9%).
Back-face culling alone takes cnc's forward view from 6,235 to 778. `station/budget.py` is
honestly RED already — the drum measures 315,604 against 300,000 — so no new bound is
invented here; the number is stated and the existing bounds do the failing.

**What would overturn it.** A measurement showing the window's own solid angle hides most
of it. From the room's deepest standing point the aperture subtends only 12.1° half-angle
(2.73 m radius at 12.77 m), so a camera-aware cone clip would cut this by most of its
value — and it is wrong as a general answer, because a player at the glass sees the whole
hemisphere.

---

## INV-538 — the sky turns at 10.76 deg/s and the hull does not

**What.** `station/vista.sky_basis(ap, phase)` = Bᵀ·R_z(−φ). The hull carries no phase.

**Why.** Stars are fixed in the inertial frame; the station rotates about +Z. This is the
one thing a painted backdrop cannot do and it is why the view is geometry.

**What constrained it.** `station.rotation.omega_rad_s` = 0.187717056 and `period_s` =
33.471574, both already in the schema, both authority 5, read rather than restated. A
quarter turn is **8.37 s** and the sky sweeps **10.76 °/s** — fast enough that a player
standing at a dome window sees it move.

**Measured in the engine.** `docs/craft-4r-obsdome1-phase000.png` against
`docs/craft-4r-obsdome1-phase090.png`: **3.39% of the pixels in the glazing band differ,
max delta 206/255**, while only 0.95% of the whole frame differs — the sky moves and the
room does not. The negative control is real and fired: before the shader took its direction
from the shell's own object space, the same A/B was **0.00% different**.

**What would overturn it.** Canon placing C&C or the domes in a non-rotating section.

---

## INV-539 — C&C's window faces the wrong way along the axis

**What.** `station/vista.aperture()` aims a window along the room's own window normal **or
its half turn about the room's vertical**, whichever sees the station, and reports which.
For `cnc` it chooses the half turn.

**Why.** The room as `command_control.py` builds it puts its window normal along room-local
+Z, which `deck._place_local` maps to the station's axis **forward**. Measured: facing
forward the station fills **0.000** of the window — it looks past the nose at empty space.
Half-turned it fills **0.740**, looking down 8 km of station, which is what the reference
frame shows.

**What constrained it.** A half turn about the vertical is `(x, y, z) → (−x, y, −z)`, the
transform `deck.door_sign` already applies for the side of the corridor a plaque is on. It
is a **rotation**, so it preserves winding; a mirror would point the room the right way
with every face inside-out, which is the defect session 3x found in `dressing._cyl` and
which no render would show.

**What would overturn it.** Fixing the register instead — see the session report's patch 3.
The half turn is this module's *description* of what the build should do; the build still
faces the room forward, and the rendered frames therefore show the room as the patch would
place it. That is stated in the manifest (`yaw_deg`) and printed on every run.

**Honest negative.** A first version solved a continuous outward **tilt** so the fill hit
0.852 exactly. It was deleted: fitting the geometry to a composition is picking the
convenient reading, and the number it produced (−32.5°) had no physical meaning.
