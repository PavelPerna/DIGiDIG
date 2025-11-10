# Auth & Logout Roadmap

Date: 2025-10-23

Purpose
-------
This file captures the recommended design and actionable TODOs for improving authentication, logout, and token revocation across the DIGiDIG services. We'll keep this file updated as work progresses and use it as the canonical checklist for the feature.

Short recommendation (best solution)
-----------------------------------
Use short-lived JWT access tokens + long-lived refresh tokens. Store tokens in Secure, HttpOnly cookies (avoid localStorage). Implement refresh-token rotation and server-side revocation so that /logout can reliably revoke a session. This combination balances security (mitigates XSS, limits replay window), UX (transparent cookie auth), and operational control (revoke sessions server-side).

High level tasks (priority order)
--------------------------------
1. Identity: implement refresh-token storage & revocation
   - Add DB table (or collection) to store refresh tokens (token id, user, issued_at, expires_at, revoked boolean, device metadata).
   - Add endpoint POST `/tokens/revoke` or `/logout` that accepts a refresh token (or jti) and marks it revoked.
   - Ensure the token issuance path returns a refresh token identifier (jti) or stores a reference you can revoke.
   - Make verify/refresh check the revocation store.

2. Admin: call identity revoke from `/logout`
   - Update `admin/src/admin.py` `/logout` to call identity `/tokens/revoke` when a refresh token/cookie is present.
   - Clear cookies and return normalized JSON.

3. Switch to cookie storage (HttpOnly, Secure)
   - On login, set access_token (short-lived) and refresh_token (long-lived) as Secure, HttpOnly cookies with SameSite=strict/lax as appropriate.
   - Change admin UI to rely on cookies for auth (use fetch with credentials: 'same-origin') and stop storing access tokens in localStorage.

4. Implement refresh token rotation
   - Rotate refresh tokens on use: when a refresh is exchanged, issue a new refresh token and mark the old one revoked.
   - Protect against reuse by detecting attempts to reuse a revoked token and treating them as compromise.

5. Add CSRF / request protection for browser flows
   - Because cookies are sent automatically, implement CSRF tokens for state-changing operations (or require `SameSite` plus anti-CSRF tokens where needed).

6. Security & Monitoring
   - Add audit logging for admin actions
   - Implement rate limiting for sensitive endpoints

7. UX polish & migration
   - Keep localStorage only for non-sensitive UI state (e.g., `openUsersDomain`).
   - Offer transitional support: keep `/api/login` for programmatic clients that expect JSON; optionally set cookies for browser flows only.

Minimal short-term (quick win)
------------------------------
If you need smaller, faster progress without a large refactor:
- Implement identity `/tokens/revoke` endpoint and call it from admin `/logout`. This will allow server-side invalidation even while continuing to pass tokens in forms/headers.
- Add admin `/logout` to clear cookies and client `doLogout()` to call `/logout` (already implemented).

Security trade-offs
-------------------
- Cookies (HttpOnly) protect against XSS but require CSRF mitigations for unsafe methods.
- Keeping tokens in localStorage is easy but leaves tokens vulnerable to XSS.
- Rotation + revocation adds DB/ops complexity but provides strong security posture.

Checklist (project TODO)
------------------------
- [x] Identity: Add refresh token model & store
- [x] Identity: Add POST /tokens/revoke and verify revocation on refresh/verify
- [x] Admin: Call identity revoke from `/logout` and delete cookies
- [ ] Frontend: Stop storing tokens in localStorage; rely on HttpOnly cookies
- [x] Auth: Implement refresh-token rotation and short-living access tokens
- [ ] Security: Add CSRF protections where needed
- [ ] Security: Add audit logging for admin actions
- [ ] Security: Implement rate limiting for sensitive endpoints

How to update
-------------
- Edit this file directly in the repository when you complete a task, or create a PR referencing this file.
- Use it as the single source of truth for progress on logout/token revocation work.

Owner / Contacts
----------------
- Primary: Pavel (repo owner)
- I can implement the identity revoke endpoint and wire admin `/logout` if you want me to — tell me to proceed and I will start with the identity service changes.

Commands (useful)
-----------------
- Rebuild admin after server changes:

```bash
docker compose build admin
docker compose up -d admin
```

- Check service locally (example):

```bash
curl -I http://localhost:8003/health
```

Notes
-----
- This file was created automatically on 2025-10-23 to capture the recommended design and next steps for authentication and logout improvements.
