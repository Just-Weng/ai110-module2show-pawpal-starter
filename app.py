import streamlit as st
from pawpal_system import (
    Scheduler, Owner, Pet, Task, Priority, TimeSlot, Schedule, ScheduledTask
)
from datetime import datetime, date, timedelta
import uuid

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Initialize scheduler (global registry of all owners)
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = Scheduler()

# Initialize current owner ID
if 'current_owner_id' not in st.session_state:
    st.session_state.current_owner_id = None

# Initialize current schedule
if 'current_schedule' not in st.session_state:
    st.session_state.current_schedule = None

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")

st.markdown(
    """
**PawPal+** helps pet owners manage and schedule care tasks for their pets.
Create an owner, add pets, add tasks, and generate optimized daily schedules.
"""
)

st.divider()

# ============================================================================
# SECTION 1: Owner Management
# ============================================================================

st.subheader("👤 Owner Profile")

col1, col2, col3 = st.columns(3)

with col1:
    owner_action = st.radio(
        "Owner Action",
        ["View Existing", "Create New Owner"],
        horizontal=True,
        key="owner_action_radio"
    )

if owner_action == "Create New Owner":
    with col1:
        new_owner_name = st.text_input("Owner Name", value="Jordan", key="new_owner_name")
    with col2:
        new_owner_email = st.text_input("Email", value="jordan@email.com", key="new_owner_email")
    with col3:
        time_available = st.number_input(
            "Time Available (min/day)",
            min_value=30,
            max_value=1440,
            value=180,
            key="time_available"
        )
    
    if st.button("✨ Create Owner", key="create_owner_btn"):
        owner_id = str(uuid.uuid4())[:8]
        new_owner = Owner(
            owner_id=owner_id,
            name=new_owner_name,
            email=new_owner_email,
            time_available_per_day=int(time_available)
        )
        st.session_state.scheduler.add_owner(new_owner)
        st.session_state.current_owner_id = owner_id
        st.success(f"✅ Owner '{new_owner_name}' created!")
        st.rerun()

else:  # View Existing
    # List all owners in scheduler
    owner_list = list(st.session_state.scheduler.owners.keys())
    
    if owner_list:
        selected_owner_id = st.selectbox(
            "Select Owner",
            owner_list,
            format_func=lambda oid: st.session_state.scheduler.get_owner(oid).name,
            key="select_owner"
        )
        st.session_state.current_owner_id = selected_owner_id
    else:
        st.info("No owners yet. Create one using the 'Create New Owner' option above.")
        st.stop()

# Display current owner info
if st.session_state.current_owner_id:
    current_owner = st.session_state.scheduler.get_owner(st.session_state.current_owner_id)
    
    if current_owner:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Owner", current_owner.name)
        with col2:
            st.metric("Email", current_owner.email)
        with col3:
            st.metric("Pets", len(current_owner.get_pets()))
        with col4:
            st.metric("Total Tasks", len(current_owner.get_all_tasks()))

st.divider()

# ============================================================================
# SECTION 2: Pet Management
# ============================================================================

if st.session_state.current_owner_id:
    current_owner = st.session_state.scheduler.get_owner(st.session_state.current_owner_id)
    
    st.subheader("🐾 Manage Pets")
    
    # Add Pet Section
    st.markdown("**Add a New Pet**")
    pet_col1, pet_col2, pet_col3, pet_col4 = st.columns(4)
    
    with pet_col1:
        pet_name = st.text_input("Pet Name", value="Mochi", key="pet_name_input")
    
    with pet_col2:
        species = st.selectbox(
            "Species",
            ["dog", "cat", "rabbit", "bird", "hamster", "other"],
            key="pet_species_input"
        )
    
    with pet_col3:
        breed = st.text_input("Breed", value="Golden Retriever", key="pet_breed_input")
    
    with pet_col4:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2, key="pet_age_input")
    
    if st.button("➕ Add Pet", key="add_pet_btn"):
        pet_id = str(uuid.uuid4())[:8]
        new_pet = Pet(
            pet_id=pet_id,
            owner_id=st.session_state.current_owner_id,
            name=pet_name,
            species=species,
            breed=breed,
            age=age
        )
        st.session_state.scheduler.add_pet(st.session_state.current_owner_id, new_pet)
        st.success(f"✅ Added {pet_name}!")
        st.rerun()
    
    # Display Pets
    pets = current_owner.get_pets()
    if pets:
        st.markdown("**Your Pets**")
        pet_display_data = [
            {
                "Name": pet.name,
                "Species": pet.species.capitalize(),
                "Breed": pet.breed,
                "Age": f"{pet.age} years",
                "Tasks": len(pet.get_tasks())
            }
            for pet in pets
        ]
        st.table(pet_display_data)
    else:
        st.info("No pets yet. Add one above!")
    
    st.divider()
    
    # ============================================================================
    # SECTION 3: Task Management
    # ============================================================================
    
    st.subheader("📋 Manage Tasks")
    
    if pets:
        st.markdown("**Add a Task to a Pet**")
        task_col1, task_col2 = st.columns(2)
        
        with task_col1:
            selected_pet_id = st.selectbox(
                "Select Pet",
                [p.pet_id for p in pets],
                format_func=lambda pid: next(p.name for p in pets if p.pet_id == pid),
                key="task_pet_select"
            )
        
        task_col3, task_col4, task_col5, task_col6 = st.columns(4)
        
        with task_col3:
            task_name = st.text_input("Task Name", value="Morning walk", key="task_name_input")
        
        with task_col4:
            task_desc = st.text_input("Description", value="30-min walk around park", key="task_desc_input")
        
        with task_col5:
            duration = st.number_input(
                "Duration (min)",
                min_value=1,
                max_value=240,
                value=30,
                key="task_duration_input"
            )
        
        with task_col6:
            frequency = st.selectbox(
                "Frequency",
                ["once", "daily", "weekly"],
                key="task_frequency_input"
            )
        
        if st.button("➕ Add Task", key="add_task_btn"):
            task_id = str(uuid.uuid4())[:8]
            new_task = Task(
                task_id=task_id,
                pet_id=selected_pet_id,
                name=task_name,
                description=task_desc,
                duration_minutes=int(duration),
                frequency=frequency
            )
            st.session_state.scheduler.add_task(
                st.session_state.current_owner_id,
                selected_pet_id,
                new_task
            )
            st.success(f"✅ Added task '{task_name}'!")
            st.rerun()
        
        # Display All Tasks
        all_tasks = current_owner.get_all_tasks()
        if all_tasks:
            st.markdown("**All Tasks**")
            
            # Tabs for task views
            tab1, tab2, tab3 = st.tabs(["All Tasks", "Pending", "Completed"])
            
            with tab1:
                task_data = [
                    {
                        "Pet": next(p.name for p in pets if p.pet_id == t.pet_id),
                        "Task": t.name,
                        "Description": t.description,
                        "Duration (min)": t.duration_minutes,
                        "Frequency": t.frequency.capitalize(),
                        "Status": "✅ Done" if t.completed else "⏳ Pending"
                    }
                    for t in all_tasks
                ]
                st.dataframe(task_data, width='stretch')
            
            with tab2:
                pending = current_owner.get_pending_tasks()
                if pending:
                    pending_data = [
                        {
                            "Pet": next(p.name for p in pets if p.pet_id == t.pet_id),
                            "Task": t.name,
                            "Duration (min)": t.duration_minutes,
                            "Frequency": t.frequency.capitalize()
                        }
                        for t in pending
                    ]
                    st.dataframe(pending_data, width='stretch')
                else:
                    st.info("All tasks completed! 🎉")
            
            with tab3:
                completed = current_owner.get_completed_tasks()
                if completed:
                    completed_data = [
                        {
                            "Pet": next(p.name for p in pets if p.pet_id == t.pet_id),
                            "Task": t.name,
                            "Completed": t.completed_at.strftime("%Y-%m-%d %H:%M") if t.completed_at else "Unknown"
                        }
                        for t in completed
                    ]
                    st.dataframe(completed_data, width='stretch')
                else:
                    st.info("No completed tasks yet.")
        else:
            st.info("No tasks yet. Add one above!")
    else:
        st.warning("⚠️ Add a pet first before creating tasks!")
    
    st.divider()
    
    # ============================================================================
    # SECTION 4: Schedule Generation
    # ============================================================================
    
    st.subheader("📅 Generate Daily Schedule")
    
    pending_tasks = current_owner.get_pending_tasks()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        schedule_date = st.date_input(
            "Select Date",
            value=date.today(),
            key="schedule_date_input"
        )
    
    with col2:
        start_hour = st.number_input(
            "Start Time (hour)",
            min_value=0,
            max_value=23,
            value=8,
            key="start_hour_input"
        )
    
    with col3:
        end_hour = st.number_input(
            "End Time (hour)",
            min_value=0,
            max_value=23,
            value=18,
            key="end_hour_input"
        )
    
    st.markdown(f"**Ready to schedule:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Tasks", len(pending_tasks))
    with col2:
        total_duration = sum(t.duration_minutes for t in pending_tasks)
        st.metric("Total Duration (min)", total_duration)
    with col3:
        st.metric("Time Available (min)", current_owner.time_available_per_day)
    
    if st.button("🚀 Generate Schedule", key="generate_schedule_btn", width='stretch'):
        if not pending_tasks:
            st.error("❌ No pending tasks to schedule!")
        else:
            # Create time slots for the day
            timeslots = []
            current_time = datetime.combine(schedule_date, datetime.min.time()).replace(hour=start_hour)
            end_time = datetime.combine(schedule_date, datetime.min.time()).replace(hour=end_hour)
            
            # Create 30-minute slots throughout the day
            slot_duration = 30
            while current_time < end_time:
                slot_end = current_time + timedelta(minutes=slot_duration)
                if slot_end > end_time:
                    slot_end = end_time
                
                slot_id = str(uuid.uuid4())[:8]
                timeslot = TimeSlot(
                    slot_id=slot_id,
                    start_time=current_time,
                    end_time=slot_end,
                    duration_minutes=int((slot_end - current_time).total_seconds() / 60)
                )
                timeslots.append(timeslot)
                current_time = slot_end
            
            # Generate schedule using scheduler
            schedule = st.session_state.scheduler.generate_owner_schedule(
                st.session_state.current_owner_id,
                schedule_date,
                timeslots
            )
            st.session_state.current_schedule = schedule
            st.success("✅ Schedule generated!")
            st.rerun()
    
    # Display Generated Schedule
    if st.session_state.current_schedule:
        st.markdown("---")
        st.markdown("### 📆 Your Daily Schedule")
        
        schedule = st.session_state.current_schedule
        explanation = schedule.explain_plan()
        st.info(explanation)
        
        # Detailed view
        with st.expander("📊 Detailed Schedule View", expanded=True):
            planned_tasks = schedule.get_plan()
            
            if planned_tasks:
                schedule_data = []
                for scheduled in planned_tasks:
                    task = next(
                        (t for t in pending_tasks if t.task_id == scheduled.task_id),
                        None
                    )
                    if task:
                        schedule_data.append({
                            "Task ID": scheduled.task_id,
                            "Task Name": task.name,
                            "Slot ID": scheduled.slot_id,
                            "Status": scheduled.status.capitalize(),
                            "Duration (min)": task.duration_minutes,
                            "Reason": scheduled.get_placement_reason()
                        })
                
                st.dataframe(schedule_data, width='stretch')
            else:
                st.warning("⚠️ No tasks could be scheduled in the available time slots.")
        
        # Mark tasks as completed
        if st.session_state.current_schedule:
            st.markdown("**Mark Tasks as Completed**")
            completed_col1, completed_col2 = st.columns([3, 1])
            
            with completed_col1:
                completed_task_id = st.selectbox(
                    "Select task to mark complete",
                    [t.task_id for t in pending_tasks],
                    format_func=lambda tid: next(t.name for t in pending_tasks if t.task_id == tid),
                    key="complete_task_select"
                )
            
            with completed_col2:
                st.write("")
                if st.button("✅ Mark Complete", key="mark_complete_btn"):
                    # Find the pet and complete the task
                    task_to_complete = next(t for t in pending_tasks if t.task_id == completed_task_id)
                    pet_id = task_to_complete.pet_id
                    
                    st.session_state.scheduler.complete_task(
                        st.session_state.current_owner_id,
                        pet_id,
                        completed_task_id
                    )
                    st.success(f"✅ Marked '{task_to_complete.name}' as completed!")
                    st.rerun()

st.divider()

# ============================================================================
# DEBUG INFO
# ============================================================================

with st.expander("🔧 Debug Info"):
    st.write("**Scheduler State:**")
    st.write(f"Owners: {list(st.session_state.scheduler.owners.keys())}")
    if st.session_state.current_owner_id:
        current = st.session_state.scheduler.get_owner(st.session_state.current_owner_id)
        st.write(f"Current Owner: {current.name}")
        st.write(f"Pets: {[p.name for p in current.get_pets()]}")
        st.write(f"All Tasks: {len(current.get_all_tasks())}")
        st.write(f"Pending Tasks: {len(current.get_pending_tasks())}")