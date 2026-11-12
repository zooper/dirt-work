# Cab controls follow the inputs

Follow-up to [cab interior](../2026-11-12-cab-interior/REVIEW.md), from its gap list ("steering wheel and joystick do not move").

- The steering wheel and joystick are separate Blender parts (`steering_wheel.glb`, `joystick.glb`), each with its origin at its pivot.
- `scripts/vehicles/cab_controls.gd` (presentation only) turns the wheel 0.6 turn each side at full articulation and tips the joystick up to 18° with the lift and tilt input, smoothed.
- The `cab_dash.jpg` shot now uses 20° articulation and full lift input. In the shot the spokes and spinner knob are rotated and the arm is lifting.
- Test: "cab steering wheel turns with the articulation"; the parts check now covers 8 models.

## Follow-up: cab header
The eye point moved from y 3.92 to 3.84. The roller-blind cassette is tucked under the roof, and the dash shelf is raised and widened so it covers the lower cab wall. In `cab.jpg` the roof header drops from about 15% to about 12% of the view.
