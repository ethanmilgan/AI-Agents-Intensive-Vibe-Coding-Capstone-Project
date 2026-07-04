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

from app.application_agent.form_filler_agent import form_filler_agent, FormFillingResult

def test_form_filler_agent_structure() -> None:
    """Verify that form_filler_agent has correct configuration properties."""
    assert form_filler_agent.name == "form_filler_agent"
    assert form_filler_agent.output_key == "form_filling_result"
    assert form_filler_agent.output_schema == FormFillingResult
    assert "AI Job Application Form Filling Agent" in form_filler_agent.instruction

@pytest.mark.asyncio
async def test_form_filler_agent_run_success() -> None:
    """Test form_filler_agent when all required fields can be successfully answered from the resume."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=form_filler_agent,
        app_name="app",
        session_service=session_service,
        auto_create_session=True,
    )
    
    resume_text = """
    Name: John Doe
    Email: john.doe@example.com
    Phone: +1-555-0199
    Experience:
    - Worked as Python developer for 3 years
    Skills: Python, SQL
    """
    
    prompt = f"""
    Resume:
    {resume_text}

    Job URL:
    https://www.linkedin.com/jobs/view/987654

    Current application page information:
    - First Name (type: text, required: True)
    - Email Address (type: text, required: True)
    - Years of Python (type: number, required: True)

    Previous answers collected:
    None
    """
    
    user_message = types.Content(parts=[types.Part.from_text(text=prompt)])
    events = runner.run_async(
        user_id="test_user_success",
        session_id="test_session_success",
        new_message=user_message,
    )
    
    async for event in events:
        pass
        
    session = await session_service.get_session(
        user_id="test_user_success",
        session_id="test_session_success",
        app_name="app"
    )
    result = session.state.get("form_filling_result")
    assert result is not None
    assert result["status"] == "CONTINUE"
    actions = result["actions"]
    assert len(actions) > 0
    
    # Verify values match resume info
    fields = {act["field"]: act for act in actions}
    assert "First Name" in fields
    assert "John" in fields["First Name"]["value"]
    
    assert "Email Address" in fields
    assert "john.doe@example.com" in fields["Email Address"]["value"]
    
    assert "Years of Python" in fields
    assert "3" in str(fields["Years of Python"]["value"])

@pytest.mark.asyncio
async def test_form_filler_agent_run_missing_fields() -> None:
    """Test form_filler_agent when a required field cannot be determined from the resume."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=form_filler_agent,
        app_name="app",
        session_service=session_service,
        auto_create_session=True,
    )
    
    resume_text = """
    Name: John Doe
    Email: john.doe@example.com
    """
    
    prompt = f"""
    Resume:
    {resume_text}

    Job URL:
    https://www.linkedin.com/jobs/view/987654

    Current application page information:
    - First Name (type: text, required: True)
    - Expected Salary (type: number, required: True)
    - Notice Period (type: number, required: True)

    Previous answers collected:
    None
    """
    
    user_message = types.Content(parts=[types.Part.from_text(text=prompt)])
    events = runner.run_async(
        user_id="test_user_missing",
        session_id="test_session_missing",
        new_message=user_message,
    )
    
    async for event in events:
        pass
        
    session = await session_service.get_session(
        user_id="test_user_missing",
        session_id="test_session_missing",
        app_name="app"
    )
    
    result = session.state.get("form_filling_result")
    assert result is not None
    assert result["status"] == "NEED_USER_INPUT"
    assert "Expected Salary" in result["missing_fields"]
    assert "Notice Period" in result["missing_fields"]
