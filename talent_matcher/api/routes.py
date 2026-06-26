from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import json

# Import database and tools
import memory.db as db
import app.tools as tools
from tools.parser_tool import extract_text_from_bytes

router = APIRouter()

# --- REQUEST SCHEMAS ---

class CandidateRequest(BaseModel):
    name: str
    email: str
    phone: str
    linkedin_url: str
    current_summary: str

class SettingRequest(BaseModel):
    key: str
    value: str

class ResumeVersionRequest(BaseModel):
    candidate_id: int
    version_name: str
    resume_json: dict
    region: str = "Global"

class ATSScoreRequest(BaseModel):
    resume_json: dict

class ApplyChangesRequest(BaseModel):
    resume_json: dict
    approved_suggestions: List[dict]
    candidate_id: int

class RoadmapRequest(BaseModel):
    resume_json: dict
    target_job_desc: str

class GlobalFitRequest(BaseModel):
    resume_json: dict
    region: str
    candidate_id: int

class HiddenSkillsRequest(BaseModel):
    raw_input_text: str
    resume_json: dict

class ShowcaseRequest(BaseModel):
    resume_json: dict

class JobSearchRequest(BaseModel):
    role: str
    location: str
    post_date: str = "past_week"

class JobMatchSingleRequest(BaseModel):
    resume_version_id: int
    job_posting_id: int
    resume_json: dict
    job_desc: str
    job_title: str

class SkillGapRequest(BaseModel):
    resume_json: dict
    target_job_desc: str

class EmailTestRequest(BaseModel):
    host: str
    port: str
    sender: str
    password: str

class EmailSendRequest(BaseModel):
    email_type: str
    candidate_name: str
    recipient: str
    data: List[dict]

class ApplySwarmRequest(BaseModel):
    candidate_name: str
    resume_json: dict
    job: dict

class NegotiateRequest(BaseModel):
    session_id: str
    user_message: str

class TwinQARequest(BaseModel):
    resume_json: dict
    recruiter_question: str

class TwinCoverLetterRequest(BaseModel):
    resume_json: dict
    job_title: str
    company: str
    job_desc: str


# --- SYSTEM ENDPOINTS ---

@router.get("/health")
def health():
    return {
        "status": "online",
        "message": "TalentMatcher next-gen Career Twin backend online",
        "database": db.DATABASE_PATH
    }

@router.post("/system/reset")
def reset_system():
    try:
        db.reset_database()
        return {"success": True, "message": "System database reset successfully."}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/system/audit-logs")
def get_audit_logs():
    return {"logs": db.get_audit_logs()}


# --- SETTINGS & CONFIGS ---

@router.get("/settings/{key}")
def get_setting(key: str):
    return {"key": key, "value": db.get_setting(key)}

@router.post("/settings")
def save_setting(req: SettingRequest):
    db.save_setting(req.key, req.value)
    return {"success": True}


# --- CANDIDATE ENDPOINTS ---

@router.get("/candidate")
def get_candidate():
    candidate = db.get_candidate()
    if not candidate:
        return {"success": False, "message": "No active candidate profile found."}
    return {"success": True, "candidate": candidate}

@router.post("/candidate")
def save_candidate(req: CandidateRequest):
    try:
        cand_id = db.save_candidate(req.name, req.email, req.phone, req.linkedin_url, req.current_summary)
        return {"success": True, "candidate_id": cand_id}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


# --- RESUME CORE & INTELLIGENCE ---

@router.post("/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        raw_text = extract_text_from_bytes(file_bytes, file.filename)
        
        # Parse into structure using Gemini tool
        parsed_data = tools.parse_resume_text(raw_text)
        
        # Auto-save candidate profile
        candidate_id = db.save_candidate(
            name=parsed_data.get("name", "Alex Mercer"),
            email=parsed_data.get("email", "alex.mercer@email.com"),
            phone=parsed_data.get("phone", "+1 (555) 019-2834"),
            linkedin_url=parsed_data.get("linkedin_url", ""),
            current_summary=parsed_data.get("current_summary", "")
        )
        
        # Auto-save original resume version
        version_id = db.save_resume_version(
            candidate_id=candidate_id,
            version_name="Original Uploaded Resume",
            resume_json=parsed_data,
            region="Global"
        )
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "resume_version_id": version_id,
            "resume": parsed_data
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/resume/versions/{candidate_id}")
def get_resume_versions(candidate_id: int):
    return {"versions": db.get_resume_versions(candidate_id)}

@router.get("/resume/versions/{candidate_id}/latest")
def get_latest_resume_version(candidate_id: int):
    ver = db.get_latest_resume_version(candidate_id)
    if not ver:
        return {"success": False, "message": "No resume versions found."}
    return {"success": True, "version": ver}

@router.post("/resume/ats-score")
def get_ats_score(req: ATSScoreRequest):
    try:
        score_report = tools.score_resume_ats(req.resume_json)
        return {"success": True, "report": score_report}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/resume/apply-changes")
def apply_changes(req: ApplyChangesRequest):
    try:
        updated_resume = tools.apply_approved_resume_changes(req.resume_json, req.approved_suggestions)
        
        # Save as a new version
        version_id = db.save_resume_version(
            candidate_id=req.candidate_id,
            version_name=f"ATS Optimized - {datetime.now().strftime('%b %d, %H:%M')}",
            resume_json=updated_resume,
            region="Global"
        )
        
        return {
            "success": True,
            "resume_version_id": version_id,
            "resume": updated_resume
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/resume/roadmap")
def get_future_roadmap(req: RoadmapRequest):
    try:
        roadmap_data = tools.generate_future_roadmap(req.resume_json, req.target_job_desc)
        return {"success": True, "roadmap": roadmap_data}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/resume/global-fit")
def get_global_fit(req: GlobalFitRequest):
    try:
        adapted_resume = tools.adapt_global_fit(req.resume_json, req.region)
        
        # Save as a regional version
        version_id = db.save_resume_version(
            candidate_id=req.candidate_id,
            version_name=f"{req.region} Adapt - {datetime.now().strftime('%b %d, %H:%M')}",
            resume_json=adapted_resume,
            region=req.region
        )
        
        return {
            "success": True,
            "resume_version_id": version_id,
            "resume": adapted_resume
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/resume/hidden-skills")
def get_hidden_skills(req: HiddenSkillsRequest):
    try:
        skills_report = tools.discover_hidden_skills(req.raw_input_text, req.resume_json)
        return {"success": True, "report": skills_report}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/resume/showcase")
def get_showcase(req: ShowcaseRequest):
    try:
        html_code = tools.generate_proof_of_skill_showcase(req.resume_json)
        return {"success": True, "html": html_code}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


# --- JOB DISCOVERY & MATCHING ---

@router.post("/jobs/search")
def search_and_scrape_jobs(req: JobSearchRequest):
    try:
        jobs = tools.search_and_scrapes_jobs(req.role, req.location, req.post_date)
        return {"success": True, "jobs": jobs}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/jobs/matches")
def get_job_matches():
    return {"matches": db.get_match_results()}

@router.post("/jobs/match-single")
def match_single_job(req: JobMatchSingleRequest):
    try:
        # Calculate semantic similarity overlap
        from bs4 import BeautifulSoup
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Simple local semantic calculator to match original logic
        # Clean job desc of html just in case
        clean_desc = BeautifulSoup(req.job_desc, "html.parser").get_text()
        resume_text = json.dumps(req.resume_json)
        
        documents = [resume_text, clean_desc]
        vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        match_score = int(round(similarity * 100))
        
        # Adjust score slightly for tech alignment
        matched_skills = []
        missing_skills = []
        
        skills = req.resume_json.get("skills", [])
        desc_lower = clean_desc.lower()
        for skill in skills:
            if re.search(rf"\b{re.escape(skill.lower())}\b", desc_lower):
                matched_skills.append(skill)
            else:
                # Skill is in resume but not job, or job but not resume?
                pass
                
        # Discover missing skills from job description that candidate doesn't have
        target_skills = ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Redis", "Kafka", "PostgreSQL", "React", "Next.js", "TypeScript", "System Design", "Microservices"]
        for ts in target_skills:
            if re.search(rf"\b{re.escape(ts.lower())}\b", desc_lower):
                if ts not in skills and ts not in matched_skills:
                    missing_skills.append(ts)
                    
        # Limit lists
        matched_skills = list(set(matched_skills))[:10]
        missing_skills = list(set(missing_skills))[:8]
        missing_keywords = [s + " Optimization" for s in missing_skills[:4]]
        
        # Base Match score on overlapping technical skills
        if len(skills) > 0:
            skill_score = int((len(matched_skills) / max(len(matched_skills) + len(missing_skills), 1)) * 100)
            # Weighted combine
            match_score = int((match_score * 0.4) + (skill_score * 0.6))
        match_score = max(min(match_score, 98), 35) # scale safely
        
        # Run ROI calculation
        roi_report = tools.analyze_resume_roi(req.resume_json, req.job_desc, req.job_title)
        
        # Run Searchability audit
        audit_report = tools.audit_resume_searchability(req.resume_json)
        roi_report["searchability_score"] = audit_report["searchability_index"]
        
        # Save match result in DB
        db.save_match_result(
            resume_version_id=req.resume_version_id,
            job_posting_id=req.job_posting_id,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            missing_keywords=missing_keywords,
            roi_metadata=roi_report
        )
        
        return {
            "success": True,
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "missing_keywords": missing_keywords,
            "roi": roi_report
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/jobs/skill-gap")
def get_skill_gap_plan(req: SkillGapRequest):
    try:
        plan = tools.build_skill_gap_plan(req.resume_json, req.target_job_desc)
        return {"success": True, "plan": plan}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


# --- EMAILING ENDPOINTS ---

@router.post("/email/test")
def test_smtp(req: EmailTestRequest):
    res = test_smtp_connection(req.host, req.port, req.sender, req.password)
    return res

@router.post("/email/send")
def send_email(req: EmailSendRequest):
    res = tools.prepare_and_send_email_alerts(
        email_type=req.email_type,
        candidate_name=req.candidate_name,
        recipient=req.recipient,
        data=req.data
    )
    return res


# --- APPLICATION CO-PILOTS & SWARMS ---

@router.post("/apply/swarm")
def run_apply_swarm(req: ApplySwarmRequest):
    try:
        swarm_result = tools.simulate_apply_swarm(req.candidate_name, req.resume_json, req.job)
        return {"success": True, "swarm": swarm_result}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/apply/logs")
def get_apply_logs():
    return {"logs": db.get_application_logs()}

@router.post("/apply/negotiate")
def negotiate(req: NegotiateRequest):
    try:
        negotiation_report = tools.salary_negotiation_turn(req.session_id, "Recruiter", req.user_message)
        return {"success": True, "negotiation": negotiation_report}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/apply/negotiate/{session_id}")
def get_negotiation_turns(session_id: str):
    return {"turns": db.get_interview_turns(session_id)}

@router.delete("/apply/negotiate/{session_id}")
def clear_negotiation(session_id: str):
    db.clear_interview_turns(session_id)
    db.add_audit_log("NEGOTIATION_CLEARED", f"Salary negotiation session {session_id} cleared.")
    return {"success": True}


# --- DIGITAL TWIN ENDPOINTS ---

@router.post("/twin/qa")
def ask_digital_twin(req: TwinQARequest):
    try:
        answer = tools.digital_twin_qa(req.resume_json, req.recruiter_question)
        return {"success": True, "answer": answer}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@router.post("/twin/cover-letter")
def generate_cover_letter(req: TwinCoverLetterRequest):
    try:
        letter = tools.generate_twin_cover_letter(req.resume_json, req.job_title, req.company, req.job_desc)
        return {"success": True, "cover_letter": letter}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
