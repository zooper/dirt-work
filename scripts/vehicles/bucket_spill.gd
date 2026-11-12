class_name BucketSpill
extends Node3D
## Presentation: shows the material carried in the bucket and, when the bucket is
## tipped forward while carrying, a stream of rock chunks plus a dust cloud.
## Reads WheelLoader.bucket_fill / tilt_angle; never changes gameplay state.
## Placed under BucketPivot at the bucket lip.

@export var dump_tilt_deg := 12.0    ## tilt beyond which material pours out
@export var lip_width := 3.4

var _loader: WheelLoader
var _heap: MeshInstance3D
var _rocks: CPUParticles3D
var _dust: CPUParticles3D
var _was_pouring := false


func _ready() -> void:
	var n: Node = self
	while n and not (n is WheelLoader):
		n = n.get_parent()
	_loader = n as WheelLoader
	_heap = _build_heap()
	add_child(_heap)
	_rocks = _build_rocks()
	add_child(_rocks)
	_dust = _build_dust()
	add_child(_dust)


func _process(_delta: float) -> void:
	if _loader == null:
		return
	var fill := clampf(_loader.bucket_fill, 0.0, 1.0)
	_heap.visible = fill > 0.02
	_heap.scale = Vector3(1.0, maxf(fill, 0.05), 1.0)
	var pouring := _loader.material_flow if _loader.material_gameplay else (fill > 0.02 and _loader.tilt_angle > dump_tilt_deg)
	if pouring != _was_pouring:
		_rocks.emitting = pouring
		_dust.emitting = pouring
		if pouring:
			_rocks.restart()
			_dust.restart()
		_was_pouring = pouring


func _rock_mesh() -> ArrayMesh:
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	var b := LowPolyBatch.new()
	b.add_rock(Vector3.ZERO, 0.2, rng, Palette.GRAVEL_PILE, 0.8)
	return b.commit()


func _build_heap() -> MeshInstance3D:
	# Angular mound sitting in the bucket (bucket-local: opening faces -Z, floor at y≈-1.5).
	var rng := RandomNumberGenerator.new()
	rng.seed = 91
	var b := LowPolyBatch.new()
	var pts := PackedVector3Array()
	for x in [-1.7, -0.85, 0.0, 0.85, 1.7]:
		for z in [-0.2, -0.7, -1.2, -1.7]:
			var h := 0.25 + (1.0 - absf(x) / 1.9) * 0.55 * (1.0 - absf(z + 0.9) / 1.2)
			pts.append(Vector3(x, h + rng.randf_range(-0.06, 0.06), z))
	for x in [-1.75, 1.75]:
		for z in [-0.1, -1.8]:
			pts.append(Vector3(x, -0.9, z))
	b.add_hull(pts, Palette.GRAVEL_PILE, func(_c, nrm): return Palette.GRAVEL_PILE.lerp(Palette.ROCK_WARM, rng.randf() * 0.4).darkened(0.15 * (1.0 - maxf(nrm.y, 0.0))))
	var mi := MeshInstance3D.new()
	mi.mesh = b.commit()
	mi.position = Vector3(0, -0.55, 0.0)
	return mi


func _build_rocks() -> CPUParticles3D:
	# CPU particles: identical on every renderer (incl. software Vulkan previews).
	var p := CPUParticles3D.new()
	p.amount = 320
	p.lifetime = 1.1
	p.preprocess = 1.1
	p.randomness = 0.6
	p.emitting = false
	p.local_coords = false
	p.mesh = _rock_mesh()
	p.position = Vector3(0, -0.9, -1.55)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(lip_width * 0.45, 0.25, 0.3)
	p.direction = Vector3(0, 0.2, -1)   # out over the lip, then gravity
	p.spread = 25.0
	p.initial_velocity_min = 1.8
	p.initial_velocity_max = 3.4
	p.local_coords = false
	p.gravity = Vector3(0, -9.8, 0)
	p.angular_velocity_min = -180.0
	p.angular_velocity_max = 180.0
	p.scale_amount_min = 0.7
	p.scale_amount_max = 2.2
	return p


func _build_dust() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 46
	p.lifetime = 3.6
	p.preprocess = 3.0
	p.emitting = false
	p.local_coords = false
	var quad := QuadMesh.new()
	quad.size = Vector2(3.0, 3.0)
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 1.0])
	grad.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0)])
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	tex.width = 64
	tex.height = 64
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.albedo_texture = tex
	mat.albedo_color = Palette.render(Color(0.86, 0.76, 0.64, 0.34))
	mat.vertex_color_use_as_albedo = true
	mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	quad.material = mat
	p.mesh = quad
	p.position = Vector3(0, -2.2, -2.0)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(2.4, 0.9, 1.6)
	p.direction = Vector3(0, 1, 0)
	p.spread = 60.0
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.8
	p.gravity = Vector3(0.45, 0.22, 0.1)   # drifts downwind and rises
	p.scale_amount_min = 0.9
	p.scale_amount_max = 2.8
	var fade := Gradient.new()
	fade.offsets = PackedFloat32Array([0.0, 0.25, 1.0])
	fade.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0)])
	p.color_ramp = fade
	return p
