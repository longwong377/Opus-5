extends CanvasLayer
## THE INTERFACE. What a player is told about where they are and what they can
## do, drawn over the build they are standing in.
##
## WHAT THIS EXISTS TO END. As of session 4d this project had 85,940 lines of
## Python and 3,291 of GDScript, and the whole of its user interface was one
## `Label` in `interact.gd` reading `[E]  operate the docking clamp`. The
## owner's verdict was that it does not read as a game, and that is a fair
## reading of a first-person build with no reticle, no location readout and no
## heading: a screenshot of it is a photograph of a corridor, not a frame from
## something you play.
##
## EVERY NUMBER ON SCREEN IS ALREADY IN THE SIMULATION. Nothing here invents a
## stat, and that is the rule this file is built to. The place name and the verb
## come from `station/interact.py`'s sidecar, which derives them from
## `directory.PLACES["interacts"]`; the sector, ring and deck come from the name
## of the mesh the build was assembled from; the heading, ring angle and radius
## are read off the player body's own transform in the drum frame. A HUD that
## displays a number no system produces is a mock-up, and this project has been
## burned by artefacts that describe nothing twice already (a committed frame
## that no longer described the code, a cached triangle total).
##
## IT IS NOT IN THE HEADLESS WALK TEST. `walk.gd` skips building this under
## `--walk-test`: `station/walkable.py` parses the `WALKTEST` line and nothing
## else, and a Control tree drawing over a null rendering driver could only ever
## subtract from that gate. `--no-hud` is the control, and it is `interact.gd`'s
## flag too, so a frame taken with it has NO interface on it at all -- which is
## the A/B that says this file does something.
##
## THE LOOK IS THE SHOW'S, and it is checkable: `reference/03-sector-blue/
## comand and contorl.webp` is Command and Control lit the way B5 lights it --
## near-black blue, cold cyan strip light, amber and red on the consoles, and
## not one rounded panel or soft shadow anywhere. So: hairlines, small tracked
## capitals, cyan for state and amber for the thing you can act on, and no fill
## heavier than a wash. Nothing here is skeuomorphic and nothing is decorative.

# -- palette, sampled from the reference frame ------------------------------
# Cyan is the strip lighting, amber the console keys, ink the wall in shadow.
const CYAN := Color(0.494, 0.812, 0.882)
const AMBER := Color(1.0, 0.702, 0.290)
const INK := Color(0.016, 0.031, 0.047)

## How long the prompt takes to arrive and to leave, in seconds. Short enough
## that it feels like a response and long enough that it is not a flicker.
const FADE_S := 0.10

## Where the compass tape stops caring, in degrees either side of the heading.
const TAPE_SPAN_DEG := 60.0

# -- what the face draws, recomputed every frame ----------------------------
var place_name := ""
var place_inside := false
var near_name := ""
var near_m := 0.0
var sector := ""
var ring := ""
var deck := ""
var heading_deg := 0.0
var ring_deg := 0.0
var radius_m := 0.0
var speed_m_s := 0.0
var gravity_m_s2 := 0.0
var field := ""
var prompt_verb := ""
var prompt_label := ""
var prompt_place := ""
var prompt_m := 0.0
var hot := 0.0

# UNTYPED ON PURPOSE, all three. `_player`'s `gravity_mode`, `_interact`'s
# `refresh()` and `Face`'s `h` are SCRIPT members, not members of CharacterBody3D,
# Node or Control -- and GDScript resolves a statically typed variable's members
# at parse time, so declaring these with their engine types makes the file fail
# to compile rather than fail to run. The alternative is `.get("gravity_mode")`
# everywhere, which hides what is being read.
var _player
var _cam: Camera3D
var _interact
var _face
## place key -> [lo, hi] world box, unioned over that place's interactables.
var _boxes := {}
var _last_report := ""


## Wire the HUD to the body it belongs to and to the things it can name.
##
## `glb` is the mesh the deck was assembled from and it is the ONLY place the
## sector/ring/deck triple is available in the engine: `walkable.py` names the
## file `{sector}_{ring}_{deck}[_z{z}].glb` and hands the engine world metres,
## not an address. Reading the address off the filename is the same trick
## `dress_scene.gd` uses to stay inside one description of the look -- the
## generator already decided, so nothing here decides again.
func bind(player: Node3D, interact: Node, glb: String,
		interact_json: String) -> void:
	_player = player
	if _player != null:
		_cam = _player.get_node_or_null("Camera3D") as Camera3D
		gravity_m_s2 = float(_player.gravity_m_s2)
		field = String(_player.gravity_mode).to_upper()
	_interact = interact
	_address(glb)
	_places(interact_json)

	# ONE PROMPT, NOT TWO. `interact.gd` carries a bare debug Label from the
	# session that introduced the verb table, and `walk.gd` still reads its text
	# back for the `used_prompt=` field of the WALKTEST verdict -- so it is
	# HIDDEN rather than removed or emptied. Deleting it would take a gate's
	# evidence with it; leaving it visible would put two sentences on screen.
	if _interact != null:
		var old = _interact.get_node_or_null("UseHUD")
		if old != null:
			old.visible = false

	_face = Face.new()
	_face.h = self
	_face.name = "Face"
	_face.set_anchors_preset(Control.PRESET_FULL_RECT)
	_face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_face)
	set_process(true)


## The address, off the name of the mesh. `shot_blue_0_0.glb`, `blue_0_0.glb`
## and `blue_0_0_z7114_col.glb` all name the same deck.
func _address(glb: String) -> void:
	var stem := glb.get_file().get_basename()
	if stem.begins_with("shot_"):
		stem = stem.substr(5)
	if stem.ends_with("_col"):
		stem = stem.substr(0, stem.length() - 4)
	if stem.ends_with("_nouse"):
		stem = stem.substr(0, stem.length() - 6)
	var p := stem.split("_")
	if p.size() >= 3:
		sector = String(p[0]).to_upper()
		ring = String(p[1])
		deck = String(p[2])


## Where the named places are, unioned from their own interactables' boxes.
##
## NOT A SECOND REGISTER. `station/directory.py` holds the 128 places and their
## addresses and it is Python; the engine never sees it. What the engine does
## see is the interact sidecar, and every row on it carries the `place` it
## belongs to and a measured world box -- so the extent of a place is the extent
## of the things in it. That is approximate at the edges and it is DERIVED,
## which is the property that matters: it cannot disagree with the register,
## because it is made of the register's own output.
func _places(path: String) -> void:
	if path == "" or not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	var rows = JSON.parse_string(f.get_as_text())
	if typeof(rows) != TYPE_ARRAY:
		return
	for row in rows:
		if typeof(row) != TYPE_DICTIONARY:
			continue
		var key := String(row.get("place", ""))
		var c = row.get("centre")
		var hf = row.get("half")
		if key == "" or typeof(c) != TYPE_ARRAY or typeof(hf) != TYPE_ARRAY:
			continue
		if c.size() != 3 or hf.size() != 3:
			continue
		var ctr := Vector3(float(c[0]), float(c[1]), float(c[2]))
		var hv := Vector3(float(hf[0]), float(hf[1]), float(hf[2]))
		var lo: Vector3 = ctr - hv
		var hi: Vector3 = ctr + hv
		if _boxes.has(key):
			var b: Array = _boxes[key]
			_boxes[key] = [Vector3(minf(b[0].x, lo.x), minf(b[0].y, lo.y),
					minf(b[0].z, lo.z)),
				Vector3(maxf(b[1].x, hi.x), maxf(b[1].y, hi.y),
					maxf(b[1].z, hi.z))]
		else:
			_boxes[key] = [lo, hi]


## A place key as a person would read it: `bay_elevators` -> `BAY ELEVATORS`.
func _pretty(key: String) -> String:
	return key.replace("_", " ").to_upper()


func _process(delta: float) -> void:
	if _player == null:
		return
	var p: Vector3 = _player.global_position
	radius_m = sqrt(p.x * p.x + p.y * p.y)
	ring_deg = fposmod(rad_to_deg(atan2(p.y, p.x)), 360.0)
	var vel: Vector3 = _player.velocity
	speed_m_s = vel.length()

	# -- HEADING, IN THE FRAME THE STATION ACTUALLY HAS -------------------
	# A compass rose is a planet's idea. This is a spinning ring 8 km long, so
	# the two axes that mean anything are ALONG THE SPINE and AROUND THE BARREL:
	# FORE and AFT down +Z and -Z, SPINWARD and ANTISPINWARD tangentially. The
	# tangent is z_hat x r_hat, the same handedness `player.gd` derives its
	# walking basis from, so a player who walks "spinward" on this tape is
	# walking the way the drum turns.
	var fwd := Vector3(0, 0, 1)
	if _cam != null:
		fwd = -_cam.global_transform.basis.z
	elif _player != null:
		fwd = -_player.global_transform.basis.z
	var radial := Vector3(p.x, p.y, 0.0)
	if radial.length() > 1.0:
		radial = radial.normalized()
		var tangent := Vector3(0, 0, 1).cross(radial).normalized()
		heading_deg = fposmod(rad_to_deg(atan2(fwd.dot(tangent),
			fwd.dot(Vector3(0, 0, 1)))), 360.0)
	else:
		heading_deg = fposmod(rad_to_deg(atan2(fwd.x, fwd.z)), 360.0)

	_where(p)

	# -- WHAT IS IN REACH -------------------------------------------------
	# `interact.gd::refresh()` is frame-guarded and idempotent, so asking it
	# here cannot double-count `prompt_frames` and cannot disagree with what the
	# `E` key would use. There is no second look-at test in this file, for the
	# same reason there is no second verb table.
	var it = null
	if _interact != null:
		it = _interact.refresh()
	if it != null:
		prompt_verb = String(it.verb).to_upper()
		prompt_label = String(it.label).to_upper()
		prompt_place = _pretty(String(it.place))
		# FROM THE EYE, because `interact.gd::scan` measures its reach from the
		# eye. Measured from the body's origin instead, a bay door 2.5 m up
		# reads 3.09 m on a HUD whose prompt only appears inside 2.40 m -- a
		# number that contradicts the thing it is printed next to.
		var from: Vector3 = (_cam.global_position if _cam != null else p)
		prompt_m = from.distance_to(it.centre)
	hot = move_toward(hot, (1.0 if it != null else 0.0),
		delta / maxf(FADE_S, 0.001))
	if _face != null:
		_face.queue_redraw()

	var line := report()
	if line != _last_report:
		_last_report = line
		print("hud: %s" % line)


## Which named place the body is standing in, or the nearest one and how far.
func _where(p: Vector3) -> void:
	place_inside = false
	place_name = ""
	near_name = ""
	near_m = 0.0
	var best := INF
	for k in _boxes:
		var b: Array = _boxes[k]
		var lo: Vector3 = b[0]
		var hi: Vector3 = b[1]
		# 1.5 m of slack, because a place's extent here is the extent of the
		# things IN it and a room is bigger than its furniture.
		if p.x >= lo.x - 1.5 and p.x <= hi.x + 1.5 \
				and p.y >= lo.y - 1.5 and p.y <= hi.y + 1.5 \
				and p.z >= lo.z - 1.5 and p.z <= hi.z + 1.5:
			place_inside = true
			place_name = _pretty(String(k))
			return
		var q := Vector3(clampf(p.x, lo.x, hi.x), clampf(p.y, lo.y, hi.y),
			clampf(p.z, lo.z, hi.z))
		var d := p.distance_to(q)
		if d < best:
			best = d
			near_name = _pretty(String(k))
			near_m = d
	# Between rooms is not nowhere: on a ring deck it is the corridor, which is
	# a place a player spends most of their time.
	place_name = "CORRIDOR"


## One line, for the log. Printed on change rather than every frame, so a shot
## run says what was on screen when the shutter opened without a wall of text.
func report() -> String:
	var s := "%s %s/%s/%s hdg=%.0f ring=%.1f r=%.1f" % [
		(place_name if place_inside else place_name + "(near " + near_name
			+ " %.1fm)" % near_m),
		sector.to_lower(), ring, deck, heading_deg, ring_deg, radius_m]
	if prompt_verb != "" and hot > 0.5:
		s += " prompt=%s/%s %.2fm" % [prompt_verb.to_lower(),
			prompt_label.to_lower().replace(" ", "_"), prompt_m]
	else:
		s += " prompt=-"
	return s


## THE FACE. Everything is drawn rather than assembled from Control nodes, and
## that is a deliberate choice rather than laziness: the whole interface is
## hairlines, ticks and small capitals, none of which a StyleBox can express
## without a texture, and a texture is a binary resource this project has a
## standing rule against. Drawing it also means the entire look is in one
## reviewable function instead of forty exported properties in a .tscn.
class Face extends Control:
	var h                                  # the HUD that owns this face

	## Godot's built-in font. No download, no import, no binary in the tree --
	## and the network is restricted in this container anyway.
	var _font: Font = ThemeDB.fallback_font

	func _draw() -> void:
		if h == null or _font == null:
			return
		var sz := size
		# One scale for the whole interface, from the frame height, so a 640x360
		# check render and a 1440p frame carry the same design rather than the
		# same pixel sizes.
		var s: float = maxf(sz.y / 720.0, 0.35)
		_compass(sz, s)
		_location(sz, s)
		_reticle(sz, s)
		_prompt(sz, s)
		_systems(sz, s)

	# -- primitives ---------------------------------------------------------

	func _hair(a: Vector2, b: Vector2, c: Color, s: float, w := 1.0) -> void:
		draw_line(a, b, c, maxf(1.0, roundf(w * s)), false)

	## A hairline that survives a white background: the same line laid twice,
	## once thick in the near-black and once thin in its own colour.
	##
	## THIS IS AN OUTLINE, NOT A DROP SHADOW, and the difference is the whole
	## point. A shadow is offset and soft and reads as a mobile-game overlay; a
	## concentric dark keyline is what a lit legend on a console has, and it is
	## the only way a cyan hairline stays legible against both the near-black
	## corridor and the white cargo the docking bay is full of. Measured on
	## `docs/engine-4e-hud-idle.png`: without it the reticle disappears against
	## crates.
	func _hair2(a: Vector2, b: Vector2, c: Color, s: float) -> void:
		draw_line(a, b, Color(INK, c.a * 0.85), maxf(3.0, roundf(3.0 * s)),
			false)
		draw_line(a, b, c, maxf(1.0, roundf(s)), false)

	## A wash of the near-black the show's panels are cut from, faded out at one
	## or both ends so it reads as a lit plate rather than as a box. Drawn in
	## strips because a CanvasItem gradient needs a texture, and a texture is a
	## binary resource this project does not commit.
	func _scrim(r: Rect2, a: float, fx: Vector2, fy := Vector2.ZERO) -> void:
		# fx/fy are (fade at the low edge, fade at the high edge) as fractions
		# of the rect. Zero means a hard edge, which is right where the rect
		# runs off the side of the frame and wrong everywhere else -- a wash
		# with four hard edges is a panel, and a panel is not what B5 does.
		#
		# NINE QUADS WITH VERTEX COLOURS, not a stack of translucent strips.
		# The strip version of this was visible as a GRID at magnification --
		# each cell was drawn one pixel oversize to avoid seams, so every
		# overlap doubled the alpha and the wash read as graph paper. Rendering
		# it at the rubric's half distance is what found it, which is the rule
		# `docs/AAA-STANDARD.md` has always carried and this project keeps
		# relearning. Shared vertices cannot seam and cannot double.
		var xs := [r.position.x, r.position.x + r.size.x * fx.x,
			r.end.x - r.size.x * fx.y, r.end.x]
		var ys := [r.position.y, r.position.y + r.size.y * fy.x,
			r.end.y - r.size.y * fy.y, r.end.y]
		var ax := [(0.0 if fx.x > 0.0 else 1.0), 1.0, 1.0,
			(0.0 if fx.y > 0.0 else 1.0)]
		var ay := [(0.0 if fy.x > 0.0 else 1.0), 1.0, 1.0,
			(0.0 if fy.y > 0.0 else 1.0)]
		for i in 3:
			if xs[i + 1] - xs[i] < 0.5:
				continue
			for j in 3:
				if ys[j + 1] - ys[j] < 0.5:
					continue
				draw_polygon(PackedVector2Array([
						Vector2(xs[i], ys[j]), Vector2(xs[i + 1], ys[j]),
						Vector2(xs[i + 1], ys[j + 1]),
						Vector2(xs[i], ys[j + 1])]),
					PackedColorArray([
						Color(INK, a * ax[i] * ay[j]),
						Color(INK, a * ax[i + 1] * ay[j]),
						Color(INK, a * ax[i + 1] * ay[j + 1]),
						Color(INK, a * ax[i] * ay[j + 1])]))

	## Small capitals with the letters pushed apart. The show's signage and its
	## console legends are both tracked, and untracked default-font capitals
	## read as a debug overlay, which is what this file exists to stop being.
	func _tracked(pos: Vector2, text: String, px: int, c: Color,
			track: float) -> float:
		var x := pos.x
		for i in text.length():
			var ch := text[i]
			draw_char(_font, Vector2(x, pos.y), ch, px, c)
			x += _font.get_char_size(ch.unicode_at(0), px).x + track
		return x - pos.x

	func _tracked_width(text: String, px: int, track: float) -> float:
		var w := 0.0
		for i in text.length():
			w += _font.get_char_size(text[i].unicode_at(0), px).x + track
		return maxf(w - track, 0.0)

	## An L-bracket, the corner detail every B5 console panel is edged with.
	func _bracket(at: Vector2, dx: float, dy: float, c: Color,
			s: float) -> void:
		_hair(at, at + Vector2(dx, 0), c, s)
		_hair(at, at + Vector2(0, dy), c, s)

	# -- the heading tape ---------------------------------------------------

	## FORE / SPINWARD / AFT / ANTISPINWARD, because that is what a ring has.
	func _cardinal(deg: int) -> String:
		match deg:
			0: return "FORE"
			90: return "SPIN"
			180: return "AFT"
			270: return "ANTI"
		return ""

	func _compass(sz: Vector2, s: float) -> void:
		var cx := sz.x * 0.5
		var y := 44.0 * s
		var half := minf(260.0 * s, sz.x * 0.34)
		var ppd := half / TAPE_SPAN_DEG
		var hdg: float = h.heading_deg

		_scrim(Rect2(cx - half - 30.0 * s, y - 36.0 * s, (half + 30.0 * s) * 2.0,
			76.0 * s), 0.50, Vector2(0.30, 0.30), Vector2(0.22, 0.34))

		# The baseline, faded out at both ends so the tape reads as a window on
		# something continuous rather than as a bar with hard stops.
		var segs := 48
		for i in segs:
			var x0 := cx - half + (2.0 * half) * (float(i) / segs)
			var x1 := cx - half + (2.0 * half) * (float(i + 1) / segs)
			var t := absf((x0 + x1) * 0.5 - cx) / half
			var a: float = 0.42 * (1.0 - t * t)
			_hair(Vector2(x0, y), Vector2(x1, y), Color(CYAN, a), s)

		var base := int(floor((hdg - TAPE_SPAN_DEG) / 5.0)) * 5
		for k in range(0, int(TAPE_SPAN_DEG * 2 / 5) + 3):
			var d := base + k * 5
			var off := wrapf(float(d) - hdg, -180.0, 180.0)
			if absf(off) > TAPE_SPAN_DEG:
				continue
			var x := cx + off * ppd
			var t2 := absf(off) / TAPE_SPAN_DEG
			var fade: float = clampf(1.0 - t2 * t2, 0.0, 1.0)
			var dd := int(fposmod(float(d), 360.0))
			var major := (dd % 15) == 0
			_hair(Vector2(x, y), Vector2(x, y + (9.0 if major else 4.0) * s),
				Color(CYAN, (0.85 if major else 0.45) * fade), s)
			if not major:
				continue
			var lab := _cardinal(dd)
			var px := int(roundf(11.0 * s))
			var col := Color(CYAN, 0.95 * fade)
			if lab == "":
				if dd % 30 != 0:
					continue
				lab = "%03d" % dd
				col = Color(CYAN, 0.62 * fade)
			var w := _tracked_width(lab, px, 1.2 * s)
			_tracked(Vector2(x - w * 0.5, y + 22.0 * s), lab, px, col, 1.2 * s)

		# The index. A caret over the tape and the number under it, in amber,
		# because it is the one value on the strip that is about YOU.
		var pts := PackedVector2Array([
			Vector2(cx - 5.0 * s, y - 9.0 * s),
			Vector2(cx + 5.0 * s, y - 9.0 * s),
			Vector2(cx, y - 1.0 * s)])
		draw_colored_polygon(pts, Color(AMBER, 0.92))
		_hair(Vector2(cx, y), Vector2(cx, y + 13.0 * s), Color(AMBER, 0.55), s)
		var num := "%03d" % int(roundf(fposmod(hdg, 360.0)))
		var px2 := int(roundf(13.0 * s))
		var nw := _tracked_width(num, px2, 2.0 * s)
		var box := Rect2(cx - nw * 0.5 - 7.0 * s, y - 30.0 * s,
			nw + 14.0 * s, 19.0 * s)
		draw_rect(box, Color(INK, 0.55), true)
		draw_rect(box, Color(AMBER, 0.55), false, maxf(1.0, roundf(s)))
		_tracked(Vector2(cx - nw * 0.5, y - 15.5 * s), num, px2,
			Color(AMBER, 0.95), 2.0 * s)

	# -- where you are ------------------------------------------------------

	func _location(sz: Vector2, s: float) -> void:
		var x := 34.0 * s
		var y := 40.0 * s
		var px := int(roundf(21.0 * s))
		var here: String = h.place_name
		var addr := "SECTOR %s   RING %s   DECK %s" % [h.sector, h.ring, h.deck]
		var third := "R %.1f M   PHI %05.1f" % [h.radius_m, h.ring_deg]
		if not h.place_inside and h.near_name != "":
			third = "%s  %.0f M   %s" % [h.near_name, h.near_m, third]

		var wide: float = maxf(maxf(_tracked_width(here, px, 3.0 * s),
			_tracked_width(addr, int(roundf(11.0 * s)), 1.6 * s)),
			_tracked_width(third, int(roundf(10.0 * s)), 1.4 * s))
		_scrim(Rect2(0.0, 0.0, x + wide + 74.0 * s, y + 62.0 * s), 0.54,
			Vector2(0.0, 0.36), Vector2(0.0, 0.34))

		_bracket(Vector2(x - 12.0 * s, y - 20.0 * s), 16.0 * s, 22.0 * s,
			Color(CYAN, 0.70), s)
		var w := _tracked(Vector2(x, y), here, px, Color(CYAN, 0.98), 3.0 * s)

		var rule_w: float = maxf(w, 196.0 * s)
		_hair(Vector2(x, y + 9.0 * s), Vector2(x + rule_w, y + 9.0 * s),
			Color(CYAN, 0.42), s)

		_tracked(Vector2(x, y + 26.0 * s), addr, int(roundf(11.0 * s)),
			Color(CYAN, 0.74), 1.6 * s)
		_tracked(Vector2(x, y + 42.0 * s), third, int(roundf(10.0 * s)),
			Color(CYAN, 0.52), 1.4 * s)

	# -- the reticle --------------------------------------------------------

	## FOUR TICKS AND A DOT, and it changes when something is in reach.
	##
	## The state change is the whole job: `interact.gd` decides what you are
	## looking at with a cone and a line-of-sight ray, and until this file
	## existed a player had no way to know it had decided anything until the
	## prompt text appeared. The ticks open out, turn from the strip-light cyan
	## to the console amber and rotate a quarter turn into a diamond, so the
	## reticle answers "can I touch that" before the sentence does.
	func _reticle(sz: Vector2, s: float) -> void:
		var c := sz * 0.5
		var hotf: float = h.hot
		var gap: float = lerpf(5.0, 10.5, hotf) * s
		var ln: float = lerpf(4.0, 7.0, hotf) * s
		var col: Color = CYAN.lerp(AMBER, hotf)
		col.a = lerpf(0.55, 0.95, hotf)
		var rot: float = hotf * PI * 0.25
		for i in 4:
			var a: float = rot + float(i) * PI * 0.5
			var d := Vector2(cos(a), sin(a))
			_hair2(c + d * gap, c + d * (gap + ln), col, s)
		draw_circle(c, maxf(2.0, 2.2 * s), Color(INK, 0.8))
		draw_circle(c, maxf(1.0, 1.1 * s), Color(col, lerpf(0.85, 1.0, hotf)))
		if hotf > 0.01:
			draw_arc(c, 15.0 * s, 0.0, TAU, 48, Color(INK, 0.55 * hotf),
				maxf(3.0, roundf(3.0 * s)), false)
			draw_arc(c, 15.0 * s, 0.0, TAU, 48, Color(AMBER, 0.40 * hotf),
				maxf(1.0, roundf(s)), false)

	# -- what you can do ----------------------------------------------------

	func _prompt(sz: Vector2, s: float) -> void:
		var a: float = h.hot
		if a <= 0.01 or h.prompt_verb == "":
			return
		var cx := sz.x * 0.5
		# Rises the last few pixels as it fades in. Motion is what makes it
		# read as an answer to where the player is looking.
		var y: float = sz.y * 0.5 + 94.0 * s + (1.0 - a) * 8.0 * s

		var px := int(roundf(15.0 * s))
		var key := 24.0 * s
		var verb: String = h.prompt_verb
		var label: String = h.prompt_label
		var vw := _tracked_width(verb, px, 2.6 * s)
		var lw := _tracked_width(label, px, 2.6 * s)
		var pad := 15.0 * s
		var total: float = key + pad + vw + pad + 1.0 + pad + lw
		var x := cx - total * 0.5
		_scrim(Rect2(x - 50.0 * s, y - 26.0 * s, total + 100.0 * s, 64.0 * s),
			0.52 * a, Vector2(0.32, 0.32), Vector2(0.30, 0.34))

		# The key glyph: a square outline with the letter in it. Square, not
		# rounded -- there is not a rounded corner anywhere in Command and
		# Control.
		var kr := Rect2(x, y - key * 0.5, key, key)
		draw_rect(kr, Color(INK, 0.60 * a), true)
		draw_rect(kr, Color(AMBER, 0.85 * a), false, maxf(1.0, roundf(s)))
		var kpx := int(roundf(13.0 * s))
		var kw := _font.get_char_size(69, kpx).x        # "E"
		draw_char(_font, Vector2(kr.position.x + (key - kw) * 0.5,
			y + kpx * 0.36), "E", kpx, Color(AMBER, 0.95 * a))

		var tx := x + key + pad
		_tracked(Vector2(tx, y + px * 0.36), verb, px, Color(AMBER, 0.95 * a),
			2.6 * s)
		tx += vw + pad
		_hair(Vector2(tx, y - 8.0 * s), Vector2(tx, y + 8.0 * s),
			Color(CYAN, 0.35 * a), s)
		tx += pad
		_tracked(Vector2(tx, y + px * 0.36), label, px, Color(CYAN, 0.92 * a),
			2.6 * s)

		# A hairline under the whole thing, and the room it is in at the right
		# hand end -- the same information the location block carries, repeated
		# where the eye already is.
		var uy := y + 17.0 * s
		_hair(Vector2(x, uy), Vector2(x + total, uy), Color(AMBER, 0.30 * a), s)
		var sub: String = "%s   %.1f M" % [h.prompt_place, h.prompt_m]
		var spx := int(roundf(9.0 * s))
		var sw := _tracked_width(sub, spx, 1.2 * s)
		_tracked(Vector2(x + total - sw, uy + 12.0 * s), sub, spx,
			Color(CYAN, 0.60 * a), 1.2 * s)

	# -- the body's own state ----------------------------------------------

	func _systems(sz: Vector2, s: float) -> void:
		var x := 34.0 * s
		var y := sz.y - 34.0 * s
		var txt := "%s FIELD   %.2f M/S2   %.1f M/S" % [
			h.field, h.gravity_m_s2, h.speed_m_s]
		var w := _tracked_width(txt, int(roundf(10.0 * s)), 1.4 * s)
		_scrim(Rect2(0.0, y - 24.0 * s, x + w + 64.0 * s, sz.y - y + 24.0 * s),
			0.54, Vector2(0.0, 0.36), Vector2(0.34, 0.0))
		_hair(Vector2(x - 10.0 * s, y - 10.0 * s),
			Vector2(x - 10.0 * s, y + 3.0 * s), Color(AMBER, 0.75), s)
		_tracked(Vector2(x, y), txt, int(roundf(10.0 * s)), Color(CYAN, 0.62),
			1.4 * s)
