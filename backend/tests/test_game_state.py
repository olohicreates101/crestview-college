from app.game_state import (
    ActionResult,
    GameAction,
    GameClock,
    GameEngine,
    GameState,
    Location,
    TimePeriod,
    WorldState,
    build_initial_world,
)


def test_game_clock_initial_time() -> None:
    clock = GameClock()

    assert clock.current_year == "SS1"
    assert clock.current_term == 1
    assert clock.current_week == 1
    assert clock.day_of_week == "Monday"
    assert clock.hour == 7
    assert clock.minute == 0
    assert clock.time_period == TimePeriod.MORNING


def test_game_clock_advances_minutes_and_rolls_over() -> None:
    clock = GameClock(hour=23, minute=45)
    clock.advance_time(20)

    assert clock.hour == 0
    assert clock.minute == 5
    assert clock.day_of_week == "Tuesday"


def test_game_clock_time_periods() -> None:
    morning = GameClock(hour=6, minute=30)
    school_day = GameClock(hour=8, minute=0)
    evening = GameClock(hour=18, minute=30)
    late_night = GameClock(hour=2, minute=15)

    assert morning.time_period == TimePeriod.MORNING
    assert school_day.time_period == TimePeriod.SCHOOL_DAY
    assert evening.time_period == TimePeriod.EVENING
    assert late_night.time_period == TimePeriod.LATE_NIGHT


def test_world_has_valid_locations() -> None:
    world = build_initial_world()

    assert world.get_location("school_gate") is not None
    assert world.get_location("canteen") is not None
    assert "corridor" in world.get_location("school_gate").connected_locations


def test_world_rejects_disconnected_movement() -> None:
    world = build_initial_world()
    player_location = world.get_location("school_gate")

    assert player_location is not None
    assert world.can_move_between("school_gate", "canteen") is False


def test_game_engine_valid_movement_changes_state() -> None:
    world = build_initial_world()
    state = GameState(world=world, current_location="school_gate")
    engine = GameEngine()

    result = engine.execute(GameAction(action_type="MOVE", actor="player", target="corridor", requested_time_cost=5), state)

    assert result.success is True
    assert state.current_location == "corridor"
    assert state.clock.minute == 5
    assert result.time_advanced == 5


def test_game_engine_invalid_movement_does_not_change_state() -> None:
    world = build_initial_world()
    state = GameState(world=world, current_location="school_gate")
    engine = GameEngine()

    result = engine.execute(GameAction(action_type="MOVE", actor="player", target="canteen", requested_time_cost=5), state)

    assert result.success is False
    assert state.current_location == "school_gate"
    assert result.time_advanced == 0
    assert result.reason == "LOCATION_NOT_CONNECTED"


def test_game_engine_valid_wait_advances_time() -> None:
    world = build_initial_world()
    state = GameState(world=world, current_location="classroom")
    engine = GameEngine()

    result = engine.execute(GameAction(action_type="WAIT", actor="player", requested_time_cost=10), state)

    assert result.success is True
    assert result.time_advanced == 10
    assert state.clock.minute == 10


def test_game_engine_invalid_action_rejected() -> None:
    world = build_initial_world()
    state = GameState(world=world, current_location="school_gate")
    engine = GameEngine()

    result = engine.execute(GameAction(action_type="STUDY", actor="player", requested_time_cost=60), state)

    assert result.success is False
    assert result.reason == "ACTION_NOT_ALLOWED"
    assert state.clock.minute == 0


def test_flags_can_be_set_checked_and_cleared() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")

    assert state.has_flag("met_amaka") is False
    state.set_flag("met_amaka")
    assert state.has_flag("met_amaka") is True
    state.clear_flag("met_amaka")
    assert state.has_flag("met_amaka") is False


def test_movement_event_and_flag_event_are_created() -> None:
    world = build_initial_world()
    state = GameState(world=world, current_location="school_gate")
    engine = GameEngine()

    engine.execute(GameAction(action_type="MOVE", actor="player", target="corridor", requested_time_cost=5), state)
    state.set_flag("met_amaka")

    movement_events = [event for event in state.active_events if event.event_type == "PLAYER_MOVED"]
    flag_events = [event for event in state.active_events if event.event_type == "FLAG_CHANGED"]

    assert movement_events
    assert flag_events


def test_valid_action_advances_time_and_invalid_action_does_not() -> None:
    world = build_initial_world()
    state = GameState(world=world, current_location="school_gate")
    engine = GameEngine()

    result = engine.execute(GameAction(action_type="MOVE", actor="player", target="corridor", requested_time_cost=5), state)
    assert result.success is True
    assert state.clock.minute == 5

    bad_result = engine.execute(GameAction(action_type="MOVE", actor="player", target="library", requested_time_cost=5), state)
    assert bad_result.success is False
    assert state.clock.minute == 5
