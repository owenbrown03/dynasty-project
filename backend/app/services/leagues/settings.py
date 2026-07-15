from __future__ import annotations

from app.services.leagues.models import LeagueSettingsDetail


def build_settings_badges(league) -> list[str]:
    roster_positions = league.roster_positions or []
    settings = league.settings or {}
    scoring = league.scoring_settings or {}

    starter_count = sum(
        slot not in {"BN", "IR", "TAXI"}
        for slot in roster_positions
    )

    roster_size = len(
        roster_positions,
    )

    badges = [
        "Best Ball" if settings.get("best_ball") == 1 else "Lineup",
        f"{league.total_rosters} Team",
        f"Start {starter_count}",
        f"{roster_size} Roster",
        "SF" if "SUPER_FLEX" in roster_positions else "1QB",
        f"{scoring.get('rec', 0)} PPR",
        f"{scoring.get('pass_td', 4)} PPTD",
    ]

    tep = scoring.get("bonus_rec_te", 0)
    if tep and tep > 0:
        badges.append(f"{tep} TEP")

    return badges


def build_settings_details(league) -> list[LeagueSettingsDetail]:
    settings = league.settings or {}
    scoring = league.scoring_settings or {}
    roster_positions = league.roster_positions or []

    starter_count = sum(
        slot not in {"BN", "IR", "TAXI"}
        for slot in roster_positions
    )

    roster_size = len(
        roster_positions,
    )

    details = [
        ("Season", str(league.season)),
        ("Format", "Superflex" if "SUPER_FLEX" in roster_positions else "1QB"),
        ("Lineup", "Best Ball" if settings.get("best_ball") == 1 else "Managed"),
        ("Teams", str(league.total_rosters)),
        ("Starters", str(starter_count)),
        ("Roster Size", str(roster_size)),
        ("Draft Rounds", str(int(settings.get("draft_rounds", 4) or 4))),
        ("Playoff Teams", str(int(settings.get("playoff_teams", 6) or 6))),
        ("FAAB", str(int(settings.get("waiver_budget", 100) or 100))),
        ("Taxi", str(int(settings.get("taxi_slots", 0) or 0))),
        ("Reserve", str(int(settings.get("reserve_slots", 0) or 0))),
        ("PPR", str(scoring.get("rec", 0) or 0)),
        ("Pass TD", str(scoring.get("pass_td", 4) or 4)),
    ]

    tep = scoring.get("bonus_rec_te", 0)
    if tep and tep > 0:
        details.append(("TE Premium", str(tep)))

    trade_deadline = settings.get("trade_deadline")
    if trade_deadline:
        details.append(("Trade Deadline", str(trade_deadline)))

    return [
        LeagueSettingsDetail(label=label, value=value)
        for label, value in details
    ]
