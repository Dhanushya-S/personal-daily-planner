# Personal Daily Planner – Agentic AI Project

## 1. Project Overview

Personal Daily Planner is an AI-powered productivity application designed to help users organize daily tasks, manage priorities, and generate personalized schedules.

The project uses Agentic AI concepts with LangChain and LangGraph to analyze tasks, generate schedules, and validate the generated timetable.

## 2. Key Features

- AI-powered daily schedule generation.
- Task management with priority and deadlines.
- SQLite database for persistent task storage.
- Smart schedule validation using Python.
- Automatic date and time retrieval using an IST tool.
- Short-term conversational memory using InMemorySaver.
- LangSmith tracing and monitoring.
- Interactive web application using Streamlit.
- Schedule download functionality.

## 3. Technologies Used

- Python
- LangChain
- LangGraph
- Groq LLM (GPT-OSS-120B)
- Streamlit
- SQLite
- LangSmith
- Jupyter Notebook
- Python-dotenv

## 4. Project Structure

```text
personal-daily-planner/
│
├── agent.py
├── app.py
├── database.py
├── Daily_Planner.ipynb
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── planner.db
```

**Note:** `.env`, `.venv`, and `planner.db` are local files and are excluded from Git tracking.

## 5. Agent Workflow

The LangGraph workflow consists of three sequential nodes:

1. **Analyze Tasks:** Identifies tasks, priorities, estimated time, and user preferences.
2. **Generate Schedule:** Creates a personalized timetable based on available hours and instructions.
3. **Validate Schedule:** Reviews the generated timetable and corrects scheduling issues.

Workflow:

`Analyze Tasks → Generate Schedule → Validate Schedule`

## 6. Single Agent Demonstration

The Jupyter Notebook demonstrates a single AI agent with:

- One system prompt and agent persona.
- Date and Time Tool.
- Short-term memory using InMemorySaver.
- Three-turn conversation using the same thread ID.
- LangSmith tracing with project tags.

## 7. Smart Schedule Validation

Python-based validation checks:

- Total schedule duration.
- Available time limit.
- Activity start and end times.
- Overlapping activities.
- Activity duration consistency.
- Unscheduled time gap detection.
- Break availability.

## 8. How to Run

### Step 1: Create a Virtual Environment

```bash
python -m venv .venv
```

### Step 2: Activate the Environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys

Create a `.env` file in the project folder and add:

```env
GROQ_API_KEY=your_groq_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=personal-daily-planner
```

Replace the placeholder values with your own API keys. Never upload real API keys to GitHub.

### Step 5: Run the Application

```bash
python -m streamlit run app.py
```

The application will open in your browser.

## 9. Project Outcome

Successfully developed an AI-powered Personal Daily Planner with task management, personalized schedule generation, Python-based validation, short-term conversational memory, and LangSmith monitoring.

## 10. Future Enhancements

- Calendar integration.
- Reminder notifications.
- Weekly productivity reports.
- Improved schedule personalization.

