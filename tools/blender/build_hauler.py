"""Builds the DW-40 articulated hauler (6x6 dump truck) as glTF parts.

    blender -b --factory-startup --python tools/blender/build_hauler.py -- assets/models/hauler

Godot-space coordinates (x right, y up, -z forward), metres, standing on y=0,
articulation hinge at the origin. Parts:
  front.glb  tractor unit (engine hood, cab + operator, front axle housing)
  rear.glb   trailer unit (dump body with canopy, chassis, bogie housings)
  wheel.glb  one wheel, origin at its centre, axle along X
  load.glb   gravel heaped in the body (separate so it can be shown/hidden)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dw_blender import *  # noqa: F401,F403
import dw_blender

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
dw_blender.set_output(argv[0] if argv else "assets/models/hauler")

WHEEL_R = 0.98
TYRE_W = 0.85
TRACK = 1.3
FRONT_AXLE = -2.6
REAR_AXLES = (2.4, 4.1)
GRAVEL = mat("Gravel", (0.52, 0.50, 0.50), rough=0.95)
GRAVEL_LIGHT = mat("GravelLight", (0.66, 0.62, 0.58), rough=0.95)


def build_wheel():
    p = Part("HaulerWheel")
    R, W = WHEEL_R, TYRE_W
    core = R - 0.17
    segs = 32
    bm = bmesh.new()
    prof = [(0.0, R * 0.55), (0.0, R * 0.62), (W * 0.04, R * 0.80), (W * 0.1, core * 0.96), (W * 0.16, core),
            (W * 0.84, core), (W * 0.9, core * 0.96), (W * 0.96, R * 0.80), (W, R * 0.62), (W, R * 0.55)]
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new(G(x - W / 2, math.sin(a) * r, math.cos(a) * r)) for x, r in prof])
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for k in range(len(prof) - 1):
            bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
    p._finish(bm, RUBBER)
    blocks = 18
    for side in (-1, 1):
        for i in range(blocks):
            a = 2 * math.pi * (i + (0.5 if side > 0 else 0.0)) / blocks
            bm = bmesh.new()
            x0, x1 = 0.03, W * 0.5 + 0.03
            t0, t1, slant = -0.13, 0.13, 0.1
            vs = [(x0, t0, core - 0.01), (x1, t0 + slant, core - 0.01), (x1, t1 + slant, core - 0.01), (x0, t1, core - 0.01),
                  (x0, t0, R), (x1 - 0.06, t0 + slant, R - 0.03), (x1 - 0.06, t1 + slant, R - 0.03), (x0, t1, R)]
            v = [bm.verts.new(Vector((side * x, t, h))) for x, t, h in vs]
            for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                bm.faces.new([v[k] for k in f])
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(a, 4, "X"), verts=bm.verts)
            p._finish(bm, RUBBER, bevel=0.016)
    for side in (-1, 1):
        xo = side * (W / 2 - 0.02)
        p.cylinder(R * 0.56, 0.07, (xo, 0, 0), "x", YELLOW, segments=26, bevel=0.02)
        p.cylinder(R * 0.48, 0.16, (xo - side * 0.07, 0, 0), "x", YELLOW, segments=26, radius2=R * 0.44)
        p.cylinder(R * 0.25, 0.12, (xo - side * 0.04, 0, 0), "x", YELLOW, segments=18, bevel=0.02)
        p.cylinder(R * 0.13, 0.2, (xo, 0, 0), "x", YELLOW, segments=12, bevel=0.03)
        for k in range(10):
            a = 2 * math.pi * k / 10
            p.cylinder(0.028, 0.08, (xo + side * 0.02, math.sin(a) * R * 0.19, math.cos(a) * R * 0.19), "x", STEEL, segments=6)
    export(p.to_object(), "wheel.glb")


def build_front():
    """Tractor unit: engine in front of a tall cab; origin at the hinge."""
    p = Part("HaulerFront")
    y0 = WHEEL_R
    p.prism([(-0.3, 0.75), (-4.6, 0.75), (-4.8, 1.1), (-4.6, 1.6), (-0.3, 1.6)], -0.6, 0.6, DARK, bevel=0.06)   # frame
    p.box((2.3, 0.4, 0.5), (0, y0, FRONT_AXLE), DARK, bevel=0.06)
    # Engine hood: lower and sloping towards the nose.
    p.prism([(-1.85, 1.6), (-1.85, 2.75), (-2.1, 2.9), (-4.25, 2.62), (-4.65, 2.35), (-4.7, 1.6)], -1.15, 1.15, YELLOW, bevel=0.12, segments=3)
    p.box((1.3, 0.05, 1.6), (0, 2.85, -3.15), DARK, bevel=0.02)                      # hood top grille
    p.prism([(-4.55, 1.62), (-4.72, 1.62), (-4.7, 2.3), (-4.52, 2.35)], -0.85, 0.85, DARK, bevel=0.02)  # front grille
    for k in range(5):
        p.box((1.5, 0.05, 0.05), (0, 1.75 + k * 0.12, -4.73), BLACK, bevel=0.0)
    for s in (-1, 1):
        p.box((0.3, 0.2, 0.06), (s * 0.9, 2.15, -4.73), LAMP, bevel=0.015)
        p.box((0.16, 0.12, 0.06), (s * 0.9, 1.9, -4.73), AMBER, bevel=0.01)
        p.box((0.06, 0.6, 0.9), (s * 1.16, 2.2, -3.4), BLACK, bevel=0.01)             # side vents
        x0, x1 = s * (TRACK - TYRE_W / 2 - 0.05), s * (TRACK + TYRE_W / 2 + 0.07)
        p.arch((FRONT_AXLE, y0), WHEEL_R + 0.1, 0.1, min(x0, x1), max(x0, x1), 15, 165, DARK, steps=12, bevel=0.03)
        p.tube([(s * 1.25, 2.95, -1.9), (s * 1.25, 3.45, -1.9), (s * 1.25, 3.45, -0.5)], 0.03, RED)
    p.box((2.5, 0.35, 0.35), (0, 1.0, -4.85), DARK, bevel=0.05)                       # bumper
    # Cab: sits behind the hood, slightly offset like real haulers' centre cab.
    cz, FL, ROOF = -1.1, 2.2, 4.15
    p.box((2.1, 0.5, 1.9), (0, FL - 0.2, cz), DARK, bevel=0.05)
    p.box((2.05, 0.55, 1.8), (0, FL + 0.3, cz), YELLOW, bevel=0.06)
    for x in (-0.95, 0.95):
        for z in (cz - 0.85, cz + 0.85):
            p.box((0.12, ROOF - FL - 0.55, 0.12), (x, (FL + 0.55 + ROOF) / 2, z), BLACK, bevel=0.02)
    p.box((2.15, 0.2, 2.0), (0, ROOF + 0.05, cz), YELLOW, bevel=0.06)
    p.prism([(cz - 0.84, FL + 0.6), (cz - 0.8, FL + 0.6), (cz - 0.9, ROOF - 0.05), (cz - 0.94, ROOF - 0.05)], -0.9, 0.9, GLASS, bevel=0.0)
    for x in (-0.96, 0.96):
        p.box((0.02, ROOF - FL - 0.65, 1.6), (x, (FL + 0.6 + ROOF) / 2, cz), GLASS, bevel=0.0)
    p.box((1.8, ROOF - FL - 0.65, 0.02), (0, (FL + 0.6 + ROOF) / 2, cz + 0.88), GLASS, bevel=0.0)
    for s in (-1, 1):
        p.tube([(s * 1.05, ROOF - 0.4, cz - 0.8), (s * 1.45, ROOF - 0.45, cz - 1.0)], 0.025, BLACK)
        p.box((0.07, 0.4, 0.24), (s * 1.47, ROOF - 0.6, cz - 1.0), BLACK, bevel=0.03)
        p.box((0.22, 0.12, 0.04), (s * 0.7, ROOF + 0.05, cz - 1.03), LAMP, bevel=0.01)
    # Cab interior + operator.
    p.box((0.55, 0.15, 0.5), (0.1, FL + 0.6, cz + 0.25), SEAT, bevel=0.04)
    p.box((0.55, 0.7, 0.13), (0.1, FL + 1.0, cz + 0.52), SEAT, bevel=0.04)
    p.box((1.8, 0.45, 0.3), (0, FL + 0.6, cz - 0.62), DARK, bevel=0.03)
    p.box((0.44, 0.6, 0.28), (0.1, FL + 1.15, cz + 0.33), HIVIS, bevel=0.06, segments=2)
    p.box((0.24, 0.26, 0.24), (0.1, FL + 1.62, cz + 0.3), SKIN, bevel=0.06, segments=2)
    p.box((0.27, 0.08, 0.28), (0.1, FL + 1.78, cz + 0.3), CAP, bevel=0.03)
    p.tube([(0.1, FL + 0.7, cz - 0.55), (0.1, FL + 1.05, cz - 0.38)], 0.035, BLACK)
    # Ladder and step on the left.
    for z in (cz - 0.45, cz + 0.05):
        p.box((0.05, 1.6, 0.06), (-1.2, 1.3, z), YELLOW, bevel=0.01)
    for k in range(4):
        p.box((0.05, 0.05, 0.5), (-1.2, 0.7 + k * 0.38, cz - 0.2), BLACK, bevel=0.0)
    # Exhaust and hinge knuckle.
    p.cylinder(0.1, 1.2, (0.85, 3.4, -1.95), "y", BLACK, segments=10)
    p.box((0.8, 0.7, 0.6), (0, 1.25, -0.2), STEEL, bevel=0.05)
    export(p.to_object(), "front.glb")


def build_rear():
    """Trailer unit with the dump body; origin at the hinge."""
    p = Part("HaulerRear")
    y0 = WHEEL_R
    p.prism([(0.2, 0.8), (5.4, 0.8), (5.6, 1.1), (5.4, 1.75), (0.2, 1.75)], -0.65, 0.65, DARK, bevel=0.06)   # chassis
    for z in REAR_AXLES:
        p.box((2.3, 0.38, 0.45), (0, y0, z), DARK, bevel=0.06)
    p.box((2.2, 0.3, 2.4), (0, 1.55, sum(REAR_AXLES) / 2), DARK, bevel=0.05)               # bogie beam
    p.box((0.7, 0.6, 0.5), (0, 1.25, 0.25), STEEL, bevel=0.05)
    # Dump body: angular tub, sides slope outwards, floor rises at the rear.
    W0, W1 = 1.25, 1.55                    # half widths at floor / top
    Z0, Z1 = 0.25, 6.1                     # front / rear
    YF, YT = 1.9, 3.55                     # floor / top
    outer = []
    for z, yf in ((Z0, YF), (Z1 - 0.6, YF), (Z1, YF + 0.55)):
        outer += [(-W0, yf, z), (W0, yf, z)]
    for z in (Z0, Z1):
        outer += [(-W1, YT, z), (W1, YT, z)]
    p.hull(outer, YELLOW, bevel=0.08, segments=2)
    # Hollow it: dark interior "liner" just inside the top rim reads as the cavity.
    p.hull([(-W0 + 0.12, YF + 0.15, Z0 + 0.15), (W0 - 0.12, YF + 0.15, Z0 + 0.15), (-W0 + 0.12, YF + 0.15, Z1 - 0.7),
            (W0 - 0.12, YF + 0.15, Z1 - 0.7), (-W1 + 0.12, YT + 0.02, Z0 + 0.12), (W1 - 0.12, YT + 0.02, Z0 + 0.12),
            (-W1 + 0.12, YT + 0.02, Z1 - 0.12), (W1 - 0.12, YT + 0.02, Z1 - 0.12)], BUCKET, bevel=0.03)
    # Top rim and side ribs.
    for s in (-1, 1):
        p.box((0.14, 0.16, Z1 - Z0 + 0.1), (s * (W1 - 0.02), YT + 0.05, (Z0 + Z1) / 2), YELLOW, bevel=0.03)
        for z in (1.4, 2.8, 4.2, 5.4):
            p.box((0.1, YT - YF - 0.2, 0.14), (s * (W0 + 0.2), (YF + YT) / 2, z), YELLOW, bevel=0.02, rot=Matrix.Rotation(s * -0.18, 4, "Y"))
        # Dark model plate on the body front side (fictional branding goes on a Label3D in Godot).
        p.box((0.04, 0.8, 1.3), (s * (W1 - 0.04), 2.9, 1.25), DARK, bevel=0.02)
        x0, x1 = s * (TRACK - TYRE_W / 2 - 0.05), s * (TRACK + TYRE_W / 2 + 0.07)
        p.arch((REAR_AXLES[0], y0), WHEEL_R + 0.1, 0.08, min(x0, x1), max(x0, x1), 40, 140, DARK, steps=8, bevel=0.02)
        p.box((0.3, 0.2, 0.06), (s * 0.95, 1.35, 5.62), TAIL, bevel=0.015)
        p.box((0.2, 0.14, 0.06), (s * 0.6, 1.35, 5.62), AMBER, bevel=0.01)
    # Canopy reaching forward over the hinge, headboard.
    p.box((2.9, 0.18, 1.4), (0, YT + 0.15, Z0 - 0.55), YELLOW, bevel=0.05)
    p.box((2.6, YT - YF, 0.15), (0, (YF + YT) / 2 + 0.1, Z0), YELLOW, bevel=0.04)
    # Hoist cylinders.
    for s in (-1, 1):
        p.tube([(s * 0.8, 1.45, 0.6), (s * 1.05, 2.4, 1.2)], 0.1, STEEL)
    p.box((2.4, 0.28, 0.3), (0, 0.95, 5.55), DARK, bevel=0.04)                            # rear bumper
    export(p.to_object(), "rear.glb")


def build_load():
    """Angular gravel heaped in the body, plus a few loose chunks on top."""
    p = Part("HaulerLoad")
    rng = random.Random(42)
    pts = []
    for z in (0.5, 1.6, 2.8, 4.0, 5.2):
        for x in (-1.25, -0.6, 0.0, 0.6, 1.25):
            h = 3.4 + (1.1 - abs(x) * 0.6) * (1.0 - abs(z - 3.0) / 4.0) + rng.uniform(-0.12, 0.12)
            pts.append((x, h, z))
    for x in (-1.3, 1.3):
        for z in (0.45, 5.4):
            pts.append((x, 3.2, z))
    p.hull(pts, GRAVEL, bevel=0.0)
    for k in range(70):
        x, z = rng.uniform(-1.1, 1.1), rng.uniform(0.6, 5.2)
        top = 3.4 + (1.1 - abs(x) * 0.6) * (1.0 - abs(z - 3.0) / 4.0)
        s = rng.uniform(0.12, 0.28)
        p.box((s, s * 0.8, s * 1.1), (x, top + s * 0.2, z), GRAVEL_LIGHT if k % 3 else GRAVEL, bevel=s * 0.25,
              rot=Matrix.Rotation(rng.uniform(0, 6.3), 4, "Z") @ Matrix.Rotation(rng.uniform(0, 6.3), 4, "X"))
    export(p.to_object(smooth_angle=10.0), "load.glb")


build_wheel()
build_front()
build_rear()
build_load()
print("DONE", dw_blender.OUT)
