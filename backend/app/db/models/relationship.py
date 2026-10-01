from __future__ import annotations

import uuid

from sqlalchemy import JSON, CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("player_id", "npc_id", name="uq_relationships_player_npc"),
        CheckConstraint("trust >= 0 AND trust <= 100", name="ck_relationships_trust_range"),
        CheckConstraint("closeness >= 0 AND closeness <= 100", name="ck_relationships_closeness_range"),
        CheckConstraint("respect >= 0 AND respect <= 100", name="ck_relationships_respect_range"),
        CheckConstraint("resentment >= 0 AND resentment <= 100", name="ck_relationships_resentment_range"),
        CheckConstraint("romantic_interest >= 0 AND romantic_interest <= 100", name="ck_relationships_romantic_interest_range"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    npc_id: Mapped[str] = mapped_column(String(64), nullable=False)
    trust: Mapped[int] = mapped_column(nullable=False, default=0)
    closeness: Mapped[int] = mapped_column(nullable=False, default=0)
    respect: Mapped[int] = mapped_column(nullable=False, default=0)
    resentment: Mapped[int] = mapped_column(nullable=False, default=0)
    romantic_interest: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="stranger")
    history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    player = relationship("Player", back_populates="relationships")
    npc = relationship("NPC", back_populates="relationships")
