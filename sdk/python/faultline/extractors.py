import linecache
import re
from typing import Any

SENSITIVE_KEYS = re.compile(r"(password|secret|token|api_?key|auth|bearer|credit|card|cvv)", re.I)


def sanitize_repr(value: Any) -> str:
    try:
        representation = repr(value)
        if len(representation) > 200:
            return representation[:197] + "..."
        return representation
    except Exception:
        return "<unprintable>"


def sanitize_scope_locals(local_variables: dict[str, Any]) -> dict[str, Any]:
    sanitized = {}
    for key, value in local_variables.items():
        if SENSITIVE_KEYS.search(key):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = sanitize_repr(value)
    return sanitized


def extract_stack_frames(traceback_obj) -> list[dict[str, Any]]:
    frames = []
    current_tb = traceback_obj

    while current_tb is not None:
        frame = current_tb.tb_frame
        lineno = current_tb.tb_lineno
        filename = frame.f_code.co_filename
        function_name = frame.f_code.co_name

        code_context = None
        pre_context: list[str] = []
        post_context: list[str] = []

        try:
            linecache.checkcache(filename)
            for line_idx in range(max(1, lineno - 2), lineno):
                line = linecache.getline(filename, line_idx)
                if line:
                    pre_context.append(line.rstrip())

            target_line = linecache.getline(filename, lineno)
            if target_line:
                code_context = target_line.rstrip()

            for line_idx in range(lineno + 1, lineno + 3):
                line = linecache.getline(filename, line_idx)
                if line:
                    post_context.append(line.rstrip())
        except Exception:
            pass

        in_app = not any(
            pattern in filename
            for pattern in ("site-packages", "dist-packages", "lib/python", "Lib/")
        )

        frames.append({
            "filename": filename,
            "lineno": lineno,
            "function": function_name,
            "code_context": code_context,
            "pre_context": pre_context,
            "post_context": post_context,
            "vars": sanitize_scope_locals(frame.f_locals),
            "in_app": in_app
        })
        current_tb = current_tb.tb_next

    return frames
