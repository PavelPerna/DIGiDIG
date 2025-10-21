rebuild: down build up

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache
