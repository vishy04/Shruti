import pytest
from src.core.router import classify_intent

@pytest.mark.integration
def test_router_integration():
    intent1 = classify_intent("पिरेंका तिवारी 30 माई 38, 35, 42, 49, 40, सलवार सेंति 30, 15")
    intent2 = classify_intent("बिंदु का नाप क्या है और कब देना है")
    assert intent1 == "ORDER"
    assert intent2 is not None
