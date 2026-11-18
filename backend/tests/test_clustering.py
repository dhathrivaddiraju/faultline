import pytest
from backend.app.services.clustering import generate_fingerprint, normalize_path, normalize_token_string


def test_normalize_path():
    path = "C:\\Users\\user\\project\\views\\checkout.py"
    normalized = normalize_path(path)
    assert "\\" not in normalized
    assert normalized.endswith("views/checkout.py")


def test_normalize_token_string():
    text = "Object <Order at 0x7f8a12bc90> failed with id 550e8400-e29b-41d4-a716-446655440000"
    normalized = normalize_token_string(text)
    assert "0x7f8a12bc90" not in normalized
    assert "<mem_addr>" in normalized
    assert "550e8400-e29b-41d4-a716-446655440000" not in normalized
    assert "<uuid>" in normalized


def test_fingerprint_deterministic_clustering():
    first_execution_frames = [
        {"filename": "app/services/billing.py", "function": "process_payment", "in_app": True, "lineno": 42},
        {"filename": "app/core/gateway.py", "function": "charge_token", "in_app": True, "lineno": 105}
    ]
    second_execution_frames = [
        {"filename": "app/services/billing.py", "function": "process_payment", "in_app": True, "lineno": 44},
        {"filename": "app/core/gateway.py", "function": "charge_token", "in_app": True, "lineno": 108}
    ]

    fingerprint_a, culprit_a, _ = generate_fingerprint(
        "ValueError", first_execution_frames, "Invalid token at 0x0001"
    )
    fingerprint_b, culprit_b, _ = generate_fingerprint(
        "ValueError", second_execution_frames, "Invalid token at 0x0002"
    )

    assert fingerprint_a == fingerprint_b
    assert culprit_a == culprit_b
    assert len(fingerprint_a) == 64


def test_fingerprint_distinct_for_different_errors():
    frames_a = [{"filename": "app/views/auth.py", "function": "login", "in_app": True}]
    frames_b = [{"filename": "app/views/cart.py", "function": "add_item", "in_app": True}]

    fingerprint_a, _, _ = generate_fingerprint("KeyError", frames_a, "missing user")
    fingerprint_b, _, _ = generate_fingerprint("ValueError", frames_b, "invalid item id")

    assert fingerprint_a != fingerprint_b
