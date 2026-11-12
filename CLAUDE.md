# Claude Code instructions — Dirt Work

## Mission
Build a playable, performant low-poly heavy-equipment game in Godot 4 (GDScript). Develop on a headless Linux server over SSH; playtest on macOS. Xbox is a possible future port, not an immediate target.

## Non-negotiable workflow
- Read README.md, docs/GAME_DESIGN.md, docs/ROADMAP.md and docs/ART_DIRECTION.md before changing gameplay or visuals.
- Work in small, reviewable increments; preserve working scenes and controls.
- Use Godot 4.x stable and GDScript; do not introduce C#/.NET, native extensions or third-party plugins without approval.
- Keep gameplay, presentation, input, and persistence separate.
- No licensed brand names, proprietary vehicle meshes, or downloaded assets without provenance.
- Make every feature work with keyboard AND controller through InputMap actions, not hard-coded device keys.
- For visual changes, use the approved reference image at `docs/image.png`, follow the render/compare/iterate process in `docs/ART_DIRECTION.md`, and record real before/after screenshots; headless tests alone are not visual QA.
- Run headless import and scene smoke tests after changes. Never claim gameplay has been visually verified unless actually played or captured.
- Do not implement thousands of rigid bodies for gravel. Start with abstract volume/weight and visually deformable piles.
- Keep a changelog of decisions in docs/DECISIONS.md; update docs/ROADMAP.md when milestones change.
- Do not commit secrets, Godot .godot cache, generated builds, or large binaries.

## Project layout
- scenes/levels — playable maps
- scenes/vehicles — vehicle scenes
- scenes/ui — menus and HUD
- scripts/vehicles — controls and vehicle simulation
- scripts/gameplay — contracts, material, economy
- scripts/core — shared state and persistence
- scripts/world — presentation-only world building (palette, low-poly batches, scenery)
- assets/models, assets/materials, assets/audio — authored assets
- tests — automated scene and logic checks
- docs — design, roadmap, architecture and decisions

## First milestone
Create a simple stylized quarry, a controllable articulated wheel loader, working lift/tilt bucket, follow camera, and a visible material loading interaction. Then add a dump-truck delivery zone and a single paid contract. Prefer a convincing playable loop over visual complexity.

## Validation commands
```bash
godot --headless --path . --editor --import --quit
godot --headless --path . --quit-after 60
```
Use the Godot executable available on the host (possibly godot4). Install export templates matching the editor version before exporting. On macOS verify input and visuals manually.
