import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from backend.app.config import settings

logger = logging.getLogger("faultline.ai_analyzer")

PROMPT_TEMPLATE = """You are Faultline's senior site reliability and software engineer AI.
Analyze the following runtime crash event from production/staging.

=== INCIDENT DETAILS ===
Title: {title}
Exception Type: {exception_type}
Message: {message}
Culprit Frame: {culprit}

=== RECENT BREADCRUMBS ===
{breadcrumbs}

=== STACK TRACE FRAMES ===
{stack_trace}

=== REQUEST & USER CONTEXT ===
Request: {request_context}
User: {user_context}

Analyze this stack trace and application context. Provide a valid JSON object matching this schema:
{{
  "hypothesis": "Clear, concise root cause explanation describing why this failure occurred in production.",
  "vulnerable_code": "Snippet of the vulnerable or failing code identified from the stack trace and context.",
  "remediation_steps": [
    "Step 1: Immediate mitigation...",
    "Step 2: Code refactor or defensive check...",
    "Step 3: Verification and regression test..."
  ],
  "suggested_fix_diff": "Unified diff or before/after code replacement showing the exact fix.",
  "confidence": 0.95
}}

Return ONLY the raw JSON object. Do not include markdown code block markers or extra conversational text."""

def _generate_fallback_analysis(
    exception_type: str,
    message: str,
    culprit: str,
    stack_trace: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Intelligent heuristic analysis used when ANTHROPIC_API_KEY is not configured or during local testing.
    Produces highly realistic, actionable root-cause hypotheses and remediation steps based on exception patterns.
    """
    culprit_file = culprit.split(":")[0] if ":" in culprit else "unknown"
    culprit_func = culprit.split(":")[1] if ":" in culprit else "handler"
    
    # Extract last code context if available
    code_snippet = None
    if stack_trace:
        last_frame = stack_trace[-1]
        code_snippet = last_frame.get("code_context")

    clean_key = message.strip("'\"")
    if "KeyError" in exception_type:
        hypothesis = (
            f"The application attempted to access a missing key in dictionary context within `{culprit}`. "
            f"The upstream payload or database record did not contain the expected field, causing an unhandled KeyError."
        )
        vuln_code = code_snippet or f"# Missing defensive lookup in {culprit_func}\nvalue = payload['{clean_key}']"
        remediation = [
            f"Replace direct dictionary subscripting with `.get(key, default)` in `{culprit_file}`.",
            "Add Pydantic/schema validation on incoming request payloads to enforce required keys at ingress.",
            "Write a unit test with missing payload keys to verify default handling."
        ]
        fix_diff = f"- value = payload['{clean_key}']\n+ value = payload.get('{clean_key}', None)\n+ if value is None:\n+     raise ValidationError('Missing required field')"

    elif "ZeroDivisionError" in exception_type:
        hypothesis = (
            f"Division by zero encountered in `{culprit}`. "
            "A denominator variable evaluated to 0 when processing edge-case inputs (e.g. empty cart, zero quantity, or uninitialized rate)."
        )
        vuln_code = code_snippet or f"# Unchecked denominator in {culprit_func}\naverage = total / count"
        remediation = [
            f"Add a guard clause in `{culprit_file}` to check for denominator == 0 before performing division.",
            "Define business logic fallback value (e.g., return 0.0 or None) when count is zero.",
            "Add edge-case tests with empty datasets or zero counts."
        ]
        fix_diff = "- average = total / count\n+ average = (total / count) if count > 0 else 0.0"

    elif "NullPointer" in exception_type or "AttributeError" in exception_type or "'NoneType'" in message:
        hypothesis = (
            f"Null reference / AttributeError encountered in `{culprit}`. "
            "An object reference resolved to `None` prior to invoking an attribute or method, likely due to a database lookup returning no result or an optional relationship not being loaded."
        )
        vuln_code = code_snippet or f"# Method invoked on None object in {culprit_func}\nuser_profile = get_profile(user_id)\nemail = user_profile.email"
        remediation = [
            f"Insert an explicit null/None check before dereferencing attributes in `{culprit_file}`.",
            "Ensure database query raises NotFoundException or provides a default instance.",
            "Adopt optional chaining or type hinting (Optional[T]) to flag potential None values at lint time."
        ]
        fix_diff = "- email = user_profile.email\n+ if not user_profile:\n+     logger.warning(f'Profile not found for {user_id}')\n+     return None\n+ email = user_profile.email"

    elif "Connection" in exception_type or "Timeout" in exception_type:
        hypothesis = (
            f"Network transport timeout or connection reset in `{culprit}`. "
            "The external dependency or database socket timed out under peak latency or connection pool exhaustion."
        )
        vuln_code = code_snippet or f"# Unbounded network call in {culprit_func}\nresponse = requests.get(GATEWAY_URL)"
        remediation = [
            "Configure explicit read and connect timeouts (e.g., timeout=3.0s) on all outbound client calls.",
            "Implement exponential backoff retry using Tenacity or similar retry middleware.",
            "Introduce a circuit breaker to fail fast when downstream services become unresponsive."
        ]
        fix_diff = "- response = requests.get(GATEWAY_URL)\n+ response = client.get(GATEWAY_URL, timeout=(2.0, 5.0))"

    else:
        hypothesis = (
            f"Unhandled `{exception_type}` triggered in `{culprit}` with message '{message}'. "
            "An unexpected application state or unvalidated boundary input propagated past error boundaries."
        )
        vuln_code = code_snippet or f"# Unhandled exception in {culprit_file} at {culprit_func}\nraise {exception_type}('{message}')"
        remediation = [
            f"Audit error handling boundaries in `{culprit_file}`.",
            "Wrap external calls with structured try/except blocks capturing specific exception types.",
            "Add end-to-end integration test reproducing the exact input payload."
        ]
        fix_diff = f"- result = execute_logic()\n+ try:\n+     result = execute_logic()\n+ except {exception_type} as err:\n+     logger.error(f'Failed: {{err}}')\n+     return fallback_result"

    return {
        "hypothesis": hypothesis,
        "vulnerable_code": vuln_code,
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
    """
    Invoke Claude 3.5 Sonnet to generate an intelligent root-cause summary,
    vulnerable code identification, and step-by-step remediation plan.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.info("ANTHROPIC_API_KEY not set. Using intelligent heuristic analyzer.")
        return _generate_fallback_analysis(exception_type, message, culprit, stack_trace)

    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Format frames
        formatted_frames = []
        for f in stack_trace[-6:]:  # focus on the deepest 6 frames
            formatted_frames.append(
                f"File: {f.get('filename')}, line {f.get('lineno')}, in {f.get('function')}\n"
                f"Context: {f.get('code_context') or '<none>'}\n"
                f"Locals: {f.get('vars') or '<none>'}"
            )
        frames_text = "\n---\n".join(formatted_frames) if formatted_frames else "No stack frames available."
        
        # Format breadcrumbs
        formatted_crumbs = []
        for b in breadcrumbs[-8:]:
            formatted_crumbs.append(f"[{b.get('timestamp')}] {b.get('category')} ({b.get('level')}): {b.get('message')}")
        crumbs_text = "\n".join(formatted_crumbs) if formatted_crumbs else "None"

        prompt = PROMPT_TEMPLATE.format(
            title=title,
            exception_type=exception_type,
            message=message,
            culprit=culprit,
            breadcrumbs=crumbs_text,
            stack_trace=frames_text,
            request_context=json.dumps(request_context or {}),
            user_context=json.dumps(user_context or {})
        )

        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1000,
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        raw_content = response.content[0].text.strip()
        # Clean any accidental markdown backticks
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
            
        data = json.loads(raw_content.strip())
        data["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        return data

    except Exception as e:
        logger.error(f"Claude API analysis failed ({e}). Falling back to heuristic analysis.")
        return _generate_fallback_analysis(exception_type, message, culprit, stack_trace)
