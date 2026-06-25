# ruff: noqa
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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth
from google.auth.exceptions import DefaultCredentialsError
from dotenv import load_dotenv

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
    # Fallback to Gemini API Key from Google AI Studio if local GCP credentials are not available
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    else:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"



from app.tools import scrape_linkedin_jobs, send_job_alert_email

async def init_agent_state(callback_context) -> None:
    """Initialize agent session state with default recipient email if not provided."""
    if "recipient_email" not in callback_context.state:
        import os
        callback_context.state["recipient_email"] = os.environ.get("RECIPIENT_EMAIL", "candidate@example.com")

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a Job Alert Agent whose role is automating the job hunt and sending daily updates.\n"
        "The recipient email address for job alerts is: {recipient_email}\n"
        "When asked to find and notify about jobs, you must:\n"
        "1. Scrape/find job listings matching the user's criteria (keywords/role and location) "
        "using the `scrape_linkedin_jobs` tool.\n"
        "2. Send the found job listings to the recipient at {recipient_email} using the `send_job_alert_email` tool. "
        "The email tool expects a list of dictionaries with job details.\n"
        "Provide a summary of the actions taken once the email has been sent successfully."
    ),
    tools=[scrape_linkedin_jobs, send_job_alert_email],
    before_agent_callback=init_agent_state,
)

app = App(
    root_agent=root_agent,
    name="app",
)
