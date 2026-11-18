import atexit
import socket
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Optional
from faultline.breadcrumbs import BreadcrumbBuffer
from faultline.extractors import extract_stack_frames
from faultline.transport import HttpTransport

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class FaultlineClient:
    def __init__(
        self,
        api_key: str,
        endpoint: str = "http://localhost:8000",
        environment: str = "production",
        release: Optional[str] = None,
        max_breadcrumbs: int = 50,
        batch_size: int = 20,
        flush_interval_seconds: float = 0.5,
        compress: bool = True,
        auto_hook: bool = True
    ):
        self.api_key = api_key
        self.endpoint = endpoint
        self.environment = environment
        self.release = release
        self.server_name = socket.gethostname()
        
        self.breadcrumbs = BreadcrumbBuffer(max_breadcrumbs=max_breadcrumbs)
        self.tags: dict[str, str] = {}
        self.user: dict[str, Any] = {}
        
        self.transport = HttpTransport(
            endpoint=endpoint,
            api_key=api_key,
            batch_size=batch_size,
            flush_interval_seconds=flush_interval_seconds,
            compress=compress
        )
        
        # Register atexit flush
        atexit.register(self.close)
        
        # Install global exception hooks if enabled
        if auto_hook:
            self.install_hooks()

    def set_tag(self, key: str, value: str):
        self.tags[key] = str(value)

    def set_user(self, id: Optional[str] = None, email: Optional[str] = None, username: Optional[str] = None):
        if id: self.user["id"] = id
        if email: self.user["email"] = email
        if username: self.user["username"] = username

    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[dict[str, Any]] = None
    ):
        self.breadcrumbs.add(message=message, category=category, level=level, data=data)

    def capture_exception(
        self,
        error: Optional[BaseException] = None,
        tags: Optional[dict[str, str]] = None,
        extra: Optional[dict[str, Any]] = None,
        user: Optional[dict[str, Any]] = None,
        handled: bool = True,
        level: str = "error"
    ):
        """Capture an exception and transmit to Faultline asynchronously."""
        exc_type, exc_val, exc_tb = (None, None, None)
        if error is not None:
            exc_type = type(error)
            exc_val = error
            exc_tb = error.__traceback__
        else:
            exc_type, exc_val, exc_tb = sys.exc_info()

        if exc_val is None:
            return

        type_str = getattr(exc_type, "__name__", "Exception")
        msg_str = str(exc_val)
        frames = extract_stack_frames(exc_tb) if exc_tb else []

        merged_tags = {**self.tags, **(tags or {})}
        merged_user = {**self.user, **(user or {})}

        event = {
            "exception_type": type_str,
            "message": msg_str,
            "stack_trace": frames,
            "environment": self.environment,
            "handled": handled,
            "level": level,
            "release": self.release,
            "server_name": self.server_name,
            "tags": merged_tags,
            "breadcrumbs": self.breadcrumbs.get_all(),
            "user": merged_user,
            "timestamp": utc_now_iso()
        }

        self.transport.send(event)

    def capture_message(
        self,
        message: str,
        level: str = "info",
        tags: Optional[dict[str, str]] = None
    ):
        """Capture a critical log or panic message."""
        merged_tags = {**self.tags, **(tags or {})}
        event = {
            "exception_type": f"LogMessage.{level.upper()}",
            "message": message,
            "stack_trace": [],
            "environment": self.environment,
            "handled": True,
            "level": level,
            "release": self.release,
            "server_name": self.server_name,
            "tags": merged_tags,
            "breadcrumbs": self.breadcrumbs.get_all(),
            "user": self.user,
            "timestamp": utc_now_iso()
        }
        self.transport.send(event)

    def install_hooks(self):
        """Install global exception hooks into sys and threading."""
        orig_sys_hook = sys.excepthook

        def faultline_excepthook(exc_type, exc_val, exc_tb):
            self.capture_exception(error=exc_val, handled=False, level="fatal")
            if orig_sys_hook:
                orig_sys_hook(exc_type, exc_val, exc_tb)

        sys.excepthook = faultline_excepthook

        if hasattr(threading, "excepthook"):
            orig_thread_hook = threading.excepthook

            def faultline_thread_hook(args):
                self.capture_exception(error=args.exc_value, handled=False, level="fatal")
                if orig_thread_hook:
                    orig_thread_hook(args)

            threading.excepthook = faultline_thread_hook

    def close(self):
        self.transport.flush_and_close()
