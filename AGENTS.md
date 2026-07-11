# AGENTS.md

This file is for AI agents working in this repository. It is specific to this codebase and should be treated as the working guide for making changes safely.

## Project purpose

Dynasty is a fantasy football application centered on Sleeper leagues.

- Postgres is the application source of truth.
- Sleeper is an external system used for:
  - synchronization into the normalized database
  - authenticated write operations back to Sleeper
- Analytics should run from normalized database data whenever possible.

The primary identity model is the site user. Anonymous sessions exist to reduce friction before account creation, but active users are expected to end up with a registered site account linked to a Sleeper account. Anonymous browsing should remain possible where the product currently allows it.

## Architecture overview

### Backend

Stack:

- FastAPI
- SQLModel + SQLAlchemy async
- Postgres
- Redis
- TaskIQ workers

Main backend entry points:

- `backend/start.sh` — runs migrations and starts the API server
- `backend/app/main.py` — FastAPI app, lifespan setup, CORS, exception handlers
- `backend/app/api/v1/api.py` — API router registration
- `backend/app/core/worker.py` — TaskIQ worker startup/shutdown hooks
- `backend/app/core/broker.py` — TaskIQ broker and task auto-imports

Backend request flow:

1. FastAPI endpoint receives request.
2. `app/api/deps.py` builds a `Context` containing DB session, session/site user, linked Sleeper connection, integration clients, and Redis client.
3. Router delegates to service or CRUD.
4. Services contain business logic and orchestration.
5. CRUD is responsible for database reads/writes.
6. Integrations talk to external APIs.

Keep this layering intact.

### Frontend

Stack:

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Axios

Main frontend entry points:

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/Routes.tsx`
- `frontend/src/components/providers/AppProviders.tsx`
- `frontend/src/api/v1/client.ts`

Frontend data flow:

1. Components call hooks in `frontend/src/hooks/...`.
2. Hooks call API wrappers in `frontend/src/api/v1/endpoints/...`.
3. Axios talks to the FastAPI backend at `http://localhost:8000/api/v1`.
4. TanStack Query handles loading/caching/invalidation.

Follow the existing component and hook patterns rather than inventing a new structure.

### Database

Primary DB models live under:

- `backend/app/models/db/auth.py`
- `backend/app/models/db/sleeper/connection.py`
- `backend/app/models/db/sleeper/api.py`
- `backend/app/models/db/sleeper/personal.py`
- `backend/app/models/db/ktc/`
- `backend/app/models/db/fc/`
- `backend/app/models/db/underdog/`

Use SQLModel models consistently. Do not introduce a parallel ORM pattern.

### Background workers

Workers are used for asynchronous synchronization jobs.

Current task modules:

- `backend/app/tasks/user.py`
- `backend/app/tasks/trade.py`

If you change worker code, restart the TaskIQ worker before considering the change verified.

### Redis responsibilities

Redis is currently used for:

- TaskIQ queue transport
- short-lived Sleeper auth pending state
- WAR caching and related analytics cache usage

Do not move durable application state out of Postgres into Redis.

## Directory responsibilities

### Backend

- `backend/app/api/`
  - FastAPI dependency wiring and API routers
  - Routers should stay thin

- `backend/app/services/`
  - Business logic
  - orchestration across CRUD, integrations, analytics, and Redis
  - Prefer extending existing services over creating new ones

- `backend/app/crud/`
  - Database access only
  - queries, upserts, persistence helpers
  - Keep DB access in CRUD

- `backend/app/integrations/`
  - External API clients and transport layers
  - Sleeper, KTC, FantasyCalc, Underdog

- `backend/app/models/db/`
  - SQLModel database models

- `backend/app/schemas/`
  - Request/response schemas and typed payloads

- `backend/app/analytics/`
  - WAR and dynasty/redraft valuation logic
  - Expensive or domain-heavy calculations belong here or in services that orchestrate it

- `backend/app/tasks/`
  - Background job entry points only
  - Keep task bodies small; they should delegate to CRUD/services

- `backend/alembic/`
  - Migrations

### Frontend

- `frontend/src/api/v1/`
  - Axios client and endpoint wrappers

- `frontend/src/hooks/`
  - Query and mutation hooks
  - Existing place for request lifecycle and invalidation logic

- `frontend/src/context/`
  - App-wide UI/session/bootstrap context

- `frontend/src/components/`
  - Shared UI/layout/auth/Sleeper components

- `frontend/src/pages/`
  - Route-level and feature-level page composition
  - Current features include dashboard, leagues, trades, waivers, and orphans

- `frontend/src/types/`
  - Shared frontend types

- `frontend/src/utils/`
  - Frontend utilities such as formatting and notifications

## Project-specific coding rules

### Backend layering rules

- Keep routers thin.
- Keep business logic in services.
- Keep DB access in CRUD.
- Prefer extending existing services over creating new ones.
- Preserve async patterns end-to-end unless a sync boundary already exists.
- Avoid live Sleeper API calls in read endpoints when the data already exists in Postgres.
- Treat Postgres as the source of truth for reads and analytics.
- Use Redis for cache/queue/transient state, not durable product state.

### Database rules

- Use SQLModel models consistently.
- Reuse the existing async session pattern from `app/core/database.py`.
- If you add or change persisted fields, update the SQLModel model first and handle the migration path explicitly.
- Maintain the normalized Sleeper mirror shape rather than stuffing raw external payloads directly into new endpoints.

### Sleeper integration rules

- Read endpoints should prefer normalized DB data.
- Sleeper network calls belong in sync flows, auth flows, or explicit write flows.
- If a feature needs current Sleeper write access, route it through the existing authenticated connection model.
- Preserve the distinction between read-capable linked state and write-capable token-authenticated state on `SleeperConnection`.

### Worker rules

- TaskIQ tasks should remain small wrappers around existing sync logic.
- After changing worker code, restart the TaskIQ worker.
- If a change affects task registration, broker wiring, or worker lifecycle, verify the worker starts cleanly.

### Frontend rules

- Follow the existing frontend component patterns.
- Prefer feature hooks under `frontend/src/hooks/sleeper/` or related existing hook modules instead of embedding API logic directly in components.
- Use TanStack Query for server state, loading state, and invalidation.
- Keep page components focused on composition; keep request logic in hooks.
- Reuse existing contexts:
  - `BootstrapContext`
  - `AuthContext`
  - `SleeperAuthContext`

### Dependency rules

- Don’t add dependencies without approval.
- First look for an existing utility, service, or package already in the repo before proposing a new dependency.

## Important existing flows

### Bootstrap/session flow

Relevant files:

- `backend/app/api/v1/endpoints/bootstrap.py`
- `backend/app/services/bootstrap.py`
- `frontend/src/hooks/useBootstrap.ts`
- `frontend/src/context/BootstrapContext.tsx`

This is the main source of truth for frontend knowledge of:

- whether the site user is authenticated
- whether a Sleeper account is linked
- whether the app can read
- whether the app can write

If you change auth/link state behavior, make sure bootstrap semantics stay coherent.

Theme preference follows the same general persistence model as pre-account session state:

- anonymous users persist theme through `UserSession.settings`
- signed-in users persist theme through `SiteUser.settings`
- session theme is reconciled into the user on registration/login
- logout should preserve the current theme by creating a fresh anonymous session and copying the theme into it

### Sleeper connection flow

Relevant files:

- `backend/app/api/v1/endpoints/sleeper/connection.py`
- `backend/app/services/sleeper/connection.py`
- `backend/app/crud/sleeper/connection.py`
- `frontend/src/hooks/sleeper/useConnection.ts`
- `frontend/src/pages/dashboard/UsernameInput.tsx`

This flow currently:

- stores or updates a local `SleeperConnection`
- queues sync jobs
- supports later reconciliation from anonymous session ownership to site-user ownership

Do not break the session-to-user reconciliation model when editing connection logic.

### Sync flow

Relevant files:

- `backend/app/tasks/user.py`
- `backend/app/tasks/trade.py`
- `backend/app/crud/sleeper/user.py`
- `backend/app/crud/sleeper/leaguemate.py`
- `backend/app/crud/sleeper/league.py`

This is the core ingestion path from Sleeper into Postgres.

If a new feature needs data that can be normalized and stored, prefer extending this flow rather than adding repeated live fetches in read endpoints.

### Dashboard / analytics flow

Relevant files:

- `backend/app/services/dashboard/service.py`
- `backend/app/services/leagues/details.py`
- `backend/app/crud/value.py`
- `backend/app/analytics/war/redraft/`
- `backend/app/analytics/war/dynasty/`

The app’s value is not just raw league display. Much of the product depends on enriched player values and WAR calculations. Changes here should preserve league-context-specific calculations.

### Waiver and trade write flows

Relevant files:

- `backend/app/api/v1/endpoints/sleeper/auth.py`
- `backend/app/services/sleeper/auth.py`
- `backend/app/services/sleeper/pending.py`
- `backend/app/integrations/sleeper/write.py`
- `backend/app/api/v1/endpoints/sleeper/trades.py`
- `backend/app/api/v1/endpoints/sleeper/waivers.py`

These depend on a stored authenticated Sleeper token. Preserve the distinction between:

- linking by username for read/sync context
- linking with verified token for write capability

## Common development commands

Run from repo root unless noted.

### Docker workflow

Start the main stack:

```sh
docker compose up --build
```

Start with multiple workers:

```sh
docker compose -f docker-compose.yml -f docker-compose.workers.yml up --build
```

Start with debug worker overlay:

```sh
docker compose -f docker-compose.yml -f docker-compose.debug.yml up --build
```

Stop the stack:

```sh
docker compose down
```

Restart only the worker after worker code changes:

```sh
docker compose restart worker
```

Tail API logs:

```sh
docker compose logs -f api
```

Tail worker logs:

```sh
docker compose logs -f worker
```

### Backend workflow

The API container runs:

```sh
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

If running inside the backend container manually:

```sh
cd /workspace/backend
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Start a TaskIQ worker manually inside the backend container:

```sh
cd /workspace/backend
taskiq worker --no-configure-logging app.core.worker:broker
```

### Frontend workflow

Inside `frontend/`:

```sh
npm install
npm run dev
```

Other existing frontend scripts:

```sh
npm run build
npm run lint
npm run preview
```

## Testing and verification workflow

This repository does not currently present a mature unified automated test workflow. Verify changes in proportion to what you touched.

### Frontend verification

Use the existing frontend scripts when relevant:

```sh
cd frontend
npm run lint
npm run build
```

If you change query hooks, route composition, or page rendering, verify the affected flow in the running app.

### Backend verification

At minimum, verify:

- the API process starts cleanly
- the affected endpoint imports and runs
- the worker restarts cleanly if worker code changed
- migrations still apply if schema changed

If you add or change database models, run the migration workflow from the API container:

```sh
docker compose exec api alembic revision --autogenerate
docker compose exec api alembic upgrade head
```

Do not trust the autogenerated migration blindly. If a new field is added to an existing table and Alembic makes it non-null immediately, inspect and patch the migration to:

1. add the column nullable
2. backfill existing rows
3. alter the column to non-null

After model or migration changes, prefer Docker-based verification against the running app:

```sh
docker compose logs --tail=200 api
docker compose exec api python -c "..."
docker compose exec db psql ...
```

For sync-related changes, verify against the existing ingestion path rather than creating a second path around it.

You have permission to trigger real local backend API calls for verification when that is the most direct way to test a change. Prefer hitting the existing application endpoints over inventing ad hoc scripts when validating request, sync, and worker flows.

### Worker verification

After changing any of the following, restart the worker and verify startup:

- `backend/app/tasks/*`
- `backend/app/core/broker.py`
- `backend/app/core/worker.py`
- code directly imported by task execution paths

Do not assume API reload also refreshes the worker.

If a change affects a queued sync or write path, verify both:

- worker startup is clean
- the real endpoint or job path runs without worker runtime errors

## Change strategy for this repo

When adding or modifying behavior, prefer these approaches in order:

1. Extend an existing service.
2. Extend existing CRUD for the needed persistence/query path.
3. Reuse an existing integration client if an external call is required.
4. Add a new module only when the existing structure has no natural home.

Examples:

- New read aggregation for leagues: likely belongs in `app/services/leagues/` or `app/services/dashboard/`, backed by `app/crud/sleeper/...`
- New DB-backed Sleeper view: extend normalized models and sync pipeline first
- New frontend server interaction: add endpoint wrapper, add hook, compose in page/component

## Things to avoid

- Don’t put business logic directly in FastAPI routers.
- Don’t query the database directly from frontend code.
- Don’t add live Sleeper reads to user-facing read endpoints if the same data should come from Postgres.
- Don’t bypass the existing `Context`/dependency model in the backend without a strong reason.
- Don’t introduce sync code paths into async request handling unless unavoidable.
- Don’t add dependencies without approval.
- Don’t create duplicate services when an existing service can be extended.

## Notes on documentation state

- The top-level `README.md` is currently project notes, not a reliable operational guide.
- `frontend/README.md` is still the default Vite template.

Treat the codebase and this file as the primary implementation guide unless the project documentation is updated.
