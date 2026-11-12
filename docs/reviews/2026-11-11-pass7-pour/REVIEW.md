# Pass 7 — load in the bucket, pour and dust

Reference: rock heaped in the bucket pouring into the hauler with a dust cloud.

Changes:
- `WheelLoader.bucket_fill` (0..1): presentation hook only — no gameplay mechanics yet; M2 volume accounting will drive it.
- `scripts/vehicles/bucket_spill.gd` (node `Spill` under `BucketPivot`, added by `tools/gen_wheel_loader.py`): angular rock heap in the bucket when filled; when tipped past 12° while filled, a stream of rock chunks (CPUParticles3D, renderer-independent) arcs over the lip, plus a soft dust cloud (radial-gradient billboards).
- Boom lift limit raised 48° → 55° (more dump height); hauler body lowered 0.4 m and load re-heaped so the pour has room.
- Review `hero` shot: loader in a loading pose over the hauler body with the bucket part-tipped; camera at ~3.4 m so the load is visible.
- `tools/capture_shots.gd`: `DW_SHOTS=hero,side` filter for fast single-shot iterations (full set takes ~10 min on the software renderer).

Shots (Mobile preview, fog off): `hero.jpg` (pose over the body; load visible, stream subtle), `hero_loader_further.jpg` (earlier iteration where the stream is clearly visible but lands beside the body).

Limitations: the stream reads weakly at this angle because the bucket lip sits only ~1 m above the heaped load; the reference exaggerates dump height. Dust is faint without Forward+ fog/glow.
