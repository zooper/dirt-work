class_name SiteProps
extends Node3D
## Quarry site dressing in the yard south of the pit: Falu-red site cabin,
## floodlight towers, a crusher plant with conveyors feeding a stockpile,
## barrels and a generator. Solid parts merge into one LowPolyBatch, glowing
## parts (windows, lamps) into one emissive mesh. Simple box/hull collision.

@export var seed_value := 4412

## Showcase loading spot in the pit against the north benches (reference
## composition); the Hauler instance in quarry.tscn stands here, facing +X.
const LOADING_BAY := Vector3(4, 0, -28)
const LOADING_BAY_YAW := -PI * 0.5

var _rng := RandomNumberGenerator.new()
var _solid := LowPolyBatch.new()
var _glow := LowPolyBatch.new()
var _body: StaticBody3D


func _ready() -> void:
	_rng.seed = seed_value
	_body = StaticBody3D.new()
	_body.name = "Collision"
	add_child(_body)

	_cabin(Vector3(-40, 0, 88), PI * 0.5)   # by the crusher, behind the loading spot
	_cabin(Vector3(41, 0, 70), PI * 0.1)
	for p in [Vector3(-14, 0, 46), Vector3(22, 0, 48), Vector3(-34, 0, -30), Vector3(34, 0, -26)]:
		_floodlight(p)
	_crusher_plant(Vector3(-52, 0, 72))
	_yard_clutter(Vector3(22, 0, 60))
	_loading_bay(LOADING_BAY, LOADING_BAY_YAW)
	_upper_bench()
	_pit_plant()
	_tyre_tracks()

	add_child(_solid.to_instance("SiteSolid"))
	var glow := _glow.to_instance("SiteGlow", false)
	var m := LowPolyBatch.material().duplicate() as StandardMaterial3D
	m.emission_enabled = true
	m.emission = Palette.render(Palette.LAMP)
	m.emission_energy_multiplier = 1.6
	glow.material_override = m
	add_child(glow)


# --- Builders ---------------------------------------------------------------

func _box(center: Vector3, size: Vector3, color: Color, basis := Basis.IDENTITY, collide := false, glow := false) -> void:
	(_glow if glow else _solid).add_slab(center, size, basis, 0.0, _rng, color)
	if collide:
		_collider(center, size, basis)


func _collider(center: Vector3, size: Vector3, basis := Basis.IDENTITY) -> void:
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	cs.shape = shape
	cs.transform = Transform3D(basis, center)
	_body.add_child(cs)


func _cabin(base: Vector3, yaw: float) -> void:
	var b := Basis(Vector3.UP, yaw)
	var at := func(local: Vector3) -> Vector3: return base + b * local
	var size := Vector3(8.0, 2.9, 3.4)
	_box(at.call(Vector3(0, 0.25, 0)), Vector3(size.x + 0.3, 0.5, size.z + 0.3), Palette.MACHINE_DARK, b, true)
	_box(at.call(Vector3(0, 0.5 + size.y * 0.5, 0)), size, Palette.FALU_RED, b, true)
	# White corner trims and fascia.
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			_box(at.call(Vector3(sx * (size.x * 0.5 + 0.02), 0.5 + size.y * 0.5, sz * (size.z * 0.5 + 0.02))), Vector3(0.18, size.y, 0.18), Palette.TRIM_WHITE, b)
	_box(at.call(Vector3(0, 0.5 + size.y + 0.08, 0)), Vector3(size.x + 0.5, 0.16, size.z + 0.5), Palette.TRIM_WHITE, b)
	# Low gable roof.
	for s in [-1.0, 1.0]:
		var rb := b * Basis(Vector3.RIGHT, s * 0.22)
		_box(at.call(Vector3(0, 0.5 + size.y + 0.45, s * (size.z * 0.25 + 0.05))), Vector3(size.x + 0.6, 0.14, size.z * 0.58), Palette.MACHINE_DARK.darkened(0.2), rb)
	# Warm lit windows (front, -Z side faces the pit) with white frames + door.
	for i in 3:
		var x := -2.6 + i * 2.2
		_box(at.call(Vector3(x, 2.0, -size.z * 0.5 - 0.03)), Vector3(1.4, 0.9, 0.05), Palette.LAMP, b, false, true)
		_box(at.call(Vector3(x, 2.0, -size.z * 0.5 - 0.05)), Vector3(1.6, 0.12, 0.06), Palette.TRIM_WHITE, b)
		_box(at.call(Vector3(x, 1.5, -size.z * 0.5 - 0.06)), Vector3(1.6, 0.1, 0.12), Palette.TRIM_WHITE, b)
	_box(at.call(Vector3(3.3, 1.5, -size.z * 0.5 - 0.04)), Vector3(0.95, 2.0, 0.06), Palette.TRIM_WHITE, b)
	_box(at.call(Vector3(3.3, 0.6, -size.z * 0.5 - 0.6)), Vector3(1.4, 0.2, 1.0), Palette.MACHINE_STEEL, b)  # step


func _floodlight(base: Vector3) -> void:
	var h := 11.0
	_box(base + Vector3(0, 0.3, 0), Vector3(1.2, 0.6, 1.2), Palette.MACHINE_STEEL, Basis.IDENTITY, true)
	_box(base + Vector3(0, h * 0.5, 0), Vector3(0.28, h, 0.28), Palette.MACHINE_STEEL.lightened(0.15), Basis.IDENTITY, true)
	var face := Basis(Vector3.UP, atan2(base.x, base.z) + PI)  # aim towards pit centre
	_box(base + Vector3(0, h + 0.2, 0), Vector3(2.4, 0.15, 0.25), Palette.MACHINE_DARK, face)
	for i in 2:
		for j in 2:
			var local := Vector3(-0.6 + i * 1.2, h + 0.75 + j * 0.85, -0.12)
			_box(base + face * local, Vector3(1.0, 0.7, 0.3), Palette.MACHINE_DARK, face)
			_box(base + face * (local + Vector3(0, 0, -0.17)), Vector3(0.85, 0.55, 0.05), Palette.LAMP, face, false, true)


func _crusher_plant(base: Vector3) -> void:
	# Crusher tower: lattice legs, housing, platform with yellow rails, hopper.
	var top := 7.0
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			_box(base + Vector3(sx * 2.5, top * 0.5, sz * 2.5), Vector3(0.35, top, 0.35), Palette.MACHINE_STEEL, Basis.IDENTITY, true)
	for k in 3:
		var y := 1.5 + k * 2.0
		for s in [-1.0, 1.0]:
			_box(base + Vector3(0, y, s * 2.5), Vector3(5.0, 0.18, 0.18), Palette.MACHINE_STEEL)
			_box(base + Vector3(s * 2.5, y, 0), Vector3(0.18, 0.18, 5.0), Palette.MACHINE_STEEL)
			_box(base + Vector3(0, y + 1.0, s * 2.5), Vector3(0.12, 2.6, 0.12), Palette.MACHINE_STEEL, Basis(Vector3.BACK, s * 0.78))
	_box(base + Vector3(0, top + 1.4, 0), Vector3(5.6, 2.8, 5.6), Palette.MACHINE_DARK.lightened(0.1))
	_box(base + Vector3(0, top + 2.95, 0), Vector3(6.4, 0.2, 6.4), Palette.MACHINE_STEEL)
	_rails(base + Vector3(0, top + 3.05, 0), 6.4, 6.4)
	# Hopper (inverted frustum approximated with a hull).
	var hp := PackedVector3Array()
	for v in [Vector3(-1.2, 0, -1.2), Vector3(1.2, 0, -1.2), Vector3(1.2, 0, 1.2), Vector3(-1.2, 0, 1.2)]:
		hp.append(base + Vector3(0, top + 3.05, 0) + v)
	for v in [Vector3(-2.4, 2.0, -2.4), Vector3(2.4, 2.0, -2.4), Vector3(2.4, 2.0, 2.4), Vector3(-2.4, 2.0, 2.4)]:
		hp.append(base + Vector3(0, top + 3.05, 0) + v)
	_solid.add_hull(hp, Palette.MACHINE_YELLOW)
	# Conveyors: feed from the pit side, discharge onto a stockpile.
	_conveyor(base + Vector3(16, 0.8, -16), base + Vector3(2.0, top + 4.6, -1.5))
	var stock := base + Vector3(24, 0, 10)
	_conveyor(base + Vector3(2.6, top - 0.5, 1.5), stock + Vector3(0, 10.5, 0))
	var hull := _solid.add_mound(stock, 8.0, 5.2, 14, 4, _rng,
		func(c, _n): return Palette.GRAVEL_PILE_WARM.lerp(Palette.ROCK_COOL, c.y / 12.0).lightened(_rng.randf_range(-0.06, 0.06)))
	var cs := CollisionShape3D.new()
	var shape := ConvexPolygonShape3D.new()
	shape.points = hull
	cs.shape = shape
	_body.add_child(cs)


func _conveyor(from: Vector3, to: Vector3) -> void:
	var d := to - from
	var length := d.length()
	var dir := d / length
	var yaw := atan2(-dir.x, -dir.z)
	var pitch := asin(dir.y)
	var b := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, pitch)  # local -Z along belt
	var mid := (from + to) * 0.5
	_box(mid, Vector3(1.4, 0.12, length), Palette.MACHINE_DARK.darkened(0.3), b)           # belt
	for s in [-1.0, 1.0]:
		_box(mid + b * Vector3(s * 0.8, -0.25, 0), Vector3(0.12, 0.5, length), Palette.MACHINE_YELLOW, b)  # truss sides
		_box(mid + b * Vector3(s * 1.25, 0.55, 0), Vector3(0.05, 0.05, length), Palette.MACHINE_YELLOW, b)  # walkway rail
	_box(mid + b * Vector3(1.05, -0.05, 0), Vector3(0.6, 0.06, length), Palette.MACHINE_STEEL, b)          # walkway
	var n := int(length / 1.8)
	for i in n:
		var t := (i + 0.5) / n
		var p := from + d * t
		_box(p + b * Vector3(0, -0.45, 0), Vector3(1.6, 0.08, 0.1), Palette.MACHINE_YELLOW, b)
		_box(p + b * Vector3(1.25, 0.3, 0), Vector3(0.05, 0.5, 0.05), Palette.MACHINE_YELLOW, b)
	# Support trestles every ~9 m.
	var legs := maxi(int(length / 9.0), 1)
	for i in legs:
		var t := (i + 0.6) / (legs + 0.2)
		var p := from + d * t
		if p.y < 1.6:
			continue
		var h := p.y - 0.4
		for s in [-1.0, 1.0]:
			var foot := p + Basis(Vector3.UP, yaw) * Vector3(s * 0.9, 0, 0)
			_box(Vector3(foot.x, h * 0.5, foot.z), Vector3(0.22, h, 0.22), Palette.MACHINE_STEEL, Basis(Vector3.UP, yaw), true)
		var k := 0.0
		while k + 1.6 < h:
			_box(Vector3(p.x, k + 0.8, p.z), Vector3(0.08, 2.0, 0.08), Palette.MACHINE_STEEL, Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, 0.75 if int(k) % 2 == 0 else -0.75))
			k += 1.6


## Dressing around the hauler loading spot (the reference showcase): a chunky
## angular rock stockpile, big boulders, a lone pine and a floodlight.
func _loading_bay(hauler: Vector3, yaw: float) -> void:
	var r := Basis(Vector3.UP, yaw)   # offsets below are in hauler-local space
	# Cobble stockpile (east of the hauler's nose): big angular stones heaped up.
	var c := hauler + r * Vector3(7.5, 0, -3.5)
	var hull := PackedVector3Array()
	for i in 90:
		var a := _rng.randf() * TAU
		var d := sqrt(_rng.randf()) * 3.6
		var h := maxf(2.0 * (1.0 - d / 3.8), 0.0)
		var p := c + Vector3(cos(a) * d, h * _rng.randf_range(0.7, 1.0), sin(a) * d)
		_solid.add_rock(p, _rng.randf_range(0.32, 0.62), _rng, Palette.GRAVEL_PILE_WARM.lerp(Palette.ROCK_COOL, _rng.randf() * 0.6).darkened(_rng.randf_range(0.0, 0.18)), 0.8)
	for k in 10:
		var a := TAU * k / 10.0
		hull.append(c + Vector3(cos(a) * 3.8, 0, sin(a) * 3.8))
	hull.append(c + Vector3(0, 1.9, 0))
	var cs := CollisionShape3D.new()
	var shape := ConvexPolygonShape3D.new()
	shape.points = hull
	cs.shape = shape
	_body.add_child(cs)
	# Big boulders by the bay entrance.
	for off in [Vector3(13.5, 0, 4.0), Vector3(15.0, 0, 6.5), Vector3(12.0, 0, 8.0)]:
		var size := _rng.randf_range(0.9, 1.6)
		var pts := _solid.add_rock(hauler + r * off + Vector3.UP * size * 0.45, size, _rng, Palette.ROCK_COOL.darkened(0.2), 0.75)
		var bcs := CollisionShape3D.new()
		var bs := ConvexPolygonShape3D.new()
		bs.points = pts
		bcs.shape = bs
		_body.add_child(bcs)
	# A lone pine at the bay edge, and a floodlight among the site buildings.
	var pine := MeshInstance3D.new()
	pine.mesh = QuarryWorld.build_pine_mesh(_rng)
	pine.position = hauler + r * Vector3(15.6, 0, 9.4)
	pine.scale = Vector3.ONE * 1.6
	add_child(pine)
	_collider(pine.position + Vector3(0, 2.0, 0), Vector3(0.6, 4.0, 0.6))
	_floodlight(hauler + r * Vector3(-10.0, 0, 16.0))


## In-pit feed line behind the loading bay (reference: conveyors climbing the
## benches at the back left): a feeder hopper by the west pile, a conveyor up
## over the first bench to a transfer tower, and the red site cabin in front.
func _pit_plant() -> void:
	var feeder := Vector3(-30, 0, -33)
	_box(feeder + Vector3(0, 1.2, 0), Vector3(3.2, 2.4, 3.2), Palette.MACHINE_DARK.lightened(0.1), Basis.IDENTITY, true)
	var hp := PackedVector3Array()
	for v in [Vector3(-1.4, 2.4, -1.4), Vector3(1.4, 2.4, -1.4), Vector3(1.4, 2.4, 1.4), Vector3(-1.4, 2.4, 1.4),
			Vector3(-2.4, 4.0, -2.4), Vector3(2.4, 4.0, -2.4), Vector3(2.4, 4.0, 2.4), Vector3(-2.4, 4.0, 2.4)]:
		hp.append(feeder + v)
	_solid.add_hull(hp, Palette.MACHINE_YELLOW)
	_rails(feeder + Vector3(0, 4.0, 0), 4.8, 4.8)
	var tower := Vector3(-8, 7.0, -45)
	_conveyor(feeder + Vector3(1.5, 1.6, -1.0), tower + Vector3(0, 5.2, 0))
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			_box(tower + Vector3(sx * 1.6, 2.2, sz * 1.6), Vector3(0.25, 4.4, 0.25), Palette.MACHINE_STEEL)
	_box(tower + Vector3(0, 5.2, 0), Vector3(3.6, 1.8, 3.6), Palette.MACHINE_DARK.lightened(0.1))
	_box(tower + Vector3(0, 6.2, 0), Vector3(4.2, 0.15, 4.2), Palette.MACHINE_STEEL)
	_rails(tower + Vector3(0, 6.25, 0), 4.2, 4.2)
	_conveyor(tower + Vector3(1.5, 4.6, 0.5), tower + Vector3(14.0, 1.0, 1.5))   # out along the bench
	_cabin(Vector3(-19, 0, -13), -0.42)
	_floodlight(Vector3(-22, 0, -18))


## Packed, darker wheel ruts on the pit floor: the loader's approach to the
## hauler and the hauler's own path in (reference: tracks across the floor).
func _tyre_tracks() -> void:
	var loader_path := [Vector3(-2.2, 0, -25.2), Vector3(-5.0, 0, -18.0), Vector3(-7.0, 0, -9.0), Vector3(-4.0, 0, 1.0), Vector3(0.0, 0, 10.0)]
	_track_pair(loader_path, 2.76, 0.95)
	var hauler_path := [Vector3(-3.0, 0, -28.0), Vector3(-11.0, 0, -26.5), Vector3(-15.5, 0, -19.0), Vector3(-15.0, 0, -6.0)]
	_track_pair(hauler_path, 2.6, 0.8)
	_track_pair([Vector3(11.0, 0, -28.0), Vector3(16.0, 0, -27.0), Vector3(20.0, 0, -18.0), Vector3(20.0, 0, -11.0)], 2.6, 0.8)


func _track_pair(path: Array, track: float, width: float) -> void:
	# Densely sample a Catmull-Rom spline through `path`, then lay two ribbons.
	var pts: Array[Vector3] = []
	for i in path.size() - 1:
		var p0: Vector3 = path[maxi(i - 1, 0)]
		var p1: Vector3 = path[i]
		var p2: Vector3 = path[i + 1]
		var p3: Vector3 = path[mini(i + 2, path.size() - 1)]
		var n := int(ceil(p1.distance_to(p2) / 0.5))
		for k in n:
			var t := float(k) / n
			pts.append(0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t * t * t))
	pts.append(path[path.size() - 1])
	var base := Palette.GRAVEL_FLOOR.darkened(0.2)
	var lug := Palette.GRAVEL_FLOOR.darkened(0.3)
	for side in [-1.0, 1.0]:
		for i in pts.size() - 1:
			var a := pts[i]
			var b := pts[i + 1]
			var dir := (b - a).normalized()
			var rt := Vector3(-dir.z, 0, dir.x)
			var o: Vector3 = rt * float(side) * track * 0.5
			var y := Vector3.UP * 0.025
			var fade := clampf(minf(float(i), float(pts.size() - 2 - i)) / 6.0, 0.0, 1.0)   # soft ends
			var col := (lug if i % 2 == 0 else base).lerp(Palette.GRAVEL_FLOOR, 1.0 - fade)
			_solid.add_quad_facing(a + o - rt * width * 0.5 + y, a + o + rt * width * 0.5 + y,
				b + o + rt * width * 0.5 + y, b + o - rt * width * 0.5 + y, Vector3.UP, col)


## Working face on the second bench (y = 14) above the loading bay: the
## BenchExcavator (quarry.tscn) digs this blasted-rock heap and loads BenchHauler.
func _upper_bench() -> void:
	var c := Vector3(6.5, 14.0, -55.5)
	var rng := _rng
	_solid.add_mound(c, 3.6, 2.3, 12, 3, _rng,
		func(p, n): return LowPolyBatch._shade(Palette.GRAVEL_PILE.lerp(Palette.ROCK_COOL, rng.randf() * 0.4), n, rng))
	for i in 26:
		var a := _rng.randf() * TAU
		var d := _rng.randf_range(2.6, 4.4)
		_solid.add_rock(c + Vector3(cos(a) * d, 0.2, sin(a) * d), _rng.randf_range(0.25, 0.55), _rng,
			Palette.GRAVEL_PILE.lerp(Palette.ROCK_COOL, _rng.randf()).darkened(0.25), 0.8)


func _rails(center: Vector3, sx: float, sz: float) -> void:
	for s in [-1.0, 1.0]:
		_box(center + Vector3(0, 1.0, s * sz * 0.5), Vector3(sx, 0.07, 0.07), Palette.MACHINE_YELLOW)
		_box(center + Vector3(s * sx * 0.5, 1.0, 0), Vector3(0.07, 0.07, sz), Palette.MACHINE_YELLOW)
		_box(center + Vector3(0, 0.5, s * sz * 0.5), Vector3(sx, 0.05, 0.05), Palette.MACHINE_YELLOW)
		_box(center + Vector3(s * sx * 0.5, 0.5, 0), Vector3(0.05, 0.05, sz), Palette.MACHINE_YELLOW)
		for i in 5:
			var t := -0.5 + i / 4.0
			_box(center + Vector3(t * sx, 0.5, s * sz * 0.5), Vector3(0.07, 1.0, 0.07), Palette.MACHINE_YELLOW)
			_box(center + Vector3(s * sx * 0.5, 0.5, t * sz), Vector3(0.07, 1.0, 0.07), Palette.MACHINE_YELLOW)


func _yard_clutter(base: Vector3) -> void:
	var colors := [Color(0.1, 0.55, 0.6), Color(0.15, 0.35, 0.7), Palette.RAIL_RED, Color(0.2, 0.55, 0.3)]
	for i in 7:
		var p := base + Vector3(i % 4 * 0.75, 0, int(i / 4) * 0.75)
		var col: Color = colors[_rng.randi() % colors.size()]
		var hull := PackedVector3Array()
		for k in 8:
			var a := TAU * k / 8.0
			hull.append(p + Vector3(cos(a) * 0.32, 0, sin(a) * 0.32))
			hull.append(p + Vector3(cos(a) * 0.32, 0.9, sin(a) * 0.32))
		_solid.add_hull(hull, col)
		_collider(p + Vector3(0, 0.45, 0), Vector3(0.6, 0.9, 0.6))
	# Generator + fuel tank.
	_box(base + Vector3(-3.5, 0.75, 0.5), Vector3(2.4, 1.5, 1.2), Color(0.92, 0.92, 0.9), Basis.IDENTITY, true)
	_box(base + Vector3(-3.5, 1.0, -0.12), Vector3(1.6, 0.6, 0.04), Palette.MACHINE_DARK)
	_box(base + Vector3(-7.0, 0.9, 0.5), Vector3(3.2, 1.6, 1.6), Palette.MACHINE_YELLOW, Basis.IDENTITY, true)
