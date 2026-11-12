"""Shared Blender (bpy) helpers for Dirt Work machine models.

Imported by tools/blender/build_*.py. Coordinates passed to helpers are GODOT
space (x right, y up, -z forward); G() converts to Blender space.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ------------------------------------------------------------------ setup ----
OUT = os.path.abspath("assets/models")


def set_output(path):
    """Directory export() writes into."""
    global OUT
    OUT = os.path.abspath(path)
    os.makedirs(OUT, exist_ok=True)



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
GLASS = mat("Glass", (0.62, 0.72, 0.78), rough=0.05, alpha=0.18)
LAMP = mat("Lamp", (1.0, 0.95, 0.82), rough=0.2, emit=4.0)
TAIL = mat("TailLamp", (1.0, 0.12, 0.05), rough=0.2, emit=3.0)
AMBER = mat("Amber", (1.0, 0.55, 0.05), rough=0.2, emit=2.0)
HIVIS = mat("HiVis", (0.80, 0.95, 0.15), rough=0.8)
SKIN = mat("Skin", (0.86, 0.64, 0.50), rough=0.8)
SEAT = mat("Seat", (0.12, 0.12, 0.13), rough=0.85)
LINER = mat("Liner", (0.55, 0.56, 0.57), rough=0.9)
TINT = mat("Tint", (0.08, 0.1, 0.12), rough=0.3)
SCREEN = mat("Screen", (0.35, 0.72, 0.95), rough=0.2, emit=1.5)
TROUSERS = mat("Trousers", (0.14, 0.16, 0.24), rough=0.85)
CAP = mat("Cap", (0.10, 0.12, 0.16), rough=0.8)


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
        junk = [v for v in set(res["geom_interior"] + res["geom_unused"]) if isinstance(v, bmesh.types.BMVert)]
        if junk:
            bmesh.ops.delete(bm, geom=junk, context="VERTS")
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


