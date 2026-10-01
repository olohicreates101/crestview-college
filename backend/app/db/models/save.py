from __future__ import annotations

import uuid
from datetime import datetime, UTC

from sqlalchemy import JSON, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SaveGameRecord(Base):
    __tablename__ = "save_games"
    __table_args__ = (
        CheckConstraint("schema_version >= 1", name="ck_save_games_schema_version_positive"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    save_name: Mapped[str] = mapped_column(String(120), nullable=False, default="autosave")
    game_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
