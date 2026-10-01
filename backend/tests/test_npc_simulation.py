from app.game_state import GameState, build_initial_world
from app.npc_simulation import (
    NPCActivity,
    NPCGoal,
    NPCGoalType,
    NPCMood,
    NPCSchedule,
    NPCSimulator,
    NPCState,
    ScheduleCondition,
    ScheduleEntry,
)


def test_valid_schedule_and_condition_evaluation() -> None:
    schedule = NPCSchedule(
        npc_id="amaka",
        entries=[
            ScheduleEntry(
                id="amaka_morning",
                npc_id="amaka",
                start_time="07:00",
                end_time="08:00",
                location_id="school_gate",
                activity=NPCActivity.WAIT,
                priority=10,
                conditions=[ScheduleCondition(type="DAY_OF_WEEK", value="Monday")],
            ),
            ScheduleEntry(
                id="amaka_class",
                npc_id="amaka",
                start_time="08:00",
                end_time="10:00",
                location_id="classroom",
                activity=NPCActivity.ATTEND_CLASS,
                priority=20,
            ),
        ],
    )
    state = GameState(world=build_initial_world(), current_location="school_gate")
    state.clock.day_of_week = "Monday"
    state.clock.hour = 7
    state.clock.minute = 30

    assert schedule.get_active_entry(state) is not None
    assert schedule.get_active_entry(state).activity == NPCActivity.WAIT


def test_activity_transition_and_valid_activity_set() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    simulator = NPCSimulator(game_state=state)
    npc = NPCState(
        npc_id="amaka",
        current_location="school_gate",
        current_activity=NPCActivity.WAIT,
        mood=NPCMood.CALM,
        active_goal=NPCGoal(id="goal-1", type=NPCGoalType.MAKE_FRIENDS, priority=10, status="active"),
        schedule_id="amaka_schedule",
        schedule_position=0,
        last_updated=0,
        available_for_interaction=True,
    )

    simulator.register_npc(npc)
    simulator.set_npc_activity("amaka", NPCActivity.SOCIALIZE)

    assert simulator.npcs["amaka"].current_activity == NPCActivity.SOCIALIZE


def test_npc_moves_only_through_connected_locations() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    simulator = NPCSimulator(game_state=state)

    npc = NPCState(
        npc_id="amaka",
        current_location="school_gate",
        current_activity=NPCActivity.WALK,
        mood=NPCMood.CALM,
        active_goal=NPCGoal(id="goal-1", type=NPCGoalType.MAKE_FRIENDS, priority=10, status="active"),
        schedule_id="core",
        schedule_position=0,
        last_updated=0,
        available_for_interaction=True,
    )
    simulator.register_npc(npc)

    result = simulator.move_npc_to("amaka", "canteen")
    assert result is False

    result = simulator.move_npc_to("amaka", "corridor")
    assert result is True
    assert simulator.npcs["amaka"].current_location == "corridor"


def test_simulator_updates_on_game_clock_advancement() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    state.clock.hour = 7
    state.clock.minute = 0
    simulator = NPCSimulator(game_state=state, tick_minutes=30)

    npc = NPCState(
        npc_id="amaka",
        current_location="school_gate",
        current_activity=NPCActivity.WAIT,
        mood=NPCMood.CALM,
        active_goal=NPCGoal(id="goal-1", type=NPCGoalType.MAKE_FRIENDS, priority=10, status="active"),
        schedule_id="amaka_schedule",
        schedule_position=0,
        last_updated=0,
        available_for_interaction=True,
    )
    simulator.register_npc(npc)
    simulator.set_schedule("amaka", NPCSchedule(npc_id="amaka", entries=[
        ScheduleEntry(
            id="entry-1",
            npc_id="amaka",
            start_time="07:00",
            end_time="08:00",
            location_id="school_gate",
            activity=NPCActivity.WAIT,
            priority=10,
        )
    ]))

    simulator.update_for_game_time()
    assert simulator.npcs["amaka"].current_activity == NPCActivity.WAIT

    state.clock.hour = 7
    state.clock.minute = 45
    simulator.update_for_game_time()
    assert simulator.npcs["amaka"].current_activity == NPCActivity.WAIT


def test_core_npcs_have_distinct_schedules() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    simulator = NPCSimulator(game_state=state)
    simulator.register_default_npcs()

    assert "amaka" in simulator.npcs
    assert "chuka" in simulator.npcs
    assert "sandra" in simulator.npcs
    assert "mr_adeyemi" in simulator.npcs
    assert "mysterious_student" in simulator.npcs

    assert simulator.npcs["amaka"].active_goal.type == NPCGoalType.MAKE_FRIENDS
    assert simulator.npcs["chuka"].active_goal.type == NPCGoalType.SOCIAL_STATUS
    assert simulator.npcs["sandra"].active_goal.type == NPCGoalType.ACADEMIC_SUCCESS


def test_goal_assignment_and_priority() -> None:
    goal = NPCGoal(id="goal-1", type=NPCGoalType.HELP_SOMEONE, priority=8, status="active")
    assert goal.priority == 8
    assert goal.type == NPCGoalType.HELP_SOMEONE


def test_mood_changes_are_explicit_and_valid() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    simulator = NPCSimulator(game_state=state)
    npc = NPCState(
        npc_id="amaka",
        current_location="school_gate",
        current_activity=NPCActivity.WAIT,
        mood=NPCMood.CALM,
        active_goal=NPCGoal(id="goal-1", type=NPCGoalType.MAKE_FRIENDS, priority=10, status="active"),
        schedule_id="amaka_schedule",
        schedule_position=0,
        last_updated=0,
        available_for_interaction=True,
    )
    simulator.register_npc(npc)

    simulator.set_npc_mood("amaka", NPCMood.EXCITED)
    assert simulator.npcs["amaka"].mood == NPCMood.EXCITED


def test_encounter_event_emits_only_when_relevant() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    simulator = NPCSimulator(game_state=state)
    npc = NPCState(
        npc_id="amaka",
        current_location="school_gate",
        current_activity=NPCActivity.WAIT,
        mood=NPCMood.CALM,
        active_goal=NPCGoal(id="goal-1", type=NPCGoalType.MAKE_FRIENDS, priority=10, status="active"),
        schedule_id="amaka_schedule",
        schedule_position=0,
        last_updated=0,
        available_for_interaction=True,
    )
    simulator.register_npc(npc)
    simulator.detect_encounters()

    assert any(event.event_type == "NPC_ENCOUNTER_AVAILABLE" for event in simulator.events)

    npc2 = NPCState(
        npc_id="chuka",
        current_location="canteen",
        current_activity=NPCActivity.EAT,
        mood=NPCMood.CALM,
        active_goal=NPCGoal(id="goal-2", type=NPCGoalType.SOCIAL_STATUS, priority=9, status="active"),
        schedule_id="chuka_schedule",
        schedule_position=0,
        last_updated=0,
        available_for_interaction=False,
    )
    simulator.register_npc(npc2)
    simulator.detect_encounters()
    assert not any(event.npc_id == "chuka" and event.event_type == "NPC_ENCOUNTER_AVAILABLE" for event in simulator.events)


def test_off_screen_updates_continue_without_player_interaction() -> None:
    state = GameState(world=build_initial_world(), current_location="classroom")
    simulator = NPCSimulator(game_state=state, tick_minutes=60)
    simulator.register_default_npcs()

    state.clock.hour = 9
    state.clock.minute = 0
    simulator.update_for_game_time()

    assert any(npc.current_activity in {NPCActivity.ATTEND_CLASS, NPCActivity.WALK, NPCActivity.EAT} for npc in simulator.npcs.values())


def test_deterministic_results_for_identical_state() -> None:
    state_a = GameState(world=build_initial_world(), current_location="school_gate")
    state_b = GameState(world=build_initial_world(), current_location="school_gate")
    simulator_a = NPCSimulator(game_state=state_a, tick_minutes=30)
    simulator_b = NPCSimulator(game_state=state_b, tick_minutes=30)

    simulator_a.register_default_npcs()
    simulator_b.register_default_npcs()

    state_a.clock.hour = 8
    state_a.clock.minute = 0
    state_b.clock.hour = 8
    state_b.clock.minute = 0

    simulator_a.update_for_game_time()
    simulator_b.update_for_game_time()

    assert simulator_a.npcs["amaka"].current_location == simulator_b.npcs["amaka"].current_location
    assert simulator_a.npcs["amaka"].current_activity == simulator_b.npcs["amaka"].current_activity
