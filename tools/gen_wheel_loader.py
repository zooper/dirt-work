#!/usr/bin/env python3
"""Generates scenes/vehicles/wheel_loader.tscn (the DW-90 wheel loader).

Run from the repo root:  python3 tools/gen_wheel_loader.py
The .tscn is the artefact Godot loads; edit proportions/colours here and
regenerate rather than hand-editing the scene. Colours are sRGB palette values;
they are linearized for the Compatibility renderer (see Palette.render()).
Node paths used by scripts/tests (Chassis, FrontFrame, ArmPivot, BucketPivot,
Tip, Wheel*, RearShape, ...) must stay stable.
"""
import math
subs=[]; nodes=[]; mats={}; meshes={}
def fmt(v): return f"{v:.4f}".rstrip('0').rstrip('.') if isinstance(v,float) else str(v)
def T(x,y,z,rx=0,ry=0,rz=0):
    # Euler YXZ like Godot: R = Ry*Rx*Rz
    cx,sx=math.cos(rx),math.sin(rx); cy,sy=math.cos(ry),math.sin(ry); cz,sz=math.cos(rz),math.sin(rz)
    Rx=[[1,0,0],[0,cx,-sx],[0,sx,cx]]; Ry=[[cy,0,sy],[0,1,0],[-sy,0,cy]]; Rz=[[cz,-sz,0],[sz,cz,0],[0,0,1]]
    mm=lambda A,B:[[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    R=mm(mm(Ry,Rx),Rz)
    cols=[R[r][c] for r in range(3) for c in range(3)]  # tscn Transform3D is row-major
    return "Transform3D("+", ".join(f"{v:.6f}" for v in cols+[x,y,z])+")"
LINEARIZE = True  # project uses gl_compatibility; set False for Forward+/Mobile
def lin(c):
    if not LINEARIZE: return c
    return round(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4, 4)
def mat(name,r,g,b,a=1.0,rough=0.6,metal=0.0,emit=0.0):
    mats[name]=1
    r,g,b=lin(r),lin(g),lin(b)
    p=dict(albedo_color=f"Color({r}, {g}, {b}, {a})",roughness=rough,metallic=metal)
    if a<1: p["transparency"]=1
    if emit: p.update(emission_enabled="true",emission=f"Color({r}, {g}, {b}, 1)",emission_energy_multiplier=emit)
    subs.append((f'[sub_resource type="StandardMaterial3D" id="{name}"]',p))
mat("yellow",0.98,0.77,0.10,rough=0.45)
mat("dark",0.27,0.28,0.30,rough=0.7)
mat("steel",0.45,0.46,0.48,rough=0.5,metal=0.2)
mat("bucket",0.40,0.40,0.42,rough=0.65,metal=0.1)
mat("teeth",0.55,0.56,0.58,rough=0.4,metal=0.5)
mat("red",0.85,0.12,0.1,rough=0.5)
mat("glass",0.35,0.55,0.7,a=0.4,rough=0.1)
mat("hivis",0.75,0.95,0.15,rough=0.8)
mat("skin",0.86,0.64,0.5,rough=0.8)
mat("lamp",1.0,0.93,0.75,emit=2.5)
mat("tail",1.0,0.1,0.05,emit=2.0)
mat("black",0.06,0.06,0.07,rough=0.9)
def box(name,parent,size,pos,m,rot=(0,0,0)):
    key=("box",size,m)
    if key not in meshes:
        mid=f"m{len(meshes)}"; meshes[key]=mid
        subs.append((f'[sub_resource type="BoxMesh" id="{mid}"]',dict(size=f"Vector3({size[0]}, {size[1]}, {size[2]})",material=f'SubResource("{m}")')))
    node(name,"MeshInstance3D",parent,transform=T(*pos,*rot),mesh=f'SubResource("{meshes[key]}")')
def cyl(name,parent,r,h,pos,m,rot=(0,0,0),seg=8,top=None):
    key=("cyl",r,h,m,seg,top)
    if key not in meshes:
        mid=f"m{len(meshes)}"; meshes[key]=mid
        subs.append((f'[sub_resource type="CylinderMesh" id="{mid}"]',dict(top_radius=top if top is not None else r,bottom_radius=r,height=h,radial_segments=seg,rings=1,material=f'SubResource("{m}")')))
    node(name,"MeshInstance3D",parent,transform=T(*pos,*rot),mesh=f'SubResource("{meshes[key]}")')
def node(name,typ,parent,**p):
    hdr=f'[node name="{name}" type="{typ}"'+(f' parent="{parent}"' if parent is not None else "")+"]"
    nodes.append((hdr,p))
def inst_node(name,typ,parent,script,**p):
    q={}
    if "transform" in p: q["transform"]=p.pop("transform")
    q["script"]=f'ExtResource("{script}")'; q.update(p); node(name,typ,parent,**q)

WHEEL_R = 1.0   # visual tyre radius (m)
LIFT = WHEEL_R - 0.8  # body frames were designed around 0.8 m wheels
subs.append(('[sub_resource type="BoxShape3D" id="front_shape"]',dict(size="Vector3(2.8, 1.4, 2.4)")))
subs.append(('[sub_resource type="BoxShape3D" id="rear_shape"]',dict(size="Vector3(2.6, 1.8, 2.8)")))
node("WheelLoader","CharacterBody3D",None,script='ExtResource("1")',wheel_radius=WHEEL_R)
node("FrontShape","CollisionShape3D",".",transform=T(0,0.7,-1.5),shape='SubResource("front_shape")')
node("RearShape","CollisionShape3D",".",transform=T(0,0.9,1.6),shape='SubResource("rear_shape")')
node("Chassis","Node3D",".")
F="Chassis/FrontFrame"; R="Chassis/RearPivot"
node("FrontFrame","Node3D","Chassis",transform=T(0,LIFT,0))
def wheel(name,parent,x,z):
    # Wheel centre sits at world y = WHEEL_R; frames are raised by LIFT.
    node(name,"Node3D",parent,transform=T(x,WHEEL_R-LIFT,z))
    inst_node("Tire","MeshInstance3D",f"{parent}/{name}","3",radius=WHEEL_R,width=0.9,segments=20,lug_depth=0.09)
for n,x,z in [("WheelFL",-1.32,-1.6),("WheelFR",1.32,-1.6)]: wheel(n,F,x,z)
# front frame
box("FrontChassis",F,(1.2,0.7,2.4),(0,1.0,-1.3),"dark")
box("Tower",F,(1.35,1.1,0.9),(0,1.55,-0.75),"yellow")
box("TowerCap",F,(1.4,0.12,0.95),(0,2.12,-0.75),"dark")
for s,nm in [(-1,"L"),(1,"R")]:
    box(f"Fender{nm}",F,(1.0,0.12,2.2),(s*1.32,1.95,-1.6),"dark")
    box(f"FenderLip{nm}",F,(1.0,0.4,0.1),(s*1.32,1.75,-2.75),"dark",rot=(-0.5,0,0))
    box(f"Headlight{nm}",F,(0.22,0.16,0.08),(s*0.62,1.95,-1.22),"lamp")
    node(f"LiftRamBase{nm}","Marker3D",F,transform=T(s*0.5,0.85,-1.25))
box("Hinge",F,(0.7,0.6,0.8),(0,1.0,-0.05),"steel")
A=F+"/ArmPivot"
node("ArmPivot","Node3D",F,transform=T(0,1.7,-1.0))
for s,nm in [(-1,"L"),(1,"R")]:
    box(f"Arm{nm}",A,(0.3,0.52,3.0),(s*0.72,0,-1.4),"yellow")
    box(f"ArmPin{nm}",A,(0.36,0.2,0.2),(s*0.72,0,-2.8),"dark")
    node(f"LiftRamEnd{nm}","Marker3D",A,transform=T(s*0.5,-0.15,-1.45))
box("CrossTube",A,(1.8,0.34,0.34),(0,0.05,-1.6),"yellow")
box("TiltLever",A,(0.3,0.9,0.25),(0,0.45,-1.6),"yellow",rot=(-0.35,0,0))
node("TiltRamBase","Marker3D",A,transform=T(0,0.85,-1.75))
B=A+"/BucketPivot"
node("BucketPivot","Node3D",A,transform=T(0,0,-2.8))
box("BackUpper",B,(3.1,0.75,0.12),(0,-0.12,-0.02),"bucket",rot=(0.25,0,0))
box("BackLower",B,(3.1,0.6,0.12),(0,-0.68,-0.2),"bucket",rot=(-0.55,0,0))
box("TopPlate",B,(3.1,0.12,0.5),(0,0.25,-0.25),"bucket",rot=(-0.2,0,0))
box("BottomPlate",B,(3.1,0.12,1.35),(0,-0.95,-0.9),"bucket")
for s,nm in [(-1,"L"),(1,"R")]:
    box(f"Side{nm}",B,(0.12,1.15,1.6),(s*1.55,-0.4,-0.8),"bucket")
    box(f"SideRib{nm}",B,(0.16,0.16,1.4),(s*1.59,-0.15,-0.75),"dark")
box("Lip",B,(3.1,0.08,0.25),(0,-0.97,-1.62),"teeth")
for i in range(8):
    box(f"Tooth{i}",B,(0.14,0.09,0.3),(-1.33+i*0.38,-0.97,-1.85),"teeth")
box("TiltLug",B,(0.3,0.3,0.25),(0,0.35,0.05),"dark")
node("TiltRamEnd","Marker3D",B,transform=T(0,0.45,0.05))
node("Tip","Marker3D",B,transform=T(0,-0.97,-1.7))
# rams (siblings of chassis parts so they don't inherit arm motion)
for nm in "LR":
    inst_node(f"LiftRam{nm}","Node3D",F,"4",base_path=f'NodePath("../LiftRamBase{nm}")',end_path=f'NodePath("../ArmPivot/LiftRamEnd{nm}")')
inst_node("TiltRam","Node3D",F,"4",base_path='NodePath("../ArmPivot/TiltRamBase")',end_path='NodePath("../ArmPivot/BucketPivot/TiltRamEnd")',barrel_radius=0.12,rod_radius=0.065)
# rear frame
node("RearPivot","Node3D","Chassis",transform=T(0,LIFT,0))
for n,x,z in [("WheelRL",-1.32,1.6),("WheelRR",1.32,1.6)]: wheel(n,R,x,z)
box("RearChassis",R,(1.3,0.6,3.4),(0,0.95,1.75),"dark")
box("Deck",R,(2.3,0.14,1.9),(0,1.8,0.85),"dark")
box("Hood",R,(1.9,0.95,2.1),(0,2.2,2.35),"yellow")
box("HoodTop",R,(1.6,0.1,1.7),(0,2.72,2.4),"dark")
box("HoodSlope",R,(1.9,0.5,0.5),(0,2.55,1.35),"yellow",rot=(0.6,0,0))
box("Grille",R,(1.5,0.8,0.08),(0,2.15,3.42),"black")
box("Counterweight",R,(2.5,1.0,0.65),(0,1.35,3.55),"yellow")
box("CounterweightBand",R,(2.52,0.18,0.67),(0,1.75,3.55),"dark")
box("Bumper",R,(2.6,0.28,0.35),(0,0.85,3.75),"dark")
for s,nm in [(-1,"L"),(1,"R")]:
    box(f"TailLight{nm}",R,(0.24,0.16,0.06),(s*1.0,1.45,3.9),"tail")
    box(f"RearFender{nm}",R,(1.0,0.12,2.2),(s*1.32,1.95,1.6),"dark")
    box(f"RearFenderLip{nm}",R,(1.0,0.4,0.1),(s*1.32,1.75,2.75),"dark",rot=(0.5,0,0))
    box(f"Vent{nm}",R,(0.04,0.4,0.6),(s*0.97,2.25,3.0),"black")
    # railings
    box(f"Rail{nm}",R,(0.05,0.05,2.2),(s*1.02,3.2,2.3),"red")
    for k,z in enumerate([1.3,2.3,3.35]):
        box(f"Post{nm}{k}",R,(0.05,0.55,0.05),(s*1.02,2.95,z),"red")
# ladder (left)
for k,z in enumerate([0.1,0.55]):
    box(f"LadderStile{k}",R,(0.05,1.5,0.05),(-1.3,1.05,z),"yellow")
for k in range(4):
    box(f"LadderRung{k}",R,(0.05,0.04,0.45),(-1.3,0.45+k*0.38,0.33),"dark")
box("LadderRail",R,(0.05,0.9,0.05),(-1.3,2.25,0.1),"red")
# cab
C=R+"/Cab"
node("Cab","Node3D",R,transform=T(0,0,0.85))
box("CabBase",C,(1.75,0.35,1.75),(0,2.03,0),"dark")
for i,(x,z) in enumerate([(-0.82,-0.82),(0.82,-0.82),(-0.82,0.82),(0.82,0.82)]):
    box(f"Pillar{i}",C,(0.12,1.55,0.12),(x,2.95,z),"yellow")
box("GlassFront",C,(1.55,1.45,0.03),(0,2.95,-0.82),"glass")
box("GlassBack",C,(1.55,1.45,0.03),(0,2.95,0.82),"glass")
box("GlassL",C,(0.03,1.45,1.55),(-0.82,2.95,0),"glass")
box("GlassR",C,(0.03,1.45,1.55),(0.82,2.95,0),"glass")
box("Roof",C,(1.95,0.18,1.95),(0,3.8,0),"yellow")
box("Visor",C,(1.95,0.07,0.35),(0,3.72,-1.12),"dark")
box("MirrorL",C,(0.05,0.3,0.2),(-1.1,3.3,-0.75),"dark")
box("MirrorR",C,(0.05,0.3,0.2),(1.1,3.3,-0.75),"dark")
for s,nm in [(-1,"L"),(1,"R")]:
    box(f"WorkLight{nm}",C,(0.24,0.15,0.1),(s*0.65,3.97,-0.85),"lamp")
    box(f"RearWorkLight{nm}",C,(0.24,0.15,0.1),(s*0.65,3.97,0.85),"lamp")
inst_node("Beacon","Node3D",C,"5",transform=T(-0.65,3.98,0.55))
box("Seat",C,(0.55,0.5,0.5),(0,2.45,0.25),"black")
box("Torso",C,(0.46,0.55,0.3),(0,2.78,0.15),"hivis")
box("Head",C,(0.24,0.26,0.24),(0,3.2,0.1),"skin")
box("Cap",C,(0.28,0.08,0.34),(0,3.36,0.06),"dark")
box("Wheel",C,(0.35,0.35,0.04),(0,2.75,-0.25),"black",rot=(-0.8,0,0))
cyl("Exhaust",R,0.09,1.0,(0.55,3.0,2.9),"black",seg=6)
node("ModelLeft","Label3D",R,transform=T(-0.965,2.25,2.0,0,-math.pi/2,0),text='"DW-90"',font_size=72,pixel_size=0.005,modulate="Color(0.12, 0.12, 0.13, 1)",outline_size=0,double_sided="false")
node("ModelRight","Label3D",R,transform=T(0.965,2.25,2.0,0,math.pi/2,0),text='"DW-90"',font_size=72,pixel_size=0.005,modulate="Color(0.12, 0.12, 0.13, 1)",outline_size=0,double_sided="false")
node("PlayerInput","Node",".",script='ExtResource("2")')

out='[gd_scene format=3]\n\n'
for i,pth in [("1","res://scripts/vehicles/wheel_loader.gd"),("2","res://scripts/vehicles/player_loader_input.gd"),("3","res://scripts/vehicles/wheel_visual.gd"),("4","res://scripts/vehicles/hydraulic_ram.gd"),("5","res://scripts/vehicles/beacon.gd")]:
    out+=f'[ext_resource type="Script" path="{pth}" id="{i}"]\n'
out+="\n"
for h,p in subs: out+=h+"\n"+"".join(f"{k} = {fmt(v)}\n" for k,v in p.items())+"\n"
for h,p in nodes: out+=h+"\n"+"".join(f"{k} = {fmt(v)}\n" for k,v in p.items())+"\n"
open("scenes/vehicles/wheel_loader.tscn","w").write(out)
