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
    print('FAIL: /api/login did not return 200')
    sys.exit(3)

# collect refresh token from JSON or cookie
json_body = None
try:
    json_body = r.json()
except Exception:
    pass

refresh_token = None
if json_body and 'refresh_token' in json_body:
    refresh_token = json_body['refresh_token']
    print('Found refresh_token in JSON')
else:
    # check cookies set on the session
    ck = session.cookies.get('refresh_token')
    if ck:
        refresh_token = ck
        print('Found refresh_token in cookie')

if not refresh_token:
    print('WARN: No refresh token found in response JSON or cookies. Proceeding will likely fail.')

# 2) try rotate refresh
print('\n2) POST /tokens/refresh (first attempt)')
try:
    r2 = requests.post(IDENTITY + '/tokens/refresh', json={'refresh_token': refresh_token}, timeout=5)
    print('/tokens/refresh status', r2.status_code)
    print('body:', r2.text)
except Exception as e:
    print('ERROR: /tokens/refresh request failed:', e)
    sys.exit(4)

if r2.status_code != 200:
    print('FAIL: first refresh failed (expected 200)')
    sys.exit(5)

new = None
try:
    new = r2.json()
except Exception:
    pass
if not new or 'refresh_token' not in new:
    print('FAIL: rotation response missing new refresh_token')
    sys.exit(6)

old_refresh = refresh_token
refresh_token = new['refresh_token']
print('Rotation succeeded; got new refresh token')

# 3) admin logout
print('\n3) POST /logout (admin)')
try:
    r3 = session.post(ADMIN + '/logout', timeout=5)
    print('/logout status', r3.status_code)
    print('body:', r3.text)
except Exception as e:
    print('ERROR: /logout failed:', e)
    sys.exit(7)

if r3.status_code != 200:
    print('FAIL: /logout returned non-200 status')
    sys.exit(8)

# 4) try to refresh using the *old* refresh token; it should fail
print('\n4) POST /tokens/refresh (using old refresh token, should fail)')
try:
    r4 = requests.post(IDENTITY + '/tokens/refresh', json={'refresh_token': old_refresh}, timeout=5)
    print('/tokens/refresh status', r4.status_code)
    print('body:', r4.text)
except Exception as e:
    print('ERROR: second /tokens/refresh failed with exception:', e)
    sys.exit(9)

if r4.status_code == 200:
    print('FAIL: old refresh token unexpectedly rotated after logout')
    sys.exit(10)

print('\nOK: auth flow smoke test completed (logout revoked old refresh token)')
sys.exit(0)
