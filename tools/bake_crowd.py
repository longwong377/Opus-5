#!/usr/bin/env python3
"""Write the shared crowd body library the runtime instances walkers against.

WHY THIS EXISTS AS ITS OWN TOOL, AND IT IS INSTANCE TEN OF THIS PROJECT'S
SIGNATURE DEFECT REACHING THE ONE PATH THAT SHIPS.

`walk.gd::_load_crowd_libs` resolves `crowd_lod<N>.glb` beside the crowd
placement list and draws every walker as an instance into it. Those files were
written in exactly one place -- inside `walkable.py::_bake`, under `if crowd:`,
as a side effect of running a WALK TEST -- and `deck.py`'s own build path never
called it. So the dev checkout had 0 of them, the package therefore shipped 0
of them, and the launcher printed:

    walk: 83 room occupant(s) have a timetable and NO shared body library
          -- they cannot be drawn
    ERROR: walk: could not load any crowd library

A station simulation with nobody in it. Every craft judgement in session 4t
scored a frame rendered from the DEV TREE, where `render_shot.gd` builds bodies
directly and never consults this library at all, so nine rounds of review
looked at populated rooms and the shipped artefact was empty. That is this
file's own rule -- *a thing is built more than once in this project, and a gate
on one build path says nothing about the other* -- landing on the build the
player actually runs.

THE LIBRARY IS A FUNCTION OF THE SPECIES MIX AND NOT OF WHO IS WALKING, which
is what makes this cheap and what makes it a separate tool rather than a flag
on a deck build. `populace.station_crowd_library(lod)` takes the station's
occupancy-weighted species distribution and emits one body per (species, lod,
phase); it does not need a deck, a route or a cast. Measured: 2.0 s and 87,816
vertices at lod 4. Rebuilding a deck to obtain it -- which is what the old
`walkable.py` path did -- costs minutes and couples a shipped asset to a test.

EVERY RUNG, NOT THE ONE SOME BAKE HAPPENED TO CHOOSE. `populace.crowd_ladder()`
returns ((18.0, 2), (45.0, 4), (400.0, 8)): the runtime picks per person per
frame by distance, so shipping one rung leaves every walker outside that band
undrawable. The ladder is derived from `schedule.NPC_BUDGET`'s allowances, so
it is read here rather than restated.

AND THE CONVERSE, WHICH THIS TOOL DID NOT ASK UNTIL INV-1232. "Is every rung on
disk" and "does every walker name a rung" are different questions, and a build
can pass the first while failing the second: `populace.corridor_lod` derived the
level a placement NAMES by its own copy of `crowd_ladder`'s rule, without
`crowd_ladder`'s near-band cap, so it could answer with a level this file was
never going to write. Nothing in the runtime errors on that -- `npc.gd`'s
`_place_crowd` finds no bucket for the key and the walker is quietly not drawn.
`--selftest` now reads the `*_crowd.json` beside the libraries and asserts the
two sets agree in BOTH directions.

AND WHY THIS FILE NOW WRITES THE GLB ITSELF, session 4u. It used to hand the
OBJ to `station/export_gltf.py`, whose own docstring says what it does:
"flat-shaded normals computed per face, since the hull is faceted by design".
That is the right answer for an 8 km hull with plating steps and the wrong one
for a person. A body in this project is a stack of superellipse RINGS -- a
surface of revolution by construction -- and at the level the shipped library is
baked at those rings are 16-sided, so per-face normals put a 22.5-degree shading
step down every column of a torso, a limb and a skull. The panel's words for it
were "the ~12-sided torso cone is UNSMOOTHED -- hard facet edges across the
whole body", and it was never a modelling defect: the geometry was always
smooth-shadeable and the exporter threw the information away.

So the normals are computed here, per vertex, ANGLE-WEIGHTED and SPLIT AT A
CREASE. Three properties matter and each is a decision:

  * angle-weighted, not face-area-weighted: a ring cap is one big triangle fan
    and an area weight lets it dominate the rim vertices it shares with the
    band, tipping the rim's shading toward the cap's plane.
  * split at 60 degrees. A 16-gon ring turns 22.5 degrees per facet and a
    silhouette that reads as a cylinder must smooth those; a ring-to-cap joint
    and a boot sole turn about 90 and must NOT. 60 also leaves the 8-gon rings
    of lod4 smooth (45 degrees) and creases the 4-gon rings of lod8 (90), which
    is the right answer at both ends -- a 400 m figure has no curvature to
    preserve and a hard facet costs nothing there.
  * split by VERTEX INDEX, never by position. Parts in this module are separate
    closed shells that interpenetrate on purpose -- an arm root sits inside the
    torso -- so a position-keyed weld would smooth a nose into a skull and a
    hand into a sleeve. `_loft` already shares indices exactly where a surface
    is continuous, including the ring seam, so the index IS the smoothing
    group and no threshold is involved.

The same pass INDEXES the mesh, which the old path could not: un-indexing to
flat shading writes three vertices per triangle and shares nothing. Measured on
the shipped rungs, lod2 went 35.54 MB -> 16.36 MB while GAINING 9.4% more
triangles, and the mesh COUNT is unchanged at 864 -- so `npc.gd` allocates the
same MultiMesh buckets and the draw-call story does not move.
"""

import argparse
import json
import math
import os
import struct
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

DECKDIR = os.path.join(ROOT, "station", "generated", "scene", "deck")

# The dihedral angle above which two faces sharing a vertex do NOT share a
# normal. See the module docstring for why it is 60 and not a rounder number.
CREASE_DEG = 60.0

COMPONENT_FLOAT = 5126
COMPONENT_UINT = 5125
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


def _face_normals(verts, tris):
    out = []
    for a, b, c in tris:
        va, vb, vc = verts[a], verts[b], verts[c]
        ux, uy, uz = vb[0] - va[0], vb[1] - va[1], vb[2] - va[2]
        wx, wy, wz = vc[0] - va[0], vc[1] - va[1], vc[2] - va[2]
        nx = uy * wz - uz * wy
        ny = uz * wx - ux * wz
        nz = ux * wy - uy * wx
        ln = math.sqrt(nx * nx + ny * ny + nz * nz)
        out.append((0.0, 0.0, 0.0) if ln < 1e-18
                   else (nx / ln, ny / ln, nz / ln))
    return out


def _corner_angle(verts, tri, k):
    """Interior angle of triangle `tri` at its `k`-th corner, in radians."""
    p = verts[tri[k]]
    q = verts[tri[(k + 1) % 3]]
    r = verts[tri[(k + 2) % 3]]
    ax, ay, az = q[0] - p[0], q[1] - p[1], q[2] - p[2]
    bx, by, bz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
    la = math.sqrt(ax * ax + ay * ay + az * az)
    lb = math.sqrt(bx * bx + by * by + bz * bz)
    if la < 1e-18 or lb < 1e-18:
        return 0.0
    c = (ax * bx + ay * by + az * bz) / (la * lb)
    return math.acos(max(-1.0, min(1.0, c)))


def smooth_indexed(verts, tris, crease_deg=CREASE_DEG):
    """(positions, normals, indices) for one group, smooth-shaded with creases.

    THE FUNCTION THE WHOLE "unsmoothed body" FINDING COMES DOWN TO. See the
    module docstring for the three decisions in it; the code below is the
    mechanical part.
    """
    fn = _face_normals(verts, tris)
    cos_lim = math.cos(math.radians(crease_deg))
    # vertex index -> [(weighted normal, face normal), ...]. The corner angle is
    # computed ONCE per corner rather than once per neighbour pair; the naive
    # form is O(corners x valence) calls to `acos` and on a 416,000-triangle
    # library that is the whole runtime of this tool.
    adj = defaultdict(list)
    for fi, tri in enumerate(tris):
        g = fn[fi]
        for k in range(3):
            w = _corner_angle(verts, tri, k)
            adj[tri[k]].append((g[0] * w, g[1] * w, g[2] * w, g))

    pos, nrm, idx = [], [], []
    seen = {}
    for fi, tri in enumerate(tris):
        n0 = fn[fi]
        for k in range(3):
            vi = tri[k]
            sx = sy = sz = 0.0
            for wx, wy, wz, g in adj[vi]:
                if (g[0] * n0[0] + g[1] * n0[1] + g[2] * n0[2]) < cos_lim:
                    continue                      # across a crease: not ours
                sx += wx
                sy += wy
                sz += wz
            ln = math.sqrt(sx * sx + sy * sy + sz * sz)
            n = n0 if ln < 1e-12 else (sx / ln, sy / ln, sz / ln)
            key = (vi, int(n[0] * 2048), int(n[1] * 2048), int(n[2] * 2048))
            j = seen.get(key)
            if j is None:
                j = len(pos)
                seen[key] = j
                pos.append(verts[vi])
                nrm.append(n)
            idx.append(j)
    return pos, nrm, idx


def resolve_spans(tris, spans):
    """[(group, [triangle index, ...])] with every triangle in exactly one group.

    SPANS IN THIS PROJECT OVERLAP AND THAT IS NOT A BUG IN THEM.
    `populace.crowd_library` emits, per body, one span naming the WHOLE body
    (`crowd_<sp>_<lod>_<ph>_npc_body`) and then one span per merged material
    run INSIDE it. `deck.write_obj` resolves that by painting a per-triangle
    name and letting the last writer win, so the OBJ that reached the old glTF
    exporter carried only the material runs.

    The first cut of this file iterated the spans directly and wrote every body
    TWICE -- 910,848 triangles at lod 2 against the 416,256 the same library had
    always produced, and 2,304 meshes against 864. It was caught by comparing
    the two ledgers rather than by any assertion, which is the reason
    `--stats` reads the artefact instead of trusting the bake. Painting is the
    only correct reading, so it is done here, once, in the same order.
    """
    per = [None] * len(tris)
    for name, lo, hi in spans:
        for i in range(lo, hi):
            per[i] = name
    order, out = [], {}
    for i, name in enumerate(per):
        if name is None:
            continue
        if name not in out:
            out[name] = []
            order.append(name)
        out[name].append(i)
    return [(n, out[n]) for n in order]


def write_glb(path, verts, tris, spans, crease_deg=CREASE_DEG):
    """One mesh and one node per span group, indexed, with smooth normals.

    THE MESH NAMES ARE THE GROUP NAMES AND THAT IS LOAD-BEARING TWICE OVER.
    `npc.gd::_index_library` splits `crowd_<species>_<lod>_<phase>_npc_skin` at
    `_npc_` to find the body key, and `render_shot.gd::_material_for` /
    `dress_scene.gd` resolve the material by the LONGEST fragment contained in
    the name. A mesh named after its index resolves to nothing and the whole
    crowd renders on the magenta fallback, which `npc.gd`'s own comment records
    having happened.
    """
    buf = bytearray()
    accessors, views, meshes, nodes = [], [], [], []
    total_tris = 0

    for name, tri_ix in resolve_spans(tris, spans):
        if not tri_ix:
            continue
        # Re-base the group's triangles onto a dense local vertex list so the
        # smoothing adjacency is per group and the accessors are compact.
        remap, lv, lt = {}, [], []
        for a, b, c in (tris[i] for i in tri_ix):
            f = []
            for vi in (a, b, c):
                j = remap.get(vi)
                if j is None:
                    j = len(lv)
                    remap[vi] = j
                    lv.append(verts[vi])
                f.append(j)
            lt.append(tuple(f))
        pos, nrm, idx = smooth_indexed(lv, lt, crease_deg)
        total_tris += len(lt)

        prim = []
        for data, kind in ((pos, "POSITION"), (nrm, "NORMAL")):
            off = len(buf)
            for v in data:
                buf.extend(struct.pack("<3f", *v))
            views.append({"buffer": 0, "byteOffset": off,
                          "byteLength": len(buf) - off, "target": ARRAY_BUFFER})
            acc = {"bufferView": len(views) - 1,
                   "componentType": COMPONENT_FLOAT,
                   "count": len(data), "type": "VEC3"}
            if kind == "POSITION":
                acc["min"] = [min(v[i] for v in data) for i in range(3)]
                acc["max"] = [max(v[i] for v in data) for i in range(3)]
            accessors.append(acc)
            prim.append(len(accessors) - 1)
            while len(buf) % 4:
                buf.append(0)

        off = len(buf)
        for i in idx:
            buf.extend(struct.pack("<I", i))
        views.append({"buffer": 0, "byteOffset": off,
                      "byteLength": len(buf) - off,
                      "target": ELEMENT_ARRAY_BUFFER})
        accessors.append({"bufferView": len(views) - 1,
                          "componentType": COMPONENT_UINT, "count": len(idx),
                          "type": "SCALAR"})
        while len(buf) % 4:
            buf.append(0)

        meshes.append({"name": name, "primitives": [{
            "attributes": {"POSITION": prim[0], "NORMAL": prim[1]},
            "indices": len(accessors) - 1, "mode": 4}]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})

    gltf = {"asset": {"version": "2.0",
                      "generator": "babylon5-station/tools/bake_crowd.py"},
            "scene": 0,
            "scenes": [{"name": "Crowd", "nodes": list(range(len(nodes)))}],
            "nodes": nodes, "meshes": meshes, "accessors": accessors,
            "bufferViews": views, "buffers": [{"byteLength": len(buf)}]}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    while len(buf) % 4:
        buf.append(0)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2,
                            12 + 8 + len(js) + 8 + len(buf)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack("<II", len(buf), 0x004E4942))
        f.write(buf)
    return total_tris, len(meshes)


# Everything whose edit changes what a baked body looks like. Listed rather
# than walked, because "every .py under station/" would rebuild the library
# whenever anything in the project moved, and a 9-minute bake on every touch is
# a gate people turn off.
SOURCES = ("station/npc/body.py", "station/npc/costume.py",
           "station/npc/animation.py", "station/populace.py",
           "tools/bake_crowd.py")


def _source_mtime():
    """(name, mtime) of the most recently edited generator."""
    best = ("(none)", 0.0)
    for rel in SOURCES:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p) and os.path.getmtime(p) > best[1]:
            best = (rel, os.path.getmtime(p))
    return best


def bake(out_dir=DECKDIR, force=False, keep_obj=False):
    """Emit `crowd_lod<N>.glb` for every rung of the ladder.

    Returns the list of (lod, glb_path, n_verts, n_groups) actually written.
    """
    import populace as P

    os.makedirs(out_dir, exist_ok=True)
    newest = _source_mtime()
    written = []
    for _hi, lod in P.crowd_ladder():
        glb = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        if os.path.exists(glb) and not force:
            # STALE IS NOT THE SAME AS PRESENT, and reading it as the same is
            # this project's signature defect wearing a build-cache. `--force`
            # is a flag somebody has to remember, and a checkout that already
            # holds a library would otherwise keep shipping the body it was
            # baked from however many times `station/npc/body.py` changed --
            # the frame would be fresh and the ASSET stale, which is the
            # session-4e renderer-fallback shape one level down. So the skip is
            # conditioned on the generators' own mtimes, and it SAYS which one
            # made it rebuild.
            if os.path.getmtime(glb) >= newest[1]:
                print("  lod %d: present and newer than every generator, "
                      "skipped (--force to rebuild anyway)" % lod)
                continue
            print("  lod %d: present but STALE -- %s is newer" % (lod, newest[0]))
        v, t, g = P.station_crowd_library(lod)
        if keep_obj:
            # The OBJ is an intermediate: Godot reads the glb and nothing else
            # reads the obj, so it is 3-8 MB of package weight for nothing. It
            # is still worth having behind a flag -- `tools/preview_render.py`
            # eats OBJ and is the fast way to look at a body.
            import deck as D                                    # noqa: PLC0415
            D.write_obj(os.path.join(out_dir, "crowd_lod%d.obj" % lod), v, t, g)
        tri, nm = write_glb(glb, v, t, g)
        written.append((lod, glb, len(v), len(g)))
        print("  lod %d: %d verts, %d groups -> %d triangles in %d meshes -> "
              "%s (%.1f MB)"
              % (lod, len(v), len(g), tri, nm, os.path.basename(glb),
                 os.path.getsize(glb) / 1e6))
    return written


def read_glb(path):
    """(json, bin) of a .glb. Small, and the only reader this file needs."""
    with open(path, "rb") as f:
        data = f.read()
    magic, _ver, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError("%s is not a glb" % path)
    off, js = 12, None
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        if ctype == 0x4E4F534A:
            js = json.loads(data[off:off + clen].decode("utf-8"))
        off += clen
    return js


def bodies_in(path):
    """`{body key: (triangles, min_y)}` read back off the baked file.

    OFF THE ARTEFACT AND NOT OFF THE GENERATOR, which is the whole reason this
    exists. Every other number in this tool is what the bake INTENDED; these two
    are what a Godot import will actually see, taken from the POSITION
    accessors' own declared min/max. CLAUDE.md's rule -- a gate that reads a
    committed artefact must be able to rebuild it -- runs the other way here:
    `--stats` rebuilds nothing and reads only what shipped.
    """
    js = read_glb(path)
    acc = js["accessors"]
    out = {}
    for mesh in js["meshes"]:
        name = mesh.get("name", "?")
        cut = name.find("_npc_")
        key = name[:cut] if cut > 0 else name
        tri, lo = out.get(key, (0, 1e30))
        for p in mesh["primitives"]:
            tri += (acc[p["indices"]]["count"] // 3 if "indices" in p
                    else acc[p["attributes"]["POSITION"]]["count"] // 3)
            a = acc[p["attributes"]["POSITION"]]
            if "min" in a:
                lo = min(lo, a["min"][1])
        out[key] = (tri, lo)
    return out


# A body's own origin is the deck it stands on: `npc.gd::_walker_xform` and
# `populace._place_body` both put the instance transform's origin ON the floor
# and the mesh is expected to rise from there. This is how far above it a body
# is allowed to start.
GROUND_TOL_M = 0.002

# ...EXCEPT THE ONE POSE THAT IS NOT STANDING ON THE FLOOR. `populace.crowd_body`
# poses the `sit` and `sleep` slots on the SPECIES' OWN FITTED FURNITURE --
# `animation.seat_height` / `bunk_height` -- because a shared body cannot know
# which chair it will end up on, and the placement then puts it on the real one.
# So those two slots legitimately start a seat-height above the origin, and a
# grounding gate that did not say so would either fail for ever or be quietly
# relaxed until it could not fail at all. Named, not excluded silently.
POSED_ON_FURNITURE = ("sit", "sleep")

# ...AND THE ONE BODY WHOSE LOWEST VERTEX IS NOT A FOOT. Session 4u: 16 bodies
# came back over the 2 mm bar, by 5.6 to 27.2 mm, and every one of them was a
# ROBED Minbari -- `minbari1` and `minbari2`, whose mesh has a `skirt` part and
# no `leg` and no `foot`, because `costume.ATTACHMENTS["skirt"]`'s own note says
# the robe "REPLACES both legs and both feet".
#
# THE BODY IS NOT IN THE AIR AND THE MEASUREMENT PROVES IT THE OTHER WAY ROUND.
# `costume._skirt` builds the hem at `SKIRT_HEM_YF * stature` above the origin
# -- 50.8 mm on the 1.695 m variant and 55.5 mm on the 1.851 m one, and the bind
# pose measures +0.05084 and +0.05553, to five figures. So the worst of the 16 is
# its hem sitting 24 mm BELOW where the garment puts it at rest, not 27 mm above
# the deck. A robe that touched the deck would plough it.
#
# WHY THE OBVIOUS RULE IS THE WRONG ONE, and this is the part worth keeping.
# "Skip a body whose rig has no `foot` part" selects these 16 -- and it also
# selects every GAIM, who have `suit_leg` instead of `leg` and no `foot` at all
# because they are a sealed environment suit. Measured: a blanket no-foot skip
# stops gating 150 of 1,260 bodies, 90 of them Gaim who stand on their suit legs
# at min_y exactly 0.00000 and for whom the strict 2 mm bar is right. An
# exclusion that stops asking the question of 90 bodies in order to excuse 60 is
# how a gate stops being able to fail.
#
# So nothing is excluded. A body that stands on a HEM is measured against the
# clearance that hem was BUILT with, imported from the module that builds it
# rather than copied here, and it can still fail: the bar for the worst of the
# 16 is 57.5 mm and it measures 27.2. `--induce-floater` is the control.
HEM_PART = "skirt"

# What `--induce-floater` adds to every hem-standing body, and it is chosen to
# be unambiguous rather than marginal: 0.25 m is a robe hovering at knee height.
INDUCED_FLOAT_M = 0.25

_HEM_CACHE = {}


def hem_allowance(token, lod):
    """How high this body's lowest vertex is allowed to start, above `GROUND_TOL_M`.

    0.0 for anybody who stands on feet, legs or suit legs -- which is everybody
    but the robed. For a body whose mesh carries a `skirt` part it is the hem
    clearance `costume._skirt` gave it, from that module's own constant.

    IT ASKS THE GENERATOR, not a table written beside it. `bodies_in` reads the
    baked glb and knows only a name; the question "what is this body standing
    on" is answerable only where the body is built.
    """
    if (token, lod) in _HEM_CACHE:
        return _HEM_CACHE[(token, lod)]
    sys.path.insert(0, os.path.join(ROOT, "station", "npc"))
    import populace as P                                         # noqa: PLC0415
    import animation as A                                        # noqa: PLC0415
    import costume as C                                          # noqa: PLC0415
    base, npc_id = P.crowd_figure(token)
    try:
        rg = A.rig(base, npc_id, lod)
        parts = {p[0] for p in rg.parts}
        v = (C.SKIRT_HEM_YF * rg.skel.stature_m
             if HEM_PART in parts else 0.0)
    except Exception:                                            # noqa: BLE001
        # A body that cannot be rigged gets NO allowance. The strict bar is the
        # safe direction: it can only produce a failure to look at.
        v = 0.0
    _HEM_CACHE[(token, lod)] = v
    return v


def split_body_key(key):
    """`crowd_<token>_<lod>_<slot>` -> (token, lod, slot)."""
    tok, lod, slot = key[len("crowd_"):].rsplit("_", 2)
    return tok, int(lod), int(slot)


def stats(out_dir=DECKDIR, out=print, induce=0.0):
    """Triangles per rung and the grounding ledger. Returns (rows, floaters).

    `induce` lifts every HEM-STANDING body by that many metres before the
    comparison -- the negative control for the allowance `hem_allowance` grants
    them. It must make them fail; if it does not, the allowance has stopped
    being a bar and become an exemption.
    """
    import populace as P
    slots = {P.SLOT_OF[k] for k in POSED_ON_FURNITURE if k in P.SLOT_OF}
    rows, floaters, hemmed = [], [], []
    for _hi, lod in P.crowd_ladder():
        p = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        if not os.path.exists(p):
            out("  lod %-2d MISSING" % lod)
            continue
        bodies = bodies_in(p)
        tri = sum(t for t, _ in bodies.values())
        ground = [(k, y) for k, (_t, y) in bodies.items()
                  if int(k.rsplit("_", 1)[-1]) not in slots]
        bad = []
        for k, y in ground:
            tok, klod, _slot = split_body_key(k)
            hem = hem_allowance(tok, klod)
            if hem > 0.0:
                y += induce
                hemmed.append((k, y, hem))
            if y > GROUND_TOL_M + hem:
                bad.append((k, y))
        floaters.extend(bad)
        ys = sorted(y for _k, y in ground)
        rows.append((lod, tri, len(bodies), os.path.getsize(p)))
        out("  lod %-2d %9d triangles  %3d bodies  %6.2f MB   "
            "min_y median %+.5f  worst %+.5f  above %.0f mm: %d/%d"
            % (lod, tri, len(bodies), os.path.getsize(p) / 1e6,
               ys[len(ys) // 2], ys[-1], GROUND_TOL_M * 1000,
               len(bad), len(ground)))
    # THE ALLOWANCE IS REPORTED EVERY RUN, with its own worst case beside its own
    # bar, so nobody has to take on trust that it is not swallowing a defect.
    if hemmed:
        k, y, hem = max(hemmed, key=lambda r: r[1] - r[2])
        out("  hem-standing bodies (a `%s` part, no foot): %d, worst %s at "
            "%+.4f m against its own built hem clearance %+.4f m (+%.0f mm)"
            % (HEM_PART, len(hemmed), k, y, hem, GROUND_TOL_M * 1000))
    return rows, floaters


def preview(lod, out_dir=DECKDIR, species="human", near=False):
    """Write a shot the ENGINE can take a close crowd frame from.

    WHY THIS IS HERE AND NOT IN `tools/export_scene.py`, which is where every
    other shot lives. Three reasons and the third is the one that decided it:

      * The thing being judged is the CROWD LIBRARY -- the shared bodies a
        MultiMesh instances -- and no existing shot renders those. `--shot deck`
        bakes the placements back into triangles through `populace.bake_
        instances`, so it renders the same geometry by a different route and
        would not notice if this file wrote nonsense.
      * A deck shot is minutes of full CPU and rewrites
        `station/generated/scene/deck/*`, which is a SHARED path. CLAUDE.md
        records two sessions lost to exactly that: an agent's render taken
        against files another agent was mid-write on, read as a regression in
        the thing being tested.
      * `station/generated/scene/crowd/` is a directory nothing else in the
        project writes, so this contends with nobody.

    `render_shot.gd` reads a scene.json and nothing else, so the shot is that
    file plus a glb. Render it with:

        tools/render_godot.sh --shot crowd --no-export --res 1280x1280 \\
            --out docs/engine-crowd-lod2.png

    and read the renderer line the script prints -- it exits 3 rather than hand
    back an OpenGL 3 Compatibility frame.
    """
    import populace as P

    sdir = os.path.join(ROOT, "station", "generated", "scene", "crowd")
    os.makedirs(sdir, exist_ok=True)

    # Four bodies at four phases, a metre apart, facing the camera. The library
    # builds every body at the origin because the instance transform carries the
    # placement; here the offset IS the placement.
    verts, tris, spans = [], [], []
    # ONE body at the origin for the near shot: the half-distance frame is
    # about a face, and four bodies at 1 m means three of them off-frame
    # and the camera aimed at the gap between two of them, which is what
    # the first near render actually produced.
    n_bodies = 1 if near else 4
    for i in range(n_bodies):
        bv, bt, bg = P.crowd_body(species, lod, i * 2 % P.CROWD_PHASES)
        base, t0 = len(verts), len(tris)
        dx = (i - (n_bodies - 1) / 2.0) * 0.80
        verts.extend((x + dx, y, z) for x, y, z in bv)
        tris.extend((a + base, b + base, c + base) for a, b, c in bt)
        for nm, lo, hi in bg:
            # THE GROUP NAME MUST KEEP ITS `npc_...` FRAGMENT.
            # `render_shot.gd::_material_for` binds by the longest fragment
            # CONTAINED in the mesh name, so a name that loses it resolves to
            # nothing and the body renders on the fallback -- grey on grey,
            # which is the one failure a render cannot show.
            frag = nm[nm.find("npc_"):] if "npc_" in nm else nm
            spans.append(("crowdpreview%d_%s" % (i, frag), t0 + lo, t0 + hi))

    glb = os.path.join(sdir, "crowd_preview.glb")
    tri, nm = write_glb(glb, verts, tris, spans)

    # The camera: the rubric's HALF distance. A corridor conversation is about
    # 2 m, so craft is judged at 1 m, which is `AAA-STANDARD.md`'s own rule and
    # the one session 3r records having never applied.
    eye = (0.0, 1.50, 3.35) if not near else (0.42, 1.56, 1.02)
    aim = (0.0, 1.05, 0.0) if not near else (0.0, 1.50, 0.06)
    fov = 34.0 if not near else 20.0
    # SHADOWS ON, and it is not decoration. Godot's own default is off, so a
    # first pass of this shot came back with "0 casting shadows" and every
    # figure lit like a flat card -- no contact shadow under a boot, no form
    # shadow in an eye socket, which is exactly the geometry this session
    # exists to make readable. A frame with no shadow cannot answer the
    # question it was taken to answer.
    lights = []
    for lx in (-1.9, 0.0, 1.9):
        lights.append({"pos": [lx, 2.85, 1.35], "energy": 6.0,
                       "colour": [1.0, 0.96, 0.90], "range": 8.5,
                       "attenuation": 1.0, "shadow": True,
                       "group": "light_downlight"})
    lights.append({"pos": [0.0, 1.6, 3.6], "energy": 1.8,
                   "colour": [0.82, 0.88, 1.0], "range": 9.0,
                   "attenuation": 1.0, "group": "light_fill"})
    shot = {
        "shot": "crowd",
        "scene": "res://scenes/interior.tscn",
        "glb": [glb],
        "triangles": tri,
        "groups": [s[0] for s in spans],
        "lights": lights,
        "room": "corridor",
        "exposure": 1.0,
        "ambient": 1.3,
        "camera": {"eye": list(eye), "target": list(aim), "up": [0.0, 1.0, 0.0],
                   "fov": fov, "near": 0.05, "far": 60.0},
        "sun_from": None,
        "out_png": os.path.join(sdir, "crowd_preview.png"),
        "lod": lod, "species": species, "bodies": n_bodies,
    }
    with open(os.path.join(sdir, "scene.json"), "w", encoding="utf-8") as f:
        json.dump(shot, f, indent=1)
    print("crowd preview: %d bodies, %s lod %d, %d triangles in %d meshes"
          % (n_bodies, species, lod, tri, nm))
    print("  %s" % os.path.relpath(glb, ROOT))
    print("  render with: tools/render_godot.sh --shot crowd --no-export "
          "--res 1280x1280 --out <png>")
    return 0


def selftest(out_dir=DECKDIR, induce=0.0):
    """Assert the ladder is fully covered and every rung is loadable.

    THE ASSERTION IS PER RUNG AND NOT A COUNT, because the defect this tool
    exists to close was not "too few libraries" -- it was zero, and a count
    gate that reads `>= 1` would have passed on a one-rung bake that leaves
    every walker beyond 18 m invisible.

    AND IT CHECKS THE DIRECTORY THAT WAS BAKED, not a default. The first cut
    of this function read `DECKDIR` unconditionally, so `--out scene/station`
    baked three libraries into the streamed build and then reported OK by
    looking at three OTHER files left in `scene/deck` from a previous run --
    a gate passing on evidence from somewhere other than the thing it just
    did. `walk.gd` resolves the library beside the CROWD PLACEMENT LIST, so
    which directory holds it is the entire question.
    """
    import glob
    import populace as P
    lad = P.crowd_ladder()
    missing = []
    for _hi, lod in lad:
        p = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        if not os.path.exists(p) or os.path.getsize(p) < 1024:
            missing.append(lod)
    print("crowd library in %s -- ladder %s"
          % (os.path.relpath(out_dir, ROOT), tuple(l for _h, l in lad)))
    for _hi, lod in lad:
        p = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        ok = os.path.exists(p) and os.path.getsize(p) >= 1024
        print("  lod %-2d %-8s %s" % (
            lod, "OK" if ok else "MISSING",
            ("%.1f MB" % (os.path.getsize(p) / 1e6)) if ok else "--"))

    # -- THE OTHER DIRECTION: does every walker name a library that is here? --
    # `walk.gd::_load_crowd_libs` loads these files and `npc.gd::_place_crowd`
    # buckets each walker on `crowd_<species>_<lod>_<phase>`. A record whose
    # `lod` has no glb finds no bucket and is drawn nowhere -- no error, no
    # warning, an empty corridor. So the placement lists are read here, beside
    # the libraries, which is the only place both halves exist at once.
    have = {int(os.path.basename(p)[len("crowd_lod"):-len(".glb")])
            for p in glob.glob(os.path.join(out_dir, "crowd_lod*.glb"))}
    rows = sorted(glob.glob(os.path.join(out_dir, "*_crowd.json")))
    named, orphan, examples = {}, 0, []
    for p in rows:
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:                                # noqa: BLE001
            print("  (unreadable %s: %s)" % (os.path.basename(p), exc))
            continue
        for rec in data:
            lv = int(rec.get("lod", -1))
            named[lv] = named.get(lv, 0) + 1
            if lv not in have:
                orphan += 1
                if len(examples) < 3:
                    examples.append("%s: %s" % (os.path.basename(p),
                                                rec.get("mesh", "?")))
    if rows:
        print("\n  %d placement file(s), %d walker(s), naming lods %s"
              % (len(rows), sum(named.values()),
                 {k: v for k, v in sorted(named.items())}))
    else:
        # A GATE MUST SAY WHEN IT DID NOT RUN. Reporting OK here on the
        # strength of three files and no placements is the shape of every
        # manufactured pass in this repository.
        print("\n  NO PLACEMENT LISTS beside the libraries -- the "
              "'does every walker name a rung' half did NOT run.")

    if missing:
        print("\n  CROWD LIBRARY INCOMPLETE -- rungs %s missing." % missing)
        print("  Every walker in those distance bands is undrawable.")
        print("  Run: python3 tools/bake_crowd.py")
        return 1
    if orphan:
        print("\n  %d WALKER(S) NAME A LIBRARY THAT IS NOT HERE -- lods %s."
              % (orphan, sorted(k for k in named if k not in have)))
        for e in examples:
            print("    e.g. %s" % e)
        print("  They are drawn nowhere and the runtime logs nothing.")
        print("  The generator picked a level off the ladder: see "
              "populace.lod_for_distance and INV-1232.")
        return 1

    # -- AND THE THIRD QUESTION, session 4u: does a body STAND ON ITS ORIGIN? --
    # The two checks above ask whether the library is complete and whether the
    # placements agree with it. Neither can see that every mesh in it is in the
    # air, and every mesh in it was: measured off the shipped `crowd_lod8.glb`,
    # 157 of 168 bodies had their lowest vertex above 2 cm with a median of
    # 79.0 mm, because `feet` is an `extremity` and the leg used to stop at the
    # ankle when it was culled. A crowd hovering 8 cm over the deck is not
    # something any assertion in this project could fail for, and it is
    # something anybody would see.
    print("\nTRIANGLES AND GROUNDING, read off the baked files")
    if induce:
        print("  CONTROL: every hem-standing body lifted %+.3f m -- this run "
              "MUST fail" % induce)
    _rows, floaters = stats(out_dir, induce=induce)
    if floaters:
        print("\n  %d BODY/BODIES DO NOT STAND ON THEIR OWN ORIGIN "
              "(> %.0f mm)." % (len(floaters), GROUND_TOL_M * 1000))
        for k, y in sorted(floaters, key=lambda kv: -kv[1])[:5]:
            tok, klod, _s = split_body_key(k)
            hem = hem_allowance(tok, klod)
            print("    %-28s min_y %+.4f m   bar %+.4f m%s"
                  % (k, y, GROUND_TOL_M + hem,
                     "  (stands on a hem)" if hem else ""))
        print("  `npc.gd::_walker_xform` puts the instance origin ON the deck,")
        print("  so this is exactly how far the crowd floats. The poses that")
        print("  are MEANT to be off the floor -- %s -- are excluded by name,"
              % ", ".join(POSED_ON_FURNITURE))
        print("  and a body that stands on a `%s` is measured against the hem "
              "clearance" % HEM_PART)
        print("  `costume._skirt` built it with, which is a BAR and not an "
              "exemption.")
        return 0 if induce else 1
    if induce:
        print("\n  THE CONTROL DID NOT FAIL. The hem allowance is no longer a "
              "bar:")
        print("  a robed body lifted %+.3f m off the deck was still passed."
              % induce)
        return 1
    print("\n  CROWD LIBRARY OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DECKDIR)
    ap.add_argument("--force", action="store_true",
                    help="rebuild rungs that already exist")
    ap.add_argument("--keep-obj", action="store_true")
    ap.add_argument("--selftest", action="store_true",
                    help="assert every ladder rung is present; exit 1 if not")
    ap.add_argument("--stats", action="store_true",
                    help="triangles per rung and the grounding ledger, read "
                         "off the baked glb rather than off the generator")
    ap.add_argument("--preview", metavar="LOD", type=int, default=None,
                    help="write a scene the engine renderer can take a close "
                         "crowd frame from; see `preview()`")
    ap.add_argument("--preview-species", default="human")
    ap.add_argument("--preview-near", action="store_true",
                    help="the rubric's HALF distance -- a head at 1 m")
    ap.add_argument("--induce-floater", nargs="?", type=float,
                    const=INDUCED_FLOAT_M, default=0.0, metavar="METRES",
                    help="the negative control for the hem allowance: lift "
                         "every robed body by this much and require the "
                         "grounding gate to catch it")
    a = ap.parse_args()
    if a.stats:
        print("crowd library in %s" % os.path.relpath(a.out, ROOT))
        _rows, floaters = stats(a.out, induce=a.induce_floater)
        return 1 if floaters else 0
    if a.preview is not None:
        return preview(a.preview, a.out, a.preview_species, a.preview_near)
    if a.selftest:
        return selftest(a.out, induce=a.induce_floater)
    print("baking the shared crowd library into %s"
          % os.path.relpath(a.out, ROOT))
    bake(a.out, force=a.force, keep_obj=a.keep_obj)
    return selftest(a.out)


if __name__ == "__main__":
    sys.exit(main())
