CORE_FANTASY_POSITIONS = (
    "QB",
    "RB",
    "WR",
    "TE",
)

CORE_FANTASY_POSITION_SET = frozenset(
    CORE_FANTASY_POSITIONS,
)

POSITION_SORT_ORDER = {
    position: index
    for index, position in enumerate(
        (
            *CORE_FANTASY_POSITIONS,
            "K",
            "DEF",
        )
    )
}


def is_core_fantasy_position(
    position: str | None,
) -> bool:
    return position in CORE_FANTASY_POSITION_SET
