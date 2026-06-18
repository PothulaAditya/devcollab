import resend
from celery import Celery
from .config.config import setting

celery_app = Celery(
    "devcollab",
    broker=setting.redis_url,
    backend=setting.redis_url,
)

resend.api_key = setting.resend_api_key


@celery_app.task
def send_email(to_email, subject, body):
    resend.Emails.send({
        "from": "DevCollab <noreply@adityapothula.dev>",
        "to": to_email,
        "subject": subject,
        "html": body,
    })