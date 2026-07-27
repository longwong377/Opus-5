# Station materials

**Everything in this directory except this file is generated.** The source of
truth is `station/materials.py`; the `.tres` files and `textures/` are its
output, and each one says so in its own header.

```bash
python3 station/materials.py                 # self-test, 523 assertions
python3 station/materials.py --export        # rewrite this directory
godot --headless --path godot --import
godot --headless --path godot --script res://scripts/verify_materials.gd
```

Editing a `.tres` by hand changes what renders until the next export overwrites
it, and the change is then lost with no diff to show for it.

## Why a generator and not a folder

This directory had twelve hand-written materials. `godot/scenes/drum.tscn` had
twenty-eight more, as `StandardMaterial3D` sub-resources inside the scene, with
no mechanical relationship to these. Two descriptions of the same surfaces is
the failure mode the whole project is built to avoid — CLAUDE.md's fourth hard
rule is *"inside and outside come from the same schema… consistency is by
construction, not by discipline"* — and materials were quietly becoming the
exception. They are now declared once, in Python, and exported.

The scene's own header invited this: *"Promoting one to a .tres is a two-line
change."* Its measured values were carried over verbatim rather than
re-derived, because two independent samples of one frame that disagree are
worse than one.

## What is here

| | count | |
|---|---|---|
| `*.tres` | 59 | one `StandardMaterial3D` each |
| `textures/*.png` | 21 | 7 procedural trim sheets × albedo / normal / ORM |
| `material_rules.gen.txt` | 1 | the `material_rules` tables, to paste into a scene |

Coverage: hull exterior and its greebling, the interior corridor kit, drum
ground land-use bands, end-cap courses, the guideway truss and its light runs,
tram livery and saloon, the core tube, signage, hazard marking, and a magenta
`unbound` fallback.

## Textures

Original work, generated from `hashlib.blake2b` — no show asset is
redistributed and no external asset is used. They are trim sheets in ADR 0002's
sense: **tileable and projected triplanar**, because the glTF export carries
POSITION and NORMAL only and there are no UVs to place a decal against.

`signage_panel` is the one exception and is *not* triplanar: a sign has a
reading direction, and projecting it three ways mirrors the lettering on half
the faces. Any mesh carrying that group has to ship UVs.

ORM packing is AO in red, roughness in green, metallic in blue, which is what
`ao_texture_channel = 0`, `roughness_texture_channel = 1` and
`metallic_texture_channel = 2` in each `.tres` read.

An albedo map multiplies `albedo_color`, so the maps are centred on
`TEX_MEAN = 0.72` and each material's emitted tint is its measured albedo
divided by that. `Material.albedo` in the Python library stays in measured
units; only the file Godot reads carries the compensation.

## Texture memory

Measured, not modelled — run the importer and weigh the output:

```bash
ls -l godot/.godot/imported/*.s3tc.ctex | awk '{s+=$5} END {print s/1048576" MB"}'
```

| | |
|---|---|
| 21 maps, BC1 + BC5, mipmapped | **38.67 MB** |
| same maps at Godot's default import (`compress/mode=0`) | 174.0 MB |
| share of the 12 GB VRAM target | **0.31%** |

`station/materials.py --export` patches each `.import` to
`compress/mode=2` and `mipmaps/generate=true`, because Godot's PNG defaults are
uncompressed and un-mipped. Mips are not optional here: the hull sheet repeats
every 48 m on a body 8 km long, and without them the far end of the station
boils.

## Colour

Every albedo traces to a named frame and a named pixel region, recorded in
`station/materials.py`'s `PROVENANCE`, and the method is recorded with it: each
frame is grey-world balanced first (they all carry a cast, and not the same one
twice), only ratios within one frame are trusted, and one declared constant —
`ALBEDO_ANCHOR` — sets the absolute level for everything derived from
`grey level 1.webp`.

The finding that shapes the whole library: **balanced and clustered, every
large surface in every station interior frame in the reference set sits at
saturation 0.02–0.16.** The station is near-neutral; the colour is in the
lighting and in a small accent set. `NEGATIVE_RESULTS` records the ochre dado
that was nearly encoded before the same wall was checked under a different
light in the same frame.

## An emissive is not a light

Unchanged from before and still the thing to remember: in Forward+ an emissive
surface glows but illuminates nothing unless global illumination is on. Every
`light_*`, `*_lamp`, `marker_light_*` and `*_rimlight` material needs a real
`OmniLight3D` or `SpotLight3D` placed alongside it. The material is the visible
fitting; the light is a separate object, and it belongs to the scene.
