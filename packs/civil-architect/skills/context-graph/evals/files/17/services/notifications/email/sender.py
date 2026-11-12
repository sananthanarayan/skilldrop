"""Email delivery through the provider's HTTPS send API."""
import os

import requests

SEND_URL = "https://api.mail-provider.example.invalid/v3/send"


def send_email(to, subject, html):
    response = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {os.environ['MAIL_API_KEY']}"},
        json={"to": to, "subject": subject, "html": html},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["message_id"]
