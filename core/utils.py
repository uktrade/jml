from slack_sdk.webhook import WebhookClient

from django.conf import settings


def send_slack_message(message_content):
    url = settings.SLACK_WEB_HOOK
    webhook = WebhookClient(url)

    response = webhook.send(text=message_content)
    assert response.status_code == 200
    assert response.body == "ok"
