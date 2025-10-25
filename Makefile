# Helper to accept service as argument: make <target> <service>
%:
	@:

.DEFAULT_GOAL := help

up:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		docker compose up -d; \
	else \
		docker compose up -d $$SERVICE; \
	fi

down:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		docker compose down; \
	else \
		docker compose stop $$SERVICE; \
		docker compose rm -f $$SERVICE; \
	fi

build:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		docker compose build --no-cache; \
	else \
		docker compose build --no-cache $$SERVICE; \
	fi

rebuild: 
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		$(MAKE) down && $(MAKE) build && $(MAKE) up; \
	else \
		$(MAKE) down $$SERVICE && $(MAKE) build $$SERVICE && $(MAKE) up $$SERVICE; \
	fi

install:
	@echo "Installing and initializing services..."
	@$(MAKE) down
	@$(MAKE) build
	docker compose up -d postgres mongo
	@echo "Waiting for databases to be ready..."
	sleep 10
	docker compose up -d
	@echo "Installation complete. Default admin user (admin@example.com/admin) is auto-created if needed."

# ==============================================================================
# UNIFIED DOCKER TESTING SYSTEM
# ==============================================================================

test:  ## Run all tests using unified Docker test runner
	@python3 unified_test_runner.py all

test-quick:  ## Run quick health check tests
	@python3 unified_test_runner.py quick

test-config:  ## Run configuration tests
	@python3 unified_test_runner.py config

test-unit:  ## Run unit tests
	@python3 unified_test_runner.py unit-core

test-unit-safe:  ## Run safe unit tests (no service dependencies)
	@python3 unified_test_runner.py unit-safe

test-unit-core:  ## Run core unit tests (config, i18n, models)
	@python3 unified_test_runner.py unit-core

test-integration:  ## Run integration tests
	@python3 -m pytest _test/integration/ -v --tb=short -m "not slow"

test-persistence:  ## Run persistence tests
	@python3 unified_test_runner.py persistence

test-admin:  ## Run admin service tests
	@python3 unified_test_runner.py admin

test-identity:  ## Run identity service tests
	@python3 unified_test_runner.py identity

test-flow:  ## Run email flow tests
	@python3 unified_test_runner.py flow

test-services:  ## Start DIGiDIG services only
	@python3 unified_test_runner.py services

test-coverage:  ## Run tests with code coverage analysis
	@python3 unified_test_runner.py coverage

test-help:  ## Show available test categories
	@echo "🧪 DIGiDIG Unified Docker Testing System"
	@echo ""
	@echo "Available test categories:"
	@echo "  make test          - Run all tests"
	@echo "  make test-quick    - Quick health check"
	@echo "  make test-config   - Configuration tests"
	@echo "  make test-unit     - Core unit tests (config, i18n, models)"
	@echo "  make test-unit-safe - Safe unit tests (no service deps)"
	@echo "  make test-integration - Integration tests"
	@echo "  make test-persistence - Persistence tests"
	@echo "  make test-admin    - Admin service tests"
	@echo "  make test-identity - Identity service tests"
	@echo "  make test-flow     - Email flow tests"
	@echo "  make test-services - Start services only"
	@echo "  make test-coverage - Run tests with coverage analysis"
	@echo ""
	@echo "Direct usage:"
	@echo "  python3 unified_test_runner.py <category>"
	@echo ""
	@echo "📖 See _doc/UNIFIED-DOCKER-TESTING.md for details"


clean-cache:
	@echo "Removing non-destructive caches and build artifacts (no docker changes)..."
	@echo "Removing Python caches and build artifacts..."
	-find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf
	-find . -type d -name '.pytest_cache' -print0 | xargs -0 -r rm -rf
	-find . -type d -name '.venv' -print0 | xargs -0 -r rm -rf
	-find . -type f -name '*.pyc' -print0 | xargs -0 -r rm -f
	# Remove node_modules for local frontend components if present
	-find . -type d -name 'node_modules' -maxdepth 4 -print0 | xargs -0 -r rm -rf
	# Remove build/dist artifacts
	-find . -type d -name 'build' -print0 | xargs -0 -r rm -rf
	-find . -type d -name 'dist' -print0 | xargs -0 -r rm -rf
	@echo "Non-destructive cache clean finished."

clean:
	@echo "Removing containers, volumes, images and build artifacts..."
	@echo "Step 1/3: Stopping and removing all containers, networks, and volumes..."
	docker compose down --volumes --remove-orphans
	@echo ""
	@echo "Step 2/3: Removing built images..."
	-docker image rm $$(docker compose config --services | xargs -I {} echo digidig-{}) 2>/dev/null || true
	@echo ""
	@echo "Step 3/3: Cleaning cache..."
	@$(MAKE) clean-cache
	@echo ""
	@echo "✅ Clean finished. Databases and caches removed."




clear-cache-view:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		echo "Clearing browser cache for all web services (admin, client)..."; \
		echo "Restarting admin service..."; \
		docker compose restart admin; \
		echo "Restarting client service..."; \
		docker compose restart client; \
		echo ""; \
		echo "✓ Services restarted. Now clear your browser cache:"; \
		echo "  • Hard refresh: Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac)"; \
		echo "  • Open DevTools (F12) → Network tab → Check 'Disable cache'"; \
		echo "  • Or use Private/Incognito window"; \
	else \
		echo "Clearing browser cache for service: $$SERVICE..."; \
		docker compose restart $$SERVICE; \
		echo ""; \
		echo "✓ Service '$$SERVICE' restarted. Now clear your browser cache:"; \
		echo "  • Hard refresh: Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac)"; \
		echo "  • Open DevTools (F12) → Network tab → Check 'Disable cache'"; \
		echo "  • Or use Private/Incognito window"; \
	fi

refresh:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		echo "❌ Error: service name is required"; \
		echo "Usage: make refresh <service_name>"; \
		echo "Example: make refresh admin"; \
		echo "         make refresh client"; \
		exit 1; \
	fi; \
	echo "🔄 Full refresh of service: $$SERVICE"; \
	echo ""; \
	echo "Step 1/4: Stopping and removing service..."; \
	docker compose stop $$SERVICE; \
	docker compose rm -f $$SERVICE; \
	echo ""; \
	echo "Step 2/4: Clearing cache..."; \
	$(MAKE) clean-cache; \
	echo ""; \
	echo "Step 3/4: Building service (no cache)..."; \
	docker compose build --no-cache $$SERVICE; \
	echo ""; \
	echo "Step 4/4: Starting service..."; \
	docker compose up -d $$SERVICE; \
	echo ""; \
	echo "✅ Service '$$SERVICE' fully refreshed!"; \
	echo ""; \
	echo "⚠️  Don't forget to clear your browser cache:"; \
	echo "  • Hard refresh: Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac)"; \
	echo "  • Open DevTools (F12) → Network tab → Check 'Disable cache'"; \
	echo "  • Or use Private/Incognito window"


