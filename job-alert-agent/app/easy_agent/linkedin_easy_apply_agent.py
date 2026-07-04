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

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from .tools import execute_easy_apply_job
from app.application_agent.form_filler_agent import form_filler_agent

class EasyApplyAgentInput(BaseModel):
    job_url: str = Field(description="URL of the LinkedIn Easy Apply job")
    candidate_profile: dict = Field(description="Candidate profile containing personal info and resume path")

class EasyApplyAgentOutput(BaseModel):
    status: str = Field(description="Outcome status of the application: SUCCESS, FAILED, SKIPPED, ALREADY_APPLIED, ERROR")
    job_title: str = Field(description="Title of the job")
    company: str = Field(description="Hiring company")
    application_url: str = Field(description="URL of the job or application")
    submitted_at: str = Field(description="Timestamp when the application was submitted")
    logs: List[str] = Field(default=[], description="List of log messages generated during execution")

linkedin_easy_apply_agent = Agent(
    name="linkedin_easy_apply_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the LinkedIn Easy Apply Agent.\n\n"
        "Your only responsibility is to submit one LinkedIn Easy Apply application.\n"
        "You do NOT search jobs.\n"
        "You do NOT login.\n"
        "You do NOT parse resumes.\n"
        "Those responsibilities belong to other agents.\n\n"
        "## Objective\n"
        "Given one LinkedIn Easy Apply job URL and candidate profile data, use the execute_easy_apply_job tool "
        "to complete the application exactly like a human and submit it. Return the structured results.\n\n"
        "## Workflow & Rules\n"
        "- Trigger execute_easy_apply_job with the provided job_url and candidate_profile.\n"
        "- The tool will automate navigation, verify Easy Apply availability, and fill dynamic forms.\n"
        "- For filling job application forms page-by-page, delegate to the form_filler_agent.\n"
        "- Map the final result status (SUCCESS, FAILED, SKIPPED, ALREADY_APPLIED, ERROR) and return it. Never return free-form text."
    ),
    tools=[execute_easy_apply_job],
    output_schema=EasyApplyAgentOutput,
    output_key="easy_apply_result",
)
