import pytest
from datetime import datetime
from pawpal_system import Task, Pet


class TestTaskCompletion:
    def test_mark_completed_changes_status(self):
        # Create a task with completed=False
        task = Task(
            task_id="test_task",
            pet_id="test_pet",
            name="Test Task",
            description="A test task",
            duration_minutes=30,
            frequency="daily",
            completed=False
        )

        # Verify initial state
        assert not task.completed
        assert task.completed_at is None

        # Mark as completed
        task.mark_completed()

        # Verify status changed
        assert task.completed
        assert task.completed_at is not None
        assert isinstance(task.completed_at, datetime)

    def test_mark_completed_idempotent(self):
        # Create a task
        task = Task(
            task_id="test_task",
            pet_id="test_pet",
            name="Test Task",
            description="A test task",
            duration_minutes=30,
            frequency="daily",
            completed=False
        )

        # Mark completed twice
        task.mark_completed()
        first_completed_at = task.completed_at
        task.mark_completed()

        # Should remain completed and timestamp unchanged
        assert task.completed
        assert task.completed_at == first_completed_at


class TestTaskAddition:
    def test_add_task_increases_pet_task_count(self):
        # Create a pet
        pet = Pet(
            pet_id="test_pet",
            owner_id="test_owner",
            name="Test Pet",
            species="Dog",
            breed="Test Breed",
            age=5
        )

        # Verify initial task count
        assert len(pet.tasks) == 0

        # Create a task
        task = Task(
            task_id="test_task",
            pet_id="test_pet",
            name="Test Task",
            description="A test task",
            duration_minutes=30,
            frequency="daily"
        )

        # Add task to pet
        pet.add_task(task)

        # Verify task count increased
        assert len(pet.tasks) == 1
        assert pet.tasks[0] == task

    def test_add_task_with_wrong_pet_id_raises_error(self):
        # Create a pet
        pet = Pet(
            pet_id="test_pet",
            owner_id="test_owner",
            name="Test Pet",
            species="Dog",
            breed="Test Breed",
            age=5
        )

        # Create a task with wrong pet_id
        task = Task(
            task_id="test_task",
            pet_id="wrong_pet",
            name="Test Task",
            description="A test task",
            duration_minutes=30,
            frequency="daily"
        )

        # Adding should raise ValueError
        with pytest.raises(ValueError, match="Task pet_id mismatch"):
            pet.add_task(task)

        # Task count should remain 0
        assert len(pet.tasks) == 0

    def test_add_multiple_tasks(self):
        # Create a pet
        pet = Pet(
            pet_id="test_pet",
            owner_id="test_owner",
            name="Test Pet",
            species="Dog",
            breed="Test Breed",
            age=5
        )

        # Add two tasks
        task1 = Task(
            task_id="task1",
            pet_id="test_pet",
            name="Task 1",
            description="First task",
            duration_minutes=15,
            frequency="daily"
        )
        task2 = Task(
            task_id="task2",
            pet_id="test_pet",
            name="Task 2",
            description="Second task",
            duration_minutes=45,
            frequency="daily"
        )

        pet.add_task(task1)
        pet.add_task(task2)

        # Verify both added
        assert len(pet.tasks) == 2
        assert task1 in pet.tasks
        assert task2 in pet.tasks