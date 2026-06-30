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

import sys
import os
import time
import json
import asyncio
from playwright.sync_api import sync_playwright
from app.database import (
    get_application,
    update_application_status,
    update_application_step,
    add_application_log,
    add_hitl_prompt,
    get_pending_hitl_prompt,
    get_hitl_prompt
)
from app.easy_agent.login_worker import check_linkedin_session_sync, login_to_linkedin_sync, get_session_path
from app.application_agent.form_filler_agent import form_filler_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

def is_linkedin_easy_apply(btn, href, btn_text) -> bool:
    if btn_text and "easy apply" in btn_text.lower():
        return True
    if href and "opensduiapplyflow=true" in href.lower():
        return True
    try:
        aria_label = btn.get_attribute("aria-label")
        if aria_label and ("linkedin apply" in aria_label.lower() or "easy apply" in aria_label.lower()):
            return True
    except Exception:
        pass
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python worker.py <application_id>")
        sys.exit(1)
        
    app_id = int(sys.argv[1])
    
    # Initialize directory for screenshots
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    screenshot_dir = os.path.join(root_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"app_{app_id}.png")
    
    # Step 1: Initialize Worker log
    add_application_log(app_id, "INFO", "Worker", f"Starting background worker process for application {app_id}.")
    update_application_status(app_id, "Running")
    update_application_step(app_id, "Initializing browser automation...")
    
    app = get_application(app_id)
    if not app:
        add_application_log(app_id, "ERROR", "Worker", f"Application {app_id} not found in database.")
        sys.exit(1)
        
    job_url = app.get("job_url", "")
    is_mock = job_url.startswith("file://")
    
    # Step 2: Handle LinkedIn Login
    add_application_log(app_id, "INFO", "LinkedIn", "Verifying LinkedIn authentication status.")
    
    if is_mock:
        add_application_log(app_id, "INFO", "LinkedIn", "Mock URL detected. Skipping real LinkedIn login check.")
    else:
        # Real URL, perform active session verification
        session_valid = check_linkedin_session_sync(headless=True)
        if not session_valid:
            add_application_log(app_id, "WARNING", "LinkedIn", "No active session found. Redirecting to manual login.")
            # Launch headful browser for user sign-in
            login_success = login_to_linkedin_sync(app_id=app_id)
            if not login_success:
                # login_to_linkedin_sync handles setting status to Failed and logging error
                sys.exit(1)
        else:
            add_application_log(app_id, "INFO", "LinkedIn", "Active LinkedIn session verified successfully.")
            
    # Step 3: Launch browser context for applying
    add_application_log(app_id, "INFO", "Browser", f"Launching browser context for navigating to {job_url}.")
    update_application_step(app_id, "Navigating to job application page...")
    
    headless_val = os.environ.get("BROWSER_HEADLESS", "False").lower() == "true"
    session_path = get_session_path()
    
    try:
        with sync_playwright() as p:
            # If mock, we don't load state; otherwise load stored cookies
            if is_mock or not os.path.exists(session_path):
                context = p.chromium.launch(headless=headless_val).new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
            else:
                context = p.chromium.launch(headless=headless_val).new_context(
                    storage_state=session_path,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                
            page = context.new_page()
            page.goto(job_url, wait_until="load", timeout=30000)
            add_application_log(app_id, "INFO", "Browser", f"Successfully loaded page: {page.title()}")
            
            # Step 4: Form Filling Phase
            add_application_log(app_id, "INFO", "Form", "Initiating form filling procedures.")
            
            # Click Easy Apply / Apply button if visible on the page
            easy_apply_selectors = [
                "button:has-text('Easy Apply')",
                "a:has-text('Easy Apply')",
                ".jobs-easy-apply-button",
                "button.jobs-apply-button",
                "a.jobs-apply-button",
                "a[href*='/apply/']",
                "a:has-text('Apply')",
                "button:has-text('Apply')"
            ]
            easy_apply_btn = None
            add_application_log(app_id, "INFO", "Browser", "Waiting for Apply button to load...")
            
            # Poll up to 15 seconds for Apply button to become visible
            start_wait = time.time()
            while time.time() - start_wait < 15:
                for sel in easy_apply_selectors:
                    try:
                        locator = page.locator(sel).first
                        if locator.is_visible(timeout=500):
                            easy_apply_btn = locator
                            break
                    except Exception:
                        pass
                if easy_apply_btn:
                    break
                page.wait_for_timeout(500)
                    
            if easy_apply_btn:
                # Capture button text to check if it contains 'Easy Apply'
                btn_text = ""
                try:
                    btn_text = easy_apply_btn.inner_text().strip()
                except Exception:
                    pass
                    
                # Listen for new pages/tabs
                new_pages = []
                def handle_new_page(p):
                    new_pages.append(p)
                context.on("page", handle_new_page)
                
                # Get the href attribute
                href = None
                try:
                    href = easy_apply_btn.get_attribute("href")
                except Exception:
                    pass
                
                direct_navigated = False
                if not is_mock and href and "/apply/" in href:
                    # Construct absolute URL if relative
                    if href.startswith("/"):
                        href = "https://www.linkedin.com" + href
                    add_application_log(app_id, "INFO", "Browser", f"Found apply link: {href}. Navigating directly to it...")
                    try:
                        # Shorter timeout of 15s and wait_until="domcontentloaded" for LinkedIn loading page
                        page.goto(href, wait_until="domcontentloaded", timeout=15000)
                        page.wait_for_timeout(3000)
                        direct_navigated = True
                    except Exception as e:
                        # Check if it navigated to an external site before timing out
                        current_url = page.url
                        if "linkedin.com" not in current_url and not current_url.startswith("file://"):
                            add_application_log(app_id, "INFO", "Browser", f"Redirected to external URL: {current_url}")
                            direct_navigated = True
                        else:
                            add_application_log(app_id, "WARNING", "Browser", f"Direct navigation failed: {e}. Falling back to click...")
                
                if not direct_navigated:
                    add_application_log(app_id, "INFO", "Browser", f"Found button '{btn_text}'. Clicking it...")
                    try:
                        easy_apply_btn.click(timeout=10000)
                        page.wait_for_timeout(3000)
                    except Exception as click_err:
                        add_application_log(app_id, "WARNING", "Browser", f"Click failed or timed out: {click_err}. Checking if page redirected...")
                
                # Check for redirection
                is_external = False
                external_url = ""
                
                if new_pages:
                    is_external = True
                    external_url = new_pages[0].url
                else:
                    current_url = page.url
                    # If current URL changed from initial job_url and is external
                    if current_url != job_url:
                        if ("linkedin.com" not in current_url and not current_url.startswith("file://")) or (current_url.startswith("file://") and "external" in current_url):
                            is_external = True
                            external_url = current_url
                
                if is_external:
                    err_msg = f"This job requires an external application. Redirected to: {external_url}. External job applications are not supported by the Easy Apply automation."
                    add_application_log(app_id, "INFO", "Browser", err_msg)
                    update_application_status(app_id, "External Application", error_message=err_msg)
                    
                    try:
                        if new_pages:
                            new_pages[0].screenshot(path=screenshot_path)
                        else:
                            page.screenshot(path=screenshot_path)
                        update_application_status(app_id, "External Application", screenshot_path=screenshot_path)
                    except Exception:
                        pass
                    
                    context.browser.close()
                    sys.exit(0)
                else:
                    try:
                        page.screenshot(path=screenshot_path)
                        update_application_status(app_id, "Running", screenshot_path=screenshot_path)
                    except Exception:
                        pass
            else:
                err_msg = "Apply button not found. The job page loaded, but no apply button was detected."
                add_application_log(app_id, "ERROR", "Browser", err_msg)
                update_application_status(app_id, "Failed", error_message=err_msg)
                context.browser.close()
                sys.exit(1)

            # Verify if modal is open
            modal_visible = False
            for m_sel in [".jobs-easy-apply-modal", "[role='dialog']"]:
                try:
                    if page.locator(m_sel).first.is_visible(timeout=10000):
                        modal_visible = True
                        break
                except Exception:
                    pass
                    
            if not modal_visible:
                # If modal is not open, check if it was an external apply button
                current_url = page.url
                is_easy = is_linkedin_easy_apply(easy_apply_btn, href, btn_text)
                if ("linkedin.com" not in current_url and not current_url.startswith("file://")) or not is_easy:
                    err_msg = "This job requires external application. The button is 'Apply' instead of 'Easy Apply'. External job applications are not supported by the Easy Apply automation."
                    add_application_log(app_id, "INFO", "Browser", err_msg)
                    update_application_status(app_id, "External Application", error_message=err_msg)
                    try:
                        page.screenshot(path=screenshot_path)
                        update_application_status(app_id, "External Application", screenshot_path=screenshot_path)
                    except Exception:
                        pass
                    context.browser.close()
                    sys.exit(0)
                else:
                    err_msg = "Easy Apply modal not open. The job details loaded, but the Easy Apply modal is missing or failed to open."
                    add_application_log(app_id, "ERROR", "Browser", err_msg)
                    update_application_status(app_id, "Failed", error_message=err_msg)
                    try:
                        page.screenshot(path=screenshot_path)
                        update_application_status(app_id, "Failed", screenshot_path=screenshot_path)
                    except Exception:
                        pass
                    context.browser.close()
                    sys.exit(1)

            # Javascript scanner string
            js_scanner = """
            () => {
              const modal = document.querySelector(".jobs-easy-apply-modal, [role='dialog']");
              if (!modal) return [];
              
              const fields = [];
              
              // 1. Text/number/email/tel inputs
              const inputs = modal.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="radio"]):not([type="checkbox"]):not([type="file"]), textarea');
              inputs.forEach(el => {
                if (el.offsetWidth === 0 && el.offsetHeight === 0) return;
                
                let labelText = "";
                if (el.id) {
                  const labelEl = document.querySelector(`label[for="${el.id}"]`);
                  if (labelEl) labelText = labelEl.innerText.trim();
                }
                if (!labelText) {
                  const parentLabel = el.closest('label');
                  if (parentLabel) labelText = parentLabel.innerText.trim();
                }
                if (!labelText) {
                  labelText = el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.name || "";
                }
                
                const isRequired = el.hasAttribute('required') || 
                                   el.getAttribute('aria-required') === 'true' || 
                                   labelText.includes('*') ||
                                   !!el.closest('.required');
                                   
                labelText = labelText.replace(/\\s+/g, ' ').replace(/\\s*\\*\\s*$/, '').trim();
                
                fields.push({
                  id: el.id || "",
                  name: el.name || "",
                  label: labelText || el.name || "Input Field",
                  type: el.type === 'number' ? 'number' : 'text',
                  required: !!isRequired,
                  options: null
                });
              });
              
              // 2. Selects
              const selects = modal.querySelectorAll('select');
              selects.forEach(el => {
                if (el.offsetWidth === 0 && el.offsetHeight === 0) return;
                
                let labelText = "";
                if (el.id) {
                  const labelEl = document.querySelector(`label[for="${el.id}"]`);
                  if (labelEl) labelText = labelEl.innerText.trim();
                }
                if (!labelText) {
                  const parentLabel = el.closest('label');
                  if (parentLabel) labelText = parentLabel.innerText.trim();
                }
                if (!labelText) {
                  labelText = el.getAttribute('aria-label') || el.name || "";
                }
                
                const isRequired = el.hasAttribute('required') || 
                                   el.getAttribute('aria-required') === 'true' || 
                                   labelText.includes('*');
                                   
                labelText = labelText.replace(/\\s+/g, ' ').replace(/\\s*\\*\\s*$/, '').trim();
                const options = Array.from(el.querySelectorAll('option'))
                                     .map(o => o.innerText.trim())
                                     .filter(t => t !== "" && !t.toLowerCase().includes("select"));
                                     
                fields.push({
                  id: el.id || "",
                  name: el.name || "",
                  label: labelText || el.name || "Select Field",
                  type: 'select',
                  required: !!isRequired,
                  options: options
                });
              });
              
              // 3. Radios
              const radioNames = new Set();
              const radios = modal.querySelectorAll('input[type="radio"]');
              radios.forEach(r => {
                if (r.name) radioNames.add(r.name);
              });
              
              radioNames.forEach(name => {
                const groupRadios = Array.from(modal.querySelectorAll(`input[type="radio"][name="${name}"]`));
                if (groupRadios.length === 0 || (groupRadios[0].offsetWidth === 0 && groupRadios[0].offsetHeight === 0)) return;
                
                const fieldset = groupRadios[0].closest('fieldset');
                let labelText = "";
                if (fieldset) {
                  const legend = fieldset.querySelector('legend');
                  if (legend) labelText = legend.innerText.trim();
                }
                if (!labelText) {
                  const container = groupRadios[0].closest('.form-group, .fb-form-element-container');
                  if (container) {
                    const labelEl = container.querySelector('.label, label, span');
                    if (labelEl) labelText = labelEl.innerText.trim();
                  }
                }
                
                const isRequired = groupRadios[0].hasAttribute('required') || 
                                   labelText.includes('*');
                                   
                labelText = labelText.replace(/\\s+/g, ' ').replace(/\\s*\\*\\s*$/, '').trim();
                const options = groupRadios.map(r => {
                  let rLabel = "";
                  if (r.id) {
                    const labelEl = document.querySelector(`label[for="${r.id}"]`);
                    if (labelEl) rLabel = labelEl.innerText.trim();
                  }
                  if (!rLabel) {
                    const parentLabel = r.closest('label');
                    if (parentLabel) rLabel = parentLabel.innerText.trim();
                  }
                  return rLabel || r.value || "";
                }).filter(t => t !== "");
                
                fields.push({
                  id: groupRadios[0].id || "",
                  name: name,
                  label: labelText || name || "Radio Group",
                  type: 'radio',
                  required: !!isRequired,
                  options: options
                });
              });
              
              // 4. Checkboxes
              const checkboxes = modal.querySelectorAll('input[type="checkbox"]');
              checkboxes.forEach(el => {
                if (el.offsetWidth === 0 && el.offsetHeight === 0) return;
                
                let labelText = "";
                if (el.id) {
                  const labelEl = document.querySelector(`label[for="${el.id}"]`);
                  if (labelEl) labelText = labelEl.innerText.trim();
                }
                if (!labelText) {
                  const parentLabel = el.closest('label');
                  if (parentLabel) labelText = parentLabel.innerText.trim();
                }
                
                const isRequired = el.hasAttribute('required') || labelText.includes('*');
                labelText = labelText.replace(/\\s+/g, ' ').replace(/\\s*\\*\\s*$/, '').trim();
                
                fields.push({
                  id: el.id || "",
                  name: el.name || "",
                  label: labelText || el.name || "Checkbox Field",
                  type: 'checkbox',
                  required: !!isRequired,
                  options: null
                });
              });
              
              // 5. File uploads
              const files = modal.querySelectorAll('input[type="file"]');
              files.forEach(el => {
                let labelText = "";
                if (el.id) {
                  const labelEl = document.querySelector(`label[for="${el.id}"]`);
                  if (labelEl) labelText = labelEl.innerText.trim();
                }
                if (!labelText) {
                  const parentLabel = el.closest('label');
                  if (parentLabel) labelText = parentLabel.innerText.trim();
                }
                if (!labelText) {
                  const container = el.closest('.form-group, .fb-form-element-container');
                  if (container) {
                    const labelEl = container.querySelector('.label, label, span');
                    if (labelEl) labelText = labelEl.innerText.trim();
                  }
                }
                
                const isRequired = el.hasAttribute('required') || labelText.includes('*');
                labelText = labelText.replace(/\\s+/g, ' ').replace(/\\s*\\*\\s*$/, '').trim();
                
                fields.push({
                  id: el.id || "",
                  name: el.name || "",
                  label: labelText || el.name || "Upload File",
                  type: 'upload',
                  required: !!isRequired,
                  options: null
                });
              });
              
              return fields;
            }
            """

            previous_answers = []
            max_pages = 15
            current_page_idx = 0
            
            # Fetch profile details for prompt
            candidate_profile = {}
            if app.get("candidate_profile"):
                try:
                    candidate_profile = json.loads(app["candidate_profile"])
                except Exception:
                    pass

            while current_page_idx < max_pages:
                current_page_idx += 1
                add_application_log(app_id, "INFO", "Form", f"Processing application page {current_page_idx}...")
                update_application_step(app_id, f"Processing page {current_page_idx}...")
                try:
                    page.screenshot(path=screenshot_path)
                    update_application_status(app_id, "Running", screenshot_path=screenshot_path)
                except Exception:
                    pass
                
                # Check for the submit/review button to see if we are on the final submit page
                submit_btn_selector = "button:has-text('Submit application'):visible, button:has-text('Submit'):visible, .btn-submit:visible"
                submit_btn = page.locator(submit_btn_selector).first
                
                is_review_page = False
                try:
                    if submit_btn.is_visible(timeout=1000):
                        is_review_page = True
                except Exception:
                    pass
                    
                if is_review_page:
                    add_application_log(app_id, "INFO", "Form", "Final submission/review page reached. Waiting for approval.")
                    update_application_step(app_id, "Review page reached. Awaiting candidate submission confirmation...")
                    page.screenshot(path=screenshot_path)
                    update_application_status(app_id, "Waiting for Final Review", screenshot_path=screenshot_path)
                    
                    # Wait for user to approve/complete the application
                    approved = False
                    start_approve_wait = time.time()
                    while time.time() - start_approve_wait < 60:
                        current_app = get_application(app_id)
                        if current_app and current_app["status"] in ["Completed", "Cancelled"]:
                            approved = current_app["status"] == "Completed"
                            break
                        time.sleep(1)
                        
                    if approved:
                        add_application_log(app_id, "INFO", "Worker", "Application submission approved. Clicking submit...")
                        update_application_step(app_id, "Submitting application...")
                        submit_btn.click()
                        page.wait_for_timeout(5000) # Wait for completion redirect/success screen
                        page.screenshot(path=screenshot_path)
                        update_application_status(app_id, "Completed", screenshot_path=screenshot_path)
                        add_application_log(app_id, "INFO", "Worker", "Application successfully submitted and completed!")
                    else:
                        add_application_log(app_id, "WARNING", "Worker", "Application cancelled or final review timed out.")
                        update_application_status(app_id, "Cancelled")
                    break

                # Extract fields
                fields = page.evaluate(js_scanner)
                add_application_log(app_id, "INFO", "Form", f"Scanned fields: {len(fields)} found on current page.")
                
                # If there are no fields on the current page, look for Next/Review button to advance
                if not fields:
                    next_btn_selector = "button:has-text('Next'):visible, button:has-text('Review'):visible, .btn-next:visible"
                    next_btn = page.locator(next_btn_selector).first
                    try:
                        if next_btn.is_visible(timeout=2000):
                            add_application_log(app_id, "INFO", "Form", "No fields found on this page. Clicking Next to advance...")
                            next_btn.click()
                            page.wait_for_timeout(2000)
                            continue
                        else:
                            add_application_log(app_id, "WARNING", "Form", "No fields and no Next button found. Finishing page scanning.")
                            break
                    except Exception as e:
                        add_application_log(app_id, "ERROR", "Form", f"Error advancing page: {e}")
                        break

                # Execute form filler agent via asyncio run
                session_service = InMemorySessionService()
                runner = Runner(
                    agent=form_filler_agent,
                    app_name="app",
                    session_service=session_service,
                    auto_create_session=True,
                )
                
                prompt_text = f"""
                Resume Details:
                {json.dumps(candidate_profile, indent=2)}
                
                Job URL:
                {job_url}
                
                Current application page information:
                {json.dumps(fields, indent=2)}
                
                Previous answers collected during this application:
                {json.dumps(previous_answers, indent=2)}
                """
                
                user_message = types.Content(parts=[types.Part.from_text(text=prompt_text)])
                
                async def run_agent():
                    events = runner.run_async(
                        user_id=f"worker_user_{app_id}",
                        session_id=f"worker_session_{app_id}",
                        new_message=user_message,
                    )
                    async for event in events:
                        pass
                    session = await session_service.get_session(
                        user_id=f"worker_user_{app_id}",
                        session_id=f"worker_session_{app_id}",
                        app_name="app"
                    )
                    return session.state.get("form_filling_result")
                    
                import threading
                def run_async_in_thread(coro):
                    res_list = []
                    err_list = []
                    def thread_target():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            val = loop.run_until_complete(coro)
                            res_list.append(val)
                            loop.close()
                        except Exception as e:
                            err_list.append(e)
                    t = threading.Thread(target=thread_target)
                    t.start()
                    t.join()
                    if err_list:
                        raise err_list[0]
                    return res_list[0] if res_list else None

                try:
                    result = run_async_in_thread(run_agent())
                except Exception as e:
                    add_application_log(app_id, "ERROR", "Form", f"Form filler agent call failed: {e}")
                    result = None
                    
                if not result:
                    add_application_log(app_id, "ERROR", "Form", "Form filler agent returned empty result. Pausing for human intervention.")
                    result = {"status": "NEED_USER_INPUT", "missing_fields": [f["label"] for f in fields if f["required"]]}
                
                actions = result.get("actions") or []
                missing_fields = result.get("missing_fields") or []
                status_res = result.get("status", "CONTINUE")
                
                # Perform actions for fields we can fill
                for act in actions:
                    matched_field = None
                    for f in fields:
                        if act["field"].lower().strip() in f["label"].lower().strip() or f["label"].lower().strip() in act["field"].lower().strip():
                            matched_field = f
                            break
                            
                    if matched_field:
                        selector = ""
                        if matched_field["id"]:
                            selector = f"#{matched_field['id']}"
                        elif matched_field["name"]:
                            el_type = matched_field["type"]
                            if el_type == 'select':
                                selector = f"select[name='{matched_field['name']}']:visible"
                            elif el_type == 'upload':
                                selector = f"input[name='{matched_field['name']}']"
                            else:
                                selector = f"input[name='{matched_field['name']}']:visible, textarea[name='{matched_field['name']}']:visible"
                                
                        if selector:
                            try:
                                locator = page.locator(selector).first
                                if act["type"] in ["text", "number"]:
                                    locator.fill(str(act["value"]))
                                    add_application_log(app_id, "INFO", "Form", f"Filled '{matched_field['label']}' with value: {act['value']}")
                                    previous_answers.append({"field": matched_field["label"], "answer": act["value"]})
                                elif act["type"] == "select":
                                    val = act["value"]
                                    try:
                                        locator.select_option(label=val)
                                    except Exception:
                                        try:
                                            locator.select_option(value=val)
                                        except Exception:
                                            options_loc = locator.locator("option").all()
                                            for opt in options_loc:
                                                opt_text = opt.inner_text().strip()
                                                if val.lower() in opt_text.lower() or opt_text.lower() in val.lower():
                                                    locator.select_option(value=opt.get_attribute("value"))
                                                    break
                                    add_application_log(app_id, "INFO", "Form", f"Selected '{matched_field['label']}' option: {val}")
                                    previous_answers.append({"field": matched_field["label"], "answer": val})
                                elif act["type"] == "radio":
                                    val = act["value"]
                                    radios_locator = page.locator(f"input[type='radio'][name='{matched_field['name']}']:visible")
                                    count = radios_locator.count()
                                    clicked = False
                                    for idx in range(count):
                                        r = radios_locator.nth(idx)
                                        r_id = r.get_attribute("id")
                                        r_label = ""
                                        if r_id:
                                            label_el = page.locator(f"label[for='{r_id}']").first
                                            if label_el.is_visible():
                                                r_label = label_el.inner_text().strip()
                                        if not r_label:
                                            r_label = r.locator("xpath=..").inner_text().strip()
                                        if val.lower() in r_label.lower() or r_label.lower() in val.lower() or val.lower() == r.get_attribute("value", "").lower():
                                            r.click()
                                            clicked = True
                                            break
                                    if clicked:
                                        add_application_log(app_id, "INFO", "Form", f"Clicked radio '{matched_field['label']}' option: {val}")
                                        previous_answers.append({"field": matched_field["label"], "answer": val})
                                elif act["type"] == "checkbox":
                                    val = act["value"]
                                    is_checked = locator.is_checked()
                                    should_check = str(val).lower() in ["true", "yes", "check", "1", "on"]
                                    if should_check != is_checked:
                                        locator.click()
                                    add_application_log(app_id, "INFO", "Form", f"Checked checkbox '{matched_field['label']}': {should_check}")
                                    previous_answers.append({"field": matched_field["label"], "answer": val})
                                elif act["type"] == "upload":
                                    resume_p = app.get("resume_path")
                                    if resume_p and os.path.exists(resume_p):
                                        locator.set_input_files(resume_p)
                                        add_application_log(app_id, "INFO", "Form", f"Uploaded resume file: {resume_p}")
                                        previous_answers.append({"field": matched_field["label"], "answer": f"Uploaded {os.path.basename(resume_p)}"})
                            except Exception as act_err:
                                add_application_log(app_id, "WARNING", "Form", f"Failed to perform action on '{matched_field['label']}': {act_err}")

                # Handle missing fields (HITL gating)
                if status_res == "NEED_USER_INPUT" or len(missing_fields) > 0:
                    for field_name in missing_fields:
                        f_struct = None
                        for f in fields:
                            if field_name.lower().strip() in f["label"].lower().strip() or f["label"].lower().strip() in field_name.lower().strip():
                                f_struct = f
                                break
                        
                        input_type = "text"
                        options = None
                        if f_struct:
                            input_type = f_struct["type"]
                            options = f_struct["options"]
                            
                        add_application_log(app_id, "INFO", "Form", f"Gating on missing field: {field_name}")
                        update_application_step(app_id, f"Awaiting user input on: {field_name}")
                        page.screenshot(path=screenshot_path)
                        prompt_id = add_hitl_prompt(app_id, f_struct["label"] if f_struct else field_name, input_type, options)
                        update_application_status(app_id, "Waiting for User Input", screenshot_path=screenshot_path)
                        
                        # Poll database until resolved
                        resolved = False
                        start_poll = time.time()
                        while time.time() - start_poll < 300:
                            prompt = get_hitl_prompt(prompt_id)
                            if prompt and prompt["status"] == "Resolved":
                                resolved = True
                                answer_val = prompt["answer_value"]
                                break
                            time.sleep(1)
                            
                        if not resolved:
                            add_application_log(app_id, "ERROR", "Form", f"Timeout waiting for user input on: {field_name}")
                            update_application_status(app_id, "Failed", error_message=f"Timeout waiting for answer on {field_name}")
                            sys.exit(1)
                            
                        add_application_log(app_id, "INFO", "Form", f"User provided answer for '{field_name}': {answer_val}")
                        update_application_status(app_id, "Running")
                        
                        # Fill the user-provided answer in the form
                        if f_struct:
                            if f_struct["id"]:
                                selector = f"#{f_struct['id']}"
                            else:
                                if f_struct["type"] == 'select':
                                    selector = f"select[name='{f_struct['name']}']:visible"
                                else:
                                    selector = f"input[name='{f_struct['name']}']:visible"
                                    
                            if f_struct["id"] or f_struct["name"]:
                                try:
                                    locator = page.locator(selector).first
                                    if input_type in ["text", "number"]:
                                        locator.fill(str(answer_val))
                                    elif input_type == "select":
                                        try:
                                            locator.select_option(label=answer_val)
                                        except Exception:
                                            try:
                                                locator.select_option(value=answer_val)
                                            except Exception:
                                                options_loc = locator.locator("option").all()
                                                for opt in options_loc:
                                                    opt_text = opt.inner_text().strip()
                                                    if answer_val.lower() in opt_text.lower() or opt_text.lower() in answer_val.lower():
                                                        locator.select_option(value=opt.get_attribute("value"))
                                                        break
                                    elif input_type == "radio":
                                        radios_locator = page.locator(f"input[type='radio'][name='{f_struct['name']}']:visible")
                                        count = radios_locator.count()
                                        for idx in range(count):
                                            r = radios_locator.nth(idx)
                                            r_id = r.get_attribute("id")
                                            r_label = ""
                                            if r_id:
                                                label_el = page.locator(f"label[for='{r_id}']").first
                                                if label_el.is_visible():
                                                    r_label = label_el.inner_text().strip()
                                            if not r_label:
                                                r_label = r.locator("xpath=..").inner_text().strip()
                                            if answer_val.lower() in r_label.lower() or r_label.lower() in answer_val.lower() or answer_val.lower() == r.get_attribute("value", "").lower():
                                                r.click()
                                                break
                                    previous_answers.append({"field": f_struct["label"], "answer": answer_val})
                                except Exception as fill_err:
                                    add_application_log(app_id, "WARNING", "Form", f"Failed to fill user answer: {fill_err}")

                # After filling, advance to next page
                next_btn_selector = "button:has-text('Next'):visible, button:has-text('Review'):visible, .btn-next:visible"
                next_btn = page.locator(next_btn_selector).first
                try:
                    if next_btn.is_visible(timeout=2000):
                        add_application_log(app_id, "INFO", "Form", "Advancing page...")
                        next_btn.click()
                        page.wait_for_timeout(2500) # Wait for page transit
                    else:
                        add_application_log(app_id, "WARNING", "Form", "Next/Review button not found. Moving on.")
                except Exception as e:
                    add_application_log(app_id, "ERROR", "Form", f"Failed to advance page: {e}")
                    break

            # Close browser context
            context.browser.close()
            
    except Exception as e:
        error_msg = f"Fatal exception occurred during background run: {str(e)}"
        print(error_msg)
        add_application_log(app_id, "ERROR", "Worker", error_msg)
        update_application_status(app_id, "Failed", error_message=error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
