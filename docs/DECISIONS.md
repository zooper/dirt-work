# Decisions

- 2026-11-11: Godot 4 + GDScript selected for a Linux SSH/headless workflow and macOS prototype.
- 2026-11-11: Low-poly Nordic quarry chosen as first environment.
- 2026-11-11: Xbox is a future possibility; no assumption of direct Godot console export.
- 2026-11-11: Simplified gravel volume model chosen over per-stone rigid-body simulation for MVP.
- 2026-11-11: Linux dev host pinned to official Godot 4.3-stable (SHA512-verified), matching CI image barichello/godot-ci:4.3.
- 2026-11-11: Wheel loader uses a kinematic CharacterBody3D with center-articulated steering kinematics instead of VehicleBody3D/RigidBody wheels: predictable, easy to tune, cheap. Revisit if suspension feel demands it.
- 2026-11-11: Loader simulation (`WheelLoader`) is input-agnostic; `PlayerLoaderInput` maps InputMap actions onto it so tests/AI can drive it directly.
- 2026-11-11: Bucket is self-levelling (approximates parallel Z-bar linkage); tilt is relative to level, not to the arms. Bucket/arms have no world collision in M1.
- 2026-11-11: Chassis pitch/roll to the floor is visual only; collision stays upright.
- 2026-11-11: Quarry is a seeded procedural blockout from primitives (no external assets). Gravel piles are drivable convex hulls without volume accounting until M2.
