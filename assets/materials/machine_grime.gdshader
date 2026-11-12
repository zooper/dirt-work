// Presentation-only grime overlay for machines (used as material_overlay).
// Quarry dust builds up low on the machine, on upward-facing surfaces and in
// blotchy patches; it fades out above `dust_height` (metres above the
// machine's ground contact). Blends over the paint; no textures required.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec3 dust_color : source_color = vec3(0.66, 0.58, 0.47);
uniform vec3 mud_color : source_color = vec3(0.36, 0.31, 0.26);
uniform float dust_height = 1.5;
uniform float ground_y = 0.0;   // world height of the machine's ground contact (set by MachineGrime)
uniform float strength : hint_range(0.0, 1.0) = 0.8;
uniform float top_dust : hint_range(0.0, 1.0) = 0.35;
uniform float noise_scale = 2.2;

varying vec3 world_pos;
varying vec3 world_nrm;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float vnoise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float h = world_pos.y - ground_y;
	float n = vnoise(world_pos * noise_scale) * 0.6 + vnoise(world_pos * noise_scale * 3.7) * 0.4;
	float low = 1.0 - smoothstep(0.15, dust_height, h + (n - 0.5) * 0.6);
	float up = smoothstep(0.55, 0.95, world_nrm.y) * top_dust * smoothstep(0.35, 0.7, n);
	float a = clamp(low * (0.45 + 0.55 * n) + up, 0.0, 1.0) * strength;
	ALBEDO = mix(mud_color, dust_color, clamp(h / max(dust_height, 0.01) + n * 0.5, 0.0, 1.0));
	ALPHA = a;
	ROUGHNESS = 0.95;
	SPECULAR = 0.2;
}
