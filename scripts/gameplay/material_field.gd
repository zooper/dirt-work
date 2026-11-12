class_name MaterialField
extends Node3D
## Authoritative 1 m columns of loose material in the quarry floor, not particles.
## Volume is conserved by every transfer. Mixed columns are well-mixed, not layered.
## Surface/collision are a smoothed, faceted approximation rebuilt at at most 5 Hz.
## No digging below the floor, overhangs or rock fracture in this prototype.

const CELL_SIZE := 1.0
const MIN_CELL := -38
const MAX_CELL := 37
const KINDS := ["sand", "gravel", "stone"]
const DIRECTIONS := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
const UPDATE_SECONDS := 0.2
const RELAX_BUDGET := 192

var _cells: Dictionary = {} # Vector2i -> {kind: cubic metres}
var _active: Array[Vector2i] = []
var _queued: Dictionary = {}
var _dirty := false
var _elapsed := 0.0
var _mesh: MeshInstance3D
var _body: StaticBody3D
var _shape: CollisionShape3D


func _ready() -> void:
	_ensure_nodes()
	rebuild_visuals()


func _physics_process(delta: float) -> void:
	_elapsed += delta
	if _elapsed < UPDATE_SECONDS:
		return
	_elapsed = fmod(_elapsed, UPDATE_SECONDS)
	relax(RELAX_BUDGET)
	if _dirty:
		rebuild_visuals()


func _local_point(p: Vector3) -> Vector3:
	return to_local(p) if is_inside_tree() else transform.affine_inverse() * p


func _in_bounds(c: Vector2i) -> bool:
	return c.x >= MIN_CELL and c.x <= MAX_CELL and c.y >= MIN_CELL and c.y <= MAX_CELL


func _cell_at(p: Vector3) -> Vector2i:
	return Vector2i(floori(p.x / CELL_SIZE), floori(p.z / CELL_SIZE))


func _volume(c: Vector2i) -> float:
	var total := 0.0
	for amount in _cells.get(c, {}).values():
		total += float(amount)
	return total


func _height(c: Vector2i) -> float:
	return _volume(c) / (CELL_SIZE * CELL_SIZE)


func _activate(c: Vector2i) -> void:
	if _in_bounds(c) and not _queued.has(c):
		_queued[c] = true
		_active.append(c)


func _changed(c: Vector2i) -> void:
	_dirty = true
	_activate(c)
	for d in DIRECTIONS:
		_activate(c + d)


func seed_pile(center: Vector3, radius: float, height: float, kind: String) -> void:
	if not KINDS.has(kind) or radius <= 0.0 or height <= 0.0:
		return
	var p := _local_point(center)
	for x in range(maxi(MIN_CELL, floori(p.x - radius)), mini(MAX_CELL + 1, ceili(p.x + radius))):
		for z in range(maxi(MIN_CELL, floori(p.z - radius)), mini(MAX_CELL + 1, ceili(p.z + radius))):
			var r := Vector2(x + 0.5 - p.x, z + 0.5 - p.z).length()
			var h := height * maxf(0.0, 1.0 - r / radius)
			if h <= 0.0:
				continue
			var c := Vector2i(x, z)
			var contents: Dictionary = _cells.get(c, {})
			contents[kind] = float(contents.get(kind, 0.0)) + h * CELL_SIZE * CELL_SIZE
			_cells[c] = contents
			_changed(c)


## Axis-aligned rectangular cutting footprint, centred on the cutting edge.
## Caller supplies swept depth/rate limit; repeated calls cannot take more than exists.
func scoop_at(world_point: Vector3, width: float, depth: float, max_volume: float) -> Dictionary:
	var taken: Dictionary = {}
	if width <= 0.0 or depth <= 0.0 or max_volume <= 0.0:
		return taken
	var p := _local_point(world_point)
	var left := p.x - width * 0.5
	var right := p.x + width * 0.5
	var near := p.z - depth * 0.5
	var far := p.z + depth * 0.5
	var candidates: Dictionary = {}
	var available := 0.0
	for x in range(maxi(MIN_CELL, floori(left)), mini(MAX_CELL + 1, ceili(right))):
		for z in range(maxi(MIN_CELL, floori(near)), mini(MAX_CELL + 1, ceili(far))):
			var c := Vector2i(x, z)
			var overlap := maxf(0.0, minf(right, x + 1.0) - maxf(left, x)) * maxf(0.0, minf(far, z + 1.0) - maxf(near, z))
			var amount := minf(_volume(c), maxf(0.0, _height(c) - maxf(p.y, 0.0)) * overlap)
			if amount > 0.0:
				candidates[c] = amount
				available += amount
	if available <= 0.0:
		return taken
	var fraction := minf(1.0, max_volume / available)
	for c in candidates:
		var part := _remove(c, float(candidates[c]) * fraction)
		for kind in part:
			taken[kind] = float(taken.get(kind, 0.0)) + float(part[kind])
	return taken


func _remove(c: Vector2i, volume: float) -> Dictionary:
	var removed: Dictionary = {}
	var total := _volume(c)
	if total <= 0.0:
		return removed
	var ratio := clampf(volume / total, 0.0, 1.0)
	var contents: Dictionary = _cells[c]
	for kind in contents.keys():
		var before := float(contents[kind])
		var amount := before * ratio
		removed[kind] = amount
		contents[kind] = maxf(0.0, before - amount)
		if contents[kind] == 0.0:
			contents.erase(kind)
	if contents.is_empty():
		_cells.erase(c)
	_changed(c)
	return removed


## This prototype supports only the flat quarry floor. Never teleport spill to a
## boundary. Caller retains its load if deposit fails (all-or-nothing operation).
func can_deposit(world_point: Vector3) -> bool:
	return world_point.is_finite() and _in_bounds(_cell_at(_local_point(world_point)))


func deposit_at(world_point: Vector3, loads: Dictionary) -> bool:
	if not can_deposit(world_point):
		return false
	for kind in loads:
		var amount := float(loads[kind])
		if not KINDS.has(kind) or not is_finite(amount) or amount < 0.0:
			return false
	var c := _cell_at(_local_point(world_point))
	var contents: Dictionary = _cells.get(c, {})
	for kind in loads:
		var amount := float(loads[kind])
		if amount > 0.0:
			contents[kind] = float(contents.get(kind, 0.0)) + amount
	if not contents.is_empty():
		_cells[c] = contents
		_changed(c)
	return true


func total_volumes() -> Dictionary:
	var totals := {"sand": 0.0, "gravel": 0.0, "stone": 0.0}
	for contents in _cells.values():
		for kind in contents:
			totals[kind] += float(contents[kind])
	return totals


## Local avalanching conserves each material separately. Budget bounds frame cost;
## disturbed piles settle over several ticks rather than solving the entire field.
func relax(budget: int = RELAX_BUDGET) -> void:
	for _i in mini(budget, _active.size()):
		var c: Vector2i = _active.pop_front()
		_queued.erase(c)
		var total := _volume(c)
		if total <= 0.0000001:
			continue
		var slope := 0.0
		for kind in _cells[c]:
			slope += tan(deg_to_rad(float(MaterialCatalog.SPECS[kind].repose))) * float(_cells[c][kind]) / total
		for d in DIRECTIONS:
			var other: Vector2i = c + d
			if not _in_bounds(other):
				continue
			var excess := _height(c) - _height(other) - slope * CELL_SIZE
			if excess > 0.02:
				var moved := _remove(c, excess * CELL_SIZE * CELL_SIZE * 0.25)
				var target: Dictionary = _cells.get(other, {})
				for kind in moved:
					target[kind] = float(target.get(kind, 0.0)) + float(moved[kind])
				_cells[other] = target
				_changed(other)


func _vertex_height(x: int, z: int) -> float:
	return (_height(Vector2i(x, z)) + _height(Vector2i(x - 1, z)) + _height(Vector2i(x, z - 1)) + _height(Vector2i(x - 1, z - 1))) * 0.25


func surface_height(world_point: Vector3) -> float:
	var p := _local_point(world_point)
	var c := _cell_at(p)
	var fx := p.x - c.x
	var fz := p.z - c.y
	# Same diagonal as the mesh, piecewise linear rather than bilinear.
	var a := _vertex_height(c.x, c.y)
	var b := _vertex_height(c.x + 1, c.y)
	var d := _vertex_height(c.x, c.y + 1)
	var e := _vertex_height(c.x + 1, c.y + 1)
	var h := a + (b - a) * fx + (e - b) * fz if fx >= fz else a + (e - d) * fx + (d - a) * fz
	return (to_global(Vector3(p.x, h, p.z)).y if is_inside_tree() else (transform * Vector3(p.x, h, p.z)).y)


func _ensure_nodes() -> void:
	if _mesh != null:
		return
	_mesh = MeshInstance3D.new()
	_mesh.name = "LooseMaterial"
	add_child(_mesh)
	_body = StaticBody3D.new()
	_body.name = "MaterialCollision"
	add_child(_body)
	_shape = CollisionShape3D.new()
	_body.add_child(_shape)


func rebuild_visuals() -> void:
	_ensure_nodes()
	_dirty = false
	var batch := LowPolyBatch.new()
	var draw_cells: Dictionary = {}
	for c in _cells:
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				draw_cells[c + Vector2i(dx, dz)] = true
	for c in draw_cells:
		var x: int = c.x
		var z: int = c.y
		var a := Vector3(x, _vertex_height(x, z), z)
		var b := Vector3(x + 1, _vertex_height(x + 1, z), z)
		var d := Vector3(x, _vertex_height(x, z + 1), z + 1)
		var e := Vector3(x + 1, _vertex_height(x + 1, z + 1), z + 1)
		if maxf(maxf(a.y, b.y), maxf(d.y, e.y)) < 0.00001:
			continue
		var contents: Dictionary = _cells.get(c, {})
		var total := _volume(c)
		var color := Color(0.43, 0.42, 0.38)
		if total > 0.0:
			color = Color(0, 0, 0, 1)
			for kind in contents:
				var weight := float(contents[kind]) / total
				var tint: Color = MaterialCatalog.SPECS[kind].color
				color.r += tint.r * weight
				color.g += tint.g * weight
				color.b += tint.b * weight
		var shade := 0.96 + float(posmod(x * 37 + z * 17, 9)) * 0.01
		batch.add_tri_facing(a, b, e, Vector3.UP, color * shade)
		batch.add_tri_facing(a, e, d, Vector3.UP, color * shade)
	if batch.is_empty():
		_mesh.mesh = null
		_shape.set_deferred("shape", null)
		return
	_mesh.mesh = batch.commit()
	_shape.set_deferred("shape", _mesh.mesh.create_trimesh_shape())
