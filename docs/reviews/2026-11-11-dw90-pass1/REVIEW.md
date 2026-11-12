# DW-90 visual pass 1 — integrated rear body

Reference: [`docs/image.png`](../../image.png) · Process: [`docs/ART_DIRECTION.md`](../../ART_DIRECTION.md)

## How the shots were made
- `tools/render_preview.sh` → `tools/capture_shots.gd`, 1600×900, on the Linux dev host (Xvfb + Mesa lavapipe).
- **Renderer limitation:** previews use the **Mobile** renderer with **fog disabled**, because Godot 4.3 Forward+ and fog crash on lavapipe. The project itself runs Forward+ (SSAO, SSIL, fog, glow) on the Mac, so the Mac image has more ambient occlusion, bounce light and haze than these shots.
- Views: `hero` (reference angle, bucket raised), `side`, `front34`, `front`, `rear`, `bucket_low`, `overview`, `cab`, `play` (gameplay chase camera).

## Gap analysis (before shots vs reference)
1. **Rear body reads as separate boxes** (`before/rear.jpg`, `before/hero.jpg`). The reference hood, flared rear fenders and counterweight form one sculpted mass with dark recessed lower panels and an angled grille frame; ours was a flat slab with a separate counterweight box sticking out. → **Fixed in this pass.**
2. **Boom/bucket reach and linkage** (`before/hero.jpg`). The reference boom is long and curved and carries the bucket well ahead of the machine, with visible twin lift rams and Z-bar; ours looks short, with the bucket hovering over the front wheels. → Next candidate.
3. **Lighting and environment** (`before/overview.jpg`, `before/hero.jpg`). The reference has warm golden-hour light with haze, large fractured rock planes and a working site (conveyors, hauler, gravel being loaded) around the machine; ours has cool midday light, dark banded cliffs and an empty pit floor. Partly hidden by the preview renderer (no fog), but sky/sun tuning and composition are real gaps.

## Change (single focus: rear body, `rear.glb` only)
In `tools/blender/build_wheel_loader.py`:
- New `Part.hull()` (convex hull) helper for tapered/flared panels.
- Counterweight rebuilt as one hull that is wide at the bumper and flares up into the hood sides.
- Shoulder flares widen the hood down over the rear fenders; yellow fender shells sit over the dark arches.
- Dark recessed lower side panels with vent slots, hood-side vent panel and panel seams.
- Rear radiator grille set into an angled yellow frame; lamps recessed into the counterweight corners; reversing lamps, bumper step.

No changes to pivots, node paths, collision shapes, physics, input or gameplay scripts.

## Result (after shots)
- `after/rear.jpg`: the rear is one heavy block with a large framed grille above the bumper and lamps set into the corners (previously a counterweight box bolted under a flat hood face).
- `after/hero.jpg`: side profile flows from hood to counterweight; the rear fender has a yellow shell like the reference; dark engine-bay panel under the hood.

## Remaining limitations
- Gaps 2 and 3 above are untouched (by design: one focused change per pass).
- The hull counterweight sides are slightly "puffy" at the rear shoulder; acceptable for now.
- Not yet checked on the Mac in Forward+; lift/tilt travel was not re-checked for interpenetration beyond the `hero`/`bucket_low` shots (the rear body does not move with the arms).

## Tests
`tests/check.sh`: import + boot + 34 checks, **TESTS PASSED (0 failures)**, no engine/script errors.
