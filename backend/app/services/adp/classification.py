from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence


SUPPORTED_TEAM_COUNTS = {8, 10, 12, 14}
QUALIFIED = "qualified"
UNKNOWN_FORMAT = "unknown_format"
UNSUPPORTED_TEAM_COUNT = "unsupported_team_count"
INCOMPLETE = "incomplete"
MISSING_PICKS = "missing_picks"
MISSING_PLAYER_IDS = "missing_player_ids"
MOCK_DRAFT = "mock"
AUCTION_DRAFT = "auction"
KEEPER_DRAFT = "keeper_draft"


@dataclass(frozen=True)
class DraftClassification:
    draft_kind: str
    league_format: str
    qb_format: str
    te_premium: str
    scoring_format: str
    team_count: int | None
    round_count: int | None
    is_mock: bool
    is_complete: bool
    is_qualified: bool
    qualification_code: str
    qualification_details: dict[str, object]

    def model_dump(self) -> dict[str, object]:
        return asdict(self)


def _get_attr(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _get_nested(source: Any, key: str) -> Any:
    value = _get_attr(source, key, None)
    return value or {}


def _coerce_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_datetime(value: Any) -> datetime | None:
    if value in (None, "", 0):
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = None

    if numeric is not None:
        if numeric > 10_000_000_000:
            numeric /= 1000.0
        return datetime.fromtimestamp(numeric, tz=UTC)

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    return None


def _extract_team_count(draft: Any, league: Any | None) -> int | None:
    return (
        _coerce_int(_get_attr(league, "total_rosters"))
        or _coerce_int(_get_nested(draft, "settings").get("teams"))
        or _coerce_int(_get_nested(draft, "settings").get("teams_count"))
        or _coerce_int(_get_nested(draft, "metadata").get("teams"))
    )


def _extract_round_count(
    draft: Any,
    league: Any | None,
    picks: Sequence[Mapping[str, Any]],
) -> int | None:
    return (
        _coerce_int(_get_nested(draft, "settings").get("rounds"))
        or _coerce_int(_get_nested(draft, "metadata").get("rounds"))
        or _coerce_int(_get_nested(league, "settings").get("draft_rounds"))
        or max(
            (
                _coerce_int(pick.get("round"))
                for pick in picks
            ),
            default=None,
        )
    )


def _classify_qb_format(league: Any | None) -> str:
    roster_positions = _get_attr(league, "roster_positions", []) or []

    if any(position in {"SUPER_FLEX", "OP", "SF"} for position in roster_positions):
        return "superflex"

    qb_slots = sum(position == "QB" for position in roster_positions)
    if qb_slots >= 2:
        return "two_qb"
    if qb_slots >= 1:
        return "one_qb"
    return "unknown"


def _classify_te_premium(league: Any | None) -> str:
    scoring = _get_attr(league, "scoring_settings", {}) or {}
    rec = _coerce_float(scoring.get("rec")) or 0.0
    bonus_rec_te = _coerce_float(scoring.get("bonus_rec_te")) or 0.0
    return "premium" if bonus_rec_te > rec else "none"


def _classify_scoring_format(league: Any | None) -> str:
    scoring = _get_attr(league, "scoring_settings", {}) or {}
    rec = _coerce_float(scoring.get("rec"))

    if rec is None:
        return "unknown"
    if rec == 0:
        return "standard"
    if rec == 0.5:
        return "half_ppr"
    if rec == 1:
        return "ppr"
    return "custom"


def _classify_league_format(league: Any | None, draft: Any) -> str:
    if _get_nested(draft, "metadata").get("keeper") or _get_nested(draft, "settings").get("is_keeper"):
        return "keeper"

    league_type = _coerce_int(_get_nested(league, "settings").get("type"))
    if league_type == 2:
        return "dynasty"
    if league_type is not None:
        return "redraft"
    return "unknown"


def _rookie_pick_ratio(picks: Sequence[Mapping[str, Any]], players_by_id: Mapping[str, Any] | None) -> float | None:
    if not picks or not players_by_id:
        return None

    drafted_players = 0
    rookies = 0
    for pick in picks:
        player_id = pick.get("player_id")
        if not player_id:
            continue
        player = players_by_id.get(str(player_id))
        if player is None:
            continue
        years_exp = _coerce_int(_get_attr(player, "years_exp"))
        if years_exp is None:
            continue
        drafted_players += 1
        if years_exp == 0:
            rookies += 1

    if drafted_players == 0:
        return None

    return rookies / drafted_players


def _classify_draft_kind(
    draft: Any,
    league: Any | None,
    picks: Sequence[Mapping[str, Any]],
    players_by_id: Mapping[str, Any] | None,
) -> str:
    metadata = _get_nested(draft, "metadata")
    if metadata.get("supplemental") or metadata.get("type") == "supplemental":
        return "supplemental"

    if _get_attr(league, "previous_league_id"):
        return "rookie"

    round_count = _extract_round_count(draft, league, picks)
    rookie_ratio = _rookie_pick_ratio(picks, players_by_id)

    if round_count is not None and round_count >= 8:
        return "startup"

    if rookie_ratio is not None and rookie_ratio >= 0.75:
        return "rookie"

    if round_count is not None and round_count <= 2:
        return "supplemental"

    return "unknown"


def _is_mock_draft(draft: Any) -> bool:
    metadata = _get_nested(draft, "metadata")
    settings = _get_nested(draft, "settings")
    label_values = [
        str(metadata.get("name") or "").lower(),
        str(metadata.get("description") or "").lower(),
        str(metadata.get("type") or "").lower(),
        str(settings.get("type") or "").lower(),
        str(_get_attr(draft, "status") or "").lower(),
    ]
    return any("mock" in value for value in label_values if value)


def _is_auction_draft(draft: Any, picks: Sequence[Mapping[str, Any]]) -> bool:
    metadata = _get_nested(draft, "metadata")
    settings = _get_nested(draft, "settings")
    draft_type_values = [
        str(metadata.get("type") or "").lower(),
        str(settings.get("type") or "").lower(),
        str(_get_attr(draft, "type") or "").lower(),
    ]
    if any("auction" in value for value in draft_type_values if value):
        return True

    return any(
        (
            pick.get("amount") is not None
            or pick.get("bid_amount") is not None
            or (pick.get("metadata") or {}).get("amount") is not None
        )
        for pick in picks
    )


def classify_draft(
    draft: Mapping[str, Any] | Any,
    picks: Sequence[Mapping[str, Any]],
    league: Mapping[str, Any] | Any | None,
    *,
    players_by_id: Mapping[str, Any] | None = None,
) -> DraftClassification:
    team_count = _extract_team_count(draft, league)
    round_count = _extract_round_count(draft, league, picks)
    expected_picks = (
        team_count * round_count
        if team_count is not None and round_count is not None
        else None
    )
    valid_player_pick_count = sum(1 for pick in picks if pick.get("player_id"))
    actual_pick_count = len(picks)
    completion_ratio = (
        valid_player_pick_count / expected_picks
        if expected_picks
        else 0.0
    )

    is_mock = _is_mock_draft(draft)
    is_auction = _is_auction_draft(draft, picks)
    draft_kind = _classify_draft_kind(
        draft,
        league,
        picks,
        players_by_id,
    )
    league_format = _classify_league_format(league, draft)
    qb_format = _classify_qb_format(league)
    te_premium = _classify_te_premium(league)
    scoring_format = _classify_scoring_format(league)

    is_complete = bool(
        expected_picks
        and actual_pick_count >= int(expected_picks * 0.95)
        and valid_player_pick_count >= int(expected_picks * 0.95)
    )

    qualification_code = QUALIFIED
    is_qualified = True

    if is_mock:
        qualification_code = MOCK_DRAFT
        is_qualified = False
    elif is_auction:
        qualification_code = AUCTION_DRAFT
        is_qualified = False
    elif league_format == "keeper":
        qualification_code = KEEPER_DRAFT
        is_qualified = False
    elif team_count not in SUPPORTED_TEAM_COUNTS:
        qualification_code = UNSUPPORTED_TEAM_COUNT
        is_qualified = False
    elif actual_pick_count == 0:
        qualification_code = MISSING_PICKS
        is_qualified = False
    elif not is_complete:
        qualification_code = INCOMPLETE
        is_qualified = False
    elif completion_ratio < 0.95:
        qualification_code = MISSING_PLAYER_IDS
        is_qualified = False
    elif draft_kind == "unknown" or league_format == "unknown":
        qualification_code = UNKNOWN_FORMAT
        is_qualified = False

    return DraftClassification(
        draft_kind=draft_kind,
        league_format=league_format,
        qb_format=qb_format,
        te_premium=te_premium,
        scoring_format=scoring_format,
        team_count=team_count,
        round_count=round_count,
        is_mock=is_mock,
        is_complete=is_complete,
        is_qualified=is_qualified,
        qualification_code=qualification_code,
        qualification_details={
            "expected_picks": expected_picks,
            "actual_pick_count": actual_pick_count,
            "valid_player_pick_count": valid_player_pick_count,
            "completion_ratio": round(completion_ratio, 4),
            "draft_started_at": (
                _coerce_datetime(
                    _get_attr(draft, "start_time")
                    or _get_nested(draft, "metadata").get("start_time")
                ).isoformat()
                if _coerce_datetime(
                    _get_attr(draft, "start_time")
                    or _get_nested(draft, "metadata").get("start_time")
                )
                else None
            ),
            "draft_completed_at": (
                _coerce_datetime(
                    _get_attr(draft, "last_picked")
                    or _get_attr(draft, "completed_at")
                    or _get_nested(draft, "metadata").get("completed_at")
                ).isoformat()
                if _coerce_datetime(
                    _get_attr(draft, "last_picked")
                    or _get_attr(draft, "completed_at")
                    or _get_nested(draft, "metadata").get("completed_at")
                )
                else None
            ),
        },
    )
