from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


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
