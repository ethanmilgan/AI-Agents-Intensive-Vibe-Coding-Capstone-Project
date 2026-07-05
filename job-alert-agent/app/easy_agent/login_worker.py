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
import time
from playwright.sync_api import sync_playwright
from app.database import add_application_log, update_application_status, update_application_step

def get_session_path() -> str:
    """Gets the path to the LinkedIn session storage state JSON file."""
    profile_dir = os.environ.get("PLAYWRIGHT_PROFILE_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".playwright_profile"
    )
    os.makedirs(profile_dir, exist_ok=True)
    return os.path.join(profile_dir, "linkedin_cookies.json")

def check_linkedin_session_sync(headless: bool = True) -> bool:
    """Checks if the saved session is still valid by opening the LinkedIn feed page.
    
    Args:
        headless: Whether to run the browser headlessly.
        
    Returns:
        True if the session is valid and we are logged in, False otherwise.
    """
    session_path = get_session_path()
    if not os.path.exists(session_path):
        return False
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                storage_state=session_path,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Go to feed page
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=20000)
            page.wait_for_timeout(2000) # Wait for potential redirects
            
            current_url = page.url
            # If we are still on /feed/ and not redirected to sign-in/welcome/login
            if "linkedin.com/feed" in current_url:
                browser.close()
                return True
                
            # Double check for global-nav menu or signout elements as backup
            if page.locator(".global-nav").is_visible(timeout=3000):
                browser.close()
                return True
                
            browser.close()
    except Exception as e:
        print(f"Error checking session: {e}")
        
    return False

def login_to_linkedin_sync(app_id: int = None, timeout_seconds: int = 300) -> bool:
    """Launches a headful browser for manual login and saves the session state.
    
    Args:
        app_id: Optional ID of the database application record to log steps and updates.
        timeout_seconds: Max seconds to wait for manual login before timing out.
        
    Returns:
        True if logged in successfully and session saved, False otherwise.
    """
    session_path = get_session_path()
    
    # Load env variables for credentials
    from dotenv import load_dotenv
    # Find .env inside adk_agents folder
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "adk_agents", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        
    li_username = os.environ.get("LINKEDIN_USERNAME")
    li_password = os.environ.get("LINKEDIN_PASSWORD")
    
    try:
        with sync_playwright() as p:
            # Force headless=False to ensure the browser window is visible on the screen by default
            headless_mode = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() in ("true", "1")
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                if app_id:
                    add_application_log(app_id, "INFO", "LinkedIn", "Opening LinkedIn login page...")
                    update_application_step(app_id, "Navigating to LinkedIn login page.")
                    update_application_status(app_id, "Running")
                    
                page.goto("https://www.linkedin.com/login", wait_until="load", timeout=30000)
                
                # Check if already logged in
                already_logged_in = False
                if "linkedin.com/feed" in page.url:
                    already_logged_in = True
                else:
                    try:
                        if page.locator(".global-nav").is_visible(timeout=2000):
                            already_logged_in = True
                    except Exception:
                        pass
                
                if not already_logged_in:
                    # Enter credentials and click submit
                    if li_username and li_password:
                        if app_id:
                            add_application_log(app_id, "INFO", "LinkedIn", f"Entering credentials for username: {li_username}...")
                            update_application_step(app_id, f"Submitting LinkedIn credentials for {li_username}.")
                        
                        page.locator("#username").fill(li_username)
                        page.locator("#password").fill(li_password)
                        page.locator("button[type='submit']").click()
                        page.wait_for_timeout(3000)
                        
                start_time = time.time()
                logged_in = False
                prompt_created = False
                prompt_id = None
                
                while time.time() - start_time < timeout_seconds:
                    # Check if browser is closed
                    if page.is_closed():
                        if app_id:
                            add_application_log(app_id, "WARNING", "LinkedIn", "Browser was closed before login completed.")
                        break
                        
                    current_url = page.url
                    if "linkedin.com/feed" in current_url:
                        logged_in = True
                        break
                        
                    try:
                        # Alternative check: is the global navigation bar visible?
                        if page.locator(".global-nav").is_visible(timeout=1000):
                            logged_in = True
                            break
                    except Exception:
                        pass
                    
                    # Check if LinkedIn prompts for verification (checkpoint/challenge)
                    is_checkpoint = "checkpoint" in current_url or "challenge" in current_url
                    if not is_checkpoint:
                        try:
                            # Check if any pin or code input is visible on screen
                            if (page.locator("input[id*='pin']").is_visible(timeout=500) or 
                                page.locator("input[id*='code']").is_visible(timeout=500) or
                                page.locator("input[name*='pin']").is_visible(timeout=500) or
                                page.locator("input[name*='code']").is_visible(timeout=500)):
                                is_checkpoint = True
                        except Exception:
                            pass
                    
                    if is_checkpoint and not prompt_created and app_id:
                        add_application_log(app_id, "INFO", "LinkedIn", "2-step verification code / OTP requested by LinkedIn.")
                        from app.database import add_hitl_prompt
                        prompt_id = add_hitl_prompt(
                            app_id=app_id,
                            question_text="Please enter the LinkedIn 2FA Verification Code / OTP sent to your email or phone:",
                            input_type="text"
                        )
                        update_application_step(app_id, "Waiting for user to enter 2FA verification code in Agent Console.")
                        update_application_status(app_id, "Waiting for User Input", error_message="LinkedIn 2FA Required")
                        prompt_created = True
                    
                    # If prompt is created, poll for user's answer
                    if prompt_created and prompt_id:
                        from app.database import get_hitl_prompt
                        prompt = get_hitl_prompt(prompt_id)
                        if prompt and prompt.get("status") == "Resolved" and prompt.get("answer_value"):
                            otp_code = prompt["answer_value"]
                            add_application_log(app_id, "INFO", "LinkedIn", "Received verification code from user. Entering it...")
                            update_application_step(app_id, "Submitting 2FA verification code.")
                            update_application_status(app_id, "Running")
                            
                            # Find the OTP code input element
                            pin_input = None
                            for selector in ["input[id*='pin']", "input[id*='code']", "input[name*='pin']", "input[name*='code']"]:
                                try:
                                    loc = page.locator(selector)
                                    if loc.is_visible(timeout=1000):
                                        pin_input = loc
                                        break
                                except Exception:
                                    pass
                            
                            if pin_input:
                                pin_input.fill(otp_code)
                                # Find submit button
                                submit_btn = None
                                for btn_sel in ["#email-pin-submit-button", "#two-step-submit-button", "button[type='submit']", "button[id*='submit']"]:
                                    try:
                                        btn = page.locator(btn_sel)
                                        if btn.is_visible(timeout=1000):
                                            submit_btn = btn
                                            break
                                    except Exception:
                                        pass
                                if submit_btn:
                                    submit_btn.click()
                                else:
                                    page.keyboard.press("Enter")
                            else:
                                # If no pin input found, try typing and pressing Enter
                                page.keyboard.type(otp_code)
                                page.keyboard.press("Enter")
                                
                            # Reset prompt tracking so we don't spam it or loop again
                            prompt_created = False
                            prompt_id = None
                            page.wait_for_timeout(5000)
                    
                    # Small wait to avoid pegging CPU
                    page.wait_for_timeout(2000)
                    
                if logged_in:
                    # Wait a bit for storage state stability (cookies fully written)
                    page.wait_for_timeout(3000)
                    # Save storage state (cookies, localStorage, etc.)
                    context.storage_state(path=session_path)
                    
                    if app_id:
                        add_application_log(app_id, "INFO", "LinkedIn", "Successfully authenticated LinkedIn session. Session saved.")
                        update_application_step(app_id, "LinkedIn login completed successfully.")
                        update_application_status(app_id, "Completed")
                        
                    browser.close()
                    return True
                else:
                    if app_id:
                        add_application_log(app_id, "ERROR", "LinkedIn", "LinkedIn authentication timed out or was cancelled.")
                        update_application_status(app_id, "Failed", error_message="LinkedIn login timed out or cancelled")
                    browser.close()
                    return False
            except Exception as e:
                # Capture error screenshot
                if app_id:
                    try:
                        screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "adk_agents", "screenshots")
                        os.makedirs(screenshot_dir, exist_ok=True)
                        screenshot_path = os.path.join(screenshot_dir, f"login_error_{app_id}.png")
                        page.screenshot(path=screenshot_path)
                        # Save screenshot path in DB
                        from app.database import get_db_connection
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE applications SET screenshot_path = ? WHERE id = ?", (screenshot_path, app_id))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass
                raise e
                
    except Exception as e:
        error_msg = f"Exception occurred during manual LinkedIn login: {str(e)}"
        print(error_msg)
        if app_id:
            add_application_log(app_id, "ERROR", "LinkedIn", error_msg)
            update_application_status(app_id, "Failed", error_message=error_msg)
            
    return False
