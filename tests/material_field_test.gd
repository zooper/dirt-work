extends SceneTree
func _initialize() -> void:
	var field := MaterialField.new()
	field.seed_pile(Vector3.ZERO, 4.0, 3.0, "sand")
	field.seed_pile(Vector3(3,0,0), 2.0, 2.0, "gravel")
	var before := field.total_volumes()
	var taken := field.scoop_at(Vector3(0,0.3,0), 2.0, 1.0, 1.5)
	assert(MaterialCatalog.volume(taken) > 0.0)
	assert(MaterialCatalog.volume(taken) <= 1.50000001)
	assert(not field.deposit_at(Vector3(100,0,0), taken))
	assert(field.deposit_at(Vector3(8,0,0), taken))
	for i in range(200):
		field.relax(192)
	for kind in before:
		assert(absf(field.total_volumes()[kind]-before[kind]) < 0.000001)
	assert(field.scoop_at(Vector3(0,100,0),2,2,5).is_empty())
	assert(not field.deposit_at(Vector3.ZERO,{"sand":-1.0}))
	field.rebuild_visuals()
	print("PASS field scoop/deposit, closed bounds, invalid loads, air scoop, 38400 relaxation updates mass-conserved")
	field.free()
	quit()
