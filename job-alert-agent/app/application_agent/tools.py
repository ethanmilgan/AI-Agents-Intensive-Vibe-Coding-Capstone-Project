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

import asyncio
import subprocess
import sys
import os

from .login_worker import check_linkedin_session_sync, login_to_linkedin_sync

async def check_linkedin_session() -> dict:
    """Checks if the saved LinkedIn session is still valid.
    
    Returns:
        A dictionary containing the session validity status.
    """
    logged_in = await asyncio.to_thread(check_linkedin_session_sync)
    return {
        "status": "success",
        "logged_in": logged_in,
        "message": "User is logged in to LinkedIn." if logged_in else "LinkedIn session is expired or missing."
    }

async def login_to_linkedin(timeout_seconds: int = 300) -> dict:
    """Launches a headful browser for manual login and waits for resolution.
    
    Args:
        timeout_seconds: Time in seconds to wait for manual login.
        
    Returns:
        A dictionary containing the login outcome status.
    """
    success = await asyncio.to_thread(login_to_linkedin_sync, None, timeout_seconds)
    if success:
        return {
            "status": "success",
            "message": "LinkedIn logged in successfully."
        }
    else:
        return {
            "status": "error",
            "message": "LinkedIn login timed out or failed."
        }

def parse_resume_to_profile(resume_path: str) -> dict:
    """Placeholder ATS resume parser.
    
    Args:
        resume_path: Path to the PDF resume file.
        
    Returns:
        An empty candidate profile dictionary.
    """
    return {}

def apply_for_job(job_url: str, job_title: str = "", company: str = "", candidate_profile: dict = None, resume_path: str = None, li_username: str = None, li_password: str = None) -> dict:
    """Queues a job application in SQLite and spawns a background worker subprocess.
    
    Args:
        job_url: LinkedIn job posting URL.
        job_title: Target job title.
        company: Target company name.
        candidate_profile: Structured candidate resume data.
        resume_path: Path to the candidate's PDF resume file.
        li_username: Optional LinkedIn username (not stored on disk).
        li_password: Optional LinkedIn password (not stored on disk).
        
    Returns:
        A dictionary indicating success and containing the created application ID.
    """
    from app.database import create_application, add_application_log
    
    # 1. Create the application in the SQLite database (sets status to 'Queued')
    app_id = create_application(
        job_url=job_url,
        job_title=job_title,
        company=company,
        candidate_profile=candidate_profile,
        resume_path=resume_path
    )
    
    add_application_log(app_id, "INFO", "Worker", f"Job application queued. Preparing to launch worker...")
    
    # 2. Spawn the worker subprocess
    worker_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker.py")
    
    env = os.environ.copy()
    if li_username:
        env["LINKEDIN_USERNAME"] = li_username
    if li_password:
        env["LINKEDIN_PASSWORD"] = li_password
        
    # Launch worker.py as a detached background subprocess
    try:
        subprocess.Popen(
            [sys.executable, worker_script, str(app_id)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True, # Detaches the process so it runs independently
            env=env
        )
        return {
            "status": "success",
            "application_id": app_id,
            "message": f"Successfully queued application {app_id} and spawned background worker."
        }
    except Exception as e:
        error_msg = f"Failed to spawn background worker: {str(e)}"
        add_application_log(app_id, "ERROR", "Worker", error_msg)
        from app.database import update_application_status
        update_application_status(app_id, "Failed", error_message=error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

def get_application_status(app_id: int) -> dict:
    """Retrieves the status of a job application.
    
    Args:
        app_id: The ID of the application.
        
    Returns:
        A dictionary containing application status.
    """
    from app.database import get_application
    app = get_application(app_id)
    if app:
        return {
            "status": "success",
            "application": app
        }
    return {
        "status": "error",
        "message": f"Application {app_id} not found."
    }
