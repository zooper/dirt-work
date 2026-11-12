# Machine grime overlay

Reference: [`docs/image.png`](../../image.png). Its machines carry dust on the tyres, wheel arches and lower panels, and the paint isn't uniform. Ours were factory-clean.

## Change
- `assets/materials/machine_grime.gdshader` is an alpha-blended `material_overlay` built from world-space height and value noise. Dust is heaviest at the ground contact and fades out by about 1.8 m. There's light dust on upward-facing surfaces and blotchy variation, mud-toned low and dust-toned higher up. It uses no textures.
- `scripts/vehicles/machine_grime.gd` (`MachineGrime`) applies the overlay to every mesh of its parent machine, skipping the operator and cab controls, and keeps `ground_y` updated so the dust stays at the wheels on ramps. It's on the DW-90, both DW-40s and the bench excavator.

## Result
`side.jpg`, `pour.jpg`, `hero.jpg`: dusty lower tyres, arches and bumpers, with the upper paint left clean.

## Limitations
- The overlay costs one extra blended pass per machine mesh, which is acceptable for a handful of machines.
- It hasn't been checked in Forward+ on the Mac.

## Follow-up: wider rock bucket and tighter hero framing
- Bucket width went from 3.45 to 3.95 m, now wider than the 3.8 m over the tyres, like the reference. The bucket also got bolt-on side cutters, a second pair of back ribs, a horizontal back band, spill-guard gussets and ten tooth adapters. The in-bucket heap and pour lip were widened to match.
- The hero camera moved 17% closer with a 42° FOV, and the pine was moved back to the left frame edge. `front34.jpg` and `hero.jpg` show the result.
