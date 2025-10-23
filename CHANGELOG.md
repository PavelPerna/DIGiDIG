# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Identity service: switched from email-based user key to username+domain; access tokens now include `jti` and can be revoked.
- Identity service: refresh tokens added (stored in DB) with rotation and a `/tokens/refresh` endpoint; `/tokens/revoke` supports revoking access (by jti) or refresh tokens.
- Admin UI: switched to HttpOnly cookie-based auth for browser flows; added `/api/login` and improved `/logout` to call identity revoke and clear cookies.
- Admin: better error forwarding from identity (non-2xx responses are now proxied instead of always returning 500).
- UI polish: top-pane avatar + logout, green Add buttons, persisted expanded domain lists in localStorage.
- Tests: added pytest-friendly integration test for login -> refresh -> logout -> old-refresh-fails.
- Repo: removed accidentally committed virtualenv artifacts and added `.gitignore`.
