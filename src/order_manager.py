import modal

from src.app import app, image, secrets


@app.function(image=image, secrets=secrets)
def process_message(sender: str, msg_type: str, msg_data: dict):
    print(f"Received background process trigger for {sender} - {msg_type}")
