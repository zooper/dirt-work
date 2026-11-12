# Rock faces: stepped blocks and scree aprons

Reference: [`docs/image.png`](../../image.png). Its benches are big angular blocks broken by horizontal fractures, with set-back upper blocks and gravel scree slopes at the foot of each wall. Ours were uniform full-height columns that read as stacked cubes. Compare `../2026-11-12-grade/hero.jpg` with `hero.jpg`.

## Change (`QuarryWorld`)
- On faces taller than 5 m, 60% of the columns split at a horizontal fracture. The upper block sits 0.4–1.4 m back, with its own lean, tone and chamfer plane. The upper blocks sit back from the lower ones.
- New `_scree()`: a ragged gravel slope along each inner face foot, 0.7–1.9 m up the wall and running 3–6 m out, with loose stones and convex collision so machines never clip it. The ramp foot is kept clear. The bench machines and their heap moved 1.5 m toward the bench edge.
- New detail draws use their own `_face_rng`, and the existing `_rng` draw order is unchanged, so piles, boulders, rubble and forest stay where they were.

## Result
`hero.jpg`, `overview.jpg`, `bench.jpg`: stepped, broken bench faces with light scree slopes and visible ledges. Tests pass, including the ramp climb.
