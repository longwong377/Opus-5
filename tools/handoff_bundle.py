#!/usr/bin/env python3
"""Cut a standalone glTF bundle of everything hand-built, for another engine.

WHY THIS EXISTS. This project's geometry is 6.6 GB on disk, split by DECK --
`blue_0_0.glb` alone is 445 MB -- because Godot streams cells and never needed
a place on its own. Handing that to a browser game is impossible: the smallest
useful unit is a whole deck. But `tools/export_scene.py --shot interior --room
<key>` already builds ONE place and writes its own `.glb`, and nothing had ever
run it across the register.

WHAT IT SELECTS, and the rule is stated rather than curated. A place qualifies
if its `module` is one of the twelve in `bespoke.BESPOKE_GEOMETRY` -- the
modules that build a named shape in hand-written code, as against `rooms.py`,
which assembles the other 89 from a shared kit. Those 89 are real and they are
all geometrically distinct (`deck.py --degeneracy`), but they are variations of
one system and they score craft 1 on this project's own scorecard. The forty
here are the ones that would be a loss.

THE OUTPUT IS GEOMETRY ONLY, and that is a property of the exporter rather
than a decision here: `station/export_gltf.py` writes positions, normals and
group names, and PBR lives in Godot `.tscn` sub-resources bound BY GROUP NAME
from `materials.py`. So a consumer gets a grey model with meaningful part
names, and `materials.json` beside it carries the bindings so the look can be
rebuilt rather than guessed.

    python3 tools/handoff_bundle.py              # build into dist/b5-handoff
    python3 tools/handoff_bundle.py --list       # say what would be built
    python3 tools/handoff_bundle.py --only a,b   # just these keys
"""
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

OUT = os.path.join(ROOT, "dist", "b5-handoff")
INTERIOR = os.path.join(ROOT, "station/generated/scene/interior")

# Already exported, and not rebuilt here -- the exterior hull is not a "room"
# and `--shot interior` has no path to it.
PREBUILT = {
    "hull": ("station/generated/scene/exterior/hull.glb",
             "the complete exterior of the station, 8,047 m"),
    "hydroponics": ("station/generated/scene/interior/hydroponics.glb",
                    "the Garden -- hydroponics section interior"),
}


def bespoke_modules():
    """The twelve modules that build their own geometry, read from the source.

    Read rather than listed, so this cannot drift from `bespoke.py`.
    """
    src = open(os.path.join(ROOT, "station/bespoke.py"), encoding="utf-8").read()
    m = re.search(r"BESPOKE_GEOMETRY\s*[:=].*?\{(.*?)\n\}", src, re.S)
    if not m:
        raise SystemExit("handoff: cannot find BESPOKE_GEOMETRY in bespoke.py")
    return set(re.findall(r'^\s*"([a-z_0-9]+)"\s*:', m.group(1), re.M))


def places():
    import directory as dr                                      # noqa: PLC0415
    mods = bespoke_modules()
    return [q for q in dr.PLACES if q.get("module") in mods]


def glb_stats(path):
    """Triangles, meshes and the bounding box, read out of the file itself.

    Not taken from the exporter's report: what ships is what the consumer
    loads, and this is the only reading that describes the shipped bytes.
    """
    with open(path, "rb") as f:
        f.read(12)
        jlen, _ = struct.unpack("<II", f.read(8))
        j = json.loads(f.read(jlen))
    tris = 0
    lo = [1e18] * 3
    hi = [-1e18] * 3
    for mesh in j.get("meshes", []):
        for pr in mesh.get("primitives", []):
            if "indices" in pr:
                tris += j["accessors"][pr["indices"]]["count"] // 3
            ai = pr.get("attributes", {}).get("POSITION")
            if ai is not None:
                a = j["accessors"][ai]
                for i in range(3):
                    lo[i] = min(lo[i], a["min"][i])
                    hi[i] = max(hi[i], a["max"][i])
    ok = ("scene" in j and "scenes" in j
          and j.get("asset", {}).get("version", "").startswith("2"))
    return {
        "triangles": tris,
        "meshes": len(j.get("meshes", [])),
        "materials": len(j.get("materials", [])),
        "size_bytes": os.path.getsize(path),
        "loads_in_three_js": ok,
        "bbox_m": [round(hi[i] - lo[i], 1) for i in range(3)],
    }


def build_one(key, timeout=900):
    """`export_scene.py --shot interior --room key` -> scene/interior/key.glb."""
    t0 = time.time()
    r = subprocess.run(
        [sys.executable, "tools/export_scene.py", "--shot", "interior",
         "--room", key],
        cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    glb = os.path.join(INTERIOR, f"{key}.glb")
    if r.returncode != 0 or not os.path.exists(glb):
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        return None, (tail[-1] if tail else f"exit {r.returncode}")
    return glb, round(time.time() - t0, 1)


def materials_table():
    """The group-name -> material bindings, so the look can be rebuilt.

    `export_gltf.py` writes no materials, by design -- the look lives in the
    `.tscn`. This is the join, dumped as data a non-Godot consumer can read.
    """
    import materials as M                                       # noqa: PLC0415
    FIELDS = ("title", "albedo", "roughness", "metallic", "specular",
              "transmittance", "emission", "emission_energy", "texture",
              "uv_scale", "triplanar", "normal_scale", "binds", "scenes",
              "source")
    out = {}
    for m in M.MATERIALS:
        out[m.name] = {f: getattr(m, f) for f in FIELDS
                       if getattr(m, f, None) not in (None, "", (), 0.0)}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="say what would be built")
    ap.add_argument("--only", default="", help="comma-separated place keys")
    ap.add_argument("--restage", action="store_true",
                    help="rebuild manifest, materials and textures from the "
                         "glb files already staged; build no geometry")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    rows = places()
    if a.only:
        want = {k for k in a.only.split(",") if k}
        rows = [q for q in rows if q["key"] in want]
    rows.sort(key=lambda q: (q["module"], q["key"]))

    if a.list:
        print(f"{len(rows)} places from {len(bespoke_modules())} hand-built modules")
        for q in rows:
            print(f"  {q['module']:16} {q['key']:22} {q.get('name','')}")
        print(f"\nplus {len(PREBUILT)} already exported: {', '.join(PREBUILT)}")
        return 0

    os.makedirs(a.out, exist_ok=True)
    manifest = {"places": [], "failed": []}

    if a.restage:
        # EVERY ROW READ BACK OUT OF THE SHIPPED BYTES. A restage exists so a
        # single late addition does not cost a 12-minute rebuild of the other
        # 34 -- and it must not shrink the manifest to whatever was built last,
        # which is what `--only` did to it once already.
        names = {q["key"]: q for q in places()}
        for f in sorted(os.listdir(a.out)):
            if not f.endswith(".glb"):
                continue
            key = f[:-4]
            q = names.get(key, {})
            row = {"key": key,
                   "name": q.get("name", PREBUILT.get(key, ("", ""))[1]),
                   "module": q.get("module", "-"), "file": f,
                   **glb_stats(os.path.join(a.out, f))}
            manifest["places"].append(row)
        _finish(a.out, manifest)
        return 0

    for key, (rel, blurb) in PREBUILT.items():
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            manifest["failed"].append({"key": key, "why": "not on disk"})
            continue
        dst = os.path.join(a.out, f"{key}.glb")
        shutil.copy2(src, dst)
        manifest["places"].append({"key": key, "name": blurb, "module": "-",
                                   "file": f"{key}.glb", **glb_stats(dst)})
        print(f"  copied  {key:22} {os.path.getsize(dst)/1048576:7.1f} MB")

    for i, q in enumerate(rows, 1):
        key = q["key"]
        if key in PREBUILT:
            continue
        print(f"  [{i}/{len(rows)}] {key} ...", flush=True)
        glb, why = build_one(key)
        if glb is None:
            manifest["failed"].append({"key": key, "module": q.get("module"),
                                       "why": why})
            print(f"     FAILED -- {why}")
            continue
        dst = os.path.join(a.out, f"{key}.glb")
        shutil.copy2(glb, dst)
        st = glb_stats(dst)
        manifest["places"].append({
            "key": key, "name": q.get("name", ""), "module": q.get("module"),
            "file": f"{key}.glb", "build_seconds": why, **st})
        print(f"     {st['size_bytes']/1048576:7.1f} MB  {st['triangles']:>9,} tri"
              f"  bbox {st['bbox_m']}")

    _finish(a.out, manifest)
    return 0


def _finish(out, manifest):
    """Materials, textures and the manifest -- the metadata half of a bundle.

    Split out so `--restage` and a full build produce the SAME metadata; two
    code paths writing one manifest is how the two would drift.
    """
    mats = materials_table()
    with open(os.path.join(out, "materials.json"), "w", encoding="utf-8") as f:
        json.dump(mats, f, indent=1, sort_keys=True, default=str)

    # THE TEXTURES, because without them the bundle is grey and the material
    # table is a list of names nobody can resolve. 49 PNGs in albedo/normal/ORM
    # triples; the `.import` sidecars beside them are Godot's and are not
    # copied.
    tex_src = os.path.join(ROOT, "godot/materials/textures")
    tex_dst = os.path.join(out, "textures")
    n_tex = 0
    if os.path.isdir(tex_src):
        os.makedirs(tex_dst, exist_ok=True)
        for f in sorted(os.listdir(tex_src)):
            if f.endswith(".png"):
                shutil.copy2(os.path.join(tex_src, f),
                             os.path.join(tex_dst, f))
                n_tex += 1

    manifest["materials"] = len(mats)
    manifest["textures"] = n_tex
    tot = sum(p["size_bytes"] for p in manifest["places"])
    manifest["total_bytes"] = tot
    manifest["total_triangles"] = sum(p["triangles"] for p in manifest["places"])
    bad = [p for p in manifest["places"] if not p["loads_in_three_js"]]
    manifest["all_files_valid_gltf2"] = not bad
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    print(f"\n{len(manifest['places'])} models, {tot/1048576:.1f} MB, "
          f"{manifest['total_triangles']:,} triangles")
    print(f"{len(mats)} materials, {n_tex} textures -> {out}")
    if bad:
        print(f"WARNING -- {len(bad)} file(s) are not loadable glTF 2: "
              + ", ".join(p["file"] for p in bad))
    if manifest["failed"]:
        print(f"{len(manifest['failed'])} could not be built:")
        for r in manifest["failed"]:
            print(f"   {r['key']:22} {r['why'][:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
