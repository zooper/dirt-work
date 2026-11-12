extends SceneTree
## Headless logic/scene tests. Run:
##   godot --headless --path . -s tests/run_tests.gd
## Exits with code 1 on any failure. Checks behaviour, not visuals or feel.

## Each player feature must be reachable from keyboard AND gamepad; a feature
## may use several actions (e.g. keyboard keys + a gamepad modifier combo).
const FEATURES := {
	"drive": ["throttle", "brake_reverse"],
	"steer": ["steer_left", "steer_right"],
	"handbrake": ["handbrake"],
	"loader arm/bucket": ["lift_up", "lift_down", "tilt_back", "tilt_dump",
		"loader_modifier", "loader_stick_up", "loader_stick_down", "loader_stick_left", "loader_stick_right"],
	"camera look": ["look_left", "look_right", "look_up", "look_down"],
	"camera switch": ["camera_switch"],
	"camera zoom": ["camera_zoom_in", "camera_zoom_out"],
	"cruise control": ["cruise_toggle", "cruise_slower", "cruise_faster"],
	"screenshot": ["screenshot"],
}

var _failures := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	_test_input_map()
	await _test_quarry_drive()
	print("TESTS %s (%d failure(s))" % ["PASSED" if _failures == 0 else "FAILED", _failures])
	quit(1 if _failures > 0 else 0)


func _check(cond: bool, msg: String) -> void:
	print(("  ok   " if cond else "  FAIL ") + msg)
	if not cond:
		_failures += 1


func _test_input_map() -> void:
	print("InputMap: every feature has keyboard and gamepad bindings")
	for feature in FEATURES:
		var has_key := false
		var has_pad := false
		var missing := []
		for a in FEATURES[feature]:
			if not InputMap.has_action(a):
				missing.append(a)
				continue
			for ev in InputMap.action_get_events(a):
				has_key = has_key or ev is InputEventKey or ev is InputEventMouseButton
				has_pad = has_pad or ev is InputEventJoypadButton or ev is InputEventJoypadMotion
		_check(has_key and has_pad and missing.is_empty(), "%s %s" % [feature, missing if missing else ""])
	# Farming Simulator default keys for the front loader.
	_check(_has_key("lift_up", KEY_J) and _has_key("lift_down", KEY_N) and _has_key("tilt_back", KEY_K) and _has_key("tilt_dump", KEY_M), "loader keys are J/N/K/M")


func _has_key(action: String, key: Key) -> bool:
	for ev in InputMap.action_get_events(action):
		if ev is InputEventKey and ev.physical_keycode == key:
			return true
	return false


func _frames(n: int) -> void:
	for i in n:
		await physics_frame


func _test_quarry_drive() -> void:
	print("Quarry: loader drives, steers, lifts and tilts")
	var level: Node = load("res://scenes/levels/quarry.tscn").instantiate()
	root.add_child(level)
	var loader := level.get_node("WheelLoader") as WheelLoader
	(loader.get_node("PlayerInput") as PlayerLoaderInput).enabled = false
	await _frames(60)
	var world := level.get_node("World") as QuarryWorld
	_check(world.piles.size() == 4, "world has 4 gravel piles")
	var forest := world.get_node("Forest") as MultiMeshInstance3D
	_check(forest.multimesh.instance_count > 500, "forest has %d pines" % forest.multimesh.instance_count)
	var draw_nodes := 0
	for n in world.get_children():
		if n is GeometryInstance3D:
			draw_nodes += 1
	var site := level.get_node("Site")
	_check(site.get_node("Collision").get_child_count() > 20, "site props have colliders")
	_check(draw_nodes <= 10, "scenery batched into %d mesh nodes" % draw_nodes)
	_check(loader.is_on_floor(), "loader settles on the floor")
	var meshes := 0
	for part in ["Chassis/FrontFrame/Model", "Chassis/RearPivot/Model", "Chassis/FrontFrame/ArmPivot/Model",
			"Chassis/FrontFrame/ArmPivot/BucketPivot/Model", "Chassis/FrontFrame/WheelFL/Tire"]:
		if not loader.get_node(part).find_children("*", "MeshInstance3D").is_empty():
			meshes += 1
	_check(meshes == 5, "all 5 Blender model parts loaded (%d)" % meshes)
	var ram := loader.get_node("Chassis/FrontFrame/LiftRamL") as Node3D
	_check(ram.get_child_count() == 2, "lift ram built barrel + rod")
	var start := loader.global_position

	loader.throttle = 1.0
	await _frames(180)
	var travelled := start.distance_to(loader.global_position)
	_check(travelled > 5.0 and loader.speed > 3.0, "throttle moves forward (%.1f m, %.1f m/s)" % [travelled, loader.speed])
	_check(loader.global_position.z < start.z, "forward is -Z")

	var yaw0 := loader.global_rotation.y
	loader.steer = 1.0
	await _frames(120)
	_check(loader.articulation > deg_to_rad(20.0), "steering articulates the frame")
	_check(loader.global_rotation.y < yaw0, "steering right turns clockwise")
	var front := loader.get_node("Chassis/FrontFrame") as Node3D
	var rear := loader.get_node("Chassis/RearPivot") as Node3D
	_check(front.rotation.y < 0.0 and rear.rotation.y > 0.0 and is_equal_approx(-front.rotation.y, rear.rotation.y), "both frames bend symmetrically around the hinge")
	loader.steer = 0.0
	loader.throttle = 0.0
	loader.brake = 1.0
	await _frames(240)
	_check(loader.speed < 0.0, "brake stops then reverses (speed %.2f at %s, wall=%s)" % [loader.speed, loader.global_position, loader.is_on_wall()])
	loader.brake = 0.0
	loader.cruise_speed = 3.0
	loader.cruise_active = true
	await _frames(240)
	_check(absf(loader.speed - 3.0) < 0.3, "cruise control holds speed (%.2f m/s)" % loader.speed)
	loader.brake = 1.0
	await _frames(2)
	_check(not loader.cruise_active, "brake cancels cruise control")
	loader.brake = 0.0
	loader.handbrake = true
	await _frames(120)
	_check(absf(loader.speed) < 0.05, "handbrake stops")
	loader.handbrake = false

	var tip0 := loader.get_bucket_tip_global().y
	loader.lift_input = 1.0
	await _frames(240)
	loader.lift_input = 0.0
	_check(is_equal_approx(loader.lift_angle, loader.lift_max_deg), "lift reaches max")
	_check(loader.get_bucket_tip_global().y > tip0 + 2.0, "raising arms raises bucket tip")
	var rod := ram.get_child(1) as Node3D
	var rod_end := loader.get_node("Chassis/FrontFrame/ArmPivot/LiftRamEndL") as Node3D
	_check(rod.global_position.distance_to(rod_end.global_position) < 1.5, "lift ram follows raised arm (%.2f m)" % rod.global_position.distance_to(rod_end.global_position))
	loader.tilt_input = 1.0
	await _frames(180)
	_check(is_equal_approx(loader.tilt_angle, loader.tilt_max_deg), "bucket dumps to max")
	loader.tilt_input = -1.0
	await _frames(240)
	_check(is_equal_approx(loader.tilt_angle, loader.tilt_min_deg), "bucket curls to min")
	loader.tilt_input = 0.0
	loader.tilt_angle = 0.0  # level bucket before checking ground clearance
	loader.lift_input = -1.0
	await _frames(360)
	_check(is_equal_approx(loader.lift_angle, loader.lift_min_deg), "lift reaches min")
	_check(loader.get_bucket_tip_global().y < loader.global_position.y + 0.6, "lowered level bucket near ground (tip y=%.2f)" % (loader.get_bucket_tip_global().y - loader.global_position.y))

	# Ramp: drive from its foot up onto the first tier.
	loader.lift_input = 0.0
	loader.global_transform = Transform3D(Basis.IDENTITY, Vector3(20, 0.05, -6))
	loader.speed = 0.0
	loader.articulation = 0.0
	loader.throttle = 1.0
	await _frames(600)
	loader.throttle = 0.0
	_check(loader.global_position.y > 3.0, "climbs ramp to upper tier (y=%.2f)" % loader.global_position.y)

	level.queue_free()
	await _frames(2)
