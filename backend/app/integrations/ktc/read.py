from bs4 import BeautifulSoup
from .transport import KTCTransport
from .schemas import KTCPlayer


# format constants
FORMAT_DYNASTY_SF  = 0
FORMAT_DYNASTY_1QB = 1
FORMAT_REDRAFT_1QB = 1
FORMAT_REDRAFT_SF  = 2


def _parse_player_elements(html_pages: list[str]) -> list[dict]:
    """Parse all onePlayer elements from a list of HTML page strings."""
    elements = []
    for html in html_pages:
        soup = BeautifulSoup(html, "html.parser")
        elements.extend(soup.find_all(class_="onePlayer"))
    return elements


def _extract_team_suffix(player_name: str) -> tuple[str, str, bool]:
    """
    KTC appends team abbr directly to player name in the DOM text.
    Returns (clean_name, team_abbr, is_rookie).
    """
    is_rookie = False
    team = ""

    if player_name.endswith("RFA"):
        team = "RFA"

    elif (
        len(player_name) > 4
        and player_name[-4] == "R"
        and player_name[-3:].isupper()
    ):
        team = player_name[-3:]
        is_rookie = True

    elif player_name.endswith("FA"):
        team = "FA"

    elif player_name[-3:].isupper():
        team = player_name[-3:]

    if is_rookie:
        clean = player_name[:-4].strip()  # remove "R" + 3-letter team
    elif team:
        clean = player_name[:-len(team)].strip()
    else:
        clean = player_name

    return clean, team, is_rookie


def _parse_element(el) -> dict | None:
    name_el  = el.find(class_="player-name")
    pos_el   = el.find(class_="position")
    value_el = el.find(class_="value")
    age_el   = el.find(class_="position hidden-xs")

    if not all([name_el, pos_el, value_el]):
        return None

    raw_name     = name_el.get_text(strip=True)
    pos_rank_str = pos_el.get_text(strip=True)
    position     = pos_rank_str[:2]
    value        = int(value_el.get_text(strip=True))

    clean_name, team, is_rookie = _extract_team_suffix(raw_name)

    age = None
    if age_el:
        age_text = age_el.get_text(strip=True)
        try:
            age = float(age_text[:4])
        except (ValueError, IndexError):
            pass

    return {
        "player_name": clean_name,
        "position": position,
        "position_rank": pos_rank_str,
        "team": team or None,
        "age": age,
        "value": value,
        "is_rookie": is_rookie,
    }


class KTCRead:
    def __init__(self, transport: KTCTransport):
        self.transport = transport

    async def get_dynasty_rankings(self, include_redraft: bool = False) -> list[KTCPlayer]:
        """
        Returns full dynasty player list with both 1QB and SF values.
        Optionally also fetches redraft values.
        """
        config = self.transport.config

        # Fetch 1QB pages first
        pages_1qb = await self.transport.get_all_pages(config.dynasty_path, FORMAT_DYNASTY_1QB)
        elements_1qb = _parse_player_elements(pages_1qb)

        players: dict[str, dict] = {}
        for el in elements_1qb:
            parsed = _parse_element(el)
            if not parsed:
                continue
            players[parsed["player_name"]] = {
                **parsed,
                "sf_value": None,
                "sf_position_rank": None,
                "redraft_value": None,
                "redraft_position_rank": None,
                "sf_redraft_value": None,
                "sf_redraft_position_rank": None,
            }

        # Fetch SF pages and merge
        pages_sf = await self.transport.get_all_pages(config.dynasty_path, FORMAT_DYNASTY_SF)
        elements_sf = _parse_player_elements(pages_sf)

        for el in elements_sf:
            parsed = _parse_element(el)
            if not parsed:
                continue
            name = parsed["player_name"]
            if name in players:
                players[name]["sf_value"] = parsed["value"]
                players[name]["sf_position_rank"] = parsed["position_rank"]
            else:
                # SF-only player (rare edge case)
                players[name] = {
                    **parsed,
                    "value": 0,
                    "sf_value": parsed["value"],
                    "sf_position_rank": parsed["position_rank"],
                    "redraft_value": None,
                    "redraft_position_rank": None,
                    "sf_redraft_value": None,
                    "sf_redraft_position_rank": None,
                }

        if include_redraft:
            await self._merge_redraft_values(players)

        return [KTCPlayer(**p) for p in players.values()]

    async def get_redraft_rankings(self) -> list[KTCPlayer]:
        """Returns redraft-only rankings with both 1QB and SF values."""
        config = self.transport.config

        pages_1qb = await self.transport.get_all_pages(config.redraft_path, FORMAT_REDRAFT_1QB)
        elements  = _parse_player_elements(pages_1qb)

        players: dict[str, dict] = {}
        for el in elements:
            parsed = _parse_element(el)
            if not parsed:
                continue
            players[parsed["player_name"]] = {
                **parsed,
                "sf_value": None,
                "sf_position_rank": None,
                "redraft_value": parsed["value"],
                "redraft_position_rank": parsed["position_rank"],
                "sf_redraft_value": None,
                "sf_redraft_position_rank": None,
            }

        pages_sf = await self.transport.get_all_pages(config.redraft_path, FORMAT_REDRAFT_SF)
        for el in _parse_player_elements(pages_sf):
            parsed = _parse_element(el)
            if not parsed:
                continue
            name = parsed["player_name"]
            if name in players:
                players[name]["sf_redraft_value"] = parsed["value"]
                players[name]["sf_redraft_position_rank"] = parsed["position_rank"]

        return [KTCPlayer(**p) for p in players.values()]

    async def _merge_redraft_values(self, players: dict[str, dict]) -> None:
        config = self.transport.config

        pages_1qb = await self.transport.get_all_pages(config.redraft_path, FORMAT_REDRAFT_1QB)
        for el in _parse_player_elements(pages_1qb):
            parsed = _parse_element(el)
            if parsed and parsed["player_name"] in players:
                players[parsed["player_name"]]["redraft_value"] = parsed["value"]
                players[parsed["player_name"]]["redraft_position_rank"] = parsed["position_rank"]

        pages_sf = await self.transport.get_all_pages(config.redraft_path, FORMAT_REDRAFT_SF)
        for el in _parse_player_elements(pages_sf):
            parsed = _parse_element(el)
            if parsed and parsed["player_name"] in players:
                players[parsed["player_name"]]["sf_redraft_value"] = parsed["value"]
                players[parsed["player_name"]]["sf_redraft_position_rank"] = parsed["position_rank"]
