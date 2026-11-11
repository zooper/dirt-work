class_name FollowCamera
extends Node3D
## Vehicle camera with two modes (camera_switch toggles, like Farming Simulator):
##   CHASE  smoothed orbit camera behind the vehicle; mouse / look_* orbit it,
##          camera_zoom_* change distance.
##   CAB    first-person from the operator seat; mouse / look_* turn the head.
## The mouse is captured while playing (Esc releases, click recaptures). Holding
## the left mouse button hands mouse motion to the loader instead of the camera.
## On gamepad the right stick looks around unless loader_modifier (LB) is held.

enum Mode { CHASE, CAB }

@export var target_path: NodePath
@export var cab_path: NodePath = ^"../WheelLoader/Chassis/RearPivot/Cab"
@export var cab_eye := Vector3(0.0, 3.6, 0.02)  ## just in front of the operator's head
@export var distance := 11.0
@export var min_distance := 6.0
@export var max_distance := 24.0
@export var height := 5.5
@export var look_height := 1.8
@export var follow_speed := 4.0
@export var yaw_follow_speed := 2.5
@export var look_speed_deg := 110.0       ## stick/arrow look speed
@export var mouse_sensitivity := 0.18     ## degrees per pixel
@export var zoom_step := 1.5
@export var capture_mouse := true

var mode := Mode.CHASE
var orbit_yaw := 0.0     ## radians relative to behind-the-vehicle (chase)
var orbit_pitch := 0.0   ## radians, + looks down more (chase)
var head_yaw := 0.0      ## cab
var head_pitch := 0.0    ## cab
var _yaw := 0.0
@onready var _target: Node3D = get_node_or_null(target_path)
@onready var _cab: Node3D = get_node_or_null(cab_path)
@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	if capture_mouse and DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if _target:
		_yaw = _target.global_rotation.y
		global_position = _desired_position()
		_camera.look_at(_target.global_position + Vector3.UP * look_height)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.keycode == KEY_ESCAPE and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif event is InputEventMouseButton and event.pressed and capture_mouse \
			and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event is InputEventMouseMotion and not (event.button_mask & MOUSE_BUTTON_MASK_LEFT) \
			and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_look(deg_to_rad(-event.relative.x * mouse_sensitivity), deg_to_rad(event.relative.y * mouse_sensitivity))
	elif event.is_action_pressed("camera_switch"):
		mode = Mode.CAB if mode == Mode.CHASE else Mode.CHASE
		head_yaw = 0.0
		head_pitch = 0.0
		orbit_yaw = 0.0
		orbit_pitch = 0.0
	elif event.is_action_pressed("camera_zoom_in"):
		distance = maxf(distance - zoom_step, min_distance)
	elif event.is_action_pressed("camera_zoom_out"):
		distance = minf(distance + zoom_step, max_distance)


func _look(dyaw: float, dpitch: float) -> void:
	if mode == Mode.CHASE:
		orbit_yaw += dyaw
		orbit_pitch = clampf(orbit_pitch + dpitch, deg_to_rad(-25), deg_to_rad(50))
	else:
		head_yaw = clampf(head_yaw + dyaw, deg_to_rad(-150), deg_to_rad(150))
		head_pitch = clampf(head_pitch - dpitch, deg_to_rad(-60), deg_to_rad(45))


func _process(delta: float) -> void:
	if _target == null:
		return
	if not Input.is_action_pressed("loader_modifier"):
		var stick := Input.get_vector("look_left", "look_right", "look_up", "look_down")
		var speed := deg_to_rad(look_speed_deg) * delta
		_look(-stick.x * speed, stick.y * speed)
	_camera.near = 0.03 if mode == Mode.CAB else 0.05
	if mode == Mode.CAB and _cab:
		var eye := _cab.global_transform * cab_eye
		global_position = eye
		_camera.global_basis = Basis.from_euler(Vector3(head_pitch, _cab.global_rotation.y + head_yaw, 0.0))
		_camera.position = Vector3.ZERO
		return
	_yaw = lerp_angle(_yaw, _target.global_rotation.y, clampf(yaw_follow_speed * delta, 0.0, 1.0))
	global_position = global_position.lerp(_desired_position(), clampf(follow_speed * delta, 0.0, 1.0))
	_camera.position = Vector3.ZERO
	_camera.look_at(_target.global_position + Vector3.UP * look_height)


func _desired_position() -> Vector3:
	var yaw := _yaw + orbit_yaw
	var back := Vector3(sin(yaw), 0.0, cos(yaw))   # +Z is behind a -Z-forward vehicle
	var h := height + distance * sin(orbit_pitch)
	return _target.global_position + back * distance * cos(orbit_pitch) + Vector3.UP * maxf(h, 1.0)
