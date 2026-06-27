from src.services.sheets.sheets_client import get_customers_ws, get_orders_ws
import io
import csv
from groq import Groq
from src.core.prompts import RAG_ANSWER_PROMPT


def fetch_recent_orders(query: str = "") -> str:
    query = query or ""

    customer_ws = get_customers_ws()
    order_ws = get_orders_ws()

    customer_data = customer_ws.get_all_values()
    order_data = order_ws.get_all_values()

    # TODO:remove ? , . and filler words from query
    fillers = {
        "ka",
        "ke",
        "ki",
        "ko",
        "kya",
        "hai",
        "tha",
        "se",
        "suit",
        "pant",
        "order",
        "measurements",
        "measurement",
    }
    # removing all punctuation to split by space next
    clean_query = (
        query.replace("?", " ").replace(".", " ").replace(",", " ").strip().lower()
    )

    search_words = [w for w in clean_query.split() if len(w) > 2 and w not in fillers]

    # TODO: use substring matching against known Names
    # all lowercase names in my database
    known_names = {
        row[1].strip().lower()
        for row in customer_data[1:]
        if len(row) > 1 and row[1].strip()
    }
    # check which customer name is present in the query string
    matched_customers = set()
    # in dev_log
    if query:
        for name in known_names:
            if name in clean_query:
                matched_customers.add(name)

    filtered_orders = [order_data[0]]

    for row in order_data[1:]:
        if len(row) > 1:
            # if no query pass full orders [50 max]
            if not query:
                filtered_orders.append(row)
                continue

            cust_name = row[1].strip().lower()
            status = row[12].lower() if len(row) > 12 else ""
            notes = row[13].lower() if len(row) > 13 else ""

            # Match if the customer name in matched_customers
            match = cust_name in matched_customers

            # Or if any of the search words match the status or notes
            if not match:
                for word in search_words:
                    if (
                        word in status and word in ["pending", "delivered"]
                    ) or word in notes:
                        match = True
                        break
            if match:
                filtered_orders.append(row)

    if len(filtered_orders) <= 1:
        filtered_orders = [order_data[0]] + order_data[1:21]

    filtered_orders = [filtered_orders[0]] + filtered_orders[1:51]

    active_customer_names = {
        row[1].strip().lower() for row in filtered_orders[1:] if len(row) > 1
    }

    filtered_customers = [customer_data[0]] + [
        row
        for row in customer_data[1:]
        if len(row) > 1 and row[1].strip().lower() in active_customer_names
    ]

    output = io.StringIO()
    writer = csv.writer(output)

    output.write("=== CUSTOMER REGISTRY (Sheet 1) ===\n")
    writer.writerows(filtered_customers)

    output.write("\n=== ORDER LEDGER (Sheet 2) ===\n")
    writer.writerows(filtered_orders)

    return output.getvalue()


def answer_question(transcript: str) -> str:

    context = fetch_recent_orders(transcript)

    client = Groq()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": RAG_ANSWER_PROMPT.format(
                    context=context,
                    question=transcript,
                ),
            }
        ],
        temperature=0.1,
    )
    # output can be none, me change to empty string if none so return string always.
    content = response.choices[0].message.content
    return content if content is not None else ""
