import asyncio
import time


class TokenBucket:
    def __init__(self, rate: int, per: float):
        self.capacity = rate
        self.tokens = float(rate)
        self.per = per
        self.fill_rate = rate / per

        self.updated = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated
            self.updated = now

            # refill tokens
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.fill_rate
            )

            if self.tokens < 1:
                # compute exact wait time instead of fixed sleep
                deficit = 1 - self.tokens
                wait = deficit / self.fill_rate

                await asyncio.sleep(wait)

                # after waiting, assume 1 token consumed
                self.tokens = max(0.0, self.tokens - 1.0)
                return

            self.tokens -= 1.0