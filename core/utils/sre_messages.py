from django.conf import settings
from django.urls import reverse
from slack_sdk.web.slack_response import SlackResponse

from core.utils.slack import FailedToSendSlackMessage, send_slack_message
from leavers.models import LeavingRequest


class FailedToSendSREAlertMessage(Exception):
    pass


def send_sre_alert_message(*, leaving_request: LeavingRequest) -> SlackResponse:
    assert leaving_request.leaving_date

    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSREAlertMessage("SLACK_SRE_CHANNEL_ID is not set")

    try:
        leaving_request_path = reverse(
            "sre-confirmation", kwargs={"leaving_request_id": leaving_request.uuid}
        )

        leaver_name = leaving_request.get_leaver_name()
        leaving_date = leaving_request.leaving_date.strftime("%d/%m/%Y")

        message_content = (
            f"{leaver_name} is leaving DIT\n"
            "\n"
            "*Actions required:*\n"
            f"We need you to confirm that {leaver_name}'s access to tools "
            "and services has been managed. This will complete their "
            f"off-boarding. ({settings.SITE_URL}{leaving_request_path}).\n"
            "\n"
            f"*Deadline: {leaving_date}*\n"
            f"Please action this request by {leaver_name}’s last working "
            f"day in the department which is {leaving_date}.\n"
            "\n"
            "DIT Leavers Service"
        )

        return send_slack_message(
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=message_content,
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSREAlertMessage("There is an issue sending a Slack message")


class FailedToSendSRECompleteMessage(Exception):
    pass


def send_sre_complete_message(
    *, thread_ts: str, leaving_request: LeavingRequest
) -> SlackResponse:

    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSRECompleteMessage("SLACK_SRE_CHANNEL_ID is not set")

    leaver_name = leaving_request.get_leaver_name()

    try:
        return send_slack_message(
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=f"Thank you for completing the "
            f"SRE leaving process for {leaver_name}",
            thread_ts=thread_ts,
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSRECompleteMessage(
            "There is an issue sending a Slack message"
        )
