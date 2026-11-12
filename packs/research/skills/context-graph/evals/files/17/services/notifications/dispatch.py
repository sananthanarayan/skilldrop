import logging

from services.notifications.email.sender import send_email
from services.notifications.render import render
from services.notifications.retry import with_retry

log = logging.getLogger(__name__)

EVENT_TEMPLATES = {
    ("user-events", "user.signed_up"): "welcome.html",
    ("invoice-events", "invoice.issued"): "invoice_issued.html",
}


def dispatch(topic, event):
    template = EVENT_TEMPLATES.get((topic, event["type"]))
    if template is None:
        return
    html = render(template, event["data"])
    message_id = with_retry(lambda: send_email(event["data"]["email"], event["subject"], html))
    log.info("sent template=%s event_id=%s provider_message_id=%s", template, event["id"], message_id)
