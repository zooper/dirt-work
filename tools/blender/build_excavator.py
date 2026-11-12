"""Builds a 30-t class crawler excavator ("DW-300") as one posed glTF prop.

    blender -b --factory-startup --python tools/blender/build_excavator.py -- assets/models/excavator

Background prop for the upper quarry bench (reference: digging on the top bench).
Godot-space coordinates (x right, y up, -z forward = boom direction), metres,
standing on y=0, origin at the slew centre. Static pose: bucket down in a pile.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dw_blender import *  # noqa: F401,F403
import dw_blender

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
dw_blender.set_output(argv[0] if argv else "assets/models/excavator")

TRACK_L, TRACK_W, GAUGE, TRACK_H = 4.6, 0.65, 2.6, 0.95


def beam(p, a, b, half, x0, x1, m, taper=1.0, bevel=0.05):
    """Straight box beam in the (z, y) plane from a to b, half-height `half`."""
    dz, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dz, dy)
    nz, ny = -dy / L, dz / L
    h2 = half * taper
    p.prism([(a[0] + nz * half, a[1] + ny * half), (b[0] + nz * h2, b[1] + ny * h2),
             (b[0] - nz * h2, b[1] - ny * h2), (a[0] - nz * half, a[1] - ny * half)], x0, x1, m, bevel=bevel)


def build():
    p = Part("Excavator")
    # ---- Undercarriage: two crawler tracks with idlers, rollers and grousers.
    for s in (-1, 1):
        x = s * GAUGE / 2
        x0, x1 = x - TRACK_W / 2, x + TRACK_W / 2
        r = TRACK_H / 2
        prof = arc_pts(-TRACK_L / 2 + r, r, r, -90, 90, 6)
        back = arc_pts(TRACK_L / 2 - r, r, r, 90, 270, 6)
        p.prism(prof + back, x0, x1, RUBBER, bevel=0.03, segments=1)
        for k in range(15):   # grousers along the top run
            z = -TRACK_L / 2 + r + k * (TRACK_L - 2 * r) / 14
            p.box((TRACK_W + 0.02, 0.05, 0.08), (x, TRACK_H + 0.01, z), BLACK, bevel=0.0)
        p.box((0.25, 0.45, TRACK_L - 1.0), (x - s * 0.02, r, 0), DARK, bevel=0.04)          # track frame
        for z in (-TRACK_L / 2 + r, TRACK_L / 2 - r):
            p.cylinder(r * 0.72, TRACK_W + 0.05, (x, r, z), "x", STEEL, segments=12)        # idler / sprocket
        for k in range(5):
            p.cylinder(0.14, TRACK_W * 0.6, (x, 0.2, -1.4 + k * 0.7), "x", STEEL, segments=8)
    p.box((GAUGE - 0.4, 0.5, 1.4), (0, 0.75, 0), DARK, bevel=0.05)                          # car body
    p.cylinder(1.05, 0.25, (0, 1.12, 0), "y", BLACK, segments=16)                           # slew ring
    # ---- Upper structure: deck, engine house, counterweight, cab on the left front.
    p.box((2.9, 0.22, 3.9), (0, 1.36, 0.35), DARK, bevel=0.04)                              # deck
    p.hull([(-1.45, 1.47, 0.0), (1.45, 1.47, 0.0), (-1.45, 1.47, 2.25), (1.45, 1.47, 2.25),
            (-1.4, 2.55, 0.1), (1.4, 2.55, 0.1), (-1.4, 2.55, 1.7), (1.4, 2.55, 1.7)], YELLOW, bevel=0.08)  # engine hood
    p.hull([(-1.45, 1.25, 1.8), (1.45, 1.25, 1.8), (-1.45, 1.25, 2.45), (1.45, 1.25, 2.45),
            (-1.42, 2.5, 1.7), (1.42, 2.5, 1.7), (-1.35, 2.35, 2.45), (1.35, 2.35, 2.45)], YELLOW, bevel=0.12, segments=3)  # counterweight
    for k in range(5):
        p.box((0.06, 0.03, 0.9), (0.2 + k * 0.2, 2.56, 0.95), BLACK, bevel=0.0)              # hood louvres
    p.box((0.4, 0.5, 0.06), (1.46, 1.95, 0.9), BLACK, bevel=0.01)                            # side grille
    p.cylinder(0.08, 0.6, (0.75, 2.85, 0.5), "y", BLACK, segments=10)                        # exhaust
    p.prism([(-1.65, 1.47), (0.0, 1.47), (0.0, 2.15), (-1.65, 2.15)], 0.25, 1.45, YELLOW, bevel=0.05)  # right front toolbox
    # Cab (left front).
    cx0, cx1 = -1.45, -0.45
    p.prism([(-1.75, 1.47), (-0.1, 1.47), (-0.1, 3.15), (-1.35, 3.15), (-1.75, 2.6)], cx0, cx1, YELLOW, bevel=0.04)
    p.prism([(-1.72, 2.05), (-1.4, 3.05), (-1.36, 3.05), (-1.68, 2.05)], cx0 + 0.04, cx1 - 0.04, TINT, bevel=0.0)  # windscreen
    p.prism([(-1.62, 2.05), (-0.25, 2.05), (-0.25, 3.02), (-1.32, 3.02), (-1.62, 2.55)], cx0 - 0.01, cx0 + 0.01, TINT, bevel=0.0)
    p.prism([(-1.62, 2.05), (-0.25, 2.05), (-0.25, 3.02), (-1.32, 3.02), (-1.62, 2.55)], cx1 - 0.01, cx1 + 0.01, TINT, bevel=0.0)
    p.box((1.08, 0.08, 1.72), (-0.95, 3.18, -0.92), YELLOW, bevel=0.03)                      # roof
    p.box((0.5, 0.7, 0.4), (-0.95, 2.45, -0.6), HIVIS, bevel=0.06)                           # operator
    p.box((0.22, 0.24, 0.22), (-0.95, 2.95, -0.62), SKIN, bevel=0.05)
    p.box((0.16, 0.1, 0.12), (-0.95, 3.27, -0.6), LAMP, bevel=0.01)                          # work lamp
    p.cylinder(0.08, 0.12, (-0.6, 3.28, -0.3), "y", AMBER, segments=8)                       # beacon
    p.tube([(0.3, 2.15, -1.6), (0.3, 2.75, -1.6), (1.4, 2.75, -1.6), (1.4, 2.65, 0.0)], 0.025, RED)  # handrail
    # ---- Front attachment: boom, stick, bucket and their cylinders (x around +0.05).
    bx0, bx1 = -0.3, 0.3
    P0, P1, P2 = (-1.55, 1.9), (-4.1, 4.75), (-6.0, 4.35)      # boom foot, knee, nose
    P3 = (-6.9, 1.15)                                           # stick tip (bucket pin)
    beam(p, P0, P1, 0.32, bx0, bx1, YELLOW, taper=1.15)
    beam(p, P1, P2, 0.37, bx0, bx1, YELLOW, taper=0.7)
    p.cylinder(0.28, 0.7, (0, P1[1], P1[0]), "x", YELLOW, segments=12)                       # knee boss
    beam(p, (P2[0] + 0.25, P2[1] + 0.5), P3, 0.26, bx0 + 0.04, bx1 - 0.04, YELLOW, taper=0.6)  # stick
    for s in (-1, 1):                                                                        # boom cylinders
        p.tube([(s * 0.42, 1.65, -1.45), (s * 0.42, 3.0, -3.2)], 0.13, YELLOW, segments=10)
        p.tube([(s * 0.42, 3.0, -3.2), (s * 0.42, 3.75, -4.15)], 0.07, WEAR, segments=8)
    p.tube([(0, 5.3, -4.0), (0, 5.4, -5.3)], 0.12, YELLOW, segments=10)                       # arm cylinder
    p.tube([(0, 5.4, -5.3), (0, 5.15, -6.0)], 0.065, WEAR, segments=8)
    p.tube([(0, 4.3, -6.35), (0, 2.6, -6.95)], 0.09, YELLOW, segments=8)                     # bucket cylinder
    p.tube([(0, 2.6, -6.95), (0, 1.75, -7.15)], 0.05, WEAR, segments=8)
    for k in range(3):                                                                       # hoses along the boom
        off = -0.12 + k * 0.12
        p.tube([(off, 2.35, -1.8), (off, 5.1, -4.0), (off, 4.75, -5.8)], 0.03, BLACK, segments=5)
    # Bucket: curled shell with teeth, open side facing the machine (digging stroke).
    W = 1.5
    shell = arc_pts(P3[0] - 0.45, P3[1] - 0.55, 0.75, 200, 340, 7)
    shell_in = arc_pts(P3[0] - 0.45, P3[1] - 0.55, 0.65, 340, 200, 7)
    p.prism(shell + shell_in, -W / 2, W / 2, BUCKET, bevel=0.02, segments=1)
    for s in (-1, 1):
        p.hull([(s * W / 2, P3[1], P3[0]), (s * W / 2, P3[1] - 1.2, P3[0] - 0.2), (s * W / 2, P3[1] - 0.7, P3[0] - 1.15),
                (s * (W / 2 - 0.05), P3[1], P3[0]), (s * (W / 2 - 0.05), P3[1] - 1.2, P3[0] - 0.2),
                (s * (W / 2 - 0.05), P3[1] - 0.7, P3[0] - 1.15)], BUCKET, bevel=0.01)
    for k in range(5):
        x = -W / 2 + 0.15 + k * (W - 0.3) / 4
        p.hull([(x - 0.06, P3[1] - 1.18, P3[0] - 0.18), (x + 0.06, P3[1] - 1.18, P3[0] - 0.18),
                (x, P3[1] - 1.45, P3[0] + 0.05), (x, P3[1] - 1.1, P3[0] - 0.05)], WEAR, bevel=0.0)
    # Gravel spilling in the bucket.
    p.hull([(-0.6, P3[1] - 0.5, P3[0] - 0.6), (0.6, P3[1] - 0.5, P3[0] - 0.6), (0, P3[1] - 0.15, P3[0] - 0.55),
            (-0.6, P3[1] - 1.0, P3[0] - 0.2), (0.6, P3[1] - 1.0, P3[0] - 0.2)], BUCKET, bevel=0.0)
    p.box((0.4, 0.08, 0.2), (0, P3[1] - 0.05, P3[0] + 0.05), DARK, bevel=0.02)
    export(p.to_object(), "excavator.glb")


build()
print("DONE", dw_blender.OUT)
