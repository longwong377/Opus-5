import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'station'))
import interior as it, rooms as R, directory as dr, deck as D, bespoke as B
schema, profile = it.load()
places = [p for p in dr.PLACES if p.get("module") in B.BESPOKE_GEOMETRY]
print("bespoke places:", len(places), flush=True)
rows=[]
for p in places:
    try:
        hl = D.room_axial_half_m(schema, profile, p)
        v,t,g = B.room_shell(schema, profile, p, hl)
    except Exception as e:
        print(f"  {p['key']:<28} SKIP {type(e).__name__}: {str(e)[:60]}", flush=True); continue
    xs=[q[0] for q in v]; ys=[q[1] for q in v]; zs=[q[2] for q in v]
    mesh_w = max(xs)-min(xs); mesh_l = max(zs)-min(zs); mesh_h = max(ys)-min(ys)
    w_full,_l,_r = R.room_extent_m(schema, profile, p)
    bw,_bl = R.bay_span_m(p)
    rows.append((p["key"], min(w_full,bw), mesh_w,
                 2*D.room_interior_half_m(schema,profile,p), mesh_l,
                 R.ceiling_m(p), mesh_h))
    print(f"  done {p['key']}", flush=True)
print(f"{'place':<26}{'shell_w':>9}{'mesh_w':>9}{'w%':>7}  {'shell_l':>9}{'mesh_l':>9}{'l%':>7}  {'sh_h':>7}{'msh_h':>7}")
bad=0
for k,sw,mw,sl,ml,sh,mh in sorted(rows, key=lambda r: r[1]/max(r[2],1e-9)):
    wp=100*sw/mw; lp=100*sl/ml
    if wp < 95: bad += 1
    print(f"{k:<26}{sw:9.3f}{mw:9.3f}{wp:6.1f}%  {sl:9.3f}{ml:9.3f}{lp:6.1f}%  {sh:7.2f}{mh:7.2f}{'  SHORT' if wp<95 else ''}")
print(f"\n{bad} of {len(rows)} bespoke places: collision shell under 95% of its own mesh width")
