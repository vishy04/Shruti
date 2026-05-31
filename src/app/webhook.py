# imports
import os
import logging
import hmac
import hashlib
import json

from fastapi import FastAPI, Query, status, Request, HTTPException
from fastapi.responses import PlainTextResponse

fastapi_app = FastAPI(title="Shruti Webhook API")
logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.INFO)

PROCESSED_MESSAGE_IDS = set()  # to avoid duplicate message ids(for handling)


# GET /webhook - one-time handshake
# https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint
@fastapi_app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    # challenge is for verification security (challenge-response)
    challenge: str = Query(None, alias="hub.challenge"),
):
    expected_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and token == expected_token:
        logger.info("Webhook verification successful!")
        return PlainTextResponse(challenge)  # return for verification to meta

    logger.warning("Wrong token")
    return PlainTextResponse("Forbidden", status_code=status.HTTP_403_FORBIDDEN)


@fastapi_app.get("/debug")
async def debug_sheet():
    from src.services.sheets.sheets_client import get_customers_ws, get_orders_ws

    cust_ws, ord_ws = get_customers_ws(), get_orders_ws()

    try:
        row_604 = ord_ws.row_values(604)
        headers = ord_ws.row_values(1)
        return {"row_604": row_604, "headers": headers}
    except Exception as e:
        return {"error": str(e)}


@fastapi_app.post("/webhook")
async def receive_webhook(request: Request):
    # something to do with verification ( see doc )
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    if not signature:
        logger.warning("Missing Signature Header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature Missing"
        )
    # parsing the signature comes as "sha256=HEX_DIGEST"
    try:
        sig_format, sig_hash = signature.split("=")
    except ValueError:
        logger.warning("Invalid Signature Header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Signature Header"
        )

    app_secret_raw = os.environ.get("WHATSAPP_APP_SECRET", "")
    print(
        f"[DEBUG SECRET] Loaded WHATSAPP_APP_SECRET length: {len(app_secret_raw)}",
        flush=True,
    )
    if app_secret_raw:
        print(
            f"[DEBUG SECRET] WHATSAPP_APP_SECRET preview: {app_secret_raw[:3]}...{app_secret_raw[-3:]}",
            flush=True,
        )
    else:
        print("[DEBUG SECRET] WHATSAPP_APP_SECRET is empty!", flush=True)

    app_secret = app_secret_raw.encode("utf-8")
    expected_hash = hmac.new(app_secret, body, hashlib.sha256).hexdigest()

    print(f"[DEBUG SECRET] Received sig_hash: {sig_hash}", flush=True)
    print(f"[DEBUG SECRET] Expected sig_hash: {expected_hash}", flush=True)

    if not hmac.compare_digest(sig_hash, expected_hash):
        logger.warning(
            f"Sign verification failed. Expected: {expected_hash}, got: {sig_hash}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature Mismatch"
        )

    # parsing payload(I hate this shit)

    payload = json.loads(body.decode("utf-8"))
    logger.info(f"Received payload: {json.dumps(payload, indent=2)}")

    # meta sends nested so unpacking
    # https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview/
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})  # dict
            messages = value.get("messages", [])
            for msg in messages:
                msg_id = msg.get("id")
                sender = msg.get("from")

                # authorization
                authorized_phone = os.environ.get("AUTHORIZED_PHONE")

                if authorized_phone and sender != authorized_phone:
                    logger.warning("Unauthorized access attempt")
                    continue

                # duplication check
                if msg_id in PROCESSED_MESSAGE_IDS:
                    logger.info("Skipping Duplicate message")
                    continue
                PROCESSED_MESSAGE_IDS.add(msg_id)

                msg_type = msg.get("type")
                logger.info(
                    f"Processing message {msg_id} of type {msg_type} from {sender}"
                )

                # spawn processing using Modal as whatsapp has 3 sec rule

                await process_message.spawn.aio(sender, msg_type, msg)

    return {"status": "ok"}


# fast_api app as Modal Function
# pyrefly: ignore [missing-import]
from src.main import app, image, secrets
from src.app.order_manager import process_message

import modal


@app.function(image=image, secrets=secrets)
@modal.asgi_app()
def webhook():
    return fastapi_app
