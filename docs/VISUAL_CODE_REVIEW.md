# Code review — visual pipeline (2026-11-11)

Scope: remote inspection of repository files through GitHub integration, **not** a local clone or executed test run. Current reviewed commits include `2c75bbe` (quarry) and `ca50841` (DW-90 geometry). Findings require local validation.

## What is already in place
- `tools/blender/build_wheel_loader.py` generates separate GLB meshes for rear, front, arm, bucket and wheel, using a consistent coordinate conversion.
- `tools/gen_wheel_loader.py` assembles the scene and defines stable node paths for the moving components.
- `scripts/vehicles/wheel_loader.gd` separates device input from movement and articulates the front/rear frames around the hinge.
- `scripts/world/quarry_world.gd` procedurally builds terraced rock faces and gravel details with deterministic seeds.
- `project.godot` now requests Forward+ rendering; `tools/capture_shots.gd` and `tools/render_preview.sh` support screenshot review.

## Prioritized observations
1. **Visual QA gap (high):** headless import and tests cannot prove the model looks like the reference. Add repeatable three-quarter, side, cab and bucket-up review shots with before/after comparison.
2. **Model generator ownership (high):** DW-90 visuals are generated in Blender and scene assembly Python. Edit the generators, not only the generated `.tscn` or GLBs; keep the rig node names and pivots stable.
3. **Material/lighting consistency (medium):** Blender's sRGB-to-linear conversion, Godot's Forward+ material import and procedural world colors should be reviewed in actual rendered output to avoid inconsistent brightness or washed-out colors. Do not change color math speculatively.
4. **Performance (medium):** 4096 directional shadows, SSAO, dense rubble and detailed tires may be expensive on some Macs. Profile real hardware before declaring a performance target met.
5. **World composition (medium):** procedural noise and scattered rubble alone will not create the industrial layout in the concept. Deliberately place working terraces, conveyors, crusher, floodlights and access roads in one showcase zone.
6. **Collision/visual separation (medium):** `WheelLoader` is a `CharacterBody3D` with simple shapes; visual changes must not inadvertently alter collision or steering behavior. The simulation is arcade-style, not full rigid-body vehicle physics.
7. **Scope discipline (medium):** README and roadmap correctly identify macOS playtesting as pending. Avoid adding another vehicle until a focused DW-90 visual review and controller playtest are complete.

## Recommended next PR
- Add reproducible screenshot views (three-quarter, side, front, cab, bucket travel).
- Capture before shots from the current `main`.
- Fix the three largest visual discrepancies against `docs/ART_DIRECTION.md`.
- Attach after shots, state any remaining limitations and run `tests/check.sh`.
