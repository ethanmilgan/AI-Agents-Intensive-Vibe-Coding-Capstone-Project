import streamlit as st
import requests
import re
import os
import json
import io
import time
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Load Application Resource Configurations
def load_resources_config(filename="resources.properties"):
    config = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config

app_resources = load_resources_config()
BACKEND_URL = app_resources.get("backendUrl", "http://localhost:8000")
API_KEY = app_resources.get("apiKey", "")

def get_auth_headers():
    return {"X-API-Key": API_KEY} if API_KEY else {}

# Test backend connection
backend_online = False
try:
    res = requests.get(f"{BACKEND_URL}/health", headers=get_auth_headers(), timeout=2)
    if res.status_code == 200:
        backend_online = True
except Exception:
    backend_online = False

def get_backend_setting(key, default=""):
    if backend_online:
        try:
            res = requests.get(f"{BACKEND_URL}/settings/{key}", headers=get_auth_headers(), timeout=2)
            if res.status_code == 200:
                val = res.json().get("value")
                if val is not None:
                    return val
        except Exception:
            pass
    return default

def generate_local_mock_jobs(role, location):
    companies = ["Stripe", "Google", "Meta", "Netflix", "Amazon"]
    jobs = []
    for idx, company in enumerate(companies):
        score = 85 - (idx * 12)
        job_id = f"JD-{company[:3].upper()}-{100 + idx}"
        jobs.append({
            "job_id": job_id,
            "title": f"Senior {role}",
            "company": company,
            "location": location,
            "url": f"https://{company.lower()}.com/careers",
            "description": f"We are seeking an exceptional engineer to design and scale our services in {location}. You will collaborate with team members to build highly performant applications.",
            "source": "LocalMock",
            "match_score": score,
            "missing_skills": ["Kubernetes", "Docker"] if score < 80 else [],
            "missing_keywords": ["Containerization"] if score < 80 else [],
            "roi": {
                "salary_range": "$125,000 - $145,000",
                "interview_probability": score,
                "hiring_chances": "High" if score >= 80 else "Medium"
            },
            "db_id": idx + 1
        })
    return jobs


# Document Generation Utility
def generate_tailored_docx(name, email, phone, job_title, skills, summary, experience):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Arial'
    font.size = Pt(11)
    
    # Candidate Name
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_name = p_name.add_run(name)
    run_name.bold = True
    run_name.font.size = Pt(20)
    
    # Contact
    p_contact = doc.add_paragraph()
    p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_contact.add_run(f"{email}  |  {phone}  |  Target Role: {job_title}\n")
    
    # Summary
    p_sum_h = doc.add_paragraph()
    r_sum_h = p_sum_h.add_run("PROFESSIONAL SUMMARY")
    r_sum_h.bold = True
    r_sum_h.font.size = Pt(12)
    doc.add_paragraph(summary)
    doc.add_paragraph()
    
    # Skills
    p_skills_h = doc.add_paragraph()
    r_skills_h = p_skills_h.add_run("KEY COMPETENCIES & TECHNICAL SKILLS")
    r_skills_h.bold = True
    r_skills_h.font.size = Pt(12)
    p_skills = doc.add_paragraph()
    p_skills.add_run(" • ".join(skills))
    doc.add_paragraph()
    
    # Experience
    p_exp_h = doc.add_paragraph()
    r_exp_h = p_exp_h.add_run("PROFESSIONAL EXPERIENCE")
    r_exp_h.bold = True
    r_exp_h.font.size = Pt(12)
    
    for exp in experience:
        if not exp.get('role', '').strip() or not exp.get('company', '').strip():
            continue
        p_item = doc.add_paragraph()
        r_item_title = p_item.add_run(f"{exp['role']} — {exp['company']}")
        r_item_title.bold = True
        p_item.add_run(f"\n{exp.get('dates', '')}")
        
        for bullet in exp.get('bullets', []):
            if bullet.strip():
                doc.add_paragraph(bullet, style='List Bullet')
        doc.add_paragraph()
        
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# Page Configuration for Premium Look
st.set_page_config(
    page_title="Career Twin AI - Next-Gen Career Suite",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium High-Contrast Cyber CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@400;500;700&display=swap');
    
    /* Pitch-Black Obsidian Background */
    .stApp {
        background-color: #040406 !important;
        color: #f1f5f9 !important;
    }
    
    /* Override Streamlit headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    p, li, span, label, div {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Translucent Cyber Cards with Solid Neon Outlines */
    .cyber-card {
        background-color: #0d0d15 !important;
        border: 1px solid rgba(167, 139, 250, 0.25) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.6) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .cyber-card:hover {
        border-color: #06b6d4 !important;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.25) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Left Accent Border Bars */
    .accent-card-purple {
        border-left: 4px solid #a78bfa !important;
    }
    .accent-card-cyan {
        border-left: 4px solid #06b6d4 !important;
    }
    .accent-card-emerald {
        border-left: 4px solid #10b981 !important;
    }
    .accent-card-coral {
        border-left: 4px solid #f43f5e !important;
    }
    
    /* Glowing Inputs */
    div.stTextInput > div > div > input, div.stTextArea > div > div > textarea, div.stSelectbox > div > div > div {
        background-color: #08080d !important;
        color: #ffffff !important;
        border: 1px solid rgba(167, 139, 250, 0.25) !important;
        border-radius: 8px !important;
    }
    div.stTextInput > div > div > input:focus, div.stTextArea > div > div > textarea:focus {
        border-color: #06b6d4 !important;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.4) !important;
    }
    
    /* High-contrast Pill badges */
    .cyber-pill {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin-right: 8px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .pill-cyan {
        background-color: rgba(6, 182, 212, 0.12);
        color: #06b6d4;
        border: 1px solid rgba(6, 182, 212, 0.35);
    }
    .pill-purple {
        background-color: rgba(167, 139, 250, 0.12);
        color: #a78bfa;
        border: 1px solid rgba(167, 139, 250, 0.35);
    }
    .pill-emerald {
        background-color: rgba(16, 185, 129, 0.12);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .pill-coral {
        background-color: rgba(244, 63, 94, 0.12);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.35);
    }
    
    /* Pulsing Status Indicators */
    .pulse-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        animation: pulse-anim 1.8s infinite ease-in-out;
        margin-right: 8px;
        vertical-align: middle;
    }
    .pulse-green {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }
    .pulse-blue {
        background-color: #06b6d4;
        box-shadow: 0 0 8px #06b6d4;
    }
    .pulse-purple {
        background-color: #a78bfa;
        box-shadow: 0 0 8px #a78bfa;
    }
    .pulse-grey {
        background-color: #475569;
        box-shadow: none;
        animation: none;
    }
    @keyframes pulse-anim {
        0% { transform: scale(0.9); opacity: 0.6; }
        50% { transform: scale(1.15); opacity: 1; }
        100% { transform: scale(0.9); opacity: 0.6; }
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 14px rgba(167, 139, 250, 0.35) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(167, 139, 250, 0.5) !important;
        border-color: #06b6d4 !important;
    }
    
    /* Chat Bubble styling */
    .chat-bubble {
        padding: 15px 20px;
        border-radius: 16px;
        margin-bottom: 12px;
        line-height: 1.5;
        max-width: 80%;
    }
    .chat-user {
        background-color: rgba(167, 139, 250, 0.15);
        border: 1px solid rgba(167, 139, 250, 0.3);
        color: #f1f5f9;
        margin-left: auto;
        border-bottom-right-radius: 2px;
    }
    .chat-agent {
        background-color: rgba(6, 182, 212, 0.12);
        border: 1px solid rgba(6, 182, 212, 0.3);
        color: #ffffff;
        margin-right: auto;
        border-bottom-left-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "candidate" not in st.session_state:
    st.session_state.candidate = None
if "resume_json" not in st.session_state:
    st.session_state.resume_json = None
if "candidate_id" not in st.session_state:
    st.session_state.candidate_id = None
if "resume_version_id" not in st.session_state:
    st.session_state.resume_version_id = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌌 Career Twin Hub"
if "interview_chat" not in st.session_state:
    st.session_state.interview_chat = []
if "negotiation_chat" not in st.session_state:
    st.session_state.negotiation_chat = []
if "negotiation_coach" not in st.session_state:
    st.session_state.negotiation_coach = {"recruiter_response": "Hello, we are thrilled to extend an offer to join our team as a Senior Software Engineer. The base salary we have allocated is $112,000. Let me know if you are ready to sign.", "coach_feedback": "Welcome to the Salary Negotiator Copilot. Click 'Coach Tips' to see real-time suggestions.", "suggested_script": "Start by thanking them for the offer and expressing excitement, then anchor your counter-offer professionally."}

# Load candidate profile from database if online
if backend_online and not st.session_state.candidate:
    try:
        c_res = requests.get(f"{BACKEND_URL}/candidate", headers=get_auth_headers())
        if c_res.status_code == 200:
            c_data = c_res.json()
            if c_data.get("success"):
                st.session_state.candidate = c_data["candidate"]
                st.session_state.candidate_id = c_data["candidate"]["id"]
                # Fetch latest resume
                v_res = requests.get(f"{BACKEND_URL}/resume/versions/{st.session_state.candidate_id}/latest", headers=get_auth_headers())
                if v_res.status_code == 200:
                    v_data = v_res.json()
                    if v_data.get("success"):
                        st.session_state.resume_json = v_data["version"]["resume_json"]
                        st.session_state.resume_version_id = v_data["version"]["id"]
    except Exception:
        pass

# Authentication Screen
def show_login_page():
    st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
    st.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=96)
    st.markdown("<h1 style='font-family: Outfit; font-size: 46px; letter-spacing: -1.5px; background: linear-gradient(135deg, #a78bfa 0%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>CAREER TWIN AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 16px; margin-bottom: 40px;'>Continuous Career Growth, Intelligent Optimizations & Swarm Applications</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    cols = st.columns([1, 1.6, 1])
    with cols[1]:
        st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Portal Login</h3>", unsafe_allow_html=True)
            email = st.text_input("Username/Email", placeholder="candidate@careertwin.ai")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Access Portal")
            
            if submit:
                if email.strip() and len(password) >= 6:
                    st.session_state.authenticated = True
                    st.session_state.username = email
                    st.success("Successfully authenticated!")
                    st.rerun()
                else:
                    st.error("Invalid input. (Enter any email and a password of at least 6 characters for demo access).")
        st.markdown('</div>', unsafe_allow_html=True)

# Main Application Layout
def show_dashboard():
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
            <div style='text-align: center; margin-bottom: 10px;'>
                <h2 style='font-family: Outfit; font-size: 24px; margin-bottom: 5px; color: #a78bfa;'>🌌 Career Twin</h2>
                <code style='color: #06b6d4; font-size: 13px;'>{st.session_state.username}</code>
            </div>
        """, unsafe_allow_html=True)
        
        # Telemetry lights
        st.markdown("---")
        status_color = "pulse-green" if backend_online else "pulse-grey"
        status_text = "Backend Sync Active" if backend_online else "Demo Offline Mode"
        
        st.markdown(f"""
            <div style="padding: 10px 15px; background-color: #0d0d15; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 15px;">
                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; margin-bottom: 5px; font-weight: bold;">Twin Agent Status</div>
                <div style="font-size: 13px; font-weight: bold; color: #ffffff;">
                    <span class="pulse-dot {status_color}"></span> {status_text}
                </div>
                <div style="font-size: 12px; margin-top: 8px; color: #94a3b8;">
                    🟢 Coordinator: <span style="color:#10b981;">Online</span><br>
                    🔵 Resume Agent: <span style="color:#06b6d4;">Online</span><br>
                    🔵 Job Intel Swarm: <span style="color:#a78bfa;">Ready</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu
        menu_items = [
            "🌌 Career Twin Hub",
            "📄 Resume Intelligence",
            "🗣️ Interview-to-Resume",
            "🧠 Recruiter Simulation",
            "📈 Resume ROI & Global Fit",
            "🔍 Job Discovery & Swarm",
            "🛠️ Skill Gap & Future Roadmaps",
            "🤖 Digital Twin & Negotiation",
            "🔄 Auto-Upgrade & Showcase",
            "⚙️ System Settings"
        ]
        
        st.markdown("<div style='font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: bold; margin-bottom: 5px; padding-left: 5px;'>Workspaces</div>", unsafe_allow_html=True)
        
        for item in menu_items:
            # Highlight active item using streamlit button
            btn_style = "primary" if st.session_state.active_tab == item else "secondary"
            if st.button(item, use_container_width=True, key=f"nav_{item}"):
                st.session_state.active_tab = item
                st.rerun()
                
        st.markdown("---")
        if st.button("🚪 Logout Portal", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.candidate = None
            st.session_state.resume_json = None
            st.rerun()

    # Active Workspace Router
    active = st.session_state.active_tab
    
    # ----------------------------------------------------
    # VIEW 1: CAREER TWIN HUB
    # ----------------------------------------------------
    if active == "🌌 Career Twin Hub":
        st.markdown("<h1>🌌 Career Twin Agent Workspace</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>The central command center for your digital career twin. It monitors achievements, searches jobs, and manages continuous development loops.</p>", unsafe_allow_html=True)
        
        # Dashboard Cards
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.session_state.candidate["name"] if st.session_state.candidate else "Alex Mercer"
            st.markdown(f"""
                <div class="cyber-card accent-card-purple" style="min-height: 180px;">
                    <div style="font-size: 12px; text-transform: uppercase; color: #a78bfa; font-weight: bold; margin-bottom: 10px;">Active Candidate Twin</div>
                    <h2 style="margin: 0; font-size: 26px;">{name}</h2>
                    <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px;">LinkedIn Reference Connected</p>
                    <div style="margin-top: 25px; font-size: 13px; color: #10b981; font-weight: bold;">✔ Continuous Sync Active</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            ver_name = "Original Upload"
            skills_count = 8
            if st.session_state.resume_json:
                skills_count = len(st.session_state.resume_json.get("skills", []))
                # Get latest version name
                if backend_online:
                    try:
                        v_res = requests.get(f"{BACKEND_URL}/resume/versions/{st.session_state.candidate_id}", headers=get_auth_headers())
                        if v_res.status_code == 200:
                            vers = v_res.json().get("versions", [])
                            if vers:
                                ver_name = vers[0]["version_name"]
                    except Exception:
                        pass
            st.markdown(f"""
                <div class="cyber-card accent-card-cyan" style="min-height: 180px;">
                    <div style="font-size: 12px; text-transform: uppercase; color: #06b6d4; font-weight: bold; margin-bottom: 10px;">Resume Version</div>
                    <h2 style="margin: 0; font-size: 20px; color:#ffffff;">{ver_name}</h2>
                    <p style="margin: 10px 0 0 0; color: #94a3b8; font-size: 14px;"><strong>Verified Skills:</strong> {skills_count} Technical Tags</p>
                    <div style="margin-top: 20px; font-size: 13px; color: #06b6d4; font-weight: bold;">ℹ Multi-regional templates built</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c3:
            # Fetch application count
            app_count = 0
            if backend_online:
                try:
                    a_res = requests.get(f"{BACKEND_URL}/apply/logs", headers=get_auth_headers())
                    if a_res.status_code == 200:
                        app_count = len(a_res.json().get("logs", []))
                except Exception:
                    pass
            st.markdown(f"""
                <div class="cyber-card accent-card-emerald" style="min-height: 180px;">
                    <div style="font-size: 12px; text-transform: uppercase; color: #10b981; font-weight: bold; margin-bottom: 10px;">Apply Swarm Traffic</div>
                    <h2 style="margin: 0; font-size: 38px; color:#10b981;">{app_count}</h2>
                    <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px;">Active Swarm submissions logged</p>
                    <div style="margin-top: 15px; font-size: 13px; color: #a78bfa; font-weight: bold;">✈ 1-Click apply swarm enabled</div>
                </div>
            """, unsafe_allow_html=True)
            
        # Autonomous Career loop telemetry panel
        st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
        st.markdown("<h3>🔁 Continuous Career Twin Sync Loop</h3>", unsafe_allow_html=True)
        st.write("This autonomous service monitors your Github commits and course completions, discovers latent skills, upgrades your active profile, sweeps the job market, calculates hiring probabilities, and queues highly qualified applications automatically.")
        
        loop_col1, loop_col2 = st.columns([2, 1])
        with loop_col1:
            st.info("💡 **Active Strategy:** Sweeping US and Remote Software Engineer markets for jobs above an **80% match threshold**.")
        with loop_col2:
            st.button("⚡ Trigger Manual Sync Loop", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # System Audit Logs
        st.markdown("<h3>📜 System Audit Trails</h3>", unsafe_allow_html=True)
        if backend_online:
            try:
                logs_res = requests.get(f"{BACKEND_URL}/system/audit-logs", headers=get_auth_headers())
                if logs_res.status_code == 200:
                    logs = logs_res.json().get("logs", [])
                    if logs:
                        for log in logs[:8]:
                            st.markdown(f"⏱ `[{log['timestamp'].split('T')[1][:8]}]` **{log['event_type']}**: {log['details']}")
                    else:
                        st.write("No audit logs recorded yet.")
            except Exception:
                st.error("Could not fetch audit logs.")
        else:
            # Fallback mock logs
            st.markdown("⏱ `[14:15:32]` **CANDIDATE_UPDATE**: Candidate profile updated for Alex Mercer.")
            st.markdown("⏱ `[14:15:33]` **RESUME_VERSION_CREATED**: Resume version 'Original Uploaded Resume' (Global) created.")
            st.markdown("⏱ `[14:18:22]` **SYSTEM_RESET**: Database reset and re-initialized successfully.")

    # ----------------------------------------------------
    # VIEW 2: RESUME INTELLIGENCE
    # ----------------------------------------------------
    elif active == "📄 Resume Intelligence":
        st.markdown("<h1>📄 Resume Intake, Parser & ATS Auditor</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Upload your raw resume, parse it into structured JSON, and audit its ATS readiness.</p>", unsafe_allow_html=True)
        
        col_in, col_out = st.columns([1.2, 1.8], gap="large")
        
        with col_in:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>Upload Credentials</h3>", unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("Upload PDF, DOCX or TXT Resume", type=["pdf", "docx", "txt"])
            linkedin_url = st.text_input("LinkedIn Profile URL", placeholder="https://linkedin.com/in/username")
            
            can_parse = uploaded_file is not None
            parse_btn = st.button("Parse & Score Resume", disabled=not can_parse, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_out:
            if parse_btn and uploaded_file:
                with st.spinner("Extracting tokens, parsing structure, and auditing ATS score..."):
                    if backend_online:
                        try:
                            # Parse resume
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                            p_res = requests.post(f"{BACKEND_URL}/resume/parse", files=files, headers=get_auth_headers())
                            if p_res.status_code == 200:
                                p_data = p_res.json()
                                st.session_state.resume_json = p_data["resume"]
                                st.session_state.resume_version_id = p_data["resume_version_id"]
                                # Fetch candidate
                                c_res = requests.get(f"{BACKEND_URL}/candidate", headers=get_auth_headers())
                                if c_res.status_code == 200:
                                    st.session_state.candidate = c_res.json().get("candidate")
                                    st.session_state.candidate_id = st.session_state.candidate["id"]
                        except Exception as e:
                            st.error(f"Failed to parse resume: {str(e)}")
                    else:
                        # Offline fallback simulation
                        time.sleep(1.5)
                        st.session_state.resume_json = {
                            "name": "Alex Mercer",
                            "email": "alex.mercer@email.com",
                            "phone": "+1 (555) 019-2834",
                            "linkedin_url": linkedin_url,
                            "current_summary": "Accomplished software engineer with a strong track record of developing scalable backend services, optimizing databases, and integrating systems.",
                            "skills": ["Python", "JavaScript", "SQL", "Git", "Docker", "REST APIs", "AWS"],
                            "experience": [
                                {
                                    "role": "Software Engineer",
                                    "company": "Tech Solutions Inc.",
                                    "dates": "2023 - Present",
                                    "bullets": [
                                        "Architected system components integrating Python and SQL yielding a 20% latency improvement.",
                                        "Maintained and optimized database queries reducing API call delays by 15%."
                                    ]
                                }
                            ]
                        }
                
                st.success("🎉 Resume parsed successfully and saved to Career Twin database!")
                
            # Display results if available
            if st.session_state.resume_json:
                st.markdown('<div class="cyber-card accent-card-cyan">', unsafe_allow_html=True)
                st.markdown("<h3>Audit Report</h3>", unsafe_allow_html=True)
                
                # Fetch ATS score
                score_data = None
                if backend_online:
                    try:
                        score_res = requests.post(
                            f"{BACKEND_URL}/resume/ats-score", 
                            json={"resume_json": st.session_state.resume_json}, 
                            headers=get_auth_headers()
                        )
                        if score_res.status_code == 200:
                            score_data = score_res.json().get("report")
                    except Exception:
                        pass
                
                if not score_data:
                    # Fallback score report
                    score_data = {
                        "overall_score": 72,
                        "breakdown": {"formatting": 80, "keywords": 65, "impact": 60, "structure": 85},
                        "suggestions": [
                            {"category": "Impact", "issue": "Bullet points lack business metrics.", "fix": "Quantify achievements (e.g. 'reduced latency by 20%')"},
                            {"category": "Keywords", "issue": "Competency matrix lacks cloud depth.", "fix": "Add technical tags like AWS, Kubernetes, or CI/CD."}
                        ]
                    }
                
                sc1, sc2 = st.columns([1, 2])
                with sc1:
                    st.markdown(f"""
                        <div style="text-align: center; padding: 20px; background-color: #040406; border-radius: 12px; border: 1px solid rgba(167, 139, 250, 0.2);">
                            <div style="font-size: 13px; text-transform: uppercase; color: #94a3b8; font-weight: bold;">ATS Score</div>
                            <div style="font-size: 56px; font-weight: 800; color: #a78bfa; margin: 10px 0; text-shadow: 0 0 10px rgba(167, 139, 250, 0.4);">{score_data['overall_score']}%</div>
                            <div style="font-size: 12px; color: #10b981;">✔ Ready for screening</div>
                        </div>
                    """, unsafe_allow_html=True)
                with sc2:
                    st.markdown("##### Category Breakdown")
                    st.markdown(f"📐 **Formatting & Layout:** `{score_data['breakdown']['formatting']}%`")
                    st.markdown(f"🔑 **Keyword Density:** `{score_data['breakdown']['keywords']}%`")
                    st.markdown(f"💥 **Impact & Metrics:** `{score_data['breakdown']['impact']}%`")
                    st.markdown(f"🧱 **Structural Profile:** `{score_data['breakdown']['structure']}%`")
                
                st.markdown("##### Actionable Optimizations")
                for sug in score_data["suggestions"]:
                    st.markdown(f"⚠️ **{sug['category']} Gaps:** {sug['issue']} <br><span style='color: #06b6d4;'>💡 Fix: {sug['fix']}</span>", unsafe_allow_html=True)
                
                # Show optimize button
                st.markdown("---")
                opt_col1, opt_col2 = st.columns([2, 1])
                with opt_col1:
                    st.write("Let the Resume Agent apply these optimizations truthfully, incorporating metrics and keywords.")
                with opt_col2:
                    if st.button("⚡ Apply ATS Optimizations", use_container_width=True):
                        with st.spinner("Rewriting bullet points and injecting keywords..."):
                            if backend_online:
                                try:
                                    opt_res = requests.post(
                                        f"{BACKEND_URL}/resume/apply-changes",
                                        json={
                                            "resume_json": st.session_state.resume_json,
                                            "approved_suggestions": score_data["suggestions"],
                                            "candidate_id": st.session_state.candidate_id
                                        },
                                        headers=get_auth_headers()
                                    )
                                    if opt_res.status_code == 200:
                                        st.session_state.resume_json = opt_res.json()["resume"]
                                        st.session_state.resume_version_id = opt_res.json()["resume_version_id"]
                                        st.success("Optimized resume version saved! Projected ATS Score boosted to 88%!")
                                        st.rerun()
                                except Exception as ex:
                                    st.error(f"Optimization failed: {str(ex)}")
                            else:
                                time.sleep(1)
                                # Optimize fallback
                                st.session_state.resume_json["skills"].extend(["Docker", "AWS"])
                                if len(st.session_state.resume_json["experience"]) > 0:
                                    st.session_state.resume_json["experience"][0]["bullets"][0] += " resulting in a 25% throughput improvement."
                                st.success("Optimized resume version saved locally! Projected ATS Score boosted to 88%!")
                                st.rerun()
                
                # Show parsed details
                with st.expander("Preview structured resume data"):
                    st.json(st.session_state.resume_json)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='text-align: center; padding: 80px 20px; border: 1px dashed rgba(167, 139, 250, 0.2); border-radius: 12px; background-color: #0d0d15;'>
                        <h4 style='color: #64748b;'>Awaiting Resume Upload</h4>
                        <p style='color: #475569; font-size: 14px;'>Upload your PDF or DOCX resume to extract data and audit ATS readiness.</p>
                    </div>
                """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 3: INTERVIEW TO RESUME
    # ----------------------------------------------------
    elif active == "🗣️ Interview-to-Resume":
        st.markdown("<h1>🗣️ Interview-to-Resume Agent</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Conduct a voice/chat interview with our Career Twin Agent to build a professional resume from scratch without typing your resume yourself.</p>", unsafe_allow_html=True)
        
        st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
        st.markdown("<h3>🗣️ Interactive Interview Panel</h3>", unsafe_allow_html=True)
        st.write("Answer the interview questions below. The Resume Agent will extract your achievements, technologies, and metrics, then automatically assemble your profile.")
        
        # Chat interface
        chat_container = st.container()
        with chat_container:
            # Display existing chat
            if not st.session_state.interview_chat:
                st.session_state.interview_chat.append({
                    "role": "agent",
                    "message": "Hello! I am your Resume Agent. Let's build your professional resume. To start, what is your full name, and what target job title are you aiming for?"
                })
                
            for msg in st.session_state.interview_chat:
                bubble_class = "chat-user" if msg["role"] == "user" else "chat-agent"
                st.markdown(f'<div class="chat-bubble {bubble_class}">{msg["message"]}</div>', unsafe_allow_html=True)
                
        # Send message form
        with st.form("chat_form", clear_on_submit=True):
            user_msg = st.text_input("Your Response", placeholder="Type your answer here...")
            c_send, c_clear, c_build = st.columns([1, 1, 2])
            with c_send:
                send_btn = st.form_submit_button("Send Response")
            with c_clear:
                clear_btn = st.form_submit_button("Reset Chat")
            with c_build:
                build_btn = st.form_submit_button("⚡ Synthesize Resume Now")
                
            if send_btn and user_msg.strip():
                # Add user turn
                st.session_state.interview_chat.append({"role": "user", "message": user_msg})
                
                # Simple scripted dialog simulator
                turns = [m for m in st.session_state.interview_chat if m["role"] == "user"]
                if len(turns) == 1:
                    reply = "Excellent. Next, tell me about your work experience. What companies have you worked at, what were your roles, and what is one major technical achievement you are proud of?"
                elif len(turns) == 2:
                    reply = "Got it. What technical skills, programming languages, cloud systems, and tools do you work with on a daily basis?"
                elif len(turns) == 3:
                    reply = "Great. Finally, what is your educational background, and do you have any certifications or personal projects you would like featured?"
                else:
                    reply = "Thank you! I have gathered enough intelligence to build your resume. Click the 'Synthesize Resume Now' button to compile your professional profile!"
                    
                st.session_state.interview_chat.append({"role": "agent", "message": reply})
                st.rerun()
                
            if clear_btn:
                st.session_state.interview_chat = []
                st.rerun()
                
            if build_btn:
                with st.spinner("Synthesizing Achievements and Compiling Resume..."):
                    # Mocking interview synthesis
                    time.sleep(2)
                    # Extract name from first turn
                    user_turns = [m["message"] for m in st.session_state.interview_chat if msg["role"] == "user"]
                    extracted_name = "Alex Mercer"
                    if user_turns:
                        name_match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+)", user_turns[0])
                        if name_match:
                            extracted_name = name_match.group(1)
                            
                    st.session_state.resume_json = {
                        "name": extracted_name,
                        "email": "candidate@talentai-portal.com",
                        "phone": "+1 (555) 019-2834",
                        "linkedin_url": "",
                        "current_summary": "Highly motivated engineering professional with a comprehensive understanding of software development lifecycle methodologies and cloud integrations.",
                        "skills": ["Python", "SQL", "Git", "REST APIs", "AWS", "Docker", "JavaScript"],
                        "experience": [
                            {
                                "role": "Software Engineer",
                                "company": "Enterprise Tech Corp",
                                "dates": "2023 - Present",
                                "bullets": [
                                    "Successfully engineered core backend API features using Python and relational databases.",
                                    "Collaborated within cross-functional agile teams to deliver features on schedule."
                                ]
                            }
                        ],
                        "projects": [
                            {
                                "title": "Interactive Client Portal",
                                "description": "Developed a secure web dashboard leveraging modern programming frameworks and databases."
                            }
                        ],
                        "education": [
                            {
                                "degree": "Bachelor of Science in Information Technology",
                                "institution": "State Tech College",
                                "year": "2022"
                            }
                        ]
                    }
                    st.success("🎉 Resume successfully synthesized from interview! Redirecting to Resume Intelligence workspace...")
                    time.sleep(1.5)
                    st.session_state.active_tab = "📄 Resume Intelligence"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 4: RECRUITER SIMULATION
    # ----------------------------------------------------
    elif active == "🧠 Recruiter Simulation":
        st.markdown("<h1>🧠 Multi-Recruiter Simulation Agent</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Simulate how recruiters evaluate your resume against a target job and predict rejection reasons before you apply.</p>", unsafe_allow_html=True)
        
        if not st.session_state.resume_json:
            st.warning("⚠️ Please upload and parse your resume in the 'Resume Intelligence' workspace first.")
            return
            
        c1, c2 = st.columns([1.2, 1.8], gap="large")
        with c1:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>Simulation Target</h3>", unsafe_allow_html=True)
            sim_job_id = st.text_input("Target Job ID / Code", "JD-MGR-2026")
            sim_job_desc = st.text_area("Paste Job Description Requirements", height=250, placeholder="Requirements, qualifications, and core duties...")
            
            run_sim = st.button("⚡ Run Recruiter Simulation", disabled=len(sim_job_desc) < 20, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            if run_sim:
                with st.spinner("Orchestrating recruiter personas and gathering feedback..."):
                    # Call Gemini to simulate three recruiter personas
                    recruiter_feedback = None
                    if backend_online:
                        try:
                            # Use Gemini to generate personas feedback
                            model = get_gemini_model()
                            prompt = f"""
                            You are simulating three distinct recruiter personas evaluating a candidate's resume against a target job description:
                            1. **HR Screener (Sarah):** Focuses on career gaps, structure, keywords, and job tenure.
                            2. **Technical Tech Lead (Dave):** Focuses on technology depth, system architecture, tools, and code quality indicators.
                            3. **VP of Engineering (Marcus):** Focuses on leadership capability, scale of projects, business impact, and strategic alignment.
                            
                            Candidate Resume:
                            {json.dumps(st.session_state.resume_json, indent=2)}
                            
                            Target Job Description:
                            {sim_job_desc}
                            
                            Generate simulated feedback from each persona. Format response as a JSON matching this schema:
                            {{
                                "sarah": {{
                                    "score": 85,
                                    "feedback": "Feedback text",
                                    "risk": "Risk level"
                                }},
                                "dave": {{
                                    "score": 60,
                                    "feedback": "Feedback text",
                                    "risk": "Risk level"
                                }},
                                "marcus": {{
                                    "score": 70,
                                    "feedback": "Feedback text",
                                    "risk": "Risk level"
                                }}
                            }}
                            Provide raw JSON only. Do not wrap in markdown.
                            """
                            res = model.generate_content(prompt)
                            cleaned = clean_llm_json(res.text)
                            recruiter_feedback = json.loads(cleaned)
                        except Exception:
                            pass
                            
                    if not recruiter_feedback:
                        # Fallback recruiter feedback
                        time.sleep(1.5)
                        recruiter_feedback = {
                            "sarah": {
                                "score": 88,
                                "feedback": "Structure looks clean. Excellent keyword alignment for Python and SQL. Job tenure is stable with no gaps.",
                                "risk": "Low risk. Recommend moving to technical review."
                            },
                            "dave": {
                                "score": 62,
                                "feedback": "Demonstrates solid basic software practices, but backend optimization metrics are vague. No evidence of system design at scale, Kubernetes, or automated pipelines which are crucial for this role.",
                                "risk": "Medium risk. Gaps in DevOps/Infrastructure tools."
                            },
                            "marcus": {
                                "score": 68,
                                "feedback": "Good engineering focus, but achievements lack business context. Gaps in team leadership, budget scale, and strategic ownership.",
                                "risk": "Medium risk. Lacks clear senior leadership indicators."
                            }
                        }
                        
                st.success("🎉 Recruiter simulation completed!")
                
                # Display Sarah (HR)
                st.markdown(f"""
                    <div class="cyber-card accent-card-purple">
                        <h4 style="margin:0;"><span class="cyber-pill pill-purple">HR Screener</span> Sarah's Audit Log (Score: {recruiter_feedback['sarah']['score']}/100)</h4>
                        <p style="margin: 10px 0; font-style: italic; color: #f1f5f9;">"{recruiter_feedback['sarah']['feedback']}"</p>
                        <div style="font-size: 13px; font-weight: bold; color: #10b981;">👉 Recommendation: {recruiter_feedback['sarah']['risk']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display Dave (Tech Lead)
                st.markdown(f"""
                    <div class="cyber-card accent-card-cyan">
                        <h4 style="margin:0;"><span class="cyber-pill pill-cyan">Tech Lead</span> Dave's Audit Log (Score: {recruiter_feedback['dave']['score']}/100)</h4>
                        <p style="margin: 10px 0; font-style: italic; color: #f1f5f9;">"{recruiter_feedback['dave']['feedback']}"</p>
                        <div style="font-size: 13px; font-weight: bold; color: #f43f5e;">👉 Technical Risk: {recruiter_feedback['dave']['risk']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display Marcus (VP)
                st.markdown(f"""
                    <div class="cyber-card accent-card-coral">
                        <h4 style="margin:0;"><span class="cyber-pill pill-coral">VP of Engineering</span> Marcus's Audit Log (Score: {recruiter_feedback['marcus']['score']}/100)</h4>
                        <p style="margin: 10px 0; font-style: italic; color: #f1f5f9;">"{recruiter_feedback['marcus']['feedback']}"</p>
                        <div style="font-size: 13px; font-weight: bold; color: #f59e0b;">👉 Strategic Risk: {recruiter_feedback['marcus']['risk']}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='text-align: center; padding: 100px 20px; border: 1px dashed rgba(167, 139, 250, 0.2); border-radius: 12px; background-color: #0d0d15;'>
                        <h4 style='color: #64748b;'>Awaiting Simulation Setup</h4>
                        <p style='color: #475569; font-size: 14px;'>Paste the target job description requirements on the left and run simulation to read recruiter persona logs.</p>
                    </div>
                """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 5: RESUME ROI & GLOBAL FIT
    # ----------------------------------------------------
    elif active == "📈 Resume ROI & Global Fit":
        st.markdown("<h1>📈 Resume ROI, Searchability Audit & Global Adaptations</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Evaluate the financial and searchability return on investment (ROI) of your resume and adapt it for global markets.</p>", unsafe_allow_html=True)
        
        if not st.session_state.resume_json:
            st.warning("⚠️ Please upload and parse your resume in the 'Resume Intelligence' workspace first.")
            return
            
        roi_tab, global_tab = st.tabs(["📊 Resume ROI & Searchability", "🌍 Global Job Fit Engine"])
        
        with roi_tab:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>📊 Career Twin ROI Dashboard</h3>", unsafe_allow_html=True)
            st.write("We evaluate your resume's market position, predicting search findability rankings, salary benchmarks, and interview odds.")
            
            # Formulate ROI Score
            # Call backend to match single job or calculate default ROI
            roi = None
            if backend_online:
                try:
                    # Mock target data
                    desc = st.session_state.resume_json.get("current_summary", "")
                    title = st.session_state.resume_json.get("job_title", "Software Engineer")
                    roi_res = requests.post(
                        f"{BACKEND_URL}/jobs/match-single",
                        json={
                            "resume_version_id": st.session_state.resume_version_id,
                            "job_posting_id": 1, # dummy or first
                            "resume_json": st.session_state.resume_json,
                            "job_desc": desc,
                            "job_title": title
                        },
                        headers=get_auth_headers()
                    )
                    if roi_res.status_code == 200:
                        roi = roi_res.json().get("roi")
                except Exception:
                    pass
                    
            if not roi:
                # Fallback ROI
                roi = {
                    "interview_probability": 75,
                    "salary_range": "$125,000 - $148,000",
                    "hiring_chances": "Medium",
                    "searchability_score": 70,
                    "boolean_strings": [
                        '("Software Engineer" OR "Developer") AND Python AND SQL AND (Docker OR AWS)'
                    ],
                    "roi_boosters": [
                        {"skill": "Certified Kubernetes Administrator (CKA)", "salary_impact": "+$12,000", "probability_impact": "+15% Interview Odds"},
                        {"skill": "AWS Certified Solutions Architect", "salary_impact": "+$15,000", "probability_impact": "+22% Interview Odds"}
                    ]
                }
                
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background-color: #040406; border-radius: 12px; border: 1px solid rgba(167, 139, 250, 0.2);">
                        <div style="font-size: 12px; text-transform: uppercase; color: #a78bfa; font-weight: bold;">Interview Probability</div>
                        <div style="font-size: 44px; font-weight: 800; color: #a78bfa; margin: 10px 0;">{roi['interview_probability']}%</div>
                        <div style="font-size: 12px; color: #06b6d4;">Odds: {roi['hiring_chances']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with rc2:
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background-color: #040406; border-radius: 12px; border: 1px solid rgba(167, 139, 250, 0.2);">
                        <div style="font-size: 12px; text-transform: uppercase; color: #06b6d4; font-weight: bold;">Est. Salary Range</div>
                        <div style="font-size: 28px; font-weight: 800; color: #06b6d4; margin: 20px 0;">{roi['salary_range']}</div>
                        <div style="font-size: 12px; color: #94a3b8;">Based on local benchmarks</div>
                    </div>
                """, unsafe_allow_html=True)
            with rc3:
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background-color: #040406; border-radius: 12px; border: 1px solid rgba(167, 139, 250, 0.2);">
                        <div style="font-size: 12px; text-transform: uppercase; color: #10b981; font-weight: bold;">Searchability Index</div>
                        <div style="font-size: 44px; font-weight: 800; color: #10b981; margin: 10px 0;">{roi.get('searchability_score', 70)}/100</div>
                        <div style="font-size: 12px; color: #10b981;">✔ Standard Boolean match</div>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("##### 🔍 Recruiter Boolean Search Simulation")
            st.write("Recruiters search for candidates using complex Boolean logic. Your resume matched this search string:")
            for bs in roi.get("boolean_strings", []):
                st.code(bs, language="sql")
                
            st.markdown("##### ⚡ High-Yield ROI Boosters")
            st.write("Acquiring these credentials and adding them to your profile will yield the highest returns in salary and interview callbacks:")
            for bst in roi["roi_boosters"]:
                st.markdown(f"🔹 **{bst['skill']}**: Increases salary by `{bst['salary_impact']}` and interview chances by `{bst['probability_impact']}`.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with global_tab:
            st.markdown('<div class="cyber-card accent-card-cyan">', unsafe_allow_html=True)
            st.markdown("<h3>🌍 Global Job Fit Engine</h3>", unsafe_allow_html=True)
            st.write("Adapt your resume layout, headings, achievements, and technical representations for specific international markets.")
            
            reg = st.selectbox("Select Target Region/Market", ["US", "India", "Europe", "Middle East", "Remote"])
            adapt_btn = st.button("⚡ Rewrite & Adapt Resume", use_container_width=True)
            
            if adapt_btn:
                with st.spinner(f"Adapting resume style for {reg} hiring preferences..."):
                    if backend_online:
                        try:
                            g_res = requests.post(
                                f"{BACKEND_URL}/resume/global-fit",
                                json={
                                    "resume_json": st.session_state.resume_json,
                                    "region": reg,
                                    "candidate_id": st.session_state.candidate_id
                                },
                                headers=get_auth_headers()
                            )
                            if g_res.status_code == 200:
                                st.session_state.resume_json = g_res.json()["resume"]
                                st.session_state.resume_version_id = g_res.json()["resume_version_id"]
                                st.success(f"Success! Resume rewritten and saved as '{reg} Adapt' version!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Global adaptation failed: {str(e)}")
                    else:
                        time.sleep(1)
                        # Mock regional rewrite
                        st.session_state.resume_json["job_title"] = f"{st.session_state.resume_json.get('job_title', 'Software Engineer')} ({reg} Optimized)"
                        st.success(f"Success! Resume rewritten and saved locally as '{reg} Adapt' version!")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 6: JOB DISCOVERY & SWARM
    # ----------------------------------------------------
    elif active == "🔍 Job Discovery & Swarm":
        st.markdown("<h1>🔍 Job Discovery, Matching & One-Click Swarm</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Search for jobs using browser-based Playwright scraping, calculate semantic alignment, and deploy multi-agent swarms to apply.</p>", unsafe_allow_html=True)
        
        if not st.session_state.resume_json:
            st.warning("⚠️ Please upload and parse your resume in the 'Resume Intelligence' workspace first.")
            return
            
        col_s1, col_s2 = st.columns([1.2, 1.8], gap="large")
        with col_s1:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>Job Search Settings</h3>", unsafe_allow_html=True)
            role = st.text_input("Job Role / Title", "Python Software Engineer")
            location = st.text_input("Job Location", "Remote")
            post_date = st.selectbox("Posted Within", ["past_24_hours", "past_week", "past_month"])
            
            st.markdown("##### ⚡ Auto-Apply Swarm Settings")
            auto_apply = st.toggle("Enable Autonomous Auto-Apply Swarm")
            threshold = st.slider("Minimum Match Threshold (%)", 50, 95, 80)
            
            search_btn = st.button("🔍 Search & Analyze Jobs", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_s2:
            if search_btn:
                with st.spinner("Crawling job boards with Playwright scraper and compiling results..."):
                    jobs = []
                    if backend_online:
                        try:
                            # Search jobs
                            s_res = requests.post(
                                f"{BACKEND_URL}/jobs/search",
                                json={"role": role, "location": location, "post_date": post_date},
                                headers=get_auth_headers()
                            )
                            if s_res.status_code == 200:
                                raw_jobs = s_res.json().get("jobs", [])
                                # Match each job against resume
                                for rj in raw_jobs:
                                    m_res = requests.post(
                                        f"{BACKEND_URL}/jobs/match-single",
                                        json={
                                            "resume_version_id": st.session_state.resume_version_id,
                                            "job_posting_id": rj["db_id"],
                                            "resume_json": st.session_state.resume_json,
                                            "job_desc": rj["description"],
                                            "job_title": rj["title"]
                                        },
                                        headers=get_auth_headers()
                                    )
                                    if m_res.status_code == 200:
                                        m_data = m_res.json()
                                        rj["match_score"] = m_data["match_score"]
                                        rj["missing_skills"] = m_data["missing_skills"]
                                        rj["missing_keywords"] = m_data["missing_keywords"]
                                        rj["roi"] = m_data["roi"]
                                        jobs.append(rj)
                        except Exception as ex:
                            st.error(f"Search failed: {str(ex)}")
                    else:
                        # Offline fallback simulation
                        time.sleep(1.5)
                        jobs = generate_local_mock_jobs(role, location)
                            
                st.session_state.discovered_jobs = jobs
                st.success(f"🎉 Sweep completed! Found {len(jobs)} unique matches.")
                
            # Render Job Matches
            if "discovered_jobs" in st.session_state and st.session_state.discovered_jobs:
                st.markdown("<h3>Ranked Job Matches</h3>", unsafe_allow_html=True)
                
                # Sort jobs from highest score
                sorted_jobs = sorted(st.session_state.discovered_jobs, key=lambda x: x["match_score"], reverse=True)
                
                for idx, j in enumerate(sorted_jobs):
                    score = j["match_score"]
                    card_class = "accent-card-emerald" if score >= 80 else "accent-card-cyan" if score >= 65 else "accent-card-coral"
                    pill_class = "pill-emerald" if score >= 80 else "pill-cyan" if score >= 65 else "pill-coral"
                    
                    st.markdown(f"""
                        <div class="cyber-card {card_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h3 style="margin: 0; font-size: 22px;">{j['title']}</h3>
                                <span class="cyber-pill {pill_class}" style="font-size: 14px; padding: 6px 14px;">{score}% Match</span>
                            </div>
                            <h4 style="margin: 5px 0 10px 0; color: #a78bfa; font-size: 16px;">{j['company']} — <span style="color: #94a3b8;">{j['location']}</span></h4>
                            <p style="font-size: 14px; color: #f1f5f9;"><strong>Salary Est:</strong> {j['roi']['salary_range']}</p>
                    """, unsafe_allow_html=True)
                    
                    if j.get("missing_skills"):
                        st.markdown(f"<p style='font-size: 14px; color: #f43f5e;'><strong>⚠️ Skill Gaps:</strong> {', '.join(j['missing_skills'])}</p>", unsafe_allow_html=True)
                        
                    # Apply Swarm Button or Auto-applied alert
                    st.markdown("---")
                    
                    # If auto-apply active and above threshold
                    if auto_apply and score >= threshold:
                        st.markdown(f"<div style='font-size: 13px; color: #10b981; font-weight: bold; margin-bottom: 10px;'>✔ Auto-Apply Swarm triggered successfully. (Match {score}% &ge; Threshold {threshold}%)</div>", unsafe_allow_html=True)
                        
                    cols_btn = st.columns(3)
                    with cols_btn[0]:
                        if st.button("⚡ Run Apply Swarm", key=f"swarm_{j['job_id']}_{idx}"):
                            with st.spinner("Deploying swarm agents (tailoring summary, compiling cover letter, deploying Playwright)..."):
                                if backend_online:
                                    try:
                                        swarm_res = requests.post(
                                            f"{BACKEND_URL}/apply/swarm",
                                            json={
                                                "candidate_name": st.session_state.candidate["name"] if st.session_state.candidate else "Alex Mercer",
                                                "resume_json": st.session_state.resume_json,
                                                "job": j
                                            },
                                            headers=get_auth_headers()
                                        )
                                        if swarm_res.status_code == 200:
                                            s_data = swarm_res.json()["swarm"]
                                            st.success("🎉 Swarm application complete! Aligned assets generated.")
                                            with st.expander("Show Swarm Generated Cover Letter"):
                                                st.write(s_data["cover_letter"])
                                            with st.expander("Show Interview Prep Cheatsheet"):
                                                st.markdown("##### Tough Questions to Expect")
                                                for q in s_data["cheatsheet"]["tough_questions"]:
                                                    st.markdown(f"- {q}")
                                                st.markdown("##### Tactical Talking Points")
                                                for p in s_data["cheatsheet"]["talking_points"]:
                                                    st.markdown(f"- {p}")
                                    except Exception as ex:
                                        st.error(f"Swarm failed: {str(ex)}")
                                else:
                                    time.sleep(1.5)
                                    # Fallback swarm
                                    st.success("🎉 Swarm application simulated successfully! Aligned assets logged.")
                                    with st.expander("Show Swarm Generated Cover Letter"):
                                        st.write("Dear hiring manager, I am excited to apply for this role...")
                    with cols_btn[1]:
                        # Download Cover letter directly
                        if st.button("📄 Generate Cover Letter", key=f"cl_{j['job_id']}_{idx}"):
                            with st.spinner("Synthesizing cover letter..."):
                                if backend_online:
                                    try:
                                        cl_res = requests.post(
                                            f"{BACKEND_URL}/twin/cover-letter",
                                            json={
                                                "resume_json": st.session_state.resume_json,
                                                "job_title": j["title"],
                                                "company": j["company"],
                                                "job_desc": j["description"]
                                            },
                                            headers=get_auth_headers()
                                        )
                                        if cl_res.status_code == 200:
                                            st.info(cl_res.json()["cover_letter"])
                                    except Exception:
                                        pass
                                else:
                                    st.info("Dear Hiring Team,\n\nI am thrilled to apply for the position. Given my backend and database engineering background, I can add immediate value...")
                    with cols_btn[2]:
                        with st.expander("Show Full Requirements"):
                            st.write(j["description"])
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='text-align: center; padding: 120px 20px; border: 1px dashed rgba(167, 139, 250, 0.2); border-radius: 12px; background-color: #0d0d15;'>
                        <h4 style='color: #64748b;'>Awaiting Search Sweep</h4>
                        <p style='color: #475569; font-size: 14px;'>Enter your target role and location on the left, then click 'Search & Analyze' to run Playwright crawlers and calculate similarity overrides.</p>
                    </div>
                """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 7: SKILL GAP & FUTURE ROADMAPS
    # ----------------------------------------------------
    elif active == "🛠️ Skill Gap & Future Roadmaps":
        st.markdown("<h1>🛠️ Skill Gap Auto-Builder & Future Resume Generator</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Analyze skill gaps against any job description, generate week-by-week learning roadmaps, and produce your 3-6 months 'Future Resume'.</p>", unsafe_allow_html=True)
        
        if not st.session_state.resume_json:
            st.warning("⚠️ Please upload and parse your resume in the 'Resume Intelligence' workspace first.")
            return
            
        col_g1, col_g2 = st.columns([1.2, 1.8], gap="large")
        with col_g1:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>Target Job Spec</h3>", unsafe_allow_html=True)
            gap_job_desc = st.text_area("Paste Target Requirements", height=250, placeholder="Responsibilities, tech stack, and missing requirements...")
            
            build_plan = st.button("⚡ Generate Future Resume & Roadmap", disabled=len(gap_job_desc) < 20, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_g2:
            if build_plan:
                with st.spinner("Comparing profiles, identifying gaps, and outlining 12-week schedule..."):
                    roadmap_data = None
                    if backend_online:
                        try:
                            r_res = requests.post(
                                f"{BACKEND_URL}/resume/roadmap",
                                json={"resume_json": st.session_state.resume_json, "target_job_desc": gap_job_desc},
                                headers=get_auth_headers()
                            )
                            if r_res.status_code == 200:
                                roadmap_data = r_res.json().get("roadmap")
                        except Exception:
                            pass
                            
                    if not roadmap_data:
                        # Fallback roadmap
                        time.sleep(1.5)
                        roadmap_data = {
                            "future_resume": {
                                "name": st.session_state.resume_json.get("name", "Candidate"),
                                "current_summary": st.session_state.resume_json.get("current_summary", "") + " Enhanced with cloud infrastructure orchestration and devops automation competencies.",
                                "skills": list(st.session_state.resume_json.get("skills", [])) + ["Kubernetes", "Terraform", "CI/CD Orchestration"],
                                "projects": [
                                    {
                                        "title": "Autonomous Infrastructure Deployment Pipeline",
                                        "description": "Designed and deployed a multi-tier web application to AWS using Terraform for IaC and GitHub Actions for continuous integration, hosted in a Kubernetes cluster."
                                    }
                                ]
                            },
                            "roadmap": [
                                {
                                    "weeks": "Weeks 1-4: Containerization & Docker Mastery",
                                    "focus": "Docker fundamentals, multi-stage builds, networking, and volume bindings.",
                                    "resources": ["Docker Curriculum (docker-curriculum.com)", "FreeCodeCamp Docker Course"],
                                    "milestone": "Dockerize a legacy backend app and deploy it securely."
                                },
                                {
                                    "weeks": "Weeks 5-8: Kubernetes Cluster Orchestration",
                                    "focus": "Pods, Deployments, Services, ConfigMaps, Ingress, and Helm charts.",
                                    "resources": ["Kubernetes.io Tutorials", "KubeAcademy by VMware"],
                                    "milestone": "Deploy your dockerized app to a local Minikube cluster."
                                },
                                {
                                    "weeks": "Weeks 9-12: Infrastructure as Code & Pipelines",
                                    "focus": "Terraform plans, state management, and GitHub Actions CI/CD workflows.",
                                    "resources": ["HashiCorp Learn Terraform", "GitHub Actions Documentation"],
                                    "milestone": "Write a complete pipeline that provisions an EC2 instance and deploys your app on git push."
                                }
                            ]
                        }
                        
                st.success("🎉 Future Resume & Roadmap generated successfully!")
                
                # Display Future Resume
                st.markdown('<div class="cyber-card accent-card-cyan">', unsafe_allow_html=True)
                st.markdown("<h3>🔮 Your Projected 3-6 Months Future Resume</h3>", unsafe_allow_html=True)
                st.write(f"**Target Aligned Summary:** {roadmap_data['future_resume']['current_summary']}")
                st.write("**Upgraded Skills:**")
                skills_html = "".join(f'<span class="cyber-pill pill-purple">{s}</span>' for s in roadmap_data['future_resume']['skills'])
                st.markdown(skills_html, unsafe_allow_html=True)
                st.markdown("##### Target Capstone Showcase Project")
                for proj in roadmap_data['future_resume'].get('projects', []):
                    st.markdown(f"⚡ **{proj['title']}**: {proj['description']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display Roadmap
                st.markdown("<h3>📅 12-Week Skill Bridge Learning Plan</h3>", unsafe_allow_html=True)
                for step in roadmap_data["roadmap"]:
                    st.markdown(f"""
                        <div class="cyber-card accent-card-purple">
                            <h4 style="margin: 0; color: #a78bfa;">{step['weeks']}: {step['focus']}</h4>
                            <p style="margin: 8px 0; font-size: 14px; color: #94a3b8;"><strong>Milestone:</strong> {step['milestone']}</p>
                            <p style="margin: 0; font-size: 13px;"><strong>Free Resources:</strong> {', '.join(step['resources'])}</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='text-align: center; padding: 120px 20px; border: 1px dashed rgba(167, 139, 250, 0.2); border-radius: 12px; background-color: #0d0d15;'>
                        <h4 style='color: #64748b;'>Awaiting Requirements Input</h4>
                        <p style='color: #475569; font-size: 14px;'>Paste the target job description on the left to analyze gaps, build projects, and chart your 12-week roadmap.</p>
                    </div>
                """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 8: DIGITAL TWIN & NEGOTIATION
    # ----------------------------------------------------
    elif active == "🤖 Digital Twin & Negotiation":
        st.markdown("<h1>🤖 Digital Twin Candidate & Real-Time Salary Negotiator</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Activate your digital twin to answer recruiter questions truthfully, or practice salary negotiations with real-time coaching.</p>", unsafe_allow_html=True)
        
        if not st.session_state.resume_json:
            st.warning("⚠️ Please upload and parse your resume in the 'Resume Intelligence' workspace first.")
            return
            
        twin_tab, neg_tab = st.tabs(["🤖 Digital Twin Recruiter Q&A", "🤝 Salary Negotiator Copilot"])
        
        with twin_tab:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>🤖 Recruiter Q&A Console</h3>", unsafe_allow_html=True)
            st.write("Recruiters can ask your Digital Twin anything. It answers in the first-person, drawing facts strictly from your resume.")
            
            q_rec = st.text_input("Recruiter Question", placeholder="e.g. Do you have experience with microservice latency optimization?")
            ask_btn = st.button("⚡ Ask Digital Twin", use_container_width=True)
            
            if ask_btn and q_rec.strip():
                with st.spinner("Consulting resume facts and synthesizing truthful response..."):
                    answer = "Thank you for asking. Based on my resume, I have hands-on experience developing microservices at Tech Solutions Inc., where I successfully integrated systems to improve backend latency by 20%."
                    if backend_online:
                        try:
                            ans_res = requests.post(
                                f"{BACKEND_URL}/twin/qa",
                                json={"resume_json": st.session_state.resume_json, "recruiter_question": q_rec},
                                headers=get_auth_headers()
                            )
                            if ans_res.status_code == 200:
                                answer = ans_res.json()["answer"]
                        except Exception:
                            pass
                    st.markdown(f"""
                        <div style="padding: 20px; background-color: #040406; border: 1px solid rgba(6,182,212,0.3); border-radius: 10px; margin-top: 20px;">
                            <div style="font-size: 11px; text-transform: uppercase; color: #06b6d4; font-weight: bold; margin-bottom: 5px;">Twin's Professional Response</div>
                            <p style="margin: 0; font-style: italic; font-size: 15px; line-height: 1.5;">"{answer}"</p>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with neg_tab:
            st.markdown('<div class="cyber-card accent-card-cyan">', unsafe_allow_html=True)
            st.markdown("<h3>🤝 Salary Negotiator Roleplay</h3>", unsafe_allow_html=True)
            st.write("Practice countering low-ball offers. Negotiate with a tough recruiter, and receive real-time strategies and scripts from your Coach.")
            
            # Display conversation
            chat_container_neg = st.container()
            with chat_container_neg:
                # Display current turn
                st.markdown(f'<div class="chat-bubble chat-agent"><strong>Recruiter:</strong> {st.session_state.negotiation_coach["recruiter_response"]}</div>', unsafe_allow_html=True)
                
            # Coach Advice Panel
            st.markdown(f"""
                <div style="padding: 15px; background-color: #050508; border-left: 4px solid #a78bfa; border-radius: 6px; margin: 15px 0;">
                    <div style="font-size: 12px; font-weight: bold; color: #a78bfa; text-transform: uppercase;">💡 Real-Time Coach Feedback</div>
                    <p style="margin: 5px 0; font-size: 14px; color: #f1f5f9;">{st.session_state.negotiation_coach['coach_feedback']}</p>
                    <div style="font-size: 12px; color: #06b6d4; font-weight: bold; margin-top: 8px;">👉 Suggested Script to Type:</div>
                    <code style="color: #06b6d4; font-size: 13px;">"{st.session_state.negotiation_coach['suggested_script']}"</code>
                </div>
            """, unsafe_allow_html=True)
            
            # Form input
            with st.form("neg_form", clear_on_submit=True):
                candidate_msg = st.text_input("Your Response to Recruiter", placeholder="e.g. Thank you for the offer. I am seeking a base salary of $132,000...")
                
                c_neg_send, c_neg_reset = st.columns(2)
                with c_neg_send:
                    neg_send_btn = st.form_submit_button("Send Counter-Offer")
                with c_neg_reset:
                    neg_reset_btn = st.form_submit_button("Reset Negotiation")
                    
                if neg_send_btn and candidate_msg.strip():
                    with st.spinner("Recruiter is formulating response... Coach is analyzing strategy..."):
                        if backend_online:
                            try:
                                neg_res = requests.post(
                                    f"{BACKEND_URL}/apply/negotiate",
                                    json={"session_id": "demo_session", "user_message": candidate_msg},
                                    headers=get_auth_headers()
                                )
                                if neg_res.status_code == 200:
                                    st.session_state.negotiation_coach = neg_res.json()["negotiation"]
                                    st.rerun()
                            except Exception:
                                pass
                        else:
                            # Mock next turn
                            time.sleep(1)
                            st.session_state.negotiation_coach = {
                                "recruiter_response": "We appreciate your counter-offer. While $132,000 is slightly above our standard allocation, we could compromise at a base of $122,000 with a sign-on bonus of $5,000. This is our absolute best offer. Does that align with your expectations?",
                                "coach_feedback": "Excellent counter! You successfully nudged the recruiter up. They are compromising. Now, focus on accepting the sign-on bonus but ask for another small base salary bump to secure a win.",
                                "suggested_script": "Thank you for working with me on this. The sign-on bonus is a great addition. If we can adjust the base to $126,000, I will sign the offer letter immediately."
                            }
                            st.rerun()
                            
                if neg_reset_btn:
                    if backend_online:
                        try:
                            requests.delete(f"{BACKEND_URL}/apply/negotiate/demo_session", headers=get_auth_headers())
                        except Exception:
                            pass
                    st.session_state.negotiation_coach = {
                        "recruiter_response": "Hello, we are thrilled to extend an offer to join our team as a Senior Software Engineer. The base salary we have allocated is $112,000. Let me know if you are ready to sign.",
                        "coach_feedback": "Welcome to the Salary Negotiator Copilot. Counter-offers anchor the value you add.",
                        "suggested_script": "Start by thanking them for the offer and expressing excitement, then anchor your counter-offer professionally."
                    }
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 9: AUTO-UPGRADE & SHOWCASE
    # ----------------------------------------------------
    elif active == "🔄 Auto-Upgrade & Showcase":
        st.markdown("<h1>🔄 Auto-Upgrading Resume & Showcase Portfolio</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Connect Github repositories to discover hidden, latent skills, auto-upgrade your resume, and download a premium portfolio showcase.</p>", unsafe_allow_html=True)
        
        if not st.session_state.resume_json:
            st.warning("⚠️ Please upload and parse your resume in the 'Resume Intelligence' workspace first.")
            return
            
        up_tab, show_tab = st.tabs(["🔄 Auto-Upgrading & Hidden Skills", "🎨 Proof-of-Skill Showcase"])
        
        with up_tab:
            st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
            st.markdown("<h3>🔄 Auto-Upgrading Sync Panel</h3>", unsafe_allow_html=True)
            st.write("Paste your raw developer artifacts (recent Github commit messages, project notes, or documentation text) below. The agent will audit these to discover latent skills you forgot to list.")
            
            commits_input = st.text_area("Paste Git Commits / Work Notes", height=200, placeholder="e.g. merge pull request #12 from feature/auth-fix; resolved merge conflict; configured kubernetes deployment manifests and set up load balancing...")
            sync_btn = st.button("⚡ Audit Artifacts & Upgrade Resume", use_container_width=True)
            
            if sync_btn and commits_input.strip():
                with st.spinner("Analyzing commits, parsing technologies, and discovering hidden competencies..."):
                    report = None
                    if backend_online:
                        try:
                            up_res = requests.post(
                                f"{BACKEND_URL}/resume/hidden-skills",
                                json={"raw_input_text": commits_input, "resume_json": st.session_state.resume_json},
                                headers=get_auth_headers()
                            )
                            if up_res.status_code == 200:
                                report = up_res.json().get("report")
                        except Exception:
                            pass
                            
                    if not report:
                        # Fallback report
                        time.sleep(1.5)
                        report = {
                            "discovered_skills": [
                                {
                                    "skill": "Kubernetes Orchestration",
                                    "evidence": "Detected pod manifests, load balancing, and ingress configurations in commit messages.",
                                    "suggested_bullet": "Configured multi-pod Kubernetes deployment manifests and ingress controllers, establishing load balancing and boosting service availability."
                                },
                                {
                                    "skill": "Git flow / PR Reviews",
                                    "evidence": "Detected extensive merge resolutions and pull request conflict management.",
                                    "suggested_bullet": "Managed repository branch integrity, reviewing team PRs and resolving complex merge conflicts to maintain continuous integration workflows."
                                }
                            ],
                            "confidence_score": 88
                        }
                        
                st.success("🎉 Hidden skills discovered and verified!")
                st.markdown(f"**Discovered Skills Confidence Rating:** `{report['confidence_score']}/100`")
                
                # Render discovered skills
                for idx, skill in enumerate(report["discovered_skills"]):
                    st.markdown(f"""
                        <div style="padding: 15px; background-color: #050508; border-radius: 8px; border: 1px solid rgba(6,182,212,0.25); margin-bottom: 12px;">
                            <div style="font-size: 12px; font-weight: bold; color: #06b6d4; text-transform: uppercase;">⚡ Discovered Competency: {skill['skill']}</div>
                            <p style="margin: 5px 0; font-size: 13px; color: #94a3b8;"><strong>Evidence:</strong> {skill['evidence']}</p>
                            <div style="font-size: 13px; margin-top: 5px; color: #a78bfa;"><strong>Suggested Bullet addition:</strong> "{skill['suggested_bullet']}"</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # Option to merge
                if st.button("➕ Merge Discovered Skills into Active Resume", use_container_width=True):
                    for skill in report["discovered_skills"]:
                        if skill["skill"] not in st.session_state.resume_json["skills"]:
                            st.session_state.resume_json["skills"].append(skill["skill"])
                        if len(st.session_state.resume_json["experience"]) > 0:
                            st.session_state.resume_json["experience"][0]["bullets"].append(skill["suggested_bullet"])
                    st.success("🎉 Discovered skills successfully merged! Resume updated.")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with show_tab:
            st.markdown('<div class="cyber-card accent-card-cyan">', unsafe_allow_html=True)
            st.markdown("<h3>🎨 Proof-of-Skill Interactive Showcase</h3>", unsafe_allow_html=True)
            st.write("Generate a high-fidelity, responsive single-page HTML portfolio displaying your skills, experience, and interactive project sandboxes for recruiters.")
            
            showcase_btn = st.button("⚡ Compile Showcase Portfolio", use_container_width=True)
            
            if showcase_btn:
                with st.spinner("Compiling HTML5, CSS3, and JavaScript widgets..."):
                    html_code = ""
                    if backend_online:
                        try:
                            s_res = requests.post(
                                f"{BACKEND_URL}/resume/showcase",
                                json={"resume_json": st.session_state.resume_json},
                                headers=get_auth_headers()
                            )
                            if s_res.status_code == 200:
                                html_code = s_res.json()["html"]
                        except Exception:
                            pass
                            
                    if not html_code:
                        # Fallback showcase tool
                        html_code = generate_proof_of_skill_showcase(st.session_state.resume_json)
                        
                st.success("🎉 Showcase compiled successfully!")
                
                # Preview structure
                st.components.v1.html(html_code, height=500, scrolling=True)
                
                # Download button
                st.download_button(
                    label="⬇| Download Showcase HTML Portfolio",
                    data=html_code,
                    file_name=f"Showcase_{st.session_state.resume_json.get('name','Candidate').replace(' ', '_')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # VIEW 10: SYSTEM SETTINGS
    # ----------------------------------------------------
    elif active == "⚙️ System Settings":
        st.markdown("<h1>⚙️ System, SMTP & Alert Settings</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Configure your email notifications, SMTP credentials, API keys, and database utilities.</p>", unsafe_allow_html=True)
        
        st.markdown('<div class="cyber-card accent-card-purple">', unsafe_allow_html=True)
        st.markdown("<h3>📧 SMTP Notification Settings</h3>", unsafe_allow_html=True)
        st.write("Configure your email server to receive job alerts, application updates, and items needing your immediate attention.")
        
        # Read existing settings
        host_val = get_backend_setting("smtp_host", "smtp.gmail.com")
        port_val = get_backend_setting("smtp_port", "587")
        sender_val = get_backend_setting("smtp_sender", "")
        recipient_val = get_backend_setting("smtp_recipient", "")
        password_val = get_backend_setting("smtp_password", "")
        
        with st.form("smtp_form"):
            smtp_host = st.text_input("SMTP Server Host", value=host_val)
            smtp_port = st.text_input("SMTP Port (e.g. 587 or 465)", value=port_val)
            smtp_sender = st.text_input("Sender Email Address", value=sender_val)
            smtp_recipient = st.text_input("Recipient Email Address", value=recipient_val)
            smtp_password = st.text_input("SMTP Auth Password / App Password", type="password", value=password_val)
            
            c_test, c_save = st.columns(2)
            with c_test:
                test_smtp_btn = st.form_submit_button("🧪 Run Connection Diagnostic")
            with c_save:
                save_smtp_btn = st.form_submit_button("💾 Save Settings")
                
            if save_smtp_btn:
                if backend_online:
                    try:
                        requests.post(f"{BACKEND_URL}/settings", json={"key": "smtp_host", "value": smtp_host}, headers=get_auth_headers())
                        requests.post(f"{BACKEND_URL}/settings", json={"key": "smtp_port", "value": smtp_port}, headers=get_auth_headers())
                        requests.post(f"{BACKEND_URL}/settings", json={"key": "smtp_sender", "value": smtp_sender}, headers=get_auth_headers())
                        requests.post(f"{BACKEND_URL}/settings", json={"key": "smtp_recipient", "value": smtp_recipient}, headers=get_auth_headers())
                        requests.post(f"{BACKEND_URL}/settings", json={"key": "smtp_password", "value": smtp_password}, headers=get_auth_headers())
                        st.success("SMTP configuration successfully updated!")
                    except Exception as ex:
                        st.error(f"Failed to update configurations: {str(ex)}")
                else:
                    st.success("SMTP configuration successfully saved locally in demo mode!")
                    
            if test_smtp_btn:
                with st.spinner("Initiating SMTP handshake and sending test payload..."):
                    if backend_online:
                        try:
                            diag_res = requests.post(
                                f"{BACKEND_URL}/email/test",
                                json={
                                    "host": smtp_host,
                                    "port": smtp_port,
                                    "sender": smtp_sender,
                                    "password": smtp_password
                                },
                                headers=get_auth_headers()
                            )
                            if diag_res.status_code == 200:
                                diag_data = diag_res.json()
                                if diag_data.get("success"):
                                    st.success("✔ SMTP Handshake OK! Connection diagnostics successful!")
                                else:
                                    st.error(f"❌ Handshake failed: {diag_data.get('error')}")
                        except Exception as ex:
                            st.error(f"Diagnostic failed: {str(ex)}")
                    else:
                        time.sleep(1)
                        st.success("✔ (Demo) SMTP Handshake Simulated OK! Connection diagnostics successful!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # System Reset
        st.markdown('<div class="cyber-card accent-card-coral">', unsafe_allow_html=True)
        st.markdown("<h3>⚠ Database Maintenance Utilities</h3>", unsafe_allow_html=True)
        st.write("Erase all cached profiles, resume versions, matched jobs, and application histories. Resetting is irreversible.")
        if st.button("❌ Hard Reset Database", use_container_width=True):
            with st.spinner("Wiping local databases..."):
                if backend_online:
                    try:
                        reset_res = requests.post(f"{BACKEND_URL}/system/reset", headers=get_auth_headers())
                        if reset_res.status_code == 200:
                            st.session_state.candidate = None
                            st.session_state.resume_json = None
                            st.success("System database reset successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Reset failed: {str(e)}")
                else:
                    st.session_state.candidate = None
                    st.session_state.resume_json = None
                    st.success("System database reset successfully in demo mode!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Main Entrance
if __name__ == "__main__":
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()
