import asyncio
import random

async def retry(fn, retries=3):
    for attempt in range(retries):
        try:
            return await fn()

        except Exception as e:
            if attempt == retries - 1:
                raise

            wait = (2 ** attempt) + random.random()
            await asyncio.sleep(wait)