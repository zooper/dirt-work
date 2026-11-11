@tool
class_name ChamferBox
extends MeshInstance3D
## Flat-shaded box with bevelled edges and an optional tapered top — the basic
## "premium low-poly" panel for machines and props. Presentation only.

@export var size := Vector3.ONE:
	set(v): size = v; _rebuild()
@export var chamfer := 0.1:          ## bevel size in metres
	set(v): chamfer = v; _rebuild()
@export var top_scale := Vector2.ONE: ## x/z scale of the top face (taper)
	set(v): top_scale = v; _rebuild()
@export var top_shift_z := 0.0:       ## slide the top face along Z (slopes)
	set(v): top_shift_z = v; _rebuild()
@export var color := Palette.MACHINE_YELLOW:
	set(v): color = v; _rebuild()


func _ready() -> void:
	_rebuild()


func _rebuild() -> void:
	if not is_inside_tree():
		return
	var h := size * 0.5
	var c := minf(chamfer, minf(h.x, minf(h.y, h.z)) * 0.95)
	var pts := PackedVector3Array()
	for sy in [-1.0, 1.0]:
		var sc := Vector2.ONE if sy < 0.0 else top_scale
		var dz := 0.0 if sy < 0.0 else top_shift_z
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				var corner := Vector3(sx * h.x * sc.x, sy * h.y, sz * h.z * sc.y + dz)
				# Three points pulled in along each axis bevel the corner.
				pts.append(corner - Vector3(sx * c, 0, 0))
				pts.append(corner - Vector3(0, sy * c, 0))
				pts.append(corner - Vector3(0, 0, sz * c))
	var b := LowPolyBatch.new()
	var base := color
	b.add_hull(pts, color, func(_cc, n): return base.darkened(0.06 * maxf(-n.y, 0.0)))
	mesh = b.commit()
