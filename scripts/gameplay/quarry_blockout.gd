class_name QuarryBlockout
extends Node3D
## Deterministic low-poly quarry blockout: floor, terraced walls, a ramp,
## gravel piles (drivable, convex), faceted boulders and stylized pines.
## Everything is generated from primitives with a fixed seed, so the layout is
## identical on every run and no external assets are required.
##
## Gravel piles are visual/collision blockout only; volume accounting arrives in M2.

@export var seed_value := 7319
@export var floor_size := 80.0
@export var tier_height := 4.0
@export var tier_depth := 8.0

const C_GRAVEL := Color(0.62, 0.56, 0.47)
const C_GRASS := Color(0.36, 0.52, 0.28)
const C_WALL_A := Color(0.55, 0.50, 0.45)
const C_WALL_B := Color(0.47, 0.43, 0.40)
const C_PILE := Color(0.70, 0.64, 0.55)
const C_ROCK := Color(0.50, 0.50, 0.52)
const C_PINE := Color(0.16, 0.34, 0.24)
const C_TRUNK := Color(0.36, 0.25, 0.17)

var _rng := RandomNumberGenerator.new()
var _materials := {}


func _ready() -> void:
	_rng.seed = seed_value
	_build_ground()
	_build_walls()
	_build_ramp(Vector3(20.0, 0.0, -floor_size * 0.5), 8.0, 16.0, tier_height)
	_build_piles()
	_build_boulders()
	_build_pines()


# --- Layout -----------------------------------------------------------------

func _build_ground() -> void:
	var half := floor_size * 0.5
	# One flat collider for everything at y=0 avoids seams that snag the loader.
	_static_box(Vector3(400, 1, 400), Vector3(0, -0.5, 0), null)
	_mesh_box(Vector3(400, 0.1, 400), Vector3(0, -0.08, 0), C_GRASS)
	_mesh_box(Vector3(floor_size, 0.1, floor_size + 30.0), Vector3(0, -0.05, 15.0 - 0.0), C_GRAVEL)
	# Low spoil berms marking the open south edge.
	for x in [-half + 6.0, half - 6.0]:
		_static_box(Vector3(10, 1.2, 3), Vector3(x, 0.6, half + 6.0), C_WALL_B)


func _build_walls() -> void:
	var half := floor_size * 0.5
	for tier in 2:
		var h := tier_height * (tier + 1)
		var inner := half + tier * tier_depth
		var span := (inner + tier_depth) * 2.0
		var col := C_WALL_A if tier == 0 else C_WALL_B
		# North
		_static_box(Vector3(span, h, tier_depth), Vector3(0, h * 0.5, -inner - tier_depth * 0.5), col)
		# West / East (run from the north wall to the open south edge)
		var length := inner + tier_depth + half
		var zc := (-(inner + tier_depth) + half) * 0.5
		_static_box(Vector3(tier_depth, h, length), Vector3(-inner - tier_depth * 0.5, h * 0.5, zc), col)
		_static_box(Vector3(tier_depth, h, length), Vector3(inner + tier_depth * 0.5, h * 0.5, zc), col)


## Wedge ramp rising toward -Z, ending flush against a wall at `top_edge`.
func _build_ramp(top_edge: Vector3, width: float, length: float, height: float) -> void:
	var hw := width * 0.5
	var z0 := top_edge.z + length   # foot of ramp
	var z1 := top_edge.z            # top of ramp
	var x := top_edge.x
	var pts := PackedVector3Array([
		Vector3(x - hw, 0, z0), Vector3(x + hw, 0, z0),
		Vector3(x - hw, 0, z1), Vector3(x + hw, 0, z1),
		Vector3(x - hw, height, z1), Vector3(x + hw, height, z1),
	])
	var faces := [[0, 4, 1], [1, 4, 5], [0, 2, 4], [1, 5, 3], [2, 3, 4], [3, 5, 4], [0, 1, 2], [1, 3, 2]]
	_convex_static(pts, faces, C_GRAVEL.darkened(0.08))


func _build_piles() -> void:
	var spots := [Vector3(-22, 0, -22), Vector3(-8, 0, -28), Vector3(-26, 0, -6)]
	for p in spots:
		var r := _rng.randf_range(4.0, 5.5)
		var h := r * _rng.randf_range(0.42, 0.5)
		_build_pile(p, r, h)


func _build_pile(center: Vector3, radius: float, height: float) -> void:
	var segments := 9
	var ring := PackedVector3Array()
	var mid := PackedVector3Array()
	for i in segments:
		var a := TAU * i / segments + _rng.randf_range(-0.15, 0.15)
		var rr := radius * _rng.randf_range(0.85, 1.1)
		ring.append(center + Vector3(cos(a) * rr, 0, sin(a) * rr))
		var mr := rr * 0.55
		mid.append(center + Vector3(cos(a + 0.3) * mr, height * _rng.randf_range(0.5, 0.65), sin(a + 0.3) * mr))
	var top := center + Vector3(_rng.randf_range(-0.4, 0.4), height, _rng.randf_range(-0.4, 0.4))
	var pts := PackedVector3Array()
	pts.append_array(ring)
	pts.append_array(mid)
	pts.append(top)
	var faces := []
	var t := segments * 2
	for i in segments:
		var j := (i + 1) % segments
		faces.append([i, segments + i, j])
		faces.append([j, segments + i, segments + j])
		faces.append([segments + i, t, segments + j])
	_convex_static(pts, faces, C_PILE)


func _build_boulders() -> void:
	var half := floor_size * 0.5
	for i in 14:
		var p := Vector3(_rng.randf_range(-half + 3, half - 3), 0, _rng.randf_range(-half + 3, half - 3))
		if p.distance_to(Vector3(0, 0, 10)) < 12.0 or absf(p.x - 20.0) < 7.0 and p.z < -20.0:
			continue  # keep spawn and ramp approach clear
		var s := _rng.randf_range(0.7, 1.8)
		_build_rock(p + Vector3.UP * s * 0.35, s)
	# A few large rocks along wall bases for silhouette.
	for i in 8:
		var along := _rng.randf_range(-half + 4, half - 4)
		_build_rock(Vector3(along, 0.8, -half + 1.5), _rng.randf_range(1.5, 2.6))


func _build_rock(center: Vector3, size: float) -> void:
	var pts := PackedVector3Array()
	# Jittered octahedron-ish hull; convex by construction via ConvexPolygonShape3D.
	var dirs := [Vector3.UP, Vector3.DOWN, Vector3.LEFT, Vector3.RIGHT, Vector3.FORWARD, Vector3.BACK,
		Vector3(1, 1, 1), Vector3(-1, 1, 1), Vector3(1, 1, -1), Vector3(-1, 1, -1),
		Vector3(1, -1, 1), Vector3(-1, -1, 1), Vector3(1, -1, -1), Vector3(-1, -1, -1)]
	for d in dirs:
		var v: Vector3 = d.normalized() * size * _rng.randf_range(0.7, 1.15)
		v.y *= 0.7
		pts.append(center + v)
	var hull := ConvexPolygonShape3D.new()
	hull.points = pts
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	cs.shape = hull
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	mi.mesh = _flat_mesh_from_hull(pts, C_ROCK.lerp(C_WALL_A, _rng.randf()))
	body.add_child(mi)
	add_child(body)


func _build_pines() -> void:
	var half := floor_size * 0.5
	var rim := half + tier_depth * 2.0
	for i in 70:
		var p: Vector3
		var side := i % 4
		match side:
			0: p = Vector3(_rng.randf_range(-rim - 30, rim + 30), 0, _rng.randf_range(-rim - 30, -rim - 2))
			1: p = Vector3(_rng.randf_range(-rim - 30, -rim - 2), 0, _rng.randf_range(-rim, half + 40))
			2: p = Vector3(_rng.randf_range(rim + 2, rim + 30), 0, _rng.randf_range(-rim, half + 40))
			_: p = Vector3(_rng.randf_range(-half, half), 0, _rng.randf_range(half + 14, half + 50))
		_build_pine(p, _rng.randf_range(0.8, 1.4), side == 3)


func _build_pine(base: Vector3, scale_f: float, collide: bool) -> void:
	var root := StaticBody3D.new() if collide else Node3D.new()
	root.position = base
	add_child(root)
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.18 * scale_f
	trunk.bottom_radius = 0.25 * scale_f
	trunk.height = 1.6 * scale_f
	trunk.radial_segments = 5
	trunk.rings = 1
	trunk.material = _mat(C_TRUNK)
	var tmi := MeshInstance3D.new()
	tmi.mesh = trunk
	tmi.position.y = trunk.height * 0.5
	root.add_child(tmi)
	for k in 3:
		var cone := CylinderMesh.new()
		cone.top_radius = 0.0
		cone.bottom_radius = (1.6 - k * 0.4) * scale_f
		cone.height = 2.2 * scale_f
		cone.radial_segments = 6
		cone.rings = 1
		cone.material = _mat(C_PINE.lightened(k * 0.05))
		var cmi := MeshInstance3D.new()
		cmi.mesh = cone
		cmi.position.y = (1.6 + 1.0 + k * 1.2) * scale_f
		cmi.rotation.y = _rng.randf() * TAU
		root.add_child(cmi)
	if collide:
		var cs := CollisionShape3D.new()
		var shape := CylinderShape3D.new()
		shape.radius = 0.3 * scale_f
		shape.height = 4.0 * scale_f
		cs.shape = shape
		cs.position.y = shape.height * 0.5
		root.add_child(cs)


# --- Helpers ----------------------------------------------------------------

func _mat(color: Color) -> StandardMaterial3D:
	if not _materials.has(color):
		var m := StandardMaterial3D.new()
		m.albedo_color = color
		m.roughness = 0.95
		_materials[color] = m
	return _materials[color]


func _mesh_box(size: Vector3, pos: Vector3, color: Color) -> MeshInstance3D:
	var bm := BoxMesh.new()
	bm.size = size
	bm.material = _mat(color)
	var mi := MeshInstance3D.new()
	mi.mesh = bm
	mi.position = pos
	add_child(mi)
	return mi


func _static_box(size: Vector3, pos: Vector3, color: Variant) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.position = pos
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	cs.shape = shape
	body.add_child(cs)
	if color != null:
		var bm := BoxMesh.new()
		bm.size = size
		bm.material = _mat(color)
		var mi := MeshInstance3D.new()
		mi.mesh = bm
		body.add_child(mi)
	add_child(body)
	return body


func _convex_static(pts: PackedVector3Array, faces: Array, color: Color) -> StaticBody3D:
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var shape := ConvexPolygonShape3D.new()
	shape.points = pts
	cs.shape = shape
	body.add_child(cs)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)  # flat shading = faceted low-poly look
	for f in faces:
		_add_tri_outward(st, pts[f[0]], pts[f[1]], pts[f[2]], _centroid(pts))
	st.generate_normals()
	st.set_material(_mat(color))
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	body.add_child(mi)
	add_child(body)
	return body


## Builds a flat-shaded mesh of the convex hull of `pts` (small point counts only).
func _flat_mesh_from_hull(pts: PackedVector3Array, color: Color) -> ArrayMesh:
	var c := _centroid(pts)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)
	var n := pts.size()
	for i in n:
		for j in range(i + 1, n):
			for k in range(j + 1, n):
				var normal := (pts[j] - pts[i]).cross(pts[k] - pts[i])
				if normal.length_squared() < 1e-8:
					continue
				normal = normal.normalized()
				var d := normal.dot(pts[i])
				var pos := false
				var neg := false
				for m in n:
					var s := normal.dot(pts[m]) - d
					if s > 1e-4: pos = true
					elif s < -1e-4: neg = true
					if pos and neg: break
				if pos and neg:
					continue
				_add_tri_outward(st, pts[i], pts[j], pts[k], c)
	st.generate_normals()
	st.set_material(_mat(color))
	return st.commit()


func _add_tri_outward(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, inside: Vector3) -> void:
	# Godot front faces are clockwise when viewed from outside.
	var n := (b - a).cross(c - a)
	if n.dot(a - inside) > 0.0:
		st.add_vertex(a); st.add_vertex(c); st.add_vertex(b)
	else:
		st.add_vertex(a); st.add_vertex(b); st.add_vertex(c)


func _centroid(pts: PackedVector3Array) -> Vector3:
	var c := Vector3.ZERO
	for p in pts:
		c += p
	return c / pts.size()
