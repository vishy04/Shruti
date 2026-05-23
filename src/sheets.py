import gspread
import json, os, io, csv
from groq import Groq
from src.prompts import RAG_ANSWER_PROMPT


def get_worksheet():
    #Authentication and fetching 
    sa_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    gc = gspread.service_account_from_dict(sa_info)
    sheet = gc.open(os.environ["GOOGLE_SHEET_NAME"])
    return sheet.sheet1


def fetch_recent_orders() -> str:
    #last 500 orders
    ws = get_worksheet()
    all_values = ws.get_all_values()

    if not all_values:
        return "No Orders found in the database"
    
    headers = all_values[0]

    #get the last 500 rows (excluding headers)
    recent_rows = all_values[1:][-500:]
    #combine headers and recent rows
    data_to_format = [headers] + recent_rows

    #convert list to CSV string for LLM (easier for it to read)
    
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerows(data_to_format)
    return output.getvalue()


def answer_question(transcript:str)-> str:
    #passing the question and sheet to llama

    context = fetch_recent_orders()

    #producing a natural answer from sheet data

    client = Groq()
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages= [
            {
                "role":"user",
                "content":RAG_ANSWER_PROMPT.format(
                    context = context ,
                    question = transcript,
                )
            }
        ] ,
        temperature=0.3 ,
    )

    return response.choices[0].message.content
    
from datetime import datetime
from src.extractor import OrderData

def append_order(order: OrderData):
    """Saves a new order as a new row in Google Sheets."""
    ws = get_worksheet()
    m = order.measurements

    # Create a list that matches the columns in your Google Sheet exactly!
    # If a value doesn't exist (is None), we put an empty string "" instead.
    row = [
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
        "Pending",  # Every new order starts with a Pending status
        order.special_instructions or "",
        datetime.now().strftime("%Y-%m-%d %H:%M"), # Logs exactly when this order was created
    ]
    
    # Append it to the sheet. 
    # "USER_ENTERED" tells Google to format numbers and dates as if a human typed them.
    ws.append_row(row, value_input_option="USER_ENTERED")

def get_next_order_number(initial: str) -> int:
    """Generates the next sequential number for an Order ID (e.g., #S-101, #S-102)"""
    ws = get_worksheet()
    
    # Fetch all values in Column 1 (Column A)
    order_ids = ws.col_values(1)  

    max_num = 100  # We start counting from 101

    # Loop through all existing IDs
    for oid in order_ids:
        # Check if the ID starts with our target letter (e.g., "#S-")
        if oid.startswith(f"#{initial}-"):
            try:
                # Split "#S-101" into ["#S", "101"], grab the "101", and turn it into an integer
                num = int(oid.split("-")[1])
                # Keep track of the highest number we've seen
                if num > max_num:
                    max_num = num
            except ValueError:
                pass # If it fails to turn into a number, just ignore it and keep going
                
    return max_num + 1
