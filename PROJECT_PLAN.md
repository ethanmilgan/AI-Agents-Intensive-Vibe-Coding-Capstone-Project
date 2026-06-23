# Project Plan: Hierarchical Resume-to-Job Application Agent

## Overview

This project is a local prototype for a hierarchical multi-agent job search and application system. The application guides a user from resume intake through ATS scoring, resume improvement, job discovery, match scoring, threshold-based application automation, and follow-up resume refinement for lower-match jobs.

The intended interface is a user-facing app where the user uploads a resume, provides a LinkedIn profile link, reviews ATS feedback, chooses whether to implement suggested resume improvements, enters job search preferences, and controls when automated applications are allowed.

## Target Workflow

1. The user uploads their resume and enters their LinkedIn profile link.
2. The ATS Analyzer Agent scores the current resume.
3. The Resume Improvement Agent suggests changes that would improve the resume.
4. If the user chooses to implement the suggestions, the agent shows the projected improved ATS score.
5. After the user implements or approves the changes, the user enters:
   - type of job they are looking for
   - when the job was posted
   - job location
6. The Job Search Agent searches the internet for matching job postings.
7. The Match Analyzer Agent generates a match percentage between the resume and each job posting.
8. The Match Analyzer Agent lists missing skills and keywords for each job posting.
9. The user chooses whether to allow automatic applications for jobs above a user-defined match threshold.
10. The Application Agent applies to job postings that meet or exceed the threshold.
11. The Lower-Match Review Agent lists remaining jobs below the threshold.
12. The Lower-Match Review Agent shows missing skills and keywords for each lower-match job.
13. The user is prompted to confirm whether they have experience with the missing skills.
14. If the user has relevant experience, the user writes short experience notes for those skills.
15. The Resume Improvement Agent updates the resume with truthful skill evidence and generates a new match rating.
16. If the new match rating satisfies the original user-defined threshold, the Application Agent applies automatically.

## Hierarchical Multi-Agent Architecture

The system uses a parent Coordinator Agent that supervises specialist subagents. Each subagent has a narrow responsibility to reduce task overlap and keep the workflow auditable.

### 1. Coordinator Agent

Role: parent entrypoint, state manager, and guardrail.

Responsibilities:

- Orchestrates the full workflow from intake through applications.
- Routes work to the correct specialist subagent.
- Tracks the current resume version, ATS score, job search criteria, match threshold, and application status.
- Requires user confirmation before implementing resume changes or enabling automatic applications.
- Blocks off-topic requests that are unrelated to career search, resume improvement, or job applications.
- Enforces workflow order so users complete resume intake and scoring before job search and auto-apply.

### 2. Resume Intake Agent

Role: resume and LinkedIn profile ingestion.

Responsibilities:

- Accepts resume uploads in PDF, DOCX, or TXT format.
- Extracts structured resume data including education, experience, projects, skills, certifications, and contact details.
- Accepts and stores a LinkedIn profile link.
- Uses LinkedIn content only when the user provides accessible text, exported profile data, or explicit authenticated access.
- Produces a normalized candidate profile for downstream agents.

### 3. ATS Analyzer Agent

Role: baseline and projected ATS scoring.

Responsibilities:

- Scores the current resume using ATS-style criteria.
- Explains the score using concrete categories such as formatting, keyword coverage, role relevance, measurable impact, skills clarity, and experience alignment.
- Produces an initial score before any changes.
- Produces a projected improved score when suggested changes are selected.
- Does not claim that any score guarantees interview selection.

### 4. Resume Improvement Agent

Role: resume improvement and truthful tailoring.

Responsibilities:

- Suggests changes that improve ATS readability and role alignment.
- Rewrites bullets only from facts provided by the user.
- Adds missing skills only when the user confirms real experience and provides supporting details.
- Maintains version history between the original resume, suggested revision, approved revision, and job-specific revision.
- Exports improved resumes when document generation is implemented.

### 5. Job Search Agent

Role: internet job discovery.

Responsibilities:

- Searches for job postings based on the user's target job type, posting date filter, and location.
- Captures job title, company, location, posting date, source URL, description, and application URL when available.
- Deduplicates postings across sources.
- Flags postings that require external login, manual review, or unsupported application flows.

### 6. Match Analyzer Agent

Role: resume-to-job comparison.

Responsibilities:

- Calculates a match percentage for each job posting.
- Lists matched skills, missing skills, missing keywords, and experience gaps.
- Separates hard requirements from preferred qualifications when the job description supports it.
- Ranks postings by match percentage.
- Re-runs matching after resume updates.

### 7. Application Agent

Role: controlled application automation.

Responsibilities:

- Applies only to jobs that meet or exceed the user-defined match threshold.
- Requires explicit user opt-in before automatic applications are enabled.
- Uses the latest approved resume version.
- Handles supported application flows such as LinkedIn Easy Apply, Greenhouse, Lever, and Workday where technically feasible.
- Pauses for user input on unknown application questions.
- Logs every attempted, completed, skipped, and failed application.

### 8. Lower-Match Review Agent

Role: second-pass review of jobs below the threshold.

Responsibilities:

- Lists remaining jobs below the user-defined threshold.
- Shows why each job did not meet the threshold.
- Prompts the user to confirm whether they have experience with the missing skills.
- Collects user-written experience notes for confirmed skills.
- Sends confirmed information to the Resume Improvement Agent for truthful updates.

## User Confirmation Points

The system must stop and ask the user before:

- implementing suggested resume changes
- using LinkedIn data that requires authenticated access
- enabling automatic applications
- selecting or changing the match threshold
- applying to any job when the application flow includes unknown questions
- adding a missing skill to the resume
- submitting any final application if the implementation uses a semi-automated safety mode

## Data Model

The workflow should persist these core records:

- `candidate_profile`: parsed resume data and LinkedIn profile reference
- `resume_versions`: original, suggested, approved, and job-specific resumes
- `ats_scores`: baseline score, projected score, and final score after approved changes
- `job_search_criteria`: target job type, posting age/date, and location
- `job_postings`: discovered jobs and source metadata
- `match_results`: match percentage, matched skills, missing skills, missing keywords, and rationale
- `application_threshold`: user-defined minimum match percentage for auto-apply
- `application_log`: applied, skipped, failed, and pending jobs
- `missing_skill_responses`: user-confirmed experience notes for lower-match jobs

## Implementation Phases

### Phase 1: Workflow Foundation

- Define shared workflow state for resume, LinkedIn link, ATS scores, job criteria, matches, threshold, and applications.
- Implement Coordinator Agent routing for the full ordered workflow.
- Add guardrails that prevent off-topic requests and fabricated resume content.
- Add resume version tracking for original, suggested, approved, and job-specific resumes.
- Add application and resume-change audit logging.
- Add clear status values for each workflow step:
  - `resume_uploaded`
  - `baseline_scored`
  - `changes_suggested`
  - `changes_approved`
  - `search_criteria_entered`
  - `jobs_found`
  - `threshold_set`
  - `auto_apply_enabled`
  - `applications_processed`
  - `lower_match_review_started`
  - `resume_updated_from_missing_skills`

### Phase 2: Resume and LinkedIn Intake

- Build resume upload support for PDF, DOCX, and TXT.
- Extract raw resume text from uploaded files.
- Parse structured resume data:
  - contact information
  - summary
  - skills
  - work experience
  - education
  - projects
  - certifications
- Add LinkedIn profile link input and validation.
- Store LinkedIn as a profile reference unless the user provides accessible LinkedIn content or explicit authenticated access.

### Phase 3: Baseline ATS Scoring

- Implement ATS Analyzer Agent scoring for the current resume.
- Add ATS score categories for:
  - formatting
  - completeness
  - keyword coverage
  - skills visibility
  - measurable impact
  - role clarity
  - grammar and consistency
- Display baseline ATS score from 0 to 100.
- Display score rationale and top improvement areas.

### Phase 4: Resume Improvement Loop

- Implement Resume Improvement Agent suggestions.
- Separate suggestions by formatting, wording, keywords, missing details, and optional role-specific improvements.
- Show proposed changes before applying them.
- Add user approval or skip controls.
- Generate projected improved ATS score if the user chooses to implement changes.
- Apply approved changes and create a new resume version.
- Preserve the original resume for comparison and rollback.

### Phase 5: Job Search Criteria

After resume changes are approved or skipped, prompt the user for:

- target job type or role
- posting date filter, such as today, past 24 hours, past week, or custom date
- job location, including remote, hybrid, city, state, or country

Validate search criteria before starting job search.

### Phase 6: Internet Job Search

- Implement Job Search Agent for internet job discovery.
- Capture for each posting:
  - title
  - company
  - location
  - posting date
  - source
  - job URL
  - application URL
  - job description text
- Deduplicate jobs by company, title, location, and URL.
- Flag postings that require login, manual review, or unsupported application flows.

### Phase 7: Match Scoring

- Implement Match Analyzer Agent.
- Compare the approved resume against every job posting.
- Generate:
  - match percentage
  - matched skills
  - missing skills
  - missing keywords
  - hard requirement gaps
  - preferred qualification gaps
  - short rationale
- Rank jobs from highest to lowest match percentage.

### Phase 8: Threshold-Based Auto-Apply

- Ask whether the user wants automatic applications enabled.
- Prompt for the user-defined minimum match percentage threshold.
- Store the threshold in workflow state.
- Show jobs that meet or exceed the threshold before applying.
- Implement Application Agent for jobs above threshold.
- Pause for unknown application questions.
- Log applied, skipped, failed, unsupported, and needs-user-input jobs.

### Phase 9: Lower-Match Job Review

- List remaining jobs below the threshold.
- Show current match percentage for each lower-match job.
- Show missing skills and missing keywords for each lower-match job.
- Show why each job did not meet the threshold.
- Ask whether the user has experience with each missing skill.
- Prompt the user to write experience notes for confirmed skills.

### Phase 10: Resume Update and Re-Match

- Update the resume only with user-confirmed missing-skill experience.
- Recalculate match ratings for affected job postings.
- If the revised match meets the original threshold, send the job to the Application Agent.
- If the revised match remains below threshold, keep the job in the lower-match review list.

## Frontend Flow

The UI should guide the user through the workflow in order:

1. **Resume Intake**
   - resume upload
   - LinkedIn profile link input
2. **ATS Score**
   - baseline score
   - score breakdown
3. **Resume Improvements**
   - suggested changes
   - approve or skip
   - projected improved score
4. **Job Search Criteria**
   - job type
   - posting date
   - location
5. **Job Matches**
   - ranked job cards
   - match percentages
   - missing skills and keywords
6. **Auto-Apply Settings**
   - opt-in toggle
   - user-defined threshold
   - jobs above threshold
7. **Application Tracker**
   - applied jobs
   - failed jobs
   - jobs needing user input
8. **Lower-Match Review**
   - lower-ranked jobs
   - missing skill prompts
   - user experience collection
   - re-scored matches

## Constraints and Safety Rules

- The agents must not fabricate skills, credentials, employment history, education, certifications, or project experience.
- The agents must distinguish between confirmed user experience and suggested future learning.
- Automated applications require explicit opt-in and a user-defined threshold.
- The system must keep an audit log of resume changes and application activity.
- Job search results should include source URLs so the user can inspect postings manually.
- Any browser automation must respect site terms, authentication requirements, rate limits, and user privacy.
- Jobs below the threshold must not be applied to unless re-scoring after user-confirmed resume updates meets the original threshold.
- The ATS score and match percentage are decision-support signals, not guarantees.

## Task Checklist

### Workflow Foundation

- [ ] Define shared workflow state for resume, LinkedIn link, ATS scores, job criteria, matches, threshold, and applications.
- [ ] Implement Coordinator Agent routing for the full ordered workflow.
- [ ] Add guardrails that prevent off-topic requests and fabricated resume content.
- [ ] Add resume version tracking for original, suggested, approved, and job-specific resumes.
- [ ] Add application and resume-change audit logging.

### Resume and LinkedIn Intake

- [ ] Build resume upload support for PDF, DOCX, and TXT.
- [ ] Extract raw resume text from uploaded files.
- [ ] Parse structured resume data: contact, skills, experience, education, projects, and certifications.
- [ ] Add LinkedIn profile link input and validation.
- [ ] Store LinkedIn as a profile reference unless the user provides accessible LinkedIn content or explicit authenticated access.

### Baseline ATS Scoring

- [ ] Implement ATS Analyzer Agent scoring for the current resume.
- [ ] Add ATS score categories for formatting, completeness, keyword coverage, measurable impact, and role clarity.
- [ ] Display baseline ATS score from 0 to 100.
- [ ] Display score rationale and top improvement areas.

### Resume Improvement Loop

- [ ] Implement Resume Improvement Agent suggestions.
- [ ] Separate suggestions by formatting, wording, keywords, missing details, and optional role-specific improvements.
- [ ] Show proposed changes before applying them.
- [ ] Add user approval or skip controls.
- [ ] Generate projected improved ATS score if the user chooses to implement changes.
- [ ] Apply approved changes and create a new resume version.

### Job Search Criteria

- [ ] Prompt for target job type or role.
- [ ] Prompt for when the job was posted.
- [ ] Prompt for job location.
- [ ] Validate search criteria before starting job search.

### Internet Job Search

- [ ] Implement Job Search Agent for internet job discovery.
- [ ] Capture job title, company, location, posting date, source URL, application URL, and job description.
- [ ] Deduplicate job postings.
- [ ] Flag postings that require login, manual review, or unsupported application flows.

### Match Scoring

- [ ] Implement Match Analyzer Agent.
- [ ] Generate match percentage for each job posting.
- [ ] Display matched skills for each job.
- [ ] Display missing skills for each job.
- [ ] Display missing keywords for each job.
- [ ] Separate hard requirement gaps from preferred qualification gaps when possible.
- [ ] Rank jobs from highest to lowest match percentage.

### Threshold-Based Auto-Apply

- [ ] Ask whether the user wants automatic applications enabled.
- [ ] Prompt for the user-defined minimum match percentage threshold.
- [ ] Show jobs that meet or exceed the threshold.
- [ ] Implement Application Agent for jobs above threshold.
- [ ] Pause for unknown application questions.
- [ ] Log applied, skipped, failed, unsupported, and needs-user-input jobs.

### Lower-Match Job Review

- [ ] List remaining jobs below the threshold.
- [ ] Show current match percentage for each lower-match job.
- [ ] Show missing skills and missing keywords for each lower-match job.
- [ ] Ask whether the user has experience with each missing skill.
- [ ] Prompt the user to write experience notes for confirmed skills.

### Resume Update and Re-Match

- [ ] Update the resume only with user-confirmed missing-skill experience.
- [ ] Recalculate match ratings for affected job postings.
- [ ] If the revised match meets the original threshold, send the job to the Application Agent.
- [ ] If the revised match remains below threshold, keep the job in the lower-match review list.

### Frontend Pages and Panels

- [ ] Build Resume Intake page with upload and LinkedIn link input.
- [ ] Build ATS Score page with baseline score and breakdown.
- [ ] Build Resume Improvements page with approve or skip controls.
- [ ] Build Job Search Criteria page.
- [ ] Build Job Matches page with ranked cards.
- [ ] Build Auto-Apply Settings page with threshold controls.
- [ ] Build Application Tracker page.
- [ ] Build Lower-Match Review page.

## Verification Plan

### Automated Tests

- Resume parsing for PDF, DOCX, and TXT.
- LinkedIn profile link validation.
- ATS score response shape and category coverage.
- Resume suggestion generation without fabrication.
- Projected ATS scoring after selected changes.
- Job search criteria validation.
- Job result normalization and deduplication.
- Match percentage calculation.
- Missing skill and keyword extraction.
- Threshold filtering.
- Application logging.
- Lower-match skill confirmation flow.
- Re-match after resume updates.

### Manual Verification

- Upload a resume and enter a LinkedIn profile link.
- Confirm the app displays a baseline ATS score.
- Review suggested resume changes and projected improved score.
- Approve changes and verify a new resume version is created.
- Enter job type, posting date, and location.
- Verify job postings are found and ranked.
- Confirm each job shows match percentage, missing skills, and missing keywords.
- Set a threshold and verify only jobs above the threshold are sent to the Application Agent.
- Confirm lower-match jobs remain visible for review.
- Add real experience for missing skills and verify the resume is updated and re-scored.
- Confirm jobs that newly meet the threshold are queued for application.
