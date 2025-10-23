#!/usr/bin/env python3
"""
Minimal integration smoke test for auth flow.
Runs against local docker-compose services expected at:
 - identity: http://localhost:8001
 - admin:    http://localhost:8005

Checks:
 1) admin /api/login returns 200 and sets a refresh cookie or includes refresh_token in JSON
 2) identity /tokens/refresh (using refresh token) returns 200 and a new access_token + refresh_token
 3) admin /logout returns 200
 4) identity /tokens/refresh with the old refresh token fails (401 or 400)

This script is intentionally simple and prints diagnostics; exit code 0 on success.
"""

import requests
import sys
import time

ADMIN = 'http://localhost:8005'
IDENTITY = 'http://localhost:8001'

session = requests.Session()

# 1) login
print('1) POST /api/login')
try:
    r = session.post(ADMIN + '/api/login', json={'email': 'admin', 'password': 'admin'}, timeout=5)
except Exception as e:
    print('ERROR: /api/login request failed:', e)
    sys.exit(2)

print('/api/login status', r.status_code)
print('body:', r.text)

if r.status_code != 200:
    import os
    import requests
    import pytest


    # Integration smoke test for auth flow (pytest-friendly)
    # Expects local docker-compose services by default at:
    # - identity: http://localhost:8001
    # - admin:    http://localhost:8005
    #
    # Set ADMIN_URL / IDENTITY_URL environment variables to override.

    ADMIN = os.getenv("ADMIN_URL", "http://localhost:8005")
    IDENTITY = os.getenv("IDENTITY_URL", "http://localhost:8001")
    TIMEOUT = float(os.getenv("INTEGRATION_TIMEOUT", "5"))


    def _extract_refresh_token(session: requests.Session, response: requests.Response) -> str | None:
        try:
            j = response.json()
        except Exception:
            j = None
        if j and isinstance(j, dict) and "refresh_token" in j:
            return j["refresh_token"]
        # fall back to cookie set on the session
        ck = session.cookies.get("refresh_token")
        return ck


    @pytest.mark.integration
    def test_auth_flow_smoke():
        session = requests.Session()

        # 1) login
        r = session.post(f"{ADMIN}/api/login", json={"email": "admin", "password": "admin"}, timeout=TIMEOUT)
        assert r.status_code == 200, f"/api/login failed: {r.status_code} {r.text}"

        refresh = _extract_refresh_token(session, r)
        assert refresh, "No refresh token found in login response (json or cookie)"

        # 2) rotate refresh
        r2 = requests.post(f"{IDENTITY}/tokens/refresh", json={"refresh_token": refresh}, timeout=TIMEOUT)
        assert r2.status_code == 200, f"first /tokens/refresh failed: {r2.status_code} {r2.text}"
        body = r2.json()
        assert isinstance(body, dict) and "refresh_token" in body, "rotation response missing new refresh_token"

        old_refresh = refresh
        new_refresh = body["refresh_token"]

        # 3) admin logout
        r3 = session.post(f"{ADMIN}/logout", timeout=TIMEOUT)
        assert r3.status_code == 200, f"/logout failed: {r3.status_code} {r3.text}"

        # 4) try to refresh using the old refresh token; it should fail
        r4 = requests.post(f"{IDENTITY}/tokens/refresh", json={"refresh_token": old_refresh}, timeout=TIMEOUT)
        assert r4.status_code != 200, f"old refresh token unexpectedly worked after logout: {r4.status_code} {r4.text}"
