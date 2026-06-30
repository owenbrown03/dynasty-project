import re
import unicodedata
from rapidfuzz import process, fuzz

SUFFIXES = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b\.?", re.IGNORECASE)

NAME_OVERRIDES: dict[str, str] = {
    "hollywoodbrown": "marquisebrown",
}


def normalize(name: str) -> str:
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = SUFFIXES.sub("", name.lower())
    name = re.sub(r"[^a-z0-9]", "", name)
    return NAME_OVERRIDES.get(name, name)


class SleeperNameIndex:
    """
    Builds normalized name -> sleeper_id lookups from the Sleeper player dict
    (as returned by SleeperRead.get_all_players()).

    Usage:
        index = SleeperNameIndex(sleeper_players)
        sleeper_id = index.match("Justin Jefferson", team="MIN")
    """

    def __init__(self, sleeper_players: dict):
        self.by_name_team: dict[str, str] = {}
        self.by_name: dict[str, str] = {}
        self._all_keys: list[str] = []

        for sleeper_id, player in sleeper_players.items():
            full_name = getattr(player, "full_name", None) or getattr(player, "first_name", "")
            if hasattr(player, "first_name") and hasattr(player, "last_name"):
                full_name = f"{player.first_name} {player.last_name}"
            if not full_name or not full_name.strip():
                continue

            key = normalize(full_name)
            team = (getattr(player, "team", None) or "") or ""

            self.by_name_team[key + team] = sleeper_id
            self.by_name.setdefault(key, sleeper_id)
            self._all_keys.append(key + team)

    def match(
        self,
        name: str,
        team: str = "",
        fuzzy_threshold: float = 88.0,
    ) -> tuple[str | None, str, float | None]:
        """
        Returns (sleeper_id, matched_via, confidence_score).
        matched_via is one of: "exact_team", "exact_name", "fuzzy", None (no match).
        """
        norm = normalize(name)

        if team:
            exact = self.by_name_team.get(norm + team)
            if exact:
                return exact, "exact", 100.0

        exact = self.by_name.get(norm)
        if exact:
            return exact, "exact", 100.0

        # Fuzzy fallback — restrict to same-team candidates if we have a team
        candidates = self._all_keys
        if team:
            same_team = [k for k in self._all_keys if k.endswith(team)]
            if same_team:
                candidates = same_team

        result = process.extractOne(norm, candidates, scorer=fuzz.ratio)
        if result is None:
            return None, "unmatched", None

        best_match, score, _ = result
        if score >= fuzzy_threshold:
            return self.by_name_team.get(best_match) or self.by_name.get(norm), "fuzzy", score

        return None, "unmatched", None