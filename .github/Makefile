# .github/Makefile - Automation targets for DIGiDIG development tasks
# This Makefile provides targets for all development and testing commands needed.
# It delegates to the main Makefile in the repo root.

REPO_ROOT := $(shell cd .. && pwd)
MAKE := make -C $(REPO_ROOT)

# Service management
.PHONY: down
down:
	$(MAKE) down

.PHONY: sso-up
sso-up:
	$(MAKE) sso-up

.PHONY: sso-logs
sso-logs:
	$(MAKE) sso-logs

.PHONY: smoke-test
smoke-test:
	$(MAKE) smoke-test

# Development tasks
.PHONY: patch-session
patch-session:
	@echo "Patching /api/session endpoints to return test user for debugging..."
	# Add logic here or call scripts

.PHONY: add-playwright-test
add-playwright-test:
	@echo "Adding Playwright test for avatar visibility..."
	# Add logic here or call scripts

.PHONY: run-smoke-container
run-smoke-container:
	@echo "Running smoke test in container..."
	# Add logic here or call scripts

.PHONY: analyze-logs
analyze-logs:
	@echo "Analyzing logs and iterating fixes..."
	# Add logic here or call scripts

.PHONY: retry-login
retry-login:
	@echo "Instructing user to retry login and capture logs..."
	# Add logic here or call scripts

# Utility
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  down              - Stop all services"
	@echo "  sso-up            - Start SSO service"
	@echo "  sso-logs          - Tail SSO logs"
	@echo "  smoke-test        - Run SSO login smoke test"
	@echo "  patch-session     - Patch /api/session for test user"
	@echo "  add-playwright-test - Add Playwright avatar test"
	@echo "  run-smoke-container - Run container smoke test"
	@echo "  analyze-logs      - Analyze logs and iterate"
	@echo "  retry-login       - User retry login instruction"