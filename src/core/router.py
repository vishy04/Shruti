from groq import Groq
import json
from src.core.prompts import ROUTER_PROMPT

def classify_intent(transcript:str) -> str:

    client = Groq()

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": ROUTER_PROMPT.format(transcript = transcript),
            }
        ],
        model="llama-3.1-8b-instant",
        temperature=0,
        max_completion_tokens=50,
        response_format={"type":"json_object"},#strict formatting
    )

    # api give no text sometime, me check empty first so load no break.
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response received from LLM")
    result = json.loads(content)
    return result.get("intent", "ORDER")
