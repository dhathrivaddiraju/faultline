import pytest
from backend.app.services.ai_analyzer import analyze_incident_with_claude

@pytest.mark.asyncio
async def test_ai_analyzer_hypothesis_and_remediation():
    result = await analyze_incident_with_claude(
        title="KeyError: 'customer_id'",
        exception_type="KeyError",
        message="'customer_id'",
        culprit="services/billing.py:process_payment",
        stack_trace=[{
            "filename": "services/billing.py",
            "lineno": 45,
            "function": "process_payment",
            "code_context": "customer_id = payload['customer_id']",
            "vars": {"payload": "{}"}
        }],
        breadcrumbs=[{
            "category": "http",
            "message": "POST /checkout received",
            "level": "info"
        }]
    )

    assert "hypothesis" in result
    assert "remediation_steps" in result
    assert len(result["remediation_steps"]) >= 2
    assert "suggested_fix_diff" in result
    assert result["confidence"] > 0.8
    assert "customer_id" in result["hypothesis"] or "key" in result["hypothesis"].lower()
