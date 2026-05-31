import requests
from dotenv import load_dotenv
import os
import json

load_dotenv(override=True)

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
AUTHORIZED_PHONE = os.getenv("AUTHORIZED_PHONE")

url = f"https://graph.facebook.com/v25.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

header = {
    "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

data = { 
    "messaging_product": "whatsapp", 
    "to": AUTHORIZED_PHONE, 
    "type": "template", 
    "template": { 
            "name": "hello_world", 
            "language": { "code": "en_US" }
    }
}


response = requests.post(url, headers=header, json=data)
print(response.status_code)
print(response.json())
