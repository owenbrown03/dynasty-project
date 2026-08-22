from app.schemas.advisor import AdvisorProposal
from app.schemas.personal_values import (
    PersonalValueMetrics,
    PersonalValuePlayer,
    PersonalValuePoolItem,
)
from app.services.advisor.candidates import (
    _match_package,
    _sum_ktc,
)


def _item(
    player_id: str,
    ktc: float,
    delta: float = 0.0,
) -> PersonalValuePoolItem:
    return PersonalValuePoolItem(
        player=PersonalValuePlayer(
            player_id=player_id,
            name=f"Player {player_id}",
            position="RB",
            ktc_value=ktc,
        ),
        market_values=PersonalValueMetrics(
            dynasty_roster_war=2.0,
        ),
        custom_values=PersonalValueMetrics(
            dynasty_roster_war=2.0 + delta,
        ),
        delta_values=PersonalValueMetrics(
            dynasty_roster_war=delta,
        ),
    )


def test_match_package_prefers_closest_single():
    pool = [
        _item("a", 3000),
        _item("b", 2100),
        _item("c", 2000),
    ]

    package = _match_package(pool, target_ktc=2000)

    assert package is not None
    assert len(package) == 1
    assert package[0].player.player_id in {"b", "c"}


def test_match_package_falls_back_to_pair():
    pool = [
        _item("a", 1200),
        _item("b", 1100),
    ]

    package = _match_package(pool, target_ktc=2300)

    assert package is not None
    assert len(package) == 2


def test_match_package_respects_used_ids():
    pool = [_item("a", 2000)]

    package = _match_package(
        pool,
        target_ktc=2000,
        used_player_ids={"a"},
    )

    assert package is None


def test_match_package_rejects_out_of_band():
    pool = [_item("a", 500)]

    package = _match_package(pool, target_ktc=2000)

    assert package is None


def test_sum_ktc_handles_missing_values():
    total = _sum_ktc([_item("a", 1500), _item("b", None)])

    assert total == 1500


def test_proposal_asymmetry_win_win():
    proposal = AdvisorProposal(
        league_id="l1",
        league_name="League",
        counterparty_id="u2",
        counterparty_name="Other",
        send=[],
        receive=[],
        market_send_total=1000,
        market_receive_total=950,
        personal_send_total=2.0,
        personal_receive_total=3.0,
    )

    assert proposal.asymmetry == "win_win"
    assert proposal.personal_gain() == 1.0


def test_proposal_asymmetry_value_trap():
    proposal = AdvisorProposal(
        league_id="l1",
        league_name="League",
        counterparty_id="u2",
        counterparty_name="Other",
        send=[],
        receive=[],
        market_send_total=1000,
        market_receive_total=600,
        personal_send_total=2.0,
        personal_receive_total=3.0,
    )

    assert proposal.asymmetry == "value_trap"


def test_proposal_asymmetry_none_without_totals():
    proposal = AdvisorProposal(
        league_id="l1",
        league_name="League",
        counterparty_id="u2",
        counterparty_name="Other",
        send=[],
        receive=[],
    )

    assert proposal.asymmetry is None
