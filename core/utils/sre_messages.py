from django.conf import settings
from django.shortcuts import reverse

from slack_sdk.web.slack_response import SlackResponse

from core.utils.slack import FailedToSendSlackMessage, send_slack_message


class FailedToSendSREAlertMessage(Exception):
    pass


def send_sre_alert_message(*, leaving_request: object) -> SlackResponse:
    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSREAlertMessage("SLACK_SRE_CHANNEL_ID is not set")

    try:
        leaving_request_path = reverse(
            "sre-confirmation",
            kwargs={"leaving_request_id": leaving_request.uuid}
        )

        message_content = (
            f"Please carry out leaving tasks for "
            f"{leaving_request.leaver_first_name} "
            f"{leaving_request.leaver_last_name}. "
            f"Please visit {settings.SITE_URL}{leaving_request_path} to update "
            "the status of these tasks."
        )

        return send_slack_message(
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=message_content,
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
