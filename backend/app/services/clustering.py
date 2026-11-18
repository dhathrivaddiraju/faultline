import re
import hashlib
from typing import Any, Union
from backend.app.schemas.event_ingest import StackFrame

# Regex patterns for normalization
MEM_ADDR_PATTERN = re.compile(r"0x[0-9a-fA-F]{4,16}")
UUID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")
TEMP_PATH_PATTERN = re.compile(r"([/\\](?:tmp|temp|AppData[/\\]Local[/\\]Temp)[/\\].*?[/\\])")
VENV_PATTERN = re.compile(r".*?[/\\](?:site-packages|dist-packages)[/\\]")

def normalize_path(path: str) -> str:
    """Normalize file paths by stripping virtualenv/temp prefixes and standardizing slashes."""
    if not path:
        return "<unknown>"
    normalized = path.replace("\\", "/")
    # Remove virtual environment paths
    normalized = VENV_PATTERN.sub("site-packages/", normalized)
    # Remove temp paths
    normalized = TEMP_PATH_PATTERN.sub("<temp>/", normalized)
    # Remove leading home/root structures to preserve only relative app path
    parts = normalized.split("/")
    if len(parts) > 3:
        normalized = "/".join(parts[-3:])
    return normalized

def normalize_string(text: str) -> str:
    """Strip memory addresses, UUIDs, and timestamps from error text or frame lines."""
    if not text:
        return ""
    text = MEM_ADDR_PATTERN.sub("<mem_addr>", text)
    text = UUID_PATTERN.sub("<uuid>", text)
    text = TIMESTAMP_PATTERN.sub("<timestamp>", text)
    return text.strip()

def generate_fingerprint(
    exception_type: str,
    stack_trace: list[Union[StackFrame, dict[str, Any]]],
    message: str = ""
) -> tuple[str, str, str]:
    """
    Generate SHA-256 fingerprint for clustering errors.
    Returns:
        (fingerprint_hash, culprit, title)
    """
    clean_type = exception_type.strip()
    normalized_frames = []
    in_app_frames = []
    
    for frame in stack_trace:
        if isinstance(frame, dict):
            fn = frame.get("filename", "")
            func = frame.get("function", "")
            is_in_app = frame.get("in_app", True)
        else:
            fn = frame.filename
            func = frame.function
            is_in_app = frame.in_app

        norm_file = normalize_path(fn)
        norm_func = normalize_string(func)
        frame_sig = f"{norm_file}:{norm_func}"
        normalized_frames.append(frame_sig)
        
        if is_in_app:
            in_app_frames.append(frame_sig)

    # Use in-app frames if available for higher clustering precision
    cluster_frames = in_app_frames if in_app_frames else normalized_frames
    
    # Culprit determination: the deepest in-app frame, or deepest frame
    culprit = cluster_frames[-1] if cluster_frames else "unknown:unknown"
    
    # Title formatting
    clean_msg = normalize_string(message)
    # Truncate message to avoid huge titles
    short_msg = clean_msg.split("\n")[0][:150] if clean_msg else ""
    title = f"{clean_type}: {short_msg}" if short_msg else clean_type

    # Canonical fingerprint string
    if cluster_frames:
        canonical_str = f"{clean_type}|" + "|".join(cluster_frames)
    else:
        # Fallback to exception type + normalized short message
        canonical_str = f"{clean_type}|{short_msg}"

    fingerprint_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    return fingerprint_hash, culprit, title
