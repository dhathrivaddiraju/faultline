import pytest
from backend.app.services.clustering import generate_fingerprint, normalize_path, normalize_string

def test_normalize_path():
    p1 = "C:\\Users\\user\\project\\views\\checkout.py"
    norm = normalize_path(p1)
    assert "\\" not in norm
    assert norm.endswith("views/checkout.py")

def test_normalize_string_strips_mem_addr_and_uuid():
    text = "Object <Order at 0x7f8a12bc90> failed with id 550e8400-e29b-41d4-a716-446655440000"
    normalized = normalize_string(text)
    assert "0x7f8a12bc90" not in normalized
    assert "<mem_addr>" in normalized
    assert "550e8400-e29b-41d4-a716-446655440000" not in normalized
    assert "<uuid>" in normalized

def test_fingerprint_deterministic_clustering():
    frames_run1 = [
        {"filename": "app/services/billing.py", "function": "process_payment", "in_app": True, "lineno": 42},
        {"filename": "app/core/gateway.py", "function": "charge_token", "in_app": True, "lineno": 105}
    ]
    # Run 2: different line number (e.g. after minor edit or whitespace change), but same frames
    frames_run2 = [
        {"filename": "app/services/billing.py", "function": "process_payment", "in_app": True, "lineno": 44},
        {"filename": "app/core/gateway.py", "function": "charge_token", "in_app": True, "lineno": 108}
    ]

    fp1, culprit1, title1 = generate_fingerprint("ValueError", frames_run1, "Invalid token at 0x0001")
    fp2, culprit2, title2 = generate_fingerprint("ValueError", frames_run2, "Invalid token at 0x0002")

    # The SHA-256 fingerprints MUST match so errors are intelligently clustered together
    assert fp1 == fp2
    assert culprit1 == culprit2
    assert len(fp1) == 64  # SHA-256 hex string

def test_fingerprint_distinct_for_different_errors():
    frames_a = [{"filename": "app/views/auth.py", "function": "login", "in_app": True}]
    frames_b = [{"filename": "app/views/cart.py", "function": "add_item", "in_app": True}]

    fp_a, _, _ = generate_fingerprint("KeyError", frames_a, "missing user")
    fp_b, _, _ = generate_fingerprint("ValueError", frames_b, "invalid item id")

    assert fp_a != fp_b
