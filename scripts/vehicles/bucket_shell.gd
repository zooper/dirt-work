@tool
class_name BucketShell
extends MeshInstance3D
## Loader bucket: a curved back/floor profile extruded across the width, with
## side plates, a top lip and teeth. Opening faces -Z; pivot at local origin
## (top-back of the bucket). Presentation only.

@export var width := 3.1:
	set(v): width = v; _rebuild()
@export var depth := 1.7:     ## floor length to the cutting edge
	set(v): depth = v; _rebuild()
@export var height := 1.3:
	set(v): height = v; _rebuild()
@export var teeth := 8:
	set(v): teeth = v; _rebuild()
@export var color := Color(0.40, 0.40, 0.43):
	set(v): color = v; _rebuild()
@export var edge_color := Color(0.62, 0.63, 0.66):
	set(v): edge_color = v; _rebuild()


func _ready() -> void:
	_rebuild()


## Profile in the YZ plane from the top lip, down the curved back, to the edge.
func _profile() -> PackedVector2Array:
	var p := PackedVector2Array()
	var r := height * 0.62
	var cy := -height + r
	var cz := -r * 0.35
	p.append(Vector2(0.0, -depth * 0.42))  # top lip reaching forward (y, z)
	p.append(Vector2(0.08, 0.05))          # top-back corner
	p.append(Vector2(-height * 0.25, 0.12))
	for i in 5:                              # quarter arc back -> floor
		var a := deg_to_rad(lerpf(0.0, 90.0, (i + 1) / 5.0))
		p.append(Vector2(cy - sin(a) * r, cz + cos(a) * r))
	p.append(Vector2(-height, -depth + 0.25))
	p.append(Vector2(-height + 0.05, -depth))  # cutting edge
	return p


func _rebuild() -> void:
	if not is_inside_tree():
		return
	var b := LowPolyBatch.new()
	var hw := width * 0.5
	var t := 0.09
	var prof := _profile()
	var inner_ref := Vector3(0, -height * 0.45, -depth * 0.55)
	for i in prof.size() - 1:
		var p0 := prof[i]
		var p1 := prof[i + 1]
		var a := Vector3(-hw, p0.x, p0.y)
		var bb := Vector3(hw, p0.x, p0.y)
		var c := Vector3(hw, p1.x, p1.y)
		var d := Vector3(-hw, p1.x, p1.y)
		var mid := (a + c) * 0.5
		var inward := (inner_ref - Vector3(0, mid.y, mid.z)).normalized()
		var shade := color.darkened(0.12 * (i % 2))
		b.add_quad_facing(a, bb, c, d, inward, shade.darkened(0.25))       # inside
		var off := -inward * t
		b.add_quad_facing(a + off, bb + off, c + off, d + off, -inward, shade)  # outside
	# Side plates: fan from the profile to an interior point, on both sides.
	for s in [-1.0, 1.0]:
		var x: float = s * hw
		var hub := Vector3(x, -height * 0.55, -depth * 0.45)
		for i in prof.size() - 1:
			b.add_tri_facing(Vector3(x, prof[i].x, prof[i].y), Vector3(x, prof[i + 1].x, prof[i + 1].y), hub, Vector3(s, 0, 0), color.darkened(0.05))
			b.add_tri_facing(Vector3(x, prof[i].x, prof[i].y), Vector3(x, prof[i + 1].x, prof[i + 1].y), hub, Vector3(-s, 0, 0), color.darkened(0.3))
		# Close the open front of the side plate (lip to edge).
		b.add_tri_facing(Vector3(x, prof[0].x, prof[0].y), Vector3(x, prof[prof.size() - 1].x, prof[prof.size() - 1].y), hub, Vector3(s, 0, 0), color.darkened(0.05))
		b.add_tri_facing(Vector3(x, prof[0].x, prof[0].y), Vector3(x, prof[prof.size() - 1].x, prof[prof.size() - 1].y), hub, Vector3(-s, 0, 0), color.darkened(0.3))
	# Cutting edge + teeth.
	var edge := prof[prof.size() - 1]
	for i in teeth:
		var x := lerpf(-hw + 0.2, hw - 0.2, float(i) / maxi(teeth - 1, 1))
		var tip := Vector3(x, edge.x - 0.02, edge.y - 0.32)
		var l := Vector3(x - 0.09, edge.x, edge.y + 0.02)
		var r := Vector3(x + 0.09, edge.x, edge.y + 0.02)
		var up := Vector3(x, edge.x + 0.08, edge.y)
		var dn := Vector3(x, edge.x - 0.06, edge.y)
		b.add_tri_facing(l, tip, up, Vector3(-0.5, 1, 0), edge_color)
		b.add_tri_facing(r, up, tip, Vector3(0.5, 1, 0), edge_color.lightened(0.1))
		b.add_tri_facing(l, dn, tip, Vector3(-0.5, -1, 0), edge_color.darkened(0.2))
		b.add_tri_facing(r, tip, dn, Vector3(0.5, -1, 0), edge_color.darkened(0.2))
	mesh = b.commit()
