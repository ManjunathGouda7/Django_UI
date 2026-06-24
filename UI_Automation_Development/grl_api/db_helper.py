from asgiref.sync import async_to_sync

def run_async(coro):
    """
    Safely execute an asynchronous coroutine in a synchronous context.
    Uses Django's async_to_sync to handle running event loops in ASGI/WSGI.
    """
    async def _run():
        return await coro
    return async_to_sync(_run)()
