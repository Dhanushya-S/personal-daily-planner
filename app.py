
import streamlit as st
import json

from datetime import date, datetime
from zoneinfo import ZoneInfo

from database import (
    add_task,
    get_tasks,
    update_task,
    delete_task
)

from agent import create_daily_schedule


# --------------------------------
# PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Personal Daily Planner",
    page_icon="📅",
    layout="wide"
)


# --------------------------------
# CURRENT DATE AND TIME
# --------------------------------

def get_current_datetime():

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    return now.strftime(
        "%d %B %Y | %I:%M %p | %A"
    )


def get_current_date():

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%d %B %Y")


# --------------------------------
# SIDEBAR
# --------------------------------

st.sidebar.title("📅 Daily Planner")

st.sidebar.caption(
    "Your AI Productivity Assistant"
)

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "My Tasks", "AI Planner"]
)

st.sidebar.divider()

st.sidebar.info(
    f"Today: {get_current_datetime()}"
)


# --------------------------------
# FETCH TASKS
# --------------------------------

tasks = get_tasks()


# --------------------------------
# DASHBOARD
# --------------------------------

if page == "Dashboard":

    st.title("📅 Personal Daily Planner")

    st.write(
        "Your AI-powered personal productivity assistant."
    )

    st.divider()

    st.header("Welcome Back! 👋")

    st.caption(get_current_datetime())

    total = len(tasks)

    completed = sum(
        1 for task in tasks if task[4] == 1
    )

    pending = total - completed

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Tasks", total)
    col2.metric("Pending Tasks", pending)
    col3.metric("Completed Tasks", completed)

    st.divider()

    st.subheader("📌 Recent Tasks")

    if tasks:

        for task in reversed(tasks[-5:]):

            status = (
                "✅ Completed"
                if task[4] == 1
                else "⏳ Pending"
            )

            st.write(
                f"**{task[1]}** | "
                f"{task[2]} Priority | {status}"
            )

    else:

        st.info(
            "No tasks available. Add your first task!"
        )


# --------------------------------
# MY TASKS
# --------------------------------

elif page == "My Tasks":

    st.title("📝 Manage Your Tasks")

    with st.form("add_task_form"):

        task_name = st.text_input(
            "Task Name",
            placeholder="Example: Python Study"
        )

        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"]
        )

        deadline = st.date_input(
            "Deadline",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "➕ Add Task",
            use_container_width=True
        )

        if submitted:

            clean_name = task_name.strip()

            if not clean_name:

                st.warning("Enter a task name.")

            else:

                add_task(
                    clean_name,
                    priority,
                    str(deadline)
                )

                st.success(
                    "Task saved to database!"
                )

                st.rerun()

    st.divider()

    st.subheader("📋 Your Task List")

    tasks = get_tasks()

    if not tasks:

        st.info("No tasks available.")

    else:

        for task in tasks:

            task_id = task[0]
            task_name = task[1]
            priority = task[2]
            deadline = task[3]
            completed = bool(task[4])

            col1, col2, col3 = st.columns([6, 1, 1])

            with col1:

                new_status = st.checkbox(
                    f"{task_name} | {priority} Priority | Due: {deadline}",
                    value=completed,
                    key=f"task_{task_id}"
                )

                if new_status != completed:

                    update_task(
                        task_id,
                        new_status
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_{task_id}"
                ):

                    delete_task(task_id)

                    st.success("Task deleted!")

                    st.rerun()

            with col3:

                if completed:
                    st.success("Done")
                else:
                    st.caption("Pending")


# --------------------------------
# AI PLANNER - LANGGRAPH AGENT
# --------------------------------

elif page == "AI Planner":

    st.title("🤖 AI Daily Planner")

    st.write(
        "Generate a personalized schedule using our LangGraph AI Agent."
    )

    st.divider()

    st.subheader("📋 Plan Your Day")

    with st.form("ai_planner_form"):

        activities = st.text_area(
            "What do you want to do today?",
            placeholder="Python Study, Java Practice, Exercise..."
        )

        available_hours = st.slider(
            "Available Hours",
            min_value=1,
            max_value=16,
            value=4
        )

        start_time = st.time_input(
            "Starting Time",
            value=datetime.now(
                ZoneInfo("Asia/Kolkata")
            ).time().replace(second=0, microsecond=0)
        )

        notes = st.text_area(
            "Additional Instructions",
            placeholder="Give more time for Python..."
        )

        generate = st.form_submit_button(
            "✨ Generate My Schedule",
            use_container_width=True
        )

    # --------------------------------
    # GENERATE SCHEDULE
    # --------------------------------

    if generate:

        current_tasks = get_tasks()

        database_task_list = []

        for task in current_tasks:

            if task[4] == 0:

                database_task_list.append(
                    f"{task[1]} - {task[2]} Priority - Deadline: {task[3]}"
                )

        combined_tasks = activities.strip()

        if database_task_list:

            combined_tasks += (
                "\n\nExisting Pending Database Tasks:\n"
                + "\n".join(database_task_list)
            )

        if not combined_tasks.strip():

            st.warning(
                "Enter activities or add pending tasks first."
            )

        else:

            try:

                with st.spinner(
                    "🤖 AI Agent is analyzing and preparing your schedule..."
                ):

                    schedule_result = create_daily_schedule(
                        tasks=combined_tasks,
                        available_hours=available_hours,
                        start_time=start_time.strftime("%I:%M %p"),
                        instructions=notes,
                        date=get_current_date()
                    )

                    # Handle dictionary or JSON string

                    if isinstance(schedule_result, dict):

                        schedule_data = schedule_result

                    elif isinstance(schedule_result, str):

                        schedule_data = json.loads(schedule_result)

                    else:

                        raise ValueError(
                            "Invalid schedule response."
                        )

                    # Validate schedule format

                    if not isinstance(
                        schedule_data.get("schedule"),
                        list
                    ):

                        raise ValueError(
                            "Invalid schedule format."
                        )

                    # Store schedule as JSON string

                    schedule = json.dumps(
                        schedule_data,
                        ensure_ascii=False,
                        indent=4
                    )

                    st.session_state["generated_schedule"] = schedule

                    st.session_state["schedule_date"] = get_current_date()

                st.success(
                    "Your AI schedule has been generated successfully!"
                )

                st.success(
                    "Python Schedule Validation: PASSED"
                )

            except Exception as e:

                st.error(
                    f"Agent Error: {str(e)}"
                )

    # --------------------------------
    # DISPLAY GENERATED SCHEDULE
    # --------------------------------

    if "generated_schedule" in st.session_state:

        st.divider()

        st.subheader("📅 Your AI Schedule")

        st.caption(
            f"Generated Date: {st.session_state['schedule_date']} | IST"
        )

        try:

            schedule_data = json.loads(
                st.session_state["generated_schedule"]
            )

            schedule_items = schedule_data["schedule"]

            if not schedule_items:

                st.warning("No activities found.")

            else:

                # Calculate Summary

                total_minutes = sum(
                    int(item["duration_minutes"])
                    for item in schedule_items
                )

                total_activities = len(schedule_items)

                task_count = sum(
                    1 for item in schedule_items
                    if item["type"].lower() == "task"
                )

                break_count = sum(
                    1 for item in schedule_items
                    if item["type"].lower() == "break"
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total Activities",
                    total_activities
                )

                col2.metric(
                    "Study / Task Sessions",
                    task_count
                )

                col3.metric(
                    "Breaks",
                    break_count
                )

                col4.metric(
                    "Total Duration",
                    f"{total_minutes // 60}h {total_minutes % 60}m"
                )

                st.divider()

                st.markdown(
                    "### 🗓️ Daily Timetable"
                )

                # Prepare timetable rows

                table_data = []

                for index, item in enumerate(
                    schedule_items,
                    start=1
                ):

                    table_data.append({
                        "No.": index,
                        "Activity": item["activity"],
                        "Start Time": item["start_time"],
                        "End Time": item["end_time"],
                        "Duration": f"{item['duration_minutes']} min",
                        "Goal": item["goal"],
                        "Type": item["type"].title()
                    })

                # Display timetable without pandas / pyarrow

                table_markdown = """
| No. | Activity | Start Time | End Time | Duration | Goal | Type |
|---|---|---|---|---|---|---|
"""

                for item in table_data:

                    table_markdown += (
                        f"| {item['No.']} "
                        f"| {item['Activity']} "
                        f"| {item['Start Time']} "
                        f"| {item['End Time']} "
                        f"| {item['Duration']} "
                        f"| {item['Goal']} "
                        f"| {item['Type']} |\n"
                    )

                st.markdown(table_markdown)

                # Download JSON

                st.download_button(
                    label="⬇️ Download My Schedule",
                    data=st.session_state["generated_schedule"],
                    file_name="daily_schedule.json",
                    mime="application/json",
                    use_container_width=True
                )

        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError
        ) as e:

            st.error(
                f"Unable to display schedule: {e}"
            )

        if st.button(
            "🗑️ Clear Generated Schedule"
        ):

            del st.session_state["generated_schedule"]

            if "schedule_date" in st.session_state:
                del st.session_state["schedule_date"]

            st.rerun()


# --------------------------------
# FOOTER
# --------------------------------

st.divider()

st.caption(
    "Personal Daily Planner | LangGraph Agentic AI Mini Project"
)
