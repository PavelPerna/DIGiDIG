## DIGiDIG — Copilot / AI Agent Instructions

Purpose: Give an AI coding agent the minimal, actionable knowledge to be productive in this repository.

- Architectural snapshot
  - DIGiDIG is a small microservices system implemented in Python (FastAPI). Main services live at top-level folders: `identity/`, `storage/`, `smtp/`, `imap/`, `client/`, `admin/`, and `apidocs/`.
  - Services communicate over an internal Docker network. Service URLs are configured in `config/config.yaml` under `services.*` and are accessed programmatically via `common/config.py` (`get_service_url` / `get_config`). Example: `config.get('services.identity.url')`.
  - Identity service is the auth authority (JWT). Other services call Identity `/verify` to validate tokens (see `identity/src/identity.py`).

- Configuration & conventions (critical)
  - Centralized YAML config lives under `config/` (default file `config/config.yaml`). Environment overrides use `DIGIDIG_ENV` and `config/config.{env}.yaml`. The loader is in `common/config.py` and `config_models.py` documents expected shapes.
  - Prefer reading configuration via `common.get_config()` or convenience helpers `get_service_url()` and `get_db_config()` — do not reimplement ad-hoc env parsing.
  - JWT secret and other sensitive values are present in dev config files but must be overridden in production (see `README.md` and `config/config.prod.example.yaml`).

- Dev workflows & commands (what actually works)
  - Install / run locally: `make install` then `docker compose up` per root `README.md` (project uses docker-compose for local integration). Use `DIGIDIG_ENV=prod` and copy `config.prod.example.yaml` for prod runs.
  - Tests: integration and unit tests live in `tests/` and `tests/integration/`. Use `make test`, `make test-build`, or the `make` targets described in `README.md` to run tests inside the test container.
  - Quick service run (for a single service during dev): each service has `src/<service>.py` and can be launched with `uvicorn` locally (but CI/dev uses Docker Compose). See `client/src/client.py` and `identity/src/identity.py` for examples.

- Project-specific patterns and gotchas
  - Identity DB initialization is destructive in dev: `identity/src/identity.py`'s `init_db()` drops & recreates tables and seeds a default admin. Take care when running identity locally against a real DB — it can wipe tables.
  - Many services expose both a REST API and web UI (Jinja2 templates under `src/templates` and static under `src/static`). Changes to templates/static may require cache clear (see `make clear-cache-view` targets in READMEs).
  - Inter-service calls use internal URLs stored in the config (example: `client` uses `IDENTITY_URL` env var and calls `/verify` to validate tokens). Prefer `get_service_url('storage')` for programmatic access.
  - i18n: translations live under `locales/{en,cs}` and services use `common/i18n.py`. Client sets language via cookie (`/api/language` endpoint in `client/src/client.py`).

- Integration points / examples
  - Token verification: `POST /verify` in `identity/src/identity.py` — other services call this to validate JWTs.
  - Storing emails: SMTP → POST `/store` on `storage` (see `storage/README.md`). IMAP reads from `storage` via `/emails`.
  - API docs hub: `apidocs/` aggregates OpenAPI specs from services; add new service spec by updating `src/apidocs.py`'s `SERVICES` dict.

- How to change config safely (example)
  - Use `common.load_config(config_path, env)` or `get_config()`; prefer not to mutate `config` directly. Example to read identity URL: `from common.config import get_service_url; url = get_service_url('identity')`.

- Code-style and structure notes for PRs
  - Each service follows a FastAPI app in `src/`. Add new endpoints in that module and keep templates/static under `src/templates` and `src/static` respectively.
  - Use `pydantic` models for request/response shapes; config model definitions are in `config_models.py` — re-use them when validating config.
  - Logging is via the standard `logging` module and services log to stdout (Docker-friendly). Keep message formats consistent with existing services for easier debugging.

- Tests and CI guidance
  - Tests are executed in Docker for consistent environment. Use `make test` and consult `tests/` for integration flows (identity, smtp/imaps flows). Unit tests under `tests/unit` show config-loading expectations.

- Quick checklist for the AI agent when making changes
  1. Does the change require config keys? Update `config/config.yaml` example and `config_models.py` if the shape changes.
 2. Will it affect inter-service calls? Update `apidocs/` and service READMEs if new endpoints should be discoverable.
 3. Avoid destructive DB init in CI; respect `DIGIDIG_ENV` to skip destructive paths.
 4. If adding UI templates, put them under `src/templates` and add related static files under `src/static`.

Please review this draft and tell me which parts need more detail (for example: specific Makefile targets, Docker Compose overrides, or examples of common refactor patterns). 
