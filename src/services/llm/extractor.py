import json
from datetime import datetime

# extraction logic
from groq import Groq
from pydantic import BaseModel

from src.core.prompts import EXTRACTION_PROMPT


class OrderData(BaseModel):
    customer_name: str
    customer_tag: str | None = None
    delivery_date: str | None = None
    raw_measurement_text: str


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

    # response content can be none, loads need string.check none first, stop crash.
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response received from LLM")
    data = json.loads(content)

    order = OrderData(**data)  # validating with python

    if not order.customer_name or order.customer_name.strip() == "":
        raise ValueError("Customer name missing from transcript")

    return order
