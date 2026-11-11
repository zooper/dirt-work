class_name PlayerLoaderInput
extends Node
## Maps InputMap actions onto a WheelLoader's control fields.
## Default layout follows Farming Simulator conventions:
##   keyboard  W/S drive, A/D steer, J/N arm up/down, K/M bucket curl/dump,
##             hold left mouse + move mouse = arm (Y) / bucket (X),
##             3 cruise on/off, 1/2 cruise slower/faster, Space handbrake
##   gamepad   RT/LT drive, left stick steer, hold LB + right stick = loader,
##             Y cruise, D-pad left/right cruise speed, A handbrake

@export var enabled := true
@export var mouse_loader_sensitivity := 0.06  ## per pixel of mouse motion
@export var cruise_step := 0.5                 ## m/s per press

@onready var loader: WheelLoader = get_parent() as WheelLoader
var _mouse_lift := 0.0
var _mouse_tilt := 0.0


func _unhandled_input(event: InputEvent) -> void:
	if not enabled or loader == null:
		return
	if event is InputEventMouseMotion and (event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		_mouse_lift += -event.relative.y * mouse_loader_sensitivity
		_mouse_tilt += event.relative.x * mouse_loader_sensitivity
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("cruise_toggle"):
		loader.cruise_active = not loader.cruise_active
		if loader.cruise_active:
			loader.cruise_speed = clampf(maxf(loader.speed, 2.0), 1.0, loader.max_forward_speed)
	elif event.is_action_pressed("cruise_faster"):
		loader.cruise_speed = minf(loader.cruise_speed + cruise_step, loader.max_forward_speed)
	elif event.is_action_pressed("cruise_slower"):
		loader.cruise_speed = maxf(loader.cruise_speed - cruise_step, 0.5)


func _physics_process(_delta: float) -> void:
	if not enabled or loader == null:
		return
	loader.throttle = Input.get_action_strength("throttle")
	loader.brake = Input.get_action_strength("brake_reverse")
	loader.steer = Input.get_axis("steer_left", "steer_right")
	loader.handbrake = Input.is_action_pressed("handbrake")

	var lift := Input.get_axis("lift_down", "lift_up")
	var tilt := Input.get_axis("tilt_back", "tilt_dump")
	if Input.is_action_pressed("loader_modifier"):
		lift += Input.get_axis("loader_stick_down", "loader_stick_up")
		tilt += Input.get_axis("loader_stick_left", "loader_stick_right")
	lift += _mouse_lift
	tilt += _mouse_tilt
	_mouse_lift = 0.0
	_mouse_tilt = 0.0
	loader.lift_input = clampf(lift, -1.0, 1.0)
	loader.tilt_input = clampf(tilt, -1.0, 1.0)
