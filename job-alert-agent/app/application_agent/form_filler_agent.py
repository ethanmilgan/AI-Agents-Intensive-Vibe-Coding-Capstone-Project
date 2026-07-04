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

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class FormFieldAction(BaseModel):
    field: str = Field(description="The name or label of the field to fill")
    type: str = Field(description="The type of the field (e.g., text, number, select, radio, checkbox, upload)")
    value: Optional[str] = Field(None, description="The value to enter or select for the field. Use option text for select/radio/checkbox options.")
    file: Optional[str] = Field(None, description="The filename of the resume or file to upload, if type is upload")

class FormFillingResult(BaseModel):
    status: Literal["CONTINUE", "NEED_USER_INPUT"] = Field(
        description="Action status. Use CONTINUE if all fields can be filled or confidently inferred. Use NEED_USER_INPUT if any required field is missing or cannot be confidently inferred."
    )
    actions: Optional[List[FormFieldAction]] = Field(
        None, description="List of actions to perform. Required if status is CONTINUE."
    )
    missing_fields: Optional[List[str]] = Field(
        None, description="List of missing required fields or questions that need clarification. Required if status is NEED_USER_INPUT."
    )

form_filler_agent = Agent(
    name="form_filler_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an AI Job Application Form Filling Agent.\n"
        "Your responsibility is to intelligently complete a LinkedIn Easy Apply application using the user's resume and the current application form.\n\n"
        "Your goal is to maximize application accuracy while never fabricating information.\n\n"
        "## Inputs\n"
        "You will receive:\n"
        "1. Resume (PDF or extracted text)\n"
        "2. Job URL\n"
        "3. Current application page information, including:\n"
        "   - field labels\n"
        "   - field types\n"
        "   - required fields\n"
        "   - dropdown options\n"
        "   - radio buttons\n"
        "   - checkboxes\n"
        "   - validation messages\n"
        "4. Previous answers collected during this application (if any).\n\n"
        "## Responsibilities\n"
        "1. Read and understand the user's resume.\n"
        "2. Extract all relevant information including: Name, Email, Phone, Address, Education, Experience, Skills, Certifications, Projects, Work authorization.\n"
        "3. Match resume information to the current application fields.\n"
        "4. Answer questions using resume information whenever possible.\n"
        "5. Reuse answers already provided earlier in the same application.\n"
        "6. Never invent/fabricate information.\n"
        "7. If a required answer cannot be determined with high confidence, stop and request user input instead of guessing.\n\n"
        "## Decision Rules\n"
        "For every field:\n"
        "- If an exact answer exists in the resume: use it.\n"
        "- If the answer can be confidently inferred from the resume: use it.\n"
        "- If confidence is low: return NEED_USER_INPUT.\n\n"
        "Never fabricate:\n"
        "- salary\n"
        "- notice period\n"
        "- visa sponsorship\n"
        "- relocation preference\n"
        "- security clearance\n"
        "- citizenship\n"
        "- GPA\n"
        "- dates not present\n"
        "- certifications not present\n"
        "- skills not present\n\n"
        "## Resume Matching Rules Examples\n"
        "- Question: \"Years of Python\" | Resume: \"Python used for 3 years\" -> Answer: 3\n"
        "- Question: \"Have you worked with Spark?\" | Resume: \"PySpark\" -> Answer: Yes\n"
        "- Question: \"Highest Qualification\" | Resume: \"Bachelor of Technology\" -> Answer: Bachelor's Degree\n\n"
        "## File Upload Rules\n"
        "- If resume upload is required: Return an action to upload the provided resume.\n"
        "- If cover letter upload is required: Request user input (NEED_USER_INPUT) unless a cover letter has already been provided.\n\n"
        "Never generate browser commands.\n"
        "Never click buttons.\n"
        "Never navigate pages.\n"
        "Only decide what information should be entered into each field."
    ),
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_schema=FormFillingResult,
    output_key="form_filling_result",
)
