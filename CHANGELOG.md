# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Configuration Refactoring

- **BREAKING CHANGE**: Consolidated admin environment variables from 9 to 2
  - Removed: `DEFAULT_ADMIN_USERNAME`, `ADMIN_USERNAME`, `ADMIN_DOMAIN`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_DOMAIN`
  - Kept only: `ADMIN_EMAIL`, `ADMIN_PASSWORD`
  - Admin username and domain now extracted dynamically from `ADMIN_EMAIL` by splitting on `@`
- **BREAKING CHANGE**: Removed SMTP authentication credentials
  - Removed: `SMTP_USER`, `SMTP_PASS` (from all services)
  - SMTP service now depends on Identity service for authentication
  - **SECURITY NOTE**: SMTP authentication temporarily accepts all credentials until Identity integration is implemented
- Updated `.env` and `.env.example` with comprehensive documentation (130+ lines, 7 organized sections)
- Added environment variable documentation for all 50+ variables across services

### Authentication Architecture

- Identity service updated to parse `ADMIN_EMAIL` and create admin account with extracted username@domain
- SMTP service prepared for Identity service authentication integration (TODO added)
- Added Identity as dependency for SMTP service in docker-compose.yml
- Single source of truth: Identity service handles all authentication

### Development Tools

- Refactored Makefile with DRY principles - all targets now accept optional service parameter
  - Usage: `make up` (all services) or `make up admin` (specific service)
  - Added `refresh` target for full rebuild with cache clearing
  - Added `clear-cache-view` target for restart + browser cache reminder
- All targets use pattern rule `%: @:` for flexible service targeting

### Documentation

- Created comprehensive README.md for all 6 services (~1,810 lines total):
  - admin/README.md (190 lines) - Admin web interface
  - client/README.md (115 lines) - Client web interface  
  - identity/README.md (285 lines) - Authentication service
  - smtp/README.md (430 lines) - SMTP server and REST API
  - imap/README.md (345 lines) - IMAP service
  - storage/README.md (445 lines) - Email storage service
- Each README includes: architecture, API docs, environment variables, development guide, examples

### Bug Fixes & Improvements

- Identity service: switched from email-based user key to username+domain; access tokens now include `jti` and can be revoked.
- Identity service: refresh tokens added (stored in DB) with rotation and a `/tokens/refresh` endpoint; `/tokens/revoke` supports revoking access (by jti) or refresh tokens.
- Admin UI: switched to HttpOnly cookie-based auth for browser flows; added `/api/login` and improved `/logout` to call identity revoke and clear cookies.
- Admin: better error forwarding from identity (non-2xx responses are now proxied instead of always returning 500).
- UI polish: top-pane avatar + logout, green Add buttons, persisted expanded domain lists in localStorage.
- Tests: added pytest-friendly integration test for login -> refresh -> logout -> old-refresh-fails.
- Updated test files to use new environment variable names (`ADMIN_EMAIL` instead of `DEFAULT_ADMIN_USERNAME`)
- Repo: removed accidentally committed virtualenv artifacts and added `.gitignore`.

