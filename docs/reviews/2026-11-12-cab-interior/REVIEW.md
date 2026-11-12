# Cab interior pass

Reference: [`docs/image.png`](../../image.png) (operator in hi-vis visible through the glass) and playtest feedback (Mac, Forward+ cab-view screenshot: "not happy with inside the cabin").

## How the shots were made
`DW_SHOTS=cab,cab_detail tools/render_preview.sh <dir>` (Xvfb + lavapipe, Mobile renderer, no fog/SSAO/SSIL). `cab_dash` is new: the cab camera pitched down 0.6 rad onto the controls.

## Gap analysis (before)
1. The camera sat in front of the operator's face, so his hi-vis arms and hands filled the lower view (Mac screenshot).
2. The dashboard was a full-width black slab with large emissive tell-tales that bloomed into white/amber blobs.
3. The steering wheel was a coarse 14-segment ring, too close to the eye.
4. The solid lower cab box covered the floor, so the cab looked like it was filled with yellow up to the glass line (`after/cab_dash.jpg` mid-pass).
5. With no fill light, everything inside rendered near-black.

## Changes
- `build_wheel_loader.py`: new `cab_interior()` with a slim steering pod and an angled instrument cluster (two round gauges, centre display, small LED tell-tales). A 24-segment wheel with hub, three spokes and a spinner knob. A low dash shelf with defrost vents, so the glass reaches down. The right armrest console has a joystick, rollers and a keypad. There's a display on the right A-pillar, a left switch panel and grab handle, interior side trims, pillar covers, a roller-blind cassette and an interior mirror. The overhead panel sits above the head, and there's a fire extinguisher. The lower cab is now four walls plus a floor plate (hollow). New interior materials are mid-grey plastic, dark trim and grip, and displays and LEDs with low emission.
- Operator split into `operator.glb`. His right hand is now on the joystick and his left on the wheel.
- `follow_camera.gd`: `cab_eye` moved to the operator's eye point (0, 3.92, 0.27). In cab view the operator is set to shadow-only, and the default pitch is -0.2.
- `gen_wheel_loader.py`: `Operator` instance and `CabFill` OmniLight3D (0.6 energy, 1.05 m range, no shadow).

## Result
- `after/cab.jpg`: clear windscreen view of the front frame and boom, top of the steering wheel at the bottom edge, pillar display on the right. No arms in view.
- `after/cab_dash.jpg`: readable gauges, display, LEDs, joystick console and pedal area instead of a black slab.
- `after/cab_detail.jpg`: the operator is still visible from outside, with his hand on the joystick.

## Remaining limitations
- Not checked on the Mac in Forward+. SSIL will brighten the interior further, so `CabFill` may need to come down.
- The windscreen top header (roof and blind cassette) still takes about 15% of the cab view.
- No animated steering wheel or joystick yet: they do not move with the inputs.

## Tests
`tests/check.sh`: TESTS PASSED (0 failures).
