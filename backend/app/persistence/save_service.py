from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.database import Base
from app.db.models.save import SaveGameRecord
from app.game_state import GameClock, GameState, Location, WorldState, build_initial_world

GAME_VERSION = "1.0.0"
SCHEMA_VERSION = 1


class SaveValidationError(ValueError):
    """Raised when a save payload is missing required data or uses an unsupported version."""


class GameSaveService:
    def __init__(self, session_factory: Callable[[], Session] | None = None) -> None:
        if session_factory is None:
            if settings.database_url:
                engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
            else:
                database_file = Path(gettempdir()) / f"crestview-save-{uuid.uuid4().hex}.sqlite3"
                engine = create_engine(f"sqlite:///{database_file}", future=True)
            self.session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
            self.engine = engine
        else:
            self.session_factory = session_factory
            self.engine = None

        self.session = self.session_factory()
        if self.engine is not None:
            Base.metadata.create_all(bind=self.engine)

    def get_save_record(self, save_id: str) -> SaveGameRecord:
        with self.session_factory() as session:
            record = session.get(SaveGameRecord, save_id)
            if record is None:
                raise SaveValidationError(f"Save not found: {save_id}")
            return record

    def list_saves(self, player_id: str | None = None) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            query = session.query(SaveGameRecord)
            if player_id is not None:
                query = query.filter(SaveGameRecord.player_id == player_id)
            records = query.order_by(SaveGameRecord.updated_at.desc()).all()
            return [
                {
                    "id": record.id,
                    "player_id": record.player_id,
                    "save_name": record.save_name,
                    "game_version": record.game_version,
                    "schema_version": record.schema_version,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat(),
                    "is_active": record.is_active,
                }
                for record in records
            ]

    def save_game(
        self,
        game_state: GameState,
        runtime_state: dict[str, Any] | None = None,
        save_name: str = "autosave",
        player_id: str | None = None,
    ) -> str:
        payload = self.serialize_game_state(game_state, runtime_state=runtime_state)
        with self.session_factory.begin() as session:
            if player_id is not None:
                existing = (
                    session.query(SaveGameRecord)
                    .filter(SaveGameRecord.player_id == player_id, SaveGameRecord.is_active.is_(True))
                    .order_by(SaveGameRecord.updated_at.desc())
                    .first()
                )
                if existing is not None:
                    existing.is_active = False

            record = SaveGameRecord(
                player_id=player_id,
                save_name=save_name,
                game_version=payload["game_version"],
                schema_version=payload["schema_version"],
                is_active=True,
                payload=payload,
            )
            session.add(record)
            session.flush()
            return record.id

    def load_game(self, save_id: str) -> GameState:
        with self.session_factory() as session:
            record = session.get(SaveGameRecord, save_id)
            if record is None:
                raise SaveValidationError(f"Save not found: {save_id}")

            if record.schema_version != SCHEMA_VERSION:
                raise SaveValidationError(f"Unsupported save schema version: {record.schema_version!r}")

            payload = record.payload
            validated = self.deserialize_game_state(payload)
            validated.runtime_state = payload.get("runtime_state", {})
            return validated

    def delete_game(self, save_id: str) -> bool:
        with self.session_factory.begin() as session:
            record = session.get(SaveGameRecord, save_id)
            if record is None:
                return False
            session.delete(record)
            return True

    def serialize_game_state(self, game_state: GameState, runtime_state: dict[str, Any] | None = None) -> dict[str, Any]:
        world_snapshot = {
            location_id: {
                "id": location.id,
                "name": location.name,
                "description": location.description,
                "available_time_range": list(location.available_time_range) if location.available_time_range else None,
                "allowed_actions": list(location.allowed_actions),
                "connected_locations": list(location.connected_locations),
                "restrictions": list(location.restrictions),
            }
            for location_id, location in game_state.world.locations.items()
        }

        payload = {
            "game_version": GAME_VERSION,
            "schema_version": SCHEMA_VERSION,
            "saved_at": datetime.now(UTC).isoformat(),
            "current_location": game_state.current_location,
            "flags": dict(game_state.flags),
            "active_events": [
                event if isinstance(event, dict) else {"event_type": event.event_type, "message": event.message, "payload": event.payload}
                for event in game_state.active_events
            ],
            "world": {
                "locations": world_snapshot,
            },
            "clock": {
                "current_year": game_state.clock.current_year,
                "current_term": game_state.clock.current_term,
                "current_week": game_state.clock.current_week,
                "day_of_week": game_state.clock.day_of_week,
                "day_index": game_state.clock.day_index,
                "hour": game_state.clock.hour,
                "minute": game_state.clock.minute,
            },
            "runtime_state": runtime_state or {},
        }
        return payload

    def deserialize_game_state(self, payload: dict[str, Any]) -> GameState:
        if not isinstance(payload, dict):
            raise SaveValidationError("Save payload must be a dictionary.")

        schema_version = payload.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            raise SaveValidationError(f"Unsupported save schema version: {schema_version!r}")

        current_location = payload.get("current_location")
        if not isinstance(current_location, str) or not current_location:
            raise SaveValidationError("Save is missing a valid current_location.")

        world_dict = payload.get("world") or {}
        locations = world_dict.get("locations") or {}
        location_map: dict[str, Location] = {}
        for location_id, item in locations.items():
            if not isinstance(item, dict):
                raise SaveValidationError(f"Invalid location payload for {location_id!r}.")
            location_map[location_id] = Location(
                id=str(item.get("id", location_id)),
                name=str(item.get("name", location_id)),
                description=str(item.get("description", "")),
                available_time_range=(
                    tuple(item.get("available_time_range"))
                    if isinstance(item.get("available_time_range"), list)
                    and len(item.get("available_time_range")) == 2
                    else None
                ),
                allowed_actions=list(item.get("allowed_actions", [])),
                connected_locations=list(item.get("connected_locations", [])),
                restrictions=list(item.get("restrictions", [])),
            )

        if not location_map:
            location_map = build_initial_world().locations

        if current_location not in location_map:
            raise SaveValidationError(f"Save location {current_location!r} does not exist in the world graph.")

        clock_payload = payload.get("clock") or {}
        clock = GameClock(
            current_year=str(clock_payload.get("current_year", "SS1")),
            current_term=int(clock_payload.get("current_term", 1)),
            current_week=int(clock_payload.get("current_week", 1)),
            day_of_week=str(clock_payload.get("day_of_week", "Monday")),
            day_index=int(clock_payload.get("day_index", 0)),
            hour=int(clock_payload.get("hour", 7)),
            minute=int(clock_payload.get("minute", 0)),
        )

        state = GameState(
            world=WorldState(locations=location_map),
            current_location=current_location,
            clock=clock,
            flags={str(key): bool(value) for key, value in (payload.get("flags") or {}).items()},
            active_events=[
                {
                    "event_type": item.get("event_type", "UNKNOWN"),
                    "message": item.get("message", ""),
                    "payload": item.get("payload", {}),
                }
                for item in (payload.get("active_events") or [])
            ],
        )
        state.runtime_state = payload.get("runtime_state", {})
        return state
