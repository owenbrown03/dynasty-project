from app.services.adp.snapshots import (
    build_default_adp_snapshot_requests,
)


def test_build_default_adp_snapshot_requests():
    requests = build_default_adp_snapshot_requests(
        seasons=["2026"],
        minimum_draft_count=3,
    )

    assert len(requests) == 16
    assert requests[0].season == "2026"
    assert requests[0].draft_kind == "startup"
    assert requests[0].qb_format == "one_qb"
    assert requests[0].te_premium == "none"
    assert requests[0].team_count == 10
    assert requests[0].minimum_draft_count == 3
    assert requests[-1].draft_kind == "rookie"
    assert requests[-1].qb_format == "superflex"
    assert requests[-1].te_premium == "premium"
    assert requests[-1].team_count == 12
