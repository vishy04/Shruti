import json
import os
import re
from datetime import datetime

import gspread
import gspread.exceptions
from gspread.utils import ValueInputOption

from src.services.llm.extractor import OrderData
from src.services.sheets.sheets_client import get_customers_ws, get_orders_ws, get_processed_messages_ws


def get_worksheets():
    """Helper to fetch both Customers and Orders sheets."""
    return get_customers_ws(), get_orders_ws()


def get_next_sequential_id(ws, prefix: str, start_num: int) -> str:
    """Generates the next sequential ID (e.g. O-1001) from Column A."""
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
        cust_id = get_next_sequential_id(cust_ws, "C", 100)
        cust_ws.append_row(
            [
                cust_id,
                order.customer_name,
                order.customer_tag or "",
                order.special_instructions or "",  # General notes
                datetime.now().strftime("%d %b %y"),
                datetime.now().strftime("%d %b %y"),
            ],
            value_input_option=ValueInputOption.user_entered,
        )

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
    try:
        processed_ws = get_processed_messages_ws()
    except gspread.exceptions.WorksheetNotFound:
        from src.services.sheets.sheets_client import _client
        sheet = _client._get_sheet()
        # Create sheet with 3 columns: Message ID, Sender, Processed At
        processed_ws = sheet.add_worksheet(title="ProcessedMessages", rows=1000, cols=3)
        processed_ws.append_row(
            ["Message ID", "Sender", "Processed At"],
            value_input_option=ValueInputOption.user_entered,
        )

    # Search for msg_id in Column A (Message ID) using an exact regex match to avoid partial matches
    cell = processed_ws.find(re.compile(rf"^{re.escape(msg_id)}$"), in_column=1)
    if cell is not None:
        return True
    else:
        # Append the new message ID to log it
        processed_ws.append_row(
            [msg_id, sender, datetime.now().strftime("%d %b %y %H:%M:%S")],
            value_input_option=ValueInputOption.user_entered,
        )
        return False
