@tool
class_name Palette
extends RefCounted
## Single source of truth for the stylised, saturated colour scheme
## (warm Nordic late-afternoon). Tune the look here rather than in scenes.

const MACHINE_YELLOW := Color(0.98, 0.77, 0.10)
const MACHINE_DARK := Color(0.27, 0.28, 0.30)
const MACHINE_STEEL := Color(0.34, 0.35, 0.37)
const TIRE := Color(0.16, 0.16, 0.17)
const RAIL_RED := Color(0.85, 0.12, 0.10)
const GLASS := Color(0.35, 0.55, 0.70, 0.45)
const HIVIS := Color(0.75, 0.95, 0.15)
const BEACON := Color(1.0, 0.55, 0.05)
const LAMP := Color(1.0, 0.93, 0.75)
const TAIL := Color(1.0, 0.1, 0.05)

const GRAVEL_FLOOR := Color(0.80, 0.70, 0.56)
const GRAVEL_PILE := Color(0.58, 0.57, 0.60)
const GRAVEL_PILE_WARM := Color(0.66, 0.61, 0.57)
const ROCK := Color(0.64, 0.62, 0.65)
const ROCK_COOL := Color(0.55, 0.56, 0.64)
const ROCK_WARM := Color(0.72, 0.66, 0.62)
const GRASS := Color(0.42, 0.58, 0.28)
const GRASS_DARK := Color(0.28, 0.45, 0.22)
const PINE := Color(0.12, 0.30, 0.19)
const PINE_LIGHT := Color(0.20, 0.38, 0.23)
const TRUNK := Color(0.50, 0.33, 0.20)
const WATER := Color(0.32, 0.62, 0.84)
const MOUNTAIN := Color(0.52, 0.60, 0.74)
const SNOW := Color(0.95, 0.96, 1.0)
const FALU_RED := Color(0.66, 0.12, 0.10)
const TRIM_WHITE := Color(0.95, 0.94, 0.90)

static var _cache := {}
static var _linearize := -1


## Converts a palette (sRGB) colour to what the active renderer expects.
## Godot 4.3's Compatibility renderer reads albedo and vertex colours as linear
## (making everything pale), so we linearize there; Forward+/Mobile handle sRGB.
static func render(c: Color) -> Color:
	if _linearize < 0:
		# Only the Compatibility (OpenGL) renderer runs without a RenderingDevice.
		_linearize = 1 if RenderingServer.get_rendering_device() == null else 0
	if _linearize == 0:
		return c
	var l := c.srgb_to_linear()
	l.a = c.a
	return l


## Cached StandardMaterial3D for solid parts of machines and props.
static func mat(color: Color, roughness := 0.7, metallic := 0.0, emission := 0.0) -> StandardMaterial3D:
	var key := "%s|%s|%s|%s" % [color, roughness, metallic, emission]
	if not _cache.has(key):
		var m := StandardMaterial3D.new()
		m.albedo_color = render(color)
		m.roughness = roughness
		m.metallic = metallic
		if color.a < 1.0:
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		if emission > 0.0:
			m.emission_enabled = true
			m.emission = render(color)
			m.emission_energy_multiplier = emission
		_cache[key] = m
	return _cache[key]
