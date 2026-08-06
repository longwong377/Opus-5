extends Node3D
## The station's ambience, as a runtime view of `station/audio.py`'s beds.
##
## WHAT THIS EXISTS TO END: layer 7 read `0` in CLAUDE.md's table from the day
## the table was written, and session 4d's audit put it plainly -- **no audio
## at all**. The owner's standard names "the sound" in the same breath as the
## textures and the physics. Until this file, the string `AudioStream` appeared
## nowhere in the project.
##
## IT MIXES, IT DOES NOT CHOOSE. Every level here comes out of
## `station/generated/audio/beds.json`, which `station/audio.py` derives from
## the occupancy, the species sleep cycles, the ship manifest and the fixture
## list. Nothing in this file decides how loud a room is, and that is the
## point: change the crowd density in Python and the murmur changes here
## without this script being touched.
##
## WHAT IT NEEDS FROM THE GENERATOR, all of it self-describing:
##
##   bank.json    the stream bank -- one WAV per timbre, with each stream's
##                measured RMS so the runtime can level-match them, the master
##                trim, and the emitter match rules
##   beds.json    per place, per hour, a level in dBA for every layer
##   the meshes   room content is named `<place_key>__<group>` by `rooms.py`,
##                so the place the player is standing in is read off the
##                GEOMETRY. There is no second table of room bounds to drift.
##
## WHY THE WAVs ARE PARSED BY HAND. Godot's `.wav` import needs an editor to
## write the `.import` sidecar, and everything in this project is generated
## headlessly. `AudioStreamWAV` takes raw PCM in `data`, so the RIFF header is
## read here -- fifty lines, no import step, and the file on disk is exactly
## what `station/audio.py --write` measured. A build step that only works in a
## GUI is a build step that rots.
##
## THE LOOPS ARE SEAMLESS BY CONSTRUCTION, not by fading. Every stream is
## synthesised in a circular buffer with spectral filtering, so `loop_begin=0`
## and `loop_end=<all of it>` is correct with nothing to cross-fade. See
## `station/audio.seam()`, which measures both artefacts a loop can have -- a
## click and a pump -- and has a negative control that fires on each.

## WHERE AM I is asked of one implementation, not of two. `hud.gd` and this file
## each derived a place's extent and disagreed by 31.6 m -- the HUD said
## `CORRIDOR (near CUSTOMS NORTH 31.6 m)` while this file said
## `place=customs_north` -- because the HUD measured the bounding box of a room's
## INTERACTABLES and this one measured the room's own geometry. The geometry rule
## was the right one and it now lives in `scripts/places.gd`, where both read it.
##
## `preload` AND NOT `class_name`, deliberately: a global class name resolves
## through the project's script-class list, which a fresh headless run has not
## scanned, so the identifier does not parse, `set_script` fails, and the cold
## start comes back `hud=0, audio_layers=0` with nothing obviously wrong.
const Places := preload("res://scripts/places.gd")

## Written by `station/audio.py --write`.
@export var bank_path: String = ""
@export var beds_path: String = ""
## Directory holding the WAVs. Defaults to the directory `bank_path` is in.
@export var audio_dir: String = ""
## Station hour, EMT. 03:00 and 13:00 are different places; that is the whole
## claim of the layer and it is asserted in `station/audio.py`'s self-test.
@export var hour: float = 13.0
## Seconds for a bed to reach a new target. A room does not change its sound
## the instant you cross the threshold -- you hear the next room before you
## are in it, and the one behind you after you have left.
@export var crossfade_s: float = 2.5
## How often the emitter set is re-sorted by distance. Every frame is waste;
## a walking player covers 0.7 m in this.
@export var emitter_refresh_s: float = 0.5
## Below this the layer's player is stopped outright, so a station of 128
## places is not 900 silent voices.
@export var silence_db: float = -60.0

var _bank: Dictionary = {}
var _beds: Dictionary = {}
var _streams: Dictionary = {}          # stream name -> AudioStreamWAV
var _players: Dictionary = {}          # "layer:stream" -> {node, db, target}
var _place_aabb: Dictionary = {}       # place key -> AABB in world space
var _emitters: Array = []              # {node, base_db, pos}
var _body: Node3D
var _here := ""
var _fallback := "central_corridor"
var _since_refresh := 0.0
## False until the first mix has run. See `_process`: the first bed a build ever
## learns snaps to its level; everything after it crossfades.
var _started := false
var _ref_dba := 94.0
var _master_trim := 0.0
var _emitter_ref := 60.0
var _calls: Array = []                 # the day's announcements, from bank.json
var _call_window := 0.25
var _pa: AudioStreamPlayer             # the one-shot the tannoy speaks through
var _fired := {}                       # index -> already spoken at this hour
var _last_call := ""


func _ready() -> void:
	if bank_path != "":
		load_bank(bank_path, beds_path)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

func load_bank(bank_file: String, beds_file: String) -> bool:
	_bank = _json(bank_file)
	if _bank.is_empty():
		push_error("ambience: no bank at %s" % bank_file)
		return false
	if beds_file != "":
		_beds = _json(beds_file)
	if audio_dir == "":
		audio_dir = bank_file.get_base_dir()
	_ref_dba = float(_bank.get("ref_dba_at_0dbfs", 94.0))
	_master_trim = float(_bank.get("master_trim_db", 0.0))
	_emitter_ref = float(_bank.get("emitter_ref_dba", 60.0))
	_fallback = String(_bank.get("fallback_place", _fallback))
	# ANNOUNCEMENTS ARE NOT PART OF THE BED, and the headless test is why. The
	# bed manifest is hourly; `broadcast`'s audibility window is a quarter of an
	# hour. Folding a call into the hourly bed made a chime that fires once read
	# as a tannoy that never stops -- it appeared at 03:00 and 13:00 alike. They
	# are a list with their real times, fired as one-shots.
	_calls = _bank.get("announcements", [])
	_call_window = float(_bank.get("announcement_window_h", 0.25))
	var loaded := 0
	for name in _bank.get("streams", {}).keys():
		var meta: Dictionary = _bank["streams"][name]
		var s := _load_wav(audio_dir.path_join(String(meta.get("file", ""))))
		if s != null:
			_streams[name] = s
			loaded += 1
	print("ambience: %d/%d streams, %d places, master trim %.2f dB" % [
		loaded, _bank.get("streams", {}).size(), _beds.size(), _master_trim])
	return loaded > 0


func _json(path: String) -> Dictionary:
	if path == "" or not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	return d if d is Dictionary else {}


## Read a 16-bit PCM RIFF file into an AudioStreamWAV, looping the whole of it.
##
## Chunk-walked rather than assumed to start at byte 44: a WAV with a LIST or a
## fact chunk in front of `data` is perfectly legal and would otherwise load as
## noise. `station/audio.py` writes a canonical 44-byte header today; this does
## not depend on that staying true.
func _load_wav(path: String) -> AudioStreamWAV:
	if not FileAccess.file_exists(path):
		push_error("ambience: missing %s" % path)
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	if f.get_buffer(4).get_string_from_ascii() != "RIFF":
		push_error("ambience: %s is not RIFF" % path)
		return null
	f.get_32()
	if f.get_buffer(4).get_string_from_ascii() != "WAVE":
		push_error("ambience: %s is not WAVE" % path)
		return null
	var channels := 1
	var rate := 44100
	var bits := 16
	var pcm := PackedByteArray()
	while f.get_position() + 8 <= f.get_length():
		var tag := f.get_buffer(4).get_string_from_ascii()
		var size := f.get_32()
		var next := f.get_position() + size + (size & 1)
		if tag == "fmt ":
			f.get_16()                      # format code; 1 = PCM
			channels = f.get_16()
			rate = f.get_32()
			f.get_32()                      # byte rate
			f.get_16()                      # block align
			bits = f.get_16()
		elif tag == "data":
			pcm = f.get_buffer(size)
		f.seek(next)
	if pcm.is_empty() or bits != 16:
		push_error("ambience: %s has no 16-bit data" % path)
		return null
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = rate
	s.stereo = channels == 2
	s.data = pcm
	# Loop the entire buffer. Correct only because the buffer is loop-exact --
	# see the header note and `station/audio.seam()`.
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = pcm.size() / (2 * channels)
	return s


# ---------------------------------------------------------------------------
# Binding to a loaded scene
# ---------------------------------------------------------------------------

## Learn where the places are, and hang the point emitters on the objects that
## make the noise. Both read the MESH NAMES, which `rooms.py` already writes as
## `<place>__<group>` with `fix_*` and `prop_*` group names. Nothing here is a
## list of coordinates that could disagree with the geometry.
func bind(visual: Node, body: Node3D) -> int:
	_body = body
	_emitters.clear()
	# The place boxes, including the 1.5 m doorway grow that used to be written
	# out below -- both are `places.gd`'s now, so the HUD and the mixer cannot
	# drift apart again.
	_place_aabb = Places.boxes(visual)
	var rules: Array = _bank.get("emitters", [])
	for m in Places.meshes(visual):
		var n := String(m.name)
		for r in rules:
			var pat := String(r.get("match", ""))
			if pat != "" and n.find(pat) >= 0:
				_add_emitter(m, r)
				break
	print("ambience: bound %d places, %d emitters (cap %d)" % [
		_place_aabb.size(), _emitters.size(),
		int(_bank.get("emitter_cap", 24))])
	return _emitters.size()


func _add_emitter(m: MeshInstance3D, rule: Dictionary) -> void:
	var stream_name := String(rule.get("stream", ""))
	if not _streams.has(stream_name):
		return
	var p := AudioStreamPlayer3D.new()
	p.stream = _streams[stream_name]
	p.unit_size = float(rule.get("range_m", 6.0))
	p.max_distance = p.unit_size * 3.0
	p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
	p.autoplay = false
	add_child(p)
	p.global_position = m.global_transform * m.get_aabb().get_center()
	_emitters.append({
		"node": p,
		# The direct field at 1 m, converted to full scale the same way a bed
		# layer is, plus this stream's own measured RMS trim.
		"db": _emitter_ref + float(rule.get("db", 0.0)) - _ref_dba
			+ _master_trim + _trim(stream_name),
		"pos": p.global_position,
	})


func _trim(stream_name: String) -> float:
	var meta: Dictionary = _bank.get("streams", {}).get(stream_name, {})
	return float(meta.get("level_trim_db", 0.0))


# ---------------------------------------------------------------------------
# Which room am I in
# ---------------------------------------------------------------------------

## The place whose geometry contains the listener, or the corridor.
##
## Deliberately containment and NOT nearest: on a ring deck every room opens off
## one corridor, so "not inside any room" means "in the corridor" rather than
## "near whichever room happens to be closest". `_fallback` is a REAL register
## key (`central_corridor`), not a made-up bed -- the corridor is a location and
## has an entry in `beds.json` like everything else.
func place_at(p: Vector3) -> String:
	var best: String = Places.at(_place_aabb, p)
	if best != "":
		return best
	return _fallback


## Every layer level for a place at an hour, keyed "layer:stream".
func bed_for(place: String, h: float) -> Dictionary:
	var row: Dictionary = _beds.get(place, {})
	if row.is_empty():
		row = _beds.get(_fallback, {})
	var hours: Dictionary = row.get("hours", {})
	if hours.is_empty():
		return {}
	var hi := int(floor(fposmod(h, 24.0)))
	var got = hours.get(str(hi), {})
	return got if got is Dictionary else {}


# ---------------------------------------------------------------------------
# The mix
# ---------------------------------------------------------------------------

func _process(delta: float) -> void:
	if _bank.is_empty():
		return
	if _body != null:
		var now := place_at(_body.global_position)
		if now != _here:
			_here = now
	var target := bed_for(_here if _here != "" else _fallback, hour)
	# Anything not in the target bed fades OUT, which is what makes walking
	# from a bar into a corridor sound like leaving a bar.
	for key in _players.keys():
		if not target.has(key):
			_players[key]["target"] = silence_db - 20.0
	for key in target.keys():
		var parts := String(key).split(":")
		if parts.size() != 2:
			continue
		var stream_name := parts[1]
		if not _streams.has(stream_name):
			continue
		var want := (float(target[key]) - _ref_dba + _master_trim
			+ _trim(stream_name))
		if not _players.has(key):
			# THE FIRST BED DOES NOT FADE IN, and this is a correctness fix
			# rather than a preference. Every layer used to start 20 dB BELOW
			# `silence_db` and approach its level with a 2.5 s time constant, so
			# for the first seconds of any build the station was measurably
			# silent. At this deck's own levels the crowd bed only crosses
			# audibility at 0.84 s, the traffic bed at 1.64 s and the air bed at
			# **2.09 s** -- so anything asking "is the station audible" before
			# then gets a truthful no, and a cold-start gate became a race
			# against a fader. It produced a false red, which costs a reader
			# their trust in every other number the gate prints.
			#
			# There is also nothing to fade FROM at boot. The crossfade exists so
			# that walking out of a bar into a corridor is smooth, and it still
			# does exactly that: `_started` is false only on the first pass, so a
			# bed learned later -- a room you walk into -- still arrives over
			# `crossfade_s`. Snapping on scene entry is what a mixer does.
			var db0 := want if not _started else silence_db - 20.0
			var pl := AudioStreamPlayer.new()
			pl.stream = _streams[stream_name]
			pl.volume_db = db0
			add_child(pl)
			_players[key] = {"node": pl, "db": db0, "target": want}
		_players[key]["target"] = want
	# Approach each target exponentially. In dB, because that is how a fade
	# sounds even: a linear ramp in amplitude spends most of its time inaudible.
	var k := 1.0 - exp(-delta / max(crossfade_s, 0.01))
	for key in _players.keys():
		var st: Dictionary = _players[key]
		st["db"] = lerp(float(st["db"]), float(st["target"]), k)
		var node: AudioStreamPlayer = st["node"]
		node.volume_db = float(st["db"])
		if float(st["db"]) <= silence_db:
			if node.playing:
				node.stop()
		elif not node.playing:
			# START AT A PER-LAYER OFFSET. Two layers can legitimately want the
			# same buffer -- a customs hall's `crowd` and its `traffic` are both
			# `crowd_babble`, because a queue under load is more people -- and
			# two players of one buffer started on the same frame are perfectly
			# coherent, which is one voice at +6 dB rather than two crowds.
			# Deterministic in the key, so a reload sounds the same.
			node.play(fposmod(float(hash(key)) * 0.001,
				max(float(node.stream.get_length()), 0.001)))
	_speak()
	_since_refresh += delta
	if _since_refresh >= emitter_refresh_s:
		_since_refresh = 0.0
		_refresh_emitters()
	# Everything after this frame is a CHANGE rather than an arrival, so it
	# crossfades. Set last, so the first pass through the loop above is the one
	# that snaps.
	_started = true


## Fire the tannoy if a call for this place is due, once per call per pass of
## the clock. The text is carried so a future HUD or subtitle has it -- it is
## `broadcast.py`'s own era-locked line, not a string written here.
func _speak() -> void:
	var here := _here if _here != "" else _fallback
	for i in _calls.size():
		var c: Dictionary = _calls[i]
		if not (c.get("places", []) as Array).has(here):
			continue
		var d: float = abs(fposmod(float(c.get("hour", 0.0)) - hour + 12.0,
			24.0) - 12.0)
		if d > _call_window:
			_fired.erase(i)
			continue
		if _fired.has(i):
			continue
		_fired[i] = true
		if _pa == null:
			_pa = AudioStreamPlayer.new()
			add_child(_pa)
		if not _streams.has("pa_chime"):
			continue
		_pa.stream = _streams["pa_chime"]
		_pa.volume_db = (float(c.get("db", 68.0)) - _ref_dba + _master_trim
			+ _trim("pa_chime"))
		_pa.play()
		_last_call = String(c.get("text", ""))
		return


## Keep only the nearest `emitter_cap` playing. A deck carries hundreds of
## ducts and rails; a mixer does not carry hundreds of voices.
func _refresh_emitters() -> void:
	if _emitters.is_empty() or _body == null:
		return
	var here := _body.global_position
	var order := _emitters.duplicate()
	order.sort_custom(func(a, b):
		return here.distance_squared_to(a["pos"]) \
			< here.distance_squared_to(b["pos"]))
	var cap := int(_bank.get("emitter_cap", 24))
	for i in order.size():
		var node: AudioStreamPlayer3D = order[i]["node"]
		if i < cap:
			node.volume_db = float(order[i]["db"])
			if not node.playing:
				node.play()
		elif node.playing:
			node.stop()


# ---------------------------------------------------------------------------
# Headless verification
# ---------------------------------------------------------------------------

## What is audible here, as one parseable line. There is no way to listen to
## this build, so the only evidence a bed reached the mixer is the mixer saying
## so -- and a `dbfs` that never moves between two places is a defect the ear
## would catch and no other test can.
func describe() -> String:
	var live := []
	for key in _players.keys():
		var db := float(_players[key]["db"])
		if db > silence_db:
			# The EFFECTIVE level, not the fader position. A stream normalised
			# to a lower RMS carries a positive trim, so two layers at the same
			# `volume_db` are not the same loudness -- printing the fader alone
			# made the sparse night crowd look 4 dB LOUDER than the busy
			# afternoon one when it is 13 dB quieter.
			var eff: float = db + float(
				_bank.get("streams", {}).get(String(key).split(":")[1], {})
					.get("rms_dbfs", 0.0))
			live.append("%s %.1f" % [key, eff])
	live.sort()
	var em := 0
	for e in _emitters:
		if (e["node"] as AudioStreamPlayer3D).playing:
			em += 1
	return "AMBIENCE place=%s hour=%05.2f layers=%d emitters=%d pa=%s [%s]" % [
		_here, hour, live.size(), em,
		("\"%s\"" % _last_call.substr(0, 40)) if _last_call != "" else "-",
		", ".join(live)]


## NOTHING HERE SURVIVES A RELOAD, AND NOTHING SHOULD.
## Every layer's level is a pure function of (place, hour, occupancy, berths in
## use) -- `station/audio.py` derives all seven and none of them accumulates.
## Restore the clock and the position and the room sounds identical.
func save_exempt() -> String:
	return "levels are a pure function of place and hour"
