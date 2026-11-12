# Showcase moved into the pit, upper-bench excavator + second hauler

Reference: [`docs/image.png`](../../image.png).

## Gap analysis (`before/hero.jpg`)
1. The loading scene stood in the open yard with conveyors and sky behind it. The reference has terraced, fractured rock walls behind the machines.
2. The excavator and second dump truck working on the upper bench (reference, top right) were missing.
3. The hero camera was close and wide-angle, so the background looked small and empty.

## Changes
- The Hauler and loading-bay dressing were rotated 90° about the hauler and moved into the pit at (4, 0, -28), in front of the north benches. The hero loader pose and camera were rotated with them.
- New `tools/blender/build_excavator.py`: a 30-t class crawler excavator ("DW-300"). It has tracks with grousers, idlers and rollers; house, counterweight and louvres; a yellow cab with tinted glass and an operator; a boom and stick with twin boom cylinders, arm and bucket cylinders and hoses; and a toothed bucket in a dig pose.
- In `quarry.tscn`, BenchExcavator (14, 14, -55) and BenchHauler (-6, 14, -54.5) stand on the second bench. `SiteProps._upper_bench()` adds a blasted-rock heap.
- The hero shot uses a 40° telephoto FOV from further back (optional 6th SHOTS field), so the benches stack up behind the machines. The pine was moved to the left frame edge.
- New `bench` review shot.

## Result
- `hero.jpg`: loader dumping into the DW-40 in front of grey faceted terraces, the excavator and second hauler on the top bench at the upper right, forest along the rim, pine on the left, and the cobble pile and boulders in the foreground. The layout now matches the reference.
- `bench.jpg`: the excavator reads correctly at mid distance, digging at the heap.

## Remaining
- The conveyors, crusher and red cabin (reference, back left) are now behind the camera, in the yard.
- The machines fill about 55% of the frame width, against about 75% in the reference.
- Dust and haze still can't be verified in the Mobile preview.

## Follow-up: in-pit feed line
- `SiteProps._pit_plant()` adds a feeder hopper by the west pile, a conveyor over the first bench to a railed transfer tower, and a second conveyor running out along the bench. A red site cabin and a floodlight stand in the pit's west side.
- `hero.jpg`: the yellow conveyors now climb behind the loader at the back left, as in the reference. The cabin is hidden behind the pine in this frame but shows in play.

## Follow-up: a visible pour
- Measured with a headless probe: at full lift and 48° tilt the bucket lip sat at y 3.2, level with the hauler rim (3.3), so the rock stream fell behind the near body wall and never showed. The particles themselves render fine (checked in a close-up debug capture).
- Changes: the hauler dump body is shallower (rim 3.15 → 2.8 m, load and side plate follow `BODY_YT`). Loader `lift_max_deg` went from 55 to 60. The rock stream got bigger, heavier and longer-lived, and the dust has more, larger and denser puffs. The hero and pour poses are now 60° lift and 40° tilt, with a longer settle time so the stream fills in.
- `pour.jpg` (new close-up) and `hero.jpg`: rock chunks and dust are visible between the lip and the rim.
