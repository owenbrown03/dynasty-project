from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.personal import (
    CommissionerLeagueDues,
    CommissionerLeagueNote,
    FinanceLeagueSeason,
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


async def upsert_finance_entry(
    *,
    db: AsyncSession,
    site_user_id: UUID,
    league_id: str,
    season: str,
    buy_in_amount: float,
    winnings_amount: float,
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
    record.updated_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
