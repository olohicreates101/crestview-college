from __future__ import annotations

import uuid

from sqlalchemy import JSON, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint("importance IN ('low', 'medium', 'high', 'critical')", name="ck_memories_importance_valid"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event: Mapped[str] = mapped_column(String(500), nullable=False)
    emotion: Mapped[str] = mapped_column(String(80), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    timestamp: Mapped[str] = mapped_column(String(50), nullable=False)
    expiration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_npc_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    related_story_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
