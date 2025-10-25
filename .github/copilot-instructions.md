## DIGiDIG — Copilot / AI Agent Instructions

Purpose: Give an AI coding agent the minimal, actionable knowledge to be productive in this repository.

- Architectural snapshot
  - DIGiDIG is a small microservices system implemented in Python (FastAPI). Main services live in `services/`: `identity/`, `storage/`, `smtp/`, `imap/`, `client/`, `admin/`, `sso/`, and `apidocs/`.
  - Services communicate over an internal Docker network. Service URLs are configured in `config/config.yaml` under `services.*` and are accessed programmatically via `lib/common/config.py` (`get_service_url` / `get_config`). Example: `config.get('services.identity.url')`.
  - **SSO Service**: Centralized authentication service that handles login/logout for all services. Other services redirect unauthenticated users to SSO and verify sessions via cookies.
  - Identity service is the auth authority (JWT). SSO service authenticates with Identity and manages session cookies. Other services verify sessions with SSO service.

- Configuration & conventions (critical)
  - Centralized YAML config lives under `config/` (default file `config/config.yaml`). Environment overrides use `DIGIDIG_ENV` and `config/config.{env}.yaml`. The loader is in `lib/common/config.py` and `lib/config_models.py` documents expected shapes.
  - Prefer reading configuration via `lib.common.config.get_config()` or convenience helpers `get_service_url()` and `get_db_config()` — do not reimplement ad-hoc env parsing.
  - JWT secret and other sensitive values are present in dev config files but must be overridden in production (see root `README.md` and `config/config.prod.example.yaml`).

- Dev workflows & commands (what actually works)
  - Install / run locally: `make install` then `docker compose up` per root `README.md` (project uses docker-compose for local integration). Use `DIGIDIG_ENV=prod` and copy `config.prod.example.yaml` for prod runs.
  - Tests: **Unified Docker testing system** - tests live in `_test/` (unit and integration subdirectories). Use `make test` (all tests), `make test-quick` (health checks), `make test-unit` (core unit tests), `make test-integration`, or `python3 unified_test_runner.py <category>` directly. All tests run in Docker for consistent environment.
  - Service-specific tests: `make test-identity`, `make test-admin`, `make test-flow` (email flow), etc. See `make test-help` for full list.
  - Quick service run (for a single service during dev): each service has `src/<service>.py` and can be launched with `uvicorn` locally (but CI/dev uses Docker Compose). See `services/client/src/client.py` and `services/identity/src/identity.py` for examples.

- Project-specific patterns and gotchas
  - Identity DB initialization is destructive in dev: `services/identity/src/identity.py`'s `init_db()` drops & recreates tables and seeds a default admin. Take care when running identity locally against a real DB — it can wipe tables.
  - Many services expose both a REST API and web UI (Jinja2 templates under `src/templates` and static under `src/static`). Changes to templates/static may require cache clear (use `make clear-cache-view` or `make refresh <service>`).
  - Inter-service calls use internal URLs stored in the config (example: `client` uses `IDENTITY_URL` env var and calls `/verify` to validate tokens). Prefer `get_service_url('storage')` for programmatic access.
  - i18n: translations live under `locales/{en,cs}` and services use `lib/common/i18n.py`. Client sets language via cookie (`/api/language` endpoint in `services/client/src/client.py`).

- Integration points / examples
  - **SSO Authentication Flow**: Services redirect to `http://sso:8006/?redirect_to=<encoded_url>` for authentication. SSO authenticates with Identity service and sets secure cookies.
  - **Session Verification**: Services verify sessions by calling SSO `/verify` endpoint or checking `access_token` cookie directly.
  - Token verification: `POST /verify` in `services/identity/src/identity.py` — SSO service calls this to validate JWTs from login.
  - Storing emails: SMTP → POST `/store` on `storage` (see `services/storage/README.md`). IMAP reads from `storage` via `/emails`.
  - API docs hub: `services/apidocs/` aggregates OpenAPI specs from services; add new service spec by updating `src/apidocs.py`'s `SERVICES` dict.

- How to change config safely (example)
  - Use `lib.common.config.load_config(config_path, env)` or `get_config()`; prefer not to mutate `config` directly. Example to read identity URL: `from lib.common.config import get_service_url; url = get_service_url('identity')`.

- Code-style and structure notes for PRs
  - Each service follows a FastAPI app in `src/`. Add new endpoints in that module and keep templates/static under `src/templates` and `src/static` respectively.
  - Use `pydantic` models for request/response shapes; config model definitions are in `lib/config_models.py` — re-use them when validating config.
  - Logging is via the standard `logging` module and services log to stdout (Docker-friendly). Keep message formats consistent with existing services for easier debugging.

- Tests and CI guidance
  - Tests are executed in Docker for consistent environment. Use `make test` and consult `_test/` for integration flows (identity, smtp/imaps flows). Unit tests under `_test/unit` show config-loading expectations.

- Quick checklist for the AI agent when making changes
  1. Does the change require config keys? Update `config/config.yaml` example and `lib/config_models.py` if the shape changes.
  2. Will it affect inter-service calls? Update `services/apidocs/` and service READMEs if new endpoints should be discoverable.
  3. Avoid destructive DB init in CI; respect `DIGIDIG_ENV` to skip destructive paths.
  4. If adding UI templates, put them under `src/templates` and add related static files under `src/static`.
  5. Run relevant tests via `make test-<service>` or `make test-integration` to ensure no regressions.
  6. Follow existing logging and error-handling patterns for consistency.
  7. Follow SOLID, DRY, and KISS principles to maintain code quality and readability.
  8. For new services requiring authentication, use SSO service pattern: redirect to SSO for login, verify sessions via SSO `/verify` endpoint.