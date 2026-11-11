#!/usr/bin/env python3
"""Generates scenes/vehicles/wheel_loader.tscn (the DW-90 wheel loader).

Run from the repo root:  python3 tools/gen_wheel_loader.py
The .tscn is the artefact Godot loads; edit proportions/colours here and
regenerate rather than hand-editing the scene.

Most panels are procedural @tool meshes (ChamferBox, FenderArch, BucketShell,
WheelVisual) that take sRGB palette colours and convert them via
Palette.render(). Plain StandardMaterial3D colours here (glass, lamps, rails)
are linearized for the Compatibility renderer (LINEARIZE).

Coordinates below are WORLD heights with the loader standing on y=0; the
FrontFrame/RearPivot nodes are raised by LIFT, which part() compensates for.
Node paths used by scripts/tests (Chassis, FrontFrame, ArmPivot, BucketPivot,
Tip, Wheel*, RearShape, FrontShape, PlayerInput, LiftRam*, Cab) must stay stable.
"""
import math

LINEARIZE = True     # project uses gl_compatibility; set False for Forward+/Mobile
WHEEL_R = 1.0        # visual tyre radius (m) - wheel centre at y = WHEEL_R
LIFT = WHEEL_R - 0.8 # frames are lifted so physics shapes stay unchanged
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
subs.append(('[sub_resource type="BoxShape3D" id="front_shape"]', dict(size="Vector3(2.8, 1.4, 2.4)")))
subs.append(('[sub_resource type="BoxShape3D" id="rear_shape"]', dict(size="Vector3(2.6, 1.8, 2.8)")))
node("WheelLoader", "CharacterBody3D", None, script='ExtResource("1")', wheel_radius=WHEEL_R, lift_min_deg=-23.0, lift_max_deg=50.0)
node("FrontShape", "CollisionShape3D", ".", transform=T(0, 0.7, -1.5), shape='SubResource("front_shape")')
node("RearShape", "CollisionShape3D", ".", transform=T(0, 0.9, 1.6), shape='SubResource("rear_shape")')
node("Chassis", "Node3D", ".")
F = "Chassis/FrontFrame"; R = "Chassis/RearPivot"
node("FrontFrame", "Node3D", "Chassis", transform=T(0, LIFT, 0))
node("RearPivot", "Node3D", "Chassis", transform=T(0, LIFT, 0))

# --------------------------------------------------------- front frame ----
wheel("WheelFL", F, -TRACK, -AXLE); wheel("WheelFR", F, TRACK, -AXLE)
fender("FenderL", F, -TRACK, -AXLE, 20, 135); fender("FenderR", F, TRACK, -AXLE, 20, 135)
part("FrontChassis", F, (1.1, 0.8, 2.4), (0, 1.15, -1.55), DARK, 0.12)
part("AxleHousing", F, (2.2, 0.35, 0.45), (0, 1.0, -AXLE), DARK, 0.1)
part("Tower", F, (1.35, 1.5, 1.0), (0, 2.05, -0.95), YELLOW, 0.16, top_scale=(0.9, 0.8), top_shift_z=0.1)
part("TowerNose", F, (1.1, 0.5, 0.5), (0, 1.55, -1.6), YELLOW, 0.12)
part("HingeFront", F, (0.7, 0.6, 0.55), (0, 1.2, -0.3), STEEL, 0.08)
for s, n in [(-1, "L"), (1, "R")]:
    box(f"Headlight{n}", F, (0.22, 0.16, 0.06), (s * 0.42, 2.35, -1.47), "lamp")
    marker(f"LiftRamBase{n}", F, (s * 0.52, 1.25, -1.75))

A = F + "/ArmPivot"
node("ArmPivot", "Node3D", F, transform=T(0, ly(F, 2.55), -0.85))
ARM = 3.2
for s, n in [(-1, "L"), (1, "R")]:
    scripted(f"Arm{n}", "MeshInstance3D", A, "6", transform=T(s * 0.78, 0, -ARM * 0.5),
             size=f"Vector3(0.3, 0.55, {ARM + 0.3})", chamfer=0.1, color=YELLOW)
    box(f"ArmPin{n}", A, (0.4, 0.2, 0.2), (s * 0.78, 0, -ARM), "black")
    node(f"LiftRamEnd{n}", "Marker3D", A, transform=T(s * 0.52, -0.22, -1.7))
scripted("CrossTube", "MeshInstance3D", A, "6", transform=T(0, 0.05, -2.0),
         size="Vector3(1.85, 0.36, 0.4)", chamfer=0.1, color=YELLOW)
scripted("TiltLever", "MeshInstance3D", A, "6", transform=T(0, 0.55, -2.05, -0.35),
         size="Vector3(0.32, 1.0, 0.28)", chamfer=0.08, color=YELLOW)
node("TiltRamBase", "Marker3D", A, transform=T(0, 0.35, -0.6))
node("TiltLeverTop", "Marker3D", A, transform=T(0, 0.98, -2.2))

B = A + "/BucketPivot"
node("BucketPivot", "Node3D", A, transform=T(0, 0, -ARM))
scripted("Shell", "MeshInstance3D", B, "8", width=3.1, depth=1.7, height=1.45, teeth=8,
         color=(0.44, 0.44, 0.47), edge_color=(0.62, 0.63, 0.66))
node("TiltRamEnd", "Marker3D", B, transform=T(0, 0.35, 0.1))
node("Tip", "Marker3D", B, transform=T(0, -1.4, -1.9))

for n in "LR":
    scripted(f"LiftRam{n}", "Node3D", F, "4", base_path=f'NodePath("../LiftRamBase{n}")', end_path=f'NodePath("../ArmPivot/LiftRamEnd{n}")')
scripted("TiltRam", "Node3D", F, "4", base_path='NodePath("../ArmPivot/TiltRamBase")',
         end_path='NodePath("../ArmPivot/TiltLeverTop")', barrel_radius=0.12, rod_radius=0.065)

# ---------------------------------------------------------- rear frame ----
wheel("WheelRL", R, -TRACK, AXLE); wheel("WheelRR", R, TRACK, AXLE)
fender("RearFenderL", R, -TRACK, AXLE, 45, 165); fender("RearFenderR", R, TRACK, AXLE, 45, 165)
part("RearChassis", R, (1.2, 0.8, 3.4), (0, 1.15, 2.1), DARK, 0.12)
part("AxleHousingR", R, (2.2, 0.35, 0.45), (0, 1.0, AXLE), DARK, 0.1)
part("HingeRear", R, (0.55, 0.45, 0.55), (0, 1.2, 0.3), STEEL, 0.08)
part("Deck", R, (2.5, 0.14, 1.7), (0, 2.05, 1.2), DARK, 0.05)
# Engine hood: tapered and sloping down towards the rear.
part("Hood", R, (1.9, 1.2, 2.3), (0, 2.7, 3.0), YELLOW, 0.22, top_scale=(0.86, 0.8), top_shift_z=-0.15)
part("HoodGrille", R, (1.3, 0.05, 1.1), (0, 3.31, 2.9), DARK, 0.02)
part("Counterweight", R, (2.55, 1.25, 0.85), (0, 1.75, 4.35), YELLOW, 0.3, top_scale=(0.95, 0.75))
part("RearGrille", R, (1.5, 0.75, 0.08), (0, 2.75, 4.16), BLACK, 0.02)
part("Bumper", R, (2.6, 0.3, 0.35), (0, 1.0, 4.75), DARK, 0.08)
part("SidePodL", R, (0.25, 0.6, 1.6), (-1.0, 1.65, 3.2), DARK, 0.06)
part("SidePodR", R, (0.25, 0.6, 1.6), (1.0, 1.65, 3.2), DARK, 0.06)
for s, n in [(-1, "L"), (1, "R")]:
    box(f"TailLight{n}", R, (0.24, 0.16, 0.06), (s * 1.0, 2.15, 4.79), "tail")
    box(f"Rail{n}", R, (0.05, 0.05, 2.2), (s * 1.02, 3.75, 3.0), "red")
    for k, z in enumerate([2.0, 3.0, 4.0]):
        box(f"Post{n}{k}", R, (0.05, 0.6, 0.05), (s * 1.02, 3.45, z), "red")
cyl("Exhaust", R, 0.09, 1.0, (0.5, 3.7, 2.3), "black", seg=6)
node("ModelLeft", "Label3D", R, transform=T(-1.14, ly(R, 2.0), 3.35, 0, -math.pi / 2, 0), text='"DW-90"', font_size=80,
     pixel_size=0.005, modulate="Color(0.08, 0.08, 0.09, 1)", outline_size=0, double_sided="false")
node("ModelRight", "Label3D", R, transform=T(1.14, ly(R, 2.0), 3.35, 0, math.pi / 2, 0), text='"DW-90"', font_size=80,
     pixel_size=0.005, modulate="Color(0.08, 0.08, 0.09, 1)", outline_size=0, double_sided="false")
# Ladder up to the deck on the left, in the gap between the wheels.
for k, z in enumerate([0.35, 0.75]):
    box(f"LadderStile{k}", R, (0.05, 1.75, 0.05), (-1.1, 1.15, z), "red")
for k in range(4):
    box(f"LadderRung{k}", R, (0.05, 0.05, 0.4), (-1.1, 0.5 + k * 0.42, 0.55), "black")

# ----------------------------------------------------------------- cab ----
C = R + "/Cab"
node("Cab", "Node3D", R, transform=T(0, 0, 1.15))
part("CabBase", C, (1.8, 0.35, 1.75), (0, 2.25, 0), DARK, 0.08)
for i, (x, z) in enumerate([(-0.84, -0.8), (0.84, -0.8), (-0.84, 0.82), (0.84, 0.82)]):
    part(f"Pillar{i}", C, (0.13, 1.6, 0.13), (x, 3.2, z), YELLOW, 0.04)
box("GlassFront", C, (1.6, 1.5, 0.03), (0, 3.2, -0.8), "glass", rot=(0.06, 0, 0))
box("GlassBack", C, (1.6, 1.5, 0.03), (0, 3.2, 0.82), "glass")
box("GlassL", C, (0.03, 1.5, 1.6), (-0.84, 3.2, 0), "glass")
box("GlassR", C, (0.03, 1.5, 1.6), (0.84, 3.2, 0), "glass")
part("Roof", C, (2.0, 0.2, 2.0), (0, 4.08, 0), YELLOW, 0.08)
part("RoofCap", C, (1.6, 0.1, 1.5), (0, 4.22, 0.05), YELLOW, 0.05)
for s, n in [(-1, "L"), (1, "R")]:
    box(f"WorkLight{n}", C, (0.24, 0.15, 0.1), (s * 0.7, 4.0, -1.02), "lamp")
    box(f"RearWorkLight{n}", C, (0.24, 0.15, 0.1), (s * 0.7, 4.0, 1.02), "lamp")
    box(f"Mirror{n}", C, (0.05, 0.32, 0.2), (s * 1.12, 3.55, -0.75), "black")
    box(f"MirrorArm{n}", C, (0.3, 0.04, 0.04), (s * 0.98, 3.55, -0.75), "black")
scripted("Beacon", "Node3D", C, "5", transform=T(-0.6, ly(C, 4.3), 0.5))
box("Seat", C, (0.55, 0.55, 0.5), (0, 2.7, 0.3), "black")
box("Torso", C, (0.46, 0.55, 0.3), (0, 3.05, 0.2), "hivis")
box("Head", C, (0.24, 0.26, 0.24), (0, 3.48, 0.15), "skin")
box("Cap", C, (0.28, 0.08, 0.34), (0, 3.64, 0.1), "black")
box("SteeringWheel", C, (0.35, 0.35, 0.04), (0, 3.0, -0.25), "black", rot=(-0.8, 0, 0))

node("PlayerInput", "Node", ".", script='ExtResource("2")')

out = "[gd_scene format=3]\n\n"
for i, pth in [("1", "res://scripts/vehicles/wheel_loader.gd"), ("2", "res://scripts/vehicles/player_loader_input.gd"),
               ("3", "res://scripts/vehicles/wheel_visual.gd"), ("4", "res://scripts/vehicles/hydraulic_ram.gd"),
               ("5", "res://scripts/vehicles/beacon.gd"), ("6", "res://scripts/vehicles/chamfer_box.gd"),
               ("7", "res://scripts/vehicles/fender_arch.gd"), ("8", "res://scripts/vehicles/bucket_shell.gd")]:
    out += f'[ext_resource type="Script" path="{pth}" id="{i}"]\n'
out += "\n"
for h, p in subs: out += h + "\n" + "".join(f"{k} = {fmt(v)}\n" for k, v in p.items()) + "\n"
for h, p in nodes: out += h + "\n" + "".join(f"{k} = {fmt(v)}\n" for k, v in p.items()) + "\n"
open("scenes/vehicles/wheel_loader.tscn", "w").write(out)
print("wrote scenes/vehicles/wheel_loader.tscn")
