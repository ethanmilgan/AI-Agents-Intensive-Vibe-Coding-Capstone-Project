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

from .tools import check_linkedin_session, login_to_linkedin

login_agent = Agent(
    name="login_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the LinkedIn Login Sub-Agent. Your single objective is to manage the user's LinkedIn login state.\n"
        "1. Check if a valid LinkedIn session exists using check_linkedin_session tool.\n"
        "2. If it is valid, confirm to the user they are logged in.\n"
        "3. If not valid, prompt the user that login is required, launch the headful browser login tool using login_to_linkedin, "
        "and inform them once they are successfully signed in and the session is stored.\n"
        "Keep your communication concise and direct."
    ),
    tools=[check_linkedin_session, login_to_linkedin],
)
