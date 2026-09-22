import hashlib
import hmac
import uuid
from datetime import datetime, timezone

import requests
from flask import current_app

SOLAPI_ENDPOINT = "https://api.solapi.com/messages/v4/send"


def _build_auth_header(api_key, api_secret):
    date = datetime.now(timezone.utc).isoformat()
    salt = uuid.uuid4().hex
    signature = hmac.new(
        api_secret.encode("utf-8"), (date + salt).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return (
        f"HMAC-SHA256 apiKey={api_key}, date={date}, salt={salt}, signature={signature}"
    )


def send_verification_sms(to_phone, text):
    config = current_app.config
    headers = {
        "Authorization": _build_auth_header(config["SOLAPI_API_KEY"], config["SOLAPI_API_SECRET"]),
        "Content-Type": "application/json",
    }
    payload = {
        "message": {
            "to": to_phone,
            "from": config["SOLAPI_SENDER"],
            "text": text,
        }
    }
    response = requests.post(SOLAPI_ENDPOINT, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
