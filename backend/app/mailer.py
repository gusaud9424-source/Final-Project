import smtplib
from email.header import Header
from email.mime.text import MIMEText

from flask import current_app


def send_verification_email(to_address, subject, body):
    config = current_app.config
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = config["GMAIL_ADDRESS"]
    message["To"] = to_address

    with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as server:
        if config["MAIL_USE_TLS"]:
            server.starttls()
        server.login(config["GMAIL_ADDRESS"], config["GMAIL_APP_PASSWORD"])
        server.send_message(message)
