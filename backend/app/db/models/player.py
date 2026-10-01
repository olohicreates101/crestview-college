from __future__ import annotations

import uuid

from sqlalchemy import JSON, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        CheckConstraint("money >= 0", name="ck_players_money_non_negative"),
        CheckConstraint("age >= 12 AND age <= 25", name="ck_players_age_game_range"),
        CheckConstraint("reputation >= 0 AND reputation <= 100", name="ck_players_reputation_range"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    gender_presentation: Mapped[str] = mapped_column(String(50), nullable=False)
    school_type: Mapped[str] = mapped_column(String(30), nullable=False)
    boarding_status: Mapped[str] = mapped_column(String(20), nullable=False)
    appearance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    traits: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    academic_strengths: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    academic_weaknesses: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    current_class: Mapped[str] = mapped_column(String(40), nullable=False)
    money: Mapped[float] = mapped_column(nullable=False, default=0.0)
    reputation: Mapped[int] = mapped_column(nullable=False, default=0)
    ambitions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    family_context: Mapped[str] = mapped_column(String(200), nullable=False)
    current_location: Mapped[str] = mapped_column(String(120), nullable=False)
    current_mood: Mapped[str] = mapped_column(String(50), nullable=False)

    inventory = relationship("PlayerInventory", back_populates="player", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="player", cascade="all, delete-orphan")
