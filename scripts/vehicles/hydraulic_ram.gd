@tool
class_name HydraulicRam
extends Node3D
## Stretches between two mount points every frame (cylinder barrel + rod), so
## lift/tilt rams follow the arms without any animation data. Presentation only.

@export var base_path: NodePath
@export var end_path: NodePath
@export var barrel_radius := 0.11
@export var rod_radius := 0.06

var _barrel: MeshInstance3D
var _rod: MeshInstance3D


func _ready() -> void:
	_barrel = _cyl(barrel_radius, Palette.MACHINE_DARK)
	_rod = _cyl(rod_radius, Color(0.85, 0.86, 0.88))
	add_child(_barrel)
	add_child(_rod)


func _cyl(r: float, color: Color) -> MeshInstance3D:
	var m := CylinderMesh.new()
	m.top_radius = r
	m.bottom_radius = r
	m.height = 1.0
	m.radial_segments = 6
	m.rings = 1
	m.material = Palette.mat(color, 0.4, 0.3 if color.r > 0.5 else 0.0)
	var mi := MeshInstance3D.new()
	mi.mesh = m
	return mi


func _process(_delta: float) -> void:
	var a := get_node_or_null(base_path) as Node3D
	var b := get_node_or_null(end_path) as Node3D
	if a == null or b == null or _barrel == null:
		return
	var pa := a.global_position
	var pb := b.global_position
	var length := pa.distance_to(pb)
	if length < 0.01:
		return
	var dir := (pb - pa) / length
	var side := dir.cross(Vector3.RIGHT if absf(dir.x) < 0.9 else Vector3.FORWARD).normalized()
	var fwd := side.cross(dir)
	var barrel_len := length * 0.6
	var rod_len := length * 0.55
	_barrel.global_transform = Transform3D(Basis(side, dir * barrel_len, fwd), pa + dir * barrel_len * 0.5)
	_rod.global_transform = Transform3D(Basis(side, dir * rod_len, fwd), pb - dir * rod_len * 0.5)
