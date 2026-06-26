# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# We need the config_loader so the properties are read
from config.config_loader import app_config

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

from app.tools import (
    parse_resume_text,
    score_resume_ats,
    apply_approved_resume_changes,
    generate_future_roadmap,
    adapt_global_fit,
    discover_hidden_skills,
    generate_proof_of_skill_showcase,
    search_and_scrapes_jobs,
    analyze_resume_roi,
    audit_resume_searchability,
    build_skill_gap_plan,
    prepare_and_send_email_alerts,
    simulate_apply_swarm,
    salary_negotiation_turn,
    digital_twin_qa,
    generate_twin_cover_letter
)

# 1. Resume Specialist Agent
resume_agent = Agent(
    name="resume_agent",
    model=Gemini(
        model=app_config.get("geminiModel", "gemini-1.5-flash"),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a professional resume writer and parser.
    Your duties include parsing raw text resumes, evaluating ATS scores, suggesting improvements, generating 3-6 month future resumes/roadmaps, adapting resumes to global markets, uncovering hidden skills, and producing verified portfolio showcases.
    Delegate to your specialized tools to accomplish these tasks.""",
    description="A specialist agent that parses, scores, optimizes, and adapts resumes. Use this agent for any resume-related work.",
    tools=[
        parse_resume_text,
        score_resume_ats,
        apply_approved_resume_changes,
        generate_future_roadmap,
        adapt_global_fit,
        discover_hidden_skills,
        generate_proof_of_skill_showcase
    ],
)

# 2. Job Intelligence Specialist Agent
job_intel_agent = Agent(
    name="job_intel_agent",
    model=Gemini(
        model=app_config.get("geminiModel", "gemini-1.5-flash"),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a job discovery and market intelligence analyst.
    Your duties include searching and scraping job postings, conducting semantic match ratings, auditing resume findability, constructing skill gap learning plans, and preparing email notification payloads.
    Delegate to your specialized tools to accomplish these tasks.""",
    description="A specialist agent that searches jobs, calculates ROI scores, performs searchability audits, and drafts alerts.",
    tools=[
        search_and_scrapes_jobs,
        analyze_resume_roi,
        audit_resume_searchability,
        build_skill_gap_plan,
        prepare_and_send_email_alerts
    ],
)

# 3. Controlled Application Specialist Agent
application_agent = Agent(
    name="application_agent",
    model=Gemini(
        model=app_config.get("geminiModel", "gemini-1.5-flash"),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an automated application assistant and negotiation coach.
    Your duties include running the One-Click Apply Swarm simulation (tailoring summaries, drafting cover letters, generating interview prep notes) and coaching the candidate through salary negotiations.
    Delegate to your specialized tools to accomplish these tasks.""",
    description="A specialist agent that executes application workflows and coaches negotiations.",
    tools=[
        simulate_apply_swarm,
        salary_negotiation_turn
    ],
)

# 4. Coordinator Agent (Parent/Root Agent)
root_agent = Agent(
    name="talent_coordinator",
    model=Gemini(
        model=app_config.get("geminiModel", "gemini-1.5-flash"),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Talent AI Coordinator, the parent agent and workflow supervisor.
    Your role is to orchestrate candidate career development, manage the autonomous Career Twin loop, and secure user consent at critical transition stages.
    You also manage the candidate's Digital Twin Q&A recruiter dashboard and generate cover letters.
    When a user requests specific resume, job, or application workflows, delegate tasks to the corresponding specialist sub-agent (resume_agent, job_intel_agent, or application_agent).
    Always verify inputs and summarize the outputs professionally.""",
    sub_agents=[resume_agent, job_intel_agent, application_agent],
    tools=[
        digital_twin_qa,
        generate_twin_cover_letter
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)
