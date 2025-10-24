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

test:
	@echo "Building test container..."
	docker build -f tests/Dockerfile -t digidig-tests .
	@echo ""
	@echo "Running integration tests..."
	@NET=$$(docker network ls --format '{{.Name}}' | grep digidig | head -1); \
	if [ -z "$$NET" ]; then \
		NET=digidig_default; \
	fi; \
	echo "Using network: $$NET"; \
	docker run --rm --network $$NET \
		-e BASE_URL=http://identity:8001 \
		-e IDENTITY_URL=http://identity:8001 \
		-e SMTP_HOST=smtp \
		-e SMTP_PORT=2525 \
		-e SMTP_REST_URL=http://smtp:8000 \
		-e IMAP_HOST=imap \
		-e IMAP_PORT=143 \
		-e IMAP_URL=http://imap:8003 \
		-e STORAGE_URL=http://storage:8002 \
		digidig-tests
	@echo ""
	@echo "✅ Tests finished."

test-all: install
	@echo "Running all tests (with fresh install)..."
	@$(MAKE) test
	@echo "✅ All tests finished."

test-build:
	@echo "Building test container..."
	docker build -f tests/Dockerfile -t digidig-tests .
	@echo "✅ Test container built."


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


test-deps:
	@echo "Installing test dependencies..."
	@python3 -m pip install --user -r tests/requirements-test.txt
	@echo "Test dependencies installed."

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
