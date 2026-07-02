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

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
import logging

setup_telemetry()

# Safely initialize logging client with a fallback for local offline environment
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
    cloud_logging_enabled = True
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    cloud_logging_enabled = False

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "adk_agents")
# In-memory session configuration - no persistent storage
session_service_uri = None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=False,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=cloud_logging_enabled,
)
app.title = "job-alert-agent"
app.description = "API for interacting with the Agent job-alert-agent"


from fastapi import BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import io
import pypdf
from google import genai
from google.genai import types

# Allow CORS during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Profile path
PROFILE_PATH = os.path.join(AGENT_DIR, "candidate_profile.json")
ENV_PATH = os.path.join(AGENT_DIR, ".env")

def save_env_var(key, value):
    os.environ[key] = str(value)
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    key_found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)
    if not key_found:
        new_lines.append(f"{key}={value}\n")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

# Models
class ProfileUpdate(BaseModel):
    personal_info: Dict[str, Any]
    education: List[Dict[str, Any]]
    experience: List[Dict[str, Any]]
    skills: Dict[str, Any]

class SettingsUpdate(BaseModel):
    JOB_KEYWORDS: Optional[str] = None
    JOB_LOCATION: Optional[str] = None
    RECIPIENT_EMAIL: Optional[str] = None
    JOB_EXPERIENCE: Optional[str] = None
    ALERT_FREQUENCY: Optional[str] = None
    EMAIL_JOB_LIMIT: Optional[str] = None
    LINKEDIN_USERNAME: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None

class HITLResolveRequest(BaseModel):
    prompt_id: int
    answer: str

class DiscoveryRequest(BaseModel):
    keywords: str
    location: str
    experience: float

class RunAlertRequest(BaseModel):
    keywords: str
    location: str
    experience: str
    frequency: str
    recipient: str

class ApplyRequest(BaseModel):
    job_url: str
    job_title: str
    company: str

@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if cloud_logging_enabled:
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info(f"Feedback received: {feedback.model_dump()}")
    return {"status": "success"}

# --- New Custom REST API Endpoints ---

@app.get("/api/profile")
def get_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return JSONResponse(status_code=500, content={"message": f"Error reading profile: {e}"})
    return {"personal_info": {}, "education": [], "experience": [], "skills": {}}

@app.post("/api/profile")
def update_profile(profile: ProfileUpdate):
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile.model_dump(), f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": "Profile updated successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error saving profile: {e}"})

@app.get("/api/settings")
def get_settings():
    return {
        "JOB_KEYWORDS": os.environ.get("JOB_KEYWORDS", ""),
        "JOB_LOCATION": os.environ.get("JOB_LOCATION", ""),
        "RECIPIENT_EMAIL": os.environ.get("RECIPIENT_EMAIL", ""),
        "JOB_EXPERIENCE": os.environ.get("JOB_EXPERIENCE", "Any Experience"),
        "ALERT_FREQUENCY": os.environ.get("ALERT_FREQUENCY", "Daily"),
        "EMAIL_JOB_LIMIT": os.environ.get("EMAIL_JOB_LIMIT", "5"),
        "LINKEDIN_USERNAME": os.environ.get("LINKEDIN_USERNAME", ""),
        "LINKEDIN_PASSWORD": "••••••••" if os.environ.get("LINKEDIN_PASSWORD") else ""
    }

@app.post("/api/settings")
def update_settings(settings: SettingsUpdate):
    try:
        for key, value in settings.model_dump(exclude_unset=True).items():
            if value is not None:
                if key == "LINKEDIN_PASSWORD" and value == "••••••••":
                    continue
                save_env_var(key, value)
        return {"status": "success", "message": "Settings updated"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error saving settings: {e}"})

@app.get("/api/applications")
def get_applications_endpoint():
    from app.database import get_all_applications
    try:
        apps = get_all_applications()
        # Decode candidate_profile JSON if string
        for a in apps:
            if a.get("candidate_profile") and isinstance(a["candidate_profile"], str):
                try:
                    a["candidate_profile"] = json.loads(a["candidate_profile"])
                except Exception:
                    pass
        return apps
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error getting applications: {e}"})

@app.get("/api/applications/{id}/logs")
def get_logs_endpoint(id: int):
    from app.database import get_application_logs
    try:
        return get_application_logs(id)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error getting application logs: {e}"})

class ApplicationStatusUpdate(BaseModel):
    status: str

@app.get("/api/applications/{id}/screenshot")
def get_screenshot_endpoint(id: int):
    from app.database import get_application
    try:
        app_data = get_application(id)
        if app_data and app_data.get("screenshot_path"):
            path = app_data["screenshot_path"]
            if os.path.exists(path):
                return FileResponse(path)
        return JSONResponse(status_code=404, content={"message": "Screenshot not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error getting screenshot: {e}"})

@app.post("/api/applications/{id}/status")
def update_app_status_endpoint(id: int, req: ApplicationStatusUpdate):
    from app.database import update_application_status
    try:
        update_application_status(id, req.status)
        return {"status": "success", "message": f"Application status updated to {req.status}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error updating status: {e}"})

@app.get("/api/hitl/pending")
def get_pending_hitl():
    from app.database import get_all_pending_hitl_prompts, get_application
    try:
        prompts = get_all_pending_hitl_prompts()
        active_prompts = []
        for p in prompts:
            app_data = get_application(p["application_id"])
            if app_data and app_data["status"] == "Waiting for User Input":
                active_prompts.append(p)
        return active_prompts
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error getting pending HITL prompts: {e}"})

@app.post("/api/hitl/resolve")
def resolve_hitl(req: HITLResolveRequest):
    from app.database import resolve_hitl_prompt, update_application_status, get_hitl_prompt
    try:
        prompt = get_hitl_prompt(req.prompt_id)
        if not prompt:
            return JSONResponse(status_code=404, content={"message": "Prompt not found"})
        
        resolve_hitl_prompt(req.prompt_id, req.answer)
        update_application_status(prompt["application_id"], "Running")
        return {"status": "success", "message": "HITL prompt resolved, application resumed"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error resolving HITL prompt: {e}"})

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        
        # 1. Parse PDF text
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
            
        # 2. Call Gemini
        client = genai.Client()
        prompt = f"""You are an expert ATS resume parser.
Analyze this candidate resume text and extract it into a structured JSON profile.

Resume Text:
{text}

Return ONLY a valid JSON object matching this schema:
{{
  "personal_info": {{
    "first_name": "string (first name)",
    "last_name": "string (last name)",
    "full_name": "string (full name)",
    "email": "string (email)",
    "phone": "string (phone number)",
    "linkedin": "string (linkedin URL or empty)",
    "github": "string (github URL or empty)",
    "location": "string (city, country or city, state)"
  }},
  "education": [
    {{
      "institution": "string",
      "degree": "string",
      "field_of_study": "string",
      "start_year": "string",
      "end_year": "string"
    }}
  ],
  "experience": [
    {{
      "job_title": "string",
      "company": "string",
      "location": "string",
      "start_date": "string",
      "end_date": "string",
      "description": ["bullet point 1", "bullet point 2"]
    }}
  ],
  "skills": {{
    "languages": ["string"],
    "databases": ["string"],
    "tools_and_platforms": ["string"],
    "analytical_skills": ["string"]
  }}
}}

Ensure the response is ONLY a raw JSON block. Do not include markdown code ticks.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        parsed_profile = json.loads(response.text)
        
        # 3. Save resume temporarily
        temp_dir = os.path.join(AGENT_DIR, "temp_resumes")
        os.makedirs(temp_dir, exist_ok=True)
        import uuid
        temp_filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
        temp_path = os.path.join(temp_dir, temp_filename)
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
            
        parsed_profile["personal_info"]["resume_path"] = temp_path
        
        # Save to candidate_profile.json
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(parsed_profile, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "profile": parsed_profile, "resume_path": temp_path}
    except Exception as e:
        # Fallback to local profile if parsing fails
        if os.path.exists(PROFILE_PATH):
            try:
                with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                    cached_profile = json.load(f)
                return {"status": "success", "profile": cached_profile, "message": f"Gemini parse failed ({e}), loaded cached profile"}
            except Exception:
                pass
        return JSONResponse(status_code=500, content={"message": f"Resume upload/parse failed: {e}"})

@app.post("/api/search-jobs")
def search_jobs(req: DiscoveryRequest):
    from app.easy_agent.tools import discover_easy_apply_jobs
    try:
        keywords_list = [k.strip() for k in req.keywords.split(",") if k.strip()][:10]
        jobs = discover_easy_apply_jobs(
            target_job_keywords=keywords_list,
            preferred_location=req.location,
            years_of_experience=req.experience
        )
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error searching jobs: {e}"})

async def run_agent_in_background(prompt: str, recipient_email: str):
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from app.agent import root_agent
    
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
        auto_create_session=True,
    )
    
    user_message = types.Content(parts=[types.Part.from_text(text=prompt)])
    events = runner.run_async(
        user_id="fastapi_user",
        session_id="fastapi_session",
        new_message=user_message,
        state_delta={"recipient_email": recipient_email},
    )
    
    async for event in events:
        # We just consume the stream to execute the agent.
        # It handles writing outputs, emails, etc.
        pass

@app.post("/api/run-alert")
def run_alert(req: RunAlertRequest, background_tasks: BackgroundTasks):
    try:
        experience_phrase = f"with experience years range '{req.experience}'" if req.experience != "Any Experience" else "at any experience level"
        frequency_phrase = f"posted in the last '{req.frequency.lower()}' frequency window"
        prompt = f"Find jobs matching keywords '{req.keywords}' in location '{req.location}' {experience_phrase} {frequency_phrase} and email them to {req.recipient}."
        
        background_tasks.add_task(run_agent_in_background, prompt, req.recipient)
        return {"status": "success", "message": "Job alert agent run started in background"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error launching job alert: {e}"})

@app.post("/api/run-apply")
def run_apply(req: ApplyRequest):
    from app.easy_agent.tools import apply_for_job as easy_apply_for_job
    try:
        # Load profile
        profile = None
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                profile = json.load(f)
        
        if not profile:
            return JSONResponse(status_code=400, content={"message": "Please upload resume/configure profile first"})
            
        resume_path = profile.get("personal_info", {}).get("resume_path")
        li_username = os.environ.get("LINKEDIN_USERNAME")
        li_password = os.environ.get("LINKEDIN_PASSWORD")
        
        res = easy_apply_for_job(
            job_url=req.job_url,
            job_title=req.job_title,
            company=req.company,
            candidate_profile=profile,
            resume_path=resume_path,
            li_username=li_username,
            li_password=li_password
        )
        return res
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error running job application: {e}"})

async def run_linkedin_login_background(timeout_seconds: int):
    from app.easy_agent.tools import login_to_linkedin
    try:
        await login_to_linkedin(timeout_seconds=timeout_seconds)
    except Exception:
        pass

@app.post("/api/linkedin/login")
def linkedin_login(background_tasks: BackgroundTasks):
    try:
        # Launch headful Chromium in a background task
        background_tasks.add_task(run_linkedin_login_background, 300)
        return {"status": "success", "message": "Interactive login window launched in background"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error launching login: {e}"})

@app.get("/api/linkedin/status")
async def linkedin_status():
    from app.easy_agent.tools import check_linkedin_session
    try:
        res = await check_linkedin_session()
        return res
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error checking session status: {e}"})

# Serve static screenshots files
screenshots_dir = os.path.join(AGENT_DIR, "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

# Serve React build frontend if it exists
frontend_dist = os.path.abspath(os.path.join(AGENT_DIR, "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
