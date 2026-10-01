from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ItemType(str, Enum):
    SCHOOL_SUPPLY = "school_supply"
    FOOD = "food"
    PHONE = "phone"
    LETTER = "letter"
    GIFT = "gift"
    KEY = "key"
    EVIDENCE = "evidence"
    CLOTHING = "clothing"
    MISCELLANEOUS = "miscellaneous"


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: ItemType
    owner_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)
    location: str = Field(..., min_length=1)
    story_relevance: str | None = None
