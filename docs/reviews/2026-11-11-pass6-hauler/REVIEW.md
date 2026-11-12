# Pass 6 — DW-40 articulated hauler and the loading composition

Reference: loader (left, rear quarter) tipping into an articulated hauler (right), both facing right, warm light from the camera side, conveyors/crusher behind, cliffs at right.

Changes:
- `tools/blender/dw_blender.py`: shared Blender helpers/materials extracted from the loader script (loader output byte-identical); `Part.hull()` de-duplicates interior geometry.
- `tools/blender/build_hauler.py` → `assets/models/hauler/{front,rear,wheel,load}.glb`: 6x6 articulated hauler — low sloping hood with grille and lamps, tall cab with operator, angular dump body with canopy, ribs and model plate, tandem bogie, hoist cylinders, chunky-tread tyres, tail lamps, gravel load heaped in the body.
- `tools/gen_hauler.py` → `scenes/vehicles/hauler.tscn`: parked, loaded prop (StaticBody3D, two collision boxes) with fictional "DW-40" plates. Placed in the site yard at (-20, 0, 66).
- Sun swung to the south-east so the loading spot is front-lit (gameplay chase camera gets side light); one red cabin moved next to the crusher.
- Review `hero` shot now stages the loader in a loading pose beside the hauler (capture-only pose; gameplay unchanged).

Shots (Mobile preview, fog off): `hero.jpg`, `overview.jpg`, `play.jpg`.
Remaining vs reference: no gravel stream/dust from the bucket, foreground rock pile/pine, excavator + second truck on the upper bench, cliffs right of frame should be terraced rock faces.
