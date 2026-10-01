from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Memory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    actor_id: str = Field(..., min_length=1)
    event: str = Field(..., min_length=1)
    emotion: str = Field(..., min_length=1)
    importance: MemoryImportance
    timestamp: datetime
    expiration: datetime | None = None
    related_npc_ids: list[str] = Field(default_factory=list)
    related_story_id: str | None = None
