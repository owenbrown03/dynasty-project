DOCKER_COMPOSE := docker compose

.PHONY: help up up-deploy down down-deploy logs-api logs-worker restart-worker migrate test-backend test-frontend lint-frontend build-frontend test

help:
	@echo "Available targets:"
	@echo "  up              Start the local stack"
	@echo "  up-deploy       Start the deployment-oriented stack"
	@echo "  down            Stop the local stack"
	@echo "  down-deploy     Stop the deployment-oriented stack"
	@echo "  logs-api        Tail API logs"
	@echo "  logs-worker     Tail worker logs"
	@echo "  restart-worker  Restart the TaskIQ worker"
	@echo "  migrate         Run Alembic migrations in the API container"
	@echo "  test-backend    Run backend pytest suite in the API container"
	@echo "  test-frontend   Run frontend Vitest suite"
	@echo "  lint-frontend   Run frontend ESLint"
	@echo "  build-frontend  Build the frontend"
	@echo "  test            Run backend and frontend test suites"

up:
	$(DOCKER_COMPOSE) up --build

up-deploy:
	$(DOCKER_COMPOSE) -f docker-compose.deploy.yml up --build -d

down:
	$(DOCKER_COMPOSE) down

down-deploy:
	$(DOCKER_COMPOSE) -f docker-compose.deploy.yml down

logs-api:
	$(DOCKER_COMPOSE) logs -f api

logs-worker:
	$(DOCKER_COMPOSE) logs -f worker

restart-worker:
	$(DOCKER_COMPOSE) restart worker

migrate:
	$(DOCKER_COMPOSE) exec api alembic upgrade head

test-backend:
	$(DOCKER_COMPOSE) exec api python -m pytest

test-frontend:
	cd frontend && npm run test

lint-frontend:
	cd frontend && npm run lint

build-frontend:
	cd frontend && npm run build

test: test-backend test-frontend
