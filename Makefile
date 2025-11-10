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
	@for service in identity storage smtp imap mail admin sso client apidocs test-suite services; do \
		echo "Pushing $$service..."; \
		docker push $(GHCR_REGISTRY)/digidig-$$service:latest || echo "⚠️  Failed to push $$service"; \
	done
	@echo "✅ All images pushed to GHCR"

pull-all:
	@echo "Pulling all service images from GHCR..."
	@echo ""
	docker pull $(GHCR_BASE) || echo "⚠️  Failed to pull base image"
	@echo ""
	@for service in identity storage smtp imap mail admin sso client apidocs test-suite services; do \
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

install:
	@echo "========================================="
	@echo "  DIGiDIG Installation"
	@echo "========================================="
	@echo ""
	@echo "Setting up Python virtual environment..."
	@if [ ! -d .venv ]; then \
		python3 -m venv .venv; \
		.venv/bin/pip install --upgrade pip; \
		.venv/bin/pip install -r requirements.txt; \
		echo "✅ Virtual environment created and dependencies installed"; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi
	@echo ""
	@HOSTNAME_ARG=$(filter-out install,$(MAKECMDGOALS)); \
	if [ -n "$$HOSTNAME_ARG" ]; then \
		echo "Using hostname: $$HOSTNAME_ARG"; \
		export DIGIDIG_HOSTNAME=$$HOSTNAME_ARG; \
	else \
		echo "Enter hostname (e.g., digidig.cz) or press Enter for default from config:"; \
		read -r hostname_input; \
		if [ -n "$$hostname_input" ]; then \
			export DIGIDIG_HOSTNAME=$$hostname_input; \
			echo "Using hostname: $$hostname_input"; \
		else \
			echo "Using hostname from config.yaml"; \
		fi; \
	fi; \
	echo ""; \
	echo "Generating .env from config..."; \
	$(MAKE) gen-env; \
	echo ""; \
	echo "=== SSL Certificate Setup ==="; \
	if [ -f .env ]; then \
		HOSTNAME=$$(grep '^HOSTNAME=' .env | cut -d'=' -f2); \
	else \
		HOSTNAME="localhost"; \
	fi; \
	echo "Hostname: $$HOSTNAME"; \
	echo ""; \
	if [ -f "ssl/$$HOSTNAME.pem" ] && [ -f "ssl/$$HOSTNAME-key.pem" ]; then \
		echo "SSL certificates already exist for $$HOSTNAME"; \
		echo "Skip certificate generation? [Y/n]"; \
		read -r skip_cert; \
		case $$skip_cert in \
			[Nn]*) GENERATE_CERT=yes ;; \
			*) GENERATE_CERT=no ;; \
		esac; \
	else \
		echo "No SSL certificates found for $$HOSTNAME"; \
		echo "Generate SSL certificate? [Y/n]"; \
		read -r gen_cert; \
		case $$gen_cert in \
			[Nn]*) GENERATE_CERT=no ;; \
			*) GENERATE_CERT=yes ;; \
		esac; \
	fi; \
	if [ "$$GENERATE_CERT" = "yes" ]; then \
		if [ "$$HOSTNAME" = "localhost" ] || [ "$$HOSTNAME" = "127.0.0.1" ]; then \
			echo "Localhost detected - generating self-signed certificate..."; \
			mkdir -p ssl; \
			openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
				-keyout ssl/$$HOSTNAME-key.pem \
				-out ssl/$$HOSTNAME.pem \
				-subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$$HOSTNAME" 2>/dev/null; \
			echo "✅ Self-signed certificate generated: ssl/$$HOSTNAME.pem"; \
		else \
			echo ""; \
			echo "SSL Certificate Options:"; \
			echo "1. Let's Encrypt (automatic, free, trusted by browsers)"; \
			echo "2. Self-signed (quick, browser will show warning)"; \
			echo ""; \
			echo "Choose option [1/2] (default: 1):"; \
			read -r cert_choice; \
			case $$cert_choice in \
				2) \
					echo "Generating self-signed certificate..."; \
					mkdir -p ssl; \
					openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
						-keyout ssl/$$HOSTNAME-key.pem \
						-out ssl/$$HOSTNAME.pem \
						-subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$$HOSTNAME" 2>/dev/null; \
					echo "✅ Self-signed certificate generated"; \
					;; \
				*) \
					echo ""; \
					echo "Let's Encrypt Requirements:"; \
					echo "  ✓ Domain $$HOSTNAME must point to this server"; \
					echo "  ✓ Port 80 must be accessible from internet"; \
					echo "  ✓ Email required for notifications"; \
					echo ""; \
					echo "Enter your email for Let's Encrypt:"; \
					read -r le_email; \
					if [ -z "$$le_email" ]; then \
						echo "❌ Email required for Let's Encrypt"; \
						echo "Falling back to self-signed certificate..."; \
						mkdir -p ssl; \
						openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
							-keyout ssl/$$HOSTNAME-key.pem \
							-out ssl/$$HOSTNAME.pem \
							-subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$$HOSTNAME" 2>/dev/null; \
						echo "✅ Self-signed certificate generated"; \
					else \
						echo "Attempting Let's Encrypt with Docker certbot..."; \
						echo "⚠️  This will temporarily bind port 80 for ACME challenge"; \
						mkdir -p ssl letsencrypt; \
						docker run --rm \
							-p 80:80 \
							-v $$(pwd)/letsencrypt:/etc/letsencrypt \
							-v $$(pwd)/ssl:/ssl \
							certbot/certbot certonly --standalone \
							-d $$HOSTNAME \
							--email $$le_email \
							--agree-tos \
							--non-interactive && \
						{ \
							sudo cp letsencrypt/live/$$HOSTNAME/fullchain.pem ssl/$$HOSTNAME.pem; \
							sudo cp letsencrypt/live/$$HOSTNAME/privkey.pem ssl/$$HOSTNAME-key.pem; \
							sudo chown $(USER):$(USER) ssl/$$HOSTNAME.pem ssl/$$HOSTNAME-key.pem; \
							echo "✅ Let's Encrypt certificate installed"; \
							echo "💡 To renew: docker run --rm -p 80:80 -v $$(pwd)/letsencrypt:/etc/letsencrypt certbot/certbot renew"; \
						} || \
						{ \
							echo "❌ Let's Encrypt failed. Possible reasons:"; \
							echo "  - Domain $$HOSTNAME doesn't point to this server IP"; \
							echo "  - Port 80 is blocked by firewall"; \
							echo "  - Port 80 is already in use (stop nginx/apache first)"; \
							echo "  - DNS not propagated yet (wait 5-10 minutes)"; \
							echo ""; \
							echo "Falling back to self-signed certificate..."; \
							openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
								-keyout ssl/$$HOSTNAME-key.pem \
								-out ssl/$$HOSTNAME.pem \
								-subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$$HOSTNAME" 2>/dev/null; \
							echo "✅ Self-signed certificate generated"; \
						}; \
					fi; \
					;; \
			esac; \
		fi; \
	else \
		echo "⚠️  Skipping certificate generation - using existing or none"; \
	fi; \
	echo ""; \
	echo "=== Docker Images Setup ==="; \
	echo "Options:"; \
	echo "1. Pull pre-built images from GHCR (fast, recommended)"; \
	echo "2. Build locally (slower, for development)"; \
	echo ""; \
	echo "Choose option [1/2] (default: 1):"; \
	read -r build_choice; \
	case $$build_choice in \
		2) \
			echo "Building all services locally..."; \
			BUILD_METHOD="build"; \
			;; \
		*) \
			echo "Attempting to pull images from GHCR..."; \
			echo ""; \
			if ! $(MAKE) pull-all; then \
				echo ""; \
				echo "⚠️  Could not pull from GHCR, will build locally"; \
				BUILD_METHOD="build"; \
			else \
				echo ""; \
				echo "✅ Images pulled successfully"; \
				BUILD_METHOD="pulled"; \
			fi; \
			;; \
	esac; \
	echo ""; \
	if [ "$$BUILD_METHOD" = "build" ]; then \
		echo "This will rebuild all services. Continue? [Y/n]"; \
		read -r answer; \
		case $$answer in \
			[Nn]*) echo "Installation cancelled."; exit 1 ;; \
		esac; \
		echo ""; \
		echo "Stopping existing services..."; \
		$(MAKE) down; \
		echo ""; \
		echo "Building services..."; \
		$(MAKE) build; \
	else \
		echo "Stopping existing services..."; \
		$(MAKE) down; \
	fi; \
	echo ""; \
	echo "Starting databases..."; \
	docker compose up -d postgres mongo; \
	echo "Waiting for databases to be ready..."; \
	sleep 10; \
	echo ""; \
	echo "Starting all services..."; \
	docker compose up -d; \
	echo ""; \
	echo "========================================="
	@echo "✅ Installation complete!"
	@echo "Default admin: admin@example.com / admin"
	@echo "========================================="



clean-cache:
	@echo "Removing non-destructive caches and build artifacts (no docker changes)..."
	@echo "Removing Python caches and build artifacts..."
	-find . -type d -name '__pycache__' ! -path './letsencrypt/*' -print0 2>/dev/null | xargs -0 -r rm -rf
	-find . -type d -name '.pytest_cache' ! -path './letsencrypt/*' -print0 2>/dev/null | xargs -0 -r rm -rf
	-find . -type f -name '*.pyc' ! -path './letsencrypt/*' -print0 2>/dev/null | xargs -0 -r rm -f
	# Remove node_modules for local frontend components if present
	-find . -maxdepth 4 -type d -name 'node_modules' ! -path './letsencrypt/*' -print0 2>/dev/null | xargs -0 -r rm -rf
	# Remove build/dist artifacts
	-find . -type d -name 'build' ! -path './letsencrypt/*' -print0 2>/dev/null | xargs -0 -r rm -rf
	-find . -type d -name 'dist' ! -path './letsencrypt/*' -print0 2>/dev/null | xargs -0 -r rm -rf
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
	@SERVICES="$(filter-out $@,$(MAKECMDGOALS))"; \
	if [ -z "$$SERVICES" ]; then \
		echo "🔄 Full refresh of ALL services"; \
		SERVICES="identity storage smtp imap mail admin sso client apidocs test-suite services"; \
	fi; \
	for SERVICE in $$SERVICES; do \
		echo ""; \
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
	done; \
	echo "⚠️  Don't forget to clear your browser cache:"; \
	echo "  • Hard refresh: Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac)"; \
	echo "  • Open DevTools (F12) → Network tab → Check 'Disable cache'"; \
	echo "  • Or use Private/Incognito window"


