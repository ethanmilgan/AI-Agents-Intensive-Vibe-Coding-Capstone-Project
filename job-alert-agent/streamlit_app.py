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
tab_panel, tab_chat, tab_preview = st.tabs([
    "⚙️ Control & Settings", 
    "💬 Chat with Agent", 
    "📧 Job Alert Email Preview"
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
