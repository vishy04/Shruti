import os
import sys
from dotenv import load_dotenv

# Ensure main directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from src.extractor import extract_order
from src.sheets import append_order, fetch_recent_orders, answer_question

def run_integration_test():
    print("=" * 60)
    print("        SILAI LIVE PIPELINE INTEGRATION TEST           ")
    print("=" * 60)
    
    # 0. Test Persistent Deduplication
    print("Step 0: Testing persistent deduplication...")
    import uuid
    from src.sheets import is_message_processed
    
    test_msg_id = f"test-wamid-{uuid.uuid4()}"
    test_sender = "918839038332"
    
    try:
        is_dup1 = is_message_processed(test_msg_id, test_sender)
        print(f"   First call: is_duplicate={is_dup1} (Expected: False)")
        
        is_dup2 = is_message_processed(test_msg_id, test_sender)
        print(f"   Second call: is_duplicate={is_dup2} (Expected: True)")
        
        if not is_dup1 and is_dup2:
            print("✅ Step 0: Persistent Deduplication Successful!")
        else:
            print("❌ Step 0: Persistent Deduplication Failed!")
            return
    except Exception as e:
        print(f"❌ Step 0 failed with error: {e}")
        return

    # 1. Test Mock Voice/Text Transcription Extraction
    mock_transcript = "Sunita gour ka suit chest 36 waist 31 hip 40 Kandha 14 sleeve 15 length 42 salwar 37 mohri 6 pocket lagana hai, delivery next week tak chahiye"
    print(f"Step 1: Extracting from mock transcript...\n   Transcript: '{mock_transcript}'")
    
    try:
        order = extract_order(mock_transcript)
        print("✅ Step 1: Extraction Successful!")
        print(f"   Customer Name: {order.customer_name}")
        print(f"   Garment: {order.garment_type}")
        print(f"   Measurements: Chest={order.measurements.chest}, Waist={order.measurements.waist}, Hip={order.measurements.hip}")
        print(f"   Notes: {order.special_instructions}")
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        return

    # 2. Test Sheets insertion & ID generation
    print("\nStep 2: Saving to Google Sheets (Relational)...")
    try:
        append_order(order)
        print("✅ Step 2: Save Successful!")
        print(f"   Assigned Order ID: {order.order_id}")
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        return

    # 3. Test RAG Context fetch
    print("\nStep 3: Fetching RAG Context...")
    try:
        context = fetch_recent_orders()
        print("✅ Step 3: Fetch Successful!")
        # Print a small slice of the context
        lines = context.split("\n")
        print("   Context Snippet:")
        for line in lines[:8]:
            print(f"     {line}")
        print("     ...")
    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        return

    # 4. Test Q&A Answering
    question = "Sunita gour ke suit ka waist measurement kya hai?"
    print(f"\nStep 4: Asking Question...\n   Question: '{question}'")
    try:
        answer = answer_question(question)
        print("✅ Step 4: Q&A Successful!")
        print(f"   Answer: {answer}")
    except Exception as e:
        print(f"❌ Step 4 failed: {e}")
        return
        
    print("=" * 60)
    print("🎉 Integration Test Passed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    run_integration_test()
