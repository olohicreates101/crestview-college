from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.npc import NPC as NPCRecord
from app.models.npc import NPC as NPCDomain


class NPCRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, npc: NPCDomain) -> NPCRecord:
        record = NPCRecord(**npc.model_dump(by_alias=True))
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, npc_id: str) -> NPCRecord | None:
        return self.session.get(NPCRecord, npc_id)

    def list(self) -> list[NPCRecord]:
        return self.session.query(NPCRecord).all()

    def delete(self, npc_id: str) -> bool:
        record = self.get_by_id(npc_id)
        if record is None:
            return False

        self.session.delete(record)
        self.session.flush()
        return True
