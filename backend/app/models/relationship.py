from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RelationshipStatus(str, Enum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    RIVAL = "rival"
    ENEMY = "enemy"
    CRUSH = "crush"
    DATING = "dating"


class Relationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: str = Field(..., min_length=1)
    npc_id: str = Field(..., min_length=1)
    trust: int = Field(..., ge=0, le=100)
    closeness: int = Field(..., ge=0, le=100)
    respect: int = Field(..., ge=0, le=100)
    resentment: int = Field(..., ge=0, le=100)
    romantic_interest: int = Field(..., ge=0, le=100)
    status: RelationshipStatus
    history: list[str] = Field(default_factory=list)
