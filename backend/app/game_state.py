from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TimePeriod(str, Enum):
    LATE_NIGHT = "late_night"
    NIGHT = "night"
    EVENING = "evening"
    AFTERNOON = "afternoon"
    SCHOOL_DAY = "school_day"
    MORNING = "morning"


class WorldActionType(str, Enum):
    MOVE = "MOVE"
    WAIT = "WAIT"
    TALK = "TALK"
    STUDY = "STUDY"
    EAT = "EAT"
    BUY_ITEM = "BUY_ITEM"
    GIVE_ITEM = "GIVE_ITEM"
    TAKE_ITEM = "TAKE_ITEM"
    LOOK = "LOOK"
    LEAVE = "LEAVE"


@dataclass
class Location:
    id: str
    name: str
    description: str
    available_time_range: tuple[int, int] | None = None
    allowed_actions: list[str] = field(default_factory=list)
    connected_locations: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)


@dataclass
class WorldState:
    locations: dict[str, Location] = field(default_factory=dict)

    def get_location(self, location_id: str) -> Location | None:
        return self.locations.get(location_id)

    def can_move_between(self, from_id: str, to_id: str) -> bool:
        origin = self.locations.get(from_id)
        if origin is None:
            return False
        return to_id in origin.connected_locations


def build_initial_world() -> WorldState:
    school_gate = Location(
        id="school_gate",
        name="School Gate",
        description="A guarded entrance to Crestview College.",
        available_time_range=(0, 23),
        allowed_actions=["MOVE", "WAIT", "LOOK"],
        connected_locations=["corridor"],
        restrictions=[],
    )
    corridor = Location(
        id="corridor",
        name="Corridor",
        description="A wide hallway linking the main departments.",
        available_time_range=(0, 23),
        allowed_actions=["MOVE", "WAIT", "LOOK"],
        connected_locations=["school_gate", "classroom", "canteen", "outdoor_area"],
        restrictions=[],
    )
    classroom = Location(
        id="classroom",
        name="Classroom",
        description="A study room with desks and a chalkboard.",
        allowed_actions=["MOVE", "WAIT", "STUDY", "LOOK"],
        connected_locations=["corridor"],
    )
    canteen = Location(
        id="canteen",
        name="Canteen",
        description="Students gather here for food and rest.",
        allowed_actions=["MOVE", "WAIT", "EAT", "LOOK"],
        connected_locations=["corridor"],
    )
    outdoor_area = Location(
        id="outdoor_area",
        name="Outdoor Area",
        description="A courtyard beside the school building.",
        allowed_actions=["MOVE", "WAIT", "LOOK"],
        connected_locations=["corridor"],
    )

    return WorldState(
        locations={
            school_gate.id: school_gate,
            corridor.id: corridor,
            classroom.id: classroom,
            canteen.id: canteen,
            outdoor_area.id: outdoor_area,
        }
    )


@dataclass
class GameClock:
    current_year: str = "SS1"
    current_term: int = 1
    current_week: int = 1
    day_of_week: str = "Monday"
    day_index: int = 0
    hour: int = 7
    minute: int = 0

    @property
    def time_period(self) -> TimePeriod:
        total_minutes = self.hour * 60 + self.minute
        if total_minutes >= 0 and total_minutes < 300:
            return TimePeriod.LATE_NIGHT
        if total_minutes >= 300 and total_minutes < 480:
            return TimePeriod.MORNING
        if total_minutes >= 480 and total_minutes < 900:
            return TimePeriod.SCHOOL_DAY
        if total_minutes >= 900 and total_minutes < 1080:
            return TimePeriod.AFTERNOON
        if total_minutes >= 1080 and total_minutes < 1260:
            return TimePeriod.EVENING
        if total_minutes >= 1260 and total_minutes < 1440:
            return TimePeriod.NIGHT
        return TimePeriod.LATE_NIGHT

    def advance_time(self, minutes: int) -> None:
        if minutes < 0:
            raise ValueError("minutes must be non-negative")

        total_minutes = self.hour * 60 + self.minute + minutes
        day_rollover = total_minutes // (24 * 60)
        remaining_minutes = total_minutes % (24 * 60)

        self.day_index += day_rollover
        self.hour = remaining_minutes // 60
        self.minute = remaining_minutes % 60

        if self.day_index >= 7:
            self.current_week += self.day_index // 7
            self.day_index %= 7

        if self.hour == 0 and self.minute == 0 and minutes > 0 and self.day_index > 0:
            self.day_of_week = self._weekday_name(self.day_index)
        elif self.day_index % 7 == 0 and minutes > 0:
            self.day_of_week = self._weekday_name(self.day_index)
        else:
            self.day_of_week = self._weekday_name(self.day_index)

    def _weekday_name(self, index: int) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[index % 7]


@dataclass
class GameAction:
    action_type: str
    actor: str
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    requested_time_cost: int = 0


@dataclass
class ActionResult:
    success: bool
    action: str
    message: str
    time_advanced: int = 0
    state_changes: list[str] = field(default_factory=list)
    reason: str | None = None


@dataclass
class GameEvent:
    event_type: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class GameState:
    world: WorldState
    current_location: str
    clock: GameClock = field(default_factory=GameClock)
    flags: dict[str, bool] = field(default_factory=dict)
    active_events: list[GameEvent] = field(default_factory=list)

    def has_flag(self, flag_name: str) -> bool:
        return self.flags.get(flag_name, False)

    def set_flag(self, flag_name: str) -> None:
        self.flags[flag_name] = True
        self.active_events.append(GameEvent(event_type="FLAG_CHANGED", message=f"Flag set: {flag_name}", payload={"flag": flag_name, "value": True}))

    def clear_flag(self, flag_name: str) -> None:
        self.flags[flag_name] = False
        self.active_events.append(GameEvent(event_type="FLAG_CHANGED", message=f"Flag cleared: {flag_name}", payload={"flag": flag_name, "value": False}))


class ActionValidator:
    def validate(self, action: GameAction, state: GameState) -> tuple[bool, str | None, str | None]:
        if action.actor != "player":
            return False, "INVALID_ACTOR", "Only the player can perform actions in this engine."

        if action.action_type not in {item.value for item in WorldActionType}:
            return False, "UNKNOWN_ACTION", "This action type is not supported."

        if action.action_type == "MOVE":
            if not action.target:
                return False, "MISSING_TARGET", "Movement requires a destination."
            if not state.world.can_move_between(state.current_location, action.target):
                return False, "LOCATION_NOT_CONNECTED", "You cannot get to the canteen directly from the school gate."

        if action.action_type == "STUDY":
            if state.current_location != "classroom":
                return False, "ACTION_NOT_ALLOWED", "You can only study in the classroom."

        if action.action_type == "WAIT":
            return True, None, None

        if action.action_type in {"LOOK", "TALK", "EAT", "BUY_ITEM", "GIVE_ITEM", "TAKE_ITEM", "LEAVE"}:
            allowed = state.world.get_location(state.current_location)
            if allowed is not None and action.action_type not in allowed.allowed_actions:
                return False, "ACTION_NOT_ALLOWED", "This action is not available in the current location."

        return True, None, None


class GameEngine:
    def __init__(self) -> None:
        self.validator = ActionValidator()

    def execute(self, action: GameAction, state: GameState) -> ActionResult:
        valid, reason, message = self.validator.validate(action, state)
        if not valid:
            return ActionResult(
                success=False,
                action=action.action_type,
                message=message or "Action not allowed.",
                time_advanced=0,
                state_changes=[],
                reason=reason,
            )

        if action.action_type == "MOVE":
            state.current_location = action.target
            state.active_events.append(
                GameEvent(
                    event_type="PLAYER_MOVED",
                    message=f"You move to {action.target}.",
                    payload={"from": action.target, "to": action.target},
                )
            )
            time_advance = action.requested_time_cost or 5
            state.clock.advance_time(time_advance)
            state.active_events.append(
                GameEvent(
                    event_type="TIME_ADVANCED",
                    message=f"Time advances by {time_advance} minutes.",
                    payload={"minutes": time_advance},
                )
            )
            return ActionResult(
                success=True,
                action=action.action_type,
                message=f"You walk into {action.target}.",
                time_advanced=time_advance,
                state_changes=["player_location_changed", "time_advanced"],
            )

        if action.action_type == "WAIT":
            time_advance = action.requested_time_cost or 10
            state.clock.advance_time(time_advance)
            state.active_events.append(
                GameEvent(
                    event_type="TIME_ADVANCED",
                    message=f"Time advances by {time_advance} minutes.",
                    payload={"minutes": time_advance},
                )
            )
            return ActionResult(
                success=True,
                action=action.action_type,
                message="You wait and observe the school for a while.",
                time_advanced=time_advance,
                state_changes=["time_advanced"],
            )

        time_advance = action.requested_time_cost or 0
        if time_advance:
            state.clock.advance_time(time_advance)
            state.active_events.append(
                GameEvent(
                    event_type="TIME_ADVANCED",
                    message=f"Time advances by {time_advance} minutes.",
                    payload={"minutes": time_advance},
                )
            )

        return ActionResult(
            success=True,
            action=action.action_type,
            message=f"The action {action.action_type.lower()} is processed.",
            time_advanced=time_advance,
            state_changes=["time_advanced"],
        )


__all__ = [
    "ActionResult",
    "ActionValidator",
    "GameAction",
    "GameClock",
    "GameEngine",
    "GameEvent",
    "GameState",
    "Location",
    "TimePeriod",
    "WorldActionType",
    "WorldState",
    "build_initial_world",
]
