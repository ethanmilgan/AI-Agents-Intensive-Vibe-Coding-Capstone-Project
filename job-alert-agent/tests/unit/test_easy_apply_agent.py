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

import pytest
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.easy_agent.linkedin_easy_apply_agent import linkedin_easy_apply_agent, EasyApplyAgentOutput
from app.easy_agent.tools import execute_easy_apply_job

def test_easy_apply_agent_structure() -> None:
    """Verify that linkedin_easy_apply_agent has correct configuration properties."""
    assert linkedin_easy_apply_agent.name == "linkedin_easy_apply_agent"
    assert linkedin_easy_apply_agent.output_key == "easy_apply_result"
    assert linkedin_easy_apply_agent.output_schema == EasyApplyAgentOutput
    assert "LinkedIn Easy Apply Agent" in linkedin_easy_apply_agent.instruction

def test_execute_easy_apply_job_tool_invalid_url() -> None:
    """Test the execute_easy_apply_job tool handles invalid URLs gracefully."""
    job_url = "https://www.linkedin.com/jobs/view/invalid99001122"
    candidate_profile = {
        "personal_info": {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "1234567890",
            "location": "Hyderabad",
            "resume_path": ""
        }
    }
    
    res = execute_easy_apply_job(job_url, candidate_profile)
    assert res["status"] in ["FAILED", "SKIPPED", "ERROR"]
    assert res["application_url"] == job_url
