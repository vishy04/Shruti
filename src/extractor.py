from pydantic import BaseModel, field_validator

class Measurements(BaseModel):
    chest: float | None = None           # Chhati
    waist: float | None = None           # Kamar
    hip: float | None = None             # Hip
    shoulder: float | None = None        # Kandha
    sleeve_length: float | None = None   # Baju
    garment_length: float | None = None  # Lambai
    salwar_length: float | None = None   # Salwar Length
    mori: float | None = None            # Mori / Bottom width

class OrderData(BaseModel):
    thinking_process: str                # Chain of thought reasoning
    customer_name: str
    customer_tag: str | None = None      # Location or relationship (e.g., babai, mami)
    garment_type: str | None = None
    measurements: Measurements
    bottom_style: str | None = None      # Trouser Pants, Traditional Salwar, Palazzo, etc.
    neckline: str | None = None          # Paan, Round, Collar, V-Neck, etc.
    has_pocket: bool = False             # Jeb
    has_lining: bool = False             # Astar
    has_dori: bool = False               # Dori
    has_lace: bool = False               # Less
    total_bill: float | None = None      # Total amount quoted
    advance_paid: float | None = None    # Advance given
    delivery_date: str | None = None     # YYYY-MM-DD
    special_instructions: str | None = None
    order_id: str | None = None          # Auto-generated later
