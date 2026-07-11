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
    progress_total: int | None = None,
    progress_offset: int = 0,
    progress_label: str | None = None,
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

                    display_total = progress_total or total
                    display_completed = min(
                        progress_offset + completed,
                        display_total,
                    )

                    rate = (
                        completed / elapsed
                        if elapsed > 0
                        else 0
                    )

                    remaining = max(
                        display_total - display_completed,
                        0,
                    )

                    eta_seconds = (
                        remaining / rate
                        if rate > 0
                        else 0
                    )

                    label = (
                        f":{progress_label}"
                        if progress_label
                        else ""
                    )

                    logger.info(
                        f"[bounded_gather{label}] "
                        f"{display_completed:,}/{display_total:,} "
                        f"({display_completed / display_total:.1%}) | "
                        f"{rate:.1f}/sec | "
                        f"ETA {eta_seconds / 60:.1f}m"
                    )

    return await asyncio.gather(
        *(_wrap(c) for c in coros),
        return_exceptions=True,
    )
