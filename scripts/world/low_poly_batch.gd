@tool
class_name LowPolyBatch
extends RefCounted
## Accumulates flat-shaded, vertex-coloured triangles into ONE ArrayMesh so a
## whole set of scenery (cliffs, rocks, hills...) costs a single draw call.
## Winding convention for add_tri(): counter-clockwise when seen from outside.

static var _shared_material: StandardMaterial3D

var _st := SurfaceTool.new()
var _count := 0


func _init() -> void:
	_st.begin(Mesh.PRIMITIVE_TRIANGLES)


static func material() -> StandardMaterial3D:
	if _shared_material == null:
		_shared_material = StandardMaterial3D.new()
		_shared_material.vertex_color_use_as_albedo = true
		# add_tri() converts colours via Palette.render() (renderer-aware).
		_shared_material.vertex_color_is_srgb = false
		_shared_material.roughness = 0.92
	return _shared_material


func is_empty() -> bool:
	return _count == 0


func add_tri(a: Vector3, b: Vector3, c: Vector3, color: Color) -> void:
	var n := (b - a).cross(c - a)
	if n.length_squared() < 1e-12:
		return
	_st.set_normal(n.normalized())
	_st.set_color(Palette.render(color))
	# Godot treats clockwise as front-facing, so emit reversed.
	_st.add_vertex(a)
	_st.add_vertex(c)
	_st.add_vertex(b)
	_count += 1


## Like add_tri but orients the face so its normal points along `outward`.
func add_tri_facing(a: Vector3, b: Vector3, c: Vector3, outward: Vector3, color: Color) -> void:
	if (b - a).cross(c - a).dot(outward) >= 0.0:
		add_tri(a, b, c, color)
	else:
		add_tri(a, c, b, color)


func add_quad_facing(a: Vector3, b: Vector3, c: Vector3, d: Vector3, outward: Vector3, color: Color) -> void:
	add_tri_facing(a, b, c, outward, color)
	add_tri_facing(a, c, d, outward, color)


func add_quad(a: Vector3, b: Vector3, c: Vector3, d: Vector3, color: Color) -> void:
	add_tri(a, b, c, color)
	add_tri(a, c, d, color)


## Convex hull of a small point set (<= ~20 points), each face coloured by
## `color_fn.call(face_centroid, face_normal)` if given, else `color`.
func add_hull(pts: PackedVector3Array, color: Color, color_fn: Callable = Callable()) -> void:
	var inside := Vector3.ZERO
	for p in pts:
		inside += p
	inside /= pts.size()
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
					if s > 1e-4:
						pos = true
					elif s < -1e-4:
						neg = true
					if pos and neg:
						break
				if pos and neg:
					continue
				var a := pts[i]
				var b := pts[j]
				var c := pts[k]
				if normal.dot(a - inside) < 0.0:
					var t := b
					b = c
					c = t
					normal = -normal
				var col := color
				if color_fn.is_valid():
					col = color_fn.call((a + b + c) / 3.0, normal)
				add_tri(a, b, c, col)


## Jittered box (8 corners) — the building block for angular rock slabs.
func add_slab(center: Vector3, size: Vector3, basis: Basis, jitter: float, rng: RandomNumberGenerator,
		color: Color, color_fn: Callable = Callable()) -> PackedVector3Array:
	var pts := PackedVector3Array()
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				var local := Vector3(sx, sy, sz) * size * 0.5
				local += Vector3(rng.randf_range(-1, 1), rng.randf_range(-1, 1), rng.randf_range(-1, 1)) * jitter
				pts.append(center + basis * local)
	add_hull(pts, color, color_fn)
	return pts


## Faceted rock: jittered 14-point hull.
func add_rock(center: Vector3, size: float, rng: RandomNumberGenerator, color: Color,
		flatten := 0.7) -> PackedVector3Array:
	var dirs := [Vector3.UP, Vector3.DOWN, Vector3.LEFT, Vector3.RIGHT, Vector3.FORWARD, Vector3.BACK,
		Vector3(1, 1, 1), Vector3(-1, 1, 1), Vector3(1, 1, -1), Vector3(-1, 1, -1),
		Vector3(1, -1, 1), Vector3(-1, -1, 1), Vector3(1, -1, -1), Vector3(-1, -1, -1)]
	var pts := PackedVector3Array()
	for d in dirs:
		var v: Vector3 = d.normalized() * size * rng.randf_range(0.7, 1.15)
		v.y *= flatten
		pts.append(center + v)
	var base := color
	add_hull(pts, color, func(_c, nrm): return _shade(base, nrm, rng))
	return pts


## Jittered cone / mound: `rings` stacked rings, coloured per face via color_fn.
func add_mound(center: Vector3, radius: float, height: float, segments: int, rings: int,
		rng: RandomNumberGenerator, color_fn: Callable, jitter := 0.12) -> PackedVector3Array:
	var levels: Array = []
	var offs := rng.randf() * TAU
	for r in rings:
		var t := float(r) / rings
		var ring := PackedVector3Array()
		var rr := radius * (1.0 - t) * (1.0 - 0.15 * t)
		var y := height * (1.0 - pow(1.0 - t, 1.0 + 0.4 * t)) if r > 0 else 0.0
		for i in segments:
			var a := TAU * i / segments + offs + rng.randf_range(-jitter, jitter) * 0.5
			var rj := rr * rng.randf_range(1.0 - jitter, 1.0 + jitter)
			ring.append(center + Vector3(cos(a) * rj, y + (rng.randf_range(-jitter, jitter) * height * 0.3 if r > 0 else 0.0), sin(a) * rj))
		levels.append(ring)
	var apex := center + Vector3(rng.randf_range(-0.05, 0.05) * radius, height, rng.randf_range(-0.05, 0.05) * radius)
	var hull_pts := PackedVector3Array()
	for r in rings:
		var lo: PackedVector3Array = levels[r]
		hull_pts.append_array(lo)
		for i in segments:
			var j := (i + 1) % segments
			if r + 1 < rings:
				var hi: PackedVector3Array = levels[r + 1]
				# Rings have different random offsets; connect by index (fine for low-poly).
				var c1: Color = color_fn.call((lo[i] + lo[j] + hi[i]) / 3.0, _face_normal(lo[i], hi[i], lo[j], center))
				add_tri_facing(lo[i], hi[i], lo[j], _outward(lo[i], lo[j], hi[i], center), c1)
				var c2: Color = color_fn.call((lo[j] + hi[i] + hi[j]) / 3.0, _face_normal(lo[j], hi[i], hi[j], center))
				add_tri_facing(lo[j], hi[i], hi[j], _outward(lo[j], hi[i], hi[j], center), c2)
			else:
				add_tri_facing(lo[i], apex, lo[j], _outward(lo[i], lo[j], apex, center), color_fn.call((lo[i] + lo[j] + apex) / 3.0, _face_normal(lo[i], lo[j], apex, center)))
	hull_pts.append(apex)
	return hull_pts


static func _face_normal(a: Vector3, b: Vector3, c: Vector3, center: Vector3) -> Vector3:
	var n := (b - a).cross(c - a).normalized()
	return n if n.dot(_outward(a, b, c, center)) >= 0.0 else -n


## Outward direction for a mound face: away from the mound axis, tilted up.
static func _outward(a: Vector3, b: Vector3, c: Vector3, center: Vector3) -> Vector3:
	var m := (a + b + c) / 3.0 - center
	return Vector3(m.x, 0.0, m.z).normalized() + Vector3.UP * 0.3


func commit() -> ArrayMesh:
	_st.set_material(material())
	return _st.commit()


## Builds a MeshInstance3D from the batch (no collision).
func to_instance(name := "Batch", cast_shadows := true) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = name
	mi.mesh = commit()
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast_shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


## Slight per-face brightness variation (by facing + random) for a hand-painted feel.
static func _shade(base: Color, normal: Vector3, rng: RandomNumberGenerator) -> Color:
	var up := clampf(normal.y, -1.0, 1.0)
	var c := base.lightened(0.08 * maxf(up, 0.0)).darkened(0.1 * maxf(-up, 0.0))
	return c.lightened(rng.randf_range(-0.06, 0.06)) if rng.randf() > 0.5 else c.darkened(rng.randf_range(0.0, 0.07))
