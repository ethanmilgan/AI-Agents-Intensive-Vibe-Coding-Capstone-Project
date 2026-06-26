# Implementation Plan: Resume to Job Application Agent System

Create a local prototype of a resume builder, optimizer, job application agent, and email alert system using a **mixed hierarchical agent architecture** built on the **Google Agent Development Kit (ADK)**, **Streamlit** (frontend), **Playwright** (browser automation), and **smtplib** (email notifications).

This plan merges the existing Job Alert agent configurations with the general architecture, Streamlit flows, and safety constraints specified in `PROJECT_PLAN.md`.

---

## Hierarchical Multi-Agent Architecture

The architecture uses a parent Coordinator Agent and three specialized subagents to keep responsibilities clean and auditable:

1. **Coordinator Agent** (Parent Agent & Workflow Controller):
   - Entry point and guardrail owner.
   - Supervises and routes workflow tasks to the Resume Agent, Job Alerts / Job Intelligence Agent, or Application Agent.
   - Performs LLM Pre-flight Gatekeeper checks to identify and reject off-topic questions.
   - Requires user confirmation before applying resume changes, using authenticated LinkedIn data, enabling automatic applications, setting the match threshold, adding missing skills, answering unknown application questions, or submitting a final application.
   - Keeps the user-facing Streamlit flow synchronized with backend state.

2. **Resume Agent** (Subagent 1 - Builder & Optimizer):
   - Combines resume builder, parser, ATS analyzer, and resume version manager.
   - Accepts resume uploads (PDF, DOCX, TXT) and extracts raw text.
   - Parses structured candidate profile data (contact, summary, skills, experience, education, projects, certifications).
   - Validates LinkedIn profile links and stores LinkedIn details as references.
   - **Template-Based Resume Formatting**: Generates resumes by referencing a folder of shared **HTML templates** provided during build.
   - Generates baseline and projected ATS readiness scores, suggest truthful improvements, and refines resume bullets with user approval.
   - Updates the resume only with user-confirmed missing-skill experience.
   - Exports finalized resumes to DOCX (`python-docx`) and PDF (HTML-to-PDF via Playwright).

3. **Job Alerts / Job Intelligence Agent** (Subagent 2 - Discovery & Match Analyzer):
   - **LinkedIn Daily & On-Demand Scraper**: Scrapes LinkedIn daily (24-hour filter) or on-demand using Playwright.
   - **Manual Authentication**: If login session cookies are invalid or missing, Playwright opens a non-headless browser window for the user to complete the manual authentication/login step.
   - **Job Matching & Deduplication**: Extracts job details, deduplicates jobs, and calculates weighted match percentages using fixed weight criteria (LLM estimates these values based on candidate fit):
     - **Skills**: 40%
     - **Experience**: 25%
     - **Role Alignment**: 20%
     - **Education**: 10%
     - **Keywords**: 5%
   - **Gaps & Ranking**: Identifies matched/missing skills and keywords. Ranks postings and splits them into above-threshold and below-threshold.
   - **Alerts & Review**: Prepares lower-match review prompts for missing skills and compiles styled HTML email payloads for new matching jobs, jobs above threshold, action-needed alerts, and application summaries. Sends notifications via SMTP.
   - **SMTP Simplification**: Pre-fills/mocks SMTP details in the background for ease of use, with an "Advanced Settings" accordion in the UI for credential overrides.

4. **Application Agent** (Subagent 3 - Browser Automation):
   - Opens application URLs using Playwright context.
   - **Heuristic Form Filler**:
     - Performs automated form filling by detecting common HTML input elements (`text`, `email`, `phone`, `textarea`, `select`, `radio`, `checkbox`, `file upload`) using labels, placeholders, aria-labels, and surrounding/nearby text.
     - Automatically fills out detected fields based on the candidate profile.
     - Pauses before clicking the final "Submit" button to allow review.
     - Supports **multi-page wizard navigation** (fills current form page, clicks "Next", waits for reload, and repeats).
     - Targets supported portals for the MVP: **Greenhouse**, **Lever**, **Wellfound**, and **LinkedIn** (Easy Apply).
   - **Heuristic Resume Upload Strategy**:
     - Searches for common upload labels or visible text (e.g., "Upload Resume", "Upload CV", "Attach Resume", "Choose File").
     - Locates the associated `<input type="file">` element (including hidden inputs referenced by labels or nearby container elements).
     - Sets the PDF resume file directly on the input.
     - If no file input is found, clicks the upload control to expose the file input, then retries setting the file.
   - **SQLite Polling Human-in-the-Loop (HITL) & CAPTCHA**:
     - **Decoupled Playwright Worker Process**: To avoid Streamlit event loop conflicts, the Playwright automation runs in a separate background worker process. Streamlit triggers it via a subprocess and monitors progress.
     - **CAPTCHA & Forms Interruption**: If a CAPTCHA gate is encountered or an unknown application question arises, the worker writes the status update to a shared SQLite database (e.g., `Waiting for User Input` or `CAPTCHA Encountered`), pauses itself, and waits in a check-loop.
     - **Manual Resolution**: The user solves the CAPTCHA manually in the open non-headless browser window or submits answers to Streamlit.
     - Once answered/resolved, Streamlit writes answers back to the SQLite store (or updates status to `resolved`). The worker detects the status change from SQLite, reads answers if applicable, and resumes form filling.
     - **Status Reporting**: Reports status updates (`Queued`, `Running`, `Waiting for User Input`, `CAPTCHA Encountered`, `Completed`, `Failed`) to SQLite for Streamlit polling.
   - **Safety Submission Gate**: Respects semi-automated safety mode by pausing before the final "Submit" button.

---

## Workflow State & Persistence

- **Session-Limited Storage**: All persistent states (parsed candidate profiles, resume versions, matched jobs, and application logs) are stored temporarily in a session database. The system remembers these records only for the duration of the active Streamlit session (they do not persist across session resets/refreshes).
- **SQLite Database**: Used to persist workflow state and manage the HITL/Worker status polling mechanism.

---

## Streamlit Frontend Flow

The Streamlit interface exposes a local step-by-step workflow:

1. **Resume Intake**: Upload current resume (PDF, DOCX, TXT) and enter LinkedIn profile link.
2. **ATS Score**: View baseline ATS score and detailed category score breakdown.
3. **Resume Improvements**: View suggested modifications, approve or skip changes, and see the projected improved score.
4. **Job Search Criteria**: Input target job type/keywords, posting date filters, and location.
5. **Job Matches**: Display ranked job cards with match percentages, matched/missing skills, and missing keywords.
6. **Auto-Apply Settings**: Opt into/out of automatic applications, set the minimum match threshold, and review jobs above the threshold.
7. **Application Tracker**: Monitor applied, failed, unsupported, and pending applications. Polls SQLite to display live worker states and alerts (like CAPTCHA notices or pending questions).
8. **Lower-Match Review**: Review jobs below the threshold, query user experience on missing skills, collect experience notes, and re-score affected jobs.
9. **Email Alerts**: Configure SMTP settings (host, port, sender, recipient, password accordion) and trigger manual or summary email alerts.

---

## Proposed Changes

### [job-alert-agent](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent)

#### [MODIFY] [app/agent.py](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/app/agent.py)
- Consolidate multi-agent definition registry to 4 clean hierarchical agents: `coordinator_agent`, `resume_agent`, `job_alerts_agent`, and `application_agent`.

#### [MODIFY] [app/tools.py](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/app/tools.py)
- Group, refactor, and register tools without duplicates:
  - **Coordinator**: `route_workflow_step`, `validate_workflow_state`, `request_user_confirmation`, `write_status_update`, `log_audit_event`.
  - **Resume**: `parse_resume_file`, `extract_resume_text`, `validate_linkedin_url`, `normalize_candidate_profile`, `score_resume_ats`, `suggest_resume_improvements`, `project_improved_ats_score`, `apply_approved_resume_changes`, `update_resume_with_confirmed_experience`, `export_resume_docx`, `export_resume_pdf`.
  - **Job Intelligence**: `validate_job_search_criteria`, `search_jobs_with_playwright`, `extract_job_posting_details`, `deduplicate_job_postings`, `score_resume_to_job_match`, `extract_missing_skills_and_keywords`, `rank_job_matches`, `build_lower_match_review`, `prepare_email_alert`, `send_email_with_smtplib`.
  - **Application**: `open_application_with_playwright`, `detect_application_platform`, `fill_application_form`, `upload_resume_file`, `pause_for_user_input`, `submit_or_pause_before_submit`, `log_application_result`, `capture_application_screenshot`.

#### [MODIFY] [streamlit_app.py](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/job-alert-agent/streamlit_app.py)
- Modify Streamlit tabs and page rendering to follow the 9-step flow outlined in the frontend flow specification.

#### [MODIFY] [.agents-cli-spec.md](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/.agents-cli-spec.md)
- Update the system specifications with the updated agent definitions, use cases, and safety rules.

---

## Safety Rules & Guardrails

- **Gatekeeper Guardrail**: The Coordinator blocks any non-career/off-topic queries immediately.
- **Truthfulness Guardrail**: Agents must strictly stick to existing candidate resume facts. No fabrication of skills, credentials, employment history, education, certifications, or project experience is allowed.
- **Semi-Automated Constraint**: The Application Agent MUST NOT submit the final form. It must pause before the final "Submit" button.
- **Opt-In Requirement**: Automated applications require explicit user opt-in and a user-defined threshold.
- **Audit Logging**: The system must keep an audit log of all resume changes, confirmation points, and application activities.
- **Source Integrity**: Job search results must include source URLs whenever available.
- **Browser Automation Compliance**: Browser automation must respect site terms, authentication requirements, rate limits, and user privacy.
- **Threshold Integrity**: Jobs below the threshold must not be applied to unless re-scoring after user-confirmed resume updates meets the original threshold.
- **Information Disclosure**: ATS scores and match percentages are decision-support signals, not guarantees.
- **Security**: SMTP credentials must not be committed to the repository and must be loaded via local environment variables.

---

## Verification Plan

### Automated Tests
- Run Pytest Unit framework:
  ```bash
  uv run pytest tests/unit/
  ```
- Run ADK UAT evaluation dataset:
  ```bash
  agents-cli eval run --dataset tests/eval/datasets/uat-dataset.jsonl
  ```

### Manual Verification
- Start the Streamlit application:
  ```bash
  uv run streamlit run streamlit_app.py --server.port 8501
  ```
- Step through the 9-step wizard tabs:
  1. Intake resume and validate empty input fields with placeholders.
  2. Verify ATS baseline scoring card.
  3. Verify resume tailoring proposals.
  4. Perform LinkedIn/Web job search and verify ranked matches.
  5. Test auto-apply settings and thresholds.
  6. Confirm Playwright logs into forms, uploads PDFs, prompts on unknown fields, and gates the submit button.
  7. Check lower-match experience re-scoring and follow-up updates.
  8. Trigger manual SMTP email alert and verify inbox.
