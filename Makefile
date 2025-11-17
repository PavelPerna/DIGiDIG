# Helper to accept service as argument: make <target> <service>
%:
	@:

.DEFAULT_GOAL := help

# Generate .env file from config/config.yaml
# This ensures HOSTNAME and all service ports are read from the single source of truth
gen-env:
	@echo "Generating .env from config.yaml..."
	@.venv/bin/python scripts/generate_env_from_config.py > .env
	@echo "✅ .env file generated from config/config.yaml"

up:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	if [ -z "$$SERVICE" ]; then \
		docker compose up -d; \
		echo ""; \
		echo "🚀 DIGiDIG Services Started!"; \
		echo ""; \
		if [ -f .venv/bin/python ] && [ -f scripts/show_services.py ]; then \
			.venv/bin/python scripts/show_services.py 2>/dev/null || echo "⚠️  Could not load service URLs from config"; \
		else \
			echo "⚠️  Python environment or config not available"; \
		fi; \
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

GHCR_BASE := ghcr.io/pavelperna/digidig-base:latest
GHCR_REGISTRY := ghcr.io/pavelperna

build-base:
	@echo "Building base image with common dependencies..."
	@echo "Checking for existing base image..."
	@docker pull $(GHCR_BASE) 2>/dev/null || echo "No remote base image found, will build from scratch"
	docker build -t $(GHCR_BASE) -f docker/base/Dockerfile docker/base/
	@echo "✅ Base image built successfully"
	@echo ""
	@echo "To push to registry, run: make push-base"

push-base:
	@echo "Pushing base image to GHCR..."
	docker push $(GHCR_BASE)
	@echo "✅ Base image pushed to $(GHCR_BASE)"

push-all:
	@echo "Pushing all service images to GHCR..."
	@for service in identity storage smtp imap mail sso services; do \
		echo "Pushing $$service..."; \
		docker push $(GHCR_REGISTRY)/digidig-$$service:latest || echo "⚠️  Failed to push $$service"; \
	done
	@echo "✅ All images pushed to GHCR"

pull-all:
	@echo "Pulling all service images from GHCR..."
	@echo ""
	docker pull $(GHCR_BASE) || echo "⚠️  Failed to pull base image"
	@echo ""
	@for service in identity storage smtp imap mail sso services; do \
		echo "Pulling $$service..."; \
		docker pull $(GHCR_REGISTRY)/digidig-$$service:latest || echo "⚠️  Failed to pull $$service"; \
		echo ""; \
	done
	@echo "✅ All images pulled from GHCR"

pull-base:
	@echo "Pulling base image from GHCR..."
	@docker pull $(GHCR_BASE) || (echo "❌ Failed to pull base image, will build locally" && $(MAKE) build-base)

build:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	echo "Ensuring base image is available..."; \
	$(MAKE) pull-base 2>/dev/null || $(MAKE) build-base; \
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

refresh:
	@SERVICE=$(filter-out $@,$(MAKECMDGOALS)); \
	echo "Ensuring base image is available..."; \
	$(MAKE) pull-base 2>/dev/null || $(MAKE) build-base; \
	if [ -z "$$SERVICE" ]; then \
		docker compose build --no-cache && docker compose up -d; \
	else \
		docker compose build --no-cache $$SERVICE && docker compose up -d $$SERVICE; \
	fi

install:
	./scripts/installer.sh

# Test services management
test-services-up:
	@echo "Stopping any existing test services..."
	@docker compose down postgres mongo identity sso mail >/dev/null 2>&1 || true
	@echo "Starting all test services..."
	@docker compose up -d postgres mongo identity sso mail
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "✅ Test services started!"
	@echo ""
	@echo "Run tests with: make test-api"
	@echo "Stop services with: make test-services-down"

test-services-down:
	@echo "Stopping all test services..."
	@docker compose down postgres mongo identity sso mail
	@echo "✅ Test services stopped"

test-api:
	@echo "Running REST API tests..."
	.venv/bin/python -m pytest _test/unit/test_rest_api.py -v

test: test-services-up
	@echo "⏳ Waiting for services to be fully ready..."
	@sleep 20
	$(MAKE) test-api
	$(MAKE) test-services-down
