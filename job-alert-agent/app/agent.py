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

import datetime
from zoneinfo import ZoneInfo
import os
import google.auth
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Load environment configuration from absolute path relative to this file
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "..", ".env")
load_dotenv(env_path, override=True)

try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except Exception:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    else:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

from app.job_intelligence_agent.agent import job_intelligence_agent
from app.application_agent.agent import application_agent
from app.easy_agent.agent import easy_agent
from app.security_agent.agent import security_agent

async def init_agent_state(callback_context) -> None:
    """Initialize agent session state with default recipient email if not provided."""
    if "recipient_email" not in callback_context.state:
        callback_context.state["recipient_email"] = os.environ.get("RECIPIENT_EMAIL", "candidate@example.com")

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Coordinator Agent. Your role is orchestrating the job hunt and career tasks.\n"
        "1. For any user request or action, you must first consult/delegate to the security_agent to validate "
        "the inputs, domain, and actions against the security guardrails. If validation fails, reject the request.\n"
        "2. For any request involving finding jobs, scraping job listings, or sending job alert email notifications, "
        "you must transfer control/delegate to the job_intelligence_agent subagent. Do not try to perform the scraping or email notifications yourself.\n"
        "3. For any request involving applying to a job, submitting a job application, or browser automation of form submissions (e.g. LinkedIn Easy Apply), "
        "you must transfer control/delegate to the application_agent subagent. Do not try to perform the application automation yourself.\n"
        "4. For any request involving easy apply automation, delegate control to the easy_agent subagent."
    ),
    sub_agents=[job_intelligence_agent, application_agent, easy_agent, security_agent],
    before_agent_callback=init_agent_state,
)

app = App(
    root_agent=root_agent,
    name="app",
)

