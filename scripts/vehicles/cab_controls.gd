class_name CabControls
extends Node
## Presentation: turns the cab steering wheel with the articulation and tips the
## loader joystick with the lift/tilt inputs. Never changes gameplay state.

@export var steering_wheel_path: NodePath = ^"../Chassis/RearPivot/SteeringWheel"
@export var joystick_path: NodePath = ^"../Chassis/RearPivot/Joystick"
@export var wheel_turns_at_full_lock := 0.6   ## fraction of a turn per side
@export var joystick_max_deg := 18.0
@export var joystick_response := 12.0         ## 1/s smoothing

var _loader: WheelLoader
var _wheel: Node3D
var _stick: Node3D
var _wheel_base: Basis
var _stick_base: Basis
var _stick_tilt := Vector2.ZERO   ## x = lift (pull back), y = tilt (dump right)


func _ready() -> void:
	_loader = get_parent() as WheelLoader
	_wheel = get_node_or_null(steering_wheel_path)
	_stick = get_node_or_null(joystick_path)
	if _wheel:
		_wheel_base = _wheel.basis
	if _stick:
		_stick_base = _stick.basis


func _process(delta: float) -> void:
	if _loader == null:
		return
	if _wheel:
		var lock := deg_to_rad(_loader.max_articulation_deg)
		var spin := -(_loader.articulation / lock) * wheel_turns_at_full_lock * TAU
		_wheel.basis = _wheel_base * Basis(Vector3.UP, spin)
	if _stick:
		var target := Vector2(_loader.lift_input, _loader.tilt_input) * deg_to_rad(joystick_max_deg)
		_stick_tilt = _stick_tilt.lerp(target, clampf(joystick_response * delta, 0.0, 1.0))
		_stick.basis = _stick_base * Basis.from_euler(Vector3(_stick_tilt.x, 0.0, -_stick_tilt.y))
