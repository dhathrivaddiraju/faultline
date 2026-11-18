import linecache
import re
import traceback
from typing import Any, Optional

SENSITIVE_KEYS = re.compile(r"(password|secret|token|api_?key|auth|bearer|credit|card|cvv)", re.I)

def sanitize_value(val: Any) -> Any:
    try:
        s = repr(val)
        if len(s) > 200:
            return s[:197] + "..."
        return s
    except Exception:
        return "<unprintable>"

def sanitize_locals(local_vars: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for k, v in local_vars.items():
        if SENSITIVE_KEYS.search(k):
            cleaned[k] = "[REDACTED]"
        else:
            cleaned[k] = sanitize_value(v)
    return cleaned

def extract_stack_frames(tb) -> list[dict[str, Any]]:
    """
    Extract structured stack trace frames from a Python traceback object.
    Includes filename, line number, function, pre/post code context lines, and locals.
    """
    frames = []
    curr = tb
    while curr is not None:
        f = curr.tb_frame
        lineno = curr.tb_lineno
        filename = f.f_code.co_filename
        function = f.f_code.co_name

        # Extract source code lines around the error
        code_context = None
        pre_context = []
        post_context = []

        try:
            linecache.checkcache(filename)
            # Fetch surrounding lines
            for l in range(max(1, lineno - 2), lineno):
                line = linecache.getline(filename, l)
                if line:
                    pre_context.append(line.rstrip())

            target_line = linecache.getline(filename, lineno)
            if target_line:
                code_context = target_line.rstrip()

            for l in range(lineno + 1, lineno + 3):
                line = linecache.getline(filename, l)
                if line:
                    post_context.append(line.rstrip())
        except Exception:
            pass

        # Determine if this frame belongs to user app vs python system libraries
        in_app = not any(p in filename for p in ("site-packages", "dist-packages", "lib/python", "Lib/"))

        frame_data = {
            "filename": filename,
            "lineno": lineno,
            "function": function,
            "code_context": code_context,
            "pre_context": pre_context,
            "post_context": post_context,
            "vars": sanitize_locals(f.f_locals),
            "in_app": in_app
        }
        frames.append(frame_data)
        curr = curr.tb_next

    return frames
