#!/usr/bin/env python3
"""Generates scenes/vehicles/wheel_loader.tscn (the DW-90 wheel loader).

Run from the repo root:  python3 tools/gen_wheel_loader.py
The .tscn is the artefact Godot loads; edit proportions/colours here and
regenerate rather than hand-editing the scene.

The meshes come from Blender: tools/blender/build_wheel_loader.py exports
assets/models/wheel_loader/{front,rear,arm,bucket,wheel}.glb. This script only
assembles them at the pivots the simulation animates, and adds markers for
the hydraulic rams, the cab camera, beacon and model labels.

Coordinates are world heights with the loader standing on y=0 and the hinge
at the origin (must match the Blender script).
Node paths used by scripts/tests (Chassis, FrontFrame, ArmPivot, BucketPivot,
Tip, Wheel*, RearShape, FrontShape, PlayerInput, LiftRam*, Cab) must stay stable.
"""
import math

LINEARIZE = False    # True only for the gl_compatibility renderer
WHEEL_R = 1.0        # visual tyre radius (m) - wheel centre at y = WHEEL_R
LIFT = 0.0           # frames are no longer offset (models are authored in world space)
TRACK = 1.32         # wheel centre x
AXLE = 1.6           # hinge-to-axle distance (matches WheelLoader exports)

YELLOW = (0.98, 0.77, 0.10)
DARK = (0.24, 0.25, 0.27)
STEEL = (0.42, 0.43, 0.46)
BLACK = (0.10, 0.10, 0.11)

subs = []; nodes = []; meshes = {}

def lin(c):
    if not LINEARIZE: return c
    return round(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4, 4)

def fmt(v):
    if isinstance(v, float): return f"{v:.4f}".rstrip('0').rstrip('.')
    if isinstance(v, tuple):  # colour
        return "Color(%s, %s, %s, 1)" % tuple(fmt(float(c)) for c in v)
    return str(v)

def T(x, y, z, rx=0.0, ry=0.0, rz=0.0):
    """Transform3D text. Godot's tscn format is ROW-major basis."""
    cx, sx = math.cos(rx), math.sin(rx); cy, sy = math.cos(ry), math.sin(ry); cz, sz = math.cos(rz), math.sin(rz)
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]; Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]; Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    mm = lambda A, B: [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    R = mm(mm(Ry, Rx), Rz)  # Godot default Euler order YXZ
    vals = [R[r][c] for r in range(3) for c in range(3)] + [x, y, z]
    return "Transform3D(" + ", ".join(f"{v:.6f}" for v in vals) + ")"

def mat(name, rgb, a=1.0, rough=0.6, metal=0.0, emit=0.0):
    r, g, b = (lin(c) for c in rgb)
    p = dict(albedo_color=f"Color({r}, {g}, {b}, {a})", roughness=rough, metallic=metal)
    if a < 1: p["transparency"] = 1
    if emit: p.update(emission_enabled="true", emission=f"Color({r}, {g}, {b}, 1)", emission_energy_multiplier=emit)
    subs.append((f'[sub_resource type="StandardMaterial3D" id="{name}"]', p))

mat("glass", (0.45, 0.62, 0.75), a=0.35, rough=0.05)
mat("lamp", (1.0, 0.95, 0.8), emit=3.0)
mat("tail", (1.0, 0.12, 0.06), emit=2.5)
mat("red", (0.86, 0.13, 0.10), rough=0.5)
mat("black", BLACK, rough=0.9)
mat("hivis", (0.78, 0.95, 0.18), rough=0.8)
mat("skin", (0.86, 0.64, 0.5), rough=0.8)
mat("chrome", (0.86, 0.87, 0.9), rough=0.25, metal=0.6)

def node(name, typ, parent, **p):
    hdr = f'[node name="{name}" type="{typ}"' + (f' parent="{parent}"' if parent is not None else "") + "]"
    nodes.append((hdr, p))

def scripted(name, typ, parent, script, transform=None, **props):
    q = {}
    if transform: q["transform"] = transform
    q["script"] = f'ExtResource("{script}")'   # script BEFORE exported props
    q.update(props); node(name, typ, parent, **q)

LIFTED = ("Chassis/FrontFrame", "Chassis/RearPivot", "Chassis/RearPivot/Cab")
def ly(parent, y):  # world height -> local height for parts on a lifted frame
    return y - LIFT if parent in LIFTED else y

def part(name, parent, size, pos, color=YELLOW, chamfer=0.1, rot=(0, 0, 0), top_scale=None, top_shift_z=None):
    props = dict(size=f"Vector3({size[0]}, {size[1]}, {size[2]})", chamfer=chamfer, color=color)
    if top_scale: props["top_scale"] = f"Vector2({top_scale[0]}, {top_scale[1]})"
    if top_shift_z is not None: props["top_shift_z"] = top_shift_z
    scripted(name, "MeshInstance3D", parent, "6", transform=T(pos[0], ly(parent, pos[1]), pos[2], *rot), **props)

def box(name, parent, size, pos, m, rot=(0, 0, 0)):
    key = ("box", size, m)
    if key not in meshes:
        mid = f"m{len(meshes)}"; meshes[key] = mid
        subs.append((f'[sub_resource type="BoxMesh" id="{mid}"]', dict(size=f"Vector3({size[0]}, {size[1]}, {size[2]})", material=f'SubResource("{m}")')))
    node(name, "MeshInstance3D", parent, transform=T(pos[0], ly(parent, pos[1]), pos[2], *rot), mesh=f'SubResource("{meshes[key]}")')

def cyl(name, parent, r, h, pos, m, seg=8, rot=(0, 0, 0)):
    key = ("cyl", r, h, m, seg)
    if key not in meshes:
        mid = f"m{len(meshes)}"; meshes[key] = mid
        subs.append((f'[sub_resource type="CylinderMesh" id="{mid}"]', dict(top_radius=r, bottom_radius=r, height=h, radial_segments=seg, rings=1, material=f'SubResource("{m}")')))
    node(name, "MeshInstance3D", parent, transform=T(pos[0], ly(parent, pos[1]), pos[2], *rot), mesh=f'SubResource("{meshes[key]}")')

def marker(name, parent, pos):
    node(name, "Marker3D", parent, transform=T(pos[0], ly(parent, pos[1]), pos[2]))

def wheel(name, parent, x, z):
    node(name, "Node3D", parent, transform=T(x, ly(parent, WHEEL_R), z))
    scripted("Tire", "MeshInstance3D", f"{parent}/{name}", "3", radius=WHEEL_R, width=0.9, segments=26, lug_depth=0.045)

def fender(name, parent, x, z, start, end):
    scripted(name, "MeshInstance3D", parent, "7", transform=T(x, ly(parent, WHEEL_R), z),
             radius=WHEEL_R + 0.12, width=1.0, start_deg=start, end_deg=end, segments=7, color=DARK)

# ---------------------------------------------------------------- root ----
GLB = "res://assets/models/wheel_loader/"
EXT = [("1", "Script", "res://scripts/vehicles/wheel_loader.gd"), ("2", "Script", "res://scripts/vehicles/player_loader_input.gd"),
       ("4", "Script", "res://scripts/vehicles/hydraulic_ram.gd"), ("5", "Script", "res://scripts/vehicles/beacon.gd"),
       ("10", "PackedScene", GLB + "front.glb"), ("11", "PackedScene", GLB + "rear.glb"), ("12", "PackedScene", GLB + "arm.glb"),
       ("13", "PackedScene", GLB + "bucket.glb"), ("14", "PackedScene", GLB + "wheel.glb")]

def model(name, parent, ext, transform=None):
    hdr = f'[node name="{name}" parent="{parent}" instance=ExtResource("{ext}")]'
    nodes.append((hdr, {"transform": transform} if transform else {}))

subs.append(('[sub_resource type="BoxShape3D" id="front_shape"]', dict(size="Vector3(2.8, 1.4, 2.4)")))
subs.append(('[sub_resource type="BoxShape3D" id="rear_shape"]', dict(size="Vector3(2.6, 1.8, 2.8)")))
node("WheelLoader", "CharacterBody3D", None, script='ExtResource("1")', wheel_radius=WHEEL_R, lift_min_deg=-22.0, lift_max_deg=50.0)
node("FrontShape", "CollisionShape3D", ".", transform=T(0, 0.7, -1.5), shape='SubResource("front_shape")')
node("RearShape", "CollisionShape3D", ".", transform=T(0, 0.9, 1.6), shape='SubResource("rear_shape")')
node("Chassis", "Node3D", ".")
F = "Chassis/FrontFrame"; R = "Chassis/RearPivot"
node("FrontFrame", "Node3D", "Chassis")
node("RearPivot", "Node3D", "Chassis")

def wheel(name, parent, x, z):
    node(name, "Node3D", parent, transform=T(x, WHEEL_R, z))
    model("Tire", f"{parent}/{name}", "14")

# Front frame
model("Model", F, "10")
wheel("WheelFL", F, -TRACK, -AXLE); wheel("WheelFR", F, TRACK, -AXLE)
for s, n in [(-1, "L"), (1, "R")]:
    marker(f"LiftRamBase{n}", F, (s * 0.52, 1.3, -1.75))
marker("TiltRamBase", F, (0, 2.85, -1.35))
A = F + "/ArmPivot"
node("ArmPivot", "Node3D", F, transform=T(0, 2.55, -0.85))
model("Model", A, "12")
ARM = 3.2
for s, n in [(-1, "L"), (1, "R")]:
    node(f"LiftRamEnd{n}", "Marker3D", A, transform=T(s * 0.52, -0.48, -1.7))
node("TiltLeverTop", "Marker3D", A, transform=T(0, 1.0, -1.9))
B = A + "/BucketPivot"
node("BucketPivot", "Node3D", A, transform=T(0, 0, -ARM))
model("Model", B, "13")
node("Tip", "Marker3D", B, transform=T(0, -1.43, -1.95))
for n in "LR":
    scripted(f"LiftRam{n}", "Node3D", F, "4", base_path=f'NodePath("../LiftRamBase{n}")', end_path=f'NodePath("../ArmPivot/LiftRamEnd{n}")')
scripted("TiltRam", "Node3D", F, "4", base_path='NodePath("../TiltRamBase")',
         end_path='NodePath("../ArmPivot/TiltLeverTop")', barrel_radius=0.12, rod_radius=0.065)

# Rear frame + cab
model("Model", R, "11")
wheel("WheelRL", R, -TRACK, AXLE); wheel("WheelRR", R, TRACK, AXLE)
C = R + "/Cab"
node("Cab", "Node3D", R, transform=T(0, 0, 1.15))
scripted("Beacon", "Node3D", C, "5", transform=T(-0.6, 4.33, 0.5))
for s, n, ry in [(-1, "Left", -math.pi / 2), (1, "Right", math.pi / 2)]:
    node(f"Model{n}", "Label3D", R, transform=T(s * 1.27, 1.95, 4.45, 0, ry, 0), text='"DW-90"', font_size=72,
         pixel_size=0.005, modulate="Color(0.06, 0.06, 0.07, 1)", outline_size=0, double_sided="false")
node("PlayerInput", "Node", ".", script='ExtResource("2")')

out = "[gd_scene format=3]\n\n"
for i, typ, pth in EXT:
    out += f'[ext_resource type="{typ}" path="{pth}" id="{i}"]\n'
out += "\n"
for h, p in subs: out += h + "\n" + "".join(f"{k} = {fmt(v)}\n" for k, v in p.items()) + "\n"
for h, p in nodes: out += h + "\n" + "".join(f"{k} = {fmt(v)}\n" for k, v in p.items()) + "\n"
open("scenes/vehicles/wheel_loader.tscn", "w").write(out)
print("wrote scenes/vehicles/wheel_loader.tscn")
