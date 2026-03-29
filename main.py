from pawpal_system import Scheduler, Owner, Pet, Task, TimeSlot
from datetime import datetime, date, time

def main():
    # Create scheduler
    scheduler = Scheduler()

    # Create owner
    owner = Owner(
        owner_id="owner1",
        name="Alice Johnson",
        email="alice@example.com",
        time_available_per_day=120  # 2 hours
    )
    scheduler.add_owner(owner)

    # Create pets
    pet1 = Pet(
        pet_id="pet1",
        owner_id="owner1",
        name="Buddy",
        species="Dog",
        breed="Golden Retriever",
        age=3
    )
    scheduler.add_pet("owner1", pet1)

    pet2 = Pet(
        pet_id="pet2",
        owner_id="owner1",
        name="Whiskers",
        species="Cat",
        breed="Siamese",
        age=2
    )
    scheduler.add_pet("owner1", pet2)

    # Create tasks with different durations
    task1 = Task(
        task_id="task1",
        pet_id="pet1",
        name="Morning Walk",
        description="Take Buddy for a walk in the park",
        duration_minutes=30,
        frequency="daily"
    )
    scheduler.add_task("owner1", "pet1", task1)

    task2 = Task(
        task_id="task2",
        pet_id="pet2",
        name="Feed Cat",
        description="Provide Whiskers with breakfast",
        duration_minutes=15,
        frequency="daily"
    )
    scheduler.add_task("owner1", "pet2", task2)

    task3 = Task(
        task_id="task3",
        pet_id="pet1",
        name="Playtime",
        description="Play fetch with Buddy",
        duration_minutes=45,
        frequency="daily"
    )
    scheduler.add_task("owner1", "pet1", task3)

    # Debug: check tasks added
    owner = scheduler.get_owner("owner1")
    if owner:
        for pet in owner.pets:
            print(f"Pet {pet.name} has {len(pet.tasks)} tasks")
            for t in pet.tasks:
                print(f"  - {t.name} completed: {t.completed}")

    # Create time slots for today (e.g., 9am-10am, 10am-11am, 11am-12am)
    today = date.today()
    slots = [
        TimeSlot(
            slot_id="slot1",
            start_time=datetime.combine(today, time(9, 0)),
            end_time=datetime.combine(today, time(10, 0)),
            duration_minutes=60
        ),
        TimeSlot(
            slot_id="slot2",
            start_time=datetime.combine(today, time(10, 0)),
            end_time=datetime.combine(today, time(11, 0)),
            duration_minutes=60
        ),
        TimeSlot(
            slot_id="slot3",
            start_time=datetime.combine(today, time(11, 0)),
            end_time=datetime.combine(today, time(12, 0)),
            duration_minutes=60
        )
    ]

    # Generate today's schedule
    schedule = scheduler.generate_owner_schedule("owner1", today, slots)

    # Debug: print pending tasks
    pending = scheduler.get_all_tasks("owner1", only_pending=True)
    print(f"Pending tasks: {len(pending)}")
    for t in pending:
        print(f"- {t.name} ({t.duration_minutes} min)")

    # Debug: print available slots
    available_slots = [s for s in slots if s.is_available]
    print(f"Available slots: {len(available_slots)}")

    # Print today's schedule in a clearer format
    print(f"Today's Schedule for {owner.name}:")
    print("=" * 50)
    if not schedule.planned_slots:
        print("No tasks scheduled.")
    else:
        for st in schedule.planned_slots:
            # Find the task details
            task = None
            pet_name = ""
            for pet in owner.pets:
                task = pet.get_task(st.task_id)
                if task:
                    pet_name = pet.name
                    break
            # Find the slot details
            slot = next((s for s in slots if s.slot_id == st.slot_id), None)
            if task and slot:
                print(f"Pet: {pet_name}")
                print(f"Task: {task.name}")
                print(f"Description: {task.description}")
                print(f"Duration: {task.duration_minutes} minutes")
                print(f"Scheduled Time: {slot.start_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"Status: {st.status}")
                print("-" * 30)

if __name__ == "__main__":
    main()