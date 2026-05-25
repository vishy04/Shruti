import gspread
import gspread.exceptions
import json
import os
import re
import io
import csv
from groq import Groq
from datetime import datetime
from src.prompts import RAG_ANSWER_PROMPT
from src.extractor import OrderData
from gspread.utils import ValueInputOption


def get_worksheets():
    """Helper to authenticate and fetch both Customers and Orders sheets."""
    sa_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    gc = gspread.service_account_from_dict(sa_info)
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])

    customers_ws = sheet.worksheet("Customers")
    orders_ws = sheet.worksheet("Orders")
    return customers_ws, orders_ws


def get_next_sequential_id(ws, prefix: str, start_num: int) -> str:
    """Generates the next sequential ID (e.g. C-101 or O-1001) from Column A."""
    ids = ws.col_values(1)  # Column A
    max_num = start_num
    for val in ids:
        if val.startswith(f"{prefix}-"):
            try:
                num = int(val.split("-")[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    return f"{prefix}-{max_num + 1}"


def fetch_recent_orders(query: str = None) -> str:
    """Fetches and filters the Customer list and Orders sheet to build a compact RAG context."""
    cust_ws, ord_ws = get_worksheets()

    customers_data = cust_ws.get_all_values()
    orders_data = ord_ws.get_all_values()

    query_words = []
    if query:
        # Normalize, remove common fillers, and split query into search terms
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
        clean_query = (
            query.replace("?", " ").replace(",", " ").replace(".", " ").lower()
        )
        query_words = [
            w.strip()
            for w in clean_query.split()
            if len(w) > 2 and w.strip() not in fillers
        ]

    filtered_customers = [customers_data[0]]  # Include headers
    matching_customer_names = set()

    for row in customers_data[1:]:
        if len(row) > 1:
            name = row[1].strip()
            name_lower = name.lower()
            tag = row[2].lower() if len(row) > 2 else ""

            # Match if any keyword is found in name or tag
            match = False
            for word in query_words:
                if word in name_lower or word in tag:
                    match = True
                    break

            # If query is empty, or there's a match, include it
            if match or not query_words:
                filtered_customers.append(row)
                matching_customer_names.add(name_lower)

    filtered_orders = [orders_data[0]]  # Include headers
    for row in orders_data[1:]:
        if len(row) > 1:
            cust_name = row[1].strip().lower()
            status = row[12].lower() if len(row) > 12 else ""
            notes = row[13].lower() if len(row) > 13 else ""

            match = False
            for word in query_words:
                if (
                    word in cust_name
                    or (word in status and word in ["pending", "delivered"])
                    or word in notes
                ):
                    match = True
                    break

            if match or not query_words:
                filtered_orders.append(row)

    # Fallback: If query yields 0 results, send the last 20 orders and their matching profiles
    if len(filtered_orders) <= 1 and len(filtered_customers) <= 1:
        recent_orders = orders_data[1:][-20:]
        filtered_orders = [orders_data[0]] + recent_orders

        recent_names = set(
            row[1].strip().lower() for row in recent_orders if len(row) > 1
        )
        filtered_customers = [customers_data[0]]
        for row in customers_data[1:]:
            if len(row) > 1 and row[1].strip().lower() in recent_names:
                filtered_customers.append(row)

    # Limit to top 50 matches to keep the prompt extremely small
    if len(filtered_orders) > 51:
        filtered_orders = [filtered_orders[0]] + filtered_orders[1:][-50:]

    output = io.StringIO()
    writer = csv.writer(output)

    output.write("=== CUSTOMER REGISTRY (Sheet 1) ===\n")
    writer.writerows(filtered_customers)

    output.write("\n=== ORDER LEDGER (Sheet 2) ===\n")
    writer.writerows(filtered_orders)

    return output.getvalue()


def answer_question(transcript: str) -> str:
    """Reads filtered spreadsheets and answers a customer question using Llama-3."""
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
        temperature=0.3,
    )
    return response.choices[0].message.content


def append_order(order: OrderData):
    """Saves a new order to the Orders sheet, registering the customer if new."""
    cust_ws, ord_ws = get_worksheets()
    m = order.measurements

    # Check for identical duplicate order in the last 5 entries to prevent double-submits
    all_orders = ord_ws.get_all_values()
    if len(all_orders) > 1:
        last_rows = all_orders[-5:]
        for row in last_rows:
            if len(row) > 10:
                row_cust_name = row[1].strip().lower()
                row_garment = row[2].strip().lower()
                try:
                    meas_match = (
                        str(row[3]) == str(m.chest or "")
                        and str(row[4]) == str(m.waist or "")
                        and str(row[5]) == str(m.hip or "")
                        and str(row[6]) == str(m.shoulder or "")
                        and str(row[7]) == str(m.sleeve_length or "")
                        and str(row[8]) == str(m.garment_length or "")
                        and str(row[9]) == str(m.salwar_length or "")
                        and str(row[10]) == str(m.mori or "")
                    )
                except IndexError:
                    meas_match = False

                if (
                    row_cust_name == order.customer_name.strip().lower()
                    and row_garment == (order.garment_type or "").strip().lower()
                    and meas_match
                ):
                    order.order_id = row[0]
                    raise ValueError("DUPLICATE_ORDER")

    # 1. Customer Check (Deduplication by case-insensitive name match)
    name_lower = order.customer_name.strip().lower()
    all_customers = cust_ws.get_all_values()
    cust_id = None

    for row in all_customers[1:]:
        if len(row) > 1 and row[1].strip().lower() == name_lower:
            cust_id = row[0]
            break

    # If customer is new, register them in Customers tab
    if not cust_id:
        res_cust = cust_ws.append_row(
            [
                "PENDING",
                order.customer_name,
                order.customer_tag or "",
                order.special_instructions or "",  # General notes
                datetime.now().strftime("%d %b %y"),
                datetime.now().strftime("%d %b %y"),
            ],
            value_input_option=ValueInputOption.user_entered,
        )

        # Get the row number dynamically from range (e.g. "Customers!A105:F105")
        updated_range = res_cust.get("updates", {}).get("updatedRange", "")
        row_num = int(re.findall(r"\d+", updated_range)[0])

        # Get the ID of the previous row with a retry loop to handle concurrent writes safely
        import time

        prev_id = "PENDING"
        for _ in range(20):
            prev_id = cust_ws.cell(row_num - 1, 1).value
            if prev_id != "PENDING":
                break
            time.sleep(0.1)

        try:
            prev_num = int((prev_id or " ").split("-")[1])
        except (ValueError, IndexError, AttributeError):
            prev_num = 100  # Default fallback

        cust_id = f"C-{prev_num + 1}"
        cust_ws.update_acell(f"A{row_num}", cust_id)

    # 2. Insert the newest order directly under the header so recent measurements
    # stay at the top of the sheet.
    order.order_id = get_next_sequential_id(ord_ws, "O", 1000)
    order_row = [
        order.order_id,
        order.customer_name,
        order.garment_type or "",
        m.chest or "",
        m.waist or "",
        m.hip or "",
        m.shoulder or "",
        m.sleeve_length or "",
        m.garment_length or "",
        m.salwar_length or "",
        m.mori or "",
        order.delivery_date or "",
        "Pending",  # Live orders default to Pending status
        order.special_instructions or "",
        datetime.now().strftime("%d %b %y"),
    ]
    ord_ws.insert_row(
        order_row,
        index=2,
        value_input_option=ValueInputOption.user_entered,
    )


def is_message_processed(msg_id: str, sender: str) -> bool:
    """Checks if a message ID has already been processed using a ProcessedMessages sheet.
    If not processed, appends it and returns False. If already processed, returns True.
    """
    sa_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    gc = gspread.service_account_from_dict(sa_info)
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])

    try:
        processed_ws = sheet.worksheet("ProcessedMessages")
    except gspread.exceptions.WorksheetNotFound:
        # Create sheet with 3 columns: Message ID, Sender, Processed At
        processed_ws = sheet.add_worksheet(title="ProcessedMessages", rows=1000, cols=3)
        processed_ws.append_row(
            ["Message ID", "Sender", "Processed At"], value_input_option="USER_ENTERED"
        )

    # Search for msg_id in Column A (Message ID) using an exact regex match to avoid partial matches
    cell = processed_ws.find(re.compile(rf"^{re.escape(msg_id)}$"), in_column=1)
    if cell is not None:
        return True
    else:
        # Append the new message ID to log it
        processed_ws.append_row(
            [msg_id, sender, datetime.now().strftime("%d %b %y %H:%M:%S")],
            value_input_option="USER_ENTERED",
        )
        return False
