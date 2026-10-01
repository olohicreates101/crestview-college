from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SchoolType(str, Enum):
    GOVERNMENT = "government"
    PRIVATE = "private"


class BoardingStatus(str, Enum):
    DAY = "day"
    BOARDING = "boarding"


class Appearance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skin_tone: str = Field(..., min_length=1)
    hair: str = Field(..., min_length=1)
    eyes: str = Field(..., min_length=1)
    glasses: bool = False
    height_build: str = Field(..., min_length=1)
    uniform: str = Field(..., min_length=1)
    shoes: str = Field(..., min_length=1)
    backpack: str = Field(..., min_length=1)


class Player(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=12, le=25)
    nickname: str | None = Field(default=None, min_length=1)
    gender_presentation: str = Field(..., min_length=1)
    school_type: SchoolType
    boarding_status: BoardingStatus
    appearance: Appearance
    traits: list[str] = Field(default_factory=list)
    academic_strengths: list[str] = Field(default_factory=list)
    academic_weaknesses: list[str] = Field(default_factory=list)
    current_class: str = Field(..., min_length=1)
    money: float = Field(..., ge=0)
    reputation: int = Field(..., ge=0, le=100)
    ambitions: list[str] = Field(default_factory=list)
    family_context: str = Field(..., min_length=1)
    current_location: str = Field(..., min_length=1)
    current_mood: str = Field(..., min_length=1)
    inventory_ids: list[str] = Field(default_factory=list)
