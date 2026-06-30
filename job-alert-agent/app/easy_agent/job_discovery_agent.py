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
from .tools import discover_easy_apply_jobs

class JobDiscoveryInput(BaseModel):
    target_job_keywords: List[str] = Field(description="Target job search keywords")
    preferred_location: str = Field(description="Preferred location for the job search")
    years_of_experience: float = Field(description="Years of experience candidate has")

class JobDiscoveryResultItem(BaseModel):
    job_title: str = Field(description="Title of the job")
    company: str = Field(description="Name of the hiring company")
    location: str = Field(description="Location of the job")
    job_url: str = Field(description="LinkedIn job view URL")
    easy_apply: bool = Field(default=True, description="Whether the job supports Easy Apply")
    posted: str = Field(description="When the job was posted (e.g. '24 hours ago', '1 week ago')")
    experience_level: str = Field(description="Target experience level or years of experience required")
    company_name: str = Field(description="Name of the company (same as company)")
    already_applied: bool = Field(default=False, description="Whether the candidate has already applied to this job")

class JobDiscoveryOutput(BaseModel):
    jobs: List[JobDiscoveryResultItem] = Field(description="List of discovered Easy Apply jobs")

job_discovery_agent = Agent(
    name="job_discovery_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Job Discovery Agent.\n\n"
        "Your sole responsibility is to discover relevant LinkedIn Easy Apply jobs.\n"
        "You DO NOT apply for jobs.\n"
        "You DO NOT fill application forms.\n"
        "You DO NOT parse resumes.\n"
        "You DO NOT login.\n"
        "Those responsibilities belong to other agents.\n\n"
        "## Objective\n"
        "Given target job keywords, preferred location, and years of experience, "
        "search LinkedIn Jobs using the discover_easy_apply_jobs tool and return a ranked list of Easy Apply jobs suitable for the candidate.\n\n"
        "## Responsibilities\n"
        "- Search LinkedIn Jobs using discover_easy_apply_jobs.\n"
        "- Only consider jobs satisfying ALL of the following: Easy Apply (true), Active, Not already applied (already_applied is false), Relevant, Matches location, Matches experience.\n"
        "- Search every supplied keyword independently, merge all results, remove duplicate jobs, and rank them.\n"
        "- Never attempt an application.\n"
        "- If LinkedIn fails (or returns empty), use the tool's fallback results which retry once internally and provide clean fallback results. Never fabricate jobs or guess missing information."
    ),
    tools=[discover_easy_apply_jobs],
    output_schema=JobDiscoveryOutput,
    output_key="job_discovery_result",
)
