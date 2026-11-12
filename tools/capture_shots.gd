extends SceneTree
## Dev tool: renders the fixed visual-review shots required by docs/ART_DIRECTION.md.
## Needs a real display/GL context (not --headless), e.g. on Linux:
##   tools/render_preview.sh <out_dir>            (Xvfb + lavapipe, Mobile renderer)
##   DISPLAY=:0 godot --path . -s tools/capture_shots.gd -- <out_dir>   (real GPU)
## Files are written as JPEG (compact enough to commit as review records).
##
## The loader spawns at (0, 0, 10) facing -Z. Each shot sets the hydraulics
## (lift/tilt degrees) and a camera position/target.

const SHOTS := [
	# name, camera, target, lift, tilt
	["hero", Vector3(-3.5, 3.4, 63.5), Vector3(-18.5, 3.0, 70.5), 55.0, 22.0],  # reference composition: loader dumping into the hauler
	["side", Vector3(-14.0, 2.3, 10.0), Vector3(0.0, 2.0, 10.0), 0.0, 0.0],
	["front34", Vector3(7.5, 3.0, 1.5), Vector3(0.0, 1.9, 8.5), 0.0, -10.0],
	["front", Vector3(0.0, 2.6, -5.0), Vector3(0.0, 2.0, 8.0), 5.0, -10.0],
	["rear", Vector3(3.0, 3.0, 25.0), Vector3(0.0, 2.0, 10.0), 0.0, 0.0],
	["bucket_low", Vector3(-9.0, 1.6, 3.0), Vector3(0.0, 1.0, 6.0), -23.0, 0.0],
	["overview", Vector3(-30, 22, 60), Vector3(0, 2, -10), 0.0, 0.0],
	["cab_detail", Vector3(-3.4, 3.7, 11.3), Vector3(0.0, 3.3, 11.0), 0.0, 0.0],   # interior through the side glass
]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var out := args[0] if args.size() > 0 else "user://shots"
	DirAccess.make_dir_recursive_absolute(out)
	root.size = Vector2i(1600, 900)
	var level: Node = load("res://scenes/levels/quarry.tscn").instantiate()
	if OS.get_environment("DW_PREVIEW_NO_FOG") == "1":
		# Mesa lavapipe crashes on Godot 4.3 fog; previews only.
		(level.get_node("WorldEnvironment") as WorldEnvironment).environment.fog_enabled = false
	root.add_child(level)
	var loader := level.get_node("WheelLoader") as WheelLoader
	(loader.get_node("PlayerInput") as PlayerLoaderInput).enabled = false
	loader.lift_angle = 8.0
	loader.tilt_angle = -15.0
	for i in 90:
		await process_frame
	var only := OS.get_environment("DW_SHOTS").split(",", false)   # e.g. DW_SHOTS=hero,side
	var want := func(n: String) -> bool: return only.is_empty() or only.has(n)
	if want.call("play"):
		_save(out + "/play.jpg")   # gameplay chase camera
	var follow := level.get_node("FollowCamera") as FollowCamera
	follow.set_process(false)
	var cam := level.get_node("FollowCamera/Camera3D") as Camera3D
	var spawn := loader.global_transform
	# Loading pose next to the parked hauler (reference composition).
	var loading := Transform3D(Basis(Vector3.UP, 1.08), Vector3(-15.9, 0.05, 72.9))
	for shot in SHOTS:
		if not want.call(shot[0]):
			continue
		loader.global_transform = loading if shot[0] == "hero" else spawn
		loader.speed = 0.0
		loader.bucket_fill = 1.0 if shot[0] == "hero" else 0.0
		loader.lift_angle = shot[3]
		loader.tilt_angle = shot[4]
		cam.global_position = shot[1]
		cam.look_at(shot[2])
		for i in 20:
			await process_frame
		_save("%s/%s.jpg" % [out, shot[0]])
	# In-cab view as the player sees it.
	if not want.call("cab"):
		quit()
		return
	loader.global_transform = spawn
	loader.bucket_fill = 0.0
	loader.lift_angle = 8.0
	loader.tilt_angle = -15.0
	follow.set_process(true)
	follow.mode = FollowCamera.Mode.CAB
	follow.head_pitch = follow.cab_default_pitch
	for i in 20:
		await process_frame
	_save(out + "/cab.jpg")
	quit()


func _save(path: String) -> void:
	var img := root.get_texture().get_image()
	var err := img.save_jpg(path, 0.86) if path.ends_with(".jpg") else img.save_png(path)
	print("saved " if err == OK else "FAILED ", path)
