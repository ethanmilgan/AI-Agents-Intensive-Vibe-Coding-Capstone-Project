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

from .tools import apply_for_job, get_application_status, parse_resume_to_profile, discover_easy_apply_jobs, execute_easy_apply_job
from .login_agent import login_agent
from .job_discovery_agent import job_discovery_agent
from .linkedin_easy_apply_agent import linkedin_easy_apply_agent

easy_agent = Agent(
    name="easy_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Easy Apply Agent. Your job is to automate job applications.\n"
        "1. When a job application task is requested, delegate to the login_agent "
        "sub-agent to check or perform LinkedIn authentication.\n"
        "2. Once authenticated (or if a valid session exists), delegate to the job_discovery_agent "
        "to search and discover Easy Apply jobs based on target keywords, location, and experience.\n"
        "3. Take the list of discovered jobs returned by the job_discovery_agent and apply to those jobs. "
        "For each job in the list, delegate to the linkedin_easy_apply_agent to submit the application. "
        "If one of the suggested jobs is applied (or skipped/already applied), proceed to the next suggested one in the list."
    ),
    sub_agents=[login_agent, job_discovery_agent, linkedin_easy_apply_agent],
    tools=[apply_for_job, get_application_status, parse_resume_to_profile, discover_easy_apply_jobs, execute_easy_apply_job],
)
