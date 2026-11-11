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

WHEEL_R = 1.0
TRACK = 1.32
AXLE = 1.6
ARM_PIVOT = (0.0, 2.55, -0.85)   # in front-frame space
ARM_LEN = 3.2                     # pivot -> bucket pin along -z


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


YELLOW = mat("Paint", (0.98, 0.74, 0.08), rough=0.42)
DARK = mat("DarkPaint", (0.20, 0.21, 0.23), rough=0.6)
STEEL = mat("Steel", (0.45, 0.46, 0.49), rough=0.45, metal=0.4)
BUCKET = mat("BucketSteel", (0.30, 0.30, 0.32), rough=0.6, metal=0.2)
WEAR = mat("WearSteel", (0.62, 0.63, 0.66), rough=0.35, metal=0.6)
RUBBER = mat("Rubber", (0.09, 0.09, 0.10), rough=0.9)
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
    p = Part("Wheel")
    R, W = WHEEL_R, 0.9
    carcass_r = R - 0.07
    # Tyre carcass: a chamfered drum (profile revolved as a prism-ring).
    segs = 32
    bm = bmesh.new()
    prof = [(0.0, R * 0.60), (0.0, R * 0.64), (W * 0.06, carcass_r * 0.97), (W * 0.14, carcass_r),
            (W * 0.86, carcass_r), (W * 0.94, carcass_r * 0.97), (W, R * 0.64), (W, R * 0.60)]
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new(G(x - W / 2, math.sin(a) * r, math.cos(a) * r)) for x, r in prof])
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for k in range(len(prof) - 1):
            bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
    p._finish(bm, RUBBER)
    # Chevron tread lugs.
    lugs = 22
    for i in range(lugs):
        a = 2 * math.pi * i / lugs
        for side in (-1, 1):
            # Each half-lug is a slanted block; the halves offset to form a chevron.
            a_off = a + side * 0.06
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.transform(bm, matrix=Matrix.Diagonal((W * 0.42, 0.22, 0.12, 1.0)), verts=bm.verts)
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(side * 0.45, 4, "Z"), verts=bm.verts)
            bmesh.ops.translate(bm, vec=Vector((side * W * 0.22, 0, carcass_r + 0.04)), verts=bm.verts)
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(a_off, 4, "X"), verts=bm.verts)
            p._finish(bm, RUBBER, bevel=0.02)
    # Rim: dished disc with a raised ring, hub and bolts on both sides.
    for side in (-1, 1):
        xo = side * (W / 2 - 0.04)
        p.cylinder(R * 0.60, 0.06, (xo, 0, 0), "x", YELLOW, segments=24, bevel=0.015)
        p.cylinder(R * 0.48, 0.10, (xo - side * 0.03, 0, 0), "x", YELLOW, segments=24, bevel=0.02)
        p.cylinder(R * 0.24, 0.16, (xo + side * 0.02, 0, 0), "x", DARK, segments=12, bevel=0.02)
        p.cylinder(R * 0.10, 0.22, (xo + side * 0.05, 0, 0), "x", STEEL, segments=8)
        for k in range(10):
            a = 2 * math.pi * k / 10
            p.cylinder(0.028, 0.06, (xo + side * 0.11, math.sin(a) * R * 0.18, math.cos(a) * R * 0.18), "x", STEEL, segments=6)
    export(p.to_object(), "wheel.glb")


# ------------------------------------------------------------ front frame ----
def build_front():
    p = Part("FrontFrame")
    # Main frame between the front wheels, nose and loader tower.
    p.prism([(-0.25, 0.75), (-2.65, 0.75), (-2.95, 1.05), (-2.85, 1.55), (-1.25, 1.6), (-0.25, 1.45)],
            -0.55, 0.55, DARK, bevel=0.06)
    p.prism([(-0.45, 1.35), (-1.55, 1.35), (-1.72, 2.25), (-1.45, 2.88), (-0.55, 2.88), (-0.38, 2.3)],
            -0.66, 0.66, YELLOW, bevel=0.08, segments=2)
    p.box((0.5, 0.25, 0.25), (0, 2.95, -1.0), DARK, bevel=0.03)                 # tower cap
    p.box((2.3, 0.36, 0.46), (0, WHEEL_R, -AXLE), DARK, bevel=0.06)             # axle housing
    p.cylinder(0.24, 0.3, (-0.98, WHEEL_R, -AXLE), "x", STEEL, segments=10)
    p.cylinder(0.24, 0.3, (0.98, WHEEL_R, -AXLE), "x", STEEL, segments=10)
    # Hinge knuckles.
    p.box((0.75, 0.22, 0.6), (0, 1.45, -0.25), STEEL, bevel=0.04)
    p.box((0.75, 0.22, 0.6), (0, 0.95, -0.25), STEEL, bevel=0.04)
    p.cylinder(0.09, 0.85, (0, 1.2, -0.12), "y", WEAR, segments=8)
    # Fenders: curved arches with a flat top-front lip.
    for s in (-1, 1):
        x0, x1 = (s * (TRACK - 0.5), s * (TRACK + 0.5))
        p.arch((-AXLE, WHEEL_R), WHEEL_R + 0.12, 0.07, min(x0, x1), max(x0, x1), 25, 150, DARK, steps=12)
        # Headlights on the tower front, work light pods.
        p.box((0.26, 0.18, 0.08), (s * 0.42, 2.45, -1.62), LAMP, bevel=0.015)
        p.box((0.32, 0.24, 0.12), (s * 0.42, 2.45, -1.55), DARK, bevel=0.02)
        # Lift-cylinder clevis on the frame.
        p.box((0.18, 0.3, 0.3), (s * 0.52, 1.3, -1.75), STEEL, bevel=0.03)
        # Steps up the tower side.
        p.box((0.32, 0.05, 0.25), (s * 0.82, 1.75, -0.6), STEEL, bevel=0.01)
    # Front counterweight/bumper plate.
    p.box((1.3, 0.35, 0.3), (0, 0.95, -2.85), DARK, bevel=0.05)
    export(p.to_object(), "front.glb")


# --------------------------------------------------------------- lift arm ----
def build_arm():
    """Origin at the arm pivot; arm runs to the bucket pin at (0, 0, -ARM_LEN)."""
    p = Part("Arm")
    L = ARM_LEN
    # Boomerang side profile (z, y): dips below the pivot-pin line in the middle.
    top = [(0.25, 0.30), (-1.0, 0.05), (-2.0, -0.22), (-L - 0.15, 0.22)]
    bot = [(-L - 0.2, -0.22), (-2.0, -0.72), (-1.0, -0.45), (0.25, -0.28)]
    for s in (-1, 1):
        p.prism(top + bot, s * 0.62, s * 0.94, YELLOW, bevel=0.05, segments=2)
        p.cylinder(0.2, 0.42, (s * 0.78, 0, 0), "x", DARK, segments=12)           # pivot boss
        p.cylinder(0.17, 0.42, (s * 0.78, 0, -L), "x", DARK, segments=12)         # bucket pin boss
        p.cylinder(0.12, 0.36, (s * 0.78, -0.48, -1.7), "x", STEEL, segments=10)  # lift ram pin
    # Cross tube and Z-bar tilt lever.
    p.prism([(-1.8, -0.55), (-2.25, -0.55), (-2.3, -0.15), (-1.75, -0.12)], -0.62, 0.62, YELLOW, bevel=0.05)
    p.prism([(-1.9, -0.2), (-2.25, -0.25), (-2.05, 1.05), (-1.75, 1.05)], -0.18, 0.18, YELLOW, bevel=0.04)
    p.cylinder(0.12, 0.5, (0, 1.0, -1.9), "x", DARK, segments=10)
    # Tilt link from lever bottom towards the bucket.
    p.prism([(-2.15, -0.45), (-L + 0.1, 0.15), (-L + 0.05, 0.38), (-2.05, -0.2)], -0.12, 0.12, DARK, bevel=0.03)
    export(p.to_object(), "arm.glb")


# ----------------------------------------------------------------- bucket ----
def build_bucket():
    """Origin at the bucket pin; opening faces -z (forward)."""
    p = Part("Bucket")
    W, H, D = 3.1, 1.45, 1.75
    # Shell profile: top lip -> curved back -> floor -> cutting edge (z, y).
    back = arc_pts(-0.55, -0.68, 0.78, 160, 290, 9)   # big rounded back
    shell = [(-D * 0.45, 0.05), (0.18, 0.1)] + [(z, y) for z, y in back[1:]] + [(-D, -H + 0.02)]
    # Thicken the polyline into a closed profile.
    t = 0.08
    inner = []
    for i, (z, y) in enumerate(shell):
        z0, y0 = shell[max(i - 1, 0)]
        z1, y1 = shell[min(i + 1, len(shell) - 1)]
        dz, dy = z1 - z0, y1 - y0
        ln = math.hypot(dz, dy) or 1.0
        inner.append((z - dy / ln * t, y + dz / ln * t))
    p.prism(shell + list(reversed(inner)), -W / 2 + 0.02, W / 2 - 0.02, BUCKET, bevel=0.015)
    # Side plates (closed profile of the opening) slightly proud of the shell.
    side = [(-D * 0.45, 0.05), (0.18, 0.12)] + [(z, y) for z, y in back[1:]] + [(-D, -H), (-D * 0.85, -H + 0.25)]
    for s in (-1, 1):
        p.prism(side, s * (W / 2 - 0.06), s * (W / 2 + 0.03), BUCKET, bevel=0.02)
        p.prism([(-D * 0.4, -0.05), (-D * 0.95, -H + 0.05), (-D * 0.85, -H + 0.3), (-D * 0.35, 0.1)],
                s * (W / 2 + 0.01), s * (W / 2 + 0.06), WEAR, bevel=0.01)       # side cutter
    # Wear strips under the floor, top spill guard, pin brackets.
    p.box((W - 0.3, 0.1, 1.0), (0, -H - 0.02, -D * 0.6), WEAR, bevel=0.02)
    p.box((W - 0.1, 0.14, 0.5), (0, 0.13, -0.15), BUCKET, bevel=0.03)
    for s in (-1, 1):
        p.box((0.16, 0.6, 0.45), (s * 0.78, 0.02, 0.05), DARK, bevel=0.03)
    p.box((0.4, 0.45, 0.35), (0, 0.32, 0.05), DARK, bevel=0.03)
    # Cutting edge and teeth.
    p.box((W - 0.05, 0.07, 0.24), (0, -H + 0.03, -D + 0.05), WEAR, bevel=0.015)
    for i in range(8):
        x = -W / 2 + 0.25 + i * (W - 0.5) / 7
        p.prism([(-D + 0.05, -H + 0.08), (-D - 0.36, -H + 0.02), (-D - 0.38, -H - 0.02), (-D + 0.05, -H - 0.04)],
                x - 0.08, x + 0.08, WEAR, bevel=0.012)
    export(p.to_object(), "bucket.glb")


# ------------------------------------------------------------- rear frame ----
def build_rear():
    p = Part("RearFrame")
    # Rear chassis rails and axle.
    p.prism([(0.25, 0.75), (3.9, 0.75), (4.1, 1.1), (3.9, 1.6), (0.25, 1.6)], -0.6, 0.6, DARK, bevel=0.06)
    p.box((2.3, 0.36, 0.46), (0, WHEEL_R, AXLE), DARK, bevel=0.06)
    p.box((0.55, 0.45, 0.55), (0, 1.2, 0.25), STEEL, bevel=0.05)
    # Engine hood: side profile tapering down to the rear, with a crowned top.
    hood = [(1.95, 1.75), (1.95, 3.05), (2.2, 3.28), (3.65, 3.22), (4.05, 2.95), (4.15, 1.75)]
    p.prism(hood, -0.95, 0.95, YELLOW, bevel=0.12, segments=3)
    p.box((1.35, 0.06, 1.2), (0, 3.28, 2.9), DARK, bevel=0.02)                # top grille
    for k in range(6):
        p.box((0.06, 0.07, 1.05), (-0.5 + k * 0.2, 3.32, 2.9), BLACK, bevel=0.0)
    for s in (-1, 1):                                                          # side vents
        for k in range(5):
            p.box((0.04, 0.05, 0.8), (s * 0.965, 2.35 + k * 0.12, 3.3), BLACK, bevel=0.0)
    # Counterweight: rounded rear block with a grille and lamps.
    cw = [(3.95, 0.8)] + arc_pts(4.35, 1.25, 0.6, 270, 360, 4)[1:] + [(4.98, 2.15)] + arc_pts(4.5, 2.15, 0.48, 0, 80, 4)[1:] + [(3.95, 2.6)]
    cw = [(3.95, 0.8), (4.6, 0.8), (4.9, 1.0), (5.0, 1.35), (4.98, 2.15), (4.85, 2.45), (4.55, 2.62), (3.95, 2.62)]
    p.prism(cw, -1.25, 1.25, YELLOW, bevel=0.1, segments=3)
    p.box((1.6, 0.8, 0.06), (0, 1.9, 5.0), BLACK, bevel=0.01)
    for k in range(5):
        p.box((1.5, 0.06, 0.08), (0, 1.6 + k * 0.15, 5.03), DARK, bevel=0.0)
    for s in (-1, 1):
        p.box((0.28, 0.18, 0.06), (s * 0.95, 2.3, 4.99), TAIL, bevel=0.01)
        p.box((0.22, 0.14, 0.06), (s * 0.95, 2.05, 4.99), AMBER, bevel=0.01)
    p.box((2.6, 0.3, 0.35), (0, 0.95, 4.85), DARK, bevel=0.06)                # bumper
    # Fenders and walkways.
    for s in (-1, 1):
        x0, x1 = s * (TRACK - 0.5), s * (TRACK + 0.5)
        p.arch((AXLE, WHEEL_R), WHEEL_R + 0.12, 0.07, min(x0, x1), max(x0, x1), 40, 168, DARK, steps=12)
        p.box((0.75, 0.07, 1.4), (s * 1.3, 2.22, 0.95), STEEL, bevel=0.01)       # walkway plate
        # Red handrails along the hood and walkway.
        p.tube([(s * 1.05, 3.4, 1.95), (s * 1.05, 3.85, 2.1), (s * 1.05, 3.85, 3.9), (s * 1.05, 3.1, 4.05)], 0.035, RED)
        p.tube([(s * 1.05, 3.85, 3.0), (s * 1.05, 3.25, 3.0)], 0.03, RED)
        p.tube([(s * 1.62, 2.25, 0.35), (s * 1.62, 3.1, 0.35), (s * 1.62, 3.1, 1.6), (s * 1.62, 2.25, 1.6)], 0.03, RED)
    # Ladder (left) from the ground to the walkway, with a grab rail.
    for z in (0.3, 0.72):
        p.tube([(-1.38, 0.35, z), (-1.38, 2.25, z)], 0.03, YELLOW)
    for k in range(5):
        p.box((0.06, 0.05, 0.42), (-1.38, 0.5 + k * 0.38, 0.51), BLACK, bevel=0.0)
    p.tube([(-1.45, 2.3, 0.3), (-1.45, 3.3, 0.45)], 0.03, RED)
    # Exhaust stack and air pre-cleaner.
    p.cylinder(0.1, 1.0, (0.55, 3.75, 2.45), "y", BLACK, segments=10)
    p.cylinder(0.12, 0.12, (0.55, 4.28, 2.45), "y", BLACK, segments=10, radius2=0.09)
    p.cylinder(0.13, 0.55, (-0.55, 3.55, 2.35), "y", DARK, segments=10)
    # ---- cab (sits on the rear frame just behind the hinge) ----
    cz = 1.15
    p.prism([(cz - 0.95, 2.05), (cz + 0.95, 2.05), (cz + 0.95, 2.4), (cz - 0.95, 2.4)], -0.95, 0.95, DARK, bevel=0.04)
    # Frame: rounded pillars and roof with overhang.
    for x in (-0.86, 0.86):
        p.prism([(cz - 0.82, 2.4), (cz - 0.7, 2.4), (cz - 0.86, 3.95), (cz - 0.98, 3.95)], x - 0.07, x + 0.07, YELLOW, bevel=0.02)
        p.prism([(cz + 0.78, 2.4), (cz + 0.9, 2.4), (cz + 0.9, 3.95), (cz + 0.78, 3.95)], x - 0.07, x + 0.07, YELLOW, bevel=0.02)
    p.prism([(cz - 1.12, 3.92), (cz + 1.0, 3.92), (cz + 1.0, 4.1), (cz + 0.8, 4.2), (cz - 0.95, 4.2), (cz - 1.15, 4.05)],
            -1.02, 1.02, YELLOW, bevel=0.05, segments=2)
    p.box((1.5, 0.1, 1.4), (0, 4.24, cz + 0.05), YELLOW, bevel=0.04)
    p.box((0.9, 0.05, 0.12), (0, 4.0, cz - 1.12), DARK, bevel=0.0)          # visor strip
    # Glass: raked front screen, sides, rear.
    p.prism([(cz - 0.74, 2.42), (cz - 0.7, 2.42), (cz - 0.86, 3.9), (cz - 0.9, 3.9)], -0.8, 0.8, GLASS, bevel=0.0)
    for x in (-0.86, 0.86):
        p.prism([(cz - 0.72, 2.45), (cz + 0.8, 2.45), (cz + 0.8, 3.9), (cz - 0.88, 3.9)], x - 0.012, x + 0.012, GLASS, bevel=0.0)
    p.box((1.6, 1.45, 0.03), (0, 3.18, cz + 0.84), GLASS, bevel=0.0)
    p.tube([(-0.87, 3.1, cz - 0.1), (-0.87, 3.1, cz + 0.3)], 0.02, BLACK)    # door handle
    # Mirrors, work lights, wipers.
    for s in (-1, 1):
        p.tube([(s * 0.95, 3.7, cz - 0.75), (s * 1.25, 3.7, cz - 0.85)], 0.025, BLACK)
        p.box((0.06, 0.34, 0.22), (s * 1.28, 3.6, cz - 0.85), BLACK, bevel=0.02)
        p.box((0.26, 0.16, 0.1), (s * 0.72, 4.13, cz - 1.15), DARK, bevel=0.02)
        p.box((0.22, 0.12, 0.04), (s * 0.72, 4.13, cz - 1.21), LAMP, bevel=0.01)
        p.box((0.26, 0.16, 0.1), (s * 0.72, 4.13, cz + 1.02), DARK, bevel=0.02)
        p.box((0.22, 0.12, 0.04), (s * 0.72, 4.13, cz + 1.08), LAMP, bevel=0.01)
    # Interior: seat, console, steering wheel, operator in hi-vis.
    p.box((0.6, 0.5, 0.55), (0, 2.68, cz + 0.3), SEAT, bevel=0.05)
    p.box((0.6, 0.7, 0.15), (0, 3.05, cz + 0.6), SEAT, bevel=0.04)
    p.box((0.5, 0.45, 0.3), (0, 2.62, cz - 0.5), DARK, bevel=0.04)
    p.cylinder(0.04, 0.3, (0, 2.95, cz - 0.42), "y", BLACK, segments=6)
    p.cylinder(0.17, 0.04, (0, 3.1, cz - 0.4), "y", BLACK, segments=12)
    p.box((0.5, 0.6, 0.32), (0, 3.15, cz + 0.32), HIVIS, bevel=0.06, segments=2)
    p.box((0.13, 0.42, 0.13), (-0.3, 3.15, cz + 0.1), HIVIS, bevel=0.04)
    p.box((0.13, 0.42, 0.13), (0.3, 3.15, cz + 0.1), HIVIS, bevel=0.04)
    p.box((0.26, 0.28, 0.26), (0, 3.62, cz + 0.28), SKIN, bevel=0.06, segments=2)
    p.box((0.3, 0.09, 0.33), (0, 3.79, cz + 0.25), DARK, bevel=0.03)
    # Beacon base (the animated dome is a Godot node).
    p.cylinder(0.13, 0.06, (-0.6, 4.3, cz + 0.5), "y", BLACK, segments=10)
    export(p.to_object(), "rear.glb")


build_wheel()
build_front()
build_arm()
build_bucket()
build_rear()
print("DONE", OUT)
