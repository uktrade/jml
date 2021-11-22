from django.conf import settings
from slack_sdk.web.slack_response import SlackResponse

from core.utils.slack import FailedToSendSlackMessage, send_slack_message


class FailedToSendSREAlertMessage(Exception):
    pass


def send_sre_alert_message(*, first_name: str, last_name: str) -> SlackResponse:
    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSREAlertMessage("SLACK_SRE_CHANNEL_ID is not set")

    try:
        return send_slack_message(
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=f"Please carry out leaving tasks for {first_name} {last_name}",
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSREAlertMessage("There is an issue sending a Slack message")


class FailedToSendSRECompleteMessage(Exception):
    pass


def send_sre_complete_message(*, thread_ts: str) -> SlackResponse:
    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSRECompleteMessage("SLACK_SRE_CHANNEL_ID is not set")

    try:
        return send_slack_message(
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content="SRE Complete message",
            thread_ts=thread_ts,
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSRECompleteMessage(
            "There is an issue sending a Slack message"
        )
