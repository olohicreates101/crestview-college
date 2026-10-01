from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.relationship import Relationship as RelationshipRecord
from app.models.relationship import Relationship as RelationshipDomain


class RelationshipRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, relationship: RelationshipDomain) -> RelationshipRecord:
        record = RelationshipRecord(**relationship.model_dump())
        self.session.add(record)
        self.session.flush()
        return record

    def get_between_player_and_npc(self, player_id: str, npc_id: str) -> RelationshipRecord | None:
        return (
            self.session.query(RelationshipRecord)
            .filter(RelationshipRecord.player_id == player_id, RelationshipRecord.npc_id == npc_id)
            .first()
        )

    def update(self, relationship_id: str, **updates: object) -> RelationshipRecord | None:
        record = self.session.get(RelationshipRecord, relationship_id)
        if record is None:
            return None

        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)

        self.session.flush()
        return record
