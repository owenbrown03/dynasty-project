import asyncio

from app.api.cancellation import cancel_on_disconnect


class _DisconnectingRequest:
    def __init__(self):
        self._notified = False

    async def receive(self):
        if not self._notified:
            self._notified = True
            return {"type": "http.disconnect"}
        await asyncio.sleep(3600)


class _QuietRequest:
    async def receive(self):
        await asyncio.sleep(3600)


def test_disconnect_cancellation_is_absorbed():
    async def handler():
        async with cancel_on_disconnect(_DisconnectingRequest()):
            await asyncio.sleep(5)
            return "done"

    result = asyncio.run(asyncio.wait_for(handler(), timeout=10))

    assert result is None


def test_external_cancellation_still_propagates():
    async def run():
        async def handler():
            async with cancel_on_disconnect(_QuietRequest()):
                await asyncio.sleep(5)
                return "done"

        task = asyncio.create_task(handler())
        await asyncio.sleep(0.05)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            return "cancelled"
        return "completed"

    assert asyncio.run(run()) == "cancelled"


def test_normal_completion_passes_through():
    async def handler():
        async with cancel_on_disconnect(_QuietRequest()):
            return "ok"

    assert asyncio.run(handler()) == "ok"
