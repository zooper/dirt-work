extends SceneTree
func _initialize():
	var bucket := BucketMaterial.new()
	bucket.loads = {"sand": 4.2}
	assert(bucket.retention(-20, 0, 0, false) > bucket.retention(0, 0, 0, true))
	assert(bucket.retention(0, 6, 2, true) < bucket.retention(0, 0, 0, false))
	assert(bucket.mass() == 6720.0)
	var total := 0.0
	for i in 600:
		total += MaterialCatalog.volume(MaterialCatalog.take(bucket.loads, bucket.release_amount(1.0/60, 60, 0, 0, false)))
	assert(abs(total - 4.2) < 0.00001)
	assert(bucket.volume() < 0.00001)
	print("BUCKET TESTS PASS")
	quit()
