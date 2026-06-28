import pytest
from src.services.llm.extractor import extract_order

@pytest.mark.integration
def test_extractor_integration():
    transcript = " पिरेंका तिवारी 30 माई 38, 35, 42, 49, 40, सलवार सेंति 30, 15"
    order = extract_order(transcript)
    assert order.customer_name is not None
    assert "पिरेंका" in order.customer_name or "tiwari" in order.customer_name.lower() or "तिवारी" in order.customer_name
    assert order.raw_measurement_text is not None
    assert len(order.raw_measurement_text) > 0