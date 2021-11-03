from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from django.conf import settings


slack_token = settings.SLACK_API_TOKEN
client = WebClient(token=slack_token)


def send_slack_message(message_content):
    channel_id = "TODO"

    try:
        result = client.chat_postMessage(
            channel=channel_id,
            text=message_content
        )
        print(result)

    except SlackApiError as e:
        print(f"Error posting message: {e}")
