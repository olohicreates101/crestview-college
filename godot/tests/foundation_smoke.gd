extends SceneTree


func _initialize() -> void:
	call_deferred("_run_smoke_test")


func _run_smoke_test() -> void:
	var menu_scene := load("res://scenes/main/main_menu.tscn") as PackedScene
	var menu := menu_scene.instantiate() as Control
	root.add_child(menu)
	current_scene = menu
	await process_frame
	menu.get_node("%NewGameButton").pressed.emit()
	await process_frame
	if current_scene == null or current_scene.scene_file_path != "res://scenes/game/game.tscn":
		_fail("New Game did not open the placeholder game scene.")
		return
	print("scene_flow=ok")

	var api_client := ApiClient.new()
	root.add_child(api_client)
	api_client.game_session_received.connect(_on_session_received)
	api_client.request_failed.connect(_on_request_failed)
	var error := api_client.create_game_session("godot-smoke", "Ada")
	if error != OK:
		_fail("Could not start API request: %s" % error)
		return
	create_timer(10.0).timeout.connect(_on_timeout)


func _on_session_received(state: GameSessionState) -> void:
	if state.session_id.is_empty() or state.player.get("name") != "Ada":
		_fail("Session response did not preserve the session id and player name.")
		return
	if state.current_location != "school_gate" or state.active_characters != ["amaka", "mr_adeyemi"]:
		_fail("Session response did not populate the expected scene state.")
		return
	print("api_session=ok location=%s active_characters=%s" % [state.current_location, state.active_characters])
	quit(0)


func _on_request_failed(message: String) -> void:
	_fail(message)


func _on_timeout() -> void:
	_fail("Timed out waiting for the backend session response.")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)