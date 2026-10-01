from __future__ import annotations

import uuid

from sqlalchemy import JSON, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class NPC(Base):
    __tablename__ = "npcs"
    __table_args__ = (
        CheckConstraint("age >= 12 AND age <= 80", name="ck_npcs_age_game_range"),
        CheckConstraint("slang_level >= 0 AND slang_level <= 100", name="ck_npcs_slang_level_range"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    class_name: Mapped[str] = mapped_column(String(40), nullable=False)
    appearance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    personality: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    goals: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    fears: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    current_location: Mapped[str] = mapped_column(String(120), nullable=False)
    current_mood: Mapped[str] = mapped_column(String(50), nullable=False)
    schedule: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    speech_style: Mapped[str] = mapped_column(String(80), nullable=False)
    slang_level: Mapped[int] = mapped_column(nullable=False, default=0)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="supporting")

    relationships = relationship("Relationship", back_populates="npc", cascade="all, delete-orphan")
