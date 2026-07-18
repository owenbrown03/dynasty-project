from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ADPSnapshotRequest:
    season: str
    draft_kind: str
    qb_format: str
    te_premium: str
    team_count: int
    minimum_draft_count: int


def build_default_adp_snapshot_requests(
    *,
    seasons: list[str],
    minimum_draft_count: int,
) -> list[ADPSnapshotRequest]:
    requests: list[ADPSnapshotRequest] = []

    for season in seasons:
        for draft_kind in ("startup", "rookie"):
            for qb_format in ("one_qb", "superflex"):
                for te_premium in ("none", "premium"):
                    for team_count in (10, 12):
                        requests.append(
                            ADPSnapshotRequest(
                                season=season,
                                draft_kind=draft_kind,
                                qb_format=qb_format,
                                te_premium=te_premium,
                                team_count=team_count,
                                minimum_draft_count=minimum_draft_count,
                            )
                        )

    return requests
