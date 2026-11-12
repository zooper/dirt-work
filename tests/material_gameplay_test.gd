extends SceneTree
## Integration regression: real loader input/geometry -> pile -> load -> ground.
var failures := 0
func _initialize() -> void:
	_run.call_deferred()
func check(ok: bool, label: String) -> void:
	print(("ok " if ok else "FAIL ") + label)
	if not ok:
		failures += 1
func frames(count: int) -> void:
	for i in count:
		await physics_frame
func total(game: MaterialHandling, kind: String) -> float:
	return float(game.field.total_volumes().get(kind, 0.0)) + float(game.bucket.loads.get(kind, 0.0)) + float(game.receiver.get(kind, 0.0))
func _run() -> void:
	var level: Node = load("res://scenes/levels/quarry.tscn").instantiate()
	root.add_child(level)
	var loader: WheelLoader = level.get_node("WheelLoader")
	loader.get_node("PlayerInput").enabled = false
	var game: MaterialHandling = level.get_node("MaterialHandling")
	await frames(30)
	var before := {}
	for kind in MaterialCatalog.SPECS:
		before[kind] = total(game, kind)
	# Eastern pile can be approached from the clear south pit floor.
	loader.global_position = Vector3(26, 0.05, 26)
	loader.rotation.y = 0.0
	loader.lift_angle = loader.lift_min_deg
	loader.tilt_angle = 0.0
	loader._apply_hydraulics()
	await frames(5)
	loader.throttle = 1.0
	var peak := 0.0
	for i in 300:
		await physics_frame
		peak = maxf(peak, game.bucket.volume())
	loader.throttle = 0.0
	loader.handbrake = true
	check(peak > 0.25, "real driving scoops existing pile (peak %.3fm³)" % peak)
	check(game.bucket.volume() <= game.bucket.heaped_capacity + 0.0001, "bucket capacity bounded")
	for kind in before:
		check(absf(total(game, kind) - before[kind]) < 0.0001, "drive/spill conserves " + kind)
	# Move to a clear floor location and tip the real bucket through full range.
	loader.global_position = Vector3(0, 0.05, 10)
	loader.velocity = Vector3.ZERO
	loader.speed = 0.0
	loader.lift_angle = loader.lift_max_deg
	loader.tilt_angle = loader.tilt_max_deg
	loader._apply_hydraulics()
	await frames(240)
	check(game.bucket.volume() < 0.0001, "fully tipped bucket drains to real floor")
	for kind in before:
		check(absf(total(game, kind) - before[kind]) < 0.0001, "dump conserves " + kind)
	level.queue_free()
	await process_frame
	print("MATERIAL INTEGRATION %s" % ("PASSED" if failures == 0 else "FAILED"))
	quit(1 if failures else 0)
