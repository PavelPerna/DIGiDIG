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
