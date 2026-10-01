from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.game_runtime import GameRuntime
from app.game_state import GameState, build_initial_world
from app.persistence import GameSaveService, SaveValidationError

app = FastAPI(title=settings.app_name)

save_service = GameSaveService()


class SaveRequest(BaseModel):
    save_name: str = Field(default="autosave", min_length=1, max_length=120)
    player_id: str | None = None
    runtime_state: dict[str, Any] | None = None
    game_state: dict[str, Any] | None = None


class SaveResponse(BaseModel):
    save_id: str
    save_name: str
    schema_version: int
    game_version: str


class GameSessionRequest(BaseModel):
    player_id: str | None = None
    player_name: str | None = None
    episode_id: str = "ss1_term1_episode1"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/game/sessions")
def create_game_session(request: GameSessionRequest) -> dict[str, Any]:
    runtime = GameRuntime(
        player_id=request.player_id or "player",
        player_name=request.player_name or (request.player_id or "player"),
        episode_id=request.episode_id,
    )

    scene = runtime.story_engine.get_current_scene()
    choices = runtime.story_engine.get_available_choices()
    payload = runtime.snapshot()

    # Scene-local active characters come from the authored episode data. The NPC
    # registry still stores the full simulated world roster, which may include
    # characters not currently present in the active scene.
    active_characters = list(scene.characters)

    return {
        "status": "active",
        "session_id": runtime.session_id,
        "player_id": runtime.player_id,
        "player_name": runtime.player_name,
        "episode_id": runtime.story_engine.active_episode_id,
        "scene_id": scene.id,
        "scene_title": scene.title,
        "location_id": runtime.game_state.current_location,
        "current_location": runtime.game_state.current_location,
        "day_of_week": runtime.game_state.clock.day_of_week,
        "time_of_day": f"{runtime.game_state.clock.hour:02d}:{runtime.game_state.clock.minute:02d}",
        "active_characters": active_characters,
        "available_choices": [
            {
                "id": choice.id,
                "text": choice.text,
                "next_scene_id": choice.next_scene_id,
            }
            for choice in choices
        ],
        "game_state": payload,
    }


@app.post("/saves", response_model=SaveResponse)
def create_save(request: SaveRequest) -> SaveResponse:
    game_state = request.game_state
    if not game_state:
        state = GameState(world=build_initial_world(), current_location="school_gate")
        save_id = save_service.save_game(state, runtime_state=request.runtime_state, save_name=request.save_name, player_id=request.player_id)
    else:
        try:
            state = save_service.deserialize_game_state(game_state)
        except SaveValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        save_id = save_service.save_game(state, runtime_state=request.runtime_state or {}, save_name=request.save_name, player_id=request.player_id)

    record = save_service.get_save_record(save_id)
    return SaveResponse(save_id=record.id, save_name=record.save_name, schema_version=record.schema_version, game_version=record.game_version)


@app.get("/saves")
def list_saves(player_id: str | None = None) -> list[dict[str, Any]]:
    return save_service.list_saves(player_id=player_id)


@app.get("/saves/{save_id}")
def get_save(save_id: str) -> dict[str, Any]:
    try:
        record = save_service.get_save_record(save_id)
    except SaveValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "save_id": record.id,
        "player_id": record.player_id,
        "save_name": record.save_name,
        "game_version": record.game_version,
        "schema_version": record.schema_version,
        "updated_at": record.updated_at.isoformat(),
        "payload": record.payload,
    }


@app.delete("/saves/{save_id}")
def delete_save(save_id: str) -> dict[str, str | bool]:
    deleted = save_service.delete_game(save_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Save not found: {save_id}")
    return {"save_id": save_id, "deleted": True}
