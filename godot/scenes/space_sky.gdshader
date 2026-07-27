shader_type sky;

// Deterministic star field for the exterior shots.
//
// Why a shader and not a panorama texture: a photographic starfield HDRI would
// be a real sky from a real place, and the station is in the Epsilon Eridani
// system in the show's fiction. A procedural field commits to nothing except
// "space has stars", which is the part that is not in dispute. It also costs no
// VRAM against the 12 GB budget and cannot be wrong about a constellation.
//
// Nothing else is in here. No nebula, no galactic band, no lens flare: those
// are not established by any reference in this project and an invented one
// would be doing the aesthetic work that the station is supposed to do.
//
// Determinism is by explicit integer-free hashing of the cell coordinate --
// the same direction always yields the same star -- so two renders of the same
// camera are byte-comparable.

uniform float star_gain : hint_range(0.0, 8.0) = 2.6;
// Fraction of grid cells carrying a star. Set so a 46 deg frame holds a few
// hundred bright stars, which is roughly what a dark-adapted eye sees.
uniform float bright_density : hint_range(0.0, 1.0) = 0.022;
uniform float faint_density : hint_range(0.0, 1.0) = 0.055;

// Hash without sine (Dave Hoskins). Chosen over a sin-based hash because the
// sin trick has different precision on different drivers, and this project
// renders on llvmpipe now and on real hardware later; a starfield that moves
// between them is a diffing hazard.
vec3 hash33(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.xxy + p.yxx) * p.zyx);
}

// One layer of stars. Single-cell lookup rather than a 27-tap neighbourhood:
// the star core is a fraction of a cell across, so a star clipped at a cell
// boundary is a fraction of a pixel and invisible, and 27 taps per pixel on a
// CPU rasteriser is not.
vec3 star_layer(vec3 dir, float scale, float density, float sharp, float gain) {
	vec3 g = dir * scale;
	vec3 cell = floor(g);
	vec3 h = hash33(cell);
	if (h.x > density) {
		return vec3(0.0);
	}
	// Offset inside the cell so the field does not read as a lattice.
	vec3 centre = cell + 0.5 + (h - 0.5) * 0.7;
	float d = length(g - centre);
	// Cube the uniform draw: a few bright stars, many faint ones. Real
	// magnitude distributions are steeper still, but this reads correctly and
	// keeps the bright tail inside the tonemapper's shoulder.
	float mag = h.y * h.y * h.y;
	// Colour temperature runs blue-white (hot) to amber (cool).
	vec3 tint = mix(vec3(0.72, 0.80, 1.00), vec3(1.00, 0.84, 0.63), h.z);
	return tint * exp(-d * d * sharp) * mag * gain;
}

void sky() {
	vec3 d = normalize(EYEDIR);
	vec3 c = star_layer(d, 240.0, bright_density, 42.0, star_gain);
	c += star_layer(d, 610.0, faint_density, 30.0, star_gain * 0.30);
	COLOR = c;
}
