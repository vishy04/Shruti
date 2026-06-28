import os
import sys

from dotenv import load_dotenv

# Ensure project root is in path (one level up)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from src.services.llm.extractor import extract_order


def run_tests():
    transcripts = [
        "Jyoti Sahu 38+36+43 l 44 sl 16 stend kreem orenge golv 1june",
        "Nutan 44+39+51+gla gol 42+16+salwar 38",
        "Priya 34+30+38+43+16 delivery 5 July",
        "Rekha 34+32+37+15+42",
    ]

    for i, t in enumerate(transcripts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Transcript: {t}")
        try:
            order = extract_order(t)
            print(f"Extracted customer_name: {order.customer_name}")
            print(f"Extracted customer_tag: {order.customer_tag}")
            print(f"Extracted delivery_date: {order.delivery_date}")
            print(f"Extracted raw_measurement_text: {order.raw_measurement_text}")

            # Simple assertions to match expectations
            assert order.customer_name is not None
            assert len(order.customer_name) > 0
            assert order.raw_measurement_text == t
        except Exception as e:
            print(f"Error during extraction: {e}")


if __name__ == "__main__":
    run_tests()
