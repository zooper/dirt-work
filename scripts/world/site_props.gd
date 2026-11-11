class_name SiteProps
extends Node3D
## Quarry site dressing in the yard south of the pit: Falu-red site cabin,
## floodlight towers, a crusher plant with conveyors feeding a stockpile,
## barrels and a generator. Solid parts merge into one LowPolyBatch, glowing
## parts (windows, lamps) into one emissive mesh. Simple box/hull collision.

@export var seed_value := 4412

var _rng := RandomNumberGenerator.new()
var _solid := LowPolyBatch.new()
var _glow := LowPolyBatch.new()
var _body: StaticBody3D


func _ready() -> void:
	_rng.seed = seed_value
	_body = StaticBody3D.new()
	_body.name = "Collision"
	add_child(_body)

	_cabin(Vector3(30, 0, 64), PI * 0.1)
	_cabin(Vector3(41, 0, 70), PI * 0.1)
	for p in [Vector3(-14, 0, 46), Vector3(22, 0, 48), Vector3(-34, 0, -30), Vector3(34, 0, -26)]:
		_floodlight(p)
	_crusher_plant(Vector3(-52, 0, 72))
	_yard_clutter(Vector3(22, 0, 60))

	add_child(_solid.to_instance("SiteSolid"))
	var glow := _glow.to_instance("SiteGlow", false)
	var m := LowPolyBatch.material().duplicate() as StandardMaterial3D
	m.emission_enabled = true
	m.emission = Palette.LAMP
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
