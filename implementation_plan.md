# NextRole.Ai Master Implementation & Project Plan

This document consolidates the project plan, agent folder structure reorganizations, architectural specifications, and system configurations into a single, comprehensive master plan.

---

## 1. Project Overview & Scope

NextRole.Ai is a local prototype of an autonomous resume builder, match optimizer, job application agent, and email alert system. It is built using:
*   **Hierarchical Agent Architecture**: Powered by the **Google Agent Development Kit (ADK)**.
*   **Frontend**: A modern React Single Page Application (SPA) dashboard.
*   **Browser Automation**: **Playwright** for background scrapers and form fillers.
*   **Filing Cabinet**: Local **SQLite state store** (`job_applications.db`) and `.env` credentials persistence.
*   **SMTP Alert System**: **smtplib** for email summaries of target job alerts.

### The Core Agent Workflow:
1.  **Intake**: The candidate uploads a resume PDF and configures preferences.
2.  **ATS Scoring**: The system extracts profile node properties and grades baseline ATS readiness.
3.  **Improvements**: The AI suggests bullet tailoring and calculates projected match index adjustments.
4.  **Job Discovery**: The system scrapes matching job posts, evaluates compatibility, and identifies missing skills/keywords (Keyword Gap Analysis).
5.  **Auto-Apply**: The user triggers bulk applications. The background worker logs in to LinkedIn and automates portal form submissions.
6.  **Human-in-the-Loop (HITL)**: If a CAPTCHA or 2FA checkpoint is encountered, the worker pauses, prompts the user via the React Agent Console, reads the submitted OTP response from SQLite, and resumes the application.
7.  **Alerts**: The system sends email digests listing top matching roles and application summaries.

---

## 2. Technology Stack & Dependencies

*   **Google ADK**: Agent definitions, hierarchical structures, tool calling, and state handoff.
*   **React (Vite/Tailwind)**: User dashboard, configuration locks, real-time log screens, and prompt boxes.
*   **Playwright**: Browser scraping, credential login, form inputs mapping, and PDF resume uploads.
*   **smtplib**: Automated email alerting.
*   **Local SQLite Storage**: Shared schema containing `applications`, `hitl_prompts`, and execution logs to allow decoupled background execution.

---

## 3. Hierarchical Agent Specifications

NextRole.Ai uses a clean Coordinator-Worker pattern split into six dedicated agent entities:

### 1. Coordinator Agent (`root_agent`)
*   **Role**: Parent orchestrator, workflow router, and user dispatcher.
*   **Responsibilities**:
    *   Maintains end-to-end workflow execution state.
    *   Routes requests to the correct specialist sub-agents.
    *   Ensures configuration dependencies are satisfied (locking tabs until pre-requisites are met).
*   **Skills & Tools**: `route_workflow_step`, `validate_workflow_state`, `request_user_confirmation`, `write_status_update`, `log_audit_event`

### 2. Security Agent
*   **Role**: Validation gatekeeper and safety guardrail owner.
*   **Responsibilities**:
    *   Enforces target domain whitelisting (restricting browser navigation strictly to `linkedin.com` and `www.linkedin.com`).
    *   Sanitizes input parameters and enforces batch run bounds (1 to 20 applications max).
    *   Validates browser steps against a whitelist of approved interactive actions.
    *   Masks sensitive candidate PII from diagnostics logs.
*   **Skills & Tools**: `validate_domain`, `validate_inputs`, `validate_action`

### 3. Resume Agent
*   **Role**: Resume parser, profile builder, and ATS optimizer.
*   **Responsibilities**:
    *   Ingests PDF resumes and extracts raw profile data.
    *   Structures content into contact info, skills, experience, and education.
    *   Calculates ATS scores and provides metric-driven bullet improvement suggestions.
*   **Skills & Tools**: `parse_resume_file`, `extract_resume_text`, `score_resume_ats`, `suggest_resume_improvements`, `project_improved_ats_score`, `apply_approved_resume_changes`

### 4. Job Intelligence Agent / Job Alerts Agent
*   **Role**: Job search, score matching, gap analysis, and SMTP notification.
*   **Responsibilities**:
    *   Parses keywords and executes web searches via Playwright scrapers.
    *   Evaluates matching ratings by comparing candidate experience details with target description text.
    *   Ranks matches and identifies key missing skills/keywords.
    *   Compiles and emails HTML digest summaries via SMTP.
*   **Skills & Tools**: `validate_job_search_criteria`, `search_jobs_with_playwright`, `extract_job_posting_details`, `score_resume_to_job_match`, `extract_missing_skills_and_keywords`, `rank_job_matches`, `prepare_email_alert`, `send_email_with_smtplib`

### 5. Application Agent
*   **Role**: Browser automation specialist for Greenhouse and Lever forms.
*   **Responsibilities**:
    *   Spawns Playwright browser sessions for portal application pages.
    *   Maps candidate data to form textareas, dropdown fields, and checkbox inputs.
    *   Uploads resume PDF file attachments.
    *   Pauses on the final confirmation wizard view as a submission safety gate.
*   **Skills & Tools**: `open_application_with_playwright`, `detect_application_platform`, `fill_application_form`, `upload_resume_file`, `submit_or_pause_before_submit`

### 6. LinkedIn Form Filler / Easy Apply Agent
*   **Role**: Special worker for LinkedIn credentials, cookies, and Easy Apply forms.
*   **Responsibilities**:
    *   Logs in, saves session state cookies, and handles authenticated browser worker context.
    *   Fills out multi-page LinkedIn Easy Apply dialog options.
    *   Intercepts 2FA OTP security checkpoints, prompts the dashboard, pauses, and resumes when the code is supplied.
*   **Skills & Tools**: `login_to_linkedin`, `detect_2fa_checkpoint`, `fill_easy_apply_modal`, `poll_otp_from_sqlite`, `resume_after_2fa`

---

## 4. Proposed Folder Structure

```
job-alert-agent/
├── app/                       # Parent Package Directory
│   ├── agent.py               # Coordinator Agent (Parent Orchestration)
│   ├── tools.py               # Shared coordinator-level helpers
│   ├── database.py            # SQLite database schema operations
│   ├── app_utils/             # Shared utilities (logging, typing)
│   │
│   ├── security_agent/        # Security Sub-Agent
│   │   ├── agent.py
│   │   └── tools.py
│   │
│   ├── resume_agent/          # Resume Parser & Scorer Sub-Agent
│   │   ├── agent.py
│   │   └── tools.py
│   │
│   ├── job_intelligence_agent/ # Job Discovery & Scout Sub-Agent
│   │   ├── agent.py
│   │   └── tools.py
│   │
│   └── application_agent/     # Portal Application Sub-Agent
│       ├── agent.py
│       └── tools.py
│
├── easy_agent/                # Easy Apply Sub-Agent
│   ├── agent.py
│   └── login_worker.py        # Background Playwright worker subprocess
│
├── frontend/                  # React Frontend App
└── pyproject.toml             # Python Hatch dependencies configurations
```

---

## 5. Open Architecture Questions

1.  **Shared Database Operations**: We route database schema definitions and writes through `app/database.py` rather than duplicating connection hooks in each sub-agent directory.
2.  **Hatch Packager Imports**: We import sub-agents relative to the package root (e.g. `from app.security_agent.agent import security_agent`), ensuring packaging is preserved.
