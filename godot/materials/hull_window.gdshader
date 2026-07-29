shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

// GENERATED BINDING, HAND-WRITTEN SHADER. `station/materials.py` writes the
// .tres that references this file and asserts that every uniform the .tres sets
// is declared here. Editing this file changes what renders; editing the .tres
// does not survive the next export.
//
// WHY THIS EXISTS: the habitat hull has no UVs.
//
// `station/export_gltf.py` writes POSITION and NORMAL and nothing else, so every
// material in the project relies on Godot's world triplanar. That is correct for
// greebles and plating -- an axis-aligned box of hull looks the same from any of
// the three projections -- and it is WRONG for a pattern with an orientation.
//
// Triplanar blends the x, y and z projections by the surface normal. On the
// drum's barrel the x and y projections both contribute, each carries its own
// grid of window rows, and the two do not line up. Session 3k's first engine
// frame showed the result as a crosshatch lattice over the window bands, logged
// as a major against `exterior_approach`. It is not a tuning problem: a window
// band runs AROUND a cylinder, and no blend of three flat projections says that.
//
// So the mapping is cylindrical about the station's spin axis, which is world
// +Z in `interior.py` and everywhere else in this project.

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D orm_tex : hint_default_white, filter_linear_mipmap_anisotropic;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic;
uniform sampler2D emission_tex : source_color, filter_linear_mipmap_anisotropic;

uniform vec4 albedo_color : source_color = vec4(0.833, 0.808, 0.783, 1.0);
uniform vec3 emission_color : source_color = vec3(1.0, 1.0, 1.0);
uniform float emission_energy = 3.4;
uniform float metallic = 0.34;
uniform float roughness = 0.58;
uniform float specular = 0.45;
uniform float normal_scale = 1.0;

// The sheet's metric repeat -- station/materials.py WINDOW_REPEAT_M, which is
// WINDOW_ROWS * interior.DECK_PITCH_M. Passed in rather than written here so the
// two cannot drift.
uniform float repeat_m = 28.8;

// THE SEAM. An arc-length coordinate (angle * radius) jumps by one circumference
// at +/-pi, and a texture sampled across that jump gets a hard mismatched column
// plus a mip-selection artefact. The fix is to make the pattern close exactly:
// the number of repeats around the circumference is snapped to a whole number at
// a REFERENCE radius, so fract(u) meets itself at the seam.
//
// Snapping per-fragment radius instead would close the seam at every radius and
// put a visible ring wherever the whole number steps -- which the tapered aft
// block would show as a stack of bands. One reference radius means the barrel is
// exact and the taper is stretched by at most half a window, which nothing can
// see. `station/materials.py` passes interior.sector_shell_radius(green).
uniform float ref_radius_m = 314.3;

// LONG-PERIOD VARIATION. One 28.8 m repeat over a 1,209 m drum is 42 identical
// courses and reads as ladder rungs -- the second major from the same round. A
// block of hull with no quarters behind it has no lit windows, so whole blocks
// go dark. Sized in repeats, not metres, so a block boundary always lands on a
// tile boundary and never cuts a window in half.
uniform float dark_block_fraction : hint_range(0.0, 1.0) = 0.28;
uniform float block_repeats = 5.0;

varying vec3 world_pos;

// TAU is a Godot built-in; redeclaring it fails compilation with
// "Redefinition of 'TAU'" -- and a failed shader still RENDERS, on the
// fallback, so the frame comes back looking merely wrong rather than
// broken. tools/render_godot.sh now fails the run on SHADER ERROR.
const float TWO_PI = 6.283185307179586;

// Hash without sine, same reason as space_sky.gdshader: the sin trick has
// different precision on different drivers, and this project renders on llvmpipe
// now and on real hardware later. A window that lights up when the GPU changes
// is a diffing hazard.
float hash21(vec2 p) {
	vec3 q = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
	q += dot(q, q.yzx + 33.33);
	return fract((q.x + q.y) * q.z);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float ang = atan(world_pos.y, world_pos.x);
	// Whole repeats around the circumference at the reference radius, so u
	// increases by an integer over a full turn and the seam closes.
	float cols = max(1.0, floor(TWO_PI * ref_radius_m / repeat_m + 0.5));
	vec2 uv = vec2(ang / TWO_PI * cols, world_pos.z / repeat_m);

	// Derivatives from the SMOOTH tangent frame rather than from uv, which is
	// discontinuous at the seam. Taking dFdx(uv) there gives a gradient the
	// width of the whole station and selects the smallest mip, which draws the
	// seam as a blurred stripe -- the artefact this mapping exists to remove,
	// reintroduced by the way it is sampled.
	vec3 t_circ = normalize(vec3(-world_pos.y, world_pos.x, 0.0) + vec3(1e-6));
	vec3 dpdx = dFdx(world_pos);
	vec3 dpdy = dFdy(world_pos);
	vec2 ddx = vec2(dot(dpdx, t_circ), dpdx.z) / repeat_m;
	vec2 ddy = vec2(dot(dpdy, t_circ), dpdy.z) / repeat_m;

	vec4 alb = textureGrad(albedo_tex, uv, ddx, ddy);
	vec3 orm = textureGrad(orm_tex, uv, ddx, ddy).rgb;
	vec3 nrm = textureGrad(normal_tex, uv, ddx, ddy).rgb;
	vec3 emi = textureGrad(emission_tex, uv, ddx, ddy).rgb;

	ALBEDO = alb.rgb * albedo_color.rgb;
	AO = orm.r;
	AO_LIGHT_AFFECT = 0.35;
	ROUGHNESS = orm.g * roughness;
	METALLIC = orm.b * metallic;
	SPECULAR = specular;
	NORMAL_MAP = nrm;
	NORMAL_MAP_DEPTH = normal_scale;

	float blk = hash21(floor(uv / block_repeats));
	EMISSION = emi * emission_color * emission_energy
		* step(dark_block_fraction, blk);
}
