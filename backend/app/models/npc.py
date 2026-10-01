from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .player import Appearance


class NPCTier(str, Enum):
    CORE = "core"
    SUPPORTING = "supporting"
    BACKGROUND = "background"


class NPC(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=12, le=80)
    class_name: str = Field(..., alias="class", min_length=1)
    appearance: Appearance
    personality: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    current_location: str = Field(..., min_length=1)
    current_mood: str = Field(..., min_length=1)
    secrets: list[str] = Field(default_factory=list)
    memory_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    schedule: list[str] = Field(default_factory=list)
    speech_style: str = Field(..., min_length=1)
    slang_level: int = Field(..., ge=0, le=100)
    tier: NPCTier = NPCTier.SUPPORTING
