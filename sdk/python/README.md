# Faultline Python SDK

Python client library for the Faultline error monitoring service.

## Installation

```bash
pip install faultline-sdk
```

## Usage

```python
import faultline

faultline.init(
    api_key="fl_live_production_demo_key_99",
    endpoint="http://localhost:8000",
    environment="production",
    release="v1.2.0"
)

faultline.add_breadcrumb("Payment gateway dispatch", category="http", data={"amount": 49.99})

@faultline.capture_exceptions(tags={"service": "billing"})
def charge_card(token: str):
    if not token:
        raise ValueError("Invalid charge token")

with faultline.capture(tags={"module": "reports"}):
    generate_statement()

try:
    process_order()
except Exception as exc:
    faultline.capture_exception(exc, tags={"criticality": "high"})
```
