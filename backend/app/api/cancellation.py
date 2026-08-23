import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import Request

logger = logging.getLogger(__name__)

@asynccontextmanager
async def cancel_on_disconnect(request: Request):
    """
    Context manager that monitors client connection state.
    If the client disconnects before the request handler finishes,
    cancels the calling request handler task to free up resources immediately.

    Cancellation triggered by the disconnect watcher is absorbed so it does
    not surface as an ASGI error; cancellations from any other source are
    re-raised unchanged.
    """
    current_task = asyncio.current_task()
    if not current_task:
        yield
        return

    disconnected = False

    # Watcher task listens for the http.disconnect event.
    async def watch_disconnect():
        nonlocal disconnected
        try:
            while True:
                message = await request.receive()
                if message["type"] == "http.disconnect":
                    logger.info("Client disconnected. Canceling request task.")
                    disconnected = True
                    current_task.cancel()
                    break
        except asyncio.CancelledError:
            # Raised when watch_disconnect itself is cancelled.
            pass
        except Exception as e:
            logger.warning(f"Error in request disconnect watcher: {e}")

    watcher = asyncio.create_task(watch_disconnect())
    try:
        yield
    except asyncio.CancelledError:
        if not disconnected:
            raise
        logger.info(
            "Request handler execution successfully aborted on client disconnect."
        )
    finally:
        watcher.cancel()
        try:
            await watcher
        except asyncio.CancelledError:
            pass
