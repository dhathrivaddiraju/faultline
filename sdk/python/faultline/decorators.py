import functools
import inspect
from contextlib import contextmanager
from typing import Optional, Callable, Any

_global_client = None

def get_client():
    global _global_client
    return _global_client

def set_client(client):
    global _global_client
    _global_client = client

def capture_exceptions(
    tags: Optional[dict[str, str]] = None,
    reraise: bool = True,
    level: str = "error"
):
    """
    Decorator to wrap functions and automatically capture any unhandled exceptions.
    Usage:
        @capture_exceptions(tags={"service": "billing"})
        def charge_customer(card_id, amount):
            ...
    """
    def decorator(fn: Callable[..., Any]):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                client = get_client()
                try:
                    return await fn(*args, **kwargs)
                except Exception as err:
                    if client:
                        client.capture_exception(err, tags=tags, level=level, handled=False)
                    if reraise:
                        raise
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                client = get_client()
                try:
                    return fn(*args, **kwargs)
                except Exception as err:
                    if client:
                        client.capture_exception(err, tags=tags, level=level, handled=False)
                    if reraise:
                        raise
            return sync_wrapper
    return decorator

@contextmanager
def capture(tags: Optional[dict[str, str]] = None, reraise: bool = True):
    """
    Context manager to safely execute a code block and capture unhandled exceptions.
    Usage:
        with faultline.capture(tags={"action": "checkout"}):
            process_payment()
    """
    client = get_client()
    try:
        yield
    except Exception as err:
        if client:
            client.capture_exception(err, tags=tags, handled=False)
        if reraise:
            raise
