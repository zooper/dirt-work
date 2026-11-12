class_name MaterialHandling
extends Node3D
## Prototype bulk-volume gameplay on the flat quarry floor. Dust is presentation only.
var bucket := BucketMaterial.new()
var field: MaterialField
var receiver: Dictionary = {}
var _loader: WheelLoader
var _last_tip: Vector3
var _last_velocity := Vector3.ZERO
var _hud: Label
var _receiver_mesh: MeshInstance3D

func _ready() -> void:
	_loader = get_parent().get_node("WheelLoader")
	field = MaterialField.new()
	add_child(field)
	var world = get_parent().get_node("World")
	var kinds := ["sand", "gravel", "stone", "sand"]
	for i in world.piles.size():
		var pile: Dictionary = world.piles[i]
		field.seed_pile(pile.center, pile.radius, pile.height, kinds[i])
	field.rebuild_visuals()
	_last_tip = _loader.get_bucket_tip_global()
	_loader.material_gameplay = true
	var truck = get_parent().get_node("Hauler")
	truck.get_node("Load").hide()
	_receiver_mesh = MeshInstance3D.new()
	_receiver_mesh.mesh = BoxMesh.new()
	_receiver_mesh.mesh.size = Vector3(2.7, 1.0, 4.0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = MaterialCatalog.SPECS.gravel.color
	_receiver_mesh.material_override = mat
	truck.add_child(_receiver_mesh)
	_receiver_mesh.position = Vector3(0, 3.2, 3.0)
	_receiver_mesh.hide()
	var canvas := CanvasLayer.new()
	add_child(canvas)
	_hud = Label.new()
	canvas.add_child(_hud)
	_hud.position = Vector2(20, 110)

func _physics_process(delta: float) -> void:
	if not is_instance_valid(_loader):
		return
	var tip := _loader.get_bucket_tip_global()
	var travel := Vector2(tip.x - _last_tip.x, tip.z - _last_tip.z).length()
	var accel := (_loader.velocity - _last_velocity).length() / maxf(delta, 0.001)
	_loader.material_flow = false
	_loader.dig_resistance = 0.0
	# Bounded sweep samples avoid tunnelling. Teleports must not excavate.
	if travel > 0.0001 and travel < 1.0 and _loader.speed > 0.05 and _loader.tilt_angle < 20.0:
		var steps := maxi(1, ceili(travel / 0.15))
		for i in steps:
			var point := _last_tip.lerp(tip, float(i + 1) / steps)
			var query := PhysicsRayQueryParameters3D.create(_last_tip + Vector3.UP * 0.05, point + Vector3.UP * 0.05)
			query.exclude = [_loader.get_rid()]
			var hit := get_world_3d().direct_space_state.intersect_ray(query)
			if not hit.is_empty() and not field.is_ancestor_of(hit.collider):
				break
			# Eight narrow cuts follow the actual bucket's lateral axis.
			var side: Vector3 = _loader.get_node("Chassis/FrontFrame/ArmPivot/BucketPivot").global_basis.x.normalized()
			for strip in 8:
				var cut := point + side * ((float(strip) + 0.5) * 0.35 - 1.4)
				query.from = cut - (tip - _last_tip) / steps + Vector3.UP * 0.05
				query.to = cut + Vector3.UP * 0.05
				var edge_hit := get_world_3d().direct_space_state.intersect_ray(query)
				if not edge_hit.is_empty() and not field.is_ancestor_of(edge_hit.collider):
					continue
				var loads := field.scoop_at(cut, 0.35, 0.35, minf(bucket.free_volume(), 0.35 * travel / steps))
				MaterialCatalog.merge(bucket.loads, loads)
				for kind in loads:
					_loader.dig_resistance = maxf(_loader.dig_resistance, MaterialCatalog.SPECS[kind].resistance)
	var release := bucket.release_amount(delta, _loader.tilt_angle, accel, 0.0, _loader.lift_input > 0.1)
	if release > 0.0:
		var truck: Node3D = get_parent().get_node("Hauler")
		var local := truck.to_local(tip)
		var in_bed := absf(local.x) < 1.35 and local.z > 1.0 and local.z < 5.0 and local.y > 3.1
		# No transfer through solid objects. Material hitting the receiver is
		# accepted only to its capacity; blocked/outside-floor flow stays aboard.
		var clear_floor := false
		if field.can_deposit(tip):
			var down := PhysicsRayQueryParameters3D.create(tip, Vector3(tip.x, -1.0, tip.z))
			down.exclude = [_loader.get_rid()]
			var below := get_world_3d().direct_space_state.intersect_ray(down)
			clear_floor = below.is_empty() or field.is_ancestor_of(below.collider) or below.position.y < 0.2
		if in_bed:
			release = minf(release, maxf(0.0, 20.0 - MaterialCatalog.volume(receiver)))
		if release > 0.0 and (in_bed or clear_floor):
			var removed := MaterialCatalog.take(bucket.loads, release)
			if in_bed:
				MaterialCatalog.merge(receiver, removed)
				_receiver_mesh.show()
				_receiver_mesh.scale.y = clampf(MaterialCatalog.volume(receiver) / 10.8, 0.01, 2.0)
			elif not field.deposit_at(tip, removed):
				MaterialCatalog.merge(bucket.loads, removed)
			_loader.material_flow = true
	_loader.bucket_fill = bucket.volume() / bucket.heaped_capacity
	_loader.payload_kg = bucket.mass()
	_hud.text = "Bucket: %.2f m³ / %.1f t  |  Delivered: %.2f m³\nSand: west/north • Gravel: west/south • Stone: west/centre\nLower edge, drive into pile, curl and lift. Tilt forward to tip.\nPrototype: bulk material on quarry floor only; outside pit load is retained." % [bucket.volume(), bucket.mass() / 1000.0, MaterialCatalog.volume(receiver)]
	_last_tip = tip
	_last_velocity = _loader.velocity
