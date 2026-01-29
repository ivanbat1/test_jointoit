.PHONY: help build up down restart logs ps test clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start services"
	@echo "  make down       - Stop services"
	@echo "  make restart    - Restart services"
	@echo "  make logs       - View service logs"
	@echo "  make ps         - Show running services"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Remove containers and volumes"

# Build Docker images
build:
	docker compose build

# Start services
up:
	docker compose up

# Start demon services
up-d:
	docker compose up -d

# Stop services
down:
	docker compose down

# Restart services
restart:
	docker compose restart

# View logs
logs:
	docker compose logs -f

# Show running services
ps:
	docker compose ps

# Run tests
test:
	pytest tests/ -v

# Clean up
clean:
	docker compose down -v

