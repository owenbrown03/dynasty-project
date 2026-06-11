import asyncio
import random
from typing import Awaitable, TypeVar, Callable

T = TypeVar("T")


async def retry(
    fn: Callable[[], Awaitable[T]],
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
) -> T:
    last_exc = None

    for attempt in range(retries):
        try:
            return await fn()

        except Exception as e:
            last_exc = e

            if attempt == retries - 1:
                raise

            delay = min(max_delay, base_delay * (2 ** attempt))
            delay = delay + random.uniform(0, 0.25 * delay)

            await asyncio.sleep(delay)

    raise last_exc