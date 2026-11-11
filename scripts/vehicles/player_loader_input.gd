class_name PlayerLoaderInput
extends Node
## Maps InputMap actions onto a WheelLoader's control fields.
## Works identically for keyboard and gamepad; see project.godot [input].

@export var enabled := true
@onready var loader: WheelLoader = get_parent() as WheelLoader


func _physics_process(_delta: float) -> void:
	if not enabled or loader == null:
		return
	loader.throttle = Input.get_action_strength("throttle")
	loader.brake = Input.get_action_strength("brake_reverse")
	loader.steer = Input.get_axis("steer_left", "steer_right")
	loader.handbrake = Input.is_action_pressed("handbrake")
	loader.lift_input = Input.get_axis("lift_down", "lift_up")
	loader.tilt_input = Input.get_axis("tilt_back", "tilt_dump")
