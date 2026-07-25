from app.domain.positions import POSITION_SORT_ORDER


def format_players(player_ids: list[str], player_map: dict[str, dict]) -> list[str]:
    """
    Takes a pre-loaded player map and a list of IDs, filtering and sorting
    them into a position-prioritized text manifest.
    """
    current_roster_dicts = [
        player_map[p_id] for p_id in player_ids 
        if p_id in player_map
    ]
    
    current_roster_dicts.sort(
        key=lambda p: (
            POSITION_SORT_ORDER.get(
                p.get("position"),
                99,
            ),
            p.get(
                "last_name",
                "",
            ),
        )
    )
    
    return [
        f"{p.get('position')} {p.get('first_name')} {p.get('last_name')}" 
        for p in current_roster_dicts
    ]


def format_player_cards(
    player_ids: list[str],
    player_map: dict[str, dict],
) -> list[dict[str, str | None]]:
    """
    Takes a pre-loaded player map and returns a position-sorted
    structured player manifest for UI surfaces that need player IDs.
    """
    current_roster_dicts = [
        player_map[p_id]
        for p_id in player_ids
        if p_id in player_map
    ]

    current_roster_dicts.sort(
        key=lambda p: (
            POSITION_SORT_ORDER.get(
                p.get("position"),
                99,
            ),
            p.get(
                "last_name",
                "",
            ),
        )
    )

    return [
        {
            "player_id": player.get(
                "player_id",
            ),
            "name": " ".join(
                part
                for part in [
                    player.get(
                        "first_name",
                    ),
                    player.get(
                        "last_name",
                    ),
                ]
                if part
            ),
            "position": player.get(
                "position",
            ),
            "team": player.get(
                "team",
            ),
        }
        for player in current_roster_dicts
    ]
