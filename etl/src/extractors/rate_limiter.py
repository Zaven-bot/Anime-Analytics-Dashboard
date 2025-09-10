import asyncio

class JikanRateLimiter:
    """
    Simple rate limiter for Jikan API requests.
    """
    def __init__(self, delay: float = 1.5):
        self.delay = delay
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            await asyncio.sleep(self.delay)
