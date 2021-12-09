from django.conf import settings

from notifications_python_client.notifications import (
    NotificationsAPIClient,
)


notification_client = NotificationsAPIClient(
    settings.GOVUK_NOTIFY_API_KEY,
)


def email(email_address, template_id, personalisation):
    message_response = notification_client.send_email_notification(
        email_address=email_address,
        template_id=template_id,
        personalisation=personalisation,
    )

    return message_response
