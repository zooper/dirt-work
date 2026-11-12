class_name MaterialCatalog
extends RefCounted
## Tunable bulk-material approximations, not measured universal constants.
## Density is loose bulk kg/m³; repose is dry stable-slope degrees.
const SPECS := {
	"sand": {"density": 1600.0, "repose": 30.0, "resistance": 0.35, "flow": 3.2, "color": Color(0.70, 0.56, 0.35)},
	"gravel": {"density": 1800.0, "repose": 38.0, "resistance": 0.65, "flow": 2.2, "color": Color(0.48, 0.47, 0.44)},
	"stone": {"density": 2100.0, "repose": 44.0, "resistance": 1.0, "flow": 1.4, "color": Color(0.34, 0.38, 0.41)},
}

static func volume(loads: Dictionary) -> float:
	var result := 0.0
	for kind in loads:
		result += float(loads[kind])
	return result

static func mass(loads: Dictionary) -> float:
	var result := 0.0
	for kind in loads:
		result += float(loads[kind]) * float(SPECS[kind].density)
	return result

static func merge(into: Dictionary, from: Dictionary) -> void:
	for kind in from:
		into[kind] = float(into.get(kind, 0.0)) + float(from[kind])

static func take(loads: Dictionary, amount: float) -> Dictionary:
	var result := {}
	var total := volume(loads)
	if total <= 0.0 or amount <= 0.0:
		return result
	var fraction := minf(amount / total, 1.0)
	for kind in loads.keys():
		var v := float(loads[kind]) * fraction
		result[kind] = v
		loads[kind] = maxf(0.0, float(loads[kind]) - v)
		if loads[kind] <= 0.00000001:
			loads.erase(kind)
	return result
