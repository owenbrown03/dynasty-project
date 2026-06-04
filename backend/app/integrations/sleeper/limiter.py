import asyncio
import time

class TokenBucket:
    def __init__(self, rate: int, per: float):
        self.capacity = rate
        self.tokens = rate
        self.per = per
        self.updated = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated

            # refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * (self.capacity / self.per)
            )
            self.updated = now

            if self.tokens < 1:
                wait = self.per / self.capacity
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1