#!/usr/bin/env python3
"""Wrap an exported slice in a self-contained, walkable WebGL page.

The slice JSON is INLINED rather than fetched: a published Artifact runs under a
CSP that blocks every external host, so a build that fetches its own data is a
build that shows a black screen. Same reason the trailer embeds its frames.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = r"""<title>Babylon 5 — walk the station</title>
<style>
  :root{
    --void:#05070b; --plate:#141922; --ice:#9fc4d8; --amber:#ff8b3d;
    --ink:#e8ecf2; --mute:#79808e; --line:#252c38;
    --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
    --sans:"Helvetica Neue",Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--void);color:var(--ink);
            font-family:var(--sans);overflow:hidden}
  #stage{position:fixed;inset:0}
  canvas{display:block;width:100%;height:100%;cursor:crosshair}

  .panel{position:fixed;left:0;right:0;top:0;bottom:0;display:grid;
         place-items:center;background:rgba(5,7,11,.93);z-index:5;
         padding:24px;text-align:center}
  .panel.gone{display:none}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.34em;
           text-transform:uppercase;color:var(--mute)}
  h1{font-size:clamp(26px,6vw,52px);font-weight:200;letter-spacing:.3em;
     text-transform:uppercase;margin:.4em 0 .1em;text-indent:.3em}
  .lede{color:var(--mute);font-size:14px;line-height:1.7;max-width:56ch;
        margin:14px auto 0}
  .lede b{color:var(--ice);font-weight:400}
  button{font-family:var(--mono);font-size:12px;letter-spacing:.22em;
         text-transform:uppercase;color:var(--ink);background:var(--plate);
         border:1px solid var(--line);padding:14px 30px;cursor:pointer;
         margin-top:26px}
  button:hover{border-color:var(--ice);color:var(--ice)}
  button:focus-visible{outline:2px solid var(--amber);outline-offset:3px}
  .keys{font-family:var(--mono);font-size:11px;color:var(--mute);
        margin-top:20px;letter-spacing:.1em;line-height:2}
  .keys kbd{border:1px solid var(--line);padding:2px 7px;color:var(--ink)}

  #hud{position:fixed;left:16px;bottom:14px;font-family:var(--mono);
       font-size:11px;color:rgba(232,236,242,.72);line-height:1.8;
       text-shadow:0 1px 3px #000;pointer-events:none;z-index:3}
  #hud b{color:var(--amber);font-weight:400}
  #reticle{position:fixed;left:50%;top:50%;width:3px;height:3px;margin:-1.5px;
           background:rgba(159,196,216,.75);z-index:3;pointer-events:none}
  #note{position:fixed;right:16px;bottom:14px;font-family:var(--mono);
        font-size:10.5px;color:var(--mute);text-align:right;line-height:1.8;
        z-index:3;pointer-events:none}
</style>

<div id="stage"><canvas id="gl"></canvas></div>
<div id="reticle" hidden></div>
<div id="hud" hidden></div>
<div id="note" hidden></div>

<div class="panel" id="panel">
  <div>
    <div class="eyebrow">Earth Alliance · Babylon 5 · Blue Sector</div>
    <h1>Walk the station</h1>
    <p class="lede" id="lede"></p>
    <button id="go">Enter the corridor</button>
    <div class="keys">
      <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd> move ·
      <kbd>mouse</kbd> look · <kbd>shift</kbd> run · <kbd>space</kbd> jump ·
      <kbd>esc</kbd> release
    </div>
  </div>
</div>

<script id="slice" type="application/json">__SLICE__</script>
<script>
const D = JSON.parse(document.getElementById('slice').textContent);

function bytes(b64){
  const s = atob(b64), n = s.length, u = new Uint8Array(n);
  for (let i = 0; i < n; i++) u[i] = s.charCodeAt(i);
  return u.buffer;
}
const POS  = new Float32Array(bytes(D.pos));
const IDX  = new Uint32Array(bytes(D.idx));
const CPOS = new Float32Array(bytes(D.cpos));
const CIDX = new Uint32Array(bytes(D.cidx));

document.getElementById('lede').innerHTML =
  'This is the real station. The geometry below is the same '
  + '<b>' + D.deck + '</b> mesh the engine loads, sliced to '
  + '<b>' + D.arc_m.toFixed(0) + ' m of arc</b> at ' + D.place
  + ' &mdash; ' + D.tris.toLocaleString() + ' triangles in '
  + D.materials.length + ' materials, generated offline in Python from one '
  + 'authoritative schema. You walk on the <b>collision shell</b>, not the '
  + 'render mesh, for the same reason the engine does.';
document.getElementById('note').innerHTML =
  D.deck + ' &middot; r ' + D.floor_r_m.toFixed(2) + ' m &middot; z '
  + D.z_m.toFixed(0) + ' m<br>ring unrolled to arc coordinates';

// ---------------------------------------------------------------------------
// Per-vertex normals, accumulated. Cheaper than unindexing 89k triangles and
// the corridor's plating reads better smooth-shaded at the seams anyway.
// ---------------------------------------------------------------------------
const NRM = new Float32Array(POS.length);
for (let i = 0; i < IDX.length; i += 3) {
  const a = IDX[i] * 3, b = IDX[i+1] * 3, c = IDX[i+2] * 3;
  const ux = POS[b] - POS[a], uy = POS[b+1] - POS[a+1], uz = POS[b+2] - POS[a+2];
  const vx = POS[c] - POS[a], vy = POS[c+1] - POS[a+1], vz = POS[c+2] - POS[a+2];
  const nx = uy*vz - uz*vy, ny = uz*vx - ux*vz, nz = ux*vy - uy*vx;
  for (const o of [a, b, c]) { NRM[o] += nx; NRM[o+1] += ny; NRM[o+2] += nz; }
}
for (let i = 0; i < NRM.length; i += 3) {
  const l = Math.hypot(NRM[i], NRM[i+1], NRM[i+2]) || 1;
  NRM[i] /= l; NRM[i+1] /= l; NRM[i+2] /= l;
}

// ---------------------------------------------------------------------------
// GL
// ---------------------------------------------------------------------------
const cv = document.getElementById('gl');
const gl = cv.getContext('webgl2', {antialias: true});
if (!gl) { document.getElementById('lede').textContent =
  'This browser has no WebGL 2, which this build needs.'; }

const VS = `#version 300 es
in vec3 p; in vec3 n;
uniform mat4 mvp; uniform vec3 eye;
out vec3 vn; out vec3 vd;
void main(){ vn = n; vd = p - eye; gl_Position = mvp * vec4(p, 1.0); }`;

const FS = `#version 300 es
precision highp float;
in vec3 vn; in vec3 vd;
uniform vec3 albedo; uniform vec3 emission; uniform float energy;
out vec4 o;
void main(){
  vec3 N = normalize(vn);
  float d = length(vd);
  // A lamp at the eye, falling off, plus a little sky from inboard. The engine
  // lights this from 1,563 tagged fittings; a browser gets the cheap read.
  vec3 L = normalize(-vd);
  float lam = max(dot(N, L), 0.0);
  // A NEAR WALL MUST NOT BLOW OUT. The first pass ran the eye lamp at 5.2 with
  // a soft falloff, which clipped every surface inside about 3 m to white and
  // lost the plating the corridor is made of. The corridor is lit by its own
  // strips in the engine; here the lamp is a fill and the emissives carry it.
  float fall = 1.0 / (1.0 + 0.16 * d * d);
  float sky = 0.30 + 0.30 * max(N.y, 0.0);
  vec3 c = albedo * (sky * 0.62 + lam * fall * 1.55) + emission * energy * 0.62;
  c = c / (c + vec3(0.85));                       // reinhard, keeps lamps sane
  o = vec4(pow(c, vec3(1.0/2.2)), 1.0);           // to sRGB
}`;

function sh(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(s);
  return s; }
const prog = gl.createProgram();
gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
gl.linkProgram(prog); gl.useProgram(prog);

const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
function buf(data, loc, size){
  const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
  gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
}
buf(POS, gl.getAttribLocation(prog, 'p'), 3);
buf(NRM, gl.getAttribLocation(prog, 'n'), 3);
const ib = gl.createBuffer();
gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, IDX, gl.STATIC_DRAW);

const U = {
  mvp: gl.getUniformLocation(prog, 'mvp'),
  eye: gl.getUniformLocation(prog, 'eye'),
  albedo: gl.getUniformLocation(prog, 'albedo'),
  emission: gl.getUniformLocation(prog, 'emission'),
  energy: gl.getUniformLocation(prog, 'energy'),
};
gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
gl.clearColor(0.012, 0.016, 0.024, 1);

// ---------------------------------------------------------------------------
// Collision -- brute force over the shell. 506 triangles; a spatial index would
// be premature and is one more thing to be wrong.
// ---------------------------------------------------------------------------
const EYE_H = 1.75, RADIUS = 0.34, GRAV = -12.6, STEP = 0.42;

function rayTri(ox, oy, oz, dx, dy, dz, i, best){
  const a = CIDX[i]*3, b = CIDX[i+1]*3, c = CIDX[i+2]*3;
  const e1x = CPOS[b]-CPOS[a], e1y = CPOS[b+1]-CPOS[a+1], e1z = CPOS[b+2]-CPOS[a+2];
  const e2x = CPOS[c]-CPOS[a], e2y = CPOS[c+1]-CPOS[a+1], e2z = CPOS[c+2]-CPOS[a+2];
  const px = dy*e2z - dz*e2y, py = dz*e2x - dx*e2z, pz = dx*e2y - dy*e2x;
  const det = e1x*px + e1y*py + e1z*pz;
  if (Math.abs(det) < 1e-9) return best;
  const inv = 1/det;
  const tx = ox-CPOS[a], ty = oy-CPOS[a+1], tz = oz-CPOS[a+2];
  const u = (tx*px + ty*py + tz*pz) * inv;
  if (u < 0 || u > 1) return best;
  const qx = ty*e1z - tz*e1y, qy = tz*e1x - tx*e1z, qz = tx*e1y - ty*e1x;
  const v = (dx*qx + dy*qy + dz*qz) * inv;
  if (v < 0 || u + v > 1) return best;
  const t = (e2x*qx + e2y*qy + e2z*qz) * inv;
  return (t > 1e-4 && t < best) ? t : best;
}
function cast(ox, oy, oz, dx, dy, dz, max){
  let best = max;
  for (let i = 0; i < CIDX.length; i += 3)
    best = rayTri(ox, oy, oz, dx, dy, dz, i, best);
  return best;
}
/** Floor height under a point, or null. Cast from head height downward. */
function groundAt(x, y, z){
  const t = cast(x, y + STEP, z, 0, -1, 0, 60);
  return t < 60 ? (y + STEP - t) : null;
}
/** Can the body move from `from` to `to` without entering a wall? */
function blocked(fx, fy, fz, tx, tz){
  const dx = tx - fx, dz = tz - fz;
  const len = Math.hypot(dx, dz);
  if (len < 1e-6) return false;
  const nx = dx/len, nz = dz/len;
  for (const h of [0.35, 1.05, 1.62]) {
    if (cast(fx, fy + h, fz, nx, 0, nz, len + RADIUS) < len + RADIUS) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------
// SPAWN FACING DOWN THE CORRIDOR, AND CLEAR OF THE VESTIBULE. The place's own
// angle puts the eye against the room's wall -- a headless walk test measured
// 0.5 m of travel one way against 25 m the other -- so the body starts a few
// metres along the arc and looks down it. `deck_camera` does the same thing
// with `--at-offset`, and for the same reason.
const P = {x: -4, y: 0, z: 0, vy: 0, yaw: Math.PI, pitch: 0, ground: true,
           walked: 0, air: 0};
// PROBE FROM INSIDE THE CORRIDOR, NOT FROM ABOVE IT. `groundAt` casts DOWN, so
// a probe started above the soffit finds the top of the ceiling and the body
// spawns on the roof -- which is what the first browser frames showed: the deck
// receding, seen from outside, with the walls apparently missing. The corridor
// is about 2.6 m tall, so 1.0 m is inside it and 3 m is not.
{ let g = null;
  for (const x of [-4, -6, -8, -2, 0]) { g = groundAt(x, 1.0, 0);
    if (g !== null) { P.x = x; break; } }
  P.y = (g === null ? 0 : g); }

const keys = {};
addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'Space') e.preventDefault();
});
addEventListener('keyup', e => keys[e.code] = false);

const panel = document.getElementById('panel');
document.getElementById('go').addEventListener('click', () => cv.requestPointerLock());
document.addEventListener('pointerlockchange', () => {
  const on = document.pointerLockElement === cv;
  panel.classList.toggle('gone', on);
  for (const id of ['hud','reticle','note']) document.getElementById(id).hidden = !on;
});
document.addEventListener('mousemove', e => {
  if (document.pointerLockElement !== cv) return;
  P.yaw   -= e.movementX * 0.0022;
  P.pitch -= e.movementY * 0.0022;
  P.pitch = Math.max(-1.45, Math.min(1.45, P.pitch));
});

function step(dt){
  const run = keys['ShiftLeft'] || keys['ShiftRight'];
  const speed = run ? 4.6 : 1.9;              // populace._walk_speed is 1.47
  let f = 0, s = 0;
  if (keys['KeyW']) f += 1; if (keys['KeyS']) f -= 1;
  if (keys['KeyD']) s += 1; if (keys['KeyA']) s -= 1;
  const l = Math.hypot(f, s) || 1;
  const cy = Math.cos(P.yaw), sy = Math.sin(P.yaw);
  let mx = (cy * f/l - sy * s/l) * speed * dt;
  let mz = (sy * f/l + cy * s/l) * speed * dt;

  // Axis-separated so a body slides along a wall instead of stopping dead.
  if (mx && !blocked(P.x, P.y, P.z, P.x + mx, P.z)) P.x += mx; else mx = 0;
  if (mz && !blocked(P.x, P.y, P.z, P.x, P.z + mz)) P.z += mz; else mz = 0;
  P.walked += Math.hypot(mx, mz);

  P.vy += GRAV * dt;
  if (P.ground && keys['Space']) { P.vy = 4.2; P.ground = false; }
  P.y += P.vy * dt;
  const g = groundAt(P.x, P.y + STEP, P.z);
  if (g !== null && P.y <= g + 0.02) { P.y = g; P.vy = 0; P.ground = true; }
  else { P.ground = false; P.air += dt; }
  if (P.y < -40) { P.x = 0; P.z = 0; P.y = 0; P.vy = 0; }   // fell out
}

function mat(out, fov, asp, near, far, ex, ey, ez, yaw, pitch){
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const fx = cy*cp, fy = sp, fz = sy*cp;
  const rx = -sy,   ry = 0,  rz = cy;
  const ux = -cy*sp, uy = cp, uz = -sy*sp;
  const f = 1/Math.tan(fov/2), nf = 1/(near-far);
  const V = [rx,ux,-fx,0, ry,uy,-fy,0, rz,uz,-fz,0,
             -(rx*ex+ry*ey+rz*ez), -(ux*ex+uy*ey+uz*ez), (fx*ex+fy*ey+fz*ez), 1];
  const Pm = [f/asp,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0];
  for (let i=0;i<4;i++) for (let j=0;j<4;j++){
    let s=0; for (let k=0;k<4;k++) s += Pm[k*4+j]*V[i*4+k];
    out[i*4+j]=s;
  }
  return out;
}

const MVP = new Float32Array(16);
let last = 0, fps = 0;
function frame(t){
  const dt = Math.min(0.05, (t - last)/1000 || 0.016); last = t;
  fps = fps*0.9 + (1/dt)*0.1;
  if (document.pointerLockElement === cv) step(dt);

  const w = cv.clientWidth, h = cv.clientHeight;
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  gl.viewport(0,0,w,h);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  const ey = P.y + EYE_H;
  mat(MVP, 1.16, w/h, 0.05, 400, P.x, ey, P.z, P.yaw, P.pitch);
  gl.uniformMatrix4fv(U.mvp, false, MVP);
  gl.uniform3f(U.eye, P.x, ey, P.z);
  for (const m of D.materials) {
    gl.uniform3fv(U.albedo, m.albedo);
    gl.uniform3fv(U.emission, m.emission || [0,0,0]);
    gl.uniform1f(U.energy, m.emission ? m.energy : 0);
    gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, m.start * 4);
  }

  document.getElementById('hud').innerHTML =
    '<b>' + D.name + '</b> &middot; ' + D.deck + '<br>'
    + 'arc ' + P.x.toFixed(1) + ' m &middot; axis ' + P.z.toFixed(1) + ' m'
    + ' &middot; ' + (P.ground ? 'on floor' : 'in the air') + '<br>'
    + 'walked ' + P.walked.toFixed(0) + ' m &middot; ' + fps.toFixed(0) + ' fps';
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice", default=os.path.join(ROOT, "docs/web/slice.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs/web/play.html"))
    a = ap.parse_args()
    raw = open(a.slice).read()
    # `</script>` inside a JSON blob would close the tag it lives in.
    raw = raw.replace("</", "<\\/")
    open(a.out, "w").write(PAGE.replace("__SLICE__", raw))
    d = json.loads(open(a.slice).read())
    print(f"wrote {a.out} -- {os.path.getsize(a.out)/1e6:.2f} MB, "
          f"{d['tris']:,} tris, {d['col_tris']:,} collision tris")
    return 0


if __name__ == "__main__":
    sys.exit(main())
