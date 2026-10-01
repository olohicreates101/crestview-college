from __future__ import annotations

import pytest

from app.game_state import GameState, build_initial_world
from app.npc_simulation import NPCActivity, NPCMood, NPCSimulator
from app.persistence.save_service import GameSaveService, SaveValidationError
from app.phone import PhoneEngine
from app.story_engine import StoryEngine


@pytest.fixture
def save_service() -> GameSaveService:
    return GameSaveService()


def make_game_state() -> GameState:
    state = GameState(world=build_initial_world(), current_location="corridor")
    state.clock.day_of_week = "Monday"
    state.clock.hour = 16
    state.clock.minute = 37
    state.flags["mystery_message_received"] = True
    state.flags["amaka_met"] = True
    state.active_events.append({"event_type": "FLAG_CHANGED", "message": "mystery_message_received", "payload": {"flag": "mystery_message_received", "value": True}})
    return state


def make_runtime_snapshot() -> dict:
    return {
        "player": {
            "id": "player-1",
            "name": "Aisha Bello",
            "money": 2350.0,
            "current_location": "corridor",
            "current_mood": "focused",
        },
        "inventory": [
            {"item_id": "notice_board", "quantity": 1, "location": "bag", "story_relevance": "first_day"},
            {"item_id": "manual", "quantity": 1, "location": "bag", "story_relevance": "school"},
        ],
        "relationships": {
            "amaka": {
                "player_id": "player-1",
                "npc_id": "amaka",
                "trust": 80,
                "closeness": 76,
                "respect": 70,
                "resentment": 5,
                "romantic_interest": 15,
                "status": "friend",
                "history": ["met_at_gate"],
            }
        },
        "memories": [
            {
                "id": "memory-1",
                "subject_id": "amaka",
                "actor_id": "amaka",
                "event": "shared notes at the gate",
                "emotion": "happy",
                "importance": "high",
                "timestamp": "2024-01-01T16:00:00+00:00",
                "expiration": None,
                "related_npc_ids": ["amaka"],
                "related_story_id": "first_day",
            }
        ],
        "secrets": [
            {
                "id": "secret-1",
                "owner_id": "amaka",
                "content": "she was waiting for a note",
                "known_by": ["player-1"],
                "importance": "medium",
                "discovery_method": "conversation",
                "status": "partially_known",
            }
        ],
        "rumours": [
            {
                "id": "rumour-1",
                "origin_id": "amaka",
                "target_id": "mr_adeyemi",
                "current_story": "Mr Adeyemi is strict but fair",
                "known_by": ["player-1"],
                "credibility": 60,
                "spread_rate": 15,
                "created_at": "2024-01-01T08:30:00+00:00",
                "status": "active",
            }
        ],
        "phone_state": {
            "contacts": {
                "amaka": {
                    "id": "amaka",
                    "display_name": "Amaka",
                    "character_id": "amaka",
                    "phone_number": "08030001111",
                    "relationship_type": "friend",
                    "is_known": True,
                    "is_blocked": False,
                    "created_at": "2024-01-01T08:00:00+00:00",
                }
            },
            "conversations": {
                "conv-1": {
                    "id": "conv-1",
                    "participant_ids": ["player-1", "amaka"],
                    "title": "Amaka",
                    "conversation_type": "DIRECT",
                    "message_ids": ["msg-1"],
                    "created_at": "2024-01-01T15:40:00+00:00",
                    "updated_at": "2024-01-01T15:40:00+00:00",
                    "unread_count": 1,
                }
            },
            "messages": {
                "msg-1": {
                    "id": "msg-1",
                    "conversation_id": "conv-1",
                    "sender_id": "amaka",
                    "recipient_ids": ["player-1"],
                    "text": "Welcome to school.",
                    "timestamp": "2024-01-01T15:40:00+00:00",
                    "message_type": "TEXT",
                    "status": "DELIVERED",
                    "read": False,
                    "story_relevant": True,
                    "story_event_id": "first_day",
                }
            },
            "calls": {},
            "notifications": {
                "note-1": {
                    "id": "note-1",
                    "type": "MESSAGE",
                    "title": "Unread message",
                    "body": "Welcome to school.",
                    "timestamp": "2024-01-01T15:40:00+00:00",
                    "read": False,
                    "related_entity_id": "conv-1",
                }
            },
        },
        "story_state": {
            "current_year": "SS1",
            "current_term": 1,
            "current_episode": 1,
            "current_scene": "campus",
            "completed_episodes": [1],
            "active_storylines": ["first_day"],
            "story_flags": ["mystery_message_received"],
            "major_choices": ["hello_amaka"],
            "unlocked_events": ["gate_introduction"],
            "unlocked_locations": ["school_gate"],
        },
        "npcs": {
            "amaka": {
                "npc_id": "amaka",
                "current_location": "corridor",
                "current_activity": "WALK",
                "mood": "CALM",
                "active_goal": {"id": "goal-amaka", "type": "MAKE_FRIENDS", "priority": 10, "status": "active"},
                "schedule_id": "core",
                "schedule_position": 1,
                "last_updated": 120,
                "available_for_interaction": True,
            }
        },
    }


def test_save_and_load_basic_game_state(save_service: GameSaveService) -> None:
    state = make_game_state()
    save_id = save_service.save_game(state, runtime_state=make_runtime_snapshot(), save_name="checkpoint-1")

    loaded = save_service.load_game(save_id)
    assert loaded.current_location == "corridor"
    assert loaded.clock.day_of_week == "Monday"
    assert loaded.clock.hour == 16
    assert loaded.clock.minute == 37
    assert loaded.flags["mystery_message_received"] is True
    assert getattr(loaded, "runtime_state", {})["player"]["money"] == 2350.0


def test_save_and_load_preserves_phone_story_and_relationships(save_service: GameSaveService) -> None:
    state = make_game_state()
    runtime = make_runtime_snapshot()
    save_id = save_service.save_game(state, runtime_state=runtime)

    loaded = save_service.load_game(save_id)
    phone_state = getattr(loaded, "runtime_state", {}).get("phone_state", {})
    assert phone_state["messages"]["msg-1"]["text"] == "Welcome to school."
    assert phone_state["notifications"]["note-1"]["read"] is False

    relationships = getattr(loaded, "runtime_state", {}).get("relationships", {})
    assert relationships["amaka"]["closeness"] == 76
    assert relationships["amaka"]["status"] == "friend"

    story_state = getattr(loaded, "runtime_state", {}).get("story_state", {})
    assert story_state["story_flags"] == ["mystery_message_received"]
    assert story_state["completed_episodes"] == [1]


def test_save_load_round_trip_for_npc_simulation_and_story(save_service: GameSaveService) -> None:
    state = make_game_state()
    runtime = make_runtime_snapshot()
    save_id = save_service.save_game(state, runtime_state=runtime)

    loaded = save_service.load_game(save_id)
    npc_simulator = NPCSimulator(game_state=loaded, tick_minutes=30)
    npc_simulator.npcs = {
        npc_id: type("LoadedNPC", (), {})() for npc_id in getattr(loaded, "runtime_state", {}).get("npcs", {})
    }
    npc_simulator.npcs["amaka"] = type("N", (), {"npc_id": "amaka", "current_location": "corridor", "current_activity": NPCActivity.WALK, "mood": NPCMood.CALM, "schedule_id": "core", "schedule_position": 1, "last_updated": 120, "available_for_interaction": True})()

    story_engine = StoryEngine(loaded)
    story_engine.story_state["flags"] = loaded.flags
    story_engine.story_state["relationship_scores"] = {"amaka": 80}
    story_engine.story_state["items"] = ["notice_board"]
    story_engine.story_state["phone_state"] = getattr(loaded, "runtime_state", {}).get("phone_state", {})

    assert story_engine.game_state.current_location == "corridor"
    assert getattr(loaded, "runtime_state", {}).get("npcs", {})["amaka"]["schedule_position"] == 1


def test_invalid_save_payload_fails_safely(save_service: GameSaveService) -> None:
    invalid = {
        "schema_version": 999,
        "game_version": "9.9.9",
        "current_location": "corridor",
    }

    with pytest.raises(SaveValidationError):
        save_service.deserialize_game_state(invalid)


def test_version_validation_is_enforced(save_service: GameSaveService) -> None:
    state = make_game_state()
    save_id = save_service.save_game(state, runtime_state={})

    record = save_service.get_save_record(save_id)
    record.schema_version = 999
    save_service.session.merge(record)
    save_service.session.commit()

    with pytest.raises(SaveValidationError):
        save_service.load_game(save_id)


def test_full_round_trip_integration(save_service: GameSaveService) -> None:
    state = make_game_state()
    state.current_location = "classroom"
    state.flags["story_advances"] = True
    runtime = make_runtime_snapshot()
    runtime["player"]["current_location"] = "classroom"
    runtime["relationships"]["amaka"]["trust"] = 90
    runtime["story_state"]["current_scene"] = "classroom_intro"

    save_id = save_service.save_game(state, runtime_state=runtime, save_name="full-roundtrip")
    loaded = save_service.load_game(save_id)

    assert loaded.current_location == "classroom"
    assert loaded.flags["story_advances"] is True
    assert getattr(loaded, "runtime_state", {})["relationships"]["amaka"]["trust"] == 90
    assert getattr(loaded, "runtime_state", {})["story_state"]["current_scene"] == "classroom_intro"


def test_transaction_rollback_for_failed_save(save_service: GameSaveService, monkeypatch: pytest.MonkeyPatch) -> None:
    state = make_game_state()
    original = save_service.save_game

    def boom(*args, **kwargs):
        raise RuntimeError("database write failed")

    monkeypatch.setattr(save_service, "save_game", boom)
    with pytest.raises(RuntimeError):
        save_service.save_game(state, runtime_state={})

    assert save_service.list_saves() == []
