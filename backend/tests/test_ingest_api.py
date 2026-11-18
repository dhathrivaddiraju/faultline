import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app, seed_default_project
from backend.app.database import create_tables, init_engine

@pytest.mark.asyncio
async def test_capture_endpoint_performance_and_auth():
    await init_engine()
    await create_tables()
    await seed_default_project()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Test missing API key returns 401
        res = await ac.post("/api/v1/capture", json={
            "exception_type": "RuntimeError",
            "message": "Crash"
        })
        assert res.status_code == 401

        # 2. Test valid API key (using default seeded demo key)
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

        res = await ac.post(
            "/api/v1/capture",
            json=payload,
            headers={"X-Project-Key": "fl_live_production_demo_key_99"}
        )
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "accepted"
        assert "event_id" in data
        assert "queued successfully" in data["message"]
