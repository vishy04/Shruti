import os
import pytest
import uuid
from src.services.llm.extractor import extract_order
from src.services.sheets.sheets import append_order, is_message_processed
from src.services.llm.rag import fetch_recent_orders, answer_question

@pytest.mark.integration
def test_live_sheets_pipeline_integration():
    # 0. Test Persistent Deduplication
    test_msg_id = f"test-wamid-{uuid.uuid4()}"
    test_sender = "918839038332"

    is_dup1 = is_message_processed(test_msg_id, test_sender)
    assert is_dup1 is False, "First deduplication check should be False"

    is_dup2 = is_message_processed(test_msg_id, test_sender)
    assert is_dup2 is True, "Second deduplication check should be True"

    # 1. Test Mock Voice/Text Transcription Extraction
    mock_transcript = "Sunita gour ka suit chest 36 waist 31 hip 40 Kandha 14 sleeve 15 length 42 salwar 37 mohri 6 pocket lagana hai, delivery next week tak chahiye"
    order = extract_order(mock_transcript)
    
    assert order.customer_name.lower() == "sunita gour"
    assert order.garment_type.lower() == "suit"
    assert order.measurements is not None
    assert order.measurements.chest == 36
    assert order.measurements.waist == 31
    assert order.measurements.hip == 40

    # 2. Test Sheets insertion & ID generation
    append_order(order)
    assert order.order_id is not None
    assert order.order_id.startswith("O-")

    # 3. Test RAG Context fetch
    context = fetch_recent_orders()
    assert context is not None
    assert len(context) > 0

    # 4. Test Q&A Answering
    question = "Sunita gour ke suit ka waist measurement kya hai?"
    answer = answer_question(question)
    assert answer is not None
    assert "31" in answer
