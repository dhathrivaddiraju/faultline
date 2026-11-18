import collections
from datetime import datetime, timezone
from typing import Optional, Any

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class BreadcrumbBuffer:
    """Thread-safe ring buffer storing recent breadcrumbs leading up to an error."""
    def __init__(self, max_breadcrumbs: int = 50):
        self.max_breadcrumbs = max_breadcrumbs
        self._buffer = collections.deque(maxlen=max_breadcrumbs)

    def add(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        crumb = {
            "timestamp": timestamp or utc_now_iso(),
            "category": category,
            "message": message,
            "level": level,
            "data": data or {}
        }
        self._buffer.append(crumb)

    def get_all(self) -> list[dict[str, Any]]:
        return list(self._buffer)

    def clear(self):
        self._buffer.clear()
