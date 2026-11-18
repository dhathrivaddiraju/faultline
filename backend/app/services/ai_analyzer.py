import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.config import settings

logger = logging.getLogger("faultline.ai_analyzer")

ANALYSIS_PROMPT = """Analyze the following runtime crash event:

Title: {title}
Exception Type: {exception_type}
Message: {message}
Culprit Frame: {culprit}

Breadcrumbs:
{breadcrumbs}

Stack Trace Frames:
{stack_trace}

Context:
Request: {request_context}
User: {user_context}

Return a JSON object conforming strictly to this structure:
{{
  "hypothesis": "Root cause explanation describing the failure mechanism.",
  "vulnerable_code": "Code snippet where failure originates.",
  "remediation_steps": [
    "Immediate mitigation or defensive validation.",
    "Refactoring or permanent logic correction.",
    "Regression test coverage."
  ],
  "suggested_fix_diff": "Unified diff illustrating the patch.",
  "confidence": 0.95
}}

Return only valid JSON without markdown wrapping."""


def evaluate_heuristics(
    exception_type: str,
    message: str,
    culprit: str,
    stack_trace: list[dict[str, Any]]
) -> dict[str, Any]:
    culprit_file = culprit.split(":")[0] if ":" in culprit else "unknown"
    culprit_func = culprit.split(":")[1] if ":" in culprit else "handler"
    code_snippet = stack_trace[-1].get("code_context") if stack_trace else None
    clean_key = message.strip("'\"")

    if "KeyError" in exception_type:
        hypothesis = (
            f"Missing key in dictionary lookup within {culprit}. "
            f"Upstream payload or record omitted '{clean_key}'."
        )
        vulnerable_code = code_snippet or f"value = payload['{clean_key}']"
        remediation = [
            f"Replace direct indexing with dict.get('{clean_key}', default) in {culprit_file}.",
            "Enforce required fields via payload schema validation at ingress.",
            "Add regression test verifying missing-key input handling."
        ]
        fix_diff = (
            f"- value = payload['{clean_key}']\n"
            f"+ value = payload.get('{clean_key}')\n"
            f"+ if value is None:\n"
            f"+     raise ValueError('Required field {clean_key} missing')"
        )

    elif "ZeroDivisionError" in exception_type:
        hypothesis = (
            f"Division by zero in {culprit}. Denominator evaluated to zero during calculation."
        )
        vulnerable_code = code_snippet or "ratio = numerator / denominator"
        remediation = [
            f"Add non-zero validation for denominator before division in {culprit_file}.",
            "Define fallback value for zero-count edge cases.",
            "Add unit tests for zero and empty input collections."
        ]
        fix_diff = (
            "- ratio = numerator / denominator\n"
            "+ ratio = (numerator / denominator) if denominator != 0 else 0.0"
        )

    elif any(term in exception_type for term in ("NullPointer", "AttributeError")) or "NoneType" in message:
        hypothesis = (
            f"Null reference in {culprit}. Attribute accessed on None instance."
        )
        vulnerable_code = code_snippet or f"result = record.property"
        remediation = [
            f"Verify object existence prior to dereferencing in {culprit_file}.",
            "Handle empty database lookup or missing relationship safely.",
            "Enforce Optional typing annotations across domain entities."
        ]
        fix_diff = (
            "- result = record.property\n"
            "+ if record is None:\n"
            "+     return None\n"
            "+ result = record.property"
        )

    elif any(term in exception_type for term in ("Connection", "Timeout")):
        hypothesis = (
            f"Network transport timeout or connection drop in {culprit}."
        )
        vulnerable_code = code_snippet or "response = client.get(url)"
        remediation = [
            "Set explicit connect and read timeouts on client instances.",
            "Configure retry policy with exponential backoff and jitter.",
            "Introduce circuit breaker pattern for downstream dependency failures."
        ]
        fix_diff = (
            "- response = client.get(url)\n"
            "+ response = client.get(url, timeout=(2.0, 5.0))"
        )

    else:
        hypothesis = (
            f"Unhandled {exception_type} in {culprit}: {message}."
        )
        vulnerable_code = code_snippet or f"raise {exception_type}('{message}')"
        remediation = [
            f"Audit error boundaries and exception propagation in {culprit_file}.",
            "Enclose external invocation in structured exception handlers.",
            "Add end-to-end integration test reproducing the error condition."
        ]
        fix_diff = (
            "- execute_operation()\n"
            "+ try:\n"
            "+     execute_operation()\n"
            f"+ except {exception_type} as exc:\n"
            "+     logger.error(f'Operation failed: {exc}')\n"
            "+     return fallback"
        )

    return {
        "hypothesis": hypothesis,
        "vulnerable_code": vulnerable_code,
        "remediation_steps": remediation,
        "suggested_fix_diff": fix_diff,
        "confidence": 0.94,
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }


async def analyze_incident_with_claude(
    title: str,
    exception_type: str,
    message: str,
    culprit: str,
    stack_trace: list[dict[str, Any]],
    breadcrumbs: list[dict[str, Any]],
    request_context: Optional[dict[str, Any]] = None,
    user_context: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    if not settings.ANTHROPIC_API_KEY:
        return evaluate_heuristics(exception_type, message, culprit, stack_trace)

    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        formatted_frames = []
        for frame in stack_trace[-6:]:
            formatted_frames.append(
                f"File: {frame.get('filename')}, line {frame.get('lineno')}, in {frame.get('function')}\n"
                f"Context: {frame.get('code_context') or 'none'}\n"
                f"Locals: {frame.get('vars') or 'none'}"
            )
        frames_summary = "\n---\n".join(formatted_frames) if formatted_frames else "No frame data."

        formatted_breadcrumbs = []
        for crumb in breadcrumbs[-8:]:
            formatted_breadcrumbs.append(
                f"[{crumb.get('timestamp')}] {crumb.get('category')} ({crumb.get('level')}): {crumb.get('message')}"
            )
        breadcrumbs_summary = "\n".join(formatted_breadcrumbs) if formatted_breadcrumbs else "None"

        prompt = ANALYSIS_PROMPT.format(
            title=title,
            exception_type=exception_type,
            message=message,
            culprit=culprit,
            breadcrumbs=breadcrumbs_summary,
            stack_trace=frames_summary,
            request_context=json.dumps(request_context or {}),
            user_context=json.dumps(user_context or {})
        )

        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        parsed = json.loads(content.strip())
        parsed["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        return parsed

    except Exception as exc:
        logger.error(f"Claude analysis failed: {exc}. Falling back to rule engine.")
        return evaluate_heuristics(exception_type, message, culprit, stack_trace)
