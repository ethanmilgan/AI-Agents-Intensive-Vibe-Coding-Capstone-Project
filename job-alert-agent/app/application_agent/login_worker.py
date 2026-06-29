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
    
    try:
        with sync_playwright() as p:
            # Force headless=False to ensure the browser window is visible on the screen
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            if app_id:
                add_application_log(app_id, "INFO", "LinkedIn", "Opening LinkedIn login page for user sign-in...")
                update_application_step(app_id, "LinkedIn login required! Please sign in in the opened browser window.")
                update_application_status(app_id, "Waiting for User Input", error_message="LinkedIn login required")
                
            page.goto("https://www.linkedin.com/login", wait_until="load", timeout=30000)
            
            start_time = time.time()
            logged_in = False
            
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
                    
                # Small wait to avoid pegging CPU
                page.wait_for_timeout(2000)
                
            if logged_in:
                # Wait a bit for storage state stability (cookies fully written)
                page.wait_for_timeout(3000)
                # Save storage state (cookies, localStorage, etc.)
                context.storage_state(path=session_path)
                
                if app_id:
                    add_application_log(app_id, "INFO", "LinkedIn", "Successfully authenticated LinkedIn session. Session saved.")
                    update_application_status(app_id, "Running")
                    
                browser.close()
                return True
            else:
                if app_id:
                    add_application_log(app_id, "ERROR", "LinkedIn", "LinkedIn authentication timed out or was cancelled.")
                    update_application_status(app_id, "Failed", error_message="LinkedIn login timed out or cancelled")
                browser.close()
                return False
                
    except Exception as e:
        error_msg = f"Exception occurred during manual LinkedIn login: {str(e)}"
        print(error_msg)
        if app_id:
            add_application_log(app_id, "ERROR", "LinkedIn", error_msg)
            update_application_status(app_id, "Failed", error_message=error_msg)
            
    return False
