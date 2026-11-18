import argparse
import random
import time
import faultline


def run_traffic_generator(endpoint: str, api_key: str, count: int, rate: float):
    print(f"Connecting to Faultline at {endpoint}...")

    faultline.init(
        api_key=api_key,
        endpoint=endpoint,
        environment="production",
        release="v2.4.1",
        auto_hook=False
    )

    test_identities = [
        {"id": "usr_9481", "email": "dev.operator@internal.corp"},
        {"id": "usr_2041", "email": "platform.lead@enterprise.io"},
        {"id": "usr_7719", "email": "checkout.service@system.local"}
    ]

    scenarios = ["key_error", "zero_division", "db_timeout", "null_pointer", "type_error"]

    for index in range(count):
        scenario = random.choice(scenarios)
        identity = random.choice(test_identities)
        faultline.set_user(id=identity["id"], email=identity["email"])

        try:
            if scenario == "key_error":
                faultline.add_breadcrumb("Order payload validation", category="validation", data={"items": 3})
                faultline.add_breadcrumb("Payment gateway dispatch", category="http")
                payload: dict[str, float] = {"amount": 120.50}
                _ = payload["customer_id"]

            elif scenario == "zero_division":
                faultline.add_breadcrumb("Discount calculation", category="pricing")
                total_units = 0
                _ = 150.0 / total_units

            elif scenario == "db_timeout":
                faultline.add_breadcrumb("Connection acquisition", category="database")
                raise TimeoutError("Database connection pool exhausted: 20/20 active connections.")

            elif scenario == "null_pointer":
                faultline.add_breadcrumb("Cache lookup miss", category="cache")
                account = None
                _ = account.display_name

            elif scenario == "type_error":
                faultline.add_breadcrumb("Downstream inventory payload parsing", category="http")
                count_str: Any = "invalid_int"
                _ = 10 + count_str

        except Exception as exc:
            severity = "critical" if scenario in ("db_timeout", "null_pointer") else "error"
            faultline.capture_exception(
                exc,
                tags={"service": f"service-{scenario}", "region": "us-east-1"},
                handled=False,
                level=severity
            )
            print(f"[{index + 1}/{count}] Captured {type(exc).__name__} ({scenario})")

        time.sleep(1.0 / rate if rate > 0 else 0.05)

    client = faultline.get_client()
    if client:
        client.close()
    print("Event flush complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faultline Telemetry Traffic Generator")
    parser.add_argument("--endpoint", default="http://localhost:8000", help="Faultline server endpoint")
    parser.add_argument("--key", default="fl_live_production_demo_key_99", help="Project API key")
    parser.add_argument("--count", type=int, default=25, help="Number of telemetry events to generate")
    parser.add_argument("--rate", type=float, default=10.0, help="Events per second")
    args = parser.parse_args()

    run_traffic_generator(
        endpoint=args.endpoint,
        api_key=args.key,
        count=args.count,
        rate=args.rate
    )
