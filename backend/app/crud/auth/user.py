import hashlib
import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.auth import (
    EmailVerificationToken,
    SiteUser,
    UserSession,
)
from app.schemas.auth import Login
from app.crud.auth.session import get_session_by_token
from app.services.draft.projection import (
    normalize_finance_projection_settings,
    normalize_draft_pick_projection_settings,
)
from app.services.values.basis import (
    DEFAULT_VALUE_BASIS,
    ValueBasis,
)
from app.services.values.war_settings import (
    normalize_war_value_settings,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
VALID_THEME_PREFERENCES = {"light", "dark", "system"}
VALID_ACCENT_COLORS = {
    "blue", "green", "purple", "red", "orange", "teal", "pink",
}
VALID_VALUE_PREFERENCES = {
    basis.value
    for basis in ValueBasis
}
EMAIL_VERIFICATION_TTL_HOURS = 48

async def insert_user(
    credentials: Login,
    db: AsyncSession
):
    
    hashed_pw = pwd_context.hash(credentials.password)
    new_user = SiteUser(
        email=credentials.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_credentials(
    credentials: Login, 
    db: AsyncSession
) -> SiteUser:
    
    stmt = select(SiteUser).where(SiteUser.email == credentials.email)
    results = await db.execute(stmt)
    db_user = results.scalar_one_or_none()
    return db_user
    
async def get_user_by_token(
    token: str,
    db: AsyncSession,
) -> SiteUser | None:

    session = await get_session_by_token(
        token,
        db,
    )

    if not session:
        return None

    return await get_user_by_session(
        session,
        db,
    )

async def get_user_by_session(
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser | None:
    
    if not session or not session.site_user_id:
        return None

    return await db.get(
        SiteUser,
        session.site_user_id,
    )


def is_email_verified(
    user: SiteUser | None,
) -> bool:
    return (
        user is not None
        and user.email_verified_at is not None
    )


async def create_email_verification_token(
    *,
    user: SiteUser,
    db: AsyncSession,
) -> tuple[EmailVerificationToken, str]:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8"),
    ).hexdigest()
    now = datetime.utcnow()

    verification = EmailVerificationToken(
        site_user_id=user.id,
        token_hash=token_hash,
        expires_at=(
            now + timedelta(
                hours=EMAIL_VERIFICATION_TTL_HOURS,
            )
        ),
    )

    user.verification_email_sent_at = now

    db.add(verification)
    db.add(user)
    await db.commit()
    await db.refresh(verification)
    await db.refresh(user)
    return verification, raw_token


async def get_email_verification_by_token(
    *,
    token: str,
    db: AsyncSession,
) -> EmailVerificationToken | None:
    token_hash = hashlib.sha256(
        token.encode("utf-8"),
    ).hexdigest()

    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.token_hash == token_hash,
    )
    results = await db.execute(stmt)
    return results.scalar_one_or_none()


async def consume_email_verification(
    *,
    verification: EmailVerificationToken,
    user: SiteUser,
    db: AsyncSession,
) -> SiteUser:
    now = datetime.utcnow()
    verification.consumed_at = now
    user.email_verified_at = now

    db.add(verification)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def get_theme_preference(
    user: SiteUser | None,
) -> str | None:
    if not user:
        return None

    value = (
        (user.settings or {}).get("theme_preference")
    )

    if value in VALID_THEME_PREFERENCES:
        return value

    return "light"


def get_value_preference(
    user: SiteUser | None,
) -> ValueBasis | None:
    if not user:
        return None

    value = (
        (user.settings or {}).get("value_preference")
    )

    if value in VALID_VALUE_PREFERENCES:
        return ValueBasis(value)

    return DEFAULT_VALUE_BASIS


async def set_theme_preference(
    *,
    user: SiteUser,
    theme_preference: str,
    db: AsyncSession,
) -> SiteUser:
    settings = dict(
        user.settings or {}
    )

    settings["theme_preference"] = theme_preference
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def get_accent_color(
    user: SiteUser | None,
) -> str | None:
    if not user:
        return None

    value = (
        (user.settings or {}).get("accent_color")
    )

    if value in VALID_ACCENT_COLORS:
        return value

    return "blue"


async def set_accent_color(
    *,
    user: SiteUser,
    accent_color: str,
    db: AsyncSession,
) -> SiteUser:
    settings = dict(
        user.settings or {}
    )

    settings["accent_color"] = accent_color
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def set_value_preference(
    *,
    user: SiteUser,
    value_preference: ValueBasis,
    db: AsyncSession,
) -> SiteUser:
    settings = dict(
        user.settings or {}
    )

    settings["value_preference"] = value_preference.value
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def get_draft_pick_projection_settings(
    user: SiteUser | None,
) -> dict[str, object]:
    if not user:
        return normalize_draft_pick_projection_settings(
            None,
        )

    return normalize_draft_pick_projection_settings(
        (user.settings or {}).get(
            "draft_pick_projection_settings",
        )
    )


def get_finance_projection_settings(
    user: SiteUser | None,
) -> dict[str, object]:
    if not user:
        return normalize_finance_projection_settings(
            None,
        )

    return normalize_finance_projection_settings(
        (user.settings or {}).get(
            "finance_projection_settings",
        )
    )


def get_war_value_settings(
    user: SiteUser | None,
) -> dict[str, object]:
    if not user:
        return normalize_war_value_settings(
            None,
        )

    return normalize_war_value_settings(
        (user.settings or {}).get(
            "war_value_settings",
        )
    )


async def get_war_value_settings_by_user_id(
    *,
    db: AsyncSession,
    site_user_id,
) -> dict[str, object]:
    if site_user_id is None:
        return normalize_war_value_settings(
            None,
        )

    user = await db.get(
        SiteUser,
        site_user_id,
    )

    return get_war_value_settings(
        user,
    )


async def set_war_value_settings(
    *,
    user: SiteUser,
    war_value_settings: dict[str, object],
    db: AsyncSession,
) -> SiteUser:
    settings = dict(
        user.settings or {}
    )

    settings["war_value_settings"] = (
        normalize_war_value_settings(
            war_value_settings,
        )
    )
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def set_draft_pick_projection_settings(
    *,
    user: SiteUser,
    draft_pick_projection_settings: dict[str, object],
    db: AsyncSession,
) -> SiteUser:
    settings = dict(
        user.settings or {}
    )

    settings["draft_pick_projection_settings"] = (
        normalize_draft_pick_projection_settings(
            draft_pick_projection_settings,
        )
    )
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def set_finance_projection_settings(
    *,
    user: SiteUser,
    finance_projection_settings: dict[str, object],
    db: AsyncSession,
) -> SiteUser:
    settings = dict(
        user.settings or {}
    )

    settings["finance_projection_settings"] = (
        normalize_finance_projection_settings(
            finance_projection_settings,
        )
    )
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def reconcile_session_theme_preference(
    *,
    user: SiteUser,
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser:
    if not session:
        return user

    session_preference = (
        (session.settings or {}).get(
            "theme_preference",
        )
    )

    if session_preference not in VALID_THEME_PREFERENCES:
        return user

    settings = dict(
        user.settings or {}
    )
    settings["theme_preference"] = session_preference
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def reconcile_session_value_preference(
    *,
    user: SiteUser,
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser:
    if not session:
        return user

    session_preference = (
        (session.settings or {}).get(
            "value_preference",
        )
    )

    if session_preference not in VALID_VALUE_PREFERENCES:
        return user

    settings = dict(
        user.settings or {}
    )
    settings["value_preference"] = session_preference
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def reconcile_session_draft_pick_projection_settings(
    *,
    user: SiteUser,
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser:
    if not session:
        return user

    session_settings = (
        (session.settings or {}).get(
            "draft_pick_projection_settings",
        )
    )

    if session_settings is None:
        return user

    settings = dict(
        user.settings or {}
    )
    settings["draft_pick_projection_settings"] = (
        normalize_draft_pick_projection_settings(
            session_settings,
        )
    )
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def reconcile_session_finance_projection_settings(
    *,
    user: SiteUser,
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser:
    if not session:
        return user

    session_settings = (
        (session.settings or {}).get(
            "finance_projection_settings",
        )
    )

    if session_settings is None:
        return user

    settings = dict(
        user.settings or {}
    )
    settings["finance_projection_settings"] = (
        normalize_finance_projection_settings(
            session_settings,
        )
    )
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def reconcile_session_war_value_settings(
    *,
    user: SiteUser,
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser:
    if not session:
        return user

    session_settings = (
        (session.settings or {}).get(
            "war_value_settings",
        )
    )

    if session_settings is None:
        return user

    settings = dict(
        user.settings or {}
    )
    settings["war_value_settings"] = (
        normalize_war_value_settings(
            session_settings,
        )
    )
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def reconcile_session_accent_color(
    *,
    user: SiteUser,
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser:
    if not session:
        return user

    session_color = (
        (session.settings or {}).get(
            "accent_color",
        )
    )

    if session_color not in VALID_ACCENT_COLORS:
        return user

    settings = dict(
        user.settings or {}
    )
    settings["accent_color"] = session_color
    user.settings = settings

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
