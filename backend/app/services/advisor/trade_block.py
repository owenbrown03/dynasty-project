import json
import logging

from app.api.deps import ContextDep
from app.integrations.sleeper.client import SleeperClient

logger = logging.getLogger(__name__)

TRADE_BLOCK_CACHE_TTL_SECONDS = 6 * 60 * 60


class TradeBlockSnapshot:
    """Parsed trade-block state for one league.

    player_ids maps a Sleeper player_id to the roster_id that put
    him on the block. picks holds parsed draft-pick entries with
    (round, season, original_roster_id) -> blocking roster_id.
    """

    def __init__(self) -> None:
        self.player_ids: dict[str, int] = {}
        self.picks: dict[tuple[int, str, int], int] = {}

    @classmethod
    def from_league_players(
        cls,
        entries: list[dict],
    ) -> "TradeBlockSnapshot":
        snapshot = cls()

        for entry in entries or []:
            settings = entry.get("settings") or {}
            blocking_roster_id = settings.get("otb")

            if blocking_roster_id is None:
                continue

            raw_id = str(entry.get("player_id", ""))
            pick = _parse_pick_id(raw_id)

            if pick is not None:
                round_, season, og_roster_id = pick
                snapshot.picks[(round_, season, og_roster_id)] = (
                    int(blocking_roster_id)
                )
            elif raw_id.isdigit():
                snapshot.player_ids[raw_id] = int(
                    blocking_roster_id
                )

        return snapshot


def _parse_pick_id(raw_id: str) -> tuple[int, str, int] | None:
    parts = raw_id.split(",")

    if len(parts) != 3:
        return None

    try:
        return (int(parts[0]), parts[1], int(parts[2]))
    except ValueError:
        return None


async def get_trade_block_snapshot(
    ctx: ContextDep,
    league_id: str,
) -> TradeBlockSnapshot:
    cache_key = f"advisor:trade_block:{league_id}"

    if ctx.redis is not None:
        cached = await ctx.redis.get(cache_key)

        if cached:
            return _snapshot_from_json(cached)

    client: SleeperClient = ctx.sleeper
    data = await client.read.get_league_players_status(
        league_id,
    )
    snapshot = TradeBlockSnapshot.from_league_players(data)

    if ctx.redis is not None and (
        snapshot.player_ids or snapshot.picks
    ):
        await ctx.redis.set(
            cache_key,
            _snapshot_to_json(snapshot),
            ttl_seconds=TRADE_BLOCK_CACHE_TTL_SECONDS,
        )

    return snapshot


def _snapshot_to_json(snapshot: TradeBlockSnapshot) -> str:
    return json.dumps(
        {
            "player_ids": snapshot.player_ids,
            "picks": [
                [round_, season, og, roster]
                for (
                    round_,
                    season,
                    og,
                ), roster in snapshot.picks.items()
            ],
        }
    )


def _snapshot_from_json(raw: str) -> TradeBlockSnapshot:
    payload = json.loads(raw)
    snapshot = TradeBlockSnapshot()
    snapshot.player_ids = {
        pid: int(roster)
        for pid, roster in payload.get("player_ids", {}).items()
    }

    for round_, season, og, roster in payload.get("picks", []):
        snapshot.picks[(int(round_), season, int(og))] = int(
            roster
        )

    return snapshot
