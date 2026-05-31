import modal
from src.main import app, image, secrets

# Imports
from src.services.whatsapp.whatsapp_client import send_message, download_voice_note, mark_as_read
from src.services.audio.transcriber import transcribe
from src.core.router import classify_intent
from src.services.llm.extractor import extract_order
from src.services.sheets.sheets import append_order
from src.services.llm.rag import answer_question


# modal app with secrets loaded
@app.function(image=image, secrets=secrets)
def process_message(sender: str, msg_type: str, msg_data: dict):
    """The start of  Silai Copilot."""
    try:
        # message received
        mark_as_read(msg_data["id"])

        # Check if the message is already processed (persistent deduplication)
        from src.services.sheets.sheets import is_message_processed

        if is_message_processed(msg_data["id"], sender):
            print(
                f"[DEDUPLICATION] Message {msg_data['id']} from {sender} was already processed. Skipping duplicate.",
                flush=True,
            )
            return

        send_message(sender, "Processing")

        # Conversion(audio) or process
        if msg_type == "audio":
            audio_bytes = download_voice_note(msg_data["audio"]["id"])
            transcript = transcribe(audio_bytes)
        elif msg_type == "text":
            transcript = msg_data["text"]["body"]
        else:
            send_message(sender, "Sirf voice note ya text bhejiye.")
            return

        # Intent Classification
        intent = classify_intent(transcript)

        #  IF ORDER: Process new order
        if intent == "ORDER":
            order = extract_order(transcript)

            # Save to Google Sheets (append_order now handles C-xxx and O-xxx ID generation)
            try:
                append_order(order)
            except ValueError as e:
                if str(e) == "DUPLICATE_ORDER":
                    send_message(
                        sender,
                        f"📋 Yeh order pehle se save hai! (Order ID: {order.order_id}) 😊",
                    )
                    return
                raise e

            # Build a nice reply to send back to WhatsApp
            m = order.measurements
            reply = f"✅ {order.customer_name} ji ka order save ho gaya!\n"
            reply += f"📋 Order ID: {order.order_id}\n"
            reply += f"👗 Garment: {order.garment_type}\n"
            reply += f"📏 Measurements:\n"
            if m.chest:
                reply += f'  • Chhati: {m.chest}"\n'
            if m.waist:
                reply += f'  • Kamar: {m.waist}"\n'
            if m.hip:
                reply += f'  • Hip: {m.hip}"\n'
            if m.shoulder:
                reply += f'  • Kandha: {m.shoulder}"\n'
            if m.sleeve_length:
                reply += f'  • Baju: {m.sleeve_length}"\n'
            if m.garment_length:
                reply += f'  • Lambai: {m.garment_length}"\n'
            if m.salwar_length:
                reply += f'  • Salwar Len: {m.salwar_length}"\n'
            if m.mori:
                reply += f'  • Mori: {m.mori}"\n'

            if order.delivery_date:
                reply += f"\n📅 Delivery: {order.delivery_date}\n"
            if order.special_instructions:
                reply += f"📝 Notes: {order.special_instructions}\n"

            reply += f"\nKoi galti ho toh bata dijiye, sahi kar denge! 😊"

            # Send the final receipt
            send_message(sender, reply)

        # 4b. IF QUESTION: Read the spreadsheet and answer
        elif intent == "QUESTION":
            answer = answer_question(transcript)
            send_message(sender, answer)

    except Exception as e:
        # If anything goes wrong (like a parsing error), don't crash silently
        send_message(
            sender, "😅 Maaf kijiye, kuch gadbad ho gayi. Ek baar phir se bolenge?"
        )
        print(f"Error processing message: {e}")
