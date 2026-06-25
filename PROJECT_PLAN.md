# Project Plan: Resume Builder, Optimizer, Job Application Agent, and Email Alert System

## Overview

Create a local prototype of a resume builder, optimizer, job application agent, and email alert system using a **mixed hierarchical agent architecture** built on the **Google Agent Development Kit (ADK)**, **Streamlit** for the frontend, **Playwright** for browser automation, and **smtplib** for email notifications.

The system keeps the current resume-to-job workflow:

1. The user uploads a resume and enters a LinkedIn profile link.
2. The system scores the current resume for ATS readiness.
3. The system suggests resume changes that can improve the score.
4. If the user chooses to implement the changes, the system shows the projected improved ATS score.
5. After the user approves or skips changes, the user enters the type of job they want, when the job was posted, and where the job is located.
6. The system searches the internet for matching job postings.
7. The system generates a match percentage between the resume and each job posting.
8. The system shows missing skills and keywords for each job posting.
9. The user chooses whether automatic applications are allowed above a user-defined match threshold.
10. The system applies to qualifying jobs when permitted.
11. The system lists lower-match jobs that did not meet the threshold.
12. The system prompts the user to confirm whether they have experience with missing skills.
13. If the user has relevant experience, the user writes short experience notes.
14. The system updates the resume only with confirmed experience and generates a new match rating.
15. If the new match rating satisfies the original threshold, the system applies automatically.
16. The system can send email alerts with job matches, application results, and follow-up items.

## Architecture Goal

Use the least number of agents that still keeps responsibilities clean and auditable.

The MVP architecture uses four agents total:

1. **Coordinator Agent**: parent agent and workflow controller.
2. **Resume Agent**: resume builder, parser, ATS optimizer, and resume version manager.
3. **Job Intelligence Agent**: job search, job matching, missing skill analysis, and email alert preparation.
4. **Application Agent**: browser automation, application submission workflow, human-in-the-loop prompts, and application logging.

This is a mixed hierarchy because the Coordinator Agent owns the workflow and delegates to specialist agents, while each specialist agent has multiple skills/tools it can use directly.

## Technology Stack

- **Google ADK**: agent definitions, parent/sub-agent hierarchy, tool calling, state handoff, and evaluation hooks.
- **Streamlit**: local frontend for resume upload, workflow review, approvals, threshold settings, and application status.
- **Playwright**: browser automation for job search, job page extraction, and supported application flows.
- **smtplib**: email notifications for job alerts, application summaries, and items needing user action.
- **Python document tooling**: PDF, DOCX, and TXT parsing plus resume export when implemented.
- **Local JSON or SQLite state**: MVP persistence for workflow state, resume versions, job postings, match results, and application logs.

## Agent Architecture

### 1. Coordinator Agent

Role: parent agent, workflow router, and guardrail owner.

Responsibilities:

- Own the end-to-end workflow state.
- Route work to the Resume Agent, Job Intelligence Agent, or Application Agent.
- Enforce the workflow order.
- Require user confirmation before:
  - applying resume changes
  - using LinkedIn data that requires authentication
  - enabling automatic applications
  - setting or changing the match threshold
  - adding missing skills to the resume
  - answering unknown application questions
  - submitting any final application when semi-automated safety mode is enabled
- Block off-topic requests unrelated to resume building, job search, job matching, or applications.
- Keep the user-facing Streamlit flow synchronized with backend state.

Skills/tools used by this agent:

- `route_workflow_step`
- `validate_workflow_state`
- `request_user_confirmation`
- `write_status_update`
- `log_audit_event`

### 2. Resume Agent

Role: resume builder, optimizer, ATS scorer, and resume version manager.

This agent combines the old Resume Intake, ATS Analyzer, and Resume Improvement responsibilities to reduce agent count.

Responsibilities:

- Accept resume uploads in PDF, DOCX, or TXT format.
- Extract raw resume text.
- Parse structured candidate data:
  - contact information
  - summary
  - skills
  - work experience
  - education
  - projects
  - certifications
- Accept and validate the LinkedIn profile link.
- Store LinkedIn as a reference unless the user provides accessible LinkedIn text, exported data, or explicit authenticated access.
- Generate a baseline ATS score.
- Suggest truthful resume improvements.
- Show projected ATS score if the user chooses to implement changes.
- Create improved resume versions after user approval.
- Update the resume only with user-confirmed missing-skill experience.
- Export resumes to DOCX or PDF when export support is implemented.

Skills/tools used by this agent:

- `parse_resume_file`
- `extract_resume_text`
- `validate_linkedin_url`
- `normalize_candidate_profile`
- `score_resume_ats`
- `suggest_resume_improvements`
- `project_improved_ats_score`
- `apply_approved_resume_changes`
- `update_resume_with_confirmed_experience`
- `export_resume_docx`
- `export_resume_pdf`

### 3. Job Intelligence Agent

Role: job discovery, job matching, missing skill analysis, and email alert preparation.

This agent combines the old Job Search, Match Analyzer, Lower-Match Review, and email-alert responsibilities to reduce agent count.

Responsibilities:

- Accept job search criteria:
  - target job type or role
  - posting date filter
  - job location
- Search the internet for job postings using Playwright-backed tools.
- Extract job details:
  - title
  - company
  - location
  - posting date
  - source URL
  - application URL
  - job description text
- Deduplicate jobs by company, title, location, and URL.
- Calculate match percentages between the approved resume and each job posting.
- Identify matched skills, missing skills, missing keywords, hard requirement gaps, and preferred qualification gaps.
- Rank jobs from highest to lowest match percentage.
- Split jobs into:
  - jobs above the user-defined threshold
  - jobs below the user-defined threshold
- Prepare lower-match review prompts for missing skills.
- Prepare email alerts for:
  - new matching jobs
  - jobs above threshold
  - jobs needing user input
  - application summary reports

Skills/tools used by this agent:

- `validate_job_search_criteria`
- `search_jobs_with_playwright`
- `extract_job_posting_details`
- `deduplicate_job_postings`
- `score_resume_to_job_match`
- `extract_missing_skills_and_keywords`
- `rank_job_matches`
- `build_lower_match_review`
- `prepare_email_alert`
- `send_email_with_smtplib`

### 4. Application Agent

Role: controlled browser automation for job applications.

Responsibilities:

- Apply only to jobs that meet or exceed the user-defined threshold.
- Use the latest approved resume version.
- Use Playwright to open application URLs and supported application flows.
- Support common flows where technically feasible:
  - LinkedIn Easy Apply
  - Greenhouse
  - Lever
  - Workday
- Upload the resume when required.
- Pause for human input on unknown fields.
- Respect semi-automated safety mode by pausing before final submission if enabled.
- Log each application outcome:
  - applied
  - skipped
  - failed
  - unsupported
  - needs user input
- Send application results back to the Coordinator Agent and Job Intelligence Agent.

Skills/tools used by this agent:

- `open_application_with_playwright`
- `detect_application_platform`
- `fill_application_form`
- `upload_resume_file`
- `pause_for_user_input`
- `submit_or_pause_before_submit`
- `log_application_result`
- `capture_application_screenshot`

## Streamlit Frontend Flow

Streamlit should expose a local step-by-step interface:

1. **Resume Intake**
   - upload resume
   - enter LinkedIn profile link
2. **ATS Score**
   - show baseline score
   - show score breakdown
3. **Resume Improvements**
   - show suggested changes
   - approve or skip changes
   - show projected improved score
4. **Job Search Criteria**
   - enter job type
   - choose posting date filter
   - enter location
5. **Job Matches**
   - show ranked job cards
   - show match percentages
   - show matched skills, missing skills, and missing keywords
6. **Auto-Apply Settings**
   - opt into or out of automatic applications
   - set minimum match threshold
   - review jobs above threshold
7. **Application Tracker**
   - show applied jobs
   - show failed jobs
   - show jobs needing user input
   - show unsupported jobs
8. **Lower-Match Review**
   - show jobs below threshold
   - ask whether the user has experience with missing skills
   - collect user-written experience notes
   - re-score affected jobs
9. **Email Alerts**
   - configure SMTP host, port, sender, recipient, and credentials
   - send job match alerts
   - send application summary emails
   - send user-action-needed emails

## Workflow State

Persist these records for the MVP:

- `candidate_profile`: parsed resume data and LinkedIn profile reference
- `resume_versions`: original, suggested, approved, job-specific, and missing-skill-updated resumes
- `ats_scores`: baseline score, projected score, and updated scores
- `job_search_criteria`: role, posting date filter, and location
- `job_postings`: discovered jobs and source metadata
- `match_results`: match percentage, matched skills, missing skills, missing keywords, and rationale
- `auto_apply_enabled`: explicit user opt-in for automatic applications
- `application_threshold`: user-defined minimum match percentage for auto-apply
- `application_log`: applied, skipped, failed, unsupported, and pending jobs
- `missing_skill_responses`: user-confirmed experience notes for lower-match jobs
- `email_alert_settings`: SMTP configuration and notification preferences
- `audit_log`: confirmation points, resume changes, and application actions

## Implementation Phases

### Phase 1: Local ADK and Streamlit Foundation

- **Status:** Complete for the local MVP foundation.
- Define the ADK parent Coordinator Agent and three specialist subagents.
- Define shared workflow state.
- Set up Streamlit as the local frontend.
- Add configuration for local state storage.
- Add safe environment configuration for API keys, SMTP settings, and browser automation options.

### Phase 2: Resume Builder and Optimizer

- **Status:** P0 complete for the local MVP. Deterministic local Resume Agent tools are implemented for upload extraction, parsing, LinkedIn validation, ATS scoring, suggestions, projected scoring, and approved version tracking. Resume export remains a later P2 enhancement.
- Build resume upload support for PDF, DOCX, and TXT.
- Parse resume content into structured candidate data.
- Add LinkedIn profile link validation.
- Generate baseline ATS score.
- Suggest resume improvements.
- Generate projected ATS score.
- Apply approved resume changes.
- Track resume versions.

### Phase 3: Job Search, Matching, and Email Alerts

- **Status:** Complete for the local MVP. Criteria validation, Playwright-backed job search, pasted job normalization, deduplication, weighted match scoring, missing skill extraction, ranking, Streamlit job match display, SMTP settings, email payloads, and SMTP test sending are implemented. Match scoring considers skills/keywords, role alignment, experience signals, and education signals.
- Build job search criteria inputs.
- Use Playwright to search and extract job postings.
- Normalize and deduplicate job results.
- Score resume-to-job matches.
- Extract missing skills and keywords.
- Rank jobs.
- Build email alert payloads.
- Send notifications with `smtplib`.

### Phase 4: Controlled Job Application Automation

- **Status:** P0 complete for the local MVP. Auto-apply opt-in, threshold persistence, above/below-threshold review, platform detection, safe Playwright application opening, approved-resume upload handling, human-in-the-loop pausing, and application outcome logging are implemented. The visual tracker remains a P1 page enhancement.
- Implement Playwright application automation.
- Detect common application platforms.
- Upload approved resume versions.
- Pause for unknown application questions.
- Respect threshold-based auto-apply settings.
- Log application outcomes.

### Phase 5: Lower-Match Review and Re-Match

- **Status:** P0 complete for the local MVP. Lower-match review prompts, confirmed missing-skill experience capture, truthful resume update, affected-job re-scoring, and newly qualified handoff metadata are implemented.
- List jobs below the user-defined threshold.
- Ask whether the user has experience with missing skills.
- Collect supporting experience notes.
- Update the resume only with confirmed experience.
- Re-score affected jobs.
- Send newly qualified jobs to the Application Agent if they meet the original threshold.

### Phase 6: MVP Verification

- Test resume parsing for PDF, DOCX, and TXT.
- Test LinkedIn link validation.
- Test ATS scoring and resume improvement flow.
- Test job search criteria handling.
- Test Playwright job extraction and deduplication.
- Test match scoring and missing skill extraction.
- Test threshold filtering.
- Test application logging.
- Test email notification sending through SMTP.
- Test lower-match review and re-match.

## Safety Rules

- Agents must not fabricate skills, credentials, employment history, education, certifications, or project experience.
- Resume updates must be based on existing resume facts or user-confirmed experience.
- Automated applications require explicit user opt-in and a user-defined threshold.
- The system must keep an audit log of resume changes and application activity.
- Job search results must include source URLs whenever available.
- Browser automation must respect site terms, authentication requirements, rate limits, and user privacy.
- Jobs below the threshold must not be applied to unless re-scoring after user-confirmed resume updates meets the original threshold.
- ATS scores and match percentages are decision-support signals, not guarantees.
- SMTP credentials must not be committed to the repo.

## Task Checklist

### Architecture and State

- [x] Define Coordinator Agent.
- [x] Define Resume Agent.
- [x] Define Job Intelligence Agent.
- [x] Define Application Agent.
- [x] Define shared workflow state.
- [x] Add audit logging.

### Streamlit Frontend

- [x] Build Resume Intake page.
- [x] Build ATS Score page.
- [x] Build Resume Improvements page.
- [x] Build Job Search Criteria page.
- [x] Build Job Matches page.
- [x] Build Auto-Apply Settings page.
- [x] Build Application Tracker page.
- [x] Build Lower-Match Review page.
- [x] Build Email Alerts settings page.

### Resume Agent Skills

- [x] Implement resume parsing.
- [x] Implement LinkedIn URL validation.
- [x] Implement ATS scoring.
- [x] Implement resume improvement suggestions.
- [x] Implement projected ATS scoring.
- [x] Implement approved resume updates.
- [x] Implement missing-skill resume updates.
- [ ] Implement resume export when needed.

### Job Intelligence Agent Skills

- [x] Implement job search criteria validation.
- [x] Implement Playwright job search.
- [x] Implement job detail extraction.
- [x] Implement job deduplication.
- [x] Implement match scoring.
- [x] Implement missing skills and keywords extraction.
- [x] Implement lower-match review payloads.
- [x] Implement SMTP email alerts.

### Application Agent Skills

- [x] Implement auto-apply threshold controls.
- [x] Implement Playwright application opening.
- [x] Implement application platform detection.
- [ ] Implement form filling.
- [x] Implement resume upload.
- [x] Implement unknown-question pause.
- [x] Implement submit or pause-before-submit behavior.
- [x] Implement application result logging.

## Verification Plan

### Code Correctness Tests

- Resume file parsing returns expected data structures.
- LinkedIn URL validation accepts and rejects expected inputs.
- Job posting deduplication is deterministic.
- Match scoring returns structured output.
- Application logging records every supported status.
- SMTP email payload generation does not expose secrets.

### Agent Behavior Evaluations

- The Coordinator routes each workflow step to the correct specialist agent.
- Resume Agent does not fabricate experience.
- Job Intelligence Agent separates matched and missing skills.
- Application Agent does not apply below the threshold.
- Application Agent pauses for unknown questions.
- The system updates resumes only from user-confirmed missing-skill experience.

### Manual MVP Verification

- Upload a resume and enter a LinkedIn profile link.
- Confirm baseline ATS scoring works.
- Approve resume changes and verify projected scoring.
- Search for jobs by role, posting date, and location.
- Confirm ranked job matches show missing skills and keywords.
- Configure email alerts and send a test email.
- Set an auto-apply threshold.
- Confirm only qualifying jobs are sent to the Application Agent.
- Confirm lower-match jobs can be reviewed and re-scored.
