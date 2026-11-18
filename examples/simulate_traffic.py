"""
Faultline Traffic & Crash Generator
Simulates realistic production crash events across multiple microservices to populate the dashboard.
"""

import time
import random
import faultline

def run_simulation(endpoint="http://localhost:8000", total_events=25):
    print(f"🚀 Initializing Faultline Traffic Generator targeting {endpoint}...")
    
    faultline.init(
        api_key="fl_live_production_demo_key_99",
        endpoint=endpoint,
        environment="production",
        release="v2.4.1",
        auto_hook=False
    )
    
    users = [
        {"id": "usr_9481", "email": "alex.dev@corp.internal"},
        {"id": "usr_2041", "email": "sarah.admin@enterprise.io"},
        {"id": "usr_7719", "email": "guest_customer_99@gmail.com"}
    ]

    print(f"⚡ Generating {total_events} realistic crash events across services...")

    for i in range(total_events):
        choice = random.choice(["key_error", "zero_division", "db_timeout", "null_pointer", "type_error"])
        user = random.choice(users)
        faultline.set_user(id=user["id"], email=user["email"])
        
        try:
            if choice == "key_error":
                faultline.add_breadcrumb("User clicked 'Confirm Purchase'", category="ui")
                faultline.add_breadcrumb("Validating order payload", category="validation", data={"items_count": 3})
                faultline.add_breadcrumb("Calling payment processor Stripe v3", category="http")
                payload = {"amount": 120.50}  # missing customer_id
                _ = payload["customer_id"]
                
            elif choice == "zero_division":
                faultline.add_breadcrumb("Calculating cart promotional discount", category="pricing")
                faultline.add_breadcrumb("Applying bulk tier coupon code SUMMER_2026", category="coupon")
                total_items = 0
                unit_price = 150.0 / total_items
                
            elif choice == "db_timeout":
                faultline.add_breadcrumb("Acquiring Postgres connection from pool", category="database")
                faultline.add_breadcrumb("Query: SELECT * FROM orders WHERE status = 'pending' FOR UPDATE", category="sql")
                raise TimeoutError("Database connection timed out after 5000ms: pool exhausted (max=20)")

            elif choice == "null_pointer":
                faultline.add_breadcrumb("Fetching user profile from Redis cache", category="cache", data={"hit": False})
                faultline.add_breadcrumb("Querying user profile from primary database", category="database")
                profile = None
                name = profile.full_name  # AttributeError

            elif choice == "type_error":
                faultline.add_breadcrumb("Parsing JSON response from downstream inventory service", category="http")
                qty = "unlimited"
                total = 10 + qty

        except Exception as err:
            level = "critical" if choice in ("db_timeout", "null_pointer") else "error"
            faultline.capture_exception(
                err, 
                tags={"service": f"service-{choice}", "region": "us-east-1"},
                handled=False,
                level=level
            )
            print(f"  [{i+1}/{total_events}] Captured {type(err).__name__} ({choice})")
            
        time.sleep(0.08)

    print("✨ Flushing pending SDK events to Faultline Ingestion Pipeline...")
    faultline.get_client().close()
    print("✅ All simulated crash events successfully transmitted!")

if __name__ == "__main__":
    run_simulation()
