import asyncio
import random
from typing import Callable, Awaitable, TypeVar

import httpx


T = TypeVar("T")


async def retry(
    func: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
) -> T:

    last_exception = None

    for attempt in range(retries):
        try:
            return await func()

        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.HTTPStatusError,
        ) as e:

            last_exception = e

            # Don't retry final attempt
            if attempt == retries - 1:
                raise

            delay = min(
                base_delay * (2 ** attempt),
                max_delay,
            )

            # jitter prevents multiple workers retrying together
            delay += random.uniform(0, 0.25)

            await asyncio.sleep(delay)

    raise last_exception