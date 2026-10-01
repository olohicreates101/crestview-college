from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.game_state import GameState, build_initial_world


class Contact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    character_id: str | None = None
    phone_number: str | None = None
    relationship_type: str = "unknown"
    is_known: bool = True
    is_blocked: bool = False
    created_at: datetime | None = None


class Conversation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_ids: list[str] = Field(default_factory=list)
    title: str | None = None
    conversation_type: str = "DIRECT"
    message_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    unread_count: int = 0


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(..., min_length=1)
    sender_id: str | None = None
    recipient_ids: list[str] = Field(default_factory=list)
    text: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message_type: str = "TEXT"
    status: str = "SENT"
    read: bool = False
    story_relevant: bool = False
    story_event_id: str | None = None


class Call(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caller_id: str = Field(..., min_length=1)
    recipient_id: str = Field(..., min_length=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    answered_at: datetime | None = None
    ended_at: datetime | None = None
    status: str = "RINGING"


class Notification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "SYSTEM"
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    read: bool = False
    related_entity_id: str | None = None


class PhoneState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contacts: dict[str, Contact] = Field(default_factory=dict)
    conversations: dict[str, Conversation] = Field(default_factory=dict)
    messages: dict[str, Message] = Field(default_factory=dict)
    calls: dict[str, Call] = Field(default_factory=dict)
    notifications: dict[str, Notification] = Field(default_factory=dict)

    def add_contact(self, contact: Contact) -> bool:
        if contact.id in self.contacts:
            return False
        self.contacts[contact.id] = contact
        return True

    def get_contact(self, contact_id: str) -> Contact | None:
        return self.contacts.get(contact_id)

    def create_conversation(self, participant_ids: list[str], title: str | None = None, conversation_type: str = "DIRECT") -> Conversation:
        conversation = Conversation(
            participant_ids=sorted(dict.fromkeys(participant_ids)),
            title=title,
            conversation_type=conversation_type,
        )
        self.conversations[conversation.id] = conversation
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.conversations.get(conversation_id)

    def get_conversation_by_participants(self, participant_ids: list[str]) -> Conversation | None:
        wanted = sorted(set(participant_ids))
        for conversation in self.conversations.values():
            if sorted(set(conversation.participant_ids)) == wanted:
                return conversation
        return None

    def get_messages(self, conversation_id: str) -> list[Message]:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            return []
        return [self.messages[message_id] for message_id in conversation.message_ids if message_id in self.messages]

    def send_message(
        self,
        conversation_id: str,
        sender_id: str | None,
        recipient_ids: list[str],
        text: str,
        message_type: str = "TEXT",
        status: str = "SENT",
        story_relevant: bool = False,
        story_event_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> Message:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            recipient_ids=list(dict.fromkeys(recipient_ids)),
            text=text,
            timestamp=timestamp or datetime.now(UTC),
            message_type=message_type,
            status=status,
            story_relevant=story_relevant,
            story_event_id=story_event_id,
        )
        self.messages[message.id] = message
        conversation.message_ids.append(message.id)
        conversation.updated_at = message.timestamp
        return message

    def receive_message(
        self,
        conversation_id: str,
        sender_id: str | None,
        recipient_ids: list[str],
        text: str,
        message_type: str = "TEXT",
        story_relevant: bool = False,
        story_event_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> Message:
        message = self.send_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            recipient_ids=recipient_ids,
            text=text,
            message_type=message_type,
            status="DELIVERED",
            story_relevant=story_relevant,
            story_event_id=story_event_id,
            timestamp=timestamp,
        )
        conversation = self.conversations.get(conversation_id)
        if conversation is not None:
            conversation.unread_count += 1
        return message

    def mark_message_read(self, message_id: str) -> Message | None:
        message = self.messages.get(message_id)
        if message is None:
            return None
        message.read = True
        message.status = "READ"
        conversation = self.conversations.get(message.conversation_id)
        if conversation is not None and conversation.unread_count > 0:
            conversation.unread_count = max(0, conversation.unread_count - 1)
        return message

    def mark_conversation_read(self, conversation_id: str) -> Conversation | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            return None
        for message_id in conversation.message_ids:
            message = self.messages.get(message_id)
            if message and not message.read:
                message.read = True
                message.status = "READ"
        conversation.unread_count = 0
        return conversation

    def create_call(self, caller_id: str, recipient_id: str, started_at: datetime | None = None) -> Call:
        call = Call(
            caller_id=caller_id,
            recipient_id=recipient_id,
            started_at=started_at or datetime.now(UTC),
        )
        self.calls[call.id] = call
        return call

    def update_call(self, call_id: str, status: str, answered_at: datetime | None = None, ended_at: datetime | None = None) -> Call | None:
        call = self.calls.get(call_id)
        if call is None:
            return None
        call.status = status
        if answered_at is not None:
            call.answered_at = answered_at
        if ended_at is not None:
            call.ended_at = ended_at
        return call

    def get_call(self, call_id: str) -> Call | None:
        return self.calls.get(call_id)

    def create_notification(self, type: str, title: str, body: str, related_entity_id: str | None = None, timestamp: datetime | None = None) -> Notification:
        notification = Notification(
            type=type,
            title=title,
            body=body,
            timestamp=timestamp or datetime.now(UTC),
            related_entity_id=related_entity_id,
        )
        self.notifications[notification.id] = notification
        return notification

    def get_notification(self, notification_id: str) -> Notification | None:
        return self.notifications.get(notification_id)

    def mark_notification_read(self, notification_id: str) -> Notification | None:
        notification = self.notifications.get(notification_id)
        if notification is None:
            return None
        notification.read = True
        return notification

    def get_unread_count(self) -> int:
        return sum(conversation.unread_count for conversation in self.conversations.values())


class PhoneEngine:
    def __init__(self, game_state: GameState | None = None) -> None:
        self.game_state = game_state or GameState(world=build_initial_world(), current_location="school_gate")
        self.phone_state = PhoneState()

    def _game_timestamp(self) -> datetime:
        clock = self.game_state.clock
        base = datetime(2024, 1, 1, tzinfo=UTC)
        day_offset = clock.day_index
        return base + timedelta(days=day_offset, hours=clock.hour, minutes=clock.minute)

    def add_contact(self, contact: Contact) -> bool:
        return self.phone_state.add_contact(contact)

    def get_contact(self, contact_id: str) -> Contact | None:
        return self.phone_state.get_contact(contact_id)

    def create_conversation(self, participant_ids: list[str], title: str | None = None, conversation_type: str = "DIRECT") -> Conversation:
        return self.phone_state.create_conversation(participant_ids, title=title, conversation_type=conversation_type)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.phone_state.get_conversation(conversation_id)

    def get_conversation_by_participants(self, participant_ids: list[str]) -> Conversation | None:
        return self.phone_state.get_conversation_by_participants(participant_ids)

    def send_message(
        self,
        conversation_id: str,
        sender_id: str | None,
        recipient_ids: list[str],
        text: str,
        message_type: str = "TEXT",
        status: str = "SENT",
        story_relevant: bool = False,
        story_event_id: str | None = None,
    ) -> Message:
        return self.phone_state.send_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            recipient_ids=recipient_ids,
            text=text,
            message_type=message_type,
            status=status,
            story_relevant=story_relevant,
            story_event_id=story_event_id,
            timestamp=self._game_timestamp(),
        )

    def receive_message(
        self,
        conversation_id: str,
        sender_id: str | None,
        recipient_ids: list[str],
        text: str,
        message_type: str = "TEXT",
        story_relevant: bool = False,
        story_event_id: str | None = None,
    ) -> Message:
        message = self.phone_state.receive_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            recipient_ids=recipient_ids,
            text=text,
            message_type=message_type,
            story_relevant=story_relevant,
            story_event_id=story_event_id,
            timestamp=self._game_timestamp(),
        )
        notification = self.create_notification(
            type="NEW_MESSAGE",
            title="New message",
            body=text,
            related_entity_id=message.id,
        )
        notification.read = False
        return message

    def mark_message_read(self, message_id: str) -> Message | None:
        return self.phone_state.mark_message_read(message_id)

    def mark_conversation_read(self, conversation_id: str) -> Conversation | None:
        return self.phone_state.mark_conversation_read(conversation_id)

    def create_call(self, caller_id: str, recipient_id: str) -> Call:
        return self.phone_state.create_call(caller_id=caller_id, recipient_id=recipient_id, started_at=self._game_timestamp())

    def update_call(self, call_id: str, status: str, answered_at: datetime | None = None, ended_at: datetime | None = None) -> Call | None:
        return self.phone_state.update_call(call_id, status=status, answered_at=answered_at, ended_at=ended_at)

    def create_notification(self, type: str, title: str, body: str, related_entity_id: str | None = None) -> Notification:
        return self.phone_state.create_notification(
            type=type,
            title=title,
            body=body,
            related_entity_id=related_entity_id,
            timestamp=self._game_timestamp(),
        )

    def mark_notification_read(self, notification_id: str) -> Notification | None:
        return self.phone_state.mark_notification_read(notification_id)

    def get_unread_count(self) -> int:
        return self.phone_state.get_unread_count()


__all__ = [
    "Call",
    "Contact",
    "Conversation",
    "Message",
    "Notification",
    "PhoneEngine",
    "PhoneState",
]
