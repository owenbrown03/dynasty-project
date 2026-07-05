import asyncio
import logging
import time
from typing import Awaitable, Iterable, List, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def bounded_gather(
    coros: Iterable[Awaitable[T]],
    limit: int = 100,
    log_every: int = 10,
) -> List[T]:
    semaphore = asyncio.Semaphore(limit)

    coros = list(coros)
    total = len(coros)

    if total == 0:
        return []

    completed = 0
    started = time.monotonic()

    async def _wrap(coro: Awaitable[T]):
        nonlocal completed

        async with semaphore:
            try:
                return await coro

            finally:
                completed += 1

                if completed % log_every == 0 or completed == total:
                    elapsed = time.monotonic() - started

                    rate = (
                        completed / elapsed
                        if elapsed > 0
                        else 0
                    )

                    remaining = total - completed

                    eta_seconds = (
                        remaining / rate
                        if rate > 0
                        else 0
                    )

                    logger.info(
                        "[bounded_gather] "
                        f"{completed:,}/{total:,} "
                        f"({completed / total:.1%}) | "
                        f"{rate:.1f}/sec | "
                        f"ETA {eta_seconds / 60:.1f}m"
                    )

    return await asyncio.gather(
        *(_wrap(c) for c in coros),
        return_exceptions=True,
    )