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

from app.easy_agent.job_discovery_agent import job_discovery_agent, JobDiscoveryOutput
from app.easy_agent.tools import discover_easy_apply_jobs

@pytest.fixture(autouse=True)
def setup_temp_db(monkeypatch, tmp_path):
    """Overrides DB_PATH to a temporary location for isolated testing."""
    import os
    temp_db = str(tmp_path / "test_applications.db")
    monkeypatch.setattr("app.database.DB_PATH", temp_db)
    from app.database import init_db
    init_db()
    yield temp_db
    if os.path.exists(temp_db):
        os.remove(temp_db)

def test_job_discovery_agent_structure() -> None:
    """Verify that job_discovery_agent has correct configuration properties."""
    assert job_discovery_agent.name == "job_discovery_agent"
    assert job_discovery_agent.output_key == "job_discovery_result"
    assert job_discovery_agent.output_schema == JobDiscoveryOutput
    assert "Job Discovery Agent" in job_discovery_agent.instruction

def test_discover_easy_apply_jobs_tool() -> None:
    """Test the discover_easy_apply_jobs tool fallback logic."""
    keywords = ["Software Engineer", "Data Scientist"]
    loc = "Hyderabad"
    exp = 2.5
    
    results = discover_easy_apply_jobs(keywords, loc, exp)
    assert len(results) > 0
    for job in results:
        assert job["job_title"]
        assert job["company"]
        assert job["location"]
        assert isinstance(job["location"], str)
        assert job["job_url"].startswith("https://www.linkedin.com/jobs/view/")
        assert job["easy_apply"] is True
        assert job["already_applied"] is False

def test_discover_easy_apply_jobs_filtering() -> None:
    """Test that already applied jobs are filtered out by the discovery tool."""
    from app.database import create_application
    
    keywords = ["Software Engineer"]
    loc = "Hyderabad"
    exp = 2.5
    
    # 1. Get initial list of jobs (runs live or fallback depending on system context)
    results = discover_easy_apply_jobs(keywords, loc, exp)
    assert len(results) > 0
    
    # Pick one URL to "apply" to
    applied_job = results[0]
    applied_url = applied_job["job_url"]
    
    # 2. Create an application in the DB to mark it as applied
    create_application(
        job_url=applied_url,
        job_title=applied_job["job_title"],
        company=applied_job["company"]
    )
    
    # 3. Run discovery again and check that it is filtered out
    results_after = discover_easy_apply_jobs(keywords, loc, exp)
    urls_after = [job["job_url"] for job in results_after]
    
    # The applied URL should be filtered out
    assert applied_url not in urls_after


