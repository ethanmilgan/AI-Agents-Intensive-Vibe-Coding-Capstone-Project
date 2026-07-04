# Implementation Plan: Orchestrated Multi-Agent Folder Structure

This plan reorganizes the project into a modular, separate folder structure for each subagent inside the parent agent package folder (`job-alert-agent/app`). The parent folder contains the main Orchestrator/Coordinator Agent and any shared/common files (such as database utilities) to prevent duplication.

---

## 📂 Proposed Folder Structure

Under the parent agent folder (`job-alert-agent/app`), we will establish the following structure:

```
job-alert-agent/
├── app/                       # Parent Agent Folder
│   ├── agent.py               # Coordinator Agent (Parent Orchestration, subagent calling functionality)
│   ├── tools.py               # Coordinator specific common tools
│   ├── database.py            # SQLite database schema & operations (Common across subagents)
│   ├── app_utils/             # Shared utilities (telemetry, typing)
│   │
│   ├── resume_agent/          # Resume Subagent Folder
│   │   ├── agent.py           # Resume Agent definition
│   │   ├── tools.py           # Resume parsing, ATS scoring & modification tools
│   │   ├── templates/         # HTML Templates for resume formatting
│   │   ├── implementation_plan.md # Resume Agent Explanation Plan
│   │   └── flowchart.md       # Resume Builder & Optimizer flowchart
│   │
│   ├── job_intelligence_agent/ # Job Intelligence Subagent Folder
│   │   ├── agent.py           # Job Intelligence Agent definition
│   │   ├── tools.py           # Scraper, match scoring & SMTP email tools
│   │   ├── implementation_plan.md # Job Intelligence Explanation Plan
│   │   └── flowchart.md       # Job Discovery & Analysis flowchart
│   │
│   └── application_agent/     # Application Subagent Folder
│       ├── agent.py           # Application Agent definition (Playwright controller)
│       ├── tools.py           # Trigger and status check tools
│       ├── worker.py          # Playwright background worker subprocess
│       ├── form_filler.py     # Heuristic & LLM form filling selectors
│       ├── implementation_plan.md # Application Agent Explanation Plan
│       └── flowchart.md       # Browser automation & HITL flowchart
│
├── streamlit_app.py           # Streamlit Frontend UI
└── pyproject.toml             # Project dependency configurations
```

---

## 🤖 Subagent Responsibilities & Deliverables

### 1. [Coordinator Agent](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/app/agent.py)
- **Role**: Parent coordinator and orchestrator. Handles user interaction, off-topic pre-flight checks, and delegates subagent calls.

### 2. [Resume Agent](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/app/resume_agent)
- **Role**: Parses resumes, scores ATS alignment, and tailor-optimizes bullet points.

### 3. [Job Intelligence Agent](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/app/job_intelligence_agent)
- **Role**: Discovers jobs, scores candidate-to-job match, and dispatches SMTP updates.

### 4. [Application Agent](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/app/application_agent)
- **Role**: Automates form submissions (starting with LinkedIn Easy Apply) via a background Playwright worker.

---

## ⚙️ Proposed Changes

### [job-alert-agent](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent)

- **Create folder structures**: Create subagent directories inside `app/`: `app/resume_agent/`, `app/job_intelligence_agent/`, and `app/application_agent/`.
- **Relocate files**: Relocate tools and agents. Remove duplication between parent and subfolders.
- **Shared Modules**: Place `database.py` inside `app/` since database operations are common to both the Application Agent (writes status/prompts) and Coordinator Agent / Streamlit (reads/polls status).

---

## ❓ Open Questions for User Review

> [!IMPORTANT]
> Please review the following structural configurations:
> 1. **Common Database**: We will implement `database.py` directly in `app/` so it is shared, rather than duplicating database logic across subagents. Is this aligned with your instructions?
> 2. **Imports**: Subagents will be imported as `from app.job_intelligence_agent.agent import job_intelligence_agent`. This keeps Hatch packaging intact. Is this correct?



