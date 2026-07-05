# React Frontend Specification: NextRole.Ai

This document outlines the layout, user controls, outputs, and interactive features of the **NextRole.Ai** React-based Single Page Application (SPA) dashboard. 

---

## 🧭 Global Layout & Navigation

The interface features a responsive left sidebar navigation menu with the following tabs:
1.  **Dashboard** (Analytics and quick status)
2.  **Configuration** (Resume intake, search settings, and LinkedIn credentials)
3.  **Job Discovery** (Scouted jobs table, match scores, and details slides)
4.  **Agent Console** (Playwright worker monitor and HITL 2FA input console)
5.  **ATS Optimizer** (Cover letters, outreach notes, and bullet points generator)

> [!IMPORTANT]
> **Secure Navigation Gate**: The Job Discovery, Agent Console, and ATS Optimizer tabs remain **locked and disabled** (displaying a lock icon) until the candidate completes the Configuration workspace by uploading a resume, setting preferences, and successfully authenticating with LinkedIn.

---

## 📊 Tab 1: Dashboard (Overview & Analytics)
Provides a high-level summary of your job search progress, key metrics, and action items.

### 📥 Inputs
*   *None* (Purely informational/routing view).

### 📤 Outputs
*   **Key Metrics Row (Cards)**:
    *   **Total Jobs Discovered**: Number of listings scraped.
    *   **Applications Sent**: Count of automated submissions.
    *   **Average ATS Match**: The mean match score across target roles.
    *   **Verification Alerts**: Displays count of active Human-in-the-Loop prompts (e.g., *"1 Action Required"*).
*   **Recent Activity Feed**: List of recent background worker steps and logged application updates.

---

## ⚙️ Tab 2: Configuration (Ingestion & Connection Gate)
The setup hub where the candidate profile, credentials, and constraints are established.

### 📥 Inputs
*   **Resume PDF Uploader**: Drag-and-drop file uploader (accepts `.pdf` files).
*   **Job Preferences Fields**:
    *   *Search Keywords*: Comma-separated list or tags (e.g., `"Python Developer, Data Engineer"`).
    *   *Target Location*: Preferred search locations (e.g., `"San Francisco, CA"`).
*   **LinkedIn Login Form**:
    *   *Username*: Field pre-filled from local `.env` or manual entry.
    *   *Password*: Field pre-filled from local `.env` or manual entry.

### 📤 Outputs
*   **Profile Parsing Preview**: Renders structured candidate text (Experience, Skills, Education) upon PDF parsing.
*   **LinkedIn Connection Status Card**: Displays connection status (*Disconnected*, *Connecting...*, *Connected*).

### ⚡ Interactive Features
*   **"Save Configuration" Button**: Saves settings and parses the candidate profile.
*   **"Connect LinkedIn" Button**: Triggers the background FastAPI worker to initialize chromium and log in.

---

## 🔍 Tab 3: Job Discovery (Match Evaluation & Search)
Displays compatible jobs found by the scraper, matched directly against the parsed resume profile.

### 📥 Inputs
*   **Job Selection Checkboxes**: Allows selecting individual rows to target for bulk applications.
*   **Search Bar / Filters**: Input fields to filter results by title or keyword.

### 📤 Outputs
*   **Scouted Jobs Grid**:
    *   Displays Company, Role Title, Location, and Post Date.
    *   **Match Fit Badge**: Color-coded percentage index showing compatibility (e.g., `92% Fit` [Green], `55% Fit` [Red]).
*   **Details Sidepanel (Slideout)**:
    *   Displays full scraped job description.
    *   Lists **Matched Keywords** vs. **Missing Keywords** (Keyword Gap Analysis).
    *   Highlights mismatched requirements (years of experience, qualifications).

### ⚡ Interactive Features
*   **"Run Search" Button**: Dispatches the Job Intelligence Agent scraper.
*   **"View Details" Link/Button**: Slides open the details sidepanel.
*   **"Bulk Apply" Button**: Enqueues selected jobs for automated browser submissions.

---

## 🤖 Tab 4: Agent Console (Playwright Worker & 2FA Resolver)
Provides real-time visibility into browser automation runs and handles security prompts.

### 📥 Inputs
*   **HITL Verification Input**: OTP/2FA code entry box (visible only when worker status is *Paused for Verification*).

### 📤 Outputs
*   **Worker State Badge**: Displays *Idle*, *Running*, *Paused for Verification*, or *Completed*.
*   **Real-time Process Logs Console**: Monospaced terminal container streaming Playwright subprocess events (e.g., `"[INFO] Entering credential fields..."`, `"[WARNING] 2FA required by target platform"`).
*   **Screenshot Preview**: Embedded window showing a captured image of the current browser state.

### ⚡ Interactive Features
*   **"Submit 2FA Code" Button**: Writes the user's OTP response to the SQLite database and resumes the browser worker.
*   **"Terminate Task" Button**: Halts current background processes.

---

## ✨ Tab 5: ATS Optimizer (Asset Tailoring Suite)
AI assistant that builds tailored application artifacts dynamically.

### 📥 Inputs
*   **Job Profile Selector**: Dropdown to select a specific scraped job from the SQLite database history.

### 📤 Outputs
*   **Tailored Document Workspaces**:
    *   **Cover Letter Tab**: Drafts an introductory letter matching resume qualifications to the job details.
    *   **Recruiter Outreach Tab**: Drafts a 300-character LinkedIn request or follow-up note.
    *   **Resume Bullet Optimizer Tab**: Displays your bullet points with recommended improvements (e.g., adding metrics, aligning action verbs).

### ⚡ Interactive Features
*   **"Generate tailored assets" Button**: Prompts the Gemini model to write custom documents.
*   **"Copy to Clipboard" Buttons**: Instantly copies cover letters or outreach drafts.
