"""Builds the DW-90 wheel loader as glTF parts with Blender (headless).

    blender -b --factory-startup --python tools/blender/build_wheel_loader.py -- assets/models/wheel_loader

Everything is authored here in code (no downloaded assets). Coordinates in this
file are GODOT space: x right, y up, -z forward, metres, loader standing on y=0
with the articulation hinge at the origin. They are converted to Blender space
(x, -z, y) on the way in; the glTF exporter converts back (+Y up).

Exported parts and their origins (must match tools/gen_wheel_loader.py):
  front.glb   front frame, origin = hinge
  rear.glb    rear frame + cab + interior, origin = hinge
  operator.glb seated operator (rear-frame space), origin = hinge
  arm.glb     lift arms + Z-bar lever, origin = arm pivot
  bucket.glb  bucket, origin = bucket pin
  wheel.glb   one wheel (tyre + rim), origin = wheel centre, axle along X
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dw_blender import *  # noqa: F401,F403  (helpers, materials, Part, export, arc_pts)
import dw_blender

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
dw_blender.set_output(argv[0] if argv else "assets/models/wheel_loader")

# Proportions follow the concept art: big, wide tyres; long wheelbase; tall
# boxy engine hood; massive single-beam boom on each side.
WHEEL_R = 1.15
TYRE_W = 1.05
TRACK = 1.38
AXLE = 1.75
ARM_PIVOT = (0.0, 2.45, -1.0)    # in front-frame space (low on the tower, like the reference)
ARM_LEN = 4.2                     # pivot -> bucket pin along -z (long reach)


# ------------------------------------------------------------------ wheel ----
def build_wheel():
    """Big earthmover tyre: chunky staggered tread blocks that wrap the shoulders,
    a deep-dish rim with bolt ring and hub."""
    p = Part("Wheel")
    R, W = WHEEL_R, TYRE_W
    core = R - 0.2           # carcass radius under the blocks
    segs = 36
    bm = bmesh.new()
    prof = [(0.0, R * 0.56), (0.0, R * 0.62), (W * 0.03, R * 0.80), (W * 0.08, core * 0.96), (W * 0.15, core),
            (W * 0.85, core), (W * 0.92, core * 0.96), (W * 0.97, R * 0.80), (W, R * 0.62), (W, R * 0.56)]
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new(G(x - W / 2, math.sin(a) * r, math.cos(a) * r)) for x, r in prof])
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for k in range(len(prof) - 1):
            bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
    p._finish(bm, RUBBER)
    # Tread: 20 blocks per side, staggered half a pitch, each block runs from the
    # centre line over the shoulder (slanted), leaving deep gaps between blocks.
    blocks = 20
    for side in (-1, 1):
        for i in range(blocks):
            a = 2 * math.pi * (i + (0.5 if side > 0 else 0.0)) / blocks
            bm = bmesh.new()
            # Block profile in (x along axle, tangential t) with height h, built at angle 0 (+Blender Z).
            x0, x1 = 0.03, W * 0.5 + 0.02
            t0, t1 = -0.13, 0.13
            slant = 0.12   # chevron skew towards the shoulder
            h_in, h_out = R, R - 0.03
            vs = []
            for (x, t) in ((x0, t0), (x1, t0 + slant), (x1, t1 + slant), (x0, t1)):
                vs.append((x, t, core - 0.01))
            for (x, t, h) in ((x0, t0, h_in), (x1 - 0.08, t0 + slant, h_out), (x1 - 0.08, t1 + slant, h_out), (x0, t1, h_in)):
                vs.append((x, t, h))
            # Shoulder drop: outer-top verts pulled down/outwards over the sidewall.
            v = [bm.verts.new(Vector((side * x, t, h))) for x, t, h in vs]
            for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                bm.faces.new([v[k] for k in f])
            # Shoulder lug continuing down the sidewall.
            sx = side * (W * 0.5 - 0.04)
            sh = [bm.verts.new(Vector(c)) for c in (
                (sx, t0 + slant, core - 0.02), (sx, t1 + slant, core - 0.02), (sx, t1 + slant + 0.02, R * 0.78), (sx, t0 + slant + 0.02, R * 0.78),
                (sx + side * 0.12, t0 + slant, R - 0.05), (sx + side * 0.12, t1 + slant, R - 0.05),
                (sx + side * 0.1, t1 + slant + 0.02, R * 0.76), (sx + side * 0.1, t0 + slant + 0.02, R * 0.76))]
            for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                bm.faces.new([sh[k] for k in f])
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(a, 4, "X"), verts=bm.verts)
            p._finish(bm, RUBBER, bevel=0.018)
    # Deep-dish rim: outer lip, recessed dish, bolt ring and hub, both sides.
    for side in (-1, 1):
        xo = side * (W / 2 - 0.02)
        p.cylinder(R * 0.58, 0.07, (xo, 0, 0), "x", YELLOW, segments=28, bevel=0.02)          # lip
        p.cylinder(R * 0.50, 0.08, (xo - side * 0.12, 0, 0), "x", YELLOW, segments=28, bevel=0.02)  # dish
        p.cylinder(R * 0.53, 0.16, (xo - side * 0.06, 0, 0), "x", YELLOW, segments=28, radius2=R * 0.47)
        p.cylinder(R * 0.27, 0.12, (xo - side * 0.05, 0, 0), "x", YELLOW, segments=20, bevel=0.02)  # hub flange
        p.cylinder(R * 0.15, 0.2, (xo, 0, 0), "x", YELLOW, segments=14, bevel=0.03)                # hub cap
        for k in range(12):
            a = 2 * math.pi * k / 12
            p.cylinder(0.03, 0.08, (xo + side * 0.02, math.sin(a) * R * 0.21, math.cos(a) * R * 0.21), "x", STEEL, segments=6)
        for k in range(8):   # dish holes (dark) for depth
            a = 2 * math.pi * (k + 0.5) / 8
            p.cylinder(0.05, 0.03, (xo - side * 0.075, math.sin(a) * R * 0.38, math.cos(a) * R * 0.38), "x", DARK, segments=8)
    export(p.to_object(), "wheel.glb")


# ------------------------------------------------------------ front frame ----
def build_front():
    p = Part("FrontFrame")
    Y0 = WHEEL_R  # axle height
    # Lower frame between the front wheels and the nose.
    p.prism([(-0.25, 0.85), (-2.9, 0.85), (-3.15, 1.15), (-3.0, 1.75), (-1.3, 1.85), (-0.25, 1.7)],
            -0.6, 0.6, DARK, bevel=0.07)
    # Loader tower: tall upright carrying the boom pivots, with work lights.
    p.prism([(-0.35, 1.55), (-1.75, 1.55), (-1.95, 2.15), (-1.6, 2.78), (-0.75, 2.82), (-0.3, 2.3)],
            -0.95, 0.95, YELLOW, bevel=0.1, segments=2)
    p.prism([(-1.7, 1.7), (-2.35, 1.7), (-2.45, 2.1), (-1.8, 2.3)], -0.7, 0.7, YELLOW, bevel=0.08)   # nose block
    for s in (-1, 1):
        p.box((0.28, 0.22, 0.14), (s * 0.72, 2.9, -1.62), DARK, bevel=0.03)
        p.box((0.22, 0.15, 0.04), (s * 0.72, 2.9, -1.7), LAMP, bevel=0.01)
        p.tube([(s * 0.72, 2.75, -1.55), (s * 0.72, 2.85, -1.6)], 0.03, BLACK)
        p.box((0.24, 0.16, 0.05), (s * 0.55, 2.2, -2.02), LAMP, bevel=0.01)
        p.box((0.3, 0.22, 0.12), (s * 0.55, 2.2, -1.97), DARK, bevel=0.02)
        p.box((0.2, 0.34, 0.34), (s * 0.58, 1.55, -2.6), STEEL, bevel=0.03)   # lift ram clevis
    p.box((2.5, 0.42, 0.5), (0, Y0, -AXLE), DARK, bevel=0.07)                     # axle housing
    for s in (-1, 1):
        p.cylinder(0.28, 0.35, (s * 1.05, Y0, -AXLE), "x", STEEL, segments=12)
    # Hinge knuckles.
    p.box((0.8, 0.24, 0.6), (0, 1.75, -0.25), STEEL, bevel=0.04)
    p.box((0.8, 0.24, 0.6), (0, 1.05, -0.25), STEEL, bevel=0.04)
    p.cylinder(0.1, 1.0, (0, 1.4, -0.12), "y", WEAR, segments=8)
    # Front fenders: thick flared dark arch over the top-front of the tyre.
    for s in (-1, 1):
        x0, x1 = s * (TRACK - TYRE_W / 2 - 0.06), s * (TRACK + TYRE_W / 2 + 0.08)
        p.arch((-AXLE, Y0), WHEEL_R + 0.1, 0.12, min(x0, x1), max(x0, x1), 30, 125, DARK, steps=12, bevel=0.035)
    # Front bumper/counter plate.
    p.box((1.4, 0.4, 0.35), (0, 1.05, -3.1), DARK, bevel=0.06)
    export(p.to_object(), "front.glb")


# --------------------------------------------------------------- lift arm ----
def build_arm():
    """Origin at the boom pivot; boom runs to the bucket pin at (0, 0, -ARM_LEN).
    One massive banana-shaped beam per side plus a Z-bar tilt lever."""
    p = Part("Arm")
    L = ARM_LEN
    top = [(0.32, 0.34), (-0.26 * L, 0.27), (-0.55 * L, 0.0), (-0.8 * L, -0.08), (-L - 0.24, 0.3)]
    bot = [(-L - 0.27, -0.27), (-0.8 * L, -0.8), (-0.55 * L, -0.88), (-0.26 * L, -0.62), (0.32, -0.34)]
    for s in (-1, 1):
        p.prism(top + bot, s * 0.62, s * 1.04, YELLOW, bevel=0.08, segments=2)
        p.cylinder(0.27, 0.52, (s * 0.83, 0, 0), "x", DARK, segments=16, bevel=0.02)       # pivot boss
        p.cylinder(0.21, 0.52, (s * 0.83, 0, -L), "x", DARK, segments=16, bevel=0.02)      # bucket pin boss
        p.cylinder(0.14, 0.5, (s * 0.6, -0.68, -0.5 * L), "x", STEEL, segments=10)        # lift ram pin
        p.box((0.06, 0.4, 1.2), (s * 1.06, -0.3, -0.55 * L), YELLOW, bevel=0.02)          # stiffener plate
        p.tube([(s * 1.07, -0.1, -0.15 * L), (s * 1.07, -0.35, -0.5 * L), (s * 1.07, -0.3, -0.8 * L)], 0.025, BLACK)  # hose
    # Cross tube and the big Z-bar tilt lever.
    p.prism([(-0.52 * L, -0.74), (-0.62 * L, -0.76), (-0.63 * L, -0.15), (-0.51 * L, -0.1)], -0.64, 0.64, YELLOW, bevel=0.06)
    p.prism([(-0.54 * L, -0.5), (-0.64 * L, -0.55), (-0.6 * L, 1.35), (-0.52 * L, 1.35)], -0.24, 0.24, YELLOW, bevel=0.06, segments=2)
    p.cylinder(0.14, 0.6, (0, 1.3, -0.56 * L), "x", DARK, segments=10)
    p.cylinder(0.14, 0.6, (0, -0.48, -0.6 * L), "x", DARK, segments=10)
    # Tilt link: lever bottom -> bucket top.
    p.prism([(-0.6 * L, -0.62), (-L + 0.15, 0.2), (-L + 0.05, 0.45), (-0.58 * L, -0.35)], -0.15, 0.15, DARK, bevel=0.035)
    export(p.to_object(), "arm.glb")


# ----------------------------------------------------------------- bucket ----
def build_bucket():
    """Origin at the bucket pin; opening faces -z (forward). Big rock bucket."""
    p = Part("Bucket")
    W, H, D = 3.45, 1.6, 1.95
    back = arc_pts(-0.62, -0.72, 0.88, 160, 290, 10)
    shell = [(-D * 0.45, 0.08), (0.2, 0.12)] + [(z, y) for z, y in back[1:]] + [(-D, -H + 0.02)]
    t = 0.09
    inner = []
    for i, (z, y) in enumerate(shell):
        z0, y0 = shell[max(i - 1, 0)]
        z1, y1 = shell[min(i + 1, len(shell) - 1)]
        dz, dy = z1 - z0, y1 - y0
        ln = math.hypot(dz, dy) or 1.0
        inner.append((z - dy / ln * t, y + dz / ln * t))
    p.prism(shell + list(reversed(inner)), -W / 2 + 0.02, W / 2 - 0.02, BUCKET, bevel=0.015)
    side = [(-D * 0.45, 0.08), (0.2, 0.14)] + [(z, y) for z, y in back[1:]] + [(-D, -H), (-D * 0.85, -H + 0.28)]
    for s in (-1, 1):
        p.prism(side, s * (W / 2 - 0.07), s * (W / 2 + 0.04), BUCKET, bevel=0.025)
        p.prism([(-D * 0.4, -0.05), (-D * 0.95, -H + 0.05), (-D * 0.85, -H + 0.32), (-D * 0.35, 0.12)],
                s * (W / 2 + 0.04), s * (W / 2 + 0.1), WEAR, bevel=0.012)
        # Vertical stiffener ribs on the back.
        p.box((0.12, 1.1, 0.12), (s * 0.6, -0.55, 0.22), BUCKET, bevel=0.03)
        p.box((0.18, 0.65, 0.5), (s * 0.82, 0.05, 0.08), DARK, bevel=0.04)    # pin brackets
    p.box((W + 0.05, 0.16, 0.55), (0, 0.16, -0.18), BUCKET, bevel=0.04)          # spill guard
    p.box((0.45, 0.5, 0.4), (0, 0.36, 0.08), DARK, bevel=0.04)                  # link bracket
    p.box((W - 0.3, 0.1, 1.1), (0, -H - 0.02, -D * 0.6), WEAR, bevel=0.02)
    p.box((W - 0.05, 0.08, 0.26), (0, -H + 0.03, -D + 0.05), WEAR, bevel=0.015)
    for i in range(9):
        x = -W / 2 + 0.25 + i * (W - 0.5) / 8
        p.prism([(-D + 0.05, -H + 0.09), (-D - 0.4, -H + 0.02), (-D - 0.42, -H - 0.02), (-D + 0.05, -H - 0.05)],
                x - 0.09, x + 0.09, WEAR, bevel=0.014)
    export(p.to_object(), "bucket.glb")


# ------------------------------------------------------------ cab interior ----
CAB_Z, CAB_FL, CAB_ROOF = 1.1, 2.4, 4.3     # cab centre z, floor and roof height (rear-frame space)


def cab_interior(p, cz, FL, ROOF):
    """Operator station seen from the first-person cab camera (eye ~ (0, FL+1.52, cz+0.28)).
    Modern loader layout: slim steering pod, low dash shelf so the glass reaches the
    floor, joystick armrest console on the right, display on the right A-pillar."""
    p.box((1.62, 0.03, 1.55), (0, FL + 0.02, cz + 0.05), RUBBER, bevel=0.0)                   # floor mat
    p.box((1.7, 0.04, 1.65), (0, ROOF - 0.2, cz + 0.02), LINER, bevel=0.0)                    # headliner
    p.box((0.26, 0.025, 0.1), (0, ROOF - 0.225, cz + 0.35), LAMP, bevel=0.01)                 # dome light
    p.box((1.7, 0.55, 0.05), (0, FL + 0.3, cz + 0.83), TRIM, bevel=0.01)                      # rear wall panel
    # Interior side wall trims below the side glass, and A/B-pillar covers.
    for s in (-1, 1):
        p.box((0.05, 0.5, 1.6), (s * 0.86, FL + 0.28, cz + 0.05), INTERIOR, bevel=0.015)
        p.box((0.06, 0.08, 1.6), (s * 0.85, FL + 0.55, cz + 0.05), TRIM, bevel=0.01)          # sill trim
        for zz in (cz - 0.86, cz + 0.86):
            p.box((0.1, ROOF - FL - 0.75, 0.06), (s * 0.84, (FL + 0.55 + ROOF - 0.2) / 2, zz), TRIM, bevel=0.015)
    # Low front dash shelf with vents (stays below the eye line).
    p.prism([(cz - 0.8, FL + 0.12), (cz - 0.58, FL + 0.12), (cz - 0.58, FL + 0.44), (cz - 0.74, FL + 0.52), (cz - 0.8, FL + 0.52)],
            -0.82, 0.82, INTERIOR, bevel=0.02)
    for x in (-0.6, -0.42, 0.42, 0.6):
        p.box((0.13, 0.015, 0.07), (x, FL + 0.495, cz - 0.7), GRIP, bevel=0.0)                 # defrost vents
    # Steering pod rising from the floor, instrument cluster on top facing the operator.
    p.prism([(cz - 0.66, FL + 0.03), (cz - 0.34, FL + 0.03), (cz - 0.4, FL + 0.6), (cz - 0.62, FL + 0.66)],
            -0.21, 0.21, INTERIOR, bevel=0.03, segments=2)
    tilt = Matrix.Rotation(0.55, 4, "X")
    p.box((0.46, 0.08, 0.26), (0, FL + 0.68, cz - 0.5), TRIM, bevel=0.03, rot=tilt)            # cluster housing
    p.box((0.46, 0.06, 0.05), (0, FL + 0.74, cz - 0.62), TRIM, bevel=0.02)                    # sun hood
    p.box((0.2, 0.012, 0.11), (0, FL + 0.725, cz - 0.49), DISPLAY, bevel=0.0, rot=tilt)        # centre display
    cn = Vector((0, math.cos(0.55), math.sin(0.55)))
    for x in (-0.16, 0.16):                                                                   # round gauges
        g = Vector((x, FL + 0.715, cz - 0.49))
        p.tube([tuple(g), tuple(g + cn * 0.012)], 0.05, BLACK, segments=10)
        p.tube([tuple(g + cn * 0.01), tuple(g + cn * 0.016)], 0.04, DISPLAY, segments=10)
    for k, m in enumerate((LED_G, LED_A, LED_G, LED_A)):
        p.box((0.02, 0.012, 0.02), (-0.06 + k * 0.04, FL + 0.70, cz - 0.42), m, bevel=0.0, rot=tilt)  # tell-tales
    # Steering column, wheel with grip, hub, spokes and a spinner knob.
    wc = Vector((0, FL + 0.93, cz - 0.3))
    n = Vector((0, 0.8, 0.6)).normalized()
    u = Vector((1, 0, 0))
    v = n.cross(u).normalized()
    p.tube([(0, FL + 0.62, cz - 0.46), tuple(wc - n * 0.04)], 0.035, TRIM, segments=8)
    rw = 0.175
    ring = [tuple(wc + (u * math.cos(2 * math.pi * k / 24) + v * math.sin(2 * math.pi * k / 24)) * rw) for k in range(25)]
    p.tube(ring, 0.021, GRIP, segments=8)
    p.tube([tuple(wc - n * 0.02), tuple(wc + n * 0.025)], 0.055, TRIM, segments=10)          # hub
    for ang in (math.pi * 0.15, math.pi * 0.85, math.pi * 1.5):
        d = u * math.cos(ang) + v * math.sin(ang)
        p.tube([tuple(wc + d * 0.05), tuple(wc + d * (rw - 0.01))], 0.013, TRIM, segments=5)
    knob = wc + (u * math.cos(-0.5) + v * math.sin(-0.5)) * rw
    p.tube([tuple(knob), tuple(knob + n * 0.08)], 0.02, GRIP, segments=8)                    # spinner knob
    for x in (-0.13, 0.13):                                                                   # pedals
        p.box((0.1, 0.03, 0.18), (x, FL + 0.14, cz - 0.5), GRIP, bevel=0.0, rot=Matrix.Rotation(0.7, 4, "X"))
    p.box((0.12, 0.03, 0.2), (-0.38, FL + 0.12, cz - 0.48), GRIP, bevel=0.0, rot=Matrix.Rotation(0.7, 4, "X"))  # brake
    # Air-suspension seat.
    p.box((0.4, 0.3, 0.4), (0, FL + 0.18, cz + 0.25), TRIM, bevel=0.03)                      # pedestal
    p.box((0.6, 0.16, 0.55), (0, FL + 0.42, cz + 0.22), SEAT, bevel=0.05)
    p.box((0.58, 0.78, 0.14), (0, FL + 0.9, cz + 0.55), SEAT, bevel=0.05, rot=Matrix.Rotation(-0.15, 4, "X"))
    p.box((0.34, 0.2, 0.12), (0, FL + 1.42, cz + 0.62), SEAT, bevel=0.04)                    # headrest
    # Right armrest console: joystick, roller switches, keypad.
    p.box((0.22, 0.5, 0.7), (0.43, FL + 0.38, cz + 0.12), INTERIOR, bevel=0.03)              # console body
    p.box((0.2, 0.06, 0.62), (0.43, FL + 0.66, cz + 0.14), TRIM, bevel=0.02)                 # armrest top
    p.box((0.09, 0.04, 0.1), (0.43, FL + 0.7, cz + 0.32), GRIP, bevel=0.015)                 # armrest pad
    p.cylinder(0.02, 0.12, (0.43, FL + 0.74, cz - 0.08), "y", GRIP, segments=6)
    p.box((0.08, 0.11, 0.09), (0.43, FL + 0.84, cz - 0.09), GRIP, bevel=0.025)                # joystick
    p.box((0.03, 0.02, 0.03), (0.43, FL + 0.9, cz - 0.11), LED_A, bevel=0.0)                 # joystick button
    for k in range(3):
        p.box((0.025, 0.02, 0.045), (0.38 + k * 0.05, FL + 0.7, cz + 0.07), GRIP, bevel=0.005)  # rollers
    for k in range(6):
        p.box((0.035, 0.012, 0.035), (0.39 + (k % 2) * 0.06, FL + 0.695, cz - 0.21 + (k // 2) * 0.05),
              LED_G if k == 0 else TRIM, bevel=0.0)                                             # keypad
    # Left side: switch panel and door grab handle; right A-pillar display.
    p.box((0.04, 0.22, 0.4), (-0.82, FL + 0.66, cz - 0.15), TRIM, bevel=0.01)
    for k in range(4):
        p.box((0.02, 0.04, 0.05), (-0.8, FL + 0.7, cz - 0.3 + k * 0.1), LED_G if k == 1 else GRIP, bevel=0.0)
    p.tube([(-0.8, FL + 0.85, cz - 0.55), (-0.79, FL + 1.1, cz - 0.6)], 0.017, GRIP, segments=6)   # grab handle
    p.tube([(0.78, FL + 0.95, cz - 0.62), (0.68, FL + 1.12, cz - 0.6)], 0.02, TRIM, segments=6)
    p.box((0.2, 0.16, 0.03), (0.62, FL + 1.18, cz - 0.6), TRIM, bevel=0.01, rot=Matrix.Rotation(-0.62, 4, "Z"))
    p.box((0.17, 0.12, 0.02), (0.615, FL + 1.18, cz - 0.585), DISPLAY, bevel=0.0, rot=Matrix.Rotation(-0.62, 4, "Z"))
    # Top of the windscreen: roller-blind cassette, interior mirror, radio/overhead panel.
    p.box((1.55, 0.06, 0.07), (0, ROOF - 0.27, cz - 0.9), TRIM, bevel=0.015)
    p.box((0.22, 0.07, 0.02), (0, ROOF - 0.36, cz - 0.84), TRIM, bevel=0.01)
    p.box((0.2, 0.055, 0.012), (0, ROOF - 0.36, cz - 0.83), GLASS, bevel=0.0)
    p.box((0.7, 0.07, 0.3), (0, ROOF - 0.25, cz + 0.3), TRIM, bevel=0.03)                    # overhead panel (above the head)
    p.box(       (0.14, 0.012, 0.05), (-0.15, ROOF - 0.29, cz + 0.25), DISPLAY, bevel=0.0)      # radio
    for x in (0.12, 0.24):
        p.cylinder(0.035, 0.012, (x, ROOF - 0.29, cz + 0.3), "y", GRIP, segments=10)         # vents
    # Fire extinguisher behind the seat, left.
    p.cylinder(0.065, 0.42, (-0.6, FL + 0.32, cz + 0.68), "y", EXTING, segments=10)
    p.box((0.05, 0.06, 0.08), (-0.6, FL + 0.56, cz + 0.68), BLACK, bevel=0.01)


def build_operator():
    """Seated operator in hi-vis; separate part so the cab camera can hide him."""
    p = Part("Operator")
    FL, cz = CAB_FL, CAB_Z
    p.box((0.44, 0.2, 0.48), (0, FL + 0.6, cz + 0.05), TROUSERS, bevel=0.05)                 # thighs
    for x in (-0.12, 0.12):
        p.box((0.15, 0.46, 0.15), (x, FL + 0.3, cz - 0.22), TROUSERS, bevel=0.04)          # shins
        p.box((0.16, 0.1, 0.26), (x, FL + 0.08, cz - 0.28), BLACK, bevel=0.03)              # boots
    p.box((0.46, 0.62, 0.3), (0, FL + 1.05, cz + 0.36), HIVIS, bevel=0.07, segments=2, rot=Matrix.Rotation(-0.12, 4, "X"))
    for y in (0.9, 1.16):
        p.box((0.48, 0.05, 0.32), (0, FL + y, cz + 0.36), WEAR, bevel=0.0, rot=Matrix.Rotation(-0.12, 4, "X"))
    p.box((0.12, 0.14, 0.12), (0, FL + 1.42, cz + 0.32), SKIN, bevel=0.03)                  # neck
    p.box((0.24, 0.27, 0.25), (0, FL + 1.58, cz + 0.3), SKIN, bevel=0.07, segments=2)
    p.box((0.27, 0.08, 0.29), (0, FL + 1.74, cz + 0.3), CAP, bevel=0.03)
    p.box((0.22, 0.025, 0.12), (0, FL + 1.71, cz + 0.12), CAP, bevel=0.01)                  # cap brim
    for x in (-1, 1):
        sh = (x * 0.27, FL + 1.27, cz + 0.33)
        el = (x * 0.3, FL + 0.95, cz + 0.05)
        hd = (x * 0.15, FL + 0.98, cz - 0.28) if x < 0 else (0.43, FL + 0.86, cz - 0.05)   # left on wheel, right on joystick
        p.tube([sh, el], 0.07, HIVIS, segments=8)
        p.tube([el, hd], 0.055, HIVIS, segments=8)
        p.box((0.08, 0.08, 0.1), hd, SKIN, bevel=0.03)
    export(p.to_object(), "operator.glb")


# ------------------------------------------------------------- rear frame ----
def build_rear():
    p = Part("RearFrame")
    Y0 = WHEEL_R
    # Dark lower body (engine bay sides) and rails.
    p.prism([(0.25, 0.85), (4.4, 0.85), (4.6, 1.2), (4.5, 2.1), (0.25, 2.1)], -0.8, 0.8, DARK, bevel=0.07)
    p.box((2.5, 0.42, 0.5), (0, Y0, AXLE), DARK, bevel=0.07)
    p.box((0.6, 0.5, 0.6), (0, 1.4, 0.25), STEEL, bevel=0.05)
    # ---- Rear body: hood, flared shoulders and counterweight as one heavy mass ----
    # Engine hood (narrow upper body) with chamfered rear-top edge.
    hood = [(2.0, 2.0), (2.0, 3.35), (2.15, 3.52), (4.2, 3.52), (4.62, 3.22), (4.7, 2.0)]
    p.prism(hood, -1.05, 1.05, YELLOW, bevel=0.12, segments=3)
    p.prism([(2.2, 3.47), (4.2, 3.47), (4.5, 3.27), (4.5, 3.37), (4.2, 3.57), (2.2, 3.57)], -0.92, 0.92, DARK, bevel=0.03)
    for k in range(7):
        p.box((0.06, 0.06, 1.6), (-0.6 + k * 0.2, 3.6, 3.2), BLACK, bevel=0.0)
    # Counterweight: wide at the bumper, flaring up into the hood sides, so the
    # rear reads as one sculpted block instead of a box bolted onto the hood.
    cw = []
    for x in (-1.36, 1.36):
        cw += [(x, 0.85, 4.25), (x, 0.85, 5.05), (x, 1.05, 5.27), (x, 1.95, 5.27), (x, 2.2, 5.05), (x, 2.2, 4.25)]
    for x in (-1.06, 1.06):
        cw += [(x, 2.75, 4.25), (x, 2.75, 4.4)]   # flare stays behind the grille
    p.hull(cw, YELLOW, bevel=0.09, segments=3)
    # Shoulder flares: hood side widening down over the rear fenders.
    for s in (-1, 1):
        p.hull([(s * 1.0, 2.0, 2.05), (s * 1.0, 2.0, 4.3), (s * 1.0, 2.9, 2.05), (s * 1.0, 2.9, 4.3),
                (s * 1.42, 2.0, 2.25), (s * 1.42, 2.0, 4.25), (s * 1.3, 2.35, 2.35), (s * 1.3, 2.35, 4.2)],
               YELLOW, bevel=0.06, segments=2)
        # Dark recessed lower side panel (engine bay) with vent slots.
        p.box((0.05, 0.9, 1.35), (s * 1.38, 1.5, 3.55), DARK, bevel=0.02)
        for k in range(4):
            p.box((0.03, 0.06, 1.1), (s * 1.41, 1.25 + k * 0.17, 3.55), BLACK, bevel=0.0)
        # Rear vent panel on the hood side + panel seams.
        p.box((0.05, 0.6, 0.55), (s * 1.06, 2.95, 4.1), BLACK, bevel=0.01)
        for k in range(4):
            p.box((0.04, 0.05, 0.5), (s * 1.09, 2.75 + k * 0.13, 4.1), DARK, bevel=0.0)
        p.box((0.02, 1.2, 0.03), (s * 1.06, 2.8, 3.8), BLACK, bevel=0.0)       # vertical seam
        p.box((0.02, 0.03, 1.55), (s * 1.06, 3.3, 2.85), BLACK, bevel=0.0)     # horizontal seam
    # Rear face: dark radiator grille set into an angled yellow frame.
    p.hull([(-0.95, 2.25, 4.62), (0.95, 2.25, 4.62), (-0.95, 3.2, 4.58), (0.95, 3.2, 4.58),
            (-0.82, 2.32, 4.74), (0.82, 2.32, 4.74), (-0.82, 3.12, 4.7), (0.82, 3.12, 4.7)], DARK, bevel=0.02)
    for k in range(7):
        p.box((1.5, 0.045, 0.05), (0, 2.42 + k * 0.11, 4.76), BLACK, bevel=0.0)
    for s in (-1, 1):   # yellow grille cheeks
        p.hull([(s * 0.95, 2.2, 4.6), (s * 1.06, 2.2, 4.6), (s * 0.95, 3.25, 4.56), (s * 1.06, 3.25, 4.5),
                (s * 0.92, 2.2, 4.8), (s * 0.92, 3.2, 4.72)], YELLOW, bevel=0.02)
    # Lamps recessed into the counterweight corners, number-plate recess.
    for s in (-1, 1):
        p.box((0.36, 0.26, 0.05), (s * 1.02, 1.85, 5.255), DARK, bevel=0.01)
        p.box((0.3, 0.2, 0.06), (s * 1.02, 1.85, 5.27), TAIL, bevel=0.015)
        p.box((0.22, 0.16, 0.06), (s * 0.66, 1.85, 5.27), AMBER, bevel=0.015)
        p.box((0.2, 0.12, 0.05), (s * 1.02, 1.12, 5.26), LAMP, bevel=0.01)     # reversing lamp
    p.box((1.2, 0.35, 0.08), (0, 1.4, 5.29), DARK, bevel=0.02)
    p.box((2.4, 0.12, 0.25), (0, 0.9, 5.2), DARK, bevel=0.03)                  # bumper step
    # Rear fenders: big flared dark arches over the rear tyres.
    for s in (-1, 1):
        x0, x1 = s * (TRACK - TYRE_W / 2 - 0.06), s * (TRACK + TYRE_W / 2 + 0.1)
        p.arch((AXLE, Y0), WHEEL_R + 0.1, 0.13, min(x0, x1), max(x0, x1), 35, 170, DARK, steps=14, bevel=0.04)
        p.arch((AXLE, Y0), WHEEL_R + 0.23, 0.1, min(x0, x1) + 0.05, max(x0, x1) - 0.05, 62, 150, YELLOW, steps=10, bevel=0.035)
        p.box((0.85, 0.08, 1.3), (s * 1.38, 2.42, 0.9), STEEL, bevel=0.015)     # walkway by the cab
        p.tube([(s * 1.1, 3.6, 2.05), (s * 1.1, 4.05, 2.2), (s * 1.1, 4.05, 3.9), (s * 1.1, 3.6, 4.15)], 0.035, RED)
        p.tube([(s * 1.1, 4.05, 3.05), (s * 1.1, 3.55, 3.05)], 0.03, RED)
        p.tube([(s * 1.78, 2.45, 0.35), (s * 1.78, 3.35, 0.35), (s * 1.78, 3.35, 1.6), (s * 1.78, 2.45, 1.6)], 0.03, RED)
    # Ladder (left) in the gap between the wheels, up to the walkway.
    for z in (0.12, 0.58):
        p.box((0.06, 2.1, 0.07), (-1.5, 1.4, z), YELLOW, bevel=0.01)
    for k in range(6):
        p.box((0.05, 0.05, 0.44), (-1.5, 0.55 + k * 0.34, 0.35), DARK, bevel=0.0)
    p.tube([(-1.58, 2.5, 0.12), (-1.58, 3.5, 0.3)], 0.03, RED)
    # Exhaust stack and pre-cleaner on the hood front.
    p.cylinder(0.12, 1.15, (-0.6, 4.1, 2.45), "y", BLACK, segments=12)
    p.cylinder(0.13, 0.12, (-0.6, 4.72, 2.45), "y", BLACK, segments=12, radius2=0.1)
    p.cylinder(0.15, 0.6, (0.6, 3.85, 2.35), "y", DARK, segments=12)
    # ---- cab ----
    cz, FL, ROOF = CAB_Z, CAB_FL, CAB_ROOF
    p.prism([(cz - 1.0, FL - 0.35), (cz + 1.0, FL - 0.35), (cz + 1.0, FL), (cz - 1.0, FL)], -1.0, 1.0, DARK, bevel=0.04)
    # Lower cab panels: four walls (hollow, so the floor and pedals show inside).
    for zz in (cz - 0.945, cz + 0.945):
        p.box((1.95, 0.55, 0.06), (0, FL + 0.27, zz), YELLOW, bevel=0.025)
    for x in (-0.945, 0.945):
        p.box((0.06, 0.55, 1.95), (x, FL + 0.27, cz), YELLOW, bevel=0.025)
    p.box((1.9, 0.05, 1.9), (0, FL - 0.02, cz), DARK, bevel=0.0)                              # cab floor plate
    for x in (-0.9, 0.9):
        p.prism([(cz - 0.92, FL + 0.5), (cz - 0.78, FL + 0.5), (cz - 0.9, ROOF - 0.15), (cz - 1.04, ROOF - 0.15)], x - 0.07, x + 0.07, BLACK, bevel=0.02)
        p.prism([(cz + 0.82, FL + 0.5), (cz + 0.96, FL + 0.5), (cz + 0.96, ROOF - 0.15), (cz + 0.82, ROOF - 0.15)], x - 0.07, x + 0.07, BLACK, bevel=0.02)
        p.box((0.1, 1.3, 0.1), (x, FL + 1.15, cz + 0.1), BLACK, bevel=0.02)                  # door pillar
    p.prism([(cz - 1.2, ROOF - 0.18), (cz + 1.08, ROOF - 0.18), (cz + 1.08, ROOF), (cz + 0.85, ROOF + 0.1), (cz - 1.0, ROOF + 0.1), (cz - 1.22, ROOF - 0.05)],
            -1.08, 1.08, YELLOW, bevel=0.05, segments=2)
    p.box((1.95, 0.08, 0.14), (0, ROOF - 0.22, cz - 1.12), BLACK, bevel=0.0)
    # Glass: raked windscreen, sides, rear.
    p.prism([(cz - 0.8, FL + 0.52), (cz - 0.76, FL + 0.52), (cz - 0.9, ROOF - 0.2), (cz - 0.94, ROOF - 0.2)], -0.84, 0.84, GLASS, bevel=0.0)
    for x in (-0.9, 0.9):
        p.prism([(cz - 0.78, FL + 0.55), (cz + 0.86, FL + 0.55), (cz + 0.86, ROOF - 0.2), (cz - 0.92, ROOF - 0.2)], x - 0.012, x + 0.012, GLASS, bevel=0.0)
    p.box((1.7, ROOF - FL - 0.75, 0.03), (0, (FL + 0.55 + ROOF - 0.2) / 2, cz + 0.9), GLASS, bevel=0.0)
    p.tube([(-0.92, FL + 1.1, cz - 0.1), (-0.92, FL + 1.1, cz + 0.3)], 0.02, BLACK)
    for s in (-1, 1):
        p.tube([(s * 1.0, ROOF - 0.45, cz - 0.8), (s * 1.38, ROOF - 0.5, cz - 0.95)], 0.025, BLACK)
        p.box((0.07, 0.42, 0.26), (s * 1.4, ROOF - 0.65, cz - 0.95), BLACK, bevel=0.03)
        for zz, dz in ((cz - 1.2, -0.06), (cz + 1.08, 0.06)):
            p.box((0.3, 0.18, 0.12), (s * 0.75, ROOF + 0.02, zz), DARK, bevel=0.02)
            p.box((0.24, 0.13, 0.04), (s * 0.75, ROOF + 0.02, zz + dz), LAMP, bevel=0.01)
    # ---- Cab interior (the operator is a separate part: operator.glb) ----
    cab_interior(p, cz, FL, ROOF)
    # Exterior cab details: roof light bar, wiper.
    for x in (-0.3, 0.3):
        p.box((0.24, 0.14, 0.1), (x, ROOF + 0.02, cz - 1.2), DARK, bevel=0.02)
        p.box((0.2, 0.11, 0.04), (x, ROOF + 0.02, cz - 1.26), LAMP, bevel=0.01)
    p.tube([(-0.6, FL + 0.6, cz - 0.83), (0.15, FL + 0.62, cz - 0.83)], 0.015, BLACK, segments=5)   # parked wiper
    p.cylinder(0.14, 0.06, (-0.65, ROOF + 0.13, cz + 0.5), "y", BLACK, segments=10)          # beacon base
    export(p.to_object(), "rear.glb")


build_wheel()
build_front()
build_arm()
build_bucket()
build_rear()
build_operator()
print("DONE", dw_blender.OUT)
