import secrets, os, uuid
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.models.db.auth import UserSession
from app.services.draft.projection import (
    normalize_finance_projection_settings,
    normalize_draft_pick_projection_settings,
)
from app.services.values.basis import ValueBasis
from app.services.values.war_settings import (
    normalize_war_value_settings,
)

VALID_THEME_PREFERENCES = {"light", "dark", "system"}
VALID_ACCENT_COLORS = {
    "blue", "green", "purple", "red", "orange", "teal", "pink",
}
VALID_VALUE_PREFERENCES = {
    basis.value
    for basis in ValueBasis
}

async def create_session_by_userid(
    user_id: uuid.UUID, 
    response: Response, 
    db: AsyncSession
):

    token = secrets.token_hex(32)
    new_session = UserSession(
        session_token=token,
        site_user_id=user_id,
    )
    db.add(new_session)
    await db.commit()
    is_prod = os.getenv("ENVIRONMENT") == "production"
    response.set_cookie(
        key="session_token", 
        value=token, 
        httponly=True, 
        secure=is_prod,
        samesite="lax",
        domain=None,
    )
    return new_session

async def insert_session_by_userid(
    site_user_id: uuid.UUID, 
    session: UserSession, 
    db: AsyncSession
):
    session.site_user_id = site_user_id
    await db.commit()
    await db.refresh(session)
    return session


def get_session_theme_preference(
    session: UserSession | None,
) -> str | None:
    if not session:
        return None

    value = (
        (session.settings or {}).get(
            "theme_preference",
        )
    )

    if value in VALID_THEME_PREFERENCES:
        return value

    return None


def get_session_value_preference(
    session: UserSession | None,
) -> ValueBasis | None:
    if not session:
        return None

    value = (
        (session.settings or {}).get(
            "value_preference",
        )
    )

    if value in VALID_VALUE_PREFERENCES:
        return ValueBasis(value)

    return None


async def set_session_theme_preference(
    *,
    session: UserSession,
    theme_preference: str,
    db: AsyncSession,
) -> UserSession:
    settings = dict(
        session.settings or {}
    )

    settings["theme_preference"] = theme_preference
    session.settings = settings

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


def get_session_accent_color(
    session: UserSession | None,
) -> str | None:
    if not session:
        return None

    value = (
        (session.settings or {}).get(
            "accent_color",
        )
    )

    if value in VALID_ACCENT_COLORS:
        return value

    return None


async def set_session_accent_color(
    *,
    session: UserSession,
    accent_color: str,
    db: AsyncSession,
) -> UserSession:
    settings = dict(
        session.settings or {}
    )

    settings["accent_color"] = accent_color
    session.settings = settings

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def set_session_value_preference(
    *,
    session: UserSession,
    value_preference: ValueBasis,
    db: AsyncSession,
) -> UserSession:
    settings = dict(
        session.settings or {}
    )

    settings["value_preference"] = value_preference.value
    session.settings = settings

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


def get_session_draft_pick_projection_settings(
    session: UserSession | None,
) -> dict[str, object]:
    if not session:
        return normalize_draft_pick_projection_settings(
            None,
        )

    return normalize_draft_pick_projection_settings(
        (session.settings or {}).get(
            "draft_pick_projection_settings",
        )
    )


def get_session_finance_projection_settings(
    session: UserSession | None,
) -> dict[str, object]:
    if not session:
        return normalize_finance_projection_settings(
            None,
        )

    return normalize_finance_projection_settings(
        (session.settings or {}).get(
            "finance_projection_settings",
        )
    )


def get_session_war_value_settings(
    session: UserSession | None,
) -> dict[str, object]:
    if not session:
        return normalize_war_value_settings(
            None,
        )

    return normalize_war_value_settings(
        (session.settings or {}).get(
            "war_value_settings",
        )
    )


async def set_session_war_value_settings(
    *,
    session: UserSession,
    war_value_settings: dict[str, object],
    db: AsyncSession,
) -> UserSession:
    settings = dict(
        session.settings or {}
    )

    settings["war_value_settings"] = (
        normalize_war_value_settings(
            war_value_settings,
        )
    )
    session.settings = settings

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def set_session_draft_pick_projection_settings(
    *,
    session: UserSession,
    draft_pick_projection_settings: dict[str, object],
    db: AsyncSession,
) -> UserSession:
    settings = dict(
        session.settings or {}
    )

    settings["draft_pick_projection_settings"] = (
        normalize_draft_pick_projection_settings(
            draft_pick_projection_settings,
        )
    )
    session.settings = settings

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def set_session_finance_projection_settings(
    *,
    session: UserSession,
    finance_projection_settings: dict[str, object],
    db: AsyncSession,
) -> UserSession:
    settings = dict(
        session.settings or {}
    )

    settings["finance_projection_settings"] = (
        normalize_finance_projection_settings(
            finance_projection_settings,
        )
    )
    session.settings = settings

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def delete_session(
    session: UserSession,
    response: Response,
    db: AsyncSession,
):
    await db.execute(
        delete(UserSession).where(UserSession.id == session.id)
    )

    await db.commit()

    is_prod = os.getenv("ENVIRONMENT") == "production"
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=is_prod,
        samesite="lax",
        domain=None,
    )

    return {"status": "logged_out"}

async def get_session_by_token(
    token: str, 
    db: AsyncSession
) -> UserSession | None:
    
    stmt = select(UserSession).where(
        UserSession.session_token == token
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
