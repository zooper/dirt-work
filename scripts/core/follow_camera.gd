class_name FollowCamera
extends Node3D
## Smoothed chase camera with orbit (camera_orbit_left/right) and reset (camera_reset).
## Lives outside the vehicle so it can lag behind and never inherits chassis tilt.

@export var target_path: NodePath
@export var distance := 11.0
@export var height := 5.5
@export var look_height := 1.8
@export var follow_speed := 4.0
@export var yaw_follow_speed := 2.5
@export var orbit_speed_deg := 90.0

var orbit_offset := 0.0   ## radians relative to behind-the-vehicle
var _yaw := 0.0
@onready var _target: Node3D = get_node_or_null(target_path)
@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	if _target:
		_yaw = _target.global_rotation.y
		_snap()


func _process(delta: float) -> void:
	if _target == null:
		return
	orbit_offset += Input.get_axis("camera_orbit_left", "camera_orbit_right") * deg_to_rad(orbit_speed_deg) * delta
	if Input.is_action_just_pressed("camera_reset"):
		orbit_offset = 0.0
	_yaw = lerp_angle(_yaw, _target.global_rotation.y, clampf(yaw_follow_speed * delta, 0.0, 1.0))
	global_position = global_position.lerp(_desired_position(), clampf(follow_speed * delta, 0.0, 1.0))
	_camera.look_at(_target.global_position + Vector3.UP * look_height)


func _desired_position() -> Vector3:
	var yaw := _yaw + orbit_offset
	var back := Vector3(sin(yaw), 0.0, cos(yaw))   # +Z is behind a -Z-forward vehicle
	return _target.global_position + back * distance + Vector3.UP * height


func _snap() -> void:
	global_position = _desired_position()
	_camera.look_at(_target.global_position + Vector3.UP * look_height)
