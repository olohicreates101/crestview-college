from datetime import datetime

from app.game_state import GameState, build_initial_world
from app.phone import Call, Contact, Conversation, Message, Notification, PhoneEngine, PhoneState
from app.story_engine import StoryEngine


def test_add_and_retrieve_contact() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))

    contact = Contact(
        id="amaka",
        display_name="Amaka",
        character_id="amaka",
        phone_number="08030000001",
        relationship_type="friend",
        is_known=True,
        is_blocked=False,
    )
    engine.phone_state.add_contact(contact)

    stored = engine.phone_state.get_contact("amaka")
    assert stored is not None
    assert stored.display_name == "Amaka"


def test_unknown_contact_is_preserved() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))

    contact = Contact(
        id="unknown_001",
        display_name="Unknown Number",
        character_id=None,
        phone_number=None,
        relationship_type="unknown",
        is_known=False,
        is_blocked=False,
    )
    engine.phone_state.add_contact(contact)

    stored = engine.phone_state.get_contact("unknown_001")
    assert stored is not None
    assert stored.is_known is False
    assert stored.character_id is None


def test_blocked_contact_behavior() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    contact = Contact(
        id="blocked_1",
        display_name="Blocked Contact",
        character_id="blocked_1",
        phone_number="08033333333",
        relationship_type="rival",
        is_known=True,
        is_blocked=True,
    )
    engine.phone_state.add_contact(contact)

    assert engine.phone_state.get_contact("blocked_1").is_blocked is True


def test_duplicate_contact_behavior() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    contact = Contact(
        id="amaka",
        display_name="Amaka",
        character_id="amaka",
        phone_number="08030000001",
        relationship_type="friend",
        is_known=True,
        is_blocked=False,
    )
    engine.phone_state.add_contact(contact)

    duplicate = Contact(
        id="amaka",
        display_name="Amaka Again",
        character_id="amaka",
        phone_number="08030000001",
        relationship_type="friend",
        is_known=True,
        is_blocked=False,
    )

    result = engine.phone_state.add_contact(duplicate)
    assert result is False


def test_create_direct_conversation_and_message_ordering() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    conversation = engine.phone_state.create_conversation(participant_ids=["player", "amaka"], title="Amaka")

    first = engine.send_message(conversation_id=conversation.id, sender_id="player", recipient_ids=["amaka"], text="Good morning.")
    second = engine.send_message(conversation_id=conversation.id, sender_id="amaka", recipient_ids=["player"], text="Good morning to you.")

    history = engine.phone_state.get_messages(conversation.id)
    assert [message.id for message in history] == [first.id, second.id]
    assert conversation.unread_count == 0


def test_receive_message_creates_notification_and_unread_count() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    conversation = engine.phone_state.create_conversation(participant_ids=["player", "unknown_001"], title="Unknown Number")

    message = engine.receive_message(conversation_id=conversation.id, sender_id=None, recipient_ids=["player"], text="Welcome.")

    assert message.read is False
    assert conversation.unread_count == 1
    assert len(engine.phone_state.notifications) == 1
    assert engine.phone_state.notifications[next(iter(engine.phone_state.notifications))].type == "NEW_MESSAGE"


def test_mark_message_and_conversation_read() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    conversation = engine.phone_state.create_conversation(participant_ids=["player", "amaka"], title="Amaka")
    message = engine.receive_message(conversation_id=conversation.id, sender_id="amaka", recipient_ids=["player"], text="Can we talk?")

    engine.phone_state.mark_message_read(message.id)
    engine.phone_state.mark_conversation_read(conversation.id)

    assert message.read is True
    assert conversation.unread_count == 0


def test_call_lifecycle() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    call = engine.phone_state.create_call(caller_id="player", recipient_id="amaka")

    assert call.status == "RINGING"
    engine.phone_state.update_call(call.id, status="ANSWERED", answered_at=datetime(2024, 1, 1, 8, 0))
    assert engine.phone_state.get_call(call.id).status == "ANSWERED"


def test_phone_uses_game_clock_for_timestamps() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    state.clock.hour = 8
    state.clock.minute = 20
    engine = PhoneEngine(game_state=state)

    conversation = engine.phone_state.create_conversation(participant_ids=["player", "amaka"], title="Amaka")
    message = engine.send_message(conversation_id=conversation.id, sender_id="player", recipient_ids=["amaka"], text="Morning.")

    assert message.timestamp.hour == 8
    assert message.timestamp.minute == 20


def test_story_integration_unknown_message_creates_phone_event() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    engine = StoryEngine(game_state=state)
    engine.start_episode("ss1_term1_episode1")

    engine.choose("enter_confidently")
    engine.choose("listen_to_adeyemi")
    engine.choose("stay_with_classmates")
    engine.choose("be_friendly")
    engine.choose("follow_sandra")

    messages = list(engine.phone_engine.phone_state.messages.values())
    notification_count = len(engine.phone_engine.phone_state.notifications)

    assert any(message.text == "Welcome." for message in messages)
    assert any(message.sender_id is None for message in messages)
    assert state.flags.get("mystery_message_received") is True
    assert notification_count >= 1


def test_phone_notification_read_state() -> None:
    engine = PhoneEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    notification = engine.create_notification(type="SYSTEM", title="System", body="Welcome.")

    assert notification.read is False
    engine.phone_state.mark_notification_read(notification.id)
    assert engine.phone_state.get_notification(notification.id).read is True
