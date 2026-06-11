from app.core.context import Context

CONNECT_TTL_SECONDS = 600

async def store_pending(
    ctx: Context,
    connect_id: str,
    username: str,
):
    await ctx.redis.set(
        f"sleeper_connect:{connect_id}",
        username,
        ttl_seconds=CONNECT_TTL_SECONDS,
    )


async def pop_pending(
    ctx: Context,
    connect_id: str,
) -> str | None:
    key = f"sleeper_connect:{connect_id}"

    username = await ctx.redis.get(key)

    if username:
        await ctx.redis.delete(key)

    return username