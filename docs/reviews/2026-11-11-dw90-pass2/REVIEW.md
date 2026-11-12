# DW-90 visual pass 2 — boom reach and linkage

Gap addressed: #2 from pass 1 (boom too short, bucket hovering over the front wheels).

Changes (`tools/blender/build_wheel_loader.py`, `tools/gen_wheel_loader.py`):
- Boom lengthened 3.45 → 4.2 m; pivot moved forward/down to (0, 2.45, -1.0) on a re-shaped loader tower, matching the reference (pivot ~70 % of the way from the rear to the front axle, at front-tyre-top height).
- Boom profile scales with length; stiffener plates, hydraulic hose runs; Z-bar lever, cross tube and tilt link repositioned; lift rams now run from low on the front frame (near the axle) to the boom underside.
- Hydraulic limits retuned for the new geometry (lift -12°..48°) so the lowered bucket still rests on the ground. Physics/collision unchanged.
- Review `hero` camera moved to the reference's near side-on rear-quarter angle.

Shots (Mobile preview renderer, fog off): `hero.jpg` (bucket raised and dumping), `side.jpg`, `front34.jpg`.
Before: `../2026-11-11-dw90-pass1/after/`.

Remaining: lighting/atmosphere, rock faces, cab interior detail, hauler + gravel loading.
