import pytest

from app.game_state import GameState, build_initial_world
from app.story_engine import (
    Choice,
    Condition,
    Consequence,
    Episode,
    Scene,
    StoryEngine,
)


def test_episode_loads_and_starts_at_school_gate() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))

    episode = engine.load_episode("ss1_term1_episode1")

    assert episode.id == "ss1_term1_episode1"
    assert episode.starting_scene_id == "school_gate_arrival"
    assert engine.start_episode("ss1_term1_episode1") is not None
    assert engine.get_current_scene().id == "school_gate_arrival"


def test_invalid_episode_rejected() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))

    with pytest.raises(ValueError):
        engine.start_episode("missing_episode")


def test_scene_conditions_and_choice_filtering() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    engine.start_episode("ss1_term1_episode1")

    scene = engine.get_current_scene()
    assert scene.id == "school_gate_arrival"
    assert len(engine.get_available_choices()) >= 2

    flag_condition = Condition(type="FLAG_TRUE", flag="greeted_amaka")
    assert flag_condition.evaluate(game_state=engine.game_state, story_state=engine.story_state) is False

    engine.story_state["flags"]["greeted_amaka"] = True
    assert flag_condition.evaluate(game_state=engine.game_state, story_state=engine.story_state) is True


def test_choice_progresses_scene_and_applies_consequences() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    engine.start_episode("ss1_term1_episode1")

    choice = engine.get_choice("enter_confidently")
    result = engine.choose("enter_confidently")

    assert choice is not None
    assert result["next_scene_id"] == "classroom_introduction"
    assert engine.get_current_scene().id == "classroom_introduction"


def test_condition_validation_rejects_unknown_condition_type() -> None:
    with pytest.raises(ValueError):
        Condition(type="UNKNOWN_TYPE", flag="test")


def test_consequence_set_and_clear_flag() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    consequence = Consequence(type="SET_FLAG", flag="met_amaka")

    consequence.apply(game_state=engine.game_state, story_state=engine.story_state)
    assert engine.game_state.flags["met_amaka"] is True

    clear_action = Consequence(type="CLEAR_FLAG", flag="met_amaka")
    clear_action.apply(game_state=engine.game_state, story_state=engine.story_state)
    assert engine.game_state.flags["met_amaka"] is False


def test_consequence_advance_time_and_move_player() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    engine.game_state.current_location = "school_gate"

    Consequence(type="ADVANCE_TIME", minutes=15).apply(game_state=engine.game_state, story_state=engine.story_state)
    assert engine.game_state.clock.hour == 7
    assert engine.game_state.clock.minute == 15

    move = Consequence(type="MOVE_PLAYER", target="corridor").apply(game_state=engine.game_state, story_state=engine.story_state)
    assert move is not None
    assert engine.game_state.current_location == "corridor"


def test_first_day_scene_flow_reaches_mystery_and_completion() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    engine.start_episode("ss1_term1_episode1")

    assert engine.choose("enter_confidently")["next_scene_id"] == "classroom_introduction"
    assert engine.choose("listen_to_adeyemi")["next_scene_id"] == "break_time"
    assert engine.choose("stay_with_classmates")["next_scene_id"] == "amaka_conversation"
    assert engine.choose("be_friendly")["next_scene_id"] == "first_day_choice"
    assert engine.choose("follow_sandra")["next_scene_id"] == "unknown_message"
    assert engine.game_state.flags.get("mystery_message_received") is True
    assert engine.get_current_scene().id == "unknown_message"

    result = engine.choose("leave_school")
    assert result["next_scene_id"] == "end_of_day_hook"
    assert engine.get_current_scene().id == "end_of_day_hook"
    assert engine.episode_completion_flag == "first_day_complete"
    assert engine.game_state.flags.get("first_day_complete") is True


def test_story_engine_returns_available_choices_and_terminal_scene() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    engine.start_episode("ss1_term1_episode1")

    choice_ids = [choice.id for choice in engine.get_available_choices()]
    assert "enter_confidently" in choice_ids
    assert "look_around_first" in choice_ids

    engine.choose("enter_confidently")
    engine.choose("listen_to_adeyemi")
    engine.choose("stay_with_classmates")
    engine.choose("be_friendly")
    engine.choose("follow_sandra")
    engine.choose("leave_school")

    final_scene = engine.get_current_scene()
    assert final_scene.is_terminal is True
