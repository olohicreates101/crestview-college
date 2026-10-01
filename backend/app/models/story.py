from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SchoolYear(str, Enum):
    SS1 = "SS1"
    SS2 = "SS2"
    SS3 = "SS3"


class StoryState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_year: SchoolYear
    current_term: int = Field(..., ge=1, le=3)
    current_episode: int = Field(..., ge=1)
    current_scene: str = Field(..., min_length=1)
    completed_episodes: list[int] = Field(default_factory=list)
    active_storylines: list[str] = Field(default_factory=list)
    story_flags: list[str] = Field(default_factory=list)
    major_choices: list[str] = Field(default_factory=list)
    unlocked_events: list[str] = Field(default_factory=list)
    unlocked_locations: list[str] = Field(default_factory=list)
