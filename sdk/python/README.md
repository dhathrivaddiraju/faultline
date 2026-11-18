# Faultline Python SDK

Lightweight, sub-millisecond error monitoring and crash reporting SDK for Python applications.

## Installation

```bash
pip install faultline-sdk
```

## Quick Start

```python
import faultline

# 1. Initialize once at application startup
faultline.init(
    api_key="fl_live_production_demo_key_99",
    endpoint="http://localhost:8000",
    environment="production",
    release="v1.2.0"
)

# 2. Add breadcrumbs to trace events leading to an error
faultline.add_breadcrumb("User clicked 'Checkout'", category="ui")
faultline.add_breadcrumb("Calling payment gateway API", category="http", data={"amount": 49.99})

# 3. Automatic Global Crash Capture:
# Unhandled exceptions are automatically captured via sys.excepthook and threading.excepthook

# 4. Decorator capture:
@faultline.capture_exceptions(tags={"service": "billing"})
def charge_card(token):
    # Any crash here is automatically captured with full stack trace & breadcrumbs
    raise ValueError("Invalid charge token")

# 5. Context manager:
with faultline.capture(tags={"module": "reports"}):
    generate_annual_statement()

# 6. Manual capture in try/except:
try:
    process_order()
except Exception as err:
    faultline.capture_exception(err, tags={"criticality": "high"})
```
