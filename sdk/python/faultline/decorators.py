import functools
import inspect
from contextlib import contextmanager
from typing import Optional, Callable, Any

_global_client = None


def get_client():
    global _global_client
    return _global_client


def set_client(client) -> None:
    global _global_client
    _global_client = client


def capture_exceptions(
    tags: Optional[dict[str, str]] = None,
    reraise: bool = True,
    level: str = "error"
):
    def decorator(fn: Callable[..., Any]):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                client = get_client()
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    if client:
                        client.capture_exception(exc, tags=tags, level=level, handled=False)
                    if reraise:
                        raise
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                client = get_client()
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if client:
                        client.capture_exception(exc, tags=tags, level=level, handled=False)
                    if reraise:
                        raise
            return sync_wrapper
    return decorator


@contextmanager
def capture(tags: Optional[dict[str, str]] = None, reraise: bool = True):
    client = get_client()
    try:
        yield
    except Exception as exc:
        if client:
            client.capture_exception(exc, tags=tags, handled=False)
        if reraise:
            raise
