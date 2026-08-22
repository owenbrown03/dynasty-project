import logging

from app.core.broker import broker
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.infrastructure.redis.client import RedisClient

logger = logging.getLogger(__name__)


@broker.task
async def generate_advisor_digest_task(username: str):
    from redis.asyncio import Redis
    from starlette.responses import Response as StarletteResponse

    from app.api.deps import Context
    from app.crud.sleeper.advisor import (
        get_site_user_connection_by_sleeper_user_id,
    )
    from app.crud.sleeper.user import get_userid_by_username
    from app.integrations.gemini.factory import (
        get_gemini_client,
    )
    from app.integrations.sleeper.singleton import (
        get_worker_sleeper_client,
    )
    from app.services.advisor.digest import (
        generate_and_persist_digest,
    )

    redis_conn = Redis.from_url(settings.REDIS_URL)
    redis = RedisClient(redis=redis_conn)

    try:
        async with AsyncSessionLocal() as db:
            sleeper = await get_worker_sleeper_client()
            gemini = await get_gemini_client()

            main_user_id = await get_userid_by_username(
                db,
                sleeper,
                username,
            )

            row = await get_site_user_connection_by_sleeper_user_id(
                db,
                sleeper_user_id=main_user_id,
            )

            if row is None:
                logger.info(
                    "Digest skipped: no linked site user user=%s",
                    username,
                )
                return {"status": "skipped", "reason": "no_site_user"}

            site_user, connection = row

            ctx = Context(
                response=StarletteResponse(),
                db=db,
                session=None,
                site_user=site_user,
                connection=connection,
                sleeper=sleeper,
                underdog=None,
                ktc=None,
                fc=None,
                gemini=gemini,
                redis=redis,
            )

            report = await generate_and_persist_digest(
                ctx=ctx,
                username=username,
            )

            logger.info(
                "Digest generated report_id=%s user=%s",
                report.id if report else None,
                username,
            )

            return {
                "status": "generated",
                "report_id": report.id if report else None,
            }
    finally:
        await redis_conn.aclose()
