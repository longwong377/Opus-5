#!/usr/bin/env python3
"""A longitudinal cutaway of the station, drawn from the schema.

THE OWNER ASKED TO SEE WHAT WE ARE BUILDING, and until now there was no way to.
This project has 1,978 measured hull radius samples, five sector extents, a ring
stack per sector and 118 located places, and every one of those numbers lived in
a JSON file or a register nobody can picture. A drawing made from them is not
decoration: it is the same data the generators consume, seen side-on, so a
mistake in the schema shows up as a mistake in the picture.

NOTHING HERE IS DRAWN BY HAND. The hull outline is `radius_profile.samples`.
The sector bands are `sectors.extents_m`. The rings are `interior.ring_radii`.
The dots are `directory.PLACES` at their own `(z_m, angle_deg)` mapped onto the
ring they are addressed to. If the picture looks wrong, the schema is wrong.

    python3 tools/cutaway.py --out docs/cutaway.svg
    python3 tools/cutaway.py --selftest

SVG rather than a raster, because the station is 8,047 m long and 956 m across
and the interesting features are metres wide -- a 1600 px raster gives 5 m a
pixel and a docking bay is one dot. SVG lets the owner zoom.
"""
import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402

# Sector colours. Chosen to match the show's own names -- Blue Sector is blue --
# because a legend a reader has to consult is a legend that failed.
SECTOR_RGB = {
    "blue": "#4a76c8", "red": "#c04a4a", "green": "#4aa85e",
    "grey": "#8a8f98", "yellow": "#c9a63a", "brown": "#8a6a45",
}
INK = "#e8eaed"
BG = "#11141a"
GRID = "#2a303a"


def _hull(schema, profile):
    """The upper half of the hull outline, as (z, r) in metres."""
    return [(p["z_m"], p["radius_m"]) for p in profile]


def _rings(schema, profile):
    """(sector, z0, z1, [(r_inner, r_outer, id)]) per sector."""
    ext = schema["sectors"]["extents_m"]
    out = []
    for sec in ("yellow", "green", "grey", "red", "blue"):
        if sec not in ext:
            continue
        e = ext[sec]
        rr = [(r["r_inner"], r["r_outer"], r["id"])
              for r in it.ring_radii(schema, profile, sec)]
        out.append((sec, float(e["z0"]), float(e["z1"]), rr))
    return out


def _places():
    """(key, z, radius, sector) for every located place.

    RADIUS COMES FROM THE ADDRESS, not from a footprint. A place carries
    `(sector, ring, deck)` and the deck stack knows what radius that is, so the
    dot lands where the generators would build it -- which is the only version
    of this drawing worth making.
    """
    schema, profile = it.load()
    out = []
    for q in dr.PLACES:
        sec = q.get("sector")
        try:
            # AT THE PLACE'S OWN Z. Without it "ring 0" resolves against the
            # sector's widest cylinder and 14 of 118 places landed outside the
            # hull -- `cnc` by 94.7 m. See `interior.rings_fitting_at`.
            rr = it.ring_radii(schema, profile, sec, z_m=q.get("z_m"))
        except Exception:                                      # noqa: BLE001
            continue
        ri = q.get("ring")
        if not isinstance(ri, int) or ri >= len(rr):
            continue
        r = rr[ri]["r_mid"]
        # If the deck stack resolves, use the deck's own floor radius.
        try:
            decks = it.decks_in_ring(schema, profile, sec, ri,
                                     z_m=q.get("z_m")) or []
            lab = sorted({p["deck"] for p in dr.PLACES
                          if p.get("sector") == sec and p.get("ring") == ri})
            di = (q["deck"] if lab and max(lab) < len(decks)
                  else (lab.index(q["deck"]) if q["deck"] in lab else 0))
            if 0 <= di < len(decks):
                r = decks[di]["floor_r_m"]
        except Exception:                                      # noqa: BLE001
            pass
        out.append((q["key"], float(q.get("z_m", 0.0)), float(r), sec))
    return out


def draw(schema, profile, width_px=2400, pad=90, label_every=1):
    """The whole cutaway as an SVG string."""
    hull = _hull(schema, profile)
    zmax = max(z for z, _r in hull)
    rmax = max(r for _z, r in hull)
    # One scale for both axes -- a cutaway with a stretched z is a lie about
    # proportion, and proportion is most of what this drawing is for.
    sx = (width_px - 2 * pad) / zmax
    h_px = int(2 * rmax * sx + 2 * pad + 150)
    cy = pad + rmax * sx

    def X(z):
        return pad + z * sx

    def Y(r):
        return cy - r * sx

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" '
         f'height="{h_px}" viewBox="0 0 {width_px} {h_px}">',
         f'<rect width="100%" height="100%" fill="{BG}"/>',
         '<g font-family="DejaVu Sans, Helvetica, sans-serif">']

    # --- sector bands, drawn first so everything sits on them --------------
    for sec, z0, z1, rr in _rings(schema, profile):
        col = SECTOR_RGB.get(sec, "#666")
        ro = max((b for _a, b, _i in rr), default=0.0)
        o.append(f'<rect x="{X(z0):.1f}" y="{Y(ro):.1f}" '
                 f'width="{(z1 - z0) * sx:.1f}" height="{2 * ro * sx:.1f}" '
                 f'fill="{col}" fill-opacity="0.10"/>')
        # ring boundaries, mirrored above and below the axis
        for r_in, r_out, _rid in rr:
            for r in (r_in, r_out):
                if r <= 0:
                    continue
                for yy in (Y(r), Y(-r)):
                    o.append(f'<line x1="{X(z0):.1f}" y1="{yy:.1f}" '
                             f'x2="{X(z1):.1f}" y2="{yy:.1f}" '
                             f'stroke="{col}" stroke-opacity="0.45" '
                             f'stroke-width="1"/>')
        o.append(f'<line x1="{X(z0):.1f}" y1="{Y(ro) - 26:.1f}" '
                 f'x2="{X(z0):.1f}" y2="{Y(-ro) + 26:.1f}" stroke="{col}" '
                 f'stroke-opacity="0.7" stroke-width="1.5"/>')
        o.append(f'<text x="{X((z0 + z1) / 2):.1f}" y="{Y(ro) - 34:.1f}" '
                 f'fill="{col}" font-size="26" font-weight="600" '
                 f'text-anchor="middle">{sec.upper()}</text>')
        o.append(f'<text x="{X((z0 + z1) / 2):.1f}" y="{Y(ro) - 12:.1f}" '
                 f'fill="{INK}" fill-opacity="0.55" font-size="15" '
                 f'text-anchor="middle">'
                 f'{z0:,.0f}-{z1:,.0f} m &#183; {len(rr)} rings</text>')

    # --- the hull, both halves --------------------------------------------
    up = " ".join(f"{X(z):.1f},{Y(r):.1f}" for z, r in hull)
    dn = " ".join(f"{X(z):.1f},{Y(-r):.1f}" for z, r in hull)
    o.append(f'<polyline points="{up}" fill="none" stroke="{INK}" '
             f'stroke-width="2.2"/>')
    o.append(f'<polyline points="{dn}" fill="none" stroke="{INK}" '
             f'stroke-width="2.2"/>')
    o.append(f'<line x1="{X(0):.1f}" y1="{cy:.1f}" x2="{X(zmax):.1f}" '
             f'y2="{cy:.1f}" stroke="{GRID}" stroke-width="1" '
             f'stroke-dasharray="8 8"/>')

    # --- the 118 places ----------------------------------------------------
    pl = _places()
    for key, z, r, sec in pl:
        col = SECTOR_RGB.get(sec, "#999")
        o.append(f'<circle cx="{X(z):.1f}" cy="{Y(r):.1f}" r="3.4" '
                 f'fill="{col}" fill-opacity="0.95"/>')
        o.append(f'<circle cx="{X(z):.1f}" cy="{Y(-r):.1f}" r="1.6" '
                 f'fill="{col}" fill-opacity="0.35"/>')

    # A few anchors named, or the drawing is 118 anonymous dots. The ones a
    # viewer of the show would look for first.
    named = {"cnc", "zocalo", "docking_bays", "the_garden", "council_chamber",
             "customs_north", "medlab_one", "downbelow", "brig",
             "fusion_core", "cobra_bays", "ambassadorial_suites"}
    for key, z, r, sec in pl:
        if key not in named:
            continue
        o.append(f'<circle cx="{X(z):.1f}" cy="{Y(r):.1f}" r="6" fill="none" '
                 f'stroke="{INK}" stroke-width="1.6"/>')
        o.append(f'<text x="{X(z) + 9:.1f}" y="{Y(r) - 7:.1f}" fill="{INK}" '
                 f'font-size="15">{key.replace("_", " ")}</text>')

    # --- scale bar and title ----------------------------------------------
    bar_m = 1000.0
    bx, by = pad, h_px - 58
    o.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx + bar_m * sx:.1f}" '
             f'y2="{by:.1f}" stroke="{INK}" stroke-width="3"/>')
    for t in (0, bar_m):
        o.append(f'<line x1="{bx + t * sx:.1f}" y1="{by - 7:.1f}" '
                 f'x2="{bx + t * sx:.1f}" y2="{by + 7:.1f}" stroke="{INK}" '
                 f'stroke-width="3"/>')
    o.append(f'<text x="{bx + bar_m * sx / 2:.1f}" y="{by + 26:.1f}" '
             f'fill="{INK}" font-size="16" text-anchor="middle">1,000 m</text>')
    o.append(f'<text x="{pad}" y="{pad - 46}" fill="{INK}" font-size="30" '
             f'font-weight="600">BABYLON 5 &#183; longitudinal cutaway</text>')
    o.append(f'<text x="{pad}" y="{pad - 22}" fill="{INK}" fill-opacity="0.6" '
             f'font-size="16">{zmax:,.0f} m long &#183; {2 * rmax:,.0f} m '
             f'across at z={max(hull, key=lambda p: p[1])[0]:,.0f} m &#183; '
             f'{len(pl)} located places &#183; drawn from the schema, not by '
             f'hand</text>')
    o.append("</g></svg>")
    return "\n".join(o)


def draw_png(schema, profile, width_px=2400, pad=90):
    """The same cutaway as a raster, because nothing here can rasterise SVG.

    Not a second drawing: it consumes `_hull`, `_rings` and `_places`, the same
    three functions the SVG does, so the two cannot disagree about the station.
    It exists because there is no `rsvg-convert`, `inkscape` or `cairosvg` in
    this container and CLAUDE.md's verification rule is to LOOK at the output.
    A drawing nobody can open is a drawing nobody checked.
    """
    from PIL import Image, ImageDraw                            # noqa: PLC0415

    hull = _hull(schema, profile)
    zmax = max(z for z, _r in hull)
    rmax = max(r for _z, r in hull)
    sx = (width_px - 2 * pad) / zmax
    h_px = int(2 * rmax * sx + 2 * pad + 150)
    cy = pad + rmax * sx

    def X(z):
        return pad + z * sx

    def Y(r):
        return cy - r * sx

    im = Image.new("RGB", (width_px, h_px), BG)
    d = ImageDraw.Draw(im, "RGBA")

    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    for sec, z0, z1, rr in _rings(schema, profile):
        col = rgb(SECTOR_RGB.get(sec, "#666666"))
        ro = max((b for _a, b, _i in rr), default=0.0)
        d.rectangle([X(z0), Y(ro), X(z1), Y(-ro)], fill=col + (26,))
        for r_in, r_out, _rid in rr:
            for r in (r_in, r_out):
                if r <= 0:
                    continue
                for yy in (Y(r), Y(-r)):
                    d.line([X(z0), yy, X(z1), yy], fill=col + (115,), width=1)
        d.line([X(z0), Y(ro) - 26, X(z0), Y(-ro) + 26], fill=col + (180,),
               width=2)
        d.text((X((z0 + z1) / 2) - 22, Y(ro) - 52), sec.upper(), fill=col)
        d.text((X((z0 + z1) / 2) - 46, Y(ro) - 32),
               f"{z0:,.0f}-{z1:,.0f} m  {len(rr)} rings", fill=(150, 155, 165))

    ink = rgb(INK)
    for sign in (1, -1):
        pts = [(X(z), Y(sign * r)) for z, r in hull]
        d.line(pts, fill=ink, width=2)
    d.line([X(0), cy, X(zmax), cy], fill=rgb(GRID), width=1)

    pl = _places()
    out_of_hull = []
    for key, z, r, sec in pl:
        col = rgb(SECTOR_RGB.get(sec, "#999999"))
        near = min(hull, key=lambda p, z=z: abs(p[0] - z))
        bad = r > near[1] + 1.0
        if bad:
            out_of_hull.append((key, z, r, near[1]))
        # OUTSIDE THE HULL IS DRAWN IN RED AND RINGED. 14 of the 118 are
        # addressed to a radius the hull does not have at their z -- `cnc` is
        # 94.7 m outside the ship -- and a drawing that hid that would be
        # worse than no drawing.
        c = (230, 70, 70) if bad else col
        d.ellipse([X(z) - 4, Y(r) - 4, X(z) + 4, Y(r) + 4], fill=c)
        d.ellipse([X(z) - 2, Y(-r) - 2, X(z) + 2, Y(-r) + 2], fill=c + (110,))
        if bad:
            d.ellipse([X(z) - 9, Y(r) - 9, X(z) + 9, Y(r) + 9],
                      outline=(230, 70, 70), width=2)
            d.line([X(z), Y(r), X(z), Y(near[1])], fill=(230, 70, 70, 150),
                   width=1)

    named = {"cnc", "zocalo", "docking_bays", "the_garden", "council_chamber",
             "customs_north", "medlab_one", "downbelow", "brig",
             "fusion_core", "cobra_bays"}
    for key, z, r, _sec in pl:
        if key in named:
            d.text((X(z) + 10, Y(r) - 16), key.replace("_", " "), fill=ink)

    bar_m, bx, by = 1000.0, pad, h_px - 58
    d.line([bx, by, bx + bar_m * sx, by], fill=ink, width=3)
    for t in (0, bar_m):
        d.line([bx + t * sx, by - 7, bx + t * sx, by + 7], fill=ink, width=3)
    d.text((bx + bar_m * sx / 2 - 26, by + 10), "1,000 m", fill=ink)
    d.text((pad, pad - 62), "BABYLON 5  -  longitudinal cutaway", fill=ink)
    d.text((pad, pad - 42),
           f"{zmax:,.0f} m long, {2 * rmax:,.0f} m across, {len(pl)} located "
           f"places  -  drawn from the schema", fill=(150, 155, 165))
    if out_of_hull:
        d.text((pad, pad - 24),
               f"RED = addressed OUTSIDE the hull: {len(out_of_hull)} of "
               f"{len(pl)}", fill=(230, 70, 70))
    return im, out_of_hull


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    schema, profile = it.load()
    hull = _hull(schema, profile)
    check("the hull profile has samples", len(hull) > 500, str(len(hull)))
    zmax = max(z for z, _r in hull)
    check("the hull is the station's stated length",
          abs(zmax - 8047.0) < 1.0, f"{zmax}")
    rmax = max(r for _z, r in hull)
    check("the widest point matches the schema",
          abs(2 * rmax - schema["radius_profile"]
              ["finding"]["envelope_diameter_m"]) < 2.0,
          f"{2 * rmax:.1f}")

    # EVERY PLACE MUST LAND INSIDE THE HULL. This is the assertion that makes
    # the drawing worth making: a dot outside the outline is a place whose
    # address puts it in vacuum, and no render would ever show that because
    # nothing renders the address.
    outside = []
    for key, z, r, _sec in _places():
        near = min(hull, key=lambda p, z=z: abs(p[0] - z))
        if r > near[1] + 1.0:
            outside.append((key, round(z), round(r, 1), round(near[1], 1)))
    check("every located place is inside the hull", not outside,
          f"{len(outside)} outside: {outside[:4]}")

    pl = _places()
    check("every place resolves to a radius", len(pl) == len(dr.PLACES),
          f"{len(pl)} of {len(dr.PLACES)}")

    svg = draw(schema, profile)
    check("the drawing is emitted", svg.startswith("<svg") and len(svg) > 20000,
          f"{len(svg)} bytes")
    check("...and carries every place", svg.count("<circle") >= 2 * len(pl),
          f"{svg.count('<circle')} circles for {len(pl)} places")
    print(f"  {len(hull)} hull samples, {len(pl)} places, {len(svg):,} bytes")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="docs/cutaway.svg")
    ap.add_argument("--width", type=int, default=2400)
    ap.add_argument("--png", default="",
                    help="also write a raster, since nothing here "
                         "can rasterise SVG and a drawing nobody "
                         "can open is a drawing nobody checked")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    schema, profile = it.load()
    svg = draw(schema, profile, width_px=a.width)
    path = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(svg)
    print(f"{path}  {len(svg):,} bytes")
    if a.png:
        im, bad = draw_png(schema, profile, width_px=a.width)
        pp = a.png if os.path.isabs(a.png) else os.path.join(ROOT, a.png)
        im.save(pp)
        print(f"{pp}  {im.size[0]}x{im.size[1]}  "
              f"{len(bad)} places outside the hull")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
