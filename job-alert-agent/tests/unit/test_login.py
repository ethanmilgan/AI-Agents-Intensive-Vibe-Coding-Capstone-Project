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
import pytest
from unittest.mock import patch
from app.application_agent.login_worker import get_session_path, check_linkedin_session_sync
from app.application_agent.tools import check_linkedin_session, login_to_linkedin

def test_get_session_path(monkeypatch, tmp_path):
    """Verify get_session_path resolves correctly with environment override."""
    monkeypatch.setenv("PLAYWRIGHT_PROFILE_DIR", str(tmp_path / ".playwright_profile"))
    session_path = get_session_path()
    assert session_path == str(tmp_path / ".playwright_profile" / "linkedin_cookies.json")

def test_check_linkedin_session_no_session_exists(monkeypatch, tmp_path):
    """Verify session check returns False when no session cookies file exists."""
    monkeypatch.setenv("PLAYWRIGHT_PROFILE_DIR", str(tmp_path / "empty_dir"))
    assert check_linkedin_session_sync() is False

@pytest.mark.asyncio
async def test_check_linkedin_session_tool_logged_in():
    """Verify check_linkedin_session tool wrapper returns correctly when session is valid."""
    with patch("app.application_agent.tools.check_linkedin_session_sync", return_value=True):
        res = await check_linkedin_session()
        assert res["status"] == "success"
        assert res["logged_in"] is True
        assert "logged in" in res["message"].lower()

@pytest.mark.asyncio
async def test_check_linkedin_session_tool_logged_out():
    """Verify check_linkedin_session tool wrapper returns correctly when session is invalid."""
    with patch("app.application_agent.tools.check_linkedin_session_sync", return_value=False):
        res = await check_linkedin_session()
        assert res["status"] == "success"
        assert res["logged_in"] is False
        assert "expired" in res["message"].lower() or "missing" in res["message"].lower()

@pytest.mark.asyncio
async def test_login_to_linkedin_tool_success():
    """Verify login_to_linkedin tool wrapper reports success when login succeeds."""
    with patch("app.application_agent.tools.login_to_linkedin_sync", return_value=True):
        res = await login_to_linkedin()
        assert res["status"] == "success"
        assert "successfully" in res["message"].lower()

@pytest.mark.asyncio
async def test_login_to_linkedin_tool_timeout():
    """Verify login_to_linkedin tool wrapper reports error on timeout."""
    with patch("app.application_agent.tools.login_to_linkedin_sync", return_value=False):
        res = await login_to_linkedin()
        assert res["status"] == "error"
        assert "timeout" in res["message"].lower() or "failed" in res["message"].lower()
