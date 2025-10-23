up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

rebuild: down build up

install: down build
	@echo "Installing and initializing services..."
	docker compose up -d postgres mongo
	@echo "Waiting for databases to be ready..."
	sleep 10
	docker compose up -d
	@echo "Installation complete. Default admin user (admin@example.com/admin) is auto-created if needed."

test: install
	@echo "Running identity tests inside Docker..."
	# Build the identity tests image
	docker build -t digidig-identity-tests -f identity/tests/Dockerfile identity
	# Run the tests container on the same network so it can reach postgres and identity
	@NET=digidig_strategos-net; \
	if docker network inspect $$NET >/dev/null 2>&1; then \
	  docker run --rm --network $$NET -e SKIP_COMPOSE=1 -e BASE_URL=http://identity:8001 digidig-identity-tests; \
	else \
	  echo "Network $$NET not found, running tests without custom network"; \
	  docker run --rm -e SKIP_COMPOSE=1 -e BASE_URL=http://identity:8001 digidig-identity-tests; \
	fi
	@echo "Tests finished."


clean: down
	@echo "Removing containers, volumes, images and build artifacts..."
	# Stop and remove containers, networks, and anonymous volumes
	docker compose down --volumes --remove-orphans

	# Optionally remove built images for services in this compose (local only)
	-docker image rm $$(docker compose ls -q) 2>/dev/null || true

	# Remove common Python cache/build artifacts
	@echo "Removing Python caches and build artifacts..."
	-find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf
	-find . -type d -name '.pytest_cache' -print0 | xargs -0 -r rm -rf
	-find . -type d -name '.venv' -print0 | xargs -0 -r rm -rf
	-find . -type f -name '*.pyc' -print0 | xargs -0 -r rm -f

	# Remove node_modules if present (frontend clients)
	-find . -type d -name 'node_modules' -maxdepth 4 -print0 | xargs -0 -r rm -rf

	# Remove any build artifacts / dist folders
	-find . -type d -name 'build' -print0 | xargs -0 -r rm -rf
	-find . -type d -name 'dist' -print0 | xargs -0 -r rm -rf

	@echo "Clean finished. Databases and caches removed."


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


test-deps:
	@echo "Creating local virtualenv at .venv and installing test dependencies for identity..."
	@python3 -m venv .venv || true
	.venv/bin/python -m pip install --upgrade pip setuptools wheel || true
	.venv/bin/python -m pip install -r identity/tests/requirements.txt || true
	@echo "Test deps installed into .venv"
