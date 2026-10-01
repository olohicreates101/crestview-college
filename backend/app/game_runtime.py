from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from app.game_state import GameAction, GameEngine, GameState, build_initial_world
from app.npc_simulation import NPCSimulator
from app.persistence import GameSaveService
from app.phone import PhoneEngine
from app.story_engine import StoryEngine


class GameRuntime:
    """Central coordinator for the in-memory runtime.

    The runtime intentionally stays thin and delegates gameplay rules to the
    existing GameEngine, StoryEngine, NPC simulator, and phone engine. It acts as
    the single orchestration boundary that keeps the backend authoritative without
    replacing the subsystems already in place.
    """

    def __init__(
        self,
        game_state: GameState | None = None,
        story_engine: StoryEngine | None = None,
        phone_engine: PhoneEngine | None = None,
        npc_simulator: NPCSimulator | None = None,
        save_service: GameSaveService | None = None,
        session_id: str | None = None,
        player_id: str = "player",
        episode_id: str | None = None,
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.player_id = player_id
        self.session_started_at = datetime.now(UTC)

        self.game_state = game_state or GameState(world=build_initial_world(), current_location="school_gate")
        self.engine = GameEngine()
        self.story_engine = story_engine or StoryEngine(self.game_state)
        self.phone_engine = phone_engine or self.story_engine.phone_engine
        self.npc_simulator = npc_simulator or NPCSimulator(self.game_state)
        self.save_service = save_service or GameSaveService()

        self.story_engine.story_state.setdefault("flags", self.game_state.flags)
        self.story_engine.story_state.setdefault("relationship_scores", {})
        self.story_engine.story_state.setdefault("items", [])
        self.story_engine.story_state.setdefault("money", 0)
        self.story_engine.story_state.setdefault("memories", [])
        self.story_engine.story_state.setdefault("reputation", 0)
        self.story_engine.story_state.setdefault("recent_conversation", [])
        self.story_engine.story_state["phone_engine"] = self.phone_engine
        self.story_engine.story_state["phone_state"] = self.phone_engine.phone_state

        if not self.npc_simulator.npcs:
            self.npc_simulator.register_default_npcs()

        self.runtime_state: dict[str, Any] = {}
        self.active_episode_id: str | None = None

        if episode_id is not None:
            self.start_session(player_id=self.player_id, episode_id=episode_id)
        else:
            self._sync_runtime_state()

    def start_session(self, player_id: str = "player", episode_id: str | None = None) -> GameState:
        self.player_id = player_id
        self.session_id = str(uuid.uuid4())
        self.session_started_at = datetime.now(UTC)

        self.game_state = GameState(world=build_initial_world(), current_location="school_gate")
        self.engine = GameEngine()
        self.story_engine = StoryEngine(self.game_state)
        self.phone_engine = self.story_engine.phone_engine
        self.npc_simulator = NPCSimulator(self.game_state)
        self.npc_simulator.register_default_npcs()

        self.story_engine.story_state["flags"] = self.game_state.flags
        self.story_engine.story_state["relationship_scores"] = {}
        self.story_engine.story_state["items"] = []
        self.story_engine.story_state["money"] = 0
        self.story_engine.story_state["memories"] = []
        self.story_engine.story_state["reputation"] = 0
        self.story_engine.story_state["recent_conversation"] = []
        self.story_engine.story_state["phone_engine"] = self.phone_engine
        self.story_engine.story_state["phone_state"] = self.phone_engine.phone_state
        self.active_episode_id = episode_id

        if episode_id is not None:
            self.story_engine.start_episode(episode_id)
            self.active_episode_id = self.story_engine.active_episode_id

        self._sync_runtime_state()
        return self.game_state

    def execute_action(self, action: GameAction | dict[str, Any]) -> Any:
        if isinstance(action, dict):
            action = GameAction(**action)

        result = self.engine.execute(action, self.game_state)
        self.story_engine.story_state["flags"] = self.game_state.flags
        self.story_engine.story_state["phone_engine"] = self.phone_engine
        self.story_engine.story_state["phone_state"] = self.phone_engine.phone_state
        self.npc_simulator.update_for_game_time()
        self._sync_runtime_state()
        return result

    def advance_time(self, minutes: int) -> GameState:
        self.game_state.clock.advance_time(minutes)
        self.npc_simulator.update_for_game_time()
        self._sync_runtime_state()
        return self.game_state

    def process_conversation(self, character_id: str, player_message: str, provider: Any | None = None) -> Any:
        response = self.story_engine.start_ai_conversation(character_id, player_message, provider=provider)
        self.story_engine.story_state["flags"] = self.game_state.flags
        self._sync_runtime_state()
        return response

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): GameRuntime._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [GameRuntime._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [GameRuntime._json_safe(item) for item in value]
        if isinstance(value, set):
            return [GameRuntime._json_safe(item) for item in sorted(value, key=lambda item: str(item))]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if hasattr(value, "model_dump"):
            return GameRuntime._json_safe(value.model_dump(mode="python"))
        if hasattr(value, "dict"):
            return GameRuntime._json_safe(value.dict())
        return value

    def snapshot(self) -> dict[str, Any]:
        story_state = self.story_engine.story_state
        phone_state = self._json_safe(self.phone_engine.phone_state.model_dump(mode="python"))
        relationships: dict[str, Any] = {}
        for npc_id, value in (story_state.get("relationship_scores") or {}).items():
            relationships[npc_id] = {
                "player_id": self.player_id,
                "npc_id": npc_id,
                "trust": int(value),
                "closeness": int(value) // 2,
                "respect": max(0, int(value) // 3),
                "resentment": 0,
                "romantic_interest": 0,
                "status": "neutral" if int(value) == 0 else "friendly",
                "history": [],
            }

        story_snapshot = {
            "current_year": self.game_state.clock.current_year,
            "current_term": self.game_state.clock.current_term,
            "current_episode": self.active_episode_id or self.story_engine.active_episode_id,
            "current_scene": self.story_engine.current_scene_id,
            "completed_episodes": list(story_state.get("completed_episodes", [])),
            "active_storylines": list(story_state.get("active_storylines", [])),
            "story_flags": sorted(self.game_state.flags.keys()),
            "major_choices": list(story_state.get("major_choices", [])),
            "unlocked_events": list(story_state.get("unlocked_events", [])),
            "unlocked_locations": list(story_state.get("unlocked_locations", [])),
        }

        npcs = {
            npc_id: {
                "npc_id": npc.npc_id,
                "current_location": npc.current_location,
                "current_activity": npc.current_activity.value,
                "mood": npc.mood.value,
                "active_goal": npc.active_goal.model_dump(mode="python") if npc.active_goal else None,
                "schedule_id": npc.schedule_id,
                "schedule_position": npc.schedule_position,
                "last_updated": npc.last_updated,
                "available_for_interaction": npc.available_for_interaction,
            }
            for npc_id, npc in self.npc_simulator.npcs.items()
        }

        snapshot = {
            "player": {
                "id": self.player_id,
                "name": self.player_id,
                "money": float(story_state.get("money", 0)),
                "current_location": self.game_state.current_location,
                "current_mood": "focused",
            },
            "inventory": [
                {"item_id": item, "quantity": 1, "location": "bag", "story_relevance": "school"}
                for item in story_state.get("items", [])
            ],
            "relationships": relationships,
            "memories": list(story_state.get("memories", [])),
            "secrets": list(story_state.get("secrets", [])),
            "rumours": list(story_state.get("rumours", [])),
            "phone_state": phone_state,
            "story_state": story_snapshot,
            "npcs": npcs,
        }
        self.runtime_state = self._json_safe(snapshot)
        self.game_state.runtime_state = self.runtime_state
        return self.runtime_state

    def _sync_runtime_state(self) -> None:
        self.story_engine.story_state.setdefault("flags", self.game_state.flags)
        if "relationship_scores" not in self.story_engine.story_state:
            self.story_engine.story_state["relationship_scores"] = {}
        self.story_engine.story_state["phone_engine"] = self.phone_engine
        self.story_engine.story_state["phone_state"] = self.phone_engine.phone_state
        self.story_engine.story_state["flags"] = self.game_state.flags
        self.runtime_state = self.snapshot()
        self.game_state.runtime_state = self.runtime_state

    def save_game(self, save_name: str = "autosave", player_id: str | None = None) -> str:
        player_id = player_id or self.player_id
        self._sync_runtime_state()
        safe_runtime = self._json_safe(self.runtime_state)
        save_id = self.save_service.save_game(
            self.game_state,
            runtime_state=safe_runtime,
            save_name=save_name,
            player_id=player_id,
        )
        self.last_save_id = save_id
        return save_id

    def load_game(self, save_id: str) -> GameState:
        loaded = self.save_service.load_game(save_id)
        self.game_state = loaded
        self.engine = GameEngine()
        self.story_engine = StoryEngine(self.game_state)
        self.phone_engine = self.story_engine.phone_engine
        self.npc_simulator = NPCSimulator(self.game_state)
        self.npc_simulator.register_default_npcs()

        runtime_snapshot = getattr(self.game_state, "runtime_state", {}) or {}
        self.story_engine.story_state["flags"] = self.game_state.flags
        self.story_engine.story_state["relationship_scores"] = runtime_snapshot.get("relationships", {})
        if isinstance(self.story_engine.story_state["relationship_scores"], dict):
            normalized_relationships: dict[str, int] = {}
            for npc_id, data in self.story_engine.story_state["relationship_scores"].items():
                if isinstance(data, dict):
                    normalized_relationships[npc_id] = int(data.get("trust", 0))
            self.story_engine.story_state["relationship_scores"] = normalized_relationships
        self.story_engine.story_state["items"] = [
            item.get("item_id", item) for item in runtime_snapshot.get("inventory", []) if isinstance(item, dict)
        ]
        self.story_engine.story_state["money"] = float(runtime_snapshot.get("player", {}).get("money", 0))
        self.story_engine.story_state["memories"] = list(runtime_snapshot.get("memories", []))
        self.story_engine.story_state["phone_state"] = runtime_snapshot.get("phone_state", {})
        self.story_engine.story_state["recent_conversation"] = []
        self.story_engine.story_state["completed_episodes"] = runtime_snapshot.get("story_state", {}).get("completed_episodes", [])
        self.active_episode_id = runtime_snapshot.get("story_state", {}).get("current_episode")
        self.player_id = str(runtime_snapshot.get("player", {}).get("id", self.player_id))
        self.runtime_state = runtime_snapshot
        self.game_state.runtime_state = runtime_snapshot
        return self.game_state


__all__ = ["GameRuntime"]
