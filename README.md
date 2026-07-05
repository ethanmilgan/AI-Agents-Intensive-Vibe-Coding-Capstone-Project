# NextRole.Ai: Autonomous Career & Job Application Agent

**NextRole.Ai** is an AI-powered, multi-agent copilot designed to automate your job application lifecycle. By combining a modern React dashboard, a FastAPI orchestrator, and an autonomous Playwright browser automation engine, NextRole.Ai scouts job listings, evaluates resume ATS match rates, and automatically fills out job applications while allowing you to handle 2FA checkpoints in real-time.

---

## 🚀 Key Features

* **💼 Dynamic Sidebar Navigation**: Uses a secure configuration gate. Advanced features (Job Discovery, Agent Console, ATS Optimizer) remain locked and disabled until your candidate profile is filled, settings are configured, and LinkedIn is connected.
* **📈 ATS Match Scorecard**: Automatically evaluates your resume's compatibility against role details in real-time (ranging from $45\%$ to $96\%$), highlighting key missing keywords.
* **🤖 Background Browser Robot**: Detaches Playwright browser instances headlessly to navigate login screens and multi-step portal forms (Greenhouse, Lever, LinkedIn).
* **💬 Human-in-the-Loop (HITL) 2FA**: If LinkedIn prompts for a 2-step verification PIN or OTP code, the background worker pauses, prompts you directly in the web UI console, and resumes automation instantly upon input.
* **✨ ATS Asset Optimizer**: Automatically generates professional cover letters, LinkedIn recruiter outreach drafts, and suggestions to optimize resume experience bullets with metrics.
* **🔒 Built-in Guardrails**: Integrated Security Agent checks target domains and sanitizes form inputs before dispatching the Playwright robot.

---

## 📂 Project Structure

```bash
├── frontend/                     # React web dashboard (Vite, Tailwind, Lucide Icons)
│   ├── src/                      # UI Components (Dashboard, Console, Settings, Optimizer)
│   └── dist/                     # Compiled production assets served by FastAPI
├── job-alert-agent/              # FastAPI Backend & Agent Orchestration layer
│   ├── app/
│   │   ├── agent.py              # Root Coordinator Agent and sub-agent hierarchies
│   │   ├── fast_api_app.py       # REST API endpoints & static assets routing
│   │   ├── database.py           # SQLite db layer (applications, hitl_prompts, logs)
│   │   └── easy_agent/           # LinkedIn Form-Filling loop & Playwright workers
│   └── adk_agents/               # Environment credentials (.env) & session cookies
└── README.md                     # This file
```

---

## ⚙️ Getting Started & Setup

### Prerequisites
* Python 3.10+
* Node.js & npm
* Git

### 1. Configure the Backend Server
Navigate into the backend project, initialize the Python environment, and install dependencies:
```bash
cd job-alert-agent
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Configure your credentials inside `job-alert-agent/adk_agents/.env`:
```env
LINKEDIN_USERNAME=your-email@example.com
LINKEDIN_PASSWORD=your-password
GEMINI_API_KEY=your-api-key
```

### 2. Build the Frontend App
Navigate into the frontend folder, install packages, and compile the production build:
```bash
cd ../frontend
npm install
npm run build
```
Vite will compile the code and copy the static build index to `frontend/dist`, which the FastAPI app mounts and serves directly on root load.

### 3. Launch the Application
Run the FastAPI backend server (which will host both the API and the React web dashboard):
```bash
cd ../job-alert-agent
uv run python -m app.fast_api_app
```

Now, open your browser and navigate to **`http://localhost:8000`** to access NextRole.Ai!

---

## 🛠️ System Architecture

NextRole.Ai uses a decoupled multi-agent architecture to ensure the asynchronous browser robot doesn't lock the web interface event loop:

1. **User Action**: The React dashboard triggers commands via REST APIs.
2. **AI Delegation**: The FastAPI orchestrator routes the task through the **Coordinator Agent**, validating safety parameters using the **Security Agent**.
3. **Background Worker**: The backend launches the Playwright worker thread.
4. **State Syncing**: The background browser and web dashboard synchronize logs, application steps, and manual prompt answers using a shared **SQLite state store** (`job_applications.db`).
