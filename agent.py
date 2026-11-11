
import os
import json
from datetime import datetime
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv(override=True)

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is missing in .env file")


# ==========================================
# 2. INITIALIZE AI MODEL
# ==========================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ==========================================
# 3. DEFINE AGENT STATE
# ==========================================

class PlannerState(TypedDict, total=False):
    tasks: str
    available_hours: float
    start_time: str
    instructions: str
    date: str
    task_analysis: str
    schedule: str
    validation: str


# ==========================================
# 4. HELPER FUNCTION: TIME CONVERSION
# ==========================================

def time_to_minutes(time_text):
    parsed = datetime.strptime(time_text.strip(), "%I:%M %p")
    return parsed.hour * 60 + parsed.minute


def minutes_to_time(minutes):
    minutes = minutes % (24 * 60)
    return datetime.strptime(
        f"{minutes // 60:02d}:{minutes % 60:02d}",
        "%H:%M"
    ).strftime("%I:%M %p")


# ==========================================
# 5. NODE 1: ANALYZE TASKS
# ==========================================

def analyze_tasks(state: PlannerState):

    prompt = f"""
    You are a professional daily planning assistant.

    Analyze the user's daily tasks.

    Tasks:
    {state['tasks']}

    Available Hours:
    {state['available_hours']}

    Additional Instructions:
    {state['instructions']}

    Identify:
    1. Every task and its priority.
    2. Important and urgent tasks.
    3. Estimated time for each task.
    4. User preferences.
    5. A reasonable time allocation.

    Do not invent additional user tasks.
    Return a clear task analysis.
    """

    response = llm.invoke(prompt)

    return {
        "task_analysis": response.content
    }


# ==========================================
# 6. NODE 2: GENERATE SCHEDULE
# ==========================================

def generate_schedule(state: PlannerState):

    prompt = f"""
    You are a professional AI daily planner.

    Date: {state['date']}
    Starting Time: {state['start_time']}
    Available Hours: {state['available_hours']}

    Task Analysis:
    {state['task_analysis']}

    User Instructions:
    {state['instructions']}

    Generate a realistic daily timetable.

    RULES:
    - Start exactly at the requested starting time.
    - End exactly after the available hours.
    - Do not exceed the available time.
    - Do not leave gaps between activities.
    - Do not create overlapping activities.
    - Give more time to high-priority tasks.
    - Include short breaks.
    - Use 12-hour time format.
    - Activities must be in chronological order.
    - Every activity must have a start and end time.
    - Duration must match the start and end times.
    - Use only task or break as activity type.
    - Include a clear goal for every activity.

    Return ONLY valid JSON.
    Do not use Markdown code blocks.
    Do not add explanations outside the JSON.

    Use this exact structure:

    {{
        "schedule": [
            {{
                "activity": "Python Study",
                "start_time": "04:00 PM",
                "end_time": "05:00 PM",
                "duration_minutes": 60,
                "goal": "Complete Python practice",
                "type": "task"
            }},
            {{
                "activity": "Break",
                "start_time": "05:00 PM",
                "end_time": "05:05 PM",
                "duration_minutes": 5,
                "goal": "Rest and stretch",
                "type": "break"
            }}
        ]
    }}
    """

    response = llm.invoke(prompt)

    return {
        "schedule": response.content
    }


# ==========================================
# 7. PYTHON SCHEDULE VALIDATOR
# ==========================================

def validate_schedule_data(
    schedule_text,
    start_time,
    available_hours
):

    try:

        cleaned_text = schedule_text.strip()

        # Remove Markdown code fences if present
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.replace("```json", "")
            cleaned_text = cleaned_text.replace("```", "").strip()

        data = json.loads(cleaned_text)
        activities = data["schedule"]

        if not isinstance(activities, list) or not activities:
            return False, "Schedule is empty or invalid."

        requested_start = time_to_minutes(start_time)
        available_minutes = int(round(available_hours * 60))

        if available_minutes <= 0:
            return False, "Available hours must be greater than zero."

        expected_end = (requested_start + available_minutes) % (24 * 60)

        previous_end = None
        total_minutes = 0
        has_break = False

        for index, item in enumerate(activities, start=1):

            activity_name = item["activity"]
            activity_start = time_to_minutes(item["start_time"])
            activity_end = time_to_minutes(item["end_time"])
            duration = int(item["duration_minutes"])
            activity_type = item.get("type", "").lower()

            if duration <= 0:
                return False, f"Invalid duration in {activity_name}."

            if activity_type not in ["task", "break"]:
                return False, f"Invalid activity type in {activity_name}."

            # Calculate actual duration, including midnight crossing
            actual_duration = (
                activity_end - activity_start
            ) % (24 * 60)

            if actual_duration == 0:
                return False, f"Invalid time range in {activity_name}."

            if actual_duration != duration:
                return False, f"Duration mismatch in {activity_name}."

            # First activity must start at requested time
            if previous_end is None:

                if activity_start != requested_start:
                    return False, "Schedule does not start at requested time."

            else:

                if activity_start < previous_end:
                    return False, "Overlapping activities detected."

                if activity_start > previous_end:
                    return False, "Unscheduled time gap detected."

            if activity_type == "break":
                has_break = True

            total_minutes += duration
            previous_end = activity_end

        # Check total available duration
        if total_minutes > available_minutes:
            return False, "Schedule exceeds available hours."

        if total_minutes != available_minutes:
            return False, "Schedule does not use the available time fully."

        # Check exact ending time
        if previous_end != expected_end:
            return False, "Schedule does not end at the expected time."

        # Require at least one break
        if not has_break:
            return False, "At least one break is required."

        return True, "All schedule checks passed."

    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:

        return False, f"Schedule validation error: {error}"


# ==========================================
# 8. NODE 3: VALIDATE AND CORRECT SCHEDULE
# ==========================================

def validate_schedule(state: PlannerState):

    schedule_text = state["schedule"]

    is_valid, message = validate_schedule_data(
        schedule_text,
        state["start_time"],
        state["available_hours"]
    )

    # Ask AI to correct the schedule if validation fails
    if not is_valid:

        correction_prompt = f"""
        Correct the following daily schedule.

        Original Schedule:
        {schedule_text}

        Validation Error:
        {message}

        Required Starting Time:
        {state['start_time']}

        Available Hours:
        {state['available_hours']}

        Return ONLY valid JSON.
        Do not use Markdown code blocks.

        Required structure:

        {{
            "schedule": [
                {{
                    "activity": "Python Study",
                    "start_time": "04:00 PM",
                    "end_time": "05:00 PM",
                    "duration_minutes": 60,
                    "goal": "Complete Python practice",
                    "type": "task"
                }}
            ]
        }}

        Rules:
        - Start exactly at the required starting time.
        - End exactly after the available hours.
        - No overlapping activities.
        - No unscheduled time gaps.
        - Total duration must equal available hours.
        - Include at least one break.
        - Duration must match start and end times.
        - Use task or break as the type.
        - Use 12-hour time format.
        """

        response = llm.invoke(correction_prompt)

        corrected_schedule = response.content

        is_valid, message = validate_schedule_data(
            corrected_schedule,
            state["start_time"],
            state["available_hours"]
        )

        schedule_text = corrected_schedule

    if not is_valid:

        raise ValueError(
            f"Schedule could not pass validation: {message}"
        )

    return {
        "schedule": schedule_text,
        "validation": message
    }


# ==========================================
# 9. BUILD LANGGRAPH WORKFLOW
# ==========================================

workflow = StateGraph(PlannerState)

workflow.add_node("analyze_tasks", analyze_tasks)
workflow.add_node("generate_schedule", generate_schedule)
workflow.add_node("validate_schedule", validate_schedule)

workflow.add_edge(START, "analyze_tasks")
workflow.add_edge("analyze_tasks", "generate_schedule")
workflow.add_edge("generate_schedule", "validate_schedule")
workflow.add_edge("validate_schedule", END)

planner_agent = workflow.compile()


# ==========================================
# 10. MAIN FUNCTION
# ==========================================

def create_daily_schedule(
    tasks,
    available_hours,
    start_time,
    instructions="",
    date=""
):

    result = planner_agent.invoke({

        "tasks": tasks,
        "available_hours": available_hours,
        "start_time": start_time,
        "instructions": instructions,
        "date": date

    })

    # Return both schedule and validation result
    return {
        "schedule": result["schedule"],
        "validation": result["validation"]
    }


# ==========================================
# 11. TEST THE AGENT
# ==========================================

if __name__ == "__main__":

    test_result = create_daily_schedule(

        tasks="""
        Python Study - High Priority
        Java Practice - High Priority
        Exercise - Medium Priority
        """,

        available_hours=4,

        start_time="04:00 PM",

        instructions="Give more time to Python Study.",

        date="07 November 2026"
    )

    print("\nGENERATED DAILY SCHEDULE")

    print(test_result["schedule"])

    print("\nPYTHON VALIDATION RESULT")

    print(test_result["validation"])


print("\nLangGraph Daily Planner Agent Created Successfully!")
print("Workflow: Analyze -> Generate -> Validate")
print("Python Schedule Validation: Enabled")
