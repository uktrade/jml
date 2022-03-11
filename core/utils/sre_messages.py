from django.conf import settings
from django.urls import reverse
from slack_sdk.web.slack_response import SlackResponse

from core.utils.slack import FailedToSendSlackMessage, send_slack_message
from leavers.models import LeavingRequest


class FailedToSendSREAlertMessage(Exception):
    pass


def send_sre_alert_message(*, leaving_request: LeavingRequest) -> SlackResponse:
    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSREAlertMessage("SLACK_SRE_CHANNEL_ID is not set")

    try:
        leaving_request_path = reverse(
            "sre-confirmation", kwargs={"leaving_request_id": leaving_request.uuid}
        )

        leaver_name = leaving_request.get_leaver_name()

        if leaving_request.last_day:
            leaving_date = leaving_request.last_day.strftime("%d/%m/%Y")

            message_content = (
                f"{leaver_name} is leaving DIT on the {leaving_date}, please"
                f"remove their access from tools and services. "
                f"Confirm removal on "
                f"{settings.SITE_URL}{leaving_request_path}."
            )
        else:
            # TODO: Discuss this messaging?
            message_content = (
                f"{leaver_name} is leaving DIT, please remove their "
                "access from tools and services. Confirm removal on "
                f"{settings.SITE_URL}{leaving_request_path}."
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
