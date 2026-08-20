#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = os.getenv(
    "DYNASTY_TIMING_BASE_URL",
    "http://localhost:8000/api/v1",
)
DEFAULT_SESSION_TOKEN = os.getenv(
    "DYNASTY_SESSION_TOKEN",
    "b67a8b22c0ec54f6917534ab66a9dd516405137c51c8c9371ec8e6a82a91b65a",
)
DEFAULT_USERNAME = os.getenv(
    "DYNASTY_TIMING_USERNAME",
    "browntown333",
)
DEFAULT_DETAILS_LEAGUE_ID = os.getenv(
    "DYNASTY_TIMING_DETAILS_LEAGUE_ID",
    "1312499253972602880",
)
DEFAULT_SHARED_LEAGUE_ID = os.getenv(
    "DYNASTY_TIMING_SHARED_LEAGUE_ID",
    "1312499253972602880",
)
DEFAULT_SECOND_LEAGUE_ID = os.getenv(
    "DYNASTY_TIMING_SECOND_LEAGUE_ID",
    "1312474596544368640",
)
DEFAULT_VALUE_BASIS = os.getenv(
    "DYNASTY_TIMING_VALUE_BASIS",
    "my_war",
)
DEFAULT_BULK_SEARCH_QUERY = os.getenv(
    "DYNASTY_TIMING_BULK_SEARCH_QUERY",
    "Dav",
)
DEFAULT_RECENT_DROPS_SORT = os.getenv(
    "DYNASTY_TIMING_RECENT_DROPS_SORT",
    "recency",
)
DEFAULT_TRADE_SEASON = os.getenv(
    "DYNASTY_TIMING_TRADE_SEASON",
    str(time.localtime().tm_year),
)


class BenchmarkError(RuntimeError):
    pass


@dataclass(frozen=True)
class RequestSpec:
    name: str
    method: str
    url: str
    validator: Callable[[Any], str]
    delay_seconds: float = 0.0


@dataclass(frozen=True)
class RequestResult:
    scenario: str
    name: str
    method: str
    url: str
    status_code: int
    start_offset_seconds: float
    elapsed_seconds: float
    payload_bytes: int
    summary: str


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    results: list[RequestResult]
    wall_time_seconds: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure representative Dynasty read paths, including "
            "concurrent click-through overlap."
        ),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--session-token", default=DEFAULT_SESSION_TOKEN)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--details-league-id", default=DEFAULT_DETAILS_LEAGUE_ID)
    parser.add_argument("--shared-league-id", default=DEFAULT_SHARED_LEAGUE_ID)
    parser.add_argument("--second-league-id", default=DEFAULT_SECOND_LEAGUE_ID)
    parser.add_argument("--value-basis", default=DEFAULT_VALUE_BASIS)
    parser.add_argument("--bulk-search-query", default=DEFAULT_BULK_SEARCH_QUERY)
    parser.add_argument("--recent-drops-sort", default=DEFAULT_RECENT_DROPS_SORT)
    parser.add_argument("--trade-season", default=DEFAULT_TRADE_SEASON)
    parser.add_argument("--trade-round", type=int, default=1)
    parser.add_argument("--trade-slot", type=int, default=1)
    parser.add_argument("--trade-total-rosters", type=int, default=12)
    parser.add_argument("--trade-num-qbs", type=int, default=2)
    parser.add_argument("--trade-ppr", type=int, default=1)
    parser.add_argument(
        "--mode",
        choices=("clickthrough", "site", "overlap", "all"),
        default="all",
        help=(
            "Which scenario to run. 'clickthrough' is the dashboard -> "
            "details -> tiers path, 'site' covers the broader read surface, "
            "and 'overlap' launches the heavy reads at once."
        ),
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=2,
        help=(
            "How many times to repeat each scenario. The first cycle is the "
            "cold run if you also pass --flush-redis."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("DYNASTY_TIMING_TIMEOUT", "60")),
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--stagger-ms",
        type=float,
        default=float(os.getenv("DYNASTY_TIMING_STAGGER_MS", "50")),
        help="Delay between concurrent starts in overlap mode.",
    )
    parser.add_argument(
        "--flush-redis",
        action="store_true",
        help="Flush Redis before each cycle so the run starts cold.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        help="Optional path to write a machine-readable report.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkError(message)


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def build_url(base_url: str, path: str, params: dict[str, object] | None = None) -> str:
    url = f"{normalize_base_url(base_url)}{path}"
    if not params:
        return url
    query = urlencode(
        {
            key: value
            for key, value in params.items()
            if value is not None
        },
        doseq=True,
    )
    return f"{url}?{query}"


def build_headers(session_token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Cookie": f"session_token={session_token}",
        "User-Agent": "dynasty-timing-benchmark/2.0",
    }


def flush_redis() -> None:
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "redis",
        "redis-cli",
        "FLUSHALL",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise BenchmarkError("docker is not available; cannot flush Redis") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise BenchmarkError(
            f"Redis flush failed: {stderr or exc}"
        ) from exc

    stdout = (completed.stdout or "").strip()
    if stdout:
        print(f"Flushed Redis: {stdout}")


def decode_json(body: bytes, *, url: str, method: str) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        snippet = body[:500].decode("utf-8", errors="replace").strip()
        raise BenchmarkError(
            f"{method} {url} returned invalid JSON: {snippet!r}"
        ) from exc


def request_json(
    *,
    headers: dict[str, str],
    method: str,
    url: str,
    timeout: float,
) -> tuple[Any, int, int, float]:
    started = time.perf_counter()
    try:
        request = Request(url, method=method, headers=headers)
        with urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read()
    except HTTPError as exc:
        body = exc.read() or b""
        elapsed = time.perf_counter() - started
        snippet = body[:500].decode("utf-8", errors="replace").strip()
        raise BenchmarkError(
            f"{method} {url} returned {exc.code} after {elapsed:.3f}s: {snippet!r}"
        ) from exc
    except URLError as exc:
        raise BenchmarkError(f"{method} {url} failed: {exc.reason}") from exc

    elapsed = time.perf_counter() - started
    payload_bytes = len(body)
    payload = decode_json(
        body,
        url=url,
        method=method,
    )
    return payload, status_code, payload_bytes, elapsed


def validate_dashboard_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "dashboard payload must be an object")
    leagues = payload.get("leagues")
    require(isinstance(leagues, list), "dashboard payload must include leagues[]")
    require(leagues, "dashboard payload leagues[] must not be empty")
    require(
        all(isinstance(league, dict) for league in leagues),
        "dashboard leagues[] entries must be objects",
    )
    return f"{len(leagues)} leagues"


def validate_league_overview_payload(payload: Any) -> str:
    require(isinstance(payload, list), "league overview payload must be a list")
    require(payload, "league overview payload must not be empty")
    require(
        all(isinstance(league, dict) for league in payload),
        "league overview entries must be objects",
    )
    return f"{len(payload)} leagues"


def validate_details_payload(payload: Any, *, league_id: str) -> str:
    require(isinstance(payload, dict), "details payload must be an object")
    require(
        payload.get("league_id") == league_id,
        f"details payload league_id mismatch: expected {league_id}",
    )

    rosters = payload.get("rosters")
    require(isinstance(rosters, list), "details payload must include rosters[]")
    require(rosters, "details payload rosters[] must not be empty")
    require(
        all(isinstance(roster, dict) for roster in rosters),
        "details rosters[] entries must be objects",
    )

    require(
        isinstance(payload.get("roster_positions"), list),
        "details payload must include roster_positions[]",
    )
    require(
        isinstance(payload.get("roster_construction_targets"), list),
        "details payload must include roster_construction_targets[]",
    )
    require(
        isinstance(payload.get("settings_details"), list),
        "details payload must include settings_details[]",
    )
    return f"{len(rosters)} rosters"


def validate_tiers_payload(payload: Any, *, league_id: str, value_basis: str) -> str:
    require(isinstance(payload, dict), "tiers payload must be an object")
    require(
        payload.get("value_basis") == value_basis,
        f"tiers payload value_basis mismatch: expected {value_basis}",
    )
    if value_basis == "my_war":
        require(
            payload.get("war_league_id") == league_id,
            f"tiers payload war_league_id mismatch: expected {league_id}",
        )

    tiers = payload.get("tiers")
    require(isinstance(tiers, list), "tiers payload must include tiers[]")
    require(tiers, "tiers payload tiers[] must not be empty")
    for tier in tiers:
        require(isinstance(tier, dict), "tier groups must be objects")
        require(
            isinstance(tier.get("players"), list),
            "tier groups must include players[]",
        )
    return f"{len(tiers)} tiers"


def validate_trade_signals_payload(payload: Any) -> str:
    require(isinstance(payload, list), "trade signals payload must be a list")
    if not payload:
        return "0 trade signals"
    require(
        all(isinstance(item, dict) for item in payload),
        "trade signal entries must be objects",
    )
    return f"{len(payload)} trade signals"


def validate_waiver_overview_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "waiver overview payload must be an object")
    leagues = payload.get("leagues")
    require(isinstance(leagues, list), "waiver overview payload must include leagues[]")
    return f"{len(leagues)} leagues"


def validate_waiver_recent_drops_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "recent drops payload must be an object")
    players = payload.get("players")
    require(isinstance(players, list), "recent drops payload must include players[]")
    return f"{len(players)} players"


def validate_waiver_available_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "available players payload must be an object")
    players = payload.get("players")
    require(isinstance(players, list), "available players payload must include players[]")
    return f"{len(players)} players"


def validate_waiver_roster_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "roster players payload must be an object")
    players = payload.get("players")
    require(isinstance(players, list), "roster players payload must include players[]")
    return f"{len(players)} players"


def validate_bulk_trade_search_payload(payload: Any) -> str:
    require(isinstance(payload, list), "bulk trade search payload must be a list")
    require(
        all(isinstance(item, dict) for item in payload),
        "bulk trade search entries must be objects",
    )
    return f"{len(payload)} players"


def validate_trade_calculator_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "trade calculator payload must be an object")
    require(
        "season" in payload and "round" in payload,
        "trade calculator payload must include season and round",
    )
    return f"season {payload.get('season')} round {payload.get('round')}"


def request_spec(
    name: str,
    method: str,
    url: str,
    validator: Callable[[Any], str],
    *,
    delay_seconds: float = 0.0,
) -> RequestSpec:
    return RequestSpec(
        name=name,
        method=method,
        url=url,
        validator=validator,
        delay_seconds=delay_seconds,
    )


def build_clickthrough_specs(args: argparse.Namespace) -> list[RequestSpec]:
    return [
        request_spec(
            "dashboard",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/dashboard/{args.username}"),
            validate_dashboard_payload,
        ),
        request_spec(
            "details",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/details/{args.details_league_id}"),
            lambda payload: validate_details_payload(
                payload,
                league_id=args.details_league_id,
            ),
        ),
        request_spec(
            "tiers",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/players/tiers",
                {
                    "value_basis": args.value_basis,
                    "league_id": args.shared_league_id,
                },
            ),
            lambda payload: validate_tiers_payload(
                payload,
                league_id=args.shared_league_id,
                value_basis=args.value_basis,
            ),
        ),
    ]


def build_site_specs(args: argparse.Namespace) -> list[RequestSpec]:
    return [
        request_spec(
            "league-overview",
            "GET",
            build_url(
                args.base_url,
                f"/sleeper/leagues/overview/{args.username}",
            ),
            validate_league_overview_payload,
        ),
        request_spec(
            "dashboard",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/dashboard/{args.username}"),
            validate_dashboard_payload,
        ),
        request_spec(
            "details-primary",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/details/{args.details_league_id}"),
            lambda payload: validate_details_payload(
                payload,
                league_id=args.details_league_id,
            ),
        ),
        request_spec(
            "details-shared",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/details/{args.shared_league_id}"),
            lambda payload: validate_details_payload(
                payload,
                league_id=args.shared_league_id,
            ),
        ),
        request_spec(
            "tiers",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/players/tiers",
                {
                    "value_basis": args.value_basis,
                    "league_id": args.shared_league_id,
                },
            ),
            lambda payload: validate_tiers_payload(
                payload,
                league_id=args.shared_league_id,
                value_basis=args.value_basis,
            ),
        ),
        request_spec(
            "trade-signals",
            "GET",
            build_url(args.base_url, f"/sleeper/trades/{args.username}/trade-signals"),
            validate_trade_signals_payload,
        ),
        request_spec(
            "bulk-trade-search",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/trades/bulk/search",
                {"q": args.bulk_search_query},
            ),
            validate_bulk_trade_search_payload,
        ),
        request_spec(
            "waiver-overview",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/overview",
                {"value_basis": args.value_basis},
            ),
            validate_waiver_overview_payload,
        ),
        request_spec(
            "recent-drops",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/recent-drops",
                {
                    "value_basis": args.value_basis,
                    "page": 1,
                    "page_size": 25,
                    "sort_by": args.recent_drops_sort,
                },
            ),
            validate_waiver_recent_drops_payload,
        ),
        request_spec(
            "available-players",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/available",
                {
                    "league_id": args.shared_league_id,
                    "value_basis": args.value_basis,
                    "page": 1,
                    "page_size": 25,
                },
            ),
            validate_waiver_available_payload,
        ),
        request_spec(
            "roster-players",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/roster-players",
                {
                    "league_id": args.shared_league_id,
                    "value_basis": args.value_basis,
                },
            ),
            validate_waiver_roster_payload,
        ),
        request_spec(
            "trade-calculator",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/trades/calculator/pick-value",
                {
                    "season": args.trade_season,
                    "round": args.trade_round,
                    "slot": args.trade_slot,
                    "total_rosters": args.trade_total_rosters,
                    "num_qbs": args.trade_num_qbs,
                    "ppr": args.trade_ppr,
                },
            ),
            validate_trade_calculator_payload,
        ),
    ]


def build_overlap_specs(args: argparse.Namespace) -> list[RequestSpec]:
    stagger = max(args.stagger_ms, 0.0) / 1000.0
    return [
        request_spec(
            "dashboard",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/dashboard/{args.username}"),
            validate_dashboard_payload,
            delay_seconds=0.0,
        ),
        request_spec(
            "overview",
            "GET",
            build_url(
                args.base_url,
                f"/sleeper/leagues/overview/{args.username}",
            ),
            validate_league_overview_payload,
            delay_seconds=stagger,
        ),
        request_spec(
            "details",
            "GET",
            build_url(args.base_url, f"/sleeper/leagues/details/{args.details_league_id}"),
            lambda payload: validate_details_payload(
                payload,
                league_id=args.details_league_id,
            ),
            delay_seconds=stagger * 2,
        ),
        request_spec(
            "tiers",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/players/tiers",
                {
                    "value_basis": args.value_basis,
                    "league_id": args.shared_league_id,
                },
            ),
            lambda payload: validate_tiers_payload(
                payload,
                league_id=args.shared_league_id,
                value_basis=args.value_basis,
            ),
            delay_seconds=stagger * 3,
        ),
        request_spec(
            "trade-signals",
            "GET",
            build_url(args.base_url, f"/sleeper/trades/{args.username}/trade-signals"),
            validate_trade_signals_payload,
            delay_seconds=stagger * 4,
        ),
        request_spec(
            "waiver-overview",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/overview",
                {"value_basis": args.value_basis},
            ),
            validate_waiver_overview_payload,
            delay_seconds=stagger * 5,
        ),
        request_spec(
            "recent-drops",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/recent-drops",
                {
                    "value_basis": args.value_basis,
                    "page": 1,
                    "page_size": 25,
                    "sort_by": args.recent_drops_sort,
                },
            ),
            validate_waiver_recent_drops_payload,
            delay_seconds=stagger * 6,
        ),
        request_spec(
            "available-players",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/available",
                {
                    "league_id": args.shared_league_id,
                    "value_basis": args.value_basis,
                    "page": 1,
                    "page_size": 25,
                },
            ),
            validate_waiver_available_payload,
            delay_seconds=stagger * 7,
        ),
        request_spec(
            "roster-players",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/waivers/roster-players",
                {
                    "league_id": args.shared_league_id,
                    "value_basis": args.value_basis,
                },
            ),
            validate_waiver_roster_payload,
            delay_seconds=stagger * 8,
        ),
        request_spec(
            "bulk-trade-search",
            "GET",
            build_url(
                args.base_url,
                "/sleeper/trades/bulk/search",
                {"q": args.bulk_search_query},
            ),
            validate_bulk_trade_search_payload,
            delay_seconds=stagger * 9,
        ),
    ]


def run_spec(
    *,
    scenario: str,
    spec: RequestSpec,
    headers: dict[str, str],
    timeout: float,
    scenario_origin: float,
) -> RequestResult:
    if spec.delay_seconds > 0:
        time.sleep(spec.delay_seconds)

    started = time.perf_counter()
    payload, status_code, payload_bytes, elapsed = request_json(
        headers=headers,
        method=spec.method,
        url=spec.url,
        timeout=timeout,
    )
    summary = spec.validator(payload)

    return RequestResult(
        scenario=scenario,
        name=spec.name,
        method=spec.method,
        url=spec.url,
        status_code=status_code,
        start_offset_seconds=started - scenario_origin,
        elapsed_seconds=elapsed,
        payload_bytes=payload_bytes,
        summary=summary,
    )


def run_sequential_scenario(
    *,
    scenario: str,
    specs: list[RequestSpec],
    headers: dict[str, str],
    timeout: float,
) -> ScenarioResult:
    print(f"Scenario {scenario}:")
    started = time.perf_counter()
    results: list[RequestResult] = []

    for spec in specs:
        result = run_spec(
            scenario=scenario,
            spec=spec,
            headers=headers,
            timeout=timeout,
            scenario_origin=started,
        )
        results.append(result)
        print(
            f"  {result.name:<18} "
            f"{result.status_code} "
            f"{result.start_offset_seconds:>7.3f}s + {result.elapsed_seconds:>7.3f}s "
            f"{result.payload_bytes:>8} bytes  {result.summary}",
        )

    wall_time = time.perf_counter() - started
    return ScenarioResult(
        name=scenario,
        results=results,
        wall_time_seconds=wall_time,
    )


def run_overlap_scenario(
    *,
    scenario: str,
    specs: list[RequestSpec],
    headers: dict[str, str],
    timeout: float,
) -> ScenarioResult:
    print(f"Scenario {scenario}:")
    started = time.perf_counter()
    results: list[RequestResult] = []
    lock = threading.Lock()

    def worker(spec: RequestSpec) -> RequestResult:
        result = run_spec(
            scenario=scenario,
            spec=spec,
            headers=headers,
            timeout=timeout,
            scenario_origin=started,
        )
        with lock:
            print(
                f"  {result.name:<18} "
                f"{result.status_code} "
                f"{result.start_offset_seconds:>7.3f}s + {result.elapsed_seconds:>7.3f}s "
                f"{result.payload_bytes:>8} bytes  {result.summary}",
            )
        return result

    with ThreadPoolExecutor(max_workers=len(specs)) as executor:
        futures = [executor.submit(worker, spec) for spec in specs]
        for future in futures:
            results.append(future.result())

    wall_time = time.perf_counter() - started
    return ScenarioResult(
        name=scenario,
        results=sorted(results, key=lambda result: result.start_offset_seconds),
        wall_time_seconds=wall_time,
    )


def print_scenario_summary(result: ScenarioResult) -> None:
    print()
    print(f"Summary for {result.name}:")
    timings = [entry.elapsed_seconds for entry in result.results]
    if timings:
        print(
            f"  requests {len(timings)}  "
            f"wall {result.wall_time_seconds:.3f}s  "
            f"avg {statistics.mean(timings):.3f}s  "
            f"min {min(timings):.3f}s  "
            f"max {max(timings):.3f}s"
        )
        overlap_ratio = sum(timings) / result.wall_time_seconds if result.wall_time_seconds > 0 else float("inf")
        print(f"  overlap multiplier {overlap_ratio:.2f}x")

    if len(result.results) >= 2:
        first = result.results[0]
        last = max(result.results, key=lambda entry: entry.start_offset_seconds + entry.elapsed_seconds)
        print(
            f"  span {first.start_offset_seconds:.3f}s -> "
            f"{last.start_offset_seconds + last.elapsed_seconds:.3f}s"
        )


def write_report(path: Path, *, args: argparse.Namespace, scenarios: list[ScenarioResult]) -> None:
    payload = {
        "args": {
            "base_url": args.base_url,
            "username": args.username,
            "details_league_id": args.details_league_id,
            "shared_league_id": args.shared_league_id,
            "second_league_id": args.second_league_id,
            "value_basis": args.value_basis,
            "bulk_search_query": args.bulk_search_query,
            "recent_drops_sort": args.recent_drops_sort,
            "trade_season": args.trade_season,
            "trade_round": args.trade_round,
            "trade_slot": args.trade_slot,
            "trade_total_rosters": args.trade_total_rosters,
            "trade_num_qbs": args.trade_num_qbs,
            "trade_ppr": args.trade_ppr,
            "mode": args.mode,
            "cycles": args.cycles,
            "timeout": args.timeout,
            "stagger_ms": args.stagger_ms,
            "flush_redis": args.flush_redis,
        },
        "scenarios": [
            {
                "name": scenario.name,
                "wall_time_seconds": scenario.wall_time_seconds,
                "results": [asdict(result) for result in scenario.results],
            }
            for scenario in scenarios
        ],
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def print_comparison(scenarios: list[ScenarioResult]) -> None:
    if len(scenarios) < 2:
        return

    print()
    print("Scenario comparison:")
    for scenario in scenarios:
        timings = [result.elapsed_seconds for result in scenario.results]
        if not timings:
            continue
        print(
            f"  {scenario.name:<12} "
            f"wall {scenario.wall_time_seconds:.3f}s "
            f"avg {statistics.mean(timings):.3f}s"
        )


def scenario_plan(args: argparse.Namespace) -> list[tuple[str, Callable[[argparse.Namespace], list[RequestSpec]], Callable[..., ScenarioResult]]]:
    plans: list[tuple[str, Callable[[argparse.Namespace], list[RequestSpec]], Callable[..., ScenarioResult]]] = []

    if args.mode in {"clickthrough", "all"}:
        plans.append(("clickthrough", build_clickthrough_specs, run_sequential_scenario))
    if args.mode in {"site", "all"}:
        plans.append(("site", build_site_specs, run_sequential_scenario))
    if args.mode in {"overlap", "all"}:
        plans.append(("overlap", build_overlap_specs, run_overlap_scenario))

    return plans


def main() -> int:
    args = parse_args()

    require(args.cycles >= 1, "--cycles must be at least 1")
    require(args.timeout > 0, "--timeout must be greater than 0")
    require(bool(args.session_token), "--session-token must not be empty")

    headers = build_headers(args.session_token)
    scenarios: list[ScenarioResult] = []

    try:
        for cycle in range(1, args.cycles + 1):
            print(f"Cycle {cycle}:")
            if args.flush_redis:
                flush_redis()

            for scenario_name, spec_builder, runner in scenario_plan(args):
                specs = spec_builder(args)
                scenario_result = runner(
                    scenario=scenario_name,
                    specs=specs,
                    headers=headers,
                    timeout=args.timeout,
                )
                print_scenario_summary(scenario_result)
                scenarios.append(scenario_result)
                print()
    except BenchmarkError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print_comparison(scenarios)

    if args.report_json is not None:
        write_report(args.report_json, args=args, scenarios=scenarios)
        print()
        print(f"Wrote report to {args.report_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
