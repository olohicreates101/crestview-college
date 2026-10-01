extends Control

@onready var new_game_button: Button = %NewGameButton


func _ready() -> void:
	new_game_button.pressed.connect(_on_new_game_pressed)


func _on_new_game_pressed() -> void:
	var error := get_tree().change_scene_to_file("res://scenes/game/game.tscn")
	if error != OK:
		push_error("Could not open the placeholder game scene: %s" % error)