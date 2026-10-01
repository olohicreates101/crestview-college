from __future__ import annotations

import uuid

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Secret(Base):
    __tablename__ = "secrets"
    __table_args__ = (
        CheckConstraint("importance IN ('low', 'medium', 'high', 'critical')", name="ck_secrets_importance_valid"),
        CheckConstraint("status IN ('hidden', 'partially_known', 'exposed', 'resolved')", name="ck_secrets_status_valid"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    discovery_method: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="hidden")

    knowledge = relationship("SecretKnowledge", back_populates="secret", cascade="all, delete-orphan")


class SecretKnowledge(Base):
    __tablename__ = "secret_knowledge"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    secret_id: Mapped[str] = mapped_column(ForeignKey("secrets.id"), nullable=False)
    character_id: Mapped[str] = mapped_column(String(64), nullable=False)

    secret = relationship("Secret", back_populates="knowledge")
