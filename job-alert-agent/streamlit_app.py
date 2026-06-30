import streamlit as st
import os
import asyncio
import sys
from dotenv import load_dotenv
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agent import root_agent
import streamlit.components.v1 as components
from app.database import (
    get_all_applications,
    get_pending_hitl_prompt,
    resolve_hitl_prompt,
    update_application_status,
    get_application_logs
)
import sys
import importlib
if "app.application_agent.tools" in sys.modules:
    try:
        importlib.reload(sys.modules["app.application_agent.tools"])
    except Exception:
        pass
if "app.easy_agent.tools" in sys.modules:
    try:
        importlib.reload(sys.modules["app.easy_agent.tools"])
    except Exception:
        pass
from app.application_agent.tools import apply_for_job, check_linkedin_session, login_to_linkedin
from app.easy_agent.tools import (
    apply_for_job as easy_apply_for_job,
    check_linkedin_session as easy_check_linkedin_session,
    login_to_linkedin as easy_login_to_linkedin,
    discover_easy_apply_jobs
)

# Set page configuration
st.set_page_config(
    page_title="Job Alert Agent Control Center",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables
if "validation_error" not in st.session_state:
    st.session_state.validation_error = None
if "candidate_profile" not in st.session_state:
    import json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_profile_path = os.path.join(script_dir, "candidate_profile.json")
    if os.path.exists(local_profile_path):
        try:
            with open(local_profile_path, "r", encoding="utf-8") as f:
                st.session_state.candidate_profile = json.load(f)
            resume_p = st.session_state.candidate_profile.get("personal_info", {}).get("resume_path", "")
            st.session_state.uploaded_resume_name = os.path.basename(resume_p) if resume_p else "Loaded from profile"
            st.session_state.resume_temp_path = resume_p
        except Exception:
            st.session_state.candidate_profile = None
    else:
        st.session_state.candidate_profile = None
if "uploaded_resume_name" not in st.session_state:
    st.session_state.uploaded_resume_name = None
if "resume_temp_path" not in st.session_state:
    st.session_state.resume_temp_path = None
if "linkedin_username" not in st.session_state:
    st.session_state.linkedin_username = ""
if "linkedin_password" not in st.session_state:
    st.session_state.linkedin_password = ""

# Custom premium styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0077b5, #00a0dc);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #005a87, #0077b5);
        box-shadow: 0 4px 12px rgba(0,119,181,0.25);
    }
    .header-style {
        background: linear-gradient(135deg, #0077b5, #00a0dc);
        color: white;
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .header-style h1 {
        margin: 0;
        font-weight: 700;
    }
    .header-style p {
        margin: 5px 0 0 0;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Load configuration from .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path, override=True)

# Helper to save configs back to .env
def save_env_var(key, value):
    # Update os.environ
    os.environ[key] = str(value)
    # Read existing .env lines
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    # Check if key already exists
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
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

# Application Header Banner
st.markdown("""
<div class="header-style">
    <h1>💼 Job Alert Agent Control Center</h1>
    <p>Automate your job hunt using AI. Scrape LinkedIn jobs and email styled reports.</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.validation_error:
    st.markdown(f'<p style="color: #ff4b4b; font-weight: 600; margin-bottom: 20px; font-size: 16px;">⚠️ {st.session_state.validation_error}</p>', unsafe_allow_html=True)

# Main layout tabs
tab_panel, tab_chat, tab_preview, tab_login, tab_easy_apply = st.tabs([
    "⚙️ Control & Settings", 
    "💬 Chat with Agent", 
    "📧 Job Alert Email Preview",
    "Linkedin  job Automation",
    "Easy Apply Automation"
])



# Async function to run the agent from Streamlit
async def run_agent_in_streamlit(prompt, log_container, recipient_email):
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
        auto_create_session=True,
    )
    
    user_message = types.Content(parts=[types.Part.from_text(text=prompt)])
    events = runner.run_async(
        user_id="streamlit_user",
        session_id="streamlit_session",
        new_message=user_message,
        state_delta={"recipient_email": recipient_email},
    )
    
    logs = []
    agent_response = ""
    
    async for event in events:
        # Accumulate streaming text response
        if event.message:
            for part in event.message.parts:
                if part.text:
                    agent_response += part.text
                    log_container.markdown(agent_response)
        
        # Capture tool calls & results
        for tc in event.get_function_calls():
            log_msg = f"🔧 **Tool Call**: {tc.name}({tc.args})"
            logs.append(log_msg)
            st.toast(log_msg)
            
        for tr in event.get_function_responses():
            log_msg = f"✅ **Tool Result**: {str(tr.response)[:250]}..."
            logs.append(log_msg)
            
    return agent_response, logs

# TAB 1: Control & Settings Panel
with tab_panel:
    st.subheader("🎯 Configure Job Alert Parameters")
    
    # Load defaults from environment
    default_keywords = os.environ.get("JOB_KEYWORDS", "")
    default_location = os.environ.get("JOB_LOCATION", "")
    default_recipient = os.environ.get("RECIPIENT_EMAIL", "")
    default_experience = os.environ.get("JOB_EXPERIENCE", "Any Experience")
    default_frequency = os.environ.get("ALERT_FREQUENCY", "Daily")
    
    col1, col2 = st.columns(2)
    with col1:
        keywords = st.text_input("Job Role Keywords", value=default_keywords, placeholder="e.g. Python Developer")
        location = st.text_input("Location", value=default_location, placeholder="e.g. Seattle")
        
        experience_options = ["Any Experience", "0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"]
        try:
            default_exp_idx = experience_options.index(default_experience)
        except ValueError:
            default_exp_idx = 0
        experience = st.selectbox("Experience Level", options=experience_options, index=default_exp_idx)
        
    with col2:
        recipient = st.text_input("Recipient Email", value=default_recipient, placeholder="Email or phone")
        max_listings = st.slider("Maximum Listings", min_value=1, max_value=20, value=5)
        
        frequency_options = ["Hourly", "Daily", "Weekly", "Monthly"]
        try:
            default_freq_idx = frequency_options.index(default_frequency)
        except ValueError:
            default_freq_idx = 1
        frequency = st.selectbox("Alert Frequency", options=frequency_options, index=default_freq_idx)
        
    if st.button("Save Job Search Settings"):
        if not keywords.strip() or not location.strip() or not recipient.strip():
            st.session_state.validation_error = "Please fill all fields (Job Role Keywords, Location, and Recipient Email) correctly."
            st.rerun()
        else:
            st.session_state.validation_error = None
            save_env_var("JOB_KEYWORDS", keywords)
            save_env_var("JOB_LOCATION", location)
            save_env_var("RECIPIENT_EMAIL", recipient)
            save_env_var("JOB_EXPERIENCE", experience)
            save_env_var("ALERT_FREQUENCY", frequency)
            st.success("Search configurations saved to .env!")
            st.rerun()

    st.divider()
    st.subheader("🚀 Trigger Job Alert Agent")
    st.info("Triggering will run the agent in the background to scrape LinkedIn and send the alert.")
    
    trigger_btn = st.button("Trigger Job Hunt Alert Now")
    if trigger_btn:
        if not keywords.strip() or not location.strip() or not recipient.strip():
            st.session_state.validation_error = "Please fill all fields (Job Role Keywords, Location, and Recipient Email) correctly."
            st.rerun()
        elif not os.environ.get("GEMINI_API_KEY"):
            st.session_state.validation_error = None
            st.error("Please configure and save your Gemini API Key in the sidebar first!")
        else:
            st.session_state.validation_error = None
            with st.spinner("Agent starting... Scraping LinkedIn & generating job report..."):
                # Run the agent trigger
                experience_phrase = f"with experience years range '{experience}'" if experience != "Any Experience" else "at any experience level"
                frequency_phrase = f"posted in the last '{frequency.lower()}' frequency window"
                prompt = f"Find jobs matching keywords '{keywords}' in location '{location}' {experience_phrase} {frequency_phrase} and email them to {recipient}."
                log_box = st.empty()
                response, logs = asyncio.run(run_agent_in_streamlit(prompt, log_box, recipient))
                
                # Show execution summary
                st.success("Job Alert Agent execution complete!")
                
                # Expandable execution logs
                with st.expander("🔍 View Detailed Tool Invocation Logs", expanded=True):
                    for log in logs:
                        st.markdown(log)
                        
                st.info("Check the 'Job Alert Email Preview' tab to see the output report!")

# TAB 2: Agent Chat Interface
with tab_chat:
    st.subheader("💬 Chat with your Career Assistant")
    st.write("Command your agent in plain English! (e.g. 'Scrape Python roles in California' or 'Email developer jobs to me')")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    user_input = st.chat_input("Ask the agent to find jobs...")
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display assistant response placeholder
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            with st.spinner("Agent is reasoning..."):
                response, _ = asyncio.run(run_agent_in_streamlit(user_input, response_placeholder, recipient))
                
        st.session_state.messages.append({"role": "assistant", "content": response})

# TAB 3: Job Alert Email Preview
with tab_preview:
    st.subheader("📄 Local Job Alert Output")
    output_html_path = os.path.join(script_dir, "job_alert_output.html")
    
    if os.path.exists(output_html_path):
        st.success(f"Generated job alert file found at: {output_html_path}")
        
        # Read and display the HTML inside an iframe
        with open(output_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        components.html(html_content, height=600, scrolling=True)
        
        # Add download button
        st.download_button(
            label="Download Job Alert Report (HTML)",
            data=html_content,
            file_name="job_alert_output.html",
            mime="text/html"
        )
    else:
        st.info("No generated job alert output found yet. Run the agent in Tab 1 to generate a job report.")

# TAB 5: LinkedIn Session Login
with tab_login:
    # 1. LinkedIn Authentication & Session Manager
    st.subheader("LinkedIn Authentication & Session Manager")
    st.write(
        "Manage your LinkedIn login state here. You can check if a valid session exists, "
        "or open an interactive automated browser window to perform a manual login."
    )
    
    # Session status containers
    if "session_checked" not in st.session_state:
        st.session_state.session_checked = False
    if "session_valid" not in st.session_state:
        st.session_state.session_valid = None
        
    def run_check_session():
        with st.spinner("Checking LinkedIn session status..."):
            try:
                res = asyncio.run(check_linkedin_session())
                st.session_state.session_valid = res.get("logged_in", False)
                st.session_state.session_checked = True
            except Exception as e:
                st.error(f"Error checking session: {e}")
                st.session_state.session_valid = False
                st.session_state.session_checked = True

    # Check status button
    if st.button("Check LinkedIn Login Status", key="btn_check_linkedin_session"):
        run_check_session()
        st.rerun()
        
    # Render current status
    if st.session_state.session_checked:
        if st.session_state.session_valid:
            st.success("✅ **Active LinkedIn session verified successfully!** Cookies are loaded and valid.")
        else:
            st.warning("⚠️ **No active LinkedIn session found.** You are currently not signed in or session cookies are expired.")
    else:
        st.info("ℹ️ Login status not checked yet for this browser window. Click the button above to verify.")
        
    st.divider()
    
    # 2. Authenticate/Renew Session
    st.subheader("Authenticate/Renew Session")
    st.write(
        "If your session has expired or does not exist, click below to open a headful Chromium window. "
        "Once the browser opens, log in to your LinkedIn account manually. "
        "The background worker will automatically detect the sign-in, save your session state on success, and close the window."
    )
    
    if st.button("Launch LinkedIn Interactive Login", key="btn_launch_linkedin_login"):
        with st.spinner("Launching headful Chromium window. Please locate it and sign in manually..."):
            try:
                res = asyncio.run(login_to_linkedin(timeout_seconds=300))
                if res.get("status") == "success":
                    st.success("🎉 **Success:** LinkedIn logged in successfully. Cookies saved!")
                    st.session_state.session_valid = True
                    st.session_state.session_checked = True
                else:
                    st.error(f"❌ **Failed:** {res.get('message', 'Login timed out or failed.')}")
            except Exception as e:
                st.error(f"Error executing login: {e}")
                
    st.divider()

    # 3. Resume Upload & Automated Apply
    st.subheader("📄 Resume Upload & Automated Apply")
    
    MOCK_PROFILE = {
        "personal_info": {
            "first_name": "Jane",
            "last_name": "Doe",
            "full_name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "+1 555 123 4567",
            "location": "San Francisco, CA",
            "resume_path": ""
        }
    }
    
    def parse_pdf_resume(file_bytes) -> dict:
        import io
        import pypdf
        import json
        from google import genai
        
        # 1. Read PDF text
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
        return json.loads(response.text)

    # File Uploader
    uploaded_file = st.file_uploader("Upload your Resume (PDF format)", type=["pdf"], key="resume_uploader_login_tab")
    
    if uploaded_file is not None and st.session_state.uploaded_resume_name != uploaded_file.name:
        with st.spinner("AI parsing of resume in progress..."):
            parsed_profile = None
            use_local_cache = False
            file_bytes = uploaded_file.read()
            
            try:
                # 1. Read bytes and parse
                parsed_profile = parse_pdf_resume(file_bytes)
            except Exception as e:
                # Fallback to local pre-parsed JSON if it exists
                script_dir = os.path.dirname(os.path.abspath(__file__))
                local_profile_path = os.path.join(script_dir, "candidate_profile.json")
                if os.path.exists(local_profile_path):
                    try:
                        import json
                        with open(local_profile_path, "r", encoding="utf-8") as f:
                            parsed_profile = json.load(f)
                        use_local_cache = True
                    except Exception:
                        parsed_profile = None
                
                if parsed_profile is None:
                    err_msg = str(e)
                    if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "quota" in err_msg.lower():
                        st.error("⚠️ **Gemini API Quota/Rate Limit Exceeded**: You have hit the requests limit on the Gemini API free tier. Please wait 30 seconds and try again.")
                    else:
                        st.error(f"Error parsing resume: {err_msg}")
            
            if parsed_profile is not None:
                try:
                    # 2. Save file temporarily
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(script_dir, "temp_resumes")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    import uuid
                    temp_filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
                    temp_path = os.path.join(temp_dir, temp_filename)
                    
                    with open(temp_path, "wb") as f:
                        f.write(file_bytes)
                        
                    # 3. Update session states
                    st.session_state.resume_temp_path = temp_path
                    parsed_profile["personal_info"]["resume_path"] = temp_path
                    st.session_state.candidate_profile = parsed_profile
                    st.session_state.uploaded_resume_name = uploaded_file.name
                    
                    if use_local_cache:
                        st.success(f"Resume '{uploaded_file.name}' loaded successfully! (⚠️ Loaded from pre-parsed local cache due to Gemini rate limits)")
                    else:
                        st.success(f"Resume '{uploaded_file.name}' parsed successfully! Details are loaded for this session.")
                except Exception as save_err:
                    st.error(f"Failed to load parsed profile: {str(save_err)}")
                
    st.divider()

    # View Session Candidate Profile Summary
    profile_data = st.session_state.candidate_profile
    has_uploaded = st.session_state.uploaded_resume_name is not None
    
    if has_uploaded:
        raw_name = profile_data.get('personal_info', {}).get('full_name', 'N/A')
        raw_email = profile_data.get('personal_info', {}).get('email', 'N/A')
        raw_phone = profile_data.get('personal_info', {}).get('phone', 'N/A')
        raw_loc = profile_data.get('personal_info', {}).get('location', 'N/A')
        
        st.info("ℹ️ **Session Active View:** You can see your actual details below. Refreshing the browser will wipe this data.")
        with st.expander("👤 View Session Candidate Profile Information (Unmasked)", expanded=True):
            st.markdown(f"**Name:** {raw_name}")
            st.markdown(f"**Email:** {raw_email}")
            st.markdown(f"**Phone:** {raw_phone}")
            st.markdown(f"**Location:** {raw_loc}")
            st.markdown(f"**Resume File:** `{st.session_state.uploaded_resume_name}`")
    else:
        with st.expander("👤 View Session Candidate Profile Information (Default Protected View)", expanded=False):
            st.markdown(f"**Name:** {MOCK_PROFILE['personal_info']['full_name']}")
            st.markdown(f"**Email:** {MOCK_PROFILE['personal_info']['email']}")
            st.markdown(f"**Phone:** {MOCK_PROFILE['personal_info']['phone']}")
            st.markdown(f"**Location:** {MOCK_PROFILE['personal_info']['location']}")
            st.caption("Upload your resume above to view and apply with your own profile.")
            
    st.divider()
    
    # Input Job Link & Trigger Application
    col_u, col_t, col_c = st.columns([2, 1, 1])
    with col_u:
        job_url_input = st.text_input("LinkedIn Job URL", placeholder="https://www.linkedin.com/jobs/view/...", key="job_url_login_tab")
    with col_t:
        job_title_input = st.text_input("Job Title", placeholder="e.g. Data Scientist", key="job_title_login_tab")
    with col_c:
        job_company_input = st.text_input("Company", placeholder="e.g. PepsiCo", key="job_company_login_tab")
        
    if st.button("🚀 Trigger Browser Automation Apply", key="btn_trigger_apply_login_tab"):
        if not st.session_state.get("candidate_profile"):
            st.error("Cannot apply. Please upload your resume to build your candidate profile first.")
        elif not job_url_input.strip():
            st.error("Please enter a valid LinkedIn job URL.")
        else:
            profile = st.session_state.candidate_profile
            res = apply_for_job(
                job_url=job_url_input,
                job_title=job_title_input,
                company=job_company_input,
                candidate_profile=profile,
                resume_path=st.session_state.resume_temp_path,
                li_username=st.session_state.get("linkedin_username"),
                li_password=st.session_state.get("linkedin_password")
            )
            if res["status"] == "success":
                st.success(res["message"])
                st.rerun()
            else:
                st.error(res["message"])

    # 4. Live Progress and Screenshot of working page
    st.divider()
    st.subheader("📟 Live Application Progress & Screenshot")
    
    apps_list = get_all_applications()
    if not apps_list:
        st.info("No applications triggered yet.")
    else:
        latest_app = apps_list[0]
        app_id = latest_app["id"]
        status = latest_app["status"]
        job_title = latest_app["job_title"] or "LinkedIn Job"
        company = latest_app["company"] or "Unknown Company"
        
        # Calculate time since last update to identify if stuck/looping
        try:
            from datetime import datetime
            updated_at = datetime.fromisoformat(latest_app["updated_at"])
            delta = datetime.now() - updated_at
            seconds_since_update = int(delta.total_seconds())
        except Exception:
            seconds_since_update = 0
            
        st.markdown(f"#### Latest Application: **{job_title}** at **{company}** (ID: {app_id})")
        
        # Render status alerts
        if status == "Completed":
            st.success("✅ **Application Completed successfully!**")
        elif status == "Failed":
            st.error(f"❌ **Application Failed:** {latest_app['error_message']}")
        elif status == "Cancelled":
            st.info("⚪ **Application was Cancelled.**")
        elif status == "Waiting for User Input":
            st.warning("⚠️ **Action Required:** The automation is paused and waiting for your input (see form below).")
        elif status == "Waiting for Final Review":
            st.warning("🔍 **Final Review Gate:** Ready for submission. Please approve the preview below.")
        else: # Queued or Running
            st.info(f"⏳ **Status:** {status}...")
            if status == "Running" and seconds_since_update > 30:
                st.warning(
                    f"⚠️ **Stuck/Loop Alert:** No progress updates have been received for **{seconds_since_update} seconds**. "
                    "The worker process might be stuck, looping, or waiting on a slow page load."
                )
            elif status == "Running":
                st.success(f"⚡ **Active Progress:** Worker is actively executing (last update {seconds_since_update} seconds ago).")
                
        # Layman terminology description
        step_desc = latest_app.get("current_step")
        if not step_desc:
            if status == "Queued":
                step_desc = "Added to queue. Waiting for background worker to start..."
            elif status == "Running":
                step_desc = "Running automation worker..."
            elif status == "Waiting for User Input":
                if latest_app.get("error_message") and "login" in latest_app["error_message"].lower():
                    step_desc = "LinkedIn login required! Please sign in in the opened browser window."
                else:
                    step_desc = "Paused: Waiting for candidate screening question input..."
            elif status == "Waiting for Final Review":
                step_desc = "Ready for submission. Please approve application preview..."
            elif status == "Completed":
                step_desc = "Application submitted successfully!"
            elif status == "Failed":
                step_desc = "Application process failed."
            elif status == "Cancelled":
                step_desc = "Application process cancelled."
                
        if step_desc:
            st.info(f"🤖 **Current Action:** {step_desc}")
            
        # Render live browser screenshot
        if latest_app["screenshot_path"] and os.path.exists(latest_app["screenshot_path"]):
            st.image(latest_app["screenshot_path"], caption=f"Live Browser View (ID: {app_id})")
            
        # HITL Input Form if waiting
        if status == "Waiting for User Input":
            prompt = get_pending_hitl_prompt(app_id)
            if prompt:
                st.info("💡 **Automation paused: The agent needs your input to continue.**")
                st.markdown(f"**Question:** {prompt['question_text']}")
                ans_key = f"ans_login_tab_hitl_{prompt['id']}"
                if prompt["input_type"] == "radio" and prompt["options"]:
                    user_answer = st.radio("Choose an option:", options=prompt["options"], key=ans_key)
                elif prompt["input_type"] == "select" and prompt["options"]:
                    user_answer = st.selectbox("Select an option:", options=prompt["options"], key=ans_key)
                else:
                    user_answer = st.text_input("Enter your answer:", key=ans_key)
                    
                if st.button("Submit Answer", key=f"btn_submit_login_tab_hitl_{prompt['id']}"):
                    if not user_answer.strip() if isinstance(user_answer, str) else not user_answer:
                        st.error("Please enter a valid answer.")
                    else:
                        resolve_hitl_prompt(prompt["id"], user_answer)
                        update_application_status(app_id, "Running")
                        st.success("Answer submitted. Application resuming...")
                        st.rerun()
            elif latest_app["error_message"] and "login" in latest_app["error_message"].lower():
                st.warning("🔑 **LinkedIn Authentication Required**")
                st.markdown(
                    "The automated browser needs you to sign in to LinkedIn.\n\n"
                    "**Instructions:**\n"
                    "1. Look at your desktop for the automated Chrome browser window that popped up.\n"
                    "2. Log in manually inside that window.\n"
                    "3. The script will automatically detect your login and proceed.\n\n"
                    "Note: You must log in inside the **automated Chrome window**, not your normal browser."
                )
                st.link_button("🌐 Go to LinkedIn Login (for reference)", "https://www.linkedin.com/login")
                
                if st.button("❌ Cancel Application", key=f"btn_cancel_login_login_tab_hitl_{app_id}"):
                    update_application_status(app_id, "Cancelled")
                    st.info("Application cancelled.")
                    st.rerun()
                    
        # Approval/Cancel Form if waiting for final review
        if status == "Waiting for Final Review":
            st.warning("🔍 **Final Review Gate: Please review the screenshot above and approve submission.**")
            col_app, col_can = st.columns(2)
            with col_app:
                if st.button("✅ Approve & Submit", key=f"btn_approve_login_tab_hitl_{app_id}"):
                    update_application_status(app_id, "Completed")
                    st.success("Approved! Submitting application...")
                    st.rerun()
            with col_can:
                if st.button("❌ Cancel Application", key=f"btn_cancel_login_tab_hitl_{app_id}"):
                    update_application_status(app_id, "Cancelled")
                    st.info("Application cancelled.")
                    st.rerun()

        # Add Cancel button for active Running or Queued states to allow manual recovery
        if status in ["Running", "Queued"]:
            if st.button("❌ Cancel Application", key=f"btn_cancel_run_login_tab_hitl_{app_id}"):
                update_application_status(app_id, "Cancelled")
                st.info("Application cancelled.")
                st.rerun()
                
        # Layman logs
        with st.expander("📟 Live Worker Logs (Layman Terminology)", expanded=True):
            logs = get_application_logs(app_id)
            if not logs:
                st.caption("No logs recorded for this application yet.")
            else:
                log_lines = []
                for log in logs:
                    ts = log["timestamp"]
                    if "T" in ts:
                        time_part = ts.split("T")[1].split(".")[0]
                    else:
                        time_part = ts
                    lvl = log["level"]
                    step = log["step"]
                    msg = log["message"]
                    
                    # Convert or present message format
                    escaped_msg = msg.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("\n", " ")
                    log_lines.append(f"`{time_part}` | **{lvl}** | *{step}* | {escaped_msg}")
                    
                st.markdown("\n\n".join(log_lines))


# TAB 6: Easy Apply Session Login & Automation
with tab_easy_apply:
    # 1. LinkedIn Authentication & Session Manager
    st.subheader("Easy Apply Authentication & Session Manager")
    st.write(
        "Manage your LinkedIn login state for Easy Apply here. You can check if a valid session exists, "
        "or open an interactive automated browser window to perform a manual login."
    )
    
    # Session status containers
    if "easy_session_checked" not in st.session_state:
        st.session_state.easy_session_checked = False
    if "easy_session_valid" not in st.session_state:
        st.session_state.easy_session_valid = None
        
    def run_check_easy_session():
        with st.spinner("Checking LinkedIn session status..."):
            try:
                res = asyncio.run(easy_check_linkedin_session())
                st.session_state.easy_session_valid = res.get("logged_in", False)
                st.session_state.easy_session_checked = True
            except Exception as e:
                st.error(f"Error checking session: {e}")
                st.session_state.easy_session_valid = False
                st.session_state.easy_session_checked = True

    # Check status button
    if st.button("Check LinkedIn Login Status", key="btn_check_easy_session"):
        run_check_easy_session()
        st.rerun()
        
    # Render current status
    if st.session_state.easy_session_checked:
        if st.session_state.easy_session_valid:
            st.success("✅ **Active LinkedIn session verified successfully!** Cookies are loaded and valid.")
        else:
            st.warning("⚠️ **No active LinkedIn session found.** You are currently not signed in or session cookies are expired.")
    else:
        st.info("ℹ️ Login status not checked yet for this browser window. Click the button above to verify.")
        
    st.divider()
    
    # 2. Authenticate/Renew Session
    st.subheader("Authenticate/Renew Session")
    st.write(
        "If your session has expired or does not exist, click below to open a headful Chromium window. "
        "Once the browser opens, log in to your LinkedIn account manually. "
        "The background worker will automatically detect the sign-in, save your session state on success, and close the window."
    )
    
    if st.button("Launch LinkedIn Interactive Login", key="btn_launch_easy_login"):
        with st.spinner("Launching headful Chromium window. Please locate it and sign in manually..."):
            try:
                res = asyncio.run(easy_login_to_linkedin(timeout_seconds=300))
                if res.get("status") == "success":
                    st.success("🎉 **Success:** LinkedIn logged in successfully. Cookies saved!")
                    st.session_state.easy_session_valid = True
                    st.session_state.easy_session_checked = True
                else:
                    st.error(f"❌ **Failed:** {res.get('message', 'Login timed out or failed.')}")
            except Exception as e:
                st.error(f"Error executing login: {e}")
                
    st.divider()

    # 3. Resume Upload & Automated Apply
    st.subheader("📄 Resume Upload & Automated Apply")
    
    # File Uploader
    uploaded_file_easy = st.file_uploader("Upload your Resume (PDF format)", type=["pdf"], key="resume_uploader_easy_tab")
    
    if uploaded_file_easy is not None and st.session_state.uploaded_resume_name != uploaded_file_easy.name:
        with st.spinner("AI parsing of resume in progress..."):
            parsed_profile = None
            use_local_cache = False
            file_bytes = uploaded_file_easy.read()
            
            try:
                # 1. Read bytes and parse
                parsed_profile = parse_pdf_resume(file_bytes)
            except Exception as e:
                # Fallback to local pre-parsed JSON if it exists
                script_dir = os.path.dirname(os.path.abspath(__file__))
                local_profile_path = os.path.join(script_dir, "candidate_profile.json")
                if os.path.exists(local_profile_path):
                    try:
                        import json
                        with open(local_profile_path, "r", encoding="utf-8") as f:
                            parsed_profile = json.load(f)
                        use_local_cache = True
                    except Exception:
                        parsed_profile = None
                
                if parsed_profile is None:
                    err_msg = str(e)
                    if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "quota" in err_msg.lower():
                        st.error("⚠️ **Gemini API Quota/Rate Limit Exceeded**: You have hit the requests limit on the Gemini API free tier. Please wait 30 seconds and try again.")
                    else:
                        st.error(f"Error parsing resume: {err_msg}")
            
            if parsed_profile is not None:
                try:
                    # 2. Save file temporarily
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(script_dir, "temp_resumes")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    import uuid
                    temp_filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
                    temp_path = os.path.join(temp_dir, temp_filename)
                    
                    with open(temp_path, "wb") as f:
                        f.write(file_bytes)
                        
                    # 3. Update session states
                    st.session_state.resume_temp_path = temp_path
                    parsed_profile["personal_info"]["resume_path"] = temp_path
                    st.session_state.candidate_profile = parsed_profile
                    st.session_state.uploaded_resume_name = uploaded_file_easy.name
                    
                    if use_local_cache:
                        st.success(f"Resume '{uploaded_file_easy.name}' loaded successfully! (⚠️ Loaded from pre-parsed local cache due to Gemini rate limits)")
                    else:
                        st.success(f"Resume '{uploaded_file_easy.name}' parsed successfully! Details are loaded for this session.")
                except Exception as save_err:
                    st.error(f"Failed to load parsed profile: {str(save_err)}")
                
    st.divider()

    # View Session Candidate Profile Summary
    profile_data = st.session_state.candidate_profile
    has_uploaded = st.session_state.uploaded_resume_name is not None
    
    if has_uploaded:
        raw_name = profile_data.get('personal_info', {}).get('full_name', 'N/A')
        raw_email = profile_data.get('personal_info', {}).get('email', 'N/A')
        raw_phone = profile_data.get('personal_info', {}).get('phone', 'N/A')
        raw_loc = profile_data.get('personal_info', {}).get('location', 'N/A')
        
        st.info("ℹ️ **Session Active View:** You can see your actual details below. Refreshing the browser will wipe this data.")
        with st.expander("👤 View Session Candidate Profile Information (Unmasked)", expanded=True):
            st.markdown(f"**Name:** {raw_name}")
            st.markdown(f"**Email:** {raw_email}")
            st.markdown(f"**Phone:** {raw_phone}")
            st.markdown(f"**Location:** {raw_loc}")
            st.markdown(f"**Resume File:** `{st.session_state.uploaded_resume_name}`")
    else:
        with st.expander("👤 View Session Candidate Profile Information (Default Protected View)", expanded=False):
            st.markdown(f"**Name:** {MOCK_PROFILE['personal_info']['full_name']}")
            st.markdown(f"**Email:** {MOCK_PROFILE['personal_info']['email']}")
            st.markdown(f"**Phone:** {MOCK_PROFILE['personal_info']['phone']}")
            st.markdown(f"**Location:** {MOCK_PROFILE['personal_info']['location']}")
            st.caption("Upload your resume above to view and apply with your own profile.")
            
    st.divider()
    
    # 4. Input Search Discovery Parameters & Trigger Application
    if "easy_discovered_jobs" not in st.session_state:
        st.session_state.easy_discovered_jobs = []
        
    st.subheader("🔍 Easy Apply Job Discovery Options")
    col_k, col_l = st.columns(2)
    with col_k:
        job_keywords_easy = st.text_input("Target Job Role Keywords (comma-separated, up to 10)", placeholder="e.g. Data Scientist, Machine Learning Engineer", key="job_keywords_easy_tab")
    with col_l:
        location_easy = st.text_input("Location", placeholder="e.g. Hyderabad", key="location_easy_tab")
        
    col_x, _ = st.columns(2)
    with col_x:
        experience_easy = st.number_input("Work Experience (Years)", min_value=0.0, max_value=25.0, value=2.0, step=0.5, key="experience_easy_tab")
        
    search_clicked = st.button("🔍 Search Jobs", key="btn_search_easy_jobs")
    if search_clicked:
        if not job_keywords_easy.strip():
            st.error("Please enter target job keywords.")
        elif not location_easy.strip():
            st.error("Please enter preferred location.")
        else:
            keywords_list = [k.strip() for k in job_keywords_easy.split(",") if k.strip()][:10]
            with st.spinner("Discovering suitable Easy Apply jobs..."):
                try:
                    jobs_discovered = discover_easy_apply_jobs(
                        target_job_keywords=keywords_list,
                        preferred_location=location_easy,
                        years_of_experience=experience_easy
                    )
                    st.session_state.easy_discovered_jobs = jobs_discovered
                    st.success(f"Discovered {len(jobs_discovered)} Easy Apply jobs matching criteria!")
                except Exception as e:
                    st.error(f"Error executing discovery agent: {e}")
                    
    if st.session_state.easy_discovered_jobs:
        st.subheader("📋 Discovered Suitable Easy Apply Jobs")
        
        # Display jobs in cards layout with a checkbox on the left
        selected_jobs = []
        for idx, job in enumerate(st.session_state.easy_discovered_jobs):
            col_checkbox, col_card = st.columns([0.05, 0.95])
            with col_checkbox:
                # Add check box for each job (default checked)
                is_selected = st.checkbox("", value=True, key=f"select_job_{idx}_{job['job_url']}")
            with col_card:
                st.markdown(f"""
                <div style="background-color: white; border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 16px; font-weight: 600; color: #0077b5;">🔗 <a href="{job['job_url']}" target="_blank" style="color: #0077b5; text-decoration: none;">{job['job_title']}</a></div>
                    <div style="font-size: 13px; color: #555; margin-top: 4px; margin-bottom: 8px;">
                        🏢 <strong>{job['company']}</strong> | 📍 {job['location']} | 📅 {job['posted']} | 🎓 {job['experience_level']}
                    </div>
                    <div style="font-size: 14px; color: #333; line-height: 1.4; border-top: 1px solid #f0f0f0; padding-top: 8px;">
                        Job description matching your preferences. Easy Apply is supported.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if is_selected:
                selected_jobs.append(job)
            
        # Trigger Bulk Apply button
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            trigger_selected = st.button("🚀 Start Bulk Automated Apply", key="btn_trigger_bulk_apply_easy")
        with col_btn2:
            trigger_all = st.button("⚡ Apply to All Listed Jobs", key="btn_trigger_apply_all_easy")
            
        if trigger_selected or trigger_all:
            if not st.session_state.get("candidate_profile"):
                st.error("Cannot apply. Please upload your resume to build your candidate profile first.")
            else:
                profile = st.session_state.candidate_profile
                
                # Determine which jobs to apply to
                if trigger_selected:
                    jobs_to_apply = selected_jobs
                else:
                    jobs_to_apply = st.session_state.easy_discovered_jobs
                    
                if not jobs_to_apply:
                    st.error("No jobs selected. Please check at least one job to apply.")
                else:
                    triggered_count = 0
                    for job in jobs_to_apply:
                        res = easy_apply_for_job(
                            job_url=job["job_url"],
                            job_title=job["job_title"],
                            company=job["company"],
                            candidate_profile=profile,
                            resume_path=st.session_state.resume_temp_path,
                            li_username=st.session_state.get("linkedin_username"),
                            li_password=st.session_state.get("linkedin_password")
                        )
                        if res["status"] == "success":
                            triggered_count += 1
                    
                    if triggered_count > 0:
                        st.success(f"Successfully queued and spawned workers for {triggered_count} job application(s)!")
                        st.rerun()
                    else:
                        st.error("Failed to trigger applications.")

    # 5. Live Progress and Screenshot of working page
    st.divider()
    st.subheader("📟 Live Application Progress & Screenshot")
    
    apps_list = get_all_applications()
    if not apps_list:
        st.info("No applications triggered yet.")
    else:
        # Create option mapping for all triggered applications
        options_map = {}
        for app in apps_list:
            app_id = app["id"]
            job_title = app.get("job_title") or "LinkedIn Job"
            company = app.get("company") or "Unknown Company"
            status = app.get("status") or "Queued"
            display_str = f"{job_title} at {company} (ID: {app_id}) - [{status}]"
            options_map[display_str] = app
            
        selected_option = st.selectbox(
            "Select application to monitor:",
            options=list(options_map.keys()),
            key="easy_tab_app_monitor_selector"
        )
        latest_app = options_map[selected_option]
        app_id = latest_app["id"]
        status = latest_app["status"]
        job_title = latest_app["job_title"] or "LinkedIn Job"
        company = latest_app["company"] or "Unknown Company"
        
        # Calculate time since last update to identify if stuck/looping
        try:
            from datetime import datetime
            updated_at = datetime.fromisoformat(latest_app["updated_at"])
            delta = datetime.now() - updated_at
            seconds_since_update = int(delta.total_seconds())
        except Exception:
            seconds_since_update = 0
            
        st.markdown(f"#### Latest Application: **{job_title}** at **{company}** (ID: {app_id})")
        
        # Render status alerts
        if status == "Completed":
            st.success("✅ **Application Completed successfully!**")
        elif status == "Failed":
            st.error(f"❌ **Application Failed:** {latest_app['error_message']}")
        elif status == "Cancelled":
            st.info("⚪ **Application was Cancelled.**")
        elif status == "Waiting for User Input":
            st.warning("⚠️ **Action Required:** The automation is paused and waiting for your input (see form below).")
        elif status == "Waiting for Final Review":
            st.warning("🔍 **Final Review Gate:** Ready for submission. Please approve the preview below.")
        else: # Queued or Running
            st.info(f"⏳ **Status:** {status}...")
            if status == "Running" and seconds_since_update > 30:
                st.warning(
                    f"⚠️ **Stuck/Loop Alert:** No progress updates have been received for **{seconds_since_update} seconds**. "
                    "The worker process might be stuck, looping, or waiting on a slow page load."
                )
            elif status == "Running":
                st.success(f"⚡ **Active Progress:** Worker is actively executing (last update {seconds_since_update} seconds ago).")
                
        # Layman terminology description
        step_desc = latest_app.get("current_step")
        if not step_desc:
            if status == "Queued":
                step_desc = "Added to queue. Waiting for background worker to start..."
            elif status == "Running":
                step_desc = "Running automation worker..."
            elif status == "Waiting for User Input":
                if latest_app.get("error_message") and "login" in latest_app["error_message"].lower():
                    step_desc = "LinkedIn login required! Please sign in in the opened browser window."
                else:
                    step_desc = "Paused: Waiting for candidate screening question input..."
            elif status == "Waiting for Final Review":
                step_desc = "Ready for submission. Please approve application preview..."
            elif status == "Completed":
                step_desc = "Application submitted successfully!"
            elif status == "Failed":
                step_desc = "Application process failed."
            elif status == "Cancelled":
                step_desc = "Application process cancelled."
                
        if step_desc:
            st.info(f"🤖 **Current Action:** {step_desc}")
            
        # Render live browser screenshot
        if latest_app["screenshot_path"] and os.path.exists(latest_app["screenshot_path"]):
            st.image(latest_app["screenshot_path"], caption=f"Live Browser View (ID: {app_id})")
            
        # HITL Input Form if waiting
        if status == "Waiting for User Input":
            prompt = get_pending_hitl_prompt(app_id)
            if prompt:
                st.info("💡 **Automation paused: The agent needs your input to continue.**")
                st.markdown(f"**Question:** {prompt['question_text']}")
                ans_key = f"ans_easy_tab_hitl_{prompt['id']}"
                if prompt["input_type"] == "radio" and prompt["options"]:
                    user_answer = st.radio("Choose an option:", options=prompt["options"], key=ans_key)
                elif prompt["input_type"] == "select" and prompt["options"]:
                    user_answer = st.selectbox("Select an option:", options=prompt["options"], key=ans_key)
                else:
                    user_answer = st.text_input("Enter your answer:", key=ans_key)
                    
                if st.button("Submit Answer", key=f"btn_submit_easy_tab_hitl_{prompt['id']}"):
                    if not user_answer.strip() if isinstance(user_answer, str) else not user_answer:
                        st.error("Please enter a valid answer.")
                    else:
                        resolve_hitl_prompt(prompt["id"], user_answer)
                        update_application_status(app_id, "Running")
                        st.success("Answer submitted. Application resuming...")
                        st.rerun()
            elif latest_app["error_message"] and "login" in latest_app["error_message"].lower():
                st.warning("🔑 **LinkedIn Authentication Required**")
                st.markdown(
                    "The automated browser needs you to sign in to LinkedIn.\n\n"
                    "**Instructions:**\n"
                    "1. Look at your desktop for the automated Chrome browser window that popped up.\n"
                    "2. Log in manually inside that window.\n"
                    "3. The script will automatically detect your login and proceed.\n\n"
                    "Note: You must log in inside the **automated Chrome window**, not your normal browser."
                )
                st.link_button("🌐 Go to LinkedIn Login (for reference)", "https://www.linkedin.com/login")
                
                if st.button("❌ Cancel Application", key=f"btn_cancel_login_easy_tab_hitl_{app_id}"):
                    update_application_status(app_id, "Cancelled")
                    st.info("Application cancelled.")
                    st.rerun()
                    
        # Approval/Cancel Form if waiting for final review
        if status == "Waiting for Final Review":
            st.warning("🔍 **Final Review Gate: Please review the screenshot above and approve submission.**")
            col_app, col_can = st.columns(2)
            with col_app:
                if st.button("✅ Approve & Submit", key=f"btn_approve_easy_tab_hitl_{app_id}"):
                    update_application_status(app_id, "Completed")
                    st.success("Approved! Submitting application...")
                    st.rerun()
            with col_can:
                if st.button("❌ Cancel Application", key=f"btn_cancel_easy_tab_hitl_{app_id}"):
                    update_application_status(app_id, "Cancelled")
                    st.info("Application cancelled.")
                    st.rerun()

        # Add Cancel button for active Running or Queued states to allow manual recovery
        if status in ["Running", "Queued"]:
            if st.button("❌ Cancel Application", key=f"btn_cancel_run_easy_tab_hitl_{app_id}"):
                update_application_status(app_id, "Cancelled")
                st.info("Application cancelled.")
                st.rerun()
                
        # Layman logs
        with st.expander("📟 Live Worker Logs (Layman Terminology)", expanded=True):
            logs = get_application_logs(app_id)
            if not logs:
                st.caption("No logs recorded for this application yet.")
            else:
                log_lines = []
                for log in logs:
                    ts = log["timestamp"]
                    if "T" in ts:
                        time_part = ts.split("T")[1].split(".")[0]
                    else:
                        time_part = ts
                    lvl = log["level"]
                    step = log["step"]
                    msg = log["message"]
                    
                    # Convert or present message format
                    escaped_msg = msg.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("\n", " ")
                    log_lines.append(f"`{time_part}` | **{lvl}** | *{step}* | {escaped_msg}")
                    
                st.markdown("\n\n".join(log_lines))

# Global Auto-polling: if any application is active, rerun Streamlit every 1.5 seconds to ensure live updates
active_apps = [ap for ap in get_all_applications() if ap["status"] in ["Queued", "Running", "Waiting for User Input", "Waiting for Final Review"]]
if active_apps:
    import time
    time.sleep(1.5)
    st.rerun()

