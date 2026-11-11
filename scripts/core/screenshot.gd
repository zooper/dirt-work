extends Node
## Autoload: saves a PNG of the viewport on the "screenshot" action
## (F12 / gamepad View). Files go to user://screenshots/ — on macOS:
## ~/Library/Application Support/Godot/app_userdata/Dirt Work/screenshots/


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("screenshot"):
		capture()


func capture() -> String:
	if DisplayServer.get_name() == "headless":
		return ""
	DirAccess.make_dir_recursive_absolute("user://screenshots")
	var path := "user://screenshots/dirtwork_%s.png" % Time.get_datetime_string_from_system().replace(":", "-")
	var err := get_viewport().get_texture().get_image().save_png(path)
	var abs_path := ProjectSettings.globalize_path(path)
	print("Screenshot %s: %s" % ["saved" if err == OK else "FAILED", abs_path])
	return abs_path
