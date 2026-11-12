class_name QuarryWorld
extends Node3D
## Deterministic stylised low-poly quarry. Generated from primitives with a fixed
## seed (identical every run, no external assets). Static scenery is merged into
## a handful of vertex-coloured LowPolyBatch meshes; trees and rubble use
## MultiMesh. Collision uses simple boxes and convex hulls only.
##
## Layout (metres, -Z = north): pit floor x/z in [-40, 40], benches step up to
## the N/W/E, the pit opens south onto the site yard (z 40..100), beyond that a
## lake, forested hills and snow-capped mountains.

@export var seed_value := 7319

const PIT_HALF := 40.0
## [inner distance from centre, top height] per bench; the last is the plateau.
const TIERS := [[40.0, 7.0], [50.0, 14.0], [60.0, 20.0]]
const PLATEAU_OUTER := 170.0
const YARD_SOUTH := 100.0
const RAMP_X := 20.0

var _rng := RandomNumberGenerator.new()
var _collision: StaticBody3D
## Pile centres/radii for future volume accounting (M2) and for decoration.
var piles: Array[Dictionary] = []


func _ready() -> void:
	_rng.seed = seed_value
	_collision = StaticBody3D.new()
	_collision.name = "Collision"
	add_child(_collision)

	var ground := LowPolyBatch.new()
	var cliffs := LowPolyBatch.new()
	var props := LowPolyBatch.new()
	var far := LowPolyBatch.new()

	_build_ground(ground)
	_build_benches(ground, cliffs)
	_build_ramp(ground, cliffs)
	_build_piles(props)
	_build_rocks(props)
	_build_lake_and_hills(far)
	_build_mountains(far)
	_build_bounds()

	var ground_mi := ground.to_instance("Ground")
	ground_mi.material_override = _grain_material(0.55, 0.78, 3.0)
	add_child(ground_mi)
	var cliffs_mi := cliffs.to_instance("Cliffs")
	cliffs_mi.material_override = _grain_material(0.18, 0.82, 5.0)
	add_child(cliffs_mi)
	add_child(props.to_instance("Piles"))
	add_child(far.to_instance("Backdrop", false))
	add_child(_build_clouds().to_instance("Clouds", false))
	_build_forest()
	_build_rubble()
	_build_pebbles()


# --- Ground -----------------------------------------------------------------

func _build_ground(b: LowPolyBatch) -> void:
	# One flat collider at y=0 everywhere avoids seams that snag the loader.
	_add_box_shape(Vector3(1200, 1, 1200), Vector3(0, -0.5, 0))
	# Grass base far below the gravel so they never z-fight.
	var g := 700.0
	b.add_quad(Vector3(-g, -0.06, g), Vector3(g, -0.06, g), Vector3(g, -0.06, -g), Vector3(-g, -0.06, -g), Palette.GRASS)
	# Faceted gravel floor for pit + yard: a jittered-colour triangle grid.
	var cell := 10.0
	var x0 := -PIT_HALF - 0.0
	var x1 := PIT_HALF
	var z0 := -PIT_HALF
	var z1 := YARD_SOUTH
	var x := x0
	while x < x1 - 0.01:
		var z := z0
		while z < z1 - 0.01:
			var wx := minf(cell, x1 - x)
			var wz := minf(cell, z1 - z)
			var a := Vector3(x, 0.01, z + wz)
			var bb := Vector3(x + wx, 0.01, z + wz)
			var c := Vector3(x + wx, 0.01, z)
			var d := Vector3(x, 0.01, z)
			var yard := z > PIT_HALF
			var base := Palette.GRAVEL_FLOOR.lerp(Palette.GRASS_DARK, 0.15) if yard else Palette.GRAVEL_FLOOR
			b.add_tri(a, bb, c, _tint(base, 0.025))
			b.add_tri(a, c, d, _tint(base, 0.025))
			z += cell
		x += cell
	# Yard extends beyond the pit width to the east and west.
	for side in [-1.0, 1.0]:
		var xa: float = side * PIT_HALF
		var xb: float = side * 75.0
		b.add_quad(Vector3(minf(xa, xb), 0.008, YARD_SOUTH), Vector3(maxf(xa, xb), 0.008, YARD_SOUTH),
			Vector3(maxf(xa, xb), 0.008, PIT_HALF + 16.0), Vector3(minf(xa, xb), 0.008, PIT_HALF + 16.0),
			Palette.GRAVEL_FLOOR.lerp(Palette.GRASS, 0.35))


# --- Benches / cliffs -------------------------------------------------------

func _build_benches(ground: LowPolyBatch, cliffs: LowPolyBatch) -> void:
	for i in TIERS.size():
		var inner: float = TIERS[i][0]
		var top: float = TIERS[i][1]
		var bottom: float = 0.0 if i == 0 else TIERS[i - 1][1]
		var outer: float = PLATEAU_OUTER if i == TIERS.size() - 1 else TIERS[i + 1][0]
		var depth := outer - inner
		var south_end := PIT_HALF
		# Collision: north block + west/east blocks.
		_add_box_shape(Vector3(outer * 2.0, top, depth), Vector3(0, top * 0.5, -inner - depth * 0.5))
		var len_we := south_end + outer
		var zc := (south_end - outer) * 0.5
		_add_box_shape(Vector3(depth, top, len_we), Vector3(-inner - depth * 0.5, top * 0.5, zc))
		_add_box_shape(Vector3(depth, top, len_we), Vector3(inner + depth * 0.5, top * 0.5, zc))
		# Bench tops.
		var top_col := Palette.GRASS if i == TIERS.size() - 1 else Palette.GRAVEL_FLOOR.darkened(0.06)
		var y := top + 0.01
		ground.add_quad(Vector3(-outer, y, -inner), Vector3(outer, y, -inner), Vector3(outer, y, -outer), Vector3(-outer, y, -outer), top_col)
		for s in [-1.0, 1.0]:
			var xa: float = s * inner
			var xb: float = s * outer
			ground.add_quad(Vector3(minf(xa, xb), y, south_end), Vector3(maxf(xa, xb), y, south_end),
				Vector3(maxf(xa, xb), y, -inner), Vector3(minf(xa, xb), y, -inner), top_col)
		# Cliff faces: north, west, east, plus the exposed south ends.
		var h := top - bottom
		_slab_face(cliffs, Vector3(-inner, bottom, -inner), Vector3.RIGHT, Vector3.BACK, inner * 2.0, h)
		_slab_face(cliffs, Vector3(-inner, bottom, south_end), Vector3.FORWARD, Vector3.RIGHT, south_end + inner, h)
		_slab_face(cliffs, Vector3(inner, bottom, -inner), Vector3.BACK, Vector3.LEFT, south_end + inner, h)
		_slab_face(cliffs, Vector3(-outer, 0.0, south_end), Vector3.RIGHT, Vector3.BACK, depth, top)
		_slab_face(cliffs, Vector3(inner, 0.0, south_end), Vector3.RIGHT, Vector3.BACK, depth, top)


## Builds one continuous rock face: a jittered grid pushed back into the rock
## by stretched cellular (Voronoi) noise, so the face breaks into tall angular
## blocks and fracture planes. `along` runs along the face, `out_dir` points
## out of the rock. The face meets the bench top flush (no recess at the top).
func _slab_face(b: LowPolyBatch, start: Vector3, along: Vector3, out_dir: Vector3, length: float, height: float) -> void:
	var cell := FastNoiseLite.new()
	cell.seed = _rng.randi()
	cell.noise_type = FastNoiseLite.TYPE_CELLULAR
	cell.cellular_return_type = FastNoiseLite.RETURN_CELL_VALUE
	cell.cellular_jitter = 1.0
	cell.frequency = 1.0
	var fbm := FastNoiseLite.new()
	fbm.seed = _rng.randi()
	fbm.frequency = 0.22
	var step_u := 2.4
	var step_v := 1.6
	var nu := maxi(int(ceil(length / step_u)), 1)
	var nv := maxi(int(ceil(height / step_v)), 1)
	var pts := []
	var cells := []
	for j in nv + 1:
		var row := []
		var crow := []
		for i in nu + 1:
			var u := length * i / nu
			var v := height * j / nv
			if i > 0 and i < nu:
				u += _rng.randf_range(-0.35, 0.35) * step_u
			if j > 0 and j < nv:
				v += _rng.randf_range(-0.3, 0.3) * step_v
			var c := cell.get_noise_2d(u * 0.055, v * 0.022)   # tall cells = rock columns
			var depth := (c * 0.5 + 0.5) * 3.0 + fbm.get_noise_2d(u, v * 1.6) * 0.15
			var top_fade := clampf((height - v) / 1.0, 0.0, 1.0)
			var bottom := clampf((v + 0.3) / 1.5, 0.35, 1.0)
			var ends := clampf(minf(u, length - u) / 2.0, 0.0, 1.0)  # pinned where faces meet
			row.append(start + along * u + Vector3.UP * v - out_dir * depth * top_fade * bottom * ends)
			crow.append(c)
		pts.append(row)
		cells.append(crow)
	for j in nv:
		for i in nu:
			var a: Vector3 = pts[j][i]
			var bb: Vector3 = pts[j][i + 1]
			var c: Vector3 = pts[j + 1][i + 1]
			var d: Vector3 = pts[j + 1][i]
			var cv: float = (cells[j][i] + cells[j][i + 1] + cells[j + 1][i] + cells[j + 1][i + 1]) * 0.25
			var tone := Palette.ROCK_COOL.lerp(Palette.ROCK_WARM, clampf(cv * 0.5 + 0.5, 0.0, 1.0))
			if (i + j) % 2 == 0:
				_rock_tri(b, a, bb, c, out_dir, tone)
				_rock_tri(b, a, c, d, out_dir, tone)
			else:
				_rock_tri(b, a, bb, d, out_dir, tone)
				_rock_tri(b, bb, c, d, out_dir, tone)


func _rock_tri(b: LowPolyBatch, a: Vector3, bb: Vector3, c: Vector3, out_dir: Vector3, tone: Color) -> void:
	var n := (bb - a).cross(c - a).normalized()
	if n.dot(out_dir) < 0.0:
		n = -n
	# Up-facing ledges catch light/dust; overhangs and side planes go darker.
	var col := tone.lightened(0.12 * maxf(n.y, 0.0)).darkened(0.18 * maxf(-n.y, 0.0) + 0.1 * (1.0 - absf(n.dot(out_dir))))
	b.add_tri_facing(a, bb, c, out_dir, col)


func _build_ramp(ground: LowPolyBatch, cliffs: LowPolyBatch) -> void:
	var inner: float = TIERS[0][0]
	var height: float = TIERS[0][1]
	var hw := 4.0
	var length := 28.0
	var z0 := -inner + length
	var z1 := -inner
	var pts := PackedVector3Array([
		Vector3(RAMP_X - hw, 0, z0), Vector3(RAMP_X + hw, 0, z0),
		Vector3(RAMP_X - hw, 0, z1), Vector3(RAMP_X + hw, 0, z1),
		Vector3(RAMP_X - hw, height, z1), Vector3(RAMP_X + hw, height, z1),
	])
	_add_convex_shape(pts)
	var surf := Palette.GRAVEL_FLOOR.darkened(0.04)
	ground.add_quad(pts[0] + Vector3.UP * 0.02, pts[1] + Vector3.UP * 0.02, pts[5] + Vector3.UP * 0.02, pts[4] + Vector3.UP * 0.02, surf)
	var side := Palette.ROCK_WARM.darkened(0.1)
	cliffs.add_tri(pts[0], pts[4], pts[2], side)
	cliffs.add_tri(pts[1], pts[3], pts[5], side)
	# Berm stones along the ramp edges.
	for i in 7:
		var t := (i + 0.5) / 7.0
		for sgn in [-1.0, 1.0]:
			var p := Vector3(RAMP_X + sgn * (hw - 0.4), height * (1.0 - t) + 0.25, lerpf(z1, z0, t))
			cliffs.add_rock(p, _rng.randf_range(0.35, 0.55), _rng, Palette.ROCK)


# --- Piles, rocks, rubble ---------------------------------------------------

func _build_piles(b: LowPolyBatch) -> void:
	var spots := [Vector3(-22, 0, -22), Vector3(-6, 0, -30), Vector3(-27, 0, -2), Vector3(26, 0, 4)]
	for p in spots:
		var r := _rng.randf_range(8.5, 11.0)
		var h := r * _rng.randf_range(0.6, 0.7)
		var base := Palette.GRAVEL_PILE if _rng.randf() < 0.6 else Palette.GRAVEL_PILE_WARM
		var rng := _rng
		var hull := b.add_mound(p, r, h, 14, 4, _rng,
			func(c, n): return LowPolyBatch._shade(base.lerp(Palette.ROCK_COOL, clampf(c.y / h, 0.0, 1.0) * 0.25), n, rng))
		_add_convex_shape(hull)
		piles.append({"center": p, "radius": r, "height": h})


func _build_rocks(b: LowPolyBatch) -> void:
	# Own RNG stream: changes to other generators must not move obstacles around.
	var saved := _rng
	_rng = RandomNumberGenerator.new()
	_rng.seed = seed_value + 101
	# Boulders scattered on the pit floor, keeping the central driving area
	# (spawn + test manoeuvres) and the ramp approach clear.
	for i in 18:
		var p := Vector3(_rng.randf_range(-PIT_HALF + 4, PIT_HALF - 4), 0, _rng.randf_range(-PIT_HALF + 4, PIT_HALF - 2))
		if (absf(p.x) < 16.0 and p.z > -16.0 and p.z < 24.0) or (absf(p.x - RAMP_X) < 8.0 and p.z < -18.0):
			continue
		if _near_pile(p, 2.0):
			continue
		var s := _rng.randf_range(0.6, 1.5)
		_add_convex_shape(b.add_rock(p + Vector3.UP * s * 0.3, s, _rng, Palette.ROCK))
	# Big talus blocks at the cliff foot.
	for i in 22:
		var side := _rng.randi() % 3
		var along := _rng.randf_range(-PIT_HALF + 3, PIT_HALF - 3)
		var p: Vector3
		match side:
			0: p = Vector3(along, 0.6, -PIT_HALF + 2.0)
			1: p = Vector3(-PIT_HALF + 2.0, 0.6, along)
			_: p = Vector3(PIT_HALF - 2.0, 0.6, along)
		if absf(p.x - RAMP_X) < 7.0 and side == 0:
			continue
		var tone := [Palette.ROCK, Palette.ROCK_WARM, Palette.ROCK_COOL][_rng.randi() % 3] as Color
		_add_convex_shape(b.add_rock(p, _rng.randf_range(1.2, 2.4), _rng, tone))
	_rng = saved


func _near_pile(p: Vector3, margin: float) -> bool:
	for pile in piles:
		if Vector2(p.x - pile.center.x, p.z - pile.center.z).length() < pile.radius + margin:
			return true
	return false


## Decorative chunks on and around piles (no collision; MultiMesh = 1 draw call).
func _build_rubble() -> void:
	var chunk := LowPolyBatch.new()
	chunk.add_rock(Vector3.ZERO, 0.5, _rng, Color.WHITE, 0.8)
	var xforms: Array[Transform3D] = []
	var colors: Array[Color] = []
	for pile in piles:
		var r: float = pile.radius
		var h: float = pile.height
		for i in 220:
			var a := _rng.randf() * TAU
			var d := sqrt(_rng.randf()) * r * 1.15
			var y := maxf(h * (1.0 - d / r), 0.0) * 0.92
			var pos: Vector3 = pile.center + Vector3(cos(a) * d, y, sin(a) * d)
			var s := _rng.randf_range(0.35, 1.0) * (1.0 if d < r else 0.6)
			xforms.append(Transform3D(Basis.from_euler(Vector3(_rng.randf() * TAU, _rng.randf() * TAU, 0)).scaled(Vector3.ONE * s), pos))
			colors.append(Palette.GRAVEL_PILE.lerp(Palette.ROCK_WARM, _rng.randf()).lightened(_rng.randf_range(-0.1, 0.12)))
	add_child(_multimesh("Rubble", chunk.commit(), xforms, colors, true))


## Gravel texture: small stones scattered over the pit floor and yard.
func _build_pebbles() -> void:
	var chunk := LowPolyBatch.new()
	chunk.add_rock(Vector3.ZERO, 0.5, _rng, Color.WHITE, 0.6)
	var xforms: Array[Transform3D] = []
	var colors: Array[Color] = []
	for i in 2600:
		var p := Vector3(_rng.randf_range(-PIT_HALF + 1, PIT_HALF - 1), 0.0, _rng.randf_range(-PIT_HALF + 1, YARD_SOUTH - 2))
		var s := _rng.randf_range(0.12, 0.4) if _rng.randf() < 0.85 else _rng.randf_range(0.45, 0.8)
		xforms.append(Transform3D(Basis.from_euler(Vector3(0, _rng.randf() * TAU, 0)).scaled(Vector3(s, s, s)), p))
		colors.append(Palette.GRAVEL_PILE.lerp(Palette.GRAVEL_FLOOR, _rng.randf()).darkened(_rng.randf_range(0.0, 0.2)))
	add_child(_multimesh("Pebbles", chunk.commit(), xforms, colors, false))


# --- Forest, backdrop, sky --------------------------------------------------

static func build_pine_mesh(rng: RandomNumberGenerator) -> ArrayMesh:
	var b := LowPolyBatch.new()
	var seg := 6
	for i in seg:  # trunk
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		var r := 0.22
		b.add_quad(Vector3(cos(a0) * r, 0, sin(a0) * r), Vector3(cos(a1) * r, 0, sin(a1) * r),
			Vector3(cos(a1) * r * 0.8, 2.0, sin(a1) * r * 0.8), Vector3(cos(a0) * r * 0.8, 2.0, sin(a0) * r * 0.8), Palette.TRUNK)
	for k in 4:  # foliage tiers
		var base_y := 1.4 + k * 1.35
		var r := 1.9 - k * 0.42
		var h := 2.4 - k * 0.25
		var apex := Vector3(0, base_y + h, 0)
		var col := Palette.PINE.lerp(Palette.PINE_LIGHT, k / 4.0)
		var offs := rng.randf() * TAU
		var ring := []
		for i in 7:
			var a := TAU * i / 7.0 + offs
			ring.append(Vector3(cos(a) * r, base_y + rng.randf_range(-0.15, 0.1), sin(a) * r))
		for i in 7:
			var p0: Vector3 = ring[i]
			var p1: Vector3 = ring[(i + 1) % 7]
			b.add_tri(p0, apex, p1, col.lightened(0.08) if i % 2 == 0 else col)
			b.add_tri(p1, Vector3(0, base_y + 0.3, 0), p0, col.darkened(0.3))  # underside
	return b.commit()


func _build_forest() -> void:
	var mesh := build_pine_mesh(_rng)
	var xforms: Array[Transform3D] = []
	var colors: Array[Color] = []
	var plateau_y: float = TIERS[-1][1]
	var plateau_in: float = TIERS[-1][0] + 2.0
	# Plateau forest behind the benches (N, W, E).
	for i in 900:
		var p := Vector3(_rng.randf_range(-PLATEAU_OUTER + 10, PLATEAU_OUTER - 10), plateau_y, _rng.randf_range(-PLATEAU_OUTER + 10, PIT_HALF - 2))
		if absf(p.x) < plateau_in and p.z > -plateau_in:
			continue
		if absf(p.x) < plateau_in + 6.0 and p.z > -plateau_in - 6.0 and _rng.randf() < 0.5:
			continue  # thinner edge so the cliff silhouette reads
		_tree(xforms, colors, p)
	# Yard edges and lake shore at ground level.
	for i in 260:
		var p := Vector3(_rng.randf_range(-170, 170), 0, _rng.randf_range(PIT_HALF + 2, 230))
		if absf(p.x) < 80.0 and p.z < YARD_SOUTH + 8.0:
			continue
		if _in_lake(p, 6.0):
			continue
		_tree(xforms, colors, p)
	add_child(_multimesh("Forest", mesh, xforms, colors, true))


func _tree(xforms: Array[Transform3D], colors: Array[Color], p: Vector3) -> void:
	var s := _rng.randf_range(0.85, 1.6)
	var basis := Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3(s, s * _rng.randf_range(0.95, 1.25), s))
	xforms.append(Transform3D(basis, p))
	colors.append(Color(1, 1, 1).lerp(Color(0.8, 1.05, 0.85), _rng.randf()))


func _in_lake(p: Vector3, margin := 0.0) -> bool:
	var q := Vector2((p.x - 40.0) / (130.0 + margin), (p.z - 175.0) / (45.0 + margin))
	return q.length() < 1.0


func _build_lake_and_hills(b: LowPolyBatch) -> void:
	var seg := 22
	var c := Vector3(40, 0.03, 175)
	for i in seg:
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		var p0 := c + Vector3(cos(a0) * 130 * _rng.randf_range(0.9, 1.0), 0, sin(a0) * 45)
		var p1 := c + Vector3(cos(a1) * 130 * _rng.randf_range(0.9, 1.0), 0, sin(a1) * 45)
		b.add_tri(c, p1, p0, Palette.WATER.lightened(0.04 * (i % 2)))
	# Forested hills across the lake.
	for i in 14:
		var x := -320.0 + i * 50.0 + _rng.randf_range(-15, 15)
		var hc := Vector3(x, 0, _rng.randf_range(250, 320))
		var r := _rng.randf_range(55, 95)
		var h := _rng.randf_range(22, 48)
		var rng := _rng
		b.add_mound(hc, r, h, 12, 3, _rng,
			func(_c, _n): return Palette.PINE.lerp(Palette.GRASS_DARK, rng.randf() * 0.6).lightened(rng.randf_range(0.0, 0.08)), 0.18)


func _build_mountains(b: LowPolyBatch) -> void:
	for i in 16:
		var ang := lerpf(-PI * 0.95, PI * 0.95, i / 15.0) + _rng.randf_range(-0.08, 0.08)
		var dist := _rng.randf_range(620, 760)
		var c := Vector3(sin(ang) * dist, 0, cos(ang) * dist)
		var r := _rng.randf_range(150, 240)
		var h := _rng.randf_range(80, 150)
		b.add_mound(c, r, h, 9, 4, _rng, _mountain_color.bind(h), 0.2)


func _mountain_color(cen: Vector3, _n: Vector3, h: float) -> Color:
	var t := cen.y / h
	if t > 0.74 + _rng.randf_range(-0.05, 0.05):
		return Palette.SNOW.darkened(_rng.randf_range(0.05, 0.18))
	return Palette.MOUNTAIN.lerp(Palette.PINE, (1.0 - t) * 0.5).lightened(_rng.randf_range(-0.04, 0.06))


func _build_clouds() -> LowPolyBatch:
	var b := LowPolyBatch.new()
	for i in 11:
		var c := Vector3(_rng.randf_range(-450, 450), _rng.randf_range(110, 160), _rng.randf_range(-500, 300))
		var puffs := _rng.randi_range(4, 7)
		for k in puffs:
			var t := (k - puffs * 0.5) / puffs
			var r := _rng.randf_range(7, 13) * (1.0 - absf(t) * 0.8)
			var off := Vector3(t * 40.0, _rng.randf_range(-1, 3) + (1.0 - absf(t)) * 4.0, _rng.randf_range(-6, 6))
			var pts := PackedVector3Array()
			for d in 18:
				var v := Vector3(_rng.randf_range(-1, 1), _rng.randf_range(-0.2, 1), _rng.randf_range(-1, 1)).normalized()
				pts.append(c + off + Vector3(v.x * r * 1.4, v.y * r, v.z * r))
			var rng := _rng
			b.add_hull(pts, Color.WHITE, func(_cc, n): return Color(1.0, 0.93, 0.88).lerp(Color(0.92, 0.72, 0.74), clampf(-n.y * 0.9 + 0.15, 0.0, 1.0) + rng.randf() * 0.04))  # sunset-lit, pink undersides
	return b


# --- Bounds & helpers -------------------------------------------------------

func _build_bounds() -> void:
	# Invisible walls keep the player in the pit + yard.
	_add_box_shape(Vector3(160, 10, 2), Vector3(0, 5, YARD_SOUTH + 1.0))
	for s in [-1.0, 1.0]:
		_add_box_shape(Vector3(2, 10, YARD_SOUTH - PIT_HALF), Vector3(s * 76.0, 5, (YARD_SOUTH + PIT_HALF) * 0.5))


func _add_box_shape(size: Vector3, pos: Vector3) -> void:
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	cs.shape = shape
	cs.position = pos
	_collision.add_child(cs)


func _add_convex_shape(pts: PackedVector3Array) -> void:
	var cs := CollisionShape3D.new()
	var shape := ConvexPolygonShape3D.new()
	shape.points = pts
	cs.shape = shape
	_collision.add_child(cs)


## Vertex-colour material with a procedural grain (built-in noise, triplanar in
## world space, so no UVs or image files are needed): gravel on the ground,
## fine pitting on rock. `scale` = repeats per metre.
func _grain_material(scale: float, darkest: float, bump: float) -> StandardMaterial3D:
	var m := LowPolyBatch.material().duplicate() as StandardMaterial3D
	var noise := FastNoiseLite.new()
	noise.seed = seed_value
	noise.noise_type = FastNoiseLite.TYPE_CELLULAR
	noise.frequency = 0.06
	noise.fractal_octaves = 3
	var ramp := Gradient.new()
	ramp.set_color(0, Color(darkest, darkest, darkest))
	ramp.set_color(1, Color.WHITE)
	var tex := NoiseTexture2D.new()
	tex.width = 256
	tex.height = 256
	tex.seamless = true
	tex.noise = noise
	tex.color_ramp = ramp
	var nrm := NoiseTexture2D.new()
	nrm.width = 256
	nrm.height = 256
	nrm.seamless = true
	nrm.noise = noise
	nrm.as_normal_map = true
	nrm.bump_strength = bump
	m.albedo_texture = tex
	m.normal_enabled = true
	m.normal_texture = nrm
	m.normal_scale = 0.6
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE * scale
	return m


func _multimesh(n: String, mesh: Mesh, xforms: Array[Transform3D], colors: Array[Color], shadows: bool) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
		mm.set_instance_color(i, Palette.render(colors[i]))
	var mmi := MultiMeshInstance3D.new()
	mmi.name = n
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mmi


func _tint(c: Color, amount: float) -> Color:
	var t := _rng.randf_range(-amount, amount)
	return c.lightened(t) if t > 0.0 else c.darkened(-t)
