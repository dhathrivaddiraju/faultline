import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app, initialize_default_project
from backend.app.database import create_tables, init_engine


@pytest.mark.asyncio
async def test_capture_endpoint_performance_and_auth():
    await init_engine()
    await create_tables()
    await initialize_default_project()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauthorized_response = await client.post("/api/v1/capture", json={
            "exception_type": "RuntimeError",
            "message": "Crash"
        })
        assert unauthorized_response.status_code == 401

        payload = {
            "exception_type": "ValueError",
            "message": "Invalid credit card CVV format",
            "stack_trace": [
                {
                    "filename": "app/services/checkout.py",
                    "lineno": 72,
                    "function": "validate_cvv",
                    "code_context": "if len(cvv) < 3: raise ValueError('Invalid credit card CVV format')",
                    "in_app": True
                }
            ],
            "environment": "production",
            "level": "error",
            "tags": {"release": "v2.1.0"},
            "breadcrumbs": [
                {"message": "User submitted payment form", "category": "ui"}
            ]
        }

        response = await client.post(
            "/api/v1/capture",
            json=payload,
            headers={"X-Project-Key": "fl_live_production_demo_key_99"}
        )
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert "event_id" in response_data
        assert "Event queued" in response_data["message"]
