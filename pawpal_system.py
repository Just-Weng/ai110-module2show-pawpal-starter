from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TimeSlot:
    slot_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_available: bool = True


@dataclass
class Task:
    task_id: str
    pet_id: str
    name: str
    description: str
    duration_minutes: int
    frequency: str  # "once", "daily", "weekly"
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    completed_at: Optional[datetime] = None

    def complete(self):
        self.completed = True
        self.completed_at = datetime.now()


@dataclass
class ScheduledTask:
    task_id: str
    slot_id: str
    status: str = "planned"          # "planned" | "skipped"
    _placement_reason: str = field(default="", repr=False)

    def get_placement_reason(self) -> str:
        return self._placement_reason


@dataclass
class Schedule:
    schedule_id: str
    owner_id: str
    schedule_date: date
    _plan: list[ScheduledTask] = field(default_factory=list)
    _skipped: list[tuple[Task, str]] = field(default_factory=list)   # (task, reason)
    _total_scheduled_minutes: int = 0

    def add_scheduled_task(self, scheduled_task: ScheduledTask):
        self._plan.append(scheduled_task)

    def add_skipped_task(self, task: Task, reason: str):
        self._skipped.append((task, reason))

    def get_plan(self) -> list[ScheduledTask]:
        return self._plan

    def get_skipped(self) -> list[tuple[Task, str]]:
        return self._skipped

    def explain_plan(self) -> str:
        n_scheduled = len(self._plan)
        n_skipped = len(self._skipped)
        lines = [
            f"📅 Schedule for {self.schedule_date}",
            f"✅ {n_scheduled} task(s) scheduled — "
            f"{self._total_scheduled_minutes} min total.",
        ]
        if n_skipped:
            skipped_names = ", ".join(t.name for t, _ in self._skipped)
            lines.append(f"⚠️ {n_skipped} task(s) could not fit: {skipped_names}.")
        lines.append("Tasks were ordered shortest-first to maximise the number completed.")
        return "  \n".join(lines)


# ============================================================================
# OWNER / PET
# ============================================================================

@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    breed: str
    age: int
    _tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        self._tasks.append(task)

    def get_tasks(self) -> list[Task]:
        return self._tasks

    def get_task(self, task_id: str) -> Optional[Task]:
        return next((t for t in self._tasks if t.task_id == task_id), None)


@dataclass
class Owner:
    owner_id: str
    name: str
    email: str
    time_available_per_day: int          # minutes
    _pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        return self._pets

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        return next((p for p in self._pets if p.pet_id == pet_id), None)

    def get_all_tasks(self) -> list[Task]:
        return [t for pet in self._pets for t in pet.get_tasks()]

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.get_all_tasks() if not t.completed]

    def get_completed_tasks(self) -> list[Task]:
        return [t for t in self.get_all_tasks() if t.completed]


# ============================================================================
# SCHEDULER  —  core logic lives here
# ============================================================================

class Scheduler:
    def __init__(self):
        self.owners: dict[str, Owner] = {}

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    def add_owner(self, owner: Owner):
        self.owners[owner.owner_id] = owner

    def get_owner(self, owner_id: str) -> Optional[Owner]:
        return self.owners.get(owner_id)

    def add_pet(self, owner_id: str, pet: Pet):
        owner = self.get_owner(owner_id)
        if owner:
            owner.add_pet(pet)

    def add_task(self, owner_id: str, pet_id: str, task: Task):
        owner = self.get_owner(owner_id)
        if owner:
            pet = owner.get_pet(pet_id)
            if pet:
                pet.add_task(task)

    def complete_task(self, owner_id: str, pet_id: str, task_id: str):
        owner = self.get_owner(owner_id)
        if owner:
            pet = owner.get_pet(pet_id)
            if pet:
                task = pet.get_task(task_id)
                if task:
                    task.complete()

    # ------------------------------------------------------------------
    # Schedule generation — Shortest Task First (STF / SJF)
    # ------------------------------------------------------------------

    def generate_owner_schedule(
        self,
        owner_id: str,
        schedule_date: date,
        timeslots: list[TimeSlot],
    ) -> Schedule:
        """
        Assigns pending tasks to available time slots using a
        Shortest-Task-First (STF) greedy algorithm.

        Algorithm
        ---------
        1. Sort pending tasks by duration_minutes ascending (shortest first).
        2. Walk the sorted task list and greedily pack tasks into the first
           contiguous block of slots that can fit the task's duration.
        3. A task that cannot fit anywhere is recorded as skipped with a reason.

        This maximises the *number* of tasks that get done when time is tight.
        """
        import uuid as _uuid

        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError(f"Owner {owner_id} not found.")

        schedule = Schedule(
            schedule_id=str(_uuid.uuid4())[:8],
            owner_id=owner_id,
            schedule_date=schedule_date,
        )

        pending_tasks = owner.get_pending_tasks()
        if not pending_tasks:
            return schedule

        # ── 1. Sort tasks: shortest duration first ──────────────────────────
        sorted_tasks = sorted(pending_tasks, key=lambda t: t.duration_minutes)

        # ── 2. Track which slots are still free ─────────────────────────────
        #    We work with a simple "minutes remaining in each slot" approach so
        #    that one slot can hold multiple short tasks back-to-back.
        slot_remaining: dict[str, int] = {
            s.slot_id: s.duration_minutes for s in timeslots if s.is_available
        }
        # Preserve slot order
        ordered_slot_ids = [s.slot_id for s in timeslots if s.is_available]

        total_minutes_used = 0

        # ── 3. Greedy assignment ─────────────────────────────────────────────
        for task in sorted_tasks:
            needed = task.duration_minutes
            placed = False

            # Find the first slot with enough remaining capacity
            for slot_id in ordered_slot_ids:
                if slot_remaining[slot_id] >= needed:
                    slot_remaining[slot_id] -= needed
                    total_minutes_used += needed

                    reason = (
                        f"Shortest-first: {needed} min task fits in slot "
                        f"(slot had {slot_remaining[slot_id] + needed} min free)."
                    )
                    st_task = ScheduledTask(
                        task_id=task.task_id,
                        slot_id=slot_id,
                        status="planned",
                        _placement_reason=reason,
                    )
                    schedule.add_scheduled_task(st_task)
                    placed = True
                    break

            if not placed:
                # No single slot can fit this task
                best_remaining = max(slot_remaining.values(), default=0)
                reason = (
                    f"No slot has {needed} min free "
                    f"(largest remaining block: {best_remaining} min)."
                )
                schedule.add_skipped_task(task, reason)

        schedule._total_scheduled_minutes = total_minutes_used
        return schedule