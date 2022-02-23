from enum import Enum
from typing import Dict

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient


class EmailTemplates(Enum):
    """
    GOV.UK Notify email Templates.
    """

    csu4_leaver_email = "csu4_leaver_email_tempalte_id"


notification_client = NotificationsAPIClient(
    settings.GOVUK_NOTIFY_API_KEY,
)


def email(email_address: str, template_id: EmailTemplates, personalisation: Dict):
    message_response = notification_client.send_email_notification(
        email_address=email_address,
        template_id=template_id.value,
        personalisation=personalisation,
    )

    return message_response
