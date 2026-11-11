@tool
class_name Beacon
extends Node3D
## Rotating-beacon look: an emissive amber dome whose glow pulses, plus a small
## light. Presentation only.

@export var period := 0.8
@export var color := Palette.BEACON

var _mat: StandardMaterial3D
var _light: OmniLight3D
var _t := 0.0


func _ready() -> void:
	var dome := CylinderMesh.new()
	dome.top_radius = 0.07
	dome.bottom_radius = 0.11
	dome.height = 0.2
	dome.radial_segments = 8
	dome.rings = 1
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = color
	_mat.emission_enabled = true
	_mat.emission = color
	dome.material = _mat
	var mi := MeshInstance3D.new()
	mi.mesh = dome
	mi.position.y = 0.1
	add_child(mi)
	_light = OmniLight3D.new()
	_light.light_color = color
	_light.omni_range = 4.0
	_light.position.y = 0.3
	add_child(_light)


func _process(delta: float) -> void:
	_t = fmod(_t + delta, period)
	var pulse := pow(maxf(sin(_t / period * TAU), 0.0), 3.0)
	_mat.emission_energy_multiplier = 0.6 + 4.0 * pulse
	_light.light_energy = 0.15 + 1.2 * pulse
