from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SecretImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecretStatus(str, Enum):
    HIDDEN = "hidden"
    PARTIALLY_KNOWN = "partially_known"
    EXPOSED = "exposed"
    RESOLVED = "resolved"


class Secret(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    owner_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    known_by: list[str] = Field(default_factory=list)
    importance: SecretImportance
    discovery_method: str = Field(..., min_length=1)
    status: SecretStatus
