#!/usr/bin/env python3
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
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to python path to resolve absolute imports correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agent import root_agent

async def main():
    env_path = os.path.join(project_root, ".env")
    
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"Loaded environment configuration from: {env_path}")
    else:
        print(f"Note: .env file not found at {env_path}. Proceeding with system environment variables.")

    # Retrieve job hunt parameters
    keywords = os.environ.get("JOB_KEYWORDS", "Python Developer")
    location = os.environ.get("JOB_LOCATION", "Seattle")
    recipient = os.environ.get("RECIPIENT_EMAIL", "candidate@example.com")
    experience = os.environ.get("JOB_EXPERIENCE", "Any Experience")
    frequency = os.environ.get("ALERT_FREQUENCY", "Daily")
    
    print("\n==============================================")
    print("      DAILY JOB HUNT UPDATE TRIGGER           ")
    print("==============================================")
    print(f"Keywords:   {keywords}")
    print(f"Location:   {location}")
    print(f"Experience: {experience}")
    print(f"Frequency:  {frequency}")
    print(f"Recipient:  {recipient}")
    print("==============================================\n")

    # Construct instructions for the Job Alert Agent
    experience_phrase = f"with experience years range '{experience}'" if experience != "Any Experience" else "at any experience level"
    frequency_phrase = f"posted in the last '{frequency.lower()}' frequency window"
    prompt = f"Find jobs matching keywords '{keywords}' in location '{location}' {experience_phrase} {frequency_phrase} and email them to {recipient}."
    
    print("Invoking Job Alert Agent directly...\n")
    
    try:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="app",
            session_service=session_service,
            auto_create_session=True,
        )
        
        user_message = types.Content(parts=[types.Part.from_text(text=prompt)])
        events = runner.run_async(
            user_id="daily_trigger_user",
            session_id="daily_trigger_session",
            new_message=user_message,
            state_delta={"recipient_email": recipient},
        )
        
        async for event in events:
            # Print streaming text response from the agent
            if event.message:
                for part in event.message.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
            
            # Print tool calls
            for tc in event.get_function_calls():
                print(f"\n[Tool Call]: {tc.name}({tc.args})", flush=True)
                
            # Print tool responses
            for tr in event.get_function_responses():
                print(f"\n[Tool Result]: {tr.response}", flush=True)
                
            if event.output:
                print(f"\n[Final Output]: {event.output}", flush=True)
                
        print("\n==============================================")
        print("Job Alert Agent execution completed successfully!")
        print("==============================================\n")
        
    except Exception as e:
        print(f"Error: Agent execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
