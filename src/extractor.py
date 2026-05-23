from pydantic import BaseModel

class Measurements(BaseModel):
    raw_measurement_string: str | None = None # e.g. "34+30+38+43+16"
    chest: float | None = None           # Chhati / Number 1
    waist: float | None = None           # Kamar / Number 2
    hip: float | None = None             # Hip / Number 3
    garment_length: float | None = None  # Lambai / l / Number 4
    sleeve_length: float | None = None   # Baju / sl / Number 5
    shoulder: float | None = None        # Kandha
    salwar_length: float | None = None   # Salwar Length
    mori: float | None = None            # Mori / Bottom width

class OrderData(BaseModel):
    thinking_process: str                # Chain of thought reasoning
    customer_name: str
    customer_tag: str | None = None      # Location/relationship (e.g., babai, mami, pawar kheda)
    garment_type: str | None = None      # Frok, Suit, Blause, Lehenga, Gaun, etc.
    measurements: Measurements
    bottom_style: str | None = None      # Pant, Salwar, Plajo, Afgani, Patiyala, etc.
    neckline: str | None = None          # Paan, Gol Gla, Vot, Chokor, Collar, V, etc.
    has_pocket: bool = False             # Jeb
    has_lining: bool = False             # Astar
    has_dori: bool = False               # Dori / Latkan
    has_lace: bool = False               # Less
    has_buttons: bool = False            # Batan
    advance_paid: float | None = None    # Advance given (jma)
    delivery_date: str | None = None     # YYYY-MM-DD
    special_instructions: str | None = None
    order_id: str | None = None          # Auto-generated later


#extraction logic
from groq import Groq
from datetime import datetime
import json
from src.prompts import EXTRACTION_PROMPT

def extract_order(transcript:str) -> OrderData:
    client = Groq()
    today = datetime.now().strftime("%Y-%m-%d")

    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile", 
        messages =[
            {
                "role":"user",
                "content":EXTRACTION_PROMPT.format(
                    transcript = transcript,
                    today = today ,
                    )
            }
        ] ,
        temperature=0,
        response_format={"type":"json_object"}
    )

    data = json.loads(response.choices[0].message.content)

    order = OrderData(**data) #validating with python

    if not order.customer_name or order.customer_name.strip() == "":
        raise ValueError("Customer name missing from transcript")
    
    return order


