# Streamlit Frontend Specification: Resume to Job Application Agent

This document outlines the layout, inputs, outputs, and interactive features of the Streamlit application interface. The application is structured as a multi-tab dashboard.

---

## 🗂️ Tab 1: Resume Workspace (Resume Ingestion & Creation)
Provides options to build a new resume, optimize an existing one, or import profile data.

### 📥 Inputs
*   **Resume Ingestion Mode Selector** (Radio/Toggle):
    *   *Manual Entry*
    *   *Upload Old Resume*
    *   *Upload Visual Style Template*
    *   *Paste LinkedIn Profile*
*   **Manual Entry Form Fields** (Visible only in *Manual Entry* mode):
    *   **Contact Info**: Name, Email, Phone, LinkedIn URL, Portfolio/Website.
    *   **Professional Summary**: Text area for objective or summary.
    *   **Work Experience Section**: Dynamically expandable fields for Company Name, Role, Start/End Dates, Location, and bullet points.
    *   **Education Section**: Dynamically expandable fields for Institution, Degree, Major, Graduation Date, and GPA.
    *   **Skills Section**: Text input for comma-separated technical and soft skills.
*   **File Uploader Widgets**:
    *   *Old Resume Uploader* (Accepts `.pdf`, `.docx` - visible in *Upload Old Resume* mode).
    *   *Style Example Uploader* (Accepts `.pdf`, `.docx`, `.html` - visible in *Upload Visual Style Template* mode).
    *   *LinkedIn Profile PDF Uploader* (Accepts `.pdf` - visible in *Paste LinkedIn Profile* mode).
*   **LinkedIn Text Area** (Visible in *Paste LinkedIn Profile* mode):
    *   Text box to paste copied text from a LinkedIn profile.

### 📤 Outputs
*   **Status Indicators**: Toast messages or alerts confirming parsing success (e.g., `"Resume successfully parsed!"` or `"Style template loaded."`).
*   **Structured Resume Preview**: A formatted preview (rendered Markdown) showing the parsed or input details.

### ⚡ Interactive Features
*   **"Save Resume" Button**: Saves the structured resume JSON data to the local workspace folder.
*   **Inline Resume Editor**: Lets the user manually edit any of the parsed details directly on screen before saving.

---

## 📊 Tab 2: Tailoring & ATS Score (Job Matching & Optimization)
Evaluates resume fit against target jobs and generates tailored application files.

### 📥 Inputs
*   **Target Job URL**: URL text input to scrape job description from direct ATS portals or LinkedIn.
*   **Target Job Description**: Text area for pasting description text (auto-filled if URL scrape succeeds).
*   **Resume Template Theme Selector**: Dropdown selector (*Modern*, *Minimalist*, *Creative*) to style the output PDF.

### 📤 Outputs
*   **ATS Scorecard**: A circular gauge chart or progress bar showing the match score (`0-100`).
*   **Gap Analysis Checklist**: Highlighting missing keywords, skills, and experience gaps.
*   **Tailored Document Tabs**:
    1.  *Tailored Resume Preview*: Displaying the modified bullet points side-by-side with original bullet points.
    2.  *Custom Cover Letter*: Fully drafted cover letter tailored to the job description.
    3.  *Recruiter Outreach Message*: Drafted LinkedIn connection request note or follow-up email.
    4.  *Screening Question Answers*: Dynamic drafts answering custom application questions.

### ⚡ Interactive Features
*   **"Analyze & Tailor" Button**: Triggers the ATS Analyzer and Resume Builder agents.
*   **"Download PDF" Button**: Generates and downloads the styled PDF resume via Playwright.
*   **"Download Docx" Button**: Generates and downloads the standard Microsoft Word resume via `python-docx`.
*   **"Copy to Clipboard" Buttons**: Individual copy buttons next to the Cover Letter, Outreach note, and answers.

---

## 🤖 Tab 3: Auto-Apply Tracker (Playwright Form Filling)
Controls and monitors the browser automation for job submissions.

### 📥 Inputs
*   **Target Application URL**: Input text field for the direct job apply form.
*   **Persistent Cookies Toggle**: Checkbox to enable or disable loading session state cookies from `playwright_session/`.

### 📤 Outputs
*   **Application Progress Bar**: Step indicators showing current automation phase.
*   **Real-time Process Logs**: Visual console logging current browser actions (e.g., `"[1/4] Greenhouse portal detected"`, `"[2/4] Uploading resume file..."`).
*   **Browser Status Badge**: Displays current state: *Idle*, *Running*, *Paused for HITL Review*, or *Submission Ready*.

### ⚡ Interactive Features
*   **"Start Auto-Apply" Button**: Spawns the headful Playwright browser to navigate, fill out the form, and upload the resume.

---

## 💬 Tab 4: Human-in-the-Loop Interaction (HITL Question Resolver)
Acts as the bridge when the automated browser encounters questions it cannot answer.

### 📥 Inputs
*   **Quick Answer Input**: Simple text field for the user to type a quick response or guidance (e.g., typing *"Yes, 3 years"*).

### 📤 Outputs
*   **HITL Active Alert**: A high-visibility banner (orange/red) that displays only when the browser is paused waiting for user input.
*   **Scraped Question Box**: Shows the exact question text identified on the application page.
*   **Polished Answer Preview**: Displays the final professional answer written by the Paraphrasing Agent before it is filled into the browser form.

### ⚡ Interactive Features
*   **"Submit Answer" Button**: Sends the polished answer to the Form Filler Agent, updates the shared JSON state file, and resumes Playwright.

---

## 📬 Tab 5: Job Alerts & SMTP Settings (Email Alerts)
Manages the configuration and execution of the 24-hour scraper and email alert delivery.

### 📥 Inputs
*   **Recipient Email Address**: The email where you want to receive the alerts.
*   **Search Job Titles**: Comma-separated list of target role names (e.g., "Python Developer, Data Engineer").
*   **Search Location**: Target city or country.
*   **Advanced Settings (Collapsible Accordion)**: Optional fields for custom SMTP Server, Port, Sender Email, and App Password (pre-configured/mocked with a dummy account for showcase).

### 📤 Outputs
*   **Alert Status**: Success/Error message when notifications are sent.
*   **Scraped Jobs List**: A table showing jobs found in the last 24 hours matching the criteria, complete with role title, company, links, and ATS fit scores.

### ⚡ Interactive Features
*   **"Trigger Daily Scrape & Alert" Button**: Runs Playwright to search LinkedIn and emails the results to your recipient email.
*   **"Save SMTP Settings" Button** (Inside Advanced Settings): Saves custom SMTP credentials if you choose to override the default/dummy sender.
*   **"Send Test Email" Button** (Inside Advanced Settings): Sends a quick test email to verify custom settings.

---

## 🕒 Tab 6: History Dashboard (Application Log)
Tracks past applications and logs.

### 📥 Inputs
*   **Status Update Selector**: Dropdown selector in each row of the table to manually adjust the job status (e.g., *Submitted*, *Interviewing*, *Offer Received*, *Rejected*).

### 📤 Outputs
*   **Key Metrics Summary Cards**: Cards displaying *Total Applied*, *Average ATS Score*, and *Active Interviews*.
*   **Logged Applications Table**: Read-only log showing: Date, Company, Role, Job URL, ATS Score, and Application Status (sourced from `applications_log.json`).

### ⚡ Interactive Features
*   **"Refresh Log" Button**: Reloads the local log file.
*   **"Export Log to CSV" Button**: Exports the history table as a CSV sheet.
