from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from typing import List, Optional, Dict


@dataclass
class Task:
    task_id: str
    pet_id: str
    name: str
    description: str
    duration_minutes: int
    frequency: str = "once"  # once, daily, weekly
    completed: bool = False
    completed_at: Optional[datetime] = None

    # Mark the task as completed and set the completion timestamp.
    def mark_completed(self) -> None:
        if self.completed:
            return
        self.completed = True
        self.completed_at = datetime.now(timezone.utc)

    # Reset the task to incomplete status.
    def reset(self) -> None:
        self.completed = False
        self.completed_at = None

    # Convert the task to a dictionary representation.
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
        }


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    breed: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    # Add a task to this pet's task list.
    def add_task(self, task: Task) -> None:
        if task.pet_id != self.pet_id:
            raise ValueError("Task pet_id mismatch")
        self.tasks.append(task)

    # Remove a task from this pet's task list by task_id.
    def remove_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                self.tasks.pop(i)
                return True
        return False

    # Retrieve a task by task_id from this pet's tasks.
    def get_task(self, task_id: str) -> Optional[Task]:
        return next((task for task in self.tasks if task.task_id == task_id), None)

    # Get a list of all tasks for this pet.
    def get_tasks(self) -> List[Task]:
        return list(self.tasks)

    # Get a list of pending (incomplete) tasks for this pet.
    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self.tasks if not task.completed]

    # Get a list of completed tasks for this pet.
    def get_completed_tasks(self) -> List[Task]:
        return [task for task in self.tasks if task.completed]

    # Update pet attributes with provided keyword arguments.
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

    # Add a pet to this owner's pet list.
    def add_pet(self, pet: Pet) -> None:
        if pet.owner_id != self.owner_id:
            raise ValueError("Pet owner_id mismatch")
        self.pets.append(pet)

    # Remove a pet from this owner's pet list by pet_id.
    def remove_pet(self, pet_id: str) -> bool:
        for i, pet in enumerate(self.pets):
            if pet.pet_id == pet_id:
                self.pets.pop(i)
                return True
        return False

    # Retrieve a pet by pet_id from this owner's pets.
    def get_pet(self, pet_id: str) -> Optional[Pet]:
        return next((pet for pet in self.pets if pet.pet_id == pet_id), None)

    # Get a list of all pets for this owner.
    def get_pets(self) -> List[Pet]:
        return list(self.pets)

    # Get a list of all tasks across all pets for this owner.
    def get_all_tasks(self) -> List[Task]:
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    # Get a list of all pending tasks across all pets for this owner.
    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self.get_all_tasks() if not task.completed]

    # Get a list of all completed tasks across all pets for this owner.
    def get_completed_tasks(self) -> List[Task]:
        return [task for task in self.get_all_tasks() if task.completed]

    # Update owner attributes with provided keyword arguments.
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

    # Update the priority level and reason.
    def update(self, level: int, reason: str = "") -> None:
        self.level = level
        self.reason = reason

    # Increase the priority level by the specified amount.
    def increase(self, amount: int = 1) -> None:
        self.level += amount

    # Lower the priority level by the specified amount, not below 0.
    def lower(self, amount: int = 1) -> None:
        self.level = max(0, self.level - amount)

    # Compare this priority with another, returning True if this is higher.
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

    # Check if this time slot overlaps with another time slot.
    def overlaps_with(self, other: TimeSlot) -> bool:
        return self.start_time < other.end_time and other.start_time < self.end_time


@dataclass
class ScheduledTask:
    scheduled_task_id: str
    task_id: str
    slot_id: str
    status: str
    reason: Optional[str] = ""

    # Update the status of the scheduled task.
    def update_status(self, status: str) -> None:
        self.status = status

    # Get the reason for task placement, or a default message.
    def get_placement_reason(self) -> str:
        return self.reason or "No reason provided"


@dataclass
class Schedule:
    schedule_id: str
    owner_id: str
    date: date
    planned_slots: List[ScheduledTask] = field(default_factory=list)

    # Generate a daily schedule by assigning tasks to available time slots.
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

    # Get the list of planned scheduled tasks.
    def get_plan(self) -> List[ScheduledTask]:
        return list(self.planned_slots)

    # Provide a textual explanation of the scheduled plan.
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

    # Add an owner to the scheduler's registry.
    def add_owner(self, owner: Owner) -> None:
        if owner.owner_id in self.owners:
            raise ValueError("Owner already exists")
        self.owners[owner.owner_id] = owner

    # Retrieve an owner by owner_id.
    def get_owner(self, owner_id: str) -> Optional[Owner]:
        return self.owners.get(owner_id)

    # Add a pet to the specified owner.
    def add_pet(self, owner_id: str, pet: Pet) -> None:
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        owner.add_pet(pet)

    # Add a task to the specified pet of the specified owner.
    def add_task(self, owner_id: str, pet_id: str, task: Task) -> None:
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        pet = owner.get_pet(pet_id)
        if not pet:
            raise ValueError("Pet not found")
        pet.add_task(task)

    # Get all tasks for the specified owner, optionally only pending ones.
    def get_all_tasks(self, owner_id: str, only_pending: bool = False) -> List[Task]:
        owner = self.get_owner(owner_id)
        if not owner:
            return []
        return owner.get_pending_tasks() if only_pending else owner.get_all_tasks()

    # Mark the specified task as completed.
    def complete_task(self, owner_id: str, pet_id: str, task_id: str) -> None:
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

    # Generate a daily schedule for the specified owner.
    def generate_owner_schedule(self, owner_id: str, day: date, timeslots: List[TimeSlot]) -> Schedule:
        owner = self.get_owner(owner_id)
        if not owner:
            raise ValueError("Owner not found")

        schedule = Schedule(schedule_id=f"{owner_id}-{day.isoformat()}", owner_id=owner_id, date=day)
        schedule.generate_daily_plan(timeslots=timeslots, tasks=owner.get_pending_tasks())
        return schedule
