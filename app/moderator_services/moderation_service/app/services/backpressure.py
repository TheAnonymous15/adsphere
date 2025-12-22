class BackpressureError(Exception):
    pass


class BackpressureGuard:
    def __init__(self, queue, pressure_limit):
        self.queue = queue
        self.limit = pressure_limit

    async def check(self):
        qsize = await self.queue.size()
        if qsize > self.limit:
            raise BackpressureError(f"Queue overflow ({qsize}/{self.limit})")
