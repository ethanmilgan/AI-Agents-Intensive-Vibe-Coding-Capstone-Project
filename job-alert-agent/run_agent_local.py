import asyncio
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agent import root_agent

async def main():
    print("Initializing Runner...")
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
        auto_create_session=True,
    )
    
    prompt = "Find Python Developer jobs in Seattle and email them to candidate@example.com."
    print(f"Running Agent with prompt: {prompt}")
    
    # runner.run returns a Generator of Event
    # Let's run it and print events
    user_message = types.Content(parts=[types.Part.from_text(text=prompt)])
    events = runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=user_message,
        state_delta={"recipient_email": "candidate@example.com"},
    )
    
    async for event in events:
        # Check if event has message and print it
        if event.message:
            for part in event.message.parts:
                if part.text:
                    print(part.text, end="")
                    
        # Check for function calls
        for tc in event.get_function_calls():
            print(f"\n[Tool Call]: {tc.name}({tc.args})")
            
        # Check for function responses
        for tr in event.get_function_responses():
            print(f"\n[Tool Result]: {tr.response}")

        if event.output:
            print(f"\n[Output]: {event.output}")

if __name__ == "__main__":
    asyncio.run(main())
