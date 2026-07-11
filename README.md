# Dynasty Base

Dynasty Base is a full-stack fantasy football analytics platform centered on Sleeper leagues. It ingests league data into a normalized Postgres schema, computes player and roster value across multiple valuation systems, and exposes those workflows through a FastAPI backend and a React frontend.

The project started as a spreadsheet workflow for dynasty roster management and evolved into an application with background sync jobs, normalized league state, draft-pick ownership tracking, valuation pipelines, and authenticated write flows back to Sleeper.

## What it does

- Syncs users, leagues, rosters, drafts, transactions, and traded picks from Sleeper
- Stores normalized application state in Postgres
- Calculates redraft and dynasty WAR from stored projections
- Tracks external value systems such as KeepTradeCut and FantasyCalc
- Resolves draft-pick ownership and pick value from normalized Sleeper data
- Supports research workflows for dashboards, waivers, trade signals, tiers, and commissioner/orphan views
- Supports authenticated write actions back to Sleeper for waivers and trades

## Architecture

### Backend

- FastAPI application in [backend/app/main.py](/Users/owen/Code/dynasty/project/backend/app/main.py)
- API routers under [backend/app/api/](/Users/owen/Code/dynasty/project/backend/app/api)
- Business logic under [backend/app/services/](/Users/owen/Code/dynasty/project/backend/app/services)
- Database access under [backend/app/crud/](/Users/owen/Code/dynasty/project/backend/app/crud)
- SQLModel models under [backend/app/models/db/](/Users/owen/Code/dynasty/project/backend/app/models/db)
- Background jobs with TaskIQ under [backend/app/tasks/](/Users/owen/Code/dynasty/project/backend/app/tasks)

Request flow:

1. FastAPI endpoint receives the request.
2. Dependencies build a request `Context` with DB session, session user, Sleeper client, and Redis access.
3. Routers delegate to services.
4. Services coordinate CRUD, analytics, and integrations.
5. CRUD persists normalized data and serves read models.

### Frontend

- React + TypeScript + Vite
- Route composition under [frontend/src/pages/](/Users/owen/Code/dynasty/project/frontend/src/pages)
- Shared data hooks under [frontend/src/hooks/](/Users/owen/Code/dynasty/project/frontend/src/hooks)
- API clients under [frontend/src/api/v1/](/Users/owen/Code/dynasty/project/frontend/src/api/v1)
- Shared app contexts under [frontend/src/context/](/Users/owen/Code/dynasty/project/frontend/src/context)

Data flow:

1. Components call feature hooks.
2. Hooks call typed endpoint wrappers.
3. Axios talks to FastAPI under `/api/v1`.
4. TanStack Query caches and invalidates server state.

### Infrastructure

- Postgres is the source of truth
- Redis is used for queueing, transient auth state, and cache layers
- Docker Compose orchestrates the local stack
- TaskIQ workers process asynchronous sync tasks

## Local development

From the repo root:

```sh
docker compose up --build
```

Common container workflows:

```sh
docker compose logs -f api
docker compose logs -f worker
docker compose restart worker
docker compose exec api alembic upgrade head
```

Frontend only:

```sh
cd frontend
npm run dev
```

## Testing and verification

Frontend:

```sh
cd frontend
npm run lint
npm run test
npm run build
```

Backend:

```sh
docker compose exec api python -m pytest /workspace/backend/tests -q
```

Schema changes:

```sh
docker compose exec api alembic revision --autogenerate -m "message"
docker compose exec api alembic upgrade head
```

If you change worker-imported code, restart the worker before treating the change as verified.

## Notable implementation details

- Anonymous sessions are first-class for low-friction browsing, but the long-term identity model is the registered site user linked to a Sleeper account.
- Postgres-backed reads are preferred over live Sleeper reads whenever normalized data already exists.
- Draft picks are modeled separately from players. Sleeper ownership comes from drafts and traded picks, while external pick values are stored in source-specific tables.
- Theme preference is persisted in session settings for anonymous users and user settings for authenticated users.
- Commissioner/orphan views, leagues, waivers, and trade tooling all read from the same normalized roster and valuation layers.

## Repository guide

- [AGENTS.md](/Users/owen/Code/dynasty/project/AGENTS.md) contains the project-specific working rules for AI agents and is also a useful high-signal implementation guide.
- [frontend/README.md](/Users/owen/Code/dynasty/project/frontend/README.md) contains frontend-specific commands and structure.
