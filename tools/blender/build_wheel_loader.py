"""Builds the DW-90 wheel loader as glTF parts with Blender (headless).

    blender -b --factory-startup --python tools/blender/build_wheel_loader.py -- assets/models/wheel_loader

Everything is authored here in code (no downloaded assets). Coordinates in this
file are GODOT space: x right, y up, -z forward, metres, loader standing on y=0
with the articulation hinge at the origin. They are converted to Blender space
(x, -z, y) on the way in; the glTF exporter converts back (+Y up).

Exported parts and their origins (must match tools/gen_wheel_loader.py):
  front.glb   front frame, origin = hinge
  rear.glb    rear frame + cab + operator, origin = hinge
  arm.glb     lift arms + Z-bar lever, origin = arm pivot
  bucket.glb  bucket, origin = bucket pin
  wheel.glb   one wheel (tyre + rim), origin = wheel centre, axle along X
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ------------------------------------------------------------------ setup ----
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "assets/models/wheel_loader")
os.makedirs(OUT, exist_ok=True)

# Proportions follow the concept art: big, wide tyres; long wheelbase; tall
# boxy engine hood; massive single-beam boom on each side.
WHEEL_R = 1.15
TYRE_W = 1.05
TRACK = 1.38
AXLE = 1.75
ARM_PIVOT = (0.0, 2.45, -1.0)   # in front-frame space (low on the tower, like the reference)
ARM_LEN = 4.2                     # pivot -> bucket pin along -z (long reach)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def G(x, y, z):
    """Godot -> Blender coordinates."""
    return Vector((x, -z, y))


bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}


def mat(name, rgb, rough=0.55, metal=0.0, emit=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    lin = [srgb_to_linear(c) for c in rgb]
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*lin, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            if hasattr(m, attr):
                try:
                    setattr(m, attr, val)
                except TypeError:
                    pass
    MATS[name] = m
    return m


YELLOW = mat("Paint", (0.96, 0.66, 0.04), rough=0.4)
DARK = mat("DarkPaint", (0.17, 0.18, 0.19), rough=0.6)
STEEL = mat("Steel", (0.45, 0.46, 0.49), rough=0.45, metal=0.4)
BUCKET = mat("BucketSteel", (0.30, 0.30, 0.32), rough=0.6, metal=0.2)
WEAR = mat("WearSteel", (0.62, 0.63, 0.66), rough=0.35, metal=0.6)
RUBBER = mat("Rubber", (0.11, 0.11, 0.12), rough=0.92)
BLACK = mat("Black", (0.05, 0.05, 0.06), rough=0.8)
RED = mat("RailRed", (0.82, 0.10, 0.08), rough=0.5)
GLASS = mat("Glass", (0.35, 0.50, 0.60), rough=0.05, alpha=0.32)
LAMP = mat("Lamp", (1.0, 0.95, 0.82), rough=0.2, emit=4.0)
TAIL = mat("TailLamp", (1.0, 0.12, 0.05), rough=0.2, emit=3.0)
AMBER = mat("Amber", (1.0, 0.55, 0.05), rough=0.2, emit=2.0)
HIVIS = mat("HiVis", (0.80, 0.95, 0.15), rough=0.8)
SKIN = mat("Skin", (0.86, 0.64, 0.50), rough=0.8)
SEAT = mat("Seat", (0.12, 0.12, 0.13), rough=0.85)


# ---------------------------------------------------------- mesh helpers ----
class Part:
    """Accumulates bmesh geometry with per-face materials for one exported part."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _finish(self, bm, m, bevel=0.0, segments=1, sharp_bevel=False):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if bevel > 0.0:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mi = self._mi(m)
        for f in bm.faces:
            f.material_index = mi
        # Merge into the part's bmesh.
        tmp = bpy.data.meshes.new("tmp")
        bm.to_mesh(tmp)
        self.bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        bm.free()

    def prism(self, profile_zy, x0, x1, m, bevel=0.04, segments=2):
        """Side profile [(z, y), ...] (Godot) extruded across x0..x1."""
        bm = bmesh.new()
        a = [bm.verts.new(G(x0, y, z)) for z, y in profile_zy]
        b = [bm.verts.new(G(x1, y, z)) for z, y in profile_zy]
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
        self._finish(bm, m, bevel, segments)

    def box(self, size, center, m, bevel=0.03, segments=1, rot=None):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        sx, sy, sz = size
        M = Matrix.Diagonal((sx, sz, sy, 1.0))   # Godot (x,y,z) sizes -> Blender (x, z->y, y->z)
        if rot is not None:
            M = rot @ M
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        bmesh.ops.translate(bm, vec=G(*center), verts=bm.verts)
        self._finish(bm, m, bevel, segments)

    def cylinder(self, radius, depth, center, axis, m, segments=12, bevel=0.0, radius2=None):
        """Cylinder along Godot axis 'x', 'y' or 'z'."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              radius1=radius, radius2=radius if radius2 is None else radius2, depth=depth)
        # create_cone is along Blender Z (= Godot Y).
        rot = {"y": Matrix.Identity(4), "x": Matrix.Rotation(math.pi / 2, 4, "Y"),
               "z": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
        bmesh.ops.translate(bm, vec=G(*center), verts=bm.verts)
        self._finish(bm, m, bevel, 1)

    def hull(self, points, m, bevel=0.05, segments=2):
        """Convex hull of Godot-space points: tapered/flared panels in one piece."""
        bm = bmesh.new()
        vs = [bm.verts.new(G(*q)) for q in points]
        res = bmesh.ops.convex_hull(bm, input=vs)
        bmesh.ops.delete(bm, geom=res["geom_interior"] + res["geom_unused"], context="VERTS")
        self._finish(bm, m, bevel, segments)

    def tube(self, points, radius, m, segments=6):
        """Round bar through Godot points (rails, ladders)."""
        for p, q in zip(points, points[1:]):
            p, q = Vector(G(*p)), Vector(G(*q))
            d = q - p
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=radius, radius2=radius, depth=d.length)
            rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
            bmesh.ops.translate(bm, vec=(p + q) / 2, verts=bm.verts)
            self._finish(bm, m)

    def arch(self, center_zy, radius, thickness, x0, x1, a0, a1, m, steps=10, bevel=0.025):
        """Curved fender plate around an X axis. Angles: 0 = forward(-z), 90 = up."""
        cz, cy = center_zy
        outer, inner = [], []
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            outer.append((cz - math.cos(a) * (radius + thickness), cy + math.sin(a) * (radius + thickness)))
            inner.append((cz - math.cos(a) * radius, cy + math.sin(a) * radius))
        self.prism(outer + list(reversed(inner)), x0, x1, m, bevel, 1)

    def to_object(self, smooth_angle=35.0):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        self.bm.to_mesh(me)
        self.bm.free()
        for mm in self.mats:
            me.materials.append(mm)
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        return ob


def export(ob, filename):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, filename), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True)
    print("exported", filename, len(ob.data.polygons), "faces")


def arc_pts(cz, cy, r, a0, a1, steps):
    """Points on an arc in the (z, y) plane; angle 0 = -z (forward), 90 = up."""
    return [(cz - math.cos(math.radians(a0 + (a1 - a0) * i / steps)) * r,
             cy + math.sin(math.radians(a0 + (a1 - a0) * i / steps)) * r) for i in range(steps + 1)]


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
    cz = 1.1
    FL, ROOF = 2.4, 4.3
    p.prism([(cz - 1.0, FL - 0.35), (cz + 1.0, FL - 0.35), (cz + 1.0, FL), (cz - 1.0, FL)], -1.0, 1.0, DARK, bevel=0.04)
    p.box((1.95, 0.55, 1.95), (0, FL + 0.27, cz), YELLOW, bevel=0.06)                         # lower cab panels
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
    # Interior: seat, console, low steering wheel, operator in hi-vis + cap.
    p.box((0.6, 0.5, 0.55), (0, FL + 0.6, cz + 0.3), SEAT, bevel=0.05)
    p.box((0.6, 0.7, 0.15), (0, FL + 1.0, cz + 0.6), SEAT, bevel=0.04)
    p.box((0.5, 0.45, 0.3), (0, FL + 0.55, cz - 0.5), DARK, bevel=0.04)
    p.cylinder(0.04, 0.3, (0, FL + 0.9, cz - 0.42), "y", BLACK, segments=6)
    p.cylinder(0.17, 0.04, (0, FL + 1.05, cz - 0.4), "y", BLACK, segments=12)
    p.box((0.5, 0.6, 0.32), (0, FL + 1.1, cz + 0.32), HIVIS, bevel=0.06, segments=2)
    p.box((0.52, 0.05, 0.34), (0, FL + 1.0, cz + 0.32), WEAR, bevel=0.0)                   # reflective band
    p.box((0.13, 0.42, 0.13), (-0.3, FL + 1.1, cz + 0.1), HIVIS, bevel=0.04)
    p.box((0.13, 0.42, 0.13), (0.3, FL + 1.1, cz + 0.1), HIVIS, bevel=0.04)
    p.box((0.26, 0.28, 0.26), (0, FL + 1.57, cz + 0.28), SKIN, bevel=0.06, segments=2)
    p.box((0.3, 0.09, 0.33), (0, FL + 1.74, cz + 0.25), DARK, bevel=0.03)
    p.cylinder(0.14, 0.06, (-0.65, ROOF + 0.13, cz + 0.5), "y", BLACK, segments=10)          # beacon base
    export(p.to_object(), "rear.glb")


build_wheel()
build_front()
build_arm()
build_bucket()
build_rear()
print("DONE", OUT)
