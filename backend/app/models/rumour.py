from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Rumour(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    origin_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    current_story: str = Field(..., min_length=1)
    known_by: list[str] = Field(default_factory=list)
    credibility: int = Field(..., ge=0, le=100)
    spread_rate: int = Field(..., ge=0, le=100)
    created_at: datetime
    status: str = Field(..., min_length=1)
