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

def validate_domain(domain: str) -> dict:
    """Validate if the target domain is approved for automation navigation.
    
    Args:
        domain: The domain name to check.
        
    Returns:
        A dictionary containing approval status and validation message.
    """
    allowed = {"linkedin.com", "www.linkedin.com"}
    cleaned = domain.lower().strip()
    if cleaned in allowed:
        return {"status": "success", "allowed": True, "message": f"Domain '{domain}' is approved."}
    return {"status": "error", "allowed": False, "message": f"Domain '{domain}' is NOT approved for navigation."}

def validate_inputs(keywords: list[str], location: str, has_resume: bool, is_authenticated: bool, requested_applications: int) -> dict:
    """Validate automation input parameters before execution starts.
    
    Args:
        keywords: Target job keywords list.
        location: Preferred job location.
        has_resume: Boolean representing if a resume has been uploaded.
        is_authenticated: Boolean representing if user session is active.
        requested_applications: Count of requested applications to queue.
        
    Returns:
        A dictionary containing validation outcome.
    """
    if not keywords or not any(k.strip() for k in keywords):
        return {"status": "error", "message": "Input validation failed: target job keywords must be specified."}
    if not location or not location.strip():
        return {"status": "error", "message": "Input validation failed: location must be specified."}
    if not has_resume:
        return {"status": "error", "message": "Input validation failed: candidate resume must be uploaded."}
    if not is_authenticated:
        return {"status": "error", "message": "Input validation failed: LinkedIn user must be authenticated."}
    if requested_applications < 1 or requested_applications > 20:
        return {"status": "error", "message": f"Input validation failed: requested applications must be between 1 and 20 (got {requested_applications})."}
    return {"status": "success", "message": "All inputs successfully validated."}

def validate_action(action: str) -> dict:
    """Validate if the requested automation action is approved.
    
    Args:
        action: The requested action name.
        
    Returns:
        A dictionary containing action approval status.
    """
    allowed_actions = {
        "Search Jobs", "Open Job", "Scroll", "Click Easy Apply",
        "Upload Resume", "Upload Cover Letter", "Fill Input Field",
        "Select Dropdown", "Select Radio Button", "Check Checkbox",
        "Click Next", "Click Review", "Click Submit", "Close Dialog",
        "Return To Job Search"
    }
    if action in allowed_actions:
        return {"status": "success", "allowed": True, "message": f"Action '{action}' is approved."}
    return {"status": "error", "allowed": False, "message": f"Action '{action}' is prohibited."}
