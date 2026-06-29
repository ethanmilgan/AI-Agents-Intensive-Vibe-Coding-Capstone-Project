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
import sqlite3
import pytest
from app.database import (
    init_db,
    create_application,
    update_application_status,
    get_application,
    add_hitl_prompt,
    get_pending_hitl_prompt,
    resolve_hitl_prompt,
    cache_answer,
    get_cached_answer,
    DB_PATH
)

@pytest.fixture(autouse=True)
def setup_temp_db(monkeypatch, tmp_path):
    """Overrides DB_PATH to a temporary location for isolated testing."""
    temp_db = str(tmp_path / "test_applications.db")
    monkeypatch.setattr("app.database.DB_PATH", temp_db)
    init_db()
    yield temp_db
    if os.path.exists(temp_db):
        os.remove(temp_db)

def test_database_application_lifecycle():
    # 1. Create Application
    app_id = create_application(
        job_url="https://www.linkedin.com/jobs/view/123",
        job_title="Software Engineer",
        company="Google"
    )
    assert app_id is not None
    
    # 2. Get Application
    app = get_application(app_id)
    assert app["job_url"] == "https://www.linkedin.com/jobs/view/123"
    assert app["job_title"] == "Software Engineer"
    assert app["company"] == "Google"
    assert app["status"] == "Queued"
    
    # 3. Update Status
    update_application_status(app_id, "Running")
    app = get_application(app_id)
    assert app["status"] == "Running"
    
    # 4. Update Status with Screenshot
    update_application_status(app_id, "Waiting for Final Review", screenshot_path="/tmp/shot.png")
    app = get_application(app_id)
    assert app["status"] == "Waiting for Final Review"
    assert app["screenshot_path"] == "/tmp/shot.png"

def test_database_hitl_prompts():
    app_id = create_application(job_url="https://example.com/job")
    
    # 1. Add prompt
    prompt_id = add_hitl_prompt(
        app_id=app_id,
        question_text="How many years of experience do you have with Python?",
        input_type="text"
    )
    assert prompt_id is not None
    
    # 2. Get pending prompt
    prompt = get_pending_hitl_prompt(app_id)
    assert prompt is not None
    assert prompt["question_text"] == "How many years of experience do you have with Python?"
    assert prompt["input_type"] == "text"
    assert prompt["status"] == "Pending"
    
    # 3. Resolve prompt
    resolve_hitl_prompt(prompt_id, "3 years")
    
    # 4. Verify resolved
    prompt = get_pending_hitl_prompt(app_id)
    assert prompt is None  # Should be none since it is resolved

def test_database_qa_cache():
    # 1. Check empty cache
    ans = get_cached_answer("Do you know Go?")
    assert ans is None
    
    # 2. Cache answer
    cache_answer("Do you know Go?", "Yes, 2 years")
    
    # 3. Check cache hit
    ans = get_cached_answer("Do you know Go?")
    assert ans == "Yes, 2 years"
