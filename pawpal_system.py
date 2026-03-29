from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict
import uuid


# ── helpers ───────────────────────────────────────────────────────────────────

def _next_occurrence(current_time: Optional[str], frequency: str) -> tuple[str, Optional[str]]:
    """
    Given a frequency and an optional "HH:MM" time string, return
    (new_task_id_suffix, new_time) for the recurring copy.

    The new task_id suffix is a short UUID fragment so IDs stay unique
    even when the same task recurs many times.
    """
    suffix = uuid.uuid4().hex[:6]
    return suffix, current_time          # time-of-day stays the same each recurrence


def _due_date_for(frequency: str, from_date: date) -> date:
    """
    Return the next due date for a recurring task.
      daily  → tomorrow
      weekly → same weekday next week
    """
    if frequency == "daily":
        return from_date + timedelta(days=1)
    if frequency == "weekly":
        return from_date + timedelta(weeks=1)
    raise ValueError(f"Unexpected recurring frequency: {frequency!r}")


# ── dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class Task:
    task_id: str
    pet_id: str
    name: str
    description: str
    duration_minutes: int
    frequency: str = "once"        # once | daily | weekly
    completed: bool = False
    completed_at: Optional[datetime] = None
    time: Optional[str] = None     # "HH:MM" e.g. "09:30"
    due_date: Optional[date] = None

    def mark_completed(self) -> None:
        if self.completed:
            return
        self.completed = True
        self.completed_at = datetime.now(timezone.utc)

    def reset(self) -> None:
        self.completed = False
        self.completed_at = None

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "pet_id": self.pet_id,
            "name": self.name,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "frequency": self.frequency,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "time": self.time,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }

    def make_next_occurrence(self) -> "Task":
        """
        Return a fresh, incomplete Task for the next occurrence of this
        recurring task.  Only valid when frequency is 'daily' or 'weekly'.

        How timedelta is used
        ─────────────────────
        timedelta(days=1)   adds exactly one day to a date object.
        timedelta(weeks=1)  adds exactly seven days.
        Python's date arithmetic handles month/year rollovers automatically,
        so date(2024, 12, 31) + timedelta(days=1) → date(2025, 1, 1).

        The new task gets:
          • a unique ID built from the original ID + a short UUID suffix
          • the same time-of-day ("HH:MM") as the completed task
          • a due_date shifted forward by the appropriate timedelta
          • completed = False  (starts fresh)
        """
        if self.frequency not in ("daily", "weekly"):
            raise ValueError(
                f"make_next_occurrence called on a non-recurring task "
                f"(frequency={self.frequency!r})"
            )

        suffix, next_time = _next_occurrence(self.time, self.frequency)
        base_date = self.due_date or date.today()
        next_due = _due_date_for(self.frequency, base_date)

        return Task(
            task_id=f"{self.task_id}-{suffix}",
            pet_id=self.pet_id,
            name=self.name,
            description=self.description,
            duration_minutes=self.duration_minutes,
            frequency=self.frequency,
            completed=False,
            completed_at=None,
            time=next_time,
            due_date=next_due,
        )


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    breed: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        if task.pet_id != self.pet_id:
            raise ValueError("Task pet_id mismatch")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                self.tasks.pop(i)
                return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def get_tasks(self) -> List[Task]:
        return list(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.completed]

    def update_pet(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class Owner:
    owner_id: str
    name: str
    email: str
    time_available_per_day: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        if pet.owner_id != self.owner_id:
            raise ValueError("Pet owner_id mismatch")
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> bool:
        for i, pet in enumerate(self.pets):
            if pet.pet_id == pet_id:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        return next((p for p in self.pets if p.pet_id == pet_id), None)

    def get_pets(self) -> List[Pet]:
        return list(self.pets)

    def get_all_tasks(self) -> List[Task]:
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self.get_all_tasks() if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        return [t for t in self.get_all_tasks() if t.completed]

    def update_owner(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class Priority:
    priority_id: str
    task_id: str
    level: int
    reason: Optional[str] = None

    def update(self, level: int, reason: str = "") -> None:
        self.level = level
        self.reason = reason

    def increase(self, amount: int = 1) -> None:
        self.level += amount

    def lower(self, amount: int = 1) -> None:
        self.level = max(0, self.level - amount)

    def compare(self, other: Priority) -> bool:
        return self.level > other.level


@dataclass
class TimeSlot:
    slot_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_available: bool = True
    owner_notes: Optional[str] = ""

    def overlaps_with(self, other: TimeSlot) -> bool:
        return self.start_time < other.end_time and other.start_time < self.end_time


@dataclass
class ScheduledTask:
    scheduled_task_id: str
    task_id: str
    slot_id: str
    status: str
    reason: Optional[str] = ""

    def update_status(self, status: str) -> None:
        self.status = status

    def get_placement_reason(self) -> str:
        return self.reason or "No reason provided"


@dataclass
class Schedule:
    schedule_id: str
    owner_id: str
    date: date
    planned_slots: List[ScheduledTask] = field(default_factory=list)

    def generate_daily_plan(self, timeslots: List[TimeSlot], tasks: List[Task]) -> List[ScheduledTask]:
        available = [ts for ts in timeslots if ts.is_available]
        available.sort(key=lambda ts: ts.start_time)

        pending_tasks = [t for t in tasks if not t.completed]
        pending_tasks.sort(key=lambda t: (-1 if t.frequency == "daily" else 0, t.duration_minutes))

        schedule: List[ScheduledTask] = []
        index = 0

        for task in pending_tasks:
            while index < len(available) and available[index].duration_minutes < task.duration_minutes:
                index += 1
            if index >= len(available):
                break

            slot = available[index]
            schedule.append(ScheduledTask(
                scheduled_task_id=f"{self.schedule_id}-{task.task_id}",
                task_id=task.task_id,
                slot_id=slot.slot_id,
                status="scheduled"
            ))
            slot.is_available = False
            index += 1

        self.planned_slots = schedule
        return schedule

    def get_plan(self) -> List[ScheduledTask]:
        return list(self.planned_slots)

    def explain_plan(self) -> str:
        if not self.planned_slots:
            return "No tasks scheduled."
        lines = [f"Scheduled {len(self.planned_slots)} tasks for {self.date.isoformat()}:"]
        for st in self.planned_slots:
            lines.append(f"- {st.task_id} in slot {st.slot_id} status {st.status}")
        return "\n".join(lines)


@dataclass
class Scheduler:
    owners: Dict[str, Owner] = field(default_factory=dict)

    def add_owner(self, owner: Owner) -> None:
        if owner.owner_id in self.owners:
            raise ValueError("Owner already exists")
        self.owners[owner.owner_id] = owner

    def get_owner(self, owner_id: str) -> Optional[Owner]:
        return self.owners.get(owner_id)

    def add_pet(self, owner_id: str, pet: Pet) -> None:
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        owner.add_pet(pet)

    def add_task(self, owner_id: str, pet_id: str, task: Task) -> None:
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        pet = owner.get_pet(pet_id)
        if not pet:
            raise ValueError("Pet not found")
        pet.add_task(task)

    def get_all_tasks(self, owner_id: str, only_pending: bool = False) -> List[Task]:
        owner = self.get_owner(owner_id)
        if not owner:
            return []
        return owner.get_pending_tasks() if only_pending else owner.get_all_tasks()

    def complete_task(self, owner_id: str, pet_id: str, task_id: str) -> Optional[Task]:
        """
        Mark a task complete and, if it recurs (daily/weekly), automatically
        add the next occurrence to the same pet's task list.

        Returns the newly created recurring Task, or None for one-off tasks.

        timedelta in action
        ───────────────────
        Inside Task.make_next_occurrence():
          next_due = base_date + timedelta(days=1)   # daily
          next_due = base_date + timedelta(weeks=1)  # weekly

        timedelta is imported from Python's standard `datetime` module.
        It represents a duration and supports + / - with date and datetime
        objects directly, so there is no manual day/month arithmetic needed.
        """
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        pet = owner.get_pet(pet_id)
        if not pet:
            raise ValueError("Pet not found")
        task = pet.get_task(task_id)
        if not task:
            raise ValueError("Task not found")

        task.mark_completed()

        # Auto-schedule the next occurrence for recurring tasks
        if task.frequency in ("daily", "weekly"):
            next_task = task.make_next_occurrence()
            pet.add_task(next_task)
            return next_task

        return None

    def generate_owner_schedule(self, owner_id: str, day: date, timeslots: List[TimeSlot]) -> Schedule:
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        schedule = Schedule(schedule_id=f"{owner_id}-{day.isoformat()}", owner_id=owner_id, date=day)
        schedule.generate_daily_plan(timeslots=timeslots, tasks=owner.get_pending_tasks())
        return schedule

    def detect_conflicts(self, owner_id: str) -> List[str]:
        """
        Lightweight conflict detection: compare every pair of tasks and
        return a list of human-readable warning strings for any two tasks
        that share the same 'time' value ("HH:MM").

        Strategy — why this is "lightweight"
        ──────────────────────────────────────
        Rather than raising an exception (which would crash the program),
        this method collects all conflicts into a list and returns them.
        The caller decides what to do — print a warning, log it, block
        scheduling, etc.  An empty list means no conflicts were found.

        The detection itself uses a dict to group tasks by time in a single
        O(n) pass, then flags any bucket with more than one task.  This
        avoids the O(n²) cost of comparing every pair explicitly.

        Tasks with no time set (None) are skipped — they have no scheduled
        time to conflict on.
        """
        owner = self.get_owner(owner_id)
        if not owner:
            return []

        # Build a pet_id → pet name lookup for readable warning messages
        pet_name_by_id: Dict[str, str] = {
            pet.pet_id: pet.name for pet in owner.get_pets()
        }

        # Group pending tasks by their "HH:MM" time slot
        by_time: Dict[str, List[Task]] = {}
        for task in owner.get_pending_tasks():
            if task.time is None:
                continue
            by_time.setdefault(task.time, []).append(task)

        warnings: List[str] = []
        for slot_time, tasks in by_time.items():
            if len(tasks) < 2:
                continue
            # Build one warning per conflicting pair
            for i in range(len(tasks)):
                for j in range(i + 1, len(tasks)):
                    a, b = tasks[i], tasks[j]
                    a_pet = pet_name_by_id.get(a.pet_id, a.pet_id)
                    b_pet = pet_name_by_id.get(b.pet_id, b.pet_id)
                    warnings.append(
                        f"⚠ Conflict at {slot_time}: "
                        f'"{a.name}" ({a_pet}) and "{b.name}" ({b_pet}) '
                        f"are both scheduled at the same time."
                    )

        return warnings

    def sort_by_time(self, owner_id: str) -> List[Task]:
        """
        Return all tasks sorted chronologically by their 'time' field ("HH:MM").
        Tasks with no time set are placed at the end via the sentinel "99:99".
        """
        tasks = self.get_all_tasks(owner_id)
        return sorted(tasks, key=lambda t: t.time or "99:99")

    def filter_tasks(
        self,
        owner_id: str,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """
        Filter tasks by completion status and/or pet name (case-insensitive).
        Passing None for either parameter disables that filter.
        """
        owner = self.get_owner(owner_id)
        if not owner:
            return []

        pet_name_by_id: Dict[str, str] = {
            pet.pet_id: pet.name.lower() for pet in owner.get_pets()
        }

        results: List[Task] = []
        for task in owner.get_all_tasks():
            if completed is not None and task.completed != completed:
                continue
            if pet_name is not None:
                if pet_name_by_id.get(task.pet_id, "") != pet_name.lower():
                    continue
            results.append(task)

        return results