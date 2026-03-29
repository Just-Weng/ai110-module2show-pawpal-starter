from pawpal_system import Scheduler, Owner, Pet, Task, TimeSlot
from datetime import datetime, date, time


def print_tasks(tasks, label):
    print(f"\n{label}")
    print("=" * 50)
    if not tasks:
        print("  (no tasks)")
        return
    for t in tasks:
        status = "✓" if t.completed else "○"
        time_str = t.time if t.time else "no time set"
        print(f"  [{status}] {time_str} | {t.name:<20} | pet_id: {t.pet_id}")


def main():
    # ------------------------------------------------------------------ setup
    scheduler = Scheduler()

    owner = Owner(
        owner_id="owner1",
        name="Alice Johnson",
        email="alice@example.com",
        time_available_per_day=120
    )
    scheduler.add_owner(owner)

    pet1 = Pet(pet_id="pet1", owner_id="owner1",
               name="Buddy", species="Dog", breed="Golden Retriever", age=3)
    pet2 = Pet(pet_id="pet2", owner_id="owner1",
               name="Whiskers", species="Cat", breed="Siamese", age=2)
    scheduler.add_pet("owner1", pet1)
    scheduler.add_pet("owner1", pet2)

    # ------------------------------------------------- tasks added OUT OF ORDER
    # Intentionally scrambled times so sort_by_time has real work to do.
    task3 = Task(
        task_id="task3", pet_id="pet1",
        name="Playtime",
        description="Play fetch with Buddy",
        duration_minutes=45, frequency="daily",
        time="14:00"
    )
    task5 = Task(
        task_id="task5", pet_id="pet2",
        name="Vet Checkup",
        description="Annual checkup for Whiskers",
        duration_minutes=60, frequency="once",
        time=None             # no time set — should sort last
    )
    task1 = Task(
        task_id="task1", pet_id="pet1",
        name="Morning Walk",
        description="Take Buddy for a walk in the park",
        duration_minutes=30, frequency="daily",
        time="08:00"
    )
    task4 = Task(
        task_id="task4", pet_id="pet2",
        name="Brush Fur",
        description="Groom Whiskers",
        duration_minutes=20, frequency="weekly",
        time="11:30"
    )
    task2 = Task(
        task_id="task2", pet_id="pet2",
        name="Feed Cat",
        description="Provide Whiskers with breakfast",
        duration_minutes=15, frequency="daily",
        time="09:00"
    )
    # ── intentional conflicts ──────────────────────────────────────────────
    # Same pet, same time: both Buddy tasks clash at 08:00
    task6 = Task(
        task_id="task6", pet_id="pet1",
        name="Flea Treatment",
        description="Apply monthly flea treatment to Buddy",
        duration_minutes=10, frequency="once",
        time="08:00"          # conflicts with task1 (Morning Walk, same pet)
    )
    # Different pets, same time: Whiskers and Buddy both at 14:00
    task7 = Task(
        task_id="task7", pet_id="pet2",
        name="Afternoon Nap Check",
        description="Check on Whiskers during afternoon nap",
        duration_minutes=5, frequency="daily",
        time="14:00"          # conflicts with task3 (Playtime, different pet)
    )

    for owner_id, pet_id, task in [
        ("owner1", "pet1", task3),
        ("owner1", "pet2", task5),
        ("owner1", "pet1", task1),
        ("owner1", "pet2", task4),
        ("owner1", "pet2", task2),
        ("owner1", "pet1", task6),   # conflicts with task1 at 08:00
        ("owner1", "pet2", task7),   # conflicts with task3 at 14:00
    ]:
        scheduler.add_task(owner_id, pet_id, task)

    # -------------------------------------------------------- mark one complete
    scheduler.complete_task("owner1", "pet1", "task1")  # Morning Walk is done

    # ------------------------------------------------------- conflict detection
    conflicts = scheduler.detect_conflicts("owner1")
    print("\nConflict Detection:")
    print("=" * 50)
    if conflicts:
        for warning in conflicts:
            print(warning)
    else:
        print("  No conflicts found.")

    # ------------------------------------------------------- sort_by_time demo
    sorted_tasks = scheduler.sort_by_time("owner1")
    print_tasks(sorted_tasks, "All tasks sorted by time (tasks with no time go last)")

    # ------------------------------------------------------- filter_tasks demos
    pending = scheduler.filter_tasks("owner1", completed=False)
    print_tasks(pending, "Filter: pending tasks only")

    completed = scheduler.filter_tasks("owner1", completed=True)
    print_tasks(completed, "Filter: completed tasks only")

    buddy_tasks = scheduler.filter_tasks("owner1", pet_name="Buddy")
    print_tasks(buddy_tasks, "Filter: all tasks for Buddy")

    whiskers_pending = scheduler.filter_tasks("owner1", completed=False, pet_name="Whiskers")
    print_tasks(whiskers_pending, "Filter: pending tasks for Whiskers")

    # ------------------------------------------------ original schedule output
    today = date.today()
    slots = [
        TimeSlot(slot_id="slot1",
                 start_time=datetime.combine(today, time(9, 0)),
                 end_time=datetime.combine(today, time(10, 0)),
                 duration_minutes=60),
        TimeSlot(slot_id="slot2",
                 start_time=datetime.combine(today, time(10, 0)),
                 end_time=datetime.combine(today, time(11, 0)),
                 duration_minutes=60),
        TimeSlot(slot_id="slot3",
                 start_time=datetime.combine(today, time(11, 0)),
                 end_time=datetime.combine(today, time(12, 0)),
                 duration_minutes=60),
    ]

    schedule = scheduler.generate_owner_schedule("owner1", today, slots)
    owner_obj = scheduler.get_owner("owner1")

    print(f"\n\nToday's Schedule for {owner_obj.name}:")
    print("=" * 50)
    if not schedule.planned_slots:
        print("No tasks scheduled.")
    else:
        for st in schedule.planned_slots:
            task = pet_name = None
            for pet in owner_obj.pets:
                task = pet.get_task(st.task_id)
                if task:
                    pet_name = pet.name
                    break
            slot = next((s for s in slots if s.slot_id == st.slot_id), None)
            if task and slot:
                print(f"Pet: {pet_name}")
                print(f"Task: {task.name}")
                print(f"Duration: {task.duration_minutes} minutes")
                print(f"Scheduled Time: {slot.start_time.strftime('%H:%M')}")
                print(f"Status: {st.status}")
                print("-" * 30)


if __name__ == "__main__":
    main()