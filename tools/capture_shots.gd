extends SceneTree
## Dev tool: renders fixed camera shots of the quarry to PNG for visual review.
## Needs a real display/GL context (not --headless), e.g. on a Linux server:
##   DISPLAY=:97 godot --path . -s tools/capture_shots.gd -- <out_dir>
## Shots: "play" (follow camera as in-game), "concept" (low 3/4 hero view of the
## loader, framed like the concept art), "overview" (wide establishing view).

const SHOTS := {
	"concept": [Vector3(-7.5, 2.2, 3.0), Vector3(1.0, 2.0, 9.0)],
	"overview": [Vector3(-30, 22, 60), Vector3(0, 2, -10)],
}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var out := args[0] if args.size() > 0 else "user://shots"
	DirAccess.make_dir_recursive_absolute(out)
	root.size = Vector2i(1600, 900)
	var level: Node = load("res://scenes/levels/quarry.tscn").instantiate()
	root.add_child(level)
	var loader := level.get_node("WheelLoader") as WheelLoader
	(loader.get_node("PlayerInput") as PlayerLoaderInput).enabled = false
	loader.lift_angle = 8.0
	loader.tilt_angle = -15.0
	for i in 90:
		await process_frame
	_save(out + "/play.png")
	var follow := level.get_node("FollowCamera") as Node3D
	follow.set_process(false)
	var cam := level.get_node("FollowCamera/Camera3D") as Camera3D
	for shot in SHOTS:
		var spec: Array = SHOTS[shot]
		cam.global_position = spec[0]
		cam.look_at(spec[1])
		for i in 20:
			await process_frame
		_save("%s/%s.png" % [out, shot])
	quit()


func _save(path: String) -> void:
	var img := root.get_texture().get_image()
	img.save_png(path)
	print("saved ", path)
