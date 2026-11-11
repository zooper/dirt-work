class_name WheelLoader
extends CharacterBody3D
## Articulated wheel loader. Arcade-style kinematic simulation tuned for feel,
## not fidelity. The body origin sits at the articulation hinge; the front frame
## (arms + bucket) defines heading, the rear frame swings by the articulation angle.
##
## This script knows nothing about input devices: a controller node
## (see PlayerLoaderInput) writes the control fields below each frame.

# --- Controls (written by an input/AI controller, range noted) ---
var throttle := 0.0        ## 0..1
var brake := 0.0           ## 0..1 (also reverses when nearly stopped)
var steer := 0.0           ## -1 (left) .. 1 (right)
var handbrake := false
var lift_input := 0.0      ## -1 (lower) .. 1 (raise)
var tilt_input := 0.0      ## -1 (curl back) .. 1 (dump)

@export_group("Drive")
@export var max_forward_speed := 8.0     ## m/s
@export var max_reverse_speed := 4.5     ## m/s
@export var acceleration := 2.6          ## m/s^2 at full throttle
@export var brake_deceleration := 7.0    ## m/s^2 at full brake
@export var rolling_drag := 0.9          ## m/s^2 coast-down
@export var reverse_threshold := 0.4     ## m/s; below this, brake input reverses

@export_group("Steering")
@export var max_articulation_deg := 38.0
@export var articulation_rate_deg := 32.0    ## deg/s while steering
@export var auto_center_rate_deg := 18.0     ## deg/s when steer is released
@export var hinge_to_front_axle := 1.6       ## m
@export var hinge_to_rear_axle := 1.6        ## m

@export_group("Hydraulics")
@export var lift_min_deg := -18.0
@export var lift_max_deg := 52.0
@export var lift_rate_deg := 26.0
@export var tilt_min_deg := -45.0   ## curled back
@export var tilt_max_deg := 55.0    ## dumped
@export var tilt_rate_deg := 50.0
## Parallel-linkage approximation: bucket keeps its world angle while lifting.
@export var self_leveling := true

@export_group("Presentation")
@export var wheel_radius := 0.8
@export var chassis_align_speed := 6.0

var speed := 0.0                 ## signed, along front-frame forward (-Z)
var articulation := 0.0          ## radians, + = steering right
var lift_angle := 0.0            ## degrees
var tilt_angle := 0.0            ## degrees, relative to level

@onready var _chassis: Node3D = $Chassis
@onready var _rear_pivot: Node3D = $Chassis/RearPivot
@onready var _arm_pivot: Node3D = $Chassis/FrontFrame/ArmPivot
@onready var _bucket_pivot: Node3D = $Chassis/FrontFrame/ArmPivot/BucketPivot
@onready var _rear_shape: CollisionShape3D = $RearShape
@onready var _wheels: Array[Node3D] = [
	$Chassis/FrontFrame/WheelFL, $Chassis/FrontFrame/WheelFR,
	$Chassis/RearPivot/WheelRL, $Chassis/RearPivot/WheelRR,
]
var _rear_shape_offset: Vector3
var _wheel_spin := 0.0


func _ready() -> void:
	_rear_shape_offset = _rear_shape.position
	floor_snap_length = 0.6
	floor_max_angle = deg_to_rad(38.0)
	_apply_hydraulics()


func _physics_process(delta: float) -> void:
	_update_speed(delta)
	_update_articulation(delta)
	_update_heading(delta)
	_update_hydraulics(delta)

	var forward := -global_transform.basis.z
	var horizontal := forward * speed
	velocity.x = horizontal.x
	velocity.z = horizontal.z
	if is_on_floor():
		velocity.y = min(velocity.y, 0.0)
	else:
		velocity.y -= ProjectSettings.get_setting("physics/3d/default_gravity", 9.8) * delta
	move_and_slide()

	# Hitting a wall kills speed instead of sliding endlessly against it.
	if is_on_wall():
		var into_wall := -get_wall_normal().dot(forward * signf(speed))
		speed *= clampf(1.0 - into_wall, 0.0, 1.0)

	_update_presentation(delta)


func _update_speed(delta: float) -> void:
	var drive := 0.0
	if throttle > 0.0 and speed >= -reverse_threshold:
		drive += throttle * acceleration
	if brake > 0.0:
		if speed > reverse_threshold:
			drive -= brake * brake_deceleration
		else:
			drive -= brake * acceleration * 0.8   # reverse
	if throttle > 0.0 and speed < -reverse_threshold:
		drive += throttle * brake_deceleration  # throttle brakes while reversing

	speed += drive * delta
	if handbrake:
		speed = move_toward(speed, 0.0, brake_deceleration * 1.3 * delta)
	elif is_zero_approx(throttle) and is_zero_approx(brake):
		speed = move_toward(speed, 0.0, rolling_drag * delta)
	speed = clampf(speed, -max_reverse_speed, max_forward_speed)


func _update_articulation(delta: float) -> void:
	var limit := deg_to_rad(max_articulation_deg)
	if absf(steer) > 0.05:
		articulation = move_toward(articulation, steer * limit, deg_to_rad(articulation_rate_deg) * delta)
	else:
		articulation = move_toward(articulation, 0.0, deg_to_rad(auto_center_rate_deg) * delta)


## Center-articulated kinematics: front-frame yaw rate for a given hinge angle.
func _update_heading(delta: float) -> void:
	var denom := hinge_to_front_axle * cos(articulation) + hinge_to_rear_axle
	var yaw_rate := -speed * sin(articulation) / denom
	rotate_y(yaw_rate * delta)


func _update_hydraulics(delta: float) -> void:
	lift_angle = clampf(lift_angle + lift_input * lift_rate_deg * delta, lift_min_deg, lift_max_deg)
	tilt_angle = clampf(tilt_angle + tilt_input * tilt_rate_deg * delta, tilt_min_deg, tilt_max_deg)
	_apply_hydraulics()


func _apply_hydraulics() -> void:
	if _arm_pivot == null:
		return
	_arm_pivot.rotation.x = deg_to_rad(lift_angle)
	var bucket := -tilt_angle - (lift_angle if self_leveling else 0.0)
	_bucket_pivot.rotation.x = deg_to_rad(bucket)


func _update_presentation(delta: float) -> void:
	# Rear frame swings opposite to steering around the hinge.
	_rear_pivot.rotation.y = articulation
	_rear_shape.position = _rear_shape_offset.rotated(Vector3.UP, articulation)
	_rear_shape.rotation.y = articulation

	_wheel_spin += speed / wheel_radius * delta
	for w in _wheels:
		w.rotation.x = -_wheel_spin

	# Visually pitch/roll the chassis to the floor; collision stays upright.
	var target := Basis.IDENTITY
	if is_on_floor():
		var n := global_transform.basis.inverse() * get_floor_normal()
		var axis := Vector3.UP.cross(n)
		if axis.length() > 0.001:
			target = Basis(axis.normalized(), Vector3.UP.angle_to(n))
	_chassis.basis = _chassis.basis.slerp(target, clampf(chassis_align_speed * delta, 0.0, 1.0)).orthonormalized()


## Height of the bucket cutting edge in world space (handy for tests/HUD).
func get_bucket_tip_global() -> Vector3:
	return ($Chassis/FrontFrame/ArmPivot/BucketPivot/Tip as Node3D).global_position
