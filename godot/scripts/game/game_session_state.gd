extends RefCounted
class_name GameSessionState

var session_id: String = ""
var player: Dictionary = {}
var current_location: String = ""
var day_of_week: String = ""
var time_of_day: String = ""
var active_characters: Array[String] = []
var available_choices: Array[Dictionary] = []
var story_state: Dictionary = {}


static func from_response(payload: Dictionary) -> GameSessionState:
	var state := GameSessionState.new()
	var runtime_state: Dictionary = payload.get("game_state", {})
	state.session_id = str(payload.get("session_id", ""))
	state.player = runtime_state.get("player", {})
	state.current_location = str(payload.get("current_location", ""))
	state.day_of_week = str(payload.get("day_of_week", ""))
	state.time_of_day = str(payload.get("time_of_day", ""))
	state.story_state = runtime_state.get("story_state", {})

	for character_id in payload.get("active_characters", []):
		state.active_characters.append(str(character_id))
	for choice in payload.get("available_choices", []):
		if choice is Dictionary:
			state.available_choices.append(choice)

	return state