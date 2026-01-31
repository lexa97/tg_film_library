.PHONY: help install test lint format migrate up down clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Check code with ruff"
	@echo "  make format     - Format code with ruff"
	@echo "  make migrate    - Run database migrations"
	@echo "  make up         - Start services with Docker Compose"
	@echo "  make down       - Stop services with Docker Compose"
	@echo "  make clean      - Clean up temporary files"

install:
	pip install -r requirements.txt

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

up:
	docker-compose up -d

down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
