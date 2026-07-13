from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.personal import (
    CommissionerLeagueDues,
    CommissionerLeagueNote,
    FinanceLeagueDefault,
    FinanceLeagueSeason,
    FinanceUserDefaults,
    HiddenLeague,
    PersonalProjection,
    PersonalProjectionOutcome,
    PersonalRankCurve,
    Reminder,
)


async def get_commissioner_notes_by_league_id(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_ids: list[str],
) -> dict[str, CommissionerLeagueNote]:
    if not league_ids:
        return {}

    results = await db.execute(
        select(CommissionerLeagueNote).where(
            CommissionerLeagueNote.site_user_id == site_user_id,
            CommissionerLeagueNote.league_id.in_(league_ids),
        )
    )

    notes = results.scalars().all()
    return {
        note.league_id: note
        for note in notes
    }


async def upsert_commissioner_note(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
    note: str,
) -> CommissionerLeagueNote:
    results = await db.execute(
        select(CommissionerLeagueNote).where(
            CommissionerLeagueNote.site_user_id == site_user_id,
            CommissionerLeagueNote.league_id == league_id,
        )
    )
    record = results.scalar_one_or_none()

    if record is None:
        record = CommissionerLeagueNote(
            site_user_id=site_user_id,
            league_id=league_id,
            note=note,
        )
    else:
        record.note = note
        record.updated_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def upsert_commissioner_settings(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
    paid_years_ahead: int,
) -> CommissionerLeagueNote:
    results = await db.execute(
        select(CommissionerLeagueNote).where(
            CommissionerLeagueNote.site_user_id == site_user_id,
            CommissionerLeagueNote.league_id == league_id,
        )
    )
    record = results.scalar_one_or_none()

    if record is None:
        record = CommissionerLeagueNote(
            site_user_id=site_user_id,
            league_id=league_id,
            note="",
        )

    record.paid_years_ahead = paid_years_ahead
    record.updated_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_commissioner_dues_by_key(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_ids: list[str],
) -> dict[tuple[str, int, str], CommissionerLeagueDues]:
    if not league_ids:
        return {}

    results = await db.execute(
        select(CommissionerLeagueDues).where(
            CommissionerLeagueDues.site_user_id == site_user_id,
            CommissionerLeagueDues.league_id.in_(league_ids),
        )
    )
    dues_rows = results.scalars().all()
    return {
        (
            row.league_id,
            row.roster_id,
            row.season,
        ): row
        for row in dues_rows
    }


async def upsert_commissioner_dues(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
    roster_id: int,
    season: str,
    buy_in_amount: float | None,
    is_paid: bool,
) -> CommissionerLeagueDues:
    results = await db.execute(
        select(CommissionerLeagueDues).where(
            CommissionerLeagueDues.site_user_id == site_user_id,
            CommissionerLeagueDues.league_id == league_id,
            CommissionerLeagueDues.roster_id == roster_id,
            CommissionerLeagueDues.season == season,
        )
    )
    record = results.scalar_one_or_none()
    now = datetime.utcnow()

    if record is None:
        record = CommissionerLeagueDues(
            site_user_id=site_user_id,
            league_id=league_id,
            roster_id=roster_id,
            season=season,
        )

    record.buy_in_amount = buy_in_amount
    record.is_paid = is_paid
    record.paid_at = now if is_paid else None
    record.updated_at = now

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_finance_entries_by_key(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_ids: list[str],
) -> dict[tuple[str, str], FinanceLeagueSeason]:
    if not league_ids:
        return {}

    results = await db.execute(
        select(FinanceLeagueSeason).where(
            FinanceLeagueSeason.site_user_id == site_user_id,
            FinanceLeagueSeason.league_id.in_(league_ids),
        )
    )
    rows = results.scalars().all()

    return {
        (row.league_id, row.season): row
        for row in rows
    }


async def delete_finance_entry(
    *,
    db: AsyncSession,
    finance_entry: FinanceLeagueSeason,
) -> None:
    await db.delete(finance_entry)
    await db.commit()


async def get_finance_user_defaults(
    *,
    db: AsyncSession,
    site_user_id: UUID,
) -> FinanceUserDefaults | None:
    results = await db.execute(
        select(FinanceUserDefaults).where(
            FinanceUserDefaults.site_user_id == site_user_id,
        )
    )
    return results.scalar_one_or_none()


async def upsert_finance_user_defaults(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    buy_in_amount: float | None,
    payout_structure: dict[str, float] | None,
) -> FinanceUserDefaults:
    record = await get_finance_user_defaults(
        db=db,
        site_user_id=site_user_id,
    )

    if record is None:
        record = FinanceUserDefaults(
            site_user_id=site_user_id,
        )

    record.buy_in_amount = buy_in_amount
    record.payout_structure = payout_structure
    record.updated_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_finance_league_defaults_by_family_id(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_family_ids: list[str],
) -> dict[str, FinanceLeagueDefault]:
    if not league_family_ids:
        return {}

    results = await db.execute(
        select(FinanceLeagueDefault).where(
            FinanceLeagueDefault.site_user_id == site_user_id,
            FinanceLeagueDefault.league_family_id.in_(league_family_ids),
        )
    )
    rows = results.scalars().all()
    return {
        row.league_family_id: row
        for row in rows
    }


async def get_hidden_league_ids(
    *,
    db: AsyncSession,
    site_user_id: UUID,
) -> set[str]:
    results = await db.execute(
        select(HiddenLeague.league_id).where(
            HiddenLeague.site_user_id == site_user_id,
        )
    )
    return set(results.scalars().all())


async def get_hidden_league(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
) -> HiddenLeague | None:
    results = await db.execute(
        select(HiddenLeague).where(
            HiddenLeague.site_user_id == site_user_id,
            HiddenLeague.league_id == league_id,
        )
    )
    return results.scalar_one_or_none()


async def get_personal_projections_for_player(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    player_id: str,
) -> list[PersonalProjection]:
    results = await db.execute(
        select(PersonalProjection).where(
            PersonalProjection.site_user_id == site_user_id,
            PersonalProjection.player_id == player_id,
        )
    )
    return list(results.scalars().all())


async def get_personal_projections_for_site_user(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    player_ids: list[str] | None = None,
    seasons: list[int] | None = None,
) -> list[PersonalProjection]:
    statement = select(PersonalProjection).where(
        PersonalProjection.site_user_id == site_user_id,
    )

    if player_ids:
        statement = statement.where(
            PersonalProjection.player_id.in_(player_ids),
        )

    if seasons:
        statement = statement.where(
            PersonalProjection.season.in_(seasons),
        )

    results = await db.execute(statement)
    return list(results.scalars().all())


async def get_personal_projection_outcomes(
    *,
    db: AsyncSession,
    projection_ids: list[int],
) -> dict[int, list[PersonalProjectionOutcome]]:
    if not projection_ids:
        return {}

    results = await db.execute(
        select(PersonalProjectionOutcome).where(
            PersonalProjectionOutcome.projection_id.in_(
                projection_ids,
            )
        )
    )
    rows = list(results.scalars().all())
    output: dict[int, list[PersonalProjectionOutcome]] = {}

    for row in rows:
        output.setdefault(
            row.projection_id,
            [],
        ).append(row)

    for items in output.values():
        items.sort(
            key=lambda item: item.outcome_index,
        )

    return output


async def get_personal_projection_by_key(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    player_id: str,
    season: int,
) -> PersonalProjection | None:
    results = await db.execute(
        select(PersonalProjection).where(
            PersonalProjection.site_user_id == site_user_id,
            PersonalProjection.player_id == player_id,
            PersonalProjection.season == season,
        )
    )
    return results.scalar_one_or_none()


async def replace_personal_projection_outcomes(
    *,
    db: AsyncSession,
    projection_id: int,
    outcomes: list[tuple[int, float]],
) -> list[PersonalProjectionOutcome]:
    existing = await db.execute(
        select(PersonalProjectionOutcome).where(
            PersonalProjectionOutcome.projection_id == projection_id,
        )
    )

    for row in existing.scalars().all():
        await db.delete(row)

    await db.flush()

    new_rows: list[PersonalProjectionOutcome] = []

    for index, (position_rank, probability) in enumerate(
        outcomes,
    ):
        row = PersonalProjectionOutcome(
            projection_id=projection_id,
            outcome_index=index,
            position_rank=position_rank,
            probability=probability,
        )
        db.add(row)
        new_rows.append(row)

    await db.flush()
    return new_rows


async def upsert_personal_projection(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    player_id: str,
    season: int,
    position: str,
    default_source: str,
    is_customized: bool,
    outcomes: list[tuple[int, float]],
) -> PersonalProjection:
    record = await get_personal_projection_by_key(
        db=db,
        site_user_id=site_user_id,
        player_id=player_id,
        season=season,
    )

    now = datetime.utcnow()

    if record is None:
        record = PersonalProjection(
            site_user_id=site_user_id,
            player_id=player_id,
            season=season,
            position=position,
            default_source=default_source,
            is_customized=is_customized,
            created_at=now,
            updated_at=now,
        )
        db.add(record)
        await db.flush()
    else:
        record.position = position
        record.default_source = default_source
        record.is_customized = is_customized
        record.updated_at = now
        db.add(record)
        await db.flush()

    await replace_personal_projection_outcomes(
        db=db,
        projection_id=record.id,
        outcomes=outcomes,
    )

    await db.commit()
    await db.refresh(record)
    return record


async def get_personal_rank_curve_rows(
    *,
    db: AsyncSession,
    settings_fingerprint: str,
    curve_version: str,
) -> list[PersonalRankCurve]:
    results = await db.execute(
        select(PersonalRankCurve).where(
            PersonalRankCurve.settings_fingerprint == settings_fingerprint,
            PersonalRankCurve.curve_version == curve_version,
        )
    )
    return list(results.scalars().all())


async def replace_personal_rank_curve_rows(
    *,
    db: AsyncSession,
    settings_fingerprint: str,
    curve_version: str,
    rows: list[PersonalRankCurve],
) -> list[PersonalRankCurve]:
    existing = await db.execute(
        select(PersonalRankCurve).where(
            PersonalRankCurve.settings_fingerprint == settings_fingerprint,
            PersonalRankCurve.curve_version == curve_version,
        )
    )

    for row in existing.scalars().all():
        await db.delete(row)

    for row in rows:
        db.add(row)

    await db.commit()
    return rows


async def hide_league(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
) -> HiddenLeague:
    record = await get_hidden_league(
        db=db,
        site_user_id=site_user_id,
        league_id=league_id,
    )

    if record is None:
        record = HiddenLeague(
            site_user_id=site_user_id,
            league_id=league_id,
        )

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def unhide_league(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
) -> None:
    record = await get_hidden_league(
        db=db,
        site_user_id=site_user_id,
        league_id=league_id,
    )

    if record is None:
        return

    await db.delete(record)
    await db.commit()


async def upsert_finance_league_default(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_family_id: str,
    buy_in_amount: float | None,
    payout_structure: dict[str, float] | None,
) -> FinanceLeagueDefault:
    results = await db.execute(
        select(FinanceLeagueDefault).where(
            FinanceLeagueDefault.site_user_id == site_user_id,
            FinanceLeagueDefault.league_family_id == league_family_id,
        )
    )
    record = results.scalar_one_or_none()

    if record is None:
        record = FinanceLeagueDefault(
            site_user_id=site_user_id,
            league_family_id=league_family_id,
        )

    record.buy_in_amount = buy_in_amount
    record.payout_structure = payout_structure
    record.updated_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def upsert_finance_entry(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
    season: str,
    buy_in_amount: float,
    winnings_amount: float,
    payout_structure: dict[str, float],
    is_excluded: bool,
) -> FinanceLeagueSeason:
    results = await db.execute(
        select(FinanceLeagueSeason).where(
            FinanceLeagueSeason.site_user_id == site_user_id,
            FinanceLeagueSeason.league_id == league_id,
            FinanceLeagueSeason.season == season,
        )
    )
    record = results.scalar_one_or_none()

    if record is None:
        record = FinanceLeagueSeason(
            site_user_id=site_user_id,
            league_id=league_id,
            season=season,
        )

    record.buy_in_amount = buy_in_amount
    record.winnings_amount = winnings_amount
    record.payout_structure = payout_structure
    record.is_excluded = is_excluded
    record.updated_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_reminders_by_user(
    *,
    db: AsyncSession,
    site_user_id: UUID,
) -> list[Reminder]:
    results = await db.execute(
        select(Reminder).where(
            Reminder.site_user_id == site_user_id,
        ).order_by(
            Reminder.completed,
            Reminder.due_season,
            Reminder.due_week,
            Reminder.updated_at.desc(),
        )
    )
    return list(results.scalars().all())


async def insert_reminder(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str | None,
    title: str,
    note: str,
    due_week: int | None,
    due_season: str | None,
    delivery_channel: str,
) -> Reminder:
    reminder = Reminder(
        site_user_id=site_user_id,
        league_id=league_id,
        title=title,
        note=note,
        due_week=due_week,
        due_season=due_season,
        delivery_channel=delivery_channel,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


async def update_reminder(
    *,
    db: AsyncSession,
    reminder: Reminder,
    title: str,
    note: str,
    due_week: int | None,
    due_season: str | None,
    delivery_channel: str,
    completed: bool,
) -> Reminder:
    reminder.title = title
    reminder.note = note
    reminder.due_week = due_week
    reminder.due_season = due_season
    reminder.delivery_channel = delivery_channel
    reminder.completed = completed
    reminder.updated_at = datetime.utcnow()

    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


async def get_reminder_by_id(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    reminder_id: int,
) -> Reminder | None:
    results = await db.execute(
        select(Reminder).where(
            Reminder.site_user_id == site_user_id,
            Reminder.id == reminder_id,
        )
    )
    return results.scalar_one_or_none()


async def mark_reminder_email_sent(
    *,
    db: AsyncSession,
    reminder: Reminder,
) -> Reminder:
    reminder.email_sent_at = datetime.utcnow()
    reminder.updated_at = datetime.utcnow()
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


async def delete_reminder(
    *,
    db: AsyncSession,
    reminder: Reminder,
) -> None:
    await db.delete(reminder)
    await db.commit()
