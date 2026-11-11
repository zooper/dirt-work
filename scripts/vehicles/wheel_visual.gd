@tool
class_name WheelVisual
extends MeshInstance3D
## Procedural low-poly tyre (staggered tread lugs) with rim and hub.
## Axle along local X. Pure presentation; spinning is done by the parent node.

@export var radius := 0.8:
	set(v): radius = v; _rebuild()
@export var width := 0.72:
	set(v): width = v; _rebuild()
@export var segments := 18:
	set(v): segments = maxi(v, 8); _rebuild()
@export var lug_depth := 0.07:
	set(v): lug_depth = v; _rebuild()
@export var rim_color := Palette.MACHINE_YELLOW:
	set(v): rim_color = v; _rebuild()


func _ready() -> void:
	_rebuild()


func _rebuild() -> void:
	if not is_inside_tree():
		return
	var b := LowPolyBatch.new()
	var hw := width * 0.5
	var r_side := radius * 0.62
	var halves := [[-hw, 0.0, 0], [0.0, hw, 1]]
	for i in segments:
		var a0 := TAU * i / segments
		var a1 := TAU * (i + 1) / segments
		var d0 := Vector3(0, cos(a0), sin(a0))
		var d1 := Vector3(0, cos(a1), sin(a1))
		for h in halves:
			var x0: float = h[0]
			var x1: float = h[1]
			var lug := (i + int(h[2])) % 2 == 0
			var r := radius if lug else radius - lug_depth
			var col := Palette.TIRE.lightened(0.04) if lug else Palette.TIRE
			# Tread band (outward normal = radial).
			b.add_quad_facing(Vector3(x0, 0, 0) + d0 * r, Vector3(x0, 0, 0) + d1 * r, Vector3(x1, 0, 0) + d1 * r, Vector3(x1, 0, 0) + d0 * r, d0 + d1, col)
			if lug:  # lug walls facing neighbours
				var rl := radius - lug_depth
				b.add_quad_facing(Vector3(x0, 0, 0) + d0 * rl, Vector3(x0, 0, 0) + d0 * r, Vector3(x1, 0, 0) + d0 * r, Vector3(x1, 0, 0) + d0 * rl, d0 - d1, Palette.TIRE)
				b.add_quad_facing(Vector3(x1, 0, 0) + d1 * rl, Vector3(x1, 0, 0) + d1 * r, Vector3(x0, 0, 0) + d1 * r, Vector3(x0, 0, 0) + d1 * rl, d1 - d0, Palette.TIRE)
		# Sidewalls (slightly bulged) and rim faces on both sides.
		var r0 := radius if i % 2 == 0 else radius - lug_depth
		var r1 := radius if (i + 1) % 2 == 0 else radius - lug_depth
		for s in [-1.0, 1.0]:
			var xo: float = s * hw
			var xm: float = s * (hw + 0.04)
			var o0 := Vector3(xo, 0, 0) + d0 * minf(r0, radius - lug_depth)
			var o1 := Vector3(xo, 0, 0) + d1 * minf(r1, radius - lug_depth)
			var m0 := Vector3(xm, 0, 0) + d0 * (radius * 0.8)
			var m1 := Vector3(xm, 0, 0) + d1 * (radius * 0.8)
			var i0 := Vector3(xo - s * 0.02, 0, 0) + d0 * r_side
			var i1 := Vector3(xo - s * 0.02, 0, 0) + d1 * r_side
			_side_quad(b, o0, o1, m1, m0, s, Palette.TIRE.lightened(0.02))
			_side_quad(b, m0, m1, i1, i0, s, Palette.TIRE.lightened(0.05))
			# Rim dish + hub.
			var c := Vector3(xo - s * 0.06, 0, 0)
			var rim_col := rim_color if i % 3 != 0 else rim_color.darkened(0.05)
			_side_tri(b, i0, i1, c + d1 * radius * 0.22, s, rim_col)
			_side_tri(b, i0, c + d1 * radius * 0.22, c + d0 * radius * 0.22, s, rim_col)
			_side_tri(b, c + d0 * radius * 0.22, c + d1 * radius * 0.22, c + Vector3(s * 0.08, 0, 0), s, Palette.MACHINE_DARK)
	mesh = b.commit()


func _side_quad(b: LowPolyBatch, p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, s: float, col: Color) -> void:
	b.add_quad_facing(p0, p1, p2, p3, Vector3(s, 0, 0), col)


func _side_tri(b: LowPolyBatch, p0: Vector3, p1: Vector3, p2: Vector3, s: float, col: Color) -> void:
	b.add_tri_facing(p0, p1, p2, Vector3(s, 0, 0), col)
