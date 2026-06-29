import asyncio
import time


class TokenBucket:
    def __init__(
        self,
        *,
        capacity: int,
        refill_rate: float,
    ):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.updated = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated

            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate,
            )

            self.updated = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)

                self.tokens = 0

            else:
                self.tokens -= 1