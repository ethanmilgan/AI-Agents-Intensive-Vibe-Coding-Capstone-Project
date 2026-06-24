# Task List: Resume to Job Application Agent

## 👤 Developer 1: Streamlit Frontend & Integration
- [ ] Build the Streamlit multi-tab app layout (`streamlit_app.py`)
- [ ] Create Resume Workspace inputs (manual forms, uploads, LinkedIn imports)
- [ ] Implement Tailoring & ATS Score panel (gaps, scores, download links)
- [ ] Build Auto-Apply Tracker UI showing browser status
- [ ] Implement Human-in-the-Loop response dialog (answering unknown fields and resuming Playwright)
- [ ] Create simplified Job Alerts UI (Recipient Email, Role Search, Location) and a collapsible Advanced Settings SMTP panel
- [ ] Create Application History log dashboard

## 👤 Developer 2: Agent Logic, Scrapers & Email Service
- [ ] Define Parent Coordinator Agent and routing logic (`app/agent.py`)
- [ ] Implement off-topic Pre-flight Gatekeeper check
- [ ] Define ATS Analyzer Agent prompt instructions and score weights
- [ ] Implement Playwright LinkedIn daily job scraper tool (`app/tools.py`)
- [ ] Implement SMTP email formatter and sender (`app/email_service.py`)
- [ ] Write standalone `daily_job_alerts.py` script for task scheduling
- [ ] Setup `pytest` unit test files for parsing and emails (`tests/unit/`)

## 👤 Developer 3: Form Filling & Resume Export Engine
- [ ] Develop Form Filler Agent Playwright tool to automate LinkedIn Easy Apply and external ATS forms (Greenhouse, Lever, Workday, etc.)
- [ ] Implement browser redirect follower for external LinkedIn job links
- [ ] Develop Playwright pause-and-resume listener for unknown fields
- [ ] Create HTML-to-PDF compiler using Playwright
- [ ] Implement Word Document generator (`python-docx`)
- [ ] Implement visual layout and template style copier
- [ ] Define UAT evaluation dataset (`tests/eval/datasets/uat-dataset.jsonl`) and `eval_config.yaml`
