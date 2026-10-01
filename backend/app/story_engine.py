from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.game_state import GameAction, GameEngine, GameState, build_initial_world

ALLOWED_CONDITION_TYPES = {
    "FLAG_TRUE",
    "FLAG_FALSE",
    "LOCATION_IS",
    "TIME_BEFORE",
    "TIME_AFTER",
    "RELATIONSHIP_AT_LEAST",
}

ALLOWED_CONSEQUENCE_TYPES = {
    "SET_FLAG",
    "CLEAR_FLAG",
    "ADVANCE_TIME",
    "MOVE_PLAYER",
    "ADD_ITEM",
    "REMOVE_ITEM",
    "ADD_MONEY",
    "CHANGE_RELATIONSHIP",
    "ADD_MEMORY",
    "CHANGE_REPUTATION",
}


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    flag: str | None = None
    location: str | None = None
    time: int | None = None
    character_id: str | None = None
    minimum: int | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in ALLOWED_CONDITION_TYPES:
            raise ValueError(f"Unknown condition type: {value}")
        return value

    def evaluate(self, game_state: GameState | None, story_state: dict[str, Any] | None) -> bool:
        flags = (story_state or {}).get("flags", {}) if story_state else {}
        if self.type == "FLAG_TRUE":
            if self.flag is None:
                raise ValueError("FLAG_TRUE condition requires a flag name.")
            return bool((game_state and game_state.flags.get(self.flag, False)) or flags.get(self.flag, False))
        if self.type == "FLAG_FALSE":
            if self.flag is None:
                raise ValueError("FLAG_FALSE condition requires a flag name.")
            return not bool((game_state and game_state.flags.get(self.flag, False)) or flags.get(self.flag, False))
        if self.type == "LOCATION_IS":
            if self.location is None:
                raise ValueError("LOCATION_IS condition requires a location.")
            if game_state is None:
                return False
            return game_state.current_location == self.location
        if self.type == "TIME_BEFORE":
            if self.time is None:
                raise ValueError("TIME_BEFORE condition requires a time value.")
            if game_state is None:
                return False
            current_minutes = game_state.clock.hour * 60 + game_state.clock.minute
            return current_minutes < self.time
        if self.type == "TIME_AFTER":
            if self.time is None:
                raise ValueError("TIME_AFTER condition requires a time value.")
            if game_state is None:
                return False
            current_minutes = game_state.clock.hour * 60 + game_state.clock.minute
            return current_minutes >= self.time
        if self.type == "RELATIONSHIP_AT_LEAST":
            if self.character_id is None or self.minimum is None:
                raise ValueError("RELATIONSHIP_AT_LEAST condition requires character_id and minimum.")
            scores = (story_state or {}).get("relationship_scores", {})
            return int(scores.get(self.character_id, 0)) >= self.minimum

        raise ValueError(f"Unsupported condition type: {self.type}")


class Consequence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    flag: str | None = None
    minutes: int | None = None
    target: str | None = None
    item_id: str | None = None
    amount: int | float | None = None
    character_id: str | None = None
    delta: int | None = None
    text: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in ALLOWED_CONSEQUENCE_TYPES:
            raise ValueError(f"Unknown consequence type: {value}")
        return value

    def apply(self, game_state: GameState | None, story_state: dict[str, Any]) -> Any:
        flags = story_state.setdefault("flags", {})
        items = story_state.setdefault("items", [])
        memories = story_state.setdefault("memories", [])
        relationship_scores = story_state.setdefault("relationship_scores", {})

        if self.type == "SET_FLAG":
            if self.flag is None:
                raise ValueError("SET_FLAG requires a flag name.")
            flags[self.flag] = True
            if game_state is not None:
                game_state.flags[self.flag] = True
            return True

        if self.type == "CLEAR_FLAG":
            if self.flag is None:
                raise ValueError("CLEAR_FLAG requires a flag name.")
            flags[self.flag] = False
            if game_state is not None:
                game_state.flags[self.flag] = False
            return False

        if self.type == "ADVANCE_TIME":
            if self.minutes is None:
                raise ValueError("ADVANCE_TIME requires a minute value.")
            if game_state is None:
                return None
            game_state.clock.advance_time(self.minutes)
            return game_state.clock

        if self.type == "MOVE_PLAYER":
            if self.target is None:
                raise ValueError("MOVE_PLAYER requires a target location.")
            if game_state is None:
                return None
            engine = GameEngine()
            result = engine.execute(
                GameAction(
                    action_type="MOVE",
                    actor="player",
                    target=self.target,
                    requested_time_cost=self.minutes or 5,
                ),
                game_state,
            )
            return result

        if self.type == "ADD_ITEM":
            if self.item_id is None:
                raise ValueError("ADD_ITEM requires an item_id.")
            if self.item_id not in items:
                items.append(self.item_id)
            return items

        if self.type == "REMOVE_ITEM":
            if self.item_id is None:
                raise ValueError("REMOVE_ITEM requires an item_id.")
            if self.item_id in items:
                items.remove(self.item_id)
            return items

        if self.type == "ADD_MONEY":
            story_state["money"] = int((story_state.get("money", 0) or 0) + (self.amount or 0))
            return story_state["money"]

        if self.type == "CHANGE_RELATIONSHIP":
            if self.character_id is None:
                raise ValueError("CHANGE_RELATIONSHIP requires a character_id.")
            current = int(relationship_scores.get(self.character_id, 0))
            delta = int(self.delta or 0)
            relationship_scores[self.character_id] = current + delta
            return relationship_scores[self.character_id]

        if self.type == "ADD_MEMORY":
            memory_text = self.text or self.flag or "memory added"
            memories.append(memory_text)
            return memories

        if self.type == "CHANGE_REPUTATION":
            story_state["reputation"] = int((story_state.get("reputation", 0) or 0) + (self.amount or 0))
            return story_state["reputation"]

        raise ValueError(f"Unsupported consequence type: {self.type}")


class DialogueLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    speaker_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    emotion: str = Field(default="neutral", min_length=1)
    pose: str | None = None
    conditions: list[Condition] = Field(default_factory=list)
    next_line_id: str | None = None


class Choice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    conditions: list[Condition] = Field(default_factory=list)
    consequences: list[Consequence] = Field(default_factory=list)
    next_scene_id: str | None = None

    def is_available(self, game_state: GameState | None, story_state: dict[str, Any]) -> bool:
        return all(condition.evaluate(game_state, story_state) for condition in self.conditions)


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    episode_id: str = Field(..., min_length=1)
    location_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    characters: list[str] = Field(default_factory=list)
    dialogue: list[DialogueLine] = Field(default_factory=list)
    choices: list[Choice] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)
    entry_consequences: list[Consequence] = Field(default_factory=list)
    exit_consequences: list[Consequence] = Field(default_factory=list)
    next_scene_id: str | None = None
    is_terminal: bool = False

    def is_available(self, game_state: GameState | None, story_state: dict[str, Any]) -> bool:
        return all(condition.evaluate(game_state, story_state) for condition in self.conditions)


class Episode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    year: str = Field(..., min_length=1)
    term: int = Field(..., ge=1, le=3)
    episode_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    starting_scene_id: str = Field(..., min_length=1)
    scene_ids: list[str] = Field(default_factory=list)
    completion_flag: str = Field(..., min_length=1)


class StoryEngine:
    DATA_DIR = Path(__file__).resolve().parents[1] / "game-data"

    def __init__(self, game_state: GameState | None = None) -> None:
        self.game_state = game_state or GameState(world=build_initial_world(), current_location="school_gate")
        self.story_state: dict[str, Any] = {
            "flags": self.game_state.flags,
            "relationship_scores": {},
            "items": [],
            "money": 0,
            "memories": [],
            "reputation": 0,
        }
        self.characters = self._load_character_data()
        self.episode: Episode | None = None
        self.active_episode_id: str | None = None
        self.current_scene_id: str | None = None
        self.episodes: dict[str, Episode] = {}
        self.scenes: dict[str, Scene] = {}
        self.episode_completion_flag: str | None = None

    def _load_character_data(self) -> dict[str, dict[str, Any]]:
        directory = self.DATA_DIR / "characters"
        if not directory.exists():
            return {}

        characters: dict[str, dict[str, Any]] = {}
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            character_id = payload.get("id", path.stem)
            characters[character_id] = payload
        return characters

    def load_episode(self, episode_id: str) -> Episode:
        episode_path = self.DATA_DIR / "episodes" / f"{episode_id}.json"
        if not episode_path.exists():
            raise ValueError(f"Episode not found: {episode_id}")

        payload = json.loads(episode_path.read_text(encoding="utf-8"))
        if "episode" not in payload or "scenes" not in payload:
            raise ValueError(f"Episode file is malformed: {episode_path}")

        episode = Episode.model_validate(payload["episode"])
        scenes = [Scene.model_validate(scene) for scene in payload["scenes"]]

        self.scenes = {scene.id: scene for scene in scenes}
        self.episode = episode
        self.episodes[episode.id] = episode

        if set(episode.scene_ids) != set(self.scenes):
            raise ValueError(f"Scene IDs do not match the episode declared list for {episode.id}")

        for scene in scenes:
            if scene.episode_id != episode.id:
                raise ValueError(f"Scene {scene.id} belongs to the wrong episode.")
            if scene.next_scene_id and scene.next_scene_id not in self.scenes:
                raise ValueError(f"Scene {scene.id} references an invalid next scene: {scene.next_scene_id}")
            for choice in scene.choices:
                if choice.next_scene_id and choice.next_scene_id not in self.scenes:
                    raise ValueError(f"Choice {choice.id} in scene {scene.id} references an invalid next scene.")
            for character_id in scene.characters:
                if character_id not in self.characters:
                    raise ValueError(f"Scene {scene.id} references an unknown character: {character_id}")
            for line in scene.dialogue:
                if line.speaker_id not in self.characters:
                    raise ValueError(f"Dialogue line {line.id} references an unknown character: {line.speaker_id}")

        return episode

    def start_episode(self, episode_id: str) -> Episode:
        episode = self.load_episode(episode_id)
        self.active_episode_id = episode.id
        self.episode = episode
        self.episode_completion_flag = episode.completion_flag
        self.current_scene_id = episode.starting_scene_id
        self._apply_scene_entry(self.get_current_scene())
        return episode

    def get_scene(self, scene_id: str) -> Scene:
        if scene_id not in self.scenes:
            raise ValueError(f"Unknown scene id: {scene_id}")
        return self.scenes[scene_id]

    def get_current_scene(self) -> Scene:
        if self.current_scene_id is None:
            raise ValueError("No episode has been started.")
        return self.get_scene(self.current_scene_id)

    def get_available_choices(self) -> list[Choice]:
        scene = self.get_current_scene()
        return [choice for choice in scene.choices if choice.is_available(self.game_state, self.story_state)]

    def get_choice(self, choice_id: str) -> Choice | None:
        scene = self.get_current_scene()
        for choice in scene.choices:
            if choice.id == choice_id:
                return choice
        return None

    def _apply_scene_entry(self, scene: Scene) -> None:
        for consequence in scene.entry_consequences:
            consequence.apply(self.game_state, self.story_state)

    def _apply_scene_exit(self, scene: Scene) -> None:
        for consequence in scene.exit_consequences:
            consequence.apply(self.game_state, self.story_state)

    def choose(self, choice_id: str) -> dict[str, Any]:
        scene = self.get_current_scene()
        choice = self.get_choice(choice_id)
        if choice is None:
            raise ValueError(f"Choice not found in current scene: {choice_id}")
        if not choice.is_available(self.game_state, self.story_state):
            raise ValueError(f"Choice is unavailable: {choice_id}")

        for consequence in choice.consequences:
            consequence.apply(self.game_state, self.story_state)

        self._apply_scene_exit(scene)

        next_scene_id = choice.next_scene_id or scene.next_scene_id
        if next_scene_id is None:
            raise ValueError(f"Choice {choice_id} does not lead to a valid scene.")

        self.current_scene_id = next_scene_id
        next_scene = self.get_scene(next_scene_id)
        self._apply_scene_entry(next_scene)

        if self.episode_completion_flag and self.game_state.flags.get(self.episode_completion_flag):
            self.story_state.setdefault("completed_episodes", []).append(self.active_episode_id)

        return {
            "choice_id": choice_id,
            "next_scene_id": next_scene_id,
            "scene": next_scene,
        }


__all__ = [
    "Choice",
    "Condition",
    "Consequence",
    "DialogueLine",
    "Episode",
    "Scene",
    "StoryEngine",
]
