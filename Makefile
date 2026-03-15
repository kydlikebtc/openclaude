.PHONY: dev stop test migrate migrate-create lint typecheck build clean

# Development
dev:
	docker compose up --build

stop:
	docker compose down

# Database migrations
migrate:
	cd backend && alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	cd backend && alembic revision --autogenerate -m "$$name"

migrate-down:
	cd backend && alembic downgrade -1

# Testing
test:
	cd backend && pytest --cov=app --cov-report=term-missing

test-docker:
	docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Code quality
lint:
	cd backend && ruff check . && ruff format --check .

lint-fix:
	cd backend && ruff check --fix . && ruff format .

typecheck:
	cd backend && mypy app

# Build
build:
	docker compose build

# Cleanup
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Install local dev dependencies
install:
	cd backend && pip install -e ".[dev]"

# Setup .env from example
env:
	cp .env.example .env
	@echo "Created .env from .env.example — update SECRET_KEY before use!"
