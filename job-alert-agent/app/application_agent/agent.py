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

from .tools import apply_for_job, get_application_status, parse_resume_to_profile
from .login_agent import login_agent
from .form_filler_agent import form_filler_agent

application_agent = Agent(
    name="application_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Application Agent. Your job is to automate job applications.\n"
        "1. When a job application task is requested, delegate to the login_agent "
        "sub-agent to check or perform LinkedIn authentication.\n"
        "2. Once authenticated (or if a valid session exists), call the apply_for_job "
        "tool to trigger the application process.\n"
        "3. For filling job application forms, delegate to the form_filler_agent subagent."
    ),
    sub_agents=[login_agent, form_filler_agent],
    tools=[apply_for_job, get_application_status, parse_resume_to_profile],
)
