@tool
class_name FenderArch
extends MeshInstance3D
## Curved wheel arch around the local X axis: a bent plate of `segments` facets
## from `start_deg` to `end_deg` (0 = forward/-Z, 90 = up, 180 = back/+Z).

@export var radius := 1.12:
	set(v): radius = v; _rebuild()
@export var width := 1.0:
	set(v): width = v; _rebuild()
@export var thickness := 0.08:
	set(v): thickness = v; _rebuild()
@export var start_deg := 10.0:
	set(v): start_deg = v; _rebuild()
@export var end_deg := 150.0:
	set(v): end_deg = v; _rebuild()
@export var segments := 6:
	set(v): segments = maxi(v, 1); _rebuild()
@export var color := Palette.MACHINE_DARK:
	set(v): color = v; _rebuild()


func _ready() -> void:
	_rebuild()


func _point(deg: float, r: float, x: float) -> Vector3:
	var a := deg_to_rad(deg)
	return Vector3(x, sin(a) * r, -cos(a) * r)


func _rebuild() -> void:
	if not is_inside_tree():
		return
	var b := LowPolyBatch.new()
	var hw := width * 0.5
	var ro := radius + thickness
	for i in segments:
		var a0 := lerpf(start_deg, end_deg, float(i) / segments)
		var a1 := lerpf(start_deg, end_deg, float(i + 1) / segments)
		var mid := deg_to_rad((a0 + a1) * 0.5)
		var out := Vector3(0, sin(mid), -cos(mid))
		var col := color.lightened(0.03 * (i % 2))
		b.add_quad_facing(_point(a0, ro, -hw), _point(a1, ro, -hw), _point(a1, ro, hw), _point(a0, ro, hw), out, col)
		b.add_quad_facing(_point(a0, radius, -hw), _point(a1, radius, -hw), _point(a1, radius, hw), _point(a0, radius, hw), -out, col.darkened(0.25))
		for s in [-1.0, 1.0]:
			b.add_quad_facing(_point(a0, radius, s * hw), _point(a1, radius, s * hw), _point(a1, ro, s * hw), _point(a0, ro, s * hw), Vector3(s, 0, 0), col)
	for deg in [start_deg, end_deg]:
		var a := deg_to_rad(deg)
		var tangent := Vector3(0, cos(a), sin(a)) * (-1.0 if deg == start_deg else 1.0)
		b.add_quad_facing(_point(deg, radius, -hw), _point(deg, ro, -hw), _point(deg, ro, hw), _point(deg, radius, hw), tangent, color)
	mesh = b.commit()
