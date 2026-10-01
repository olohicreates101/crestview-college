from __future__ import annotations

import httpx
import pytest

from app.game_runtime import GameRuntime
from app.game_state import GameAction
from app.main import app


@pytest.mark.anyio
async def test_create_game_session_route_starts_new_session() -> None:
    player_name = "Ada"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/game/sessions",
            json={"player_id": "player-1", "player_name": player_name, "episode_id": "ss1_term1_episode1"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "active"
    assert payload["player_id"] == "player-1"
    assert payload["player_name"] == "Ada"
    assert payload["current_location"] == "school_gate"
    assert payload["scene_id"] == "school_gate_arrival"
    assert payload["game_state"]["player"]["name"] == "Ada"
    assert payload["active_characters"] == ["amaka", "mr_adeyemi"]
    assert set(payload["game_state"]["npcs"]).issuperset({"amaka", "chuka", "sandra", "mr_adeyemi", "mysterious_student"})


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
