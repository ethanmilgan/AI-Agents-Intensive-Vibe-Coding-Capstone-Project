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
import time
import pytest
from app.database import (
    get_application,
    init_db,
    get_application_logs
)
from app.application_agent.tools import apply_for_job

def test_worker_external_apply(monkeypatch, tmp_path):
    # Set headless environment variable to run Playwright headlessly for the test
    monkeypatch.setenv("BROWSER_HEADLESS", "True")
    monkeypatch.setenv("PLAYWRIGHT_PROFILE_DIR", str(tmp_path / ".playwright_profile"))
    
    # Isolate database path to a temporary location
    temp_db = str(tmp_path / "test_applications.db")
    monkeypatch.setenv("DATABASE_PATH", temp_db)
    monkeypatch.setattr("app.database.DB_PATH", temp_db)
    
    # Initialize the temporary database schema
    init_db()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mock_html_path = os.path.abspath(os.path.join(script_dir, "..", "mock_external_apply.html"))
    file_url = f"file:///{mock_html_path.replace(os.sep, '/')}"
    
    # Ensure there is a dummy resume file path
    dummy_resume = os.path.join(script_dir, "..", "dummy_resume.pdf")
    if not os.path.exists(dummy_resume):
        with open(dummy_resume, "wb") as f:
            f.write(b"%PDF-1.4 ... dummy content")
            
    # Session candidate profile
    profile = {
        "personal_info": {
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "9999999999",
            "location": "Hyderabad, India",
            "resume_path": dummy_resume
        },
        "education": [],
        "experience": [],
        "skills": {"languages": ["Python"]}
    }
    
    # Call tool to queue application and start worker.py background subprocess
    res = apply_for_job(
        job_url=file_url,
        job_title="Staff Data Scientist (External)",
        company="PepsiCo",
        candidate_profile=profile,
        resume_path=dummy_resume
    )
    
    assert res["status"] == "success"
    app_id = res["application_id"]
    
    # Poll database and verify it reaches External Application status
    max_wait = 45  # 45 seconds max wait
    start_time = time.time()
    
    reached_external = False
    
    while time.time() - start_time < max_wait:
        app = get_application(app_id)
        assert app is not None
        status = app["status"]
        
        if status == "External Application":
            reached_external = True
            break
        elif status == "Failed":
            pytest.fail(f"Worker failed instead of flagging external redirection: {app['error_message']}")
            
        time.sleep(1.0)
        
    # Clean up dummy resume
    if os.path.exists(dummy_resume):
        try:
            os.remove(dummy_resume)
        except Exception:
            pass
            
    assert reached_external is True

    # Verify database logs are successfully populated
    logs = get_application_logs(app_id)
    assert len(logs) > 0, "No application logs recorded in SQLite database"
    
    # Check that key logs are present
    messages = [log["message"] for log in logs]
    external_log_present = any("requires an external application" in msg or "Redirected to:" in msg for msg in messages)
    assert external_log_present is True, "No external redirection message found in logs"
