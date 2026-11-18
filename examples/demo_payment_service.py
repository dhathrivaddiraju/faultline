from fastapi import FastAPI
import faultline

faultline.init(
    api_key="fl_live_production_demo_key_99",
    endpoint="http://localhost:8000",
    environment="production",
    release="v1.0.0"
)

app = FastAPI(title="Payment Gateway Microservice")


@app.get("/checkout/charge")
@faultline.capture_exceptions(tags={"endpoint": "/checkout/charge"})
def charge_payment(amount: float, token: str):
    faultline.add_breadcrumb(f"Initiating charge for amount ${amount}", category="payment")

    if amount <= 0:
        faultline.add_breadcrumb("Invalid charge amount", category="validation", level="warning")
        raise ValueError("Charge amount must be strictly positive")

    if not token.startswith("tok_"):
        faultline.add_breadcrumb(f"Invalid token format", category="security")
        raise KeyError(f"Invalid gateway token format: {token}")

    return {"status": "success", "amount": amount, "transaction_id": "tx_99182"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
