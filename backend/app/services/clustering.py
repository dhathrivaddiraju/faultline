import hashlib
import re
from typing import Any, Union
from backend.app.schemas.event_ingest import StackFrame

MEM_ADDR_PATTERN = re.compile(r"0x[0-9a-fA-F]{4,16}")
UUID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")
TEMP_PATH_PATTERN = re.compile(r"([/\\](?:tmp|temp|AppData[/\\]Local[/\\]Temp)[/\\].*?[/\\])")
VENV_PATTERN = re.compile(r".*?[/\\](?:site-packages|dist-packages)[/\\]")


def normalize_path(path: str) -> str:
    if not path:
        return "<unknown>"
    normalized = path.replace("\\", "/")
    normalized = VENV_PATTERN.sub("site-packages/", normalized)
    normalized = TEMP_PATH_PATTERN.sub("<temp>/", normalized)
    segments = normalized.split("/")
    if len(segments) > 3:
        normalized = "/".join(segments[-3:])
    return normalized


def normalize_token_string(value: str) -> str:
    if not value:
        return ""
    value = MEM_ADDR_PATTERN.sub("<mem_addr>", value)
    value = UUID_PATTERN.sub("<uuid>", value)
    value = TIMESTAMP_PATTERN.sub("<timestamp>", value)
    return value.strip()


def generate_fingerprint(
    exception_type: str,
    stack_trace: list[Union[StackFrame, dict[str, Any]]],
    message: str = ""
) -> tuple[str, str, str]:
    clean_exception = exception_type.strip()
    normalized_frames: list[str] = []
    in_app_frames: list[str] = []

    for frame in stack_trace:
        if isinstance(frame, dict):
            filename = frame.get("filename", "")
            func_name = frame.get("function", "")
            is_in_app = frame.get("in_app", True)
        else:
            filename = frame.filename
            func_name = frame.function
            is_in_app = frame.in_app

        norm_path = normalize_path(filename)
        norm_func = normalize_token_string(func_name)
        signature = f"{norm_path}:{norm_func}"
        normalized_frames.append(signature)

        if is_in_app:
            in_app_frames.append(signature)

    active_frames = in_app_frames if in_app_frames else normalized_frames
    culprit = active_frames[-1] if active_frames else "unknown:unknown"

    clean_message = normalize_token_string(message)
    truncated_message = clean_message.split("\n")[0][:150] if clean_message else ""
    title = f"{clean_exception}: {truncated_message}" if truncated_message else clean_exception

    if active_frames:
        canonical_target = f"{clean_exception}|" + "|".join(active_frames)
    else:
        canonical_target = f"{clean_exception}|{truncated_message}"

    fingerprint = hashlib.sha256(canonical_target.encode("utf-8")).hexdigest()
    return fingerprint, culprit, title
