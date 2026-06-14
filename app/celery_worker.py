from celery import Celery
import smtplib
from email.message import EmailMessage
from.config.config import setting

"""
import os

redis_host = os.getenv("REDIS_HOST","localhost")


celery_app = Celery("devcollab",broker=f"redis://{redis_host}:6379/0",backend=f"redis://{redis_host}:6379/0")

"""


import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "devcollab",
    broker=redis_url,
    backend=redis_url,
)


@celery_app.task
def send_email(to_email,subject,body):
    msg = EmailMessage()
    msg["From"] = setting.email_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(setting.email_address,setting.email_password)
        smtp.send_message(msg)

    return f"Email sent to {to_email}"