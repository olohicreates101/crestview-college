extends Node
class_name ApiClient

signal game_session_received(state: GameSessionState)
signal request_failed(message: String)

@export var base_url: String = "http://127.0.0.1:8000"

var _http_request: HTTPRequest
var _request_pending: bool = false


func _ready() -> void:
	_http_request = HTTPRequest.new()
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


func create_game_session(
		player_id: String,
		player_name: String,
		episode_id: String = "ss1_term1_episode1"
) -> Error:
	if _request_pending:
		return ERR_BUSY

	var request_body := {
		"player_id": player_id,
		"player_name": player_name,
		"episode_id": episode_id,
	}
	_request_pending = true
	var error := _http_request.request(
		"%s/game/sessions" % base_url.trim_suffix("/"),
		PackedStringArray(["Content-Type: application/json"]),
		HTTPClient.METHOD_POST,
		JSON.stringify(request_body)
	)
	if error != OK:
		_request_pending = false
		request_failed.emit("Could not start session request: %s" % error)
	return error


func _on_request_completed(
		result: int,
		response_code: int,
		_headers: PackedStringArray,
		body: PackedByteArray
) -> void:
	_request_pending = false
	if result != HTTPRequest.RESULT_SUCCESS:
		request_failed.emit("Session request failed with network result %s." % result)
		return
	if response_code < 200 or response_code >= 300:
		request_failed.emit("Session request returned HTTP %s." % response_code)
		return

	var json := JSON.new()
	var parse_error := json.parse(body.get_string_from_utf8())
	if parse_error != OK or not json.data is Dictionary:
		request_failed.emit("Session response was not a valid JSON object.")
		return

	game_session_received.emit(GameSessionState.from_response(json.data))