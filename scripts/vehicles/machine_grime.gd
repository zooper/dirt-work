class_name MachineGrime
extends Node
## Presentation: puts the shared quarry-dust overlay shader on every mesh of the
## parent machine (wheel loader, hauler, excavator). Never touches gameplay.

const SHADER := preload("res://assets/materials/machine_grime.gdshader")

@export var dust_height := 1.8     ## metres above the machine origin where dust fades out
@export var strength := 0.85
var _mat: ShaderMaterial
@export var skip_names: PackedStringArray = ["Operator", "SteeringWheel", "Joystick"]


func _ready() -> void:
	var mat := ShaderMaterial.new()
	mat.shader = SHADER
	mat.set_shader_parameter("dust_height", dust_height)
	mat.set_shader_parameter("strength", strength)
	_mat = mat
	_apply(get_parent(), mat)
	_update_ground()


func _process(_delta: float) -> void:
	_update_ground()   # machines drive up ramps; dust stays at the wheels


func _update_ground() -> void:
	var root := get_parent() as Node3D
	if root:
		_mat.set_shader_parameter("ground_y", root.global_position.y)


func _apply(node: Node, mat: ShaderMaterial) -> void:
	if skip_names.has(node.name):
		return
	if node is MeshInstance3D:
		(node as MeshInstance3D).material_overlay = mat
	for c in node.get_children():
		_apply(c, mat)
