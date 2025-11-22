.PHONY: help dev dev-build test lint format migrate build clean install shell logs db-shell redis-cli up down restart ps

# Default target - show help
help:
	@echo "FFmpeg Backend - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - Show logs (use SERVICE=<name> for specific service)"
	@echo "  make ps           - Show running services"
	@echo ""
	@echo "Code Quality:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make format       - Auto-format code with black and ruff"
	@echo "  make lint         - Run all linters (ruff, mypy)"
	@echo "  make test         - Run test suite"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-new  - Create new migration (use MSG='description')"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo "  make redis-cli    - Open Redis CLI"
	@echo ""
	@echo "Docker:"
	@echo "  make build        - Build Docker images"
	@echo "  make build-prod   - Build production Docker image"
	@echo "  make shell        - Open shell in API container"
	@echo "  make clean        - Stop containers and remove volumes"
	@echo "  make clean-all    - Remove containers, volumes, and images"
	@echo ""

# Development
dev:
	docker-compose up

dev-build:
	docker-compose up --build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

ps:
	docker-compose ps

logs:
ifdef SERVICE
	docker-compose logs -f $(SERVICE)
else
	docker-compose logs -f
endif

# Code Quality
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running ruff --fix..."
	ruff check --fix src/ tests/

lint:
	@echo "Running ruff..."
	ruff check src/ tests/
	@echo "Running mypy..."
	mypy src/

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Database
migrate:
	docker-compose exec api alembic upgrade head

migrate-new:
ifndef MSG
	$(error MSG is required. Usage: make migrate-new MSG="your migration description")
endif
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

db-shell:
	docker-compose exec db psql -U postgres -d ffmpeg_backend

redis-cli:
	docker-compose exec redis redis-cli

# Docker
build:
	docker-compose build

build-prod:
	docker build -t ffmpeg-backend:latest -f Dockerfile .

shell:
	docker-compose exec api /bin/bash

# Cleanup
clean:
	docker-compose down -v

clean-all:
	docker-compose down -v --rmi all
	docker system prune -f
