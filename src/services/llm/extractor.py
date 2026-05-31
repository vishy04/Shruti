from pydantic import BaseModel
import json

# extraction logic

from groq import Groq
from datetime import datetime
from src.core.prompts import EXTRACTION_PROMPT


class Measurements(BaseModel):
    raw_measurement_string: str | None = None  # e.g. "34+30+38+43+16"
    chest: float | None = None  # Chhati
    waist: float | None = None  # Kamar
    hip: float | None = None  # Hip
    garment_length: float | None = None  # Length
    sleeve_length: float | None = None  # Sleeve
    shoulder: float | None = None  # Shoulder
    salwar_length: float | None = None  # Salwar Len
    mori: float | None = None  # Mori


class OrderData(BaseModel):
    thinking_process: str  # Chain of thought reasoning
    customer_name: str
    customer_tag: str | None = None  # Location or relationship tag
    garment_type: str | None = None  # Garment (e.g. Frok, Suit, Blouse)
    measurements: Measurements
    delivery_date: str | None = None  # Delivery Date
    special_instructions: str | None = (
        None  # Notes (includes bottom style, neckline, pockets, lining, etc.)
    )
    order_id: str | None = None  # Order ID


def extract_order(transcript: str) -> OrderData:
    client = Groq()
    today = datetime.now().strftime("%Y-%m-%d")

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT.format(
                    transcript=transcript,
                    today=today,
                ),
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    order = OrderData(**data)  # validating with python

    if not order.customer_name or order.customer_name.strip() == "":
        raise ValueError("Customer name missing from transcript")

    return order
