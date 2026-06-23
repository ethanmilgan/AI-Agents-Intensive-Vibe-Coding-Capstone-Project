# AI-Agents-Intensive-Vibe-Coding-Capstone-Project

## Project Overview

This project is a hierarchical multi-agent prototype for improving a resume, searching for relevant jobs, scoring resume-to-job fit, and applying to jobs when the user approves threshold-based automation.

The core workflow is:

1. Upload a resume and enter a LinkedIn profile link.
2. Generate a baseline ATS score for the current resume.
3. Suggest resume changes that can improve the ATS score.
4. Show a projected improved ATS score if the user chooses to implement the changes.
5. Ask the user for the type of job they want, when the job was posted, and where the job is located.
6. Search the internet for matching job postings.
7. Score each job posting against the resume.
8. Show missing skills and keywords for every job.
9. Ask whether the user wants automatic applications for jobs above a user-defined match threshold.
10. Apply to jobs that meet or exceed the threshold.
11. List remaining lower-match jobs.
12. Ask whether the user has experience with missing skills for those lower-match jobs.
13. Update the resume only with user-confirmed experience.
14. Recalculate match ratings.
15. Apply automatically if the revised match rating meets the original threshold.

## Agent Architecture

The system is organized as a parent Coordinator Agent with specialist subagents:

- **Coordinator Agent**: manages workflow state, routing, ordering, and guardrails.
- **Resume Intake Agent**: parses uploaded resumes and stores the LinkedIn profile link.
- **ATS Analyzer Agent**: scores the current resume and projected improved resume.
- **Resume Improvement Agent**: suggests and applies truthful resume improvements.
- **Job Search Agent**: searches for jobs based on role, posting date, and location.
- **Match Analyzer Agent**: calculates match percentages and missing skills/keywords.
- **Application Agent**: applies to jobs above the user-defined threshold after opt-in.
- **Lower-Match Review Agent**: reviews jobs below threshold and collects confirmed missing-skill experience.

## Safety Rules

- The system must not fabricate skills, experience, certifications, education, employment history, or project work.
- Resume updates must be based on existing resume facts or user-confirmed experience.
- Automatic applications require explicit user opt-in and a user-defined threshold.
- Application activity must be logged.
- Jobs below the threshold must not be applied to unless re-scoring after user-confirmed resume updates meets the original threshold.

## Current Documentation

- `PROJECT_PLAN.md` is the consolidated source of truth for:
  - the hierarchical agent spec
  - the target workflow
  - the implementation phases
  - the task checklist
  - the verification plan

The previous separate planning files have been consolidated into this single project plan to reduce duplication and keep the workflow easier to maintain.

## Frontend

The current frontend prototype is located in:

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

The frontend should be updated to guide the user through resume intake, ATS scoring, resume improvements, job search criteria, job matches, auto-apply settings, application tracking, and lower-match review.

## Run

Open `frontend/index.html` in a browser or serve the `frontend` folder with a static server.

## Notes

This repository is currently a prototype. Internet job search, ATS scoring, resume rewriting, and application automation should be connected to backend agents or APIs as the implementation matures.
