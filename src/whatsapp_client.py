import os
import httpx

def get_base_url():
    """Helper to get the correct Meta API URL for your phone number."""
    phone_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    return f"https://graph.facebook.com/v21.0/{phone_id}"

def get_headers():
    """Helper to get the authorization headers."""
    token = os.environ["WHATSAPP_ACCESS_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def send_message(to_number: str, text: str):
    """Sends a text message back to the WhatsApp user."""
    url = f"{get_base_url()}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    response = httpx.post(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return response.json()

def mark_as_read(message_id: str):
    """Marks the incoming message as 'Read' (Blue ticks) so the user knows we got it."""
    url = f"{get_base_url()}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    response = httpx.post(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return response.json()

def download_voice_note(media_id: str) -> bytes:
    """Downloads the actual audio file (.ogg) from Meta's servers."""
    token = os.environ["WHATSAPP_ACCESS_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Meta only gives us a temporary URL first
    url = f"https://graph.facebook.com/v21.0/{media_id}"
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    media_url = response.json()["url"]
    
    # Step 2: Download the actual bytes from the temporary URL
    audio_response = httpx.get(media_url, headers=headers)
    audio_response.raise_for_status()
    
    return audio_response.content
