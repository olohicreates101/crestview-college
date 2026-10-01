from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Rumour(Base):
    __tablename__ = "rumours"
    __table_args__ = (
        CheckConstraint("credibility >= 0 AND credibility <= 100", name="ck_rumours_credibility_range"),
        CheckConstraint("spread_rate >= 0 AND spread_rate <= 100", name="ck_rumours_spread_rate_range"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    origin_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    current_story: Mapped[str] = mapped_column(String(500), nullable=False)
    known_by: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    credibility: Mapped[int] = mapped_column(nullable=False, default=0)
    spread_rate: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
