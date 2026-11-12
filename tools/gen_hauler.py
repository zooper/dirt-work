#!/usr/bin/env python3
"""Generates scenes/vehicles/hauler.tscn from the Blender parts in assets/models/hauler.

    python3 tools/gen_hauler.py

The hauler is currently a parked, loaded prop (StaticBody3D with simple box
collision) used as the loading target; it is not drivable yet.
"""
import math

def T(x, y, z, ry=0.0):
    c, s = math.cos(ry), math.sin(ry)
    return f"Transform3D({c:.6f}, 0, {s:.6f}, 0, 1, 0, {-s:.6f}, 0, {c:.6f}, {x}, {y}, {z})"  # row-major

WHEEL_R, TRACK, FRONT_AXLE, REAR_AXLES = 0.98, 1.3, -2.6, (2.4, 4.1)
G = "res://assets/models/hauler/"
out = ['[gd_scene format=3]', '']
for i, f in enumerate(["front", "rear", "wheel", "load"], 1):
    out.append(f'[ext_resource type="PackedScene" path="{G}{f}.glb" id="{i}"]')
out += ['', '[sub_resource type="BoxShape3D" id="front_box"]', 'size = Vector3(2.6, 3.6, 4.9)', '',
        '[sub_resource type="BoxShape3D" id="rear_box"]', 'size = Vector3(3.2, 3.6, 6.2)', '',
        '[node name="Hauler" type="StaticBody3D"]', '',
        '[node name="FrontShape" type="CollisionShape3D" parent="."]', f'transform = {T(0, 1.8, -2.45)}', 'shape = SubResource("front_box")', '',
        '[node name="RearShape" type="CollisionShape3D" parent="."]', f'transform = {T(0, 1.8, 3.0)}', 'shape = SubResource("rear_box")', '',
        '[node name="Front" parent="." instance=ExtResource("1")]', '',
        '[node name="Rear" parent="." instance=ExtResource("2")]', '',
        '[node name="Load" parent="." instance=ExtResource("4")]', '']
wheels = [("WheelFL", -TRACK, FRONT_AXLE), ("WheelFR", TRACK, FRONT_AXLE)]
for k, z in enumerate(REAR_AXLES):
    wheels += [(f"WheelR{k}L", -TRACK, z), (f"WheelR{k}R", TRACK, z)]
for n, x, z in wheels:
    out += [f'[node name="{n}" parent="." instance=ExtResource("3")]', f'transform = {T(x, WHEEL_R, z)}', '']
for s, n in [(-1, "Left"), (1, "Right")]:
    out += [f'[node name="Model{n}" type="Label3D" parent="."]', f'transform = {T(s * 1.56, 2.3, 1.25, s * math.pi / 2)}',
            'text = "DW-40"', 'font_size = 96', 'pixel_size = 0.005', 'modulate = Color(0.95, 0.95, 0.93, 1)',
            'outline_size = 0', 'double_sided = false', '']
open("scenes/vehicles/hauler.tscn", "w").write("\n".join(out))
print("wrote scenes/vehicles/hauler.tscn")
