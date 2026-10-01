from __future__ import annotations

from app.game_runtime import GameRuntime
from app.game_state import GameAction


def test_runtime_starts_session_and_tracks_core_systems() -> None:
    runtime = GameRuntime()

    runtime.start_session(player_id="player-1", episode_id="ss1_term1_episode1")

    assert runtime.session_id is not None
    assert runtime.player_id == "player-1"
    assert runtime.game_state.current_location == "school_gate"
    assert runtime.story_engine.active_episode_id == "ss1_term1_episode1"
    assert runtime.npc_simulator is not None
    assert "amaka" in runtime.npc_simulator.npcs


def test_runtime_executes_player_action_and_advances_time() -> None:
    runtime = GameRuntime()
    runtime.start_session(player_id="player-1", episode_id="ss1_term1_episode1")

    result = runtime.execute_action(
        GameAction(action_type="MOVE", actor="player", target="corridor", requested_time_cost=5)
    )

    assert result.success is True
    assert runtime.game_state.current_location == "corridor"
    assert runtime.game_state.clock.hour >= 7
    assert runtime.game_state.clock.minute >= 5


def test_runtime_snapshot_and_save_round_trip_preserve_session_state() -> None:
    runtime = GameRuntime()
    runtime.start_session(player_id="player-1", episode_id="ss1_term1_episode1")
    runtime.story_engine.story_state["relationship_scores"]["amaka"] = 42
    runtime.phone_engine.create_conversation(["player-1", "amaka"], title="Amaka")

    snapshot = runtime.snapshot()
    assert snapshot["story_state"]["current_episode"] == "ss1_term1_episode1"
    assert snapshot["relationships"]["amaka"]["trust"] >= 0

    save_id = runtime.save_game(save_name="runtime-checkpoint", player_id="player-1")
    loaded = runtime.load_game(save_id)

    assert loaded.current_location == runtime.game_state.current_location
    assert getattr(loaded, "runtime_state", {}).get("player", {}).get("id") == "player-1"
