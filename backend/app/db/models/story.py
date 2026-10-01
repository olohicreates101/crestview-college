from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class StoryProgress(Base):
    __tablename__ = "story_progress"
    __table_args__ = (
        CheckConstraint("current_term >= 1 AND current_term <= 3", name="ck_story_progress_term_range"),
        CheckConstraint("current_year IN ('SS1', 'SS2', 'SS3')", name="ck_story_progress_year_valid"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    current_year: Mapped[str] = mapped_column(String(10), nullable=False, default="SS1")
    current_term: Mapped[int] = mapped_column(nullable=False, default=1)
    current_episode: Mapped[int] = mapped_column(nullable=False, default=1)
    current_scene: Mapped[str] = mapped_column(String(120), nullable=False, default="campus")
    completed_episodes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    active_storylines: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    story_flags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    major_choices: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    unlocked_events: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    unlocked_locations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
