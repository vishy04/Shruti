from groq import Groq
import json
from src.prompts import ROUTER_PROMPT

def classify_intent(transcript:str) -> str:

    client = Groq()

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": ROUTER_PROMPT.format(transcript = transcript),
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_completion_tokens=50,
        response_format={"type":"json_object"},#strict formatting
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("intent","ORDER")
