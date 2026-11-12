class_name BucketMaterial
extends RefCounted
## Authoritative mixed bulk load. Visual particles never own material.
var loads: Dictionary = {}
var struck_capacity := 3.0
var heaped_capacity := 4.2

func volume() -> float:
	return MaterialCatalog.volume(loads)

func mass() -> float:
	return MaterialCatalog.mass(loads)

func free_volume() -> float:
	return maxf(0.0, heaped_capacity - volume())

func retention(tilt_deg: float, acceleration: float, turning_acceleration: float, lifting: bool) -> float:
	if loads.is_empty():
		return heaped_capacity
	var repose := 0.0
	for kind in loads:
		repose += float(loads[kind]) * float(MaterialCatalog.SPECS[kind].repose)
	repose /= volume()
	# Forward tilt/acceleration reduce retention. Curling improves it. Lifting a
	# heaped bucket mobilises its surcharge, especially low-repose sand.
	var effective := tilt_deg + rad_to_deg(atan(absf(acceleration) / 9.81)) + rad_to_deg(atan(absf(turning_acceleration) / 9.81))
	var surcharge := clampf((repose - 16.0 - effective) / 24.0, 0.0, 1.0)
	if lifting:
		surcharge *= 0.35
	var body := struck_capacity * clampf((52.0 - effective) / 40.0, 0.0, 1.0)
	return body + (heaped_capacity - struck_capacity) * surcharge

func release_amount(delta: float, tilt_deg: float, acceleration: float, turning_acceleration: float, lifting: bool) -> float:
	var excess := maxf(0.0, volume() - retention(tilt_deg, acceleration, turning_acceleration, lifting))
	if excess <= 0.0:
		return 0.0
	var flow := 0.0
	for kind in loads:
		flow += float(loads[kind]) * float(MaterialCatalog.SPECS[kind].flow)
	flow /= volume()
	return minf(excess, flow * maxf(delta, 0.0))
