# Cab controls follow the inputs

Follow-up to [cab interior](../2026-11-12-cab-interior/REVIEW.md), from its gap list ("steering wheel and joystick do not move").

- The steering wheel and joystick are separate Blender parts (`steering_wheel.glb`, `joystick.glb`), each with its origin at its pivot.
- `scripts/vehicles/cab_controls.gd` (presentation only) turns the wheel 0.6 turn each side at full articulation and tips the joystick up to 18° with the lift and tilt input, smoothed.
- The `cab_dash.jpg` shot now uses 20° articulation and full lift input. In the shot the spokes and spinner knob are rotated and the arm is lifting.
- Test: "cab steering wheel turns with the articulation"; the parts check now covers 8 models.
