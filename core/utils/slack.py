from typing import Optional

from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web.slack_response import SlackResponse


class FailedToInitializeSlackClient(Exception):
    pass


def get_slack_client() -> WebClient:
    if not settings.SLACK_API_TOKEN:
        raise FailedToInitializeSlackClient()

    slack_token = settings.SLACK_API_TOKEN
    return WebClient(token=slack_token)


class FailedToSendSlackMessage(Exception):
    pass


def send_slack_message(
    *, channel_id: str, message_content: str, thread_ts: Optional[str] = None
) -> SlackResponse:
    """
    Send a slack message
    Use tread_ts if you would like to respond to a thread.
    """

    try:
        client = get_slack_client()
    except FailedToInitializeSlackClient:
        raise FailedToSendSlackMessage("Failed to initialize Slack client")

    # Post a message to the Channel
    try:
        thread_response = client.chat_postMessage(
            channel=channel_id,
            text=message_content,
            thread_ts=thread_ts,
        )
    except SlackApiError:
        raise FailedToSendSlackMessage("Unexpected error communicating with Slack API")

    assert thread_response.status_code == 200

    # Return the response
    return thread_response
