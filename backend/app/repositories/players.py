from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.player import Player as PlayerRecord
from app.models.player import Player as PlayerDomain


class PlayerRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, player: PlayerDomain) -> PlayerRecord:
        record = PlayerRecord(**player.model_dump())
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, player_id: str) -> PlayerRecord | None:
        return self.session.get(PlayerRecord, player_id)

    def update(self, player_id: str, **updates: object) -> PlayerRecord | None:
        record = self.get_by_id(player_id)
        if record is None:
            return None

        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)

        self.session.flush()
        return record

    def delete(self, player_id: str) -> bool:
        record = self.get_by_id(player_id)
        if record is None:
            return False

        self.session.delete(record)
        self.session.flush()
        return True
