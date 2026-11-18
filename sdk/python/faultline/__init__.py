from typing import Optional, Any
from faultline.client import FaultlineClient
from faultline.decorators import capture_exceptions, capture, set_client, get_client

__version__ = "1.0.0"

def init(
    api_key: str,
    endpoint: str = "http://localhost:8000",
    environment: str = "production",
    release: Optional[str] = None,
    max_breadcrumbs: int = 50,
    batch_size: int = 20,
    flush_interval_seconds: float = 0.5,
    compress: bool = True,
    auto_hook: bool = True
) -> FaultlineClient:
    """
    Initialize the Faultline SDK client.
    Installs global exception hooks and starts background worker thread.
    """
    client = FaultlineClient(
        api_key=api_key,
        endpoint=endpoint,
        environment=environment,
        release=release,
        max_breadcrumbs=max_breadcrumbs,
        batch_size=batch_size,
        flush_interval_seconds=flush_interval_seconds,
        compress=compress,
        auto_hook=auto_hook
    )
    set_client(client)
    return client

def capture_exception(
    error: Optional[BaseException] = None,
    tags: Optional[dict[str, str]] = None,
    extra: Optional[dict[str, Any]] = None,
    user: Optional[dict[str, Any]] = None,
    handled: bool = True,
    level: str = "error"
):
    client = get_client()
    if client:
        client.capture_exception(error=error, tags=tags, extra=extra, user=user, handled=handled, level=level)

def capture_message(
    message: str,
    level: str = "info",
    tags: Optional[dict[str, str]] = None
):
    client = get_client()
    if client:
        client.capture_message(message=message, level=level, tags=tags)

def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[dict[str, Any]] = None
):
    client = get_client()
    if client:
        client.add_breadcrumb(message=message, category=category, level=level, data=data)

def set_tag(key: str, value: str):
    client = get_client()
    if client:
        client.set_tag(key, value)

def set_user(id: Optional[str] = None, email: Optional[str] = None, username: Optional[str] = None):
    client = get_client()
    if client:
        client.set_user(id=id, email=email, username=username)

__all__ = [
    "init",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "set_tag",
    "set_user",
    "capture_exceptions",
    "capture",
    "FaultlineClient",
    "get_client"
]
