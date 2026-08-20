#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = os.getenv("DYNASTY_TIMING_BASE_URL", "http://localhost:8000/api/v1")
DEFAULT_SESSION_TOKEN = os.getenv(
    "DYNASTY_SESSION_TOKEN",
    "b67a8b22c0ec54f6917534ab66a9dd516405137c51c8c9371ec8e6a82a91b65a",
)
DEFAULT_USERNAME = os.getenv("DYNASTY_TIMING_USERNAME", "browntown333")
DEFAULT_DETAILS_LEAGUE_ID = os.getenv("DYNASTY_TIMING_DETAILS_LEAGUE_ID", "1312499253972602880")
DEFAULT_TIERS_LEAGUE_ID = os.getenv("DYNASTY_TIMING_TIERS_LEAGUE_ID", "1312499253972602880")
DEFAULT_VALUE_BASIS = os.getenv("DYNASTY_TIMING_VALUE_BASIS", "my_war")


class BenchmarkError(RuntimeError):
    pass


@dataclass(frozen=True)
class RequestResult:
    cycle: int
    step: str
    method: str
    url: str
    status_code: int
    elapsed_seconds: float
    payload_bytes: int
    summary: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure dashboard -> details -> tiers timing against a local Dynasty API.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--session-token", default=DEFAULT_SESSION_TOKEN)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--details-league-id", default=DEFAULT_DETAILS_LEAGUE_ID)
    parser.add_argument("--tiers-league-id", default=DEFAULT_TIERS_LEAGUE_ID)
    parser.add_argument("--value-basis", default=DEFAULT_VALUE_BASIS)
    parser.add_argument(
        "--cycles",
        type=int,
        default=2,
        help="Number of dashboard -> details -> tiers passes to run.",
    )
    parser.add_argument("--timeout", type=float, default=float(os.getenv("DYNASTY_TIMING_TIMEOUT", "60")))
    parser.add_argument("--report-json", type=Path, help="Optional path to write a JSON report")
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkError(message)


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def build_url(base_url: str, path: str) -> str:
    return f"{normalize_base_url(base_url)}{path}"


def build_headers(session_token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "User-Agent": "dynasty-timing-benchmark/1.0",
        "Cookie": f"session_token={session_token}",
    }


def request_json(
    headers: dict[str, str],
    *,
    method: str,
    url: str,
    timeout: float,
) -> tuple[Any, float, int, int]:
    started = time.perf_counter()
    try:
        request = Request(url, method=method, headers=headers)
        with urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read()
    except HTTPError as exc:
        elapsed = time.perf_counter() - started
        body = exc.read() or b""
        snippet = body[:500].decode("utf-8", errors="replace").strip()
        raise BenchmarkError(
            f"{method} {url} returned {exc.code} after {elapsed:.3f}s: {snippet!r}"
        ) from exc
    except URLError as exc:
        raise BenchmarkError(f"{method} {url} failed: {exc.reason}") from exc

    elapsed = time.perf_counter() - started
    payload_bytes = len(body)

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        snippet = body[:500].decode("utf-8", errors="replace").strip()
        raise BenchmarkError(f"{method} {url} returned invalid JSON: {snippet!r}") from exc

    return payload, elapsed, status_code, payload_bytes


def validate_dashboard_payload(payload: Any) -> str:
    require(isinstance(payload, dict), "dashboard payload must be an object")
    leagues = payload.get("leagues")
    require(isinstance(leagues, list), "dashboard payload must include leagues[]")
    require(leagues, "dashboard payload leagues[] must not be empty")
    require(all(isinstance(league, dict) for league in leagues), "dashboard leagues[] entries must be objects")
    return f"{len(leagues)} leagues"


def validate_details_payload(payload: Any, *, league_id: str) -> str:
    require(isinstance(payload, dict), "details payload must be an object")
    require(payload.get("league_id") == league_id, f"details payload league_id mismatch: expected {league_id}")

    rosters = payload.get("rosters")
    require(isinstance(rosters, list), "details payload must include rosters[]")
    require(rosters, "details payload rosters[] must not be empty")
    require(all(isinstance(roster, dict) for roster in rosters), "details rosters[] entries must be objects")

    require(isinstance(payload.get("roster_positions"), list), "details payload must include roster_positions[]")
    require(
        isinstance(payload.get("roster_construction_targets"), list),
        "details payload must include roster_construction_targets[]",
    )
    require(isinstance(payload.get("settings_details"), list), "details payload must include settings_details[]")
    return f"{len(rosters)} rosters"


def validate_tiers_payload(payload: Any, *, league_id: str, value_basis: str) -> str:
    require(isinstance(payload, dict), "tiers payload must be an object")
    require(payload.get("value_basis") == value_basis, f"tiers payload value_basis mismatch: expected {value_basis}")

    if value_basis == "my_war":
        require(payload.get("war_league_id") == league_id, f"tiers payload war_league_id mismatch: expected {league_id}")

    tiers = payload.get("tiers")
    require(isinstance(tiers, list), "tiers payload must include tiers[]")
    require(tiers, "tiers payload tiers[] must not be empty")
    for tier in tiers:
        require(isinstance(tier, dict), "tier groups must be objects")
        require(isinstance(tier.get("players"), list), "tier groups must include players[]")

    return f"{len(tiers)} tiers"


def run_cycle(
    *,
    headers: dict[str, str],
    base_url: str,
    timeout: float,
    cycle: int,
    username: str,
    details_league_id: str,
    tiers_league_id: str,
    value_basis: str,
) -> list[RequestResult]:
    steps = [
        (
            "dashboard",
            "GET",
            build_url(base_url, f"/sleeper/leagues/dashboard/{username}"),
            validate_dashboard_payload,
            {},
        ),
        (
            "details",
            "GET",
            build_url(base_url, f"/sleeper/leagues/details/{details_league_id}"),
            validate_details_payload,
            {"league_id": details_league_id},
        ),
        (
            "tiers",
            "GET",
            build_url(base_url, f"/sleeper/players/tiers?value_basis={value_basis}&league_id={tiers_league_id}"),
            validate_tiers_payload,
            {"league_id": tiers_league_id, "value_basis": value_basis},
        ),
    ]

    print(f"Cycle {cycle}:")
    results: list[RequestResult] = []
    for step_name, method, url, validator, validator_kwargs in steps:
        payload, elapsed, status_code, payload_bytes = request_json(
            headers,
            method=method,
            url=url,
            timeout=timeout,
        )
        summary = validator(payload, **validator_kwargs)
        result = RequestResult(
            cycle=cycle,
            step=step_name,
            method=method,
            url=url,
            status_code=status_code,
            elapsed_seconds=elapsed,
            payload_bytes=payload_bytes,
            summary=summary,
        )
        results.append(result)
        print(f"  {step_name:<9} {status_code} {elapsed:>7.3f}s {payload_bytes:>8} bytes  {summary}")

    return results


def print_summary(results: list[RequestResult]) -> None:
    by_step: dict[str, list[float]] = {}
    for result in results:
        by_step.setdefault(result.step, []).append(result.elapsed_seconds)

    print()
    print("Summary:")
    for step in ("dashboard", "details", "tiers"):
        timings = by_step.get(step, [])
        if not timings:
            continue
        print(
            f"  {step:<9} avg {statistics.mean(timings):.3f}s min {min(timings):.3f}s max {max(timings):.3f}s"
        )

    if len(results) >= 6:
        first_cycle = {result.step: result for result in results[:3]}
        second_cycle = {result.step: result for result in results[3:6]}
        print()
        print("Cycle 2 vs cycle 1:")
        for step in ("dashboard", "details", "tiers"):
            first = first_cycle[step].elapsed_seconds
            second = second_cycle[step].elapsed_seconds
            delta = second - first
            ratio = second / first if first > 0 else float("inf")
            print(f"  {step:<9} {first:.3f}s -> {second:.3f}s ({delta:+.3f}s, {ratio:.2f}x)")


def write_report(path: Path, *, args: argparse.Namespace, results: list[RequestResult]) -> None:
    payload = {
        "args": {
            "base_url": args.base_url,
            "username": args.username,
            "details_league_id": args.details_league_id,
            "tiers_league_id": args.tiers_league_id,
            "value_basis": args.value_basis,
            "cycles": args.cycles,
            "timeout": args.timeout,
        },
        "results": [asdict(result) for result in results],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    require(args.cycles >= 1, "--cycles must be at least 1")
    require(args.timeout > 0, "--timeout must be greater than 0")
    require(bool(args.session_token), "--session-token must not be empty")

    headers = build_headers(args.session_token)
    all_results: list[RequestResult] = []

    try:
        for cycle in range(1, args.cycles + 1):
            all_results.extend(
                run_cycle(
                    headers=headers,
                    base_url=args.base_url,
                    timeout=args.timeout,
                    cycle=cycle,
                    username=args.username,
                    details_league_id=args.details_league_id,
                    tiers_league_id=args.tiers_league_id,
                    value_basis=args.value_basis,
                )
            )
    except BenchmarkError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print_summary(all_results)

    if args.report_json is not None:
        write_report(args.report_json, args=args, results=all_results)
        print()
        print(f"Wrote report to {args.report_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
