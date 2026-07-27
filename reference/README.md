# Reference Intake

Drop reference material here. This is the ground truth the entire project is built from.

**Nothing gets modelled until the reference for it is in this folder and catalogued in `00-INDEX.md`.**

## How to upload

Easiest path: on GitHub, open the folder you want → **Add file → Upload files** → drag in as many
as you like → commit to `claude/babylon5-station-sim-discussion-kgp4by`.

You can also drag a whole batch into `20-unsorted-dump/` and I will sort and file them. Do not
spend time organising if it slows you down — an unsorted pile in the repo beats a tidy pile on
your hard drive.

## Naming

Optional, not required. If a filename is easy to give, this helps me cross-check canon:

```
s03e12_zocalo_wide_01.jpg          episode-sourced frame
bts_model_exterior_dorsal.png      behind-the-scenes / production art
plan_bluesector_deck7.jpg          schematic or deck plan
fan_hull_greeble_detail.jpg        fan-made (flag it — treated as lower authority)
unknown_corridor_junction.jpg      no idea where it's from, still useful
```

Anything unnamed still gets used. I catalogue by content, not filename.

## Source authority ranking

When two references disagree, I resolve in this order. Tell me if you want it different:

1. **On-screen footage** — the show itself, any season. Highest authority.
2. **Production material** — Foundation Imaging / Ron Thornton model shots, set blueprints,
   art department drawings, JMS's own notes and script directions.
3. **Licensed print** — official guides, technical manuals, the RPG deck plans.
4. **Fan reconstruction** — the Lurker's Guide, fan schematics, community 3D models.
5. **My inference** — where nothing exists, I extrapolate from adjacent canon and log the
   invention explicitly in `00-INDEX.md` so it is never mistaken for canon.

## What is most valuable

Ranked by how much it unblocks. Anything from the top three moves the project forward fastest:

1. **Cutaways, cross-sections, sector maps, deck plans** → `02-station-cutaways-and-plans/`
   These determine the parametric model everything else hangs off. Most valuable material there is.
2. **Exterior views from every angle**, especially clean orthographic-ish shots, scale
   comparisons, and anything showing the hull segmentation → `01-station-exterior/`
3. **Corridor / door / lift / wall-panel detail** → `10-interiors-generic-kit/`
   The modular kit is reused across ~90% of interior surface area, so accuracy here compounds.
4. Everything else, in the folder it belongs to.

Multiple angles of the same thing are *more* useful than one perfect shot — I reconstruct
3D geometry from viewpoint disagreement. Blurry is fine. Duplicates are fine.

## Folders

| Folder | Contents |
|---|---|
| `01-station-exterior` | Hull, orientation views, scale diagrams, VFX shots, lighting on the exterior |
| `02-station-cutaways-and-plans` | Sector maps, deck plans, cross-sections, schematics, dimension callouts |
| `03-sector-blue` | C&C, observation dome, main docking bays, customs, command staff quarters |
| `04-sector-red` | Zócalo, casino, Fresh Air restaurant, guest quarters, judiciary, commercial |
| `05-sector-green` | Ambassadorial wing, Council Chambers, alien sector, non-oxygen environments |
| `06-sector-brown-downbelow` | Industrial, maintenance, unfinished levels, Downbelow, lurker areas |
| `07-sector-grey` | Storage, machinery, Grey 17, poorly-mapped areas |
| `08-sector-yellow-engineering` | Fusion reactors, life support, engineering, aft sections |
| `09-garden-core-and-transit` | Central garden/drum, agro sections, core shuttle, axis, lifts, transport tubes |
| `10-interiors-generic-kit` | Corridors, doors, lift cars, wall panels, floors, ceilings, railings, signage placement |
| `11-props-and-technology` | Links, identicards, BabCom terminals, PPGs, data crystals, furniture, medlab equipment |
| `12-starfury` | Aurora & Thunderbolt exteriors, cockpit interior, instruments, cobra bay launch |
| `13-other-ships` | White Star, Omega, Sharlin, G'Quan, Vorchan, shuttles, transports, jump gate |
| `14-characters-and-uniforms` | EarthForce S1 and S2+ uniforms, security, medical, Psi Corps, civilian dress |
| `15-races-and-makeup` | Minbari, Narn, Centauri, Vorlon, Drazi, pak'ma'ra, Gaim, Brakiri, Vree, and others |
| `16-signage-typography-ui` | Fonts, sector markings, screen graphics, HUDs, logos, wayfinding |
| `17-lighting-and-color` | Lighting refs, colour scripts, mood frames per sector |
| `18-audio-notes` | Notes or links on ambience, door sounds, PA announcements, engine tone |
| `19-video-clips` | Short clips — motion reference for doors, lifts, launches, crowds |
| `20-unsorted-dump` | Anything. I will file it. |
| `21-QUARANTINE-animated-film` | **Do not model from.** 2023 animated feature, not the original series — wrong source, wrong era, reinterpreted designs. See the README in that folder. |

## A note on what we build from this

Reference is used to *understand and reconstruct*, not to copy. All geometry, textures, audio
and text in this project are authored originally from scratch. No show assets, models, textures
or audio are redistributed in this repository. Babylon 5 is the property of its rightsholders;
this is a non-commercial fan reconstruction.
