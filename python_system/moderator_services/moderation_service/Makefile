.PHONY: help install dev test docker-build docker-up docker-down docker-logs clean

help:
	@echo "AdSphere Moderation Service - Available Commands"
	@echo ""
	@echo "  install       Install Python dependencies"
	@echo "  dev           Run service in development mode"
	@echo "  test          Run tests"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start services with Docker Compose"
	@echo "  docker-down   Stop Docker services"
	@echo "  docker-logs   View Docker logs"
	@echo "  clean         Clean cache and temporary files"
	@echo ""

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

test:
	pytest tests/ -v

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Services started! Access:"
	@echo "  - Moderation API: http://localhost:8002"
	@echo "  - API Docs: http://localhost:8002/docs"
	@echo "  - Redis Commander: http://localhost:8081"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f moderation

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf cache/*
	rm -rf logs/*.log

