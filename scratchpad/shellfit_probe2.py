import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'station'))
import interior as it, rooms as R, directory as dr, deck as D, bespoke as B
schema, profile = it.load()
places = [p for p in dr.PLACES if p.get("module") in B.BESPOKE_GEOMETRY]
rows = []
for p in places:
    try:
        hl = D.room_axial_half_m(schema, profile, p)
        v, t, g = B.room_shell(schema, profile, p, hl)
    except Exception:
        continue
    xs = [q[0] for q in v]
    mesh_w = max(xs) - min(xs)
    w_full, _l, _r = R.room_extent_m(schema, profile, p)
    bw, _bl = R.bay_span_m(p)
    fr, ring, dk, dd = it.place_floor_radius(schema, profile, p)
    rows.append((p["key"], p["angle_deg"], p["z_m"], p["sector"], ring, dk,
                 fr, w_full, bw, mesh_w))
    print("done", p["key"], flush=True)
print()
print(f"{'place':<24}{'w_full':>9}{'bay_w':>8}{'mesh_w':>9}  {'binding':<8}"
      f"{'mesh/foot':>10}{'radius':>9}{'mesh_deg':>9}{'foot_deg':>9}")
over = 0
for k, ang, z, sec, ring, dk, fr, wf, bw, mw in sorted(rows, key=lambda r: -r[9] / max(r[7], 1e-9)):
    binding = "footprint" if wf <= bw else "one-bay"
    mdeg = math.degrees(mw / fr) if fr else 0.0
    fdeg = math.degrees(wf / fr) if fr else 0.0
    flag = ""
    if mw > wf * 1.02:
        over += 1
        flag = "  MESH > FOOTPRINT"
    print(f"{k:<24}{wf:9.2f}{bw:8.2f}{mw:9.2f}  {binding:<8}{mw/wf:10.2f}"
          f"{fr:9.1f}{mdeg:9.2f}{fdeg:9.2f}{flag}")
print(f"\n{over} of {len(rows)} bespoke meshes are WIDER than their own declared footprint")
