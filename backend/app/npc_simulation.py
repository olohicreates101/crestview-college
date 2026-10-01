from __future__ import annotations

import random
from collections import deque
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.game_state import GameState


class NPCActivity(str, Enum):
    ATTEND_CLASS = "ATTEND_CLASS"
    WALK = "WALK"
    EAT = "EAT"
    STUDY = "STUDY"
    TALK = "TALK"
    SOCIALIZE = "SOCIALIZE"
    PLAY = "PLAY"
    REST = "REST"
    WAIT = "WAIT"
    GO_HOME = "GO_HOME"


class NPCMood(str, Enum):
    CALM = "CALM"
    HAPPY = "HAPPY"
    EXCITED = "EXCITED"
    CURIOUS = "CURIOUS"
    NERVOUS = "NERVOUS"
    SAD = "SAD"
    ANGRY = "ANGRY"
    TIRED = "TIRED"
    EMBARRASSED = "EMBARRASSED"


class NPCGoalType(str, Enum):
    MAKE_FRIENDS = "MAKE_FRIENDS"
    ACADEMIC_SUCCESS = "ACADEMIC_SUCCESS"
    SOCIAL_STATUS = "SOCIAL_STATUS"
    AVOID_TROUBLE = "AVOID_TROUBLE"
    EXPLORE = "EXPLORE"
    HELP_SOMEONE = "HELP_SOMEONE"


class ScheduleCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    flag: str | None = None
    value: str | None = None
    time: int | None = None
    location_id: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        allowed = {"FLAG_TRUE", "FLAG_FALSE", "DAY_OF_WEEK", "TIME_BEFORE", "TIME_AFTER", "LOCATION_IS"}
        if value not in allowed:
            raise ValueError(f"Unsupported schedule condition: {value}")
        return value

    def evaluate(self, game_state: GameState) -> bool:
        if self.type == "FLAG_TRUE":
            if self.flag is None:
                raise ValueError("FLAG_TRUE requires a flag name.")
            return bool(game_state.flags.get(self.flag, False))
        if self.type == "FLAG_FALSE":
            if self.flag is None:
                raise ValueError("FLAG_FALSE requires a flag name.")
            return not bool(game_state.flags.get(self.flag, False))
        if self.type == "DAY_OF_WEEK":
            return game_state.clock.day_of_week.lower() == (self.value or "").lower()
        if self.type == "TIME_BEFORE":
            if self.time is None:
                raise ValueError("TIME_BEFORE requires a time value.")
            current_minutes = game_state.clock.hour * 60 + game_state.clock.minute
            return current_minutes < self.time
        if self.type == "TIME_AFTER":
            if self.time is None:
                raise ValueError("TIME_AFTER requires a time value.")
            current_minutes = game_state.clock.hour * 60 + game_state.clock.minute
            return current_minutes >= self.time
        if self.type == "LOCATION_IS":
            if self.location_id is None:
                raise ValueError("LOCATION_IS requires a location_id.")
            return game_state.current_location == self.location_id
        raise ValueError(f"Unsupported condition: {self.type}")


class ScheduleEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    npc_id: str = Field(..., min_length=1)
    start_time: str = Field(..., min_length=4)
    end_time: str = Field(..., min_length=4)
    location_id: str = Field(..., min_length=1)
    activity: NPCActivity
    priority: int = 5
    conditions: list[ScheduleCondition] = Field(default_factory=list)

    def contains_time(self, current_time: str) -> bool:
        current_minutes = self._parse_time(current_time)
        start_minutes = self._parse_time(self.start_time)
        end_minutes = self._parse_time(self.end_time)
        if end_minutes <= start_minutes:
            return current_minutes >= start_minutes or current_minutes < end_minutes
        return start_minutes <= current_minutes < end_minutes

    @staticmethod
    def _parse_time(value: str) -> int:
        if ":" not in value:
            raise ValueError(f"Invalid time string: {value}")
        hours, minutes = value.split(":", 1)
        return int(hours) * 60 + int(minutes)


class NPCSchedule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    npc_id: str = Field(..., min_length=1)
    entries: list[ScheduleEntry] = Field(default_factory=list)

    def get_active_entry(self, game_state: GameState) -> ScheduleEntry | None:
        current_time = f"{game_state.clock.hour:02d}:{game_state.clock.minute:02d}"
        active = [entry for entry in self.entries if entry.contains_time(current_time)]
        valid = []
        for entry in active:
            if all(condition.evaluate(game_state) for condition in entry.conditions):
                valid.append(entry)
        if not valid:
            return None
        return sorted(valid, key=lambda entry: (-entry.priority, entry.start_time))[0]


class NPCGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    type: NPCGoalType
    priority: int = 5
    target_id: str | None = None
    status: str = "active"


class NPCState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    npc_id: str = Field(..., min_length=1)
    current_location: str = Field(..., min_length=1)
    current_activity: NPCActivity = NPCActivity.WAIT
    mood: NPCMood = NPCMood.CALM
    active_goal: NPCGoal | None = None
    schedule_id: str | None = None
    schedule_position: int = 0
    last_updated: int = 0
    available_for_interaction: bool = True


class NPCEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    npc_id: str
    timestamp: str
    location_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class NPCSimulator:
    def __init__(self, game_state: GameState, tick_minutes: int = 30, rng: random.Random | None = None) -> None:
        self.game_state = game_state
        self.tick_minutes = tick_minutes
        self.rng = rng or random.Random(0)
        self.npcs: dict[str, NPCState] = {}
        self.schedules: dict[str, NPCSchedule] = {}
        self.events: list[NPCEvent] = []
        self._last_processed_minutes: int | None = None

    def register_npc(self, npc: NPCState, schedule: NPCSchedule | None = None) -> None:
        self.npcs[npc.npc_id] = npc
        if schedule is not None:
            self.schedules[npc.schedule_id or npc.npc_id] = schedule

    def set_schedule(self, npc_id: str, schedule: NPCSchedule) -> None:
        self.schedules[npc_id] = schedule
        npc = self.npcs.get(npc_id)
        if npc is not None:
            npc.schedule_id = npc_id

    def set_npc_activity(self, npc_id: str, activity: NPCActivity) -> None:
        npc = self.npcs.get(npc_id)
        if npc is None:
            raise ValueError(f"Unknown NPC: {npc_id}")
        if npc.current_activity == activity:
            return
        npc.current_activity = activity
        self._record_event("NPC_ACTIVITY_CHANGED", npc_id, metadata={"activity": activity.value})

    def set_npc_mood(self, npc_id: str, mood: NPCMood) -> None:
        npc = self.npcs.get(npc_id)
        if npc is None:
            raise ValueError(f"Unknown NPC: {npc_id}")
        if npc.mood == mood:
            return
        npc.mood = mood
        self._record_event("NPC_MOOD_CHANGED", npc_id, metadata={"mood": mood.value})

    def move_npc_to(self, npc_id: str, destination_id: str) -> bool:
        npc = self.npcs.get(npc_id)
        if npc is None:
            return False
        if npc.current_location == destination_id:
            return True
        if destination_id not in self.game_state.world.locations:
            return False

        current_location = self.game_state.world.locations.get(npc.current_location)
        if current_location is None:
            return False
        if destination_id not in current_location.connected_locations:
            return False

        previous_location = npc.current_location
        npc.current_location = destination_id
        self._record_event(
            "NPC_MOVED",
            npc_id,
            location_id=npc.current_location,
            metadata={"from": previous_location, "to": destination_id},
        )
        return True

    def _record_event(self, event_type: str, npc_id: str, location_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        timestamp = f"{self.game_state.clock.hour:02d}:{self.game_state.clock.minute:02d}"
        location = location_id or self.npcs.get(npc_id, NPCState(npc_id=npc_id, current_location="school_gate")).current_location
        self.events.append(
            NPCEvent(
                event_type=event_type,
                npc_id=npc_id,
                timestamp=timestamp,
                location_id=location,
                metadata=metadata or {},
            )
        )

    def _find_path(self, start: str, target: str) -> list[str] | None:
        if start == target:
            return [start]
        queue: deque[str] = deque([start])
        parents: dict[str, str | None] = {start: None}
        while queue:
            current = queue.popleft()
            if current == target:
                break
            location = self.game_state.world.locations.get(current)
            if location is None:
                continue
            for neighbor in location.connected_locations:
                if neighbor not in parents:
                    parents[neighbor] = current
                    queue.append(neighbor)
        if target not in parents:
            return None
        path: list[str] = []
        cursor: str | None = target
        while cursor is not None:
            path.append(cursor)
            cursor = parents[cursor]
        path.reverse()
        return path

    def update_for_game_time(self) -> None:
        current_minutes = self.game_state.clock.hour * 60 + self.game_state.clock.minute
        if self._last_processed_minutes is not None and current_minutes <= self._last_processed_minutes:
            return
        if self._last_processed_minutes is None:
            self._last_processed_minutes = current_minutes
        for npc in self.npcs.values():
            schedule = self.schedules.get(npc.schedule_id or npc.npc_id)
            if schedule is not None:
                entry = schedule.get_active_entry(self.game_state)
                if entry is not None:
                    if entry.location_id != npc.current_location:
                        route = self._find_path(npc.current_location, entry.location_id)
                        if route and len(route) > 1:
                            next_step = route[1]
                            if next_step in self.game_state.world.locations.get(npc.current_location, {}).connected_locations:
                                self.move_npc_to(npc.npc_id, next_step)
                    self.set_npc_activity(npc.npc_id, entry.activity)
                    npc.schedule_position = schedule.entries.index(entry)
            npc.last_updated = current_minutes
        self._last_processed_minutes = current_minutes
        self.detect_encounters()

    def detect_encounters(self) -> None:
        for npc in self.npcs.values():
            if not npc.available_for_interaction:
                continue
            if self.game_state.current_location == npc.current_location:
                self._record_event(
                    "NPC_ENCOUNTER_AVAILABLE",
                    npc.npc_id,
                    location_id=npc.current_location,
                    metadata={"available_for_interaction": True},
                )

    def register_default_npcs(self) -> None:
        amaka_goal = NPCGoal(id="goal-amaka", type=NPCGoalType.MAKE_FRIENDS, priority=10, status="active")
        chuka_goal = NPCGoal(id="goal-chuka", type=NPCGoalType.SOCIAL_STATUS, priority=9, status="active")
        sandra_goal = NPCGoal(id="goal-sandra", type=NPCGoalType.ACADEMIC_SUCCESS, priority=8, status="active")
        adeyemi_goal = NPCGoal(id="goal-adeyemi", type=NPCGoalType.AVOID_TROUBLE, priority=7, status="active")
        mysterious_goal = NPCGoal(id="goal-mysterious", type=NPCGoalType.EXPLORE, priority=6, status="active")

        default_schedules = {
            "amaka": NPCSchedule(
                npc_id="amaka",
                entries=[
                    ScheduleEntry(id="amaka_gate", npc_id="amaka", start_time="07:00", end_time="08:00", location_id="school_gate", activity=NPCActivity.WAIT, priority=10),
                    ScheduleEntry(id="amaka_class", npc_id="amaka", start_time="08:00", end_time="10:00", location_id="classroom", activity=NPCActivity.ATTEND_CLASS, priority=20),
                    ScheduleEntry(id="amaka_walk", npc_id="amaka", start_time="10:00", end_time="10:30", location_id="corridor", activity=NPCActivity.WALK, priority=12),
                    ScheduleEntry(id="amaka_canteen", npc_id="amaka", start_time="10:30", end_time="11:15", location_id="canteen", activity=NPCActivity.EAT, priority=12),
                ],
            ),
            "chuka": NPCSchedule(
                npc_id="chuka",
                entries=[
                    ScheduleEntry(id="chuka_gate", npc_id="chuka", start_time="07:00", end_time="08:00", location_id="corridor", activity=NPCActivity.WALK, priority=9),
                    ScheduleEntry(id="chuka_class", npc_id="chuka", start_time="08:00", end_time="10:00", location_id="classroom", activity=NPCActivity.ATTEND_CLASS, priority=20),
                    ScheduleEntry(id="chuka_social", npc_id="chuka", start_time="10:00", end_time="11:00", location_id="corridor", activity=NPCActivity.SOCIALIZE, priority=14),
                ],
            ),
            "sandra": NPCSchedule(
                npc_id="sandra",
                entries=[
                    ScheduleEntry(id="sandra_gate", npc_id="sandra", start_time="07:00", end_time="08:00", location_id="school_gate", activity=NPCActivity.WAIT, priority=11),
                    ScheduleEntry(id="sandra_class", npc_id="sandra", start_time="08:00", end_time="10:00", location_id="classroom", activity=NPCActivity.STUDY, priority=20),
                    ScheduleEntry(id="sandra_walk", npc_id="sandra", start_time="10:00", end_time="10:30", location_id="corridor", activity=NPCActivity.WALK, priority=10),
                ],
            ),
            "mr_adeyemi": NPCSchedule(
                npc_id="mr_adeyemi",
                entries=[
                    ScheduleEntry(id="adeyemi_entry", npc_id="mr_adeyemi", start_time="07:00", end_time="08:00", location_id="school_gate", activity=NPCActivity.WAIT, priority=10),
                    ScheduleEntry(id="adeyemi_class", npc_id="mr_adeyemi", start_time="08:00", end_time="12:00", location_id="classroom", activity=NPCActivity.ATTEND_CLASS, priority=18),
                ],
            ),
            "mysterious_student": NPCSchedule(
                npc_id="mysterious_student",
                entries=[
                    ScheduleEntry(id="mystery_walk", npc_id="mysterious_student", start_time="07:00", end_time="09:00", location_id="corridor", activity=NPCActivity.WALK, priority=6),
                    ScheduleEntry(id="mystery_wait", npc_id="mysterious_student", start_time="09:00", end_time="12:00", location_id="outdoor_area", activity=NPCActivity.WAIT, priority=6),
                ],
            ),
        }

        defaults = {
            "amaka": NPCState(
                npc_id="amaka",
                current_location="school_gate",
                current_activity=NPCActivity.WAIT,
                mood=NPCMood.CALM,
                active_goal=amaka_goal,
                schedule_id="amaka_schedule",
                schedule_position=0,
                last_updated=0,
                available_for_interaction=True,
            ),
            "chuka": NPCState(
                npc_id="chuka",
                current_location="corridor",
                current_activity=NPCActivity.WALK,
                mood=NPCMood.HAPPY,
                active_goal=chuka_goal,
                schedule_id="chuka_schedule",
                schedule_position=0,
                last_updated=0,
                available_for_interaction=True,
            ),
            "sandra": NPCState(
                npc_id="sandra",
                current_location="school_gate",
                current_activity=NPCActivity.WAIT,
                mood=NPCMood.CURIOUS,
                active_goal=sandra_goal,
                schedule_id="sandra_schedule",
                schedule_position=0,
                last_updated=0,
                available_for_interaction=True,
            ),
            "mr_adeyemi": NPCState(
                npc_id="mr_adeyemi",
                current_location="school_gate",
                current_activity=NPCActivity.WAIT,
                mood=NPCMood.CALM,
                active_goal=adeyemi_goal,
                schedule_id="mr_adeyemi_schedule",
                schedule_position=0,
                last_updated=0,
                available_for_interaction=False,
            ),
            "mysterious_student": NPCState(
                npc_id="mysterious_student",
                current_location="corridor",
                current_activity=NPCActivity.WALK,
                mood=NPCMood.NERVOUS,
                active_goal=mysterious_goal,
                schedule_id="mysterious_student_schedule",
                schedule_position=0,
                last_updated=0,
                available_for_interaction=True,
            ),
        }

        for npc_id, schedule in default_schedules.items():
            self.schedules[npc_id] = schedule
            npc = defaults[npc_id]
            self.npcs[npc_id] = npc


__all__ = [
    "NPCActivity",
    "NPCEvent",
    "NPCGoal",
    "NPCGoalType",
    "NPCMood",
    "NPCSchedule",
    "NPCSimulator",
    "NPCState",
    "ScheduleCondition",
    "ScheduleEntry",
]
