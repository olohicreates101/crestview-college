from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    story_relevance: Mapped[str | None] = mapped_column(String(250), nullable=True)

    inventory_links = relationship("PlayerInventory", back_populates="item", cascade="all, delete-orphan")


class PlayerInventory(Base):
    __tablename__ = "player_inventory"
    __table_args__ = (
        UniqueConstraint("player_id", "item_id", name="uq_player_inventory_player_item"),
        CheckConstraint("quantity >= 0", name="ck_player_inventory_quantity_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    location: Mapped[str] = mapped_column(String(120), nullable=False, default="bag")

    player = relationship("Player", back_populates="inventory")
    item = relationship("Item", back_populates="inventory_links")
