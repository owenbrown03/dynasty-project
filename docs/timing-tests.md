# League Details Timing Tests

Reference guide for benchmarking and profiling the league details endpoint.

For a repeatable benchmark, use [`docs/timing_benchmark.py`](./timing_benchmark.py). It supports:

- `--mode clickthrough` for dashboard -> details -> tiers
- `--mode site` for the broader read surface
- `--mode overlap` for concurrent in-flight requests that mimic clicking away before the previous page finishes
- `--mode cancel` for the same reads, but with older requests explicitly aborted after the next navigation starts

Pass `--flush-redis` to start each cycle cold on Redis. For a fully cold read, also restart the API so the in-memory caches clear.

## Endpoint

```
GET /api/v1/sleeper/leagues/details/{league_id}
```

### Authentication

Requires session cookie:

```
Cookie: session_token=b67a8b22c0ec54f6917534ab66a9dd516405137c51c8c9371ec8e6a82a91b65a
```

### Valid Test Leagues

All have rounds `[1,2,3,4]` and 12 rosters:

| Label | League ID | Notes |
|-------|-----------|-------|
| A | `1313688210445987840` | Primary test league |
| B | `1352347767644635136` | Same rounds as A, good for shared cache test |
| C | `1312262916115808256` | Same rounds, another option |

**Warning:** League `1317316464008519680` returns `null` (does not exist in DB). Always verify a league ID returns a 200 with a non-null body before using it for timing.

## Cache Architecture

| Cache | Key Pattern | TTL | Location | What it caches |
|-------|-------------|-----|----------|----------------|
| Rookie WAR shared | `rookie_war:shared::{rounds}` e.g. `rookie_war:shared::1-2-3-4` | 6 hours | Redis | Draft selections (4-column tuples) + stat seasons |
| Dashboard response | `dashboard:v1:{json}` | 10 minutes | Redis | Full serialized dashboard payload |
| League details response | `league-details:v1:{json}` | 10 minutes | Redis | Full serialized `LeagueDetailsResponse` |
| Dynasty projections | `dynasty-projection:v1:{hash}` | varies | Redis | Per-player dynasty projection objects |
| WAR calculation | in-memory LRU (size 128) | request lifetime | `WARService` singleton | Full `calculate_with_data` results keyed by `(season, scoring, roster_positions, total_rosters)` |
| Personal value hydration | in-memory + DB | persistent | `personal_values.py` | Personal rank curve rows in `personal_rank_curve` table |

## How to Flush / Reset Caches

### Full cold start (flush everything)

```sh
# 1. Flush Redis
docker compose exec redis redis-cli FLUSHALL

# 2. Restart API to clear in-memory LRU caches
docker compose restart api

# 3. Wait for API to be healthy
until curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; do
  sleep 1
done
echo "API is ready"
```

### Redis only (keep in-memory caches)

```sh
docker compose exec redis redis-cli FLUSHALL
```

This clears rookie WAR shared, league details response, and dynasty projection caches. In-memory WAR LRU caches survive.

### Targeted Redis key deletion

```sh
# Delete only rookie WAR shared cache
docker compose exec redis redis-cli KEYS "rookie_war:shared:*" | xargs docker compose exec -T redis redis-cli DEL

# Delete only league details cache
docker compose exec redis redis-cli KEYS "league-details:*" | xargs docker compose exec -T redis redis-cli DEL

# Delete only dynasty projection cache
docker compose exec redis redis-cli KEYS "dynasty-projection:*" | xargs docker compose exec -T redis redis-cli DEL
```

### In-memory only (restart API, keep Redis)

```sh
docker compose restart api
```

WAR LRU caches clear. Redis caches survive. Dashboard and league details response caches (10 minute TTLs) will expire naturally or be overwritten.

## Timing Test Protocol

The scripted version of this sequence lives in [`docs/timing_benchmark.py`](./timing_benchmark.py).
Run `python3 docs/timing_benchmark.py --mode overlap --flush-redis` to reproduce the concurrent click-through case.
Run `python3 docs/timing_benchmark.py --mode cancel --flush-redis` to reproduce the aborted-navigation case.

### Cold request (no caches)

1. Flush Redis + restart API (see "Full cold start" above)
2. Wait for health check
3. Time the request:

```sh
time curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  -b "session_token=b67a8b22c0ec54f6917534ab66a9dd516405137c51c8c9371ec8e6a82a91b65a" \
  "http://localhost:8000/api/v1/sleeper/leagues/details/1313688210445987840"
```

### Warm request (full response cache hit)

Immediately repeat the same request. The 10-minute response cache returns the full payload.

### Shared cache test (second league, same rounds)

After warming League A, request League B (same rounds `[1,2,3,4]`):

```sh
time curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  -b "session_token=b67a8b22c0ec54f6917534ab66a9dd516405137c51c8c9371ec8e6a82a91b65a" \
  "http://localhost:8000/api/v1/sleeper/leagues/details/1352347767644635136"
```

This tests whether the rookie WAR shared data (selections + seasons) is served from Redis rather than re-queried from Postgres.

### Full timing sequence

```sh
# Setup
docker compose exec redis redis-cli FLUSHALL
docker compose restart api
until curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; do sleep 1; done

TOKEN="session_token=b67a8b22c0ec54f6917534ab66a9dd516405137c51c8c9371ec8e6a82a91b65a"
A="1313688210445987840"
B="1352347767644635136"

echo "=== 1. A cold ==="
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" -b "$TOKEN" "http://localhost:8000/api/v1/sleeper/leagues/details/$A"

echo "=== 2. A warm ==="
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" -b "$TOKEN" "http://localhost:8000/api/v1/sleeper/leagues/details/$A"

echo "=== 3. B shared (same rounds) ==="
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" -b "$TOKEN" "http://localhost:8000/api/v1/sleeper/leagues/details/$B"

echo "=== 4. B warm ==="
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" -b "$TOKEN" "http://localhost:8000/api/v1/sleeper/leagues/details/$B"
```

## Log Interpretation

### Rookie WAR logs (`app.services.draft.rookie_war`)

| Log line | Meaning |
|----------|---------|
| `rookie_war shared data total took 0.3s` | Redis hit for selections + seasons |
| `rookie_war shared data total took 3.9s` | Redis miss, queried Postgres |
| `rookie_war get_selections took 3.7s` | DB query for `get_historical_rookie_draft_selections` |
| `rookie_war get_seasons took 0.1s` | DB query for `get_available_stat_seasons` |
| `rookie_war get_players took 0.1-0.5s` | Always fresh (not cached), loads full player table |
| `rookie_war season=XXXX elapsed=Xs` | Per-season WAR calculation (0.0-0.1s each) |

### Personal value hydration (`app.services.personal_values`)

| Log line | Meaning |
|----------|---------|
| `Personal value hydration source=redis ... elapsed_ms=X` | Cache hit |
| `Personal value hydration source=calculated ... elapsed_ms=X` | Cache miss, computed from scratch (~700-1000ms) |

### WAR calculations (`app.analytics.war.redraft`)

| Log line | Meaning |
|----------|---------|
| `Calculating replacement levels` | Start of a WAR calculation for one season+position |
| `Merged XXXX WAR results` | Completed WAR calculation (higher count = more players) |

## Timing Breakdown (Baseline)

Measured on the dev stack with valid league IDs:

### League A cold (8.3s)

| Phase | Time | Notes |
|-------|------|-------|
| Pre-WAR pipeline | ~2.6s | League fetch, roster construction, dynasty projections, FC/KTC pick values, trade counts |
| Personal value hydration | ~0.9s | `_ensure_personal_rank_curve` on miss |
| Selections DB query | ~3.7s | `get_historical_rookie_draft_selections` (648K rows) |
| Stat seasons DB query | ~0.1s | `get_available_stat_seasons` |
| get_players | ~0.1s | Full player table, always fresh |
| Per-season WAR loop | ~0.5s | 8 seasons × ~0.05s each |
| Redis write + response serialization | ~0.4s | Caches shared data + full response |

### League A warm (0.1s)

Full response cache hit (`league-details:v1:...`). Returns serialized `LeagueDetailsResponse` directly.

### League B shared (4.3s)

| Phase | Time | Notes |
|-------|------|-------|
| Pre-WAR pipeline | ~2.5s | Same as A (not cached at this level) |
| Personal value hydration | ~0.7s | Cache miss for this league |
| Selections from Redis | ~0.3s | **Cached!** (was 3.7s) |
| get_players | ~0.5s | Always fresh |
| Per-season WAR loop | ~0.5s | 9 seasons |

### League B warm (0.1s)

Full response cache hit.

### Summary

| Request | Time | vs Cold |
|---------|------|---------|
| A cold | 8.3s | baseline |
| A warm | 0.1s | 78x faster |
| B shared | 4.3s | 1.9x faster |
| B warm | 0.1s | 78x faster |

## Pre-WAR Pipeline Breakdown

The ~2.5s pre-WAR pipeline runs these operations sequentially:

1. **League + rosters fetch** — `get_league_with_rosters` (DB JOIN)
2. **Trade counts** — `get_trade_counts_by_roster_id` (DB JOIN + GROUP BY)
3. **User notes** — `get_user_notes_by_league_id` (DB SELECT)
4. **Sync states** — `get_sync_states` (DB SELECT)
5. **Full response cache check** — Redis GET (60s TTL)
6. **WAR shared data load** — `war_service.load_shared_data` (DB: all players + projections)
7. **Historical WAR** — 3 methods iterating overlapping seasons (5-13 DB queries + WAR calculations, many LRU-cached)
8. **Current season WAR** — `war_service.calculate_with_data` (LRU-cached from step 7)
9. **Dynasty projections** — Redis MGET + per-player computation on miss
10. **Users** — `get_users` (DB SELECT)
11. **Player values** — 4 sequential DB queries (Player, KTC, FC, Underdog ADP)
12. **Personal value hydration** — ~0.7-1.0s (see above)
13. **FC/KTC pick values** — 2 DB lookups
14. **Draft data** — 3 DB queries (drafts, completed seasons, traded picks)

### Parallelization opportunities

Steps 2-4 could run concurrently with `asyncio.gather` after step 1.

Steps 7-9 do redundant work: all three iterate overlapping seasons calling the same `get_season_stats` + `calculate_with_data`. Deduplicating to a single WAR pass per season could save ~500ms-1s.

Steps 11's 4 DB queries are independent and could run concurrently.

Steps 13's FC and KTC lookups are independent and could run concurrently.

## RedisClient API

The `RedisClient` wrapper (`backend/app/infrastructure/redis/client.py`) exposes:

```python
await redis.get(key: str) -> str | None
await redis.mget(keys: list[str]) -> list[str | None]
await redis.set(key: str, value: str, ttl_seconds: int | None = None)
await redis.delete(key: str)
await redis.delete_prefix(prefix: str)  # scan + delete
```

**Important:** Use `ttl_seconds=` not `ex=` when calling `set()`. The wrapper translates to `redis.set(key, value, ex=ttl_seconds)`.
