from app.models.db.sleeper.api import League
from app.services.adp.classification import (
    AUCTION_DRAFT,
    INCOMPLETE,
    MOCK_DRAFT,
    QUALIFIED,
    UNSUPPORTED_TEAM_COUNT,
    UNKNOWN_FORMAT,
    classify_draft,
)


def _build_dynasty_league(
    *,
    previous_league_id: str | None = None,
    total_rosters: int = 12,
    roster_positions: list[str] | None = None,
    scoring_settings: dict | None = None,
) -> League:
    return League(
        league_id="league-1",
        name="Test League",
        season="2026",
        status="in_season",
        total_rosters=total_rosters,
        draft_id="draft-1",
        previous_league_id=previous_league_id,
        settings={
            "type": 2,
            "draft_rounds": 4,
        },
        scoring_settings=scoring_settings or {
            "rec": 1.0,
            "bonus_rec_te": 1.5,
        },
        roster_positions=roster_positions or [
            "QB",
            "RB",
            "RB",
            "WR",
            "WR",
            "TE",
            "FLEX",
            "SUPER_FLEX",
            "BN",
        ],
    )


def test_classify_startup_superflex_dynasty_draft():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "settings": {"rounds": 30},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 12) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 361)
    ]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(),
    )

    assert result.draft_kind == "startup"
    assert result.league_format == "dynasty"
    assert result.qb_format == "superflex"
    assert result.te_premium == "premium"
    assert result.scoring_format == "ppr"
    assert result.is_complete is True
    assert result.is_qualified is True
    assert result.qualification_code == QUALIFIED


def test_classify_rookie_draft_from_previous_league_link():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "settings": {"rounds": 4},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 12) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 49)
    ]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(previous_league_id="league-0"),
    )

    assert result.draft_kind == "rookie"
    assert result.is_qualified is True


def test_classify_mock_draft_is_excluded():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "status": "mock_draft_complete",
        "settings": {"rounds": 30},
    }
    picks = [{"pick_no": i, "round": 1, "player_id": str(i)} for i in range(1, 13)]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(),
    )

    assert result.is_mock is True
    assert result.is_qualified is False
    assert result.qualification_code == MOCK_DRAFT


def test_classify_auction_draft_is_excluded():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "settings": {"rounds": 20, "type": "auction"},
    }
    picks = [{"pick_no": 1, "round": 1, "player_id": "1", "amount": 17}]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(),
    )

    assert result.is_qualified is False
    assert result.qualification_code == AUCTION_DRAFT


def test_classify_unsupported_team_count_is_excluded():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "settings": {"rounds": 30},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 14) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 481)
    ]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(total_rosters=16),
    )

    assert result.is_qualified is False
    assert result.qualification_code == UNSUPPORTED_TEAM_COUNT


def test_classify_fourteen_team_draft_is_qualified():
    draft = {
        "draft_id": "draft-14",
        "league_id": "league-14",
        "season": "2026",
        "settings": {"rounds": 30},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 14) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 421)
    ]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(total_rosters=14),
    )

    assert result.team_count == 14
    assert result.is_complete is True
    assert result.is_qualified is True
    assert result.qualification_code == QUALIFIED


def test_classify_eight_team_draft_is_qualified():
    draft = {
        "draft_id": "draft-8",
        "league_id": "league-8",
        "season": "2026",
        "settings": {"rounds": 30},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 8) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 241)
    ]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(total_rosters=8),
    )

    assert result.team_count == 8
    assert result.is_complete is True
    assert result.is_qualified is True
    assert result.qualification_code == QUALIFIED


def test_classify_incomplete_draft_is_excluded():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "settings": {"rounds": 4},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 12) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 30)
    ]

    result = classify_draft(
        draft,
        picks,
        _build_dynasty_league(previous_league_id="league-0"),
    )

    assert result.is_complete is False
    assert result.is_qualified is False
    assert result.qualification_code == INCOMPLETE


def test_classify_unknown_format_stays_conservative():
    draft = {
        "draft_id": "draft-1",
        "league_id": "league-1",
        "season": "2026",
        "settings": {"rounds": 5},
    }
    picks = [
        {
            "pick_no": pick_no,
            "round": ((pick_no - 1) // 12) + 1,
            "player_id": str(pick_no),
        }
        for pick_no in range(1, 61)
    ]

    result = classify_draft(
        draft,
        picks,
        League(
            league_id="league-1",
            name="Test",
            season="2026",
            status="pre_draft",
            total_rosters=12,
            draft_id="draft-1",
            settings={},
            scoring_settings={},
            roster_positions=[],
        ),
    )

    assert result.is_qualified is False
    assert result.qualification_code == UNKNOWN_FORMAT
