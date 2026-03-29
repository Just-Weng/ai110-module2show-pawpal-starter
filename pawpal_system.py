from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

@dataclass
class Owner:
    owner_id: str
    name: str
    email: str
    time_available_per_day: int

    def add_owner(self, owner_data: dict) -> None:
        pass

    def update_owner(self, **kwargs) -> None:
        pass

    def get_owner(self) -> dict:
        pass


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    breed: str
    age: int

    def add_pet(self, pet_data: dict) -> None:
        pass

    def update_pet(self, **kwargs) -> None:
        pass

    def get_pet(self) -> dict:
        pass

    def remove_pet(self) -> bool:
        pass


@dataclass
class Priority:
    priority_id: str
    task_id: str
    level: int
    reason: Optional[str] = None

    def add_priority(self, level: int, reason: str = "") -> None:
        pass

    def increase_priority(self, amount: int = 1) -> None:
        pass

    def lower_priority(self, amount: int = 1) -> None:
        pass

    def get_priority(self) -> dict:
        pass

    def compare_priorities(self, other: Priority) -> bool:
        pass


@dataclass
class TimeSlot:
    slot_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_available: bool
    owner_notes: Optional[str] = ""

    def add_time_slot(self) -> None:
        pass

    def remove_time_slot(self) -> None:
        pass

    def get_time_slot(self) -> dict:
        pass

    def overlaps_with(self, other: TimeSlot) -> bool:
        pass


@dataclass
class Task:
    task_id: str
    pet_id: str
    name: str
    category: str
    duration_minutes: int
    priority: int
    notes: Optional[str] = ""

    def add_task(self, task_data: dict) -> None:
        pass

    def update_task(self, **kwargs) -> None:
        pass

    def remove_task(self) -> None:
        pass

    def get_task(self) -> dict:
        pass


@dataclass
class ScheduledTask:
    scheduled_task_id: str
    task_id: str
    slot_id: str
    status: str
    reason: Optional[str] = ""

    def schedule_task(self, schedule_id: str, timeslot: TimeSlot) -> None:
        pass

    def update_status(self, status: str) -> None:
        pass

    def get_placement_reason(self) -> str:
        pass


@dataclass
class Schedule:
    schedule_id: str
    owner_id: str
    date: date
    planned_slots: List[ScheduledTask] = field(default_factory=list)

    def generate_daily_plan(self) -> List[ScheduledTask]:
        pass

    def get_plan(self) -> List[ScheduledTask]:
        pass

    def explain_plan(self) -> str:
        pass