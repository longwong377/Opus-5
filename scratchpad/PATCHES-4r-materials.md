# Session 4r — the materials agent's patches for files it does not own

Owned and edited: `station/materials.py`, and the generated artefacts it writes
(`godot/materials/*.tres`, `godot/materials/textures/*`,
`godot/materials/material_rules.gen.txt`). `canon/INVENTIONS.md` was appended to
(INV-570, 571, 572), which every agent does.

Everything below is a change to a file this agent does not own. **Applied by nobody.**
Ordered by how much they matter.

---

## 1. `tools/render_godot.sh` — A REGENERATED TEXTURE RENDERS THROUGH ITS PREVIOUS IMPORT, SILENTLY

**This is the most important thing in this file and it is not about a material.**

The script already carries the right rule — *"a clean checkout renders a different picture,
and returns 0"* — and warms the import cache when `godot/.godot/imported` is **absent**. But
a checkout that has an import cache and a **newer PNG** is the same defect with a narrower
door: a game-mode Godot (`--path godot <scene>`, no `--import`, no editor) does **not rescan
the filesystem**, so it loads the `.ctex` it already has. Exit 0, plausible frame, and every
craft judgement taken from it is about last session's texture.

Measured here, by accident, while doing INV-572. `station/materials.py --export` rewrote
`soil_clod_{albedo,normal,orm}.png` at 2048 (22:44). The render at 22:45 came back changed —
convincingly, 56.45% of pixels — and it was the **tile** change alone: the `.ctex` files were
still 21:54, and `soil_clod_albedo.png-….s3tc.ctex` was **699,116 bytes**, which is a 1024
BC1 with mips. After a forced `godot --path … --import` it is **2,796,268**. Two renders that
differ in a way that looks exactly like the change you made, and one of them is wrong.

Same shape as the 3z stale committed frame and the 4e OpenGL fallback: **the frame was fresh,
the renderer was right, and the texture was last session's.**

The cheap fix is to compare mtimes rather than test for a directory, beside the existing
warm-up block:

```bash
# The cache being PRESENT is not the same as it being CURRENT. Game-mode Godot
# does not rescan, so a texture regenerated since the last import renders as
# whatever was imported before it -- exit 0, plausible PNG, wrong surface.
NEWEST_TEX="$(ls -t "$ROOT"/godot/materials/textures/*.png 2>/dev/null | head -1)"
NEWEST_IMP="$(ls -t "$ROOT"/godot/.godot/imported/*.ctex 2>/dev/null | head -1)"
if [ -n "$NEWEST_TEX" ] && [ -n "$NEWEST_IMP" ] \
   && [ "$NEWEST_TEX" -nt "$NEWEST_IMP" ]; then
  echo "--- a texture is newer than the import cache; re-importing ---"
  SAVED_PROJECT="$(mktemp)"; cp "$ROOT/godot/project.godot" "$SAVED_PROJECT"
  xvfb-run -a --server-args="-screen 0 640x360x24" \
    "$GODOT" --path "$ROOT/godot" --import >/dev/null 2>&1 || true
  cp "$SAVED_PROJECT" "$ROOT/godot/project.godot"; rm -f "$SAVED_PROJECT"
fi
```

The `project.godot` save/restore is not optional and the existing block says why:
`--import` rewrites its header.

**Note for whoever applies it:** the same hazard means every frame this repository has taken
since a texture last changed is suspect in exactly one way — it shows the texture that was
imported, not the one in the tree. That is worth one `--import` before the next judged render
round, whether or not this patch lands.

---

## 2. `tools/export_scene.py` — the drum has no fill on a vertical surface under canopy

**This is the other half of INV-571 and it is the half that fixes the picture.** The bark
value is right; the tree is a silhouette because it stands in its own canopy's shade under
overhead light, and the drum's rig has nothing to lift a shaded vertical surface.

Measured (all at `garden.HERO_SHOTS["tree"]`, Vulkan 1.4.318 Forward+):

| | trunk, linear Y | trunk crushed |
|---|---|---|
| shipped | 0.00526 | 95.3% |
| shadow casters 24 → 0, nothing else changed | **0.02277** | **0.0%** |
| the ground it stands on, shipped | 0.23109 | 0.0% |

×4.33 on the trunk against ×1.50 on the ground in the same pair, so ×2.9 is shadow on the
trunk specifically. And the arithmetic agrees from the other side: summing Godot's own
`pow(1 - d/range, attenuation)` over all 60 sources in `station/generated/scene/drum/scene.json`
(`scratchpad/mat4r/irradiance.py`, which is a small standalone script anyone can re-run),
**direct** irradiance on a vertical trunk face is **80.8** against **102.2** on the ground —
×1.26, nowhere near the ×44 the render shows. The missing factor is occlusion.

**No specific number is proposed, and deliberately.** `CLAUDE.md`'s own session-4m lesson is
that a room's level must be re-measured before its exposure is touched, and that *ambient buys
level and spends contrast* — so a drum ambient lift is exactly the knob that would flatten the
drum to fix one tree. The two candidates worth measuring, in this order:

1. **A bounce/fill term for the drum only.** The ground under the tree is at linear Y 0.231; a
   fill proportional to it, cull-masked away from the sky, is physically what is missing —
   there is no GI in this renderer and a real field bounces.
2. **`--soft-fill` for the drum shot.** It exists for the corridor. CLAUDE.md records it as
   nearly inert on p5 there (6 → 24 moves p5 ×1.11), so measure before believing it.

The control that decides it is already written: `--shadow-lights 0` is the ceiling of what any
fill can buy, and anything that gets the trunk from 0.00526 to within a factor of two of
0.02277 without moving the ground more than ×1.1 is the right answer.

---

## 3. `docs/aaa-scorecard.json` — one finding's evidence is 86% about something else

`garden_townscape`'s finding (the one quoted in `STATE.md` too) reads:

> *"The trunk is 1,244 triangles with a fluted section that CANNOT BE SEEN at value 0.135, and
> docs/garden-4q-after-tree.png measures crushed 25.49% -- the worst in the drum set. The tree
> goes to silhouette. Needs its own measured derivation."*

Three corrections, all measured, all in INV-571:

* **"crushed 25.49%" is not evidence about the bark.** Painting the bark an albedo-0.90 white
  moves the whole frame's crushed fraction to **21.95%** — so the bark and its branches own
  **3.61 of the 25.49 points** and the canopy and the shadowed town block own the rest.
* **"Needs its own measured derivation" is the wrong remedy.** It has one, pinned to
  `garden.png`'s planted bank at luminance 0.132; what it needed was a measurement of the
  LIGHT, and that is item 2 above.
* **"the overturning condition is met" is false.** The entry's *"any near-field frame of a tree
  in the drum"* sits under a source field opening *"NO FRAME MEASURES THIS"* and means an
  authority-1 or -2 frame. `docs/garden-4q-after-tree.png` is our own render, and an albedo
  cannot be measured off a picture drawn with that albedo. `materials.py`'s wording is
  tightened so this reading is no longer available.

The finding's *symptom* stands: the trunk is 95.3% crushed and its flutes cannot be seen. Only
its cause and its owner change.

---

## 4. `station/vista.py` — `PANE_TRANSMITTANCE` is now a second copy of a number

`materials.viewport_glazing.transmittance = 0.840` (INV-570) is the same 0.840 as
`vista.PANE_TRANSMITTANCE`, and two copies of a computed number is the defect this project
already records for `budget.py`'s cached collision total.

```diff
-PANE_TRANSMITTANCE = 0.840
+# The pane's transmission is a property of the pane, and the pane is a material.
+# INV-570 moved it there; this reads it rather than restating it.
+PANE_TRANSMITTANCE = materials.BY_NAME["viewport_glazing"].transmittance
```

`materials._selftest` currently asserts the two agree (`"vista.py's copy of T agrees with the
material's"`, and it fails when they do not — watched, with T withdrawn, in
`scratchpad/mat4r/selftest-PREFIX-CONTROL.log`). **When this patch lands that check becomes
trivially true and should be deleted**, which is said in the check's own comment.

`godot/scripts/vista.gd::glaze()` needs no change: it already skips a surface whose material
is transmissive and reports the count, which is how the library change was verified from the
engine side. It is now a **no-op that reports zero**, and could be retired entirely at
whoever owns it's convenience — but only after item 4 of `PATCHES-4r-windows.md` (the shipped
build mounting the vista) is settled, because it is still the only thing that would catch a
pane whose material lost its transmittance.

---

## 5. Nothing to apply — two things to know

**`station/drum_ground.py` paints 12 m of ground as `hedge`.** At (20°, z 4700) the
`ground_hedge` band runs 20.0°–22.5°, about 12 m across, and it is the whole left half of the
near field's half-distance frame. The module's own comment says the hedge inside it "is 2 m
tall, 1 m wide" and "belongs in the material, not the field" — so 11 of those 12 m are rough
grass, painted with a material measured on a hedgerow at 400 m and carrying no texture. This
is a *land-use* question as much as a material one, so it is left with its measurement rather
than fixed from one side: **40.0% of that frame is ground below the horizon with no texture map
at all.** `materials.UNTEXTURED_BY_DESIGN` now names it with the number.

**`materials.py`'s generator-literal scan reports four false positives**, and they are not
this session's: `drum_endcaps` is a *place key* in `directory.py`, and `ground_r`,
`ground_cullable`, `ground_total` are `__slots__` entries and dict keys in `drum_dressing.py`
and `occluders.py`. The scan restricts itself to established prefixes and these clear it by
accident. It is a two-failure floor on `python3 station/materials.py` (the other is
`alien_status_lamp_dark`) and it predates this session — baseline captured in
`scratchpad/mat4r/selftest-BASELINE.log` at 1982be0, before anything here was written.
