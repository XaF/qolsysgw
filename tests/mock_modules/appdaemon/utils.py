import asyncio

from functools import wraps


def sync_wrapper(coro):
    @wraps(coro)
    def inner_sync_wrapper(self, *args, **kwargs):
        is_async = None
        try:
            # do this first to get the exception
            # otherwise the coro could be started and never awaited
            asyncio.get_event_loop()
            is_async = True
        except RuntimeError:
            is_async = False

        if is_async is True:
            # don't use create_task. It's python3.7 only
            f = asyncio.ensure_future(coro(self, *args, **kwargs))
        else:
            f = asyncio.run_coroutine_threadsafe(coro(self, *args, **kwargs))

        return f

    return inner_sync_wrapper
