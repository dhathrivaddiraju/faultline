import pytest
import faultline
from faultline.client import FaultlineClient
from faultline.decorators import capture_exceptions

def test_sdk_init_and_breadcrumbs():
    client = faultline.init(
        api_key="test_api_key_123",
        endpoint="http://localhost:8000",
        environment="test",
        auto_hook=False
    )
    assert isinstance(client, FaultlineClient)
    assert client.api_key == "test_api_key_123"

    faultline.add_breadcrumb("User clicked login", category="navigation")
    faultline.add_breadcrumb("API returned 200", category="http", data={"status": 200})

    crumbs = client.breadcrumbs.get_all()
    assert len(crumbs) == 2
    assert crumbs[0]["message"] == "User clicked login"
    assert crumbs[1]["data"]["status"] == 200

def test_sdk_decorator_captures_exception():
    client = faultline.init(
        api_key="test_api_key_123",
        endpoint="http://localhost:8000",
        environment="test",
        auto_hook=False
    )

    captured = []
    # Mock transport send
    client.transport.send = lambda evt: captured.append(evt)

    @capture_exceptions(tags={"layer": "database"}, reraise=False)
    def failing_function():
        raise ZeroDivisionError("Cannot divide by zero in balance calculation")

    failing_function()

    assert len(captured) == 1
    event = captured[0]
    assert event["exception_type"] == "ZeroDivisionError"
    assert "Cannot divide by zero" in event["message"]
    assert event["tags"]["layer"] == "database"
    assert event["handled"] is False
    assert len(event["stack_trace"]) > 0
