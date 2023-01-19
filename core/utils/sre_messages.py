from typing import TYPE_CHECKING, Dict, Optional

from django.conf import settings
from django.urls import reverse
from slack_sdk.web.slack_response import SlackResponse

from core.utils.helpers import DATE_FORMAT_STR, make_possessive
from core.utils.slack import FailedToSendSlackMessage, send_slack_message
from leavers.models import SlackMessage
from leavers.workflow.tasks import EmailIds

if TYPE_CHECKING:
    from leavers.models import LeavingRequest


def send_slack_message_for_leaving_request(
    *,
    leaving_request: "LeavingRequest",
    channel_id: str,
    message_content: str,
) -> SlackResponse:
    thread_ts: Optional[str] = None

    # If there is a Slack message already, use the timestamp to thread the message
    first_slack_message = leaving_request.slack_messages.order_by("-created_at").first()
    if first_slack_message:
        thread_ts = first_slack_message.slack_timestamp

    # Send the message
    slack_response = send_slack_message(
        channel_id=channel_id,
        message_content=message_content,
        thread_ts=thread_ts,
    )

    # Log the message against the LeavingRequest
    slack_timestamp = ""
    if type(slack_response.data) == dict:
        slack_timestamp = slack_response.data["ts"]

    SlackMessage.objects.create(
        slack_timestamp=slack_timestamp,
        leaving_request=leaving_request,
        channel_id=channel_id,
    )
    return slack_response


class FailedToSendSREAlertMessage(Exception):
    pass


def send_sre_alert_message(*, leaving_request: "LeavingRequest") -> SlackResponse:
    leaving_date = leaving_request.get_leaving_date()

    assert leaving_date

    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSREAlertMessage("SLACK_SRE_CHANNEL_ID is not set")

    try:
        leaving_request_path = reverse(
            "sre-detail", kwargs={"leaving_request_uuid": leaving_request.uuid}
        )

        leaver_name = leaving_request.get_leaver_name()
        leaving_date_str = leaving_date.date().strftime(DATE_FORMAT_STR)

        message_content = (
            f"{leaver_name} is leaving DIT\n"
            "\n"
            "*Actions required:*\n"
            f"We need you to confirm that {leaver_name}'s access to tools "
            "and services has been managed. This will complete their "
            f"offboarding. ({settings.SITE_URL}{leaving_request_path}).\n"
            "\n"
            "Please take any relevant actions on this record on the first "
            f"working day after {leaver_name}’s leaving date "
            f"{leaving_date_str}.\n"
            "\n"
            f"{settings.SERVICE_NAME}"
        )

        return send_slack_message_for_leaving_request(
            leaving_request=leaving_request,
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=message_content,
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSREAlertMessage("There is an issue sending a Slack message")


class FailedToSendSREReminderMessage(Exception):
    pass


def send_sre_reminder_message(
    *, email_id: "EmailIds", leaving_request: "LeavingRequest"
) -> Optional[SlackResponse]:
    """
    Send the SRE team a slack message to match the reminder email.
    """

    # Slack message content mapping
    email_id_mapping: Dict[EmailIds, str] = {
        EmailIds.SRE_REMINDER_DAY_AFTER_LWD: (
            "Yesterday was the date given as {possessive_leaver_name} "
            "last working day in DIT.\n"
            "\n"
            "Please ensure that their record on the Leaving Service is updated "
            "to show that their access to DIT services and tools has been removed.\n"
            "{sre_team_link}"
            "\n"
            "This should happen as soon as possible to avoid the risk of a "
            "security breach."
        ),
        EmailIds.SRE_REMINDER_ONE_DAY_AFTER_LD: (
            "Our records show that {possessive_leaver_name} access to DIT tools "
            "and systems has not been removed.\n"
            "\n"
            "They left DIT yesterday.\n"
            "\n"
            "This is now being classed as an ongoing security risk."
            "\n"
            "What you need to do:\n"
            "Please process this record today to confirm that "
            "{possessive_leaver_name} access to all of their DIT tools and "
            "systems has been removed.\n"
            "{sre_team_link}"
        ),
        EmailIds.SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC: (
            "Our records show that {possessive_leaver_name} access to DIT tools "
            "and systems still has not been removed.\n"
            "\n"
            "As mentioned in our message yesterday, this is now being classed as "
            "an ongoing security risk.\n"
            "\n"
            "What you need to do:\n"
            "This is your last chance to process this record to confirm that "
            "{possessive_leaver_name} access to all of their DIT tools and "
            "systems has been removed. If not done, it will be marked as not "
            "completed and escalated.\n"
            "{sre_team_link}"
        ),
    }

    if email_id not in email_id_mapping:
        return None

    leaver_name = leaving_request.get_leaver_name()
    possessive_leaver_name = ""
    if leaver_name:
        possessive_leaver_name = make_possessive(leaver_name)

    site_url = settings.SITE_URL
    sre_team_link = site_url + reverse(
        "sre-detail", kwargs={"leaving_request_uuid": leaving_request.uuid}
    )

    try:
        return send_slack_message_for_leaving_request(
            leaving_request=leaving_request,
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=email_id_mapping[email_id].format(
                leaver_name=leaver_name,
                possessive_leaver_name=possessive_leaver_name,
                sre_team_link=sre_team_link,
            ),
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSREReminderMessage(
            "There is an issue sending a Slack message"
        )


class FailedToSendSRECompleteMessage(Exception):
    pass


def send_sre_complete_message(*, leaving_request: "LeavingRequest") -> SlackResponse:
    if not settings.SLACK_SRE_CHANNEL_ID:
        raise FailedToSendSRECompleteMessage("SLACK_SRE_CHANNEL_ID is not set")

    leaver_name = leaving_request.get_leaver_name()

    try:
        return send_slack_message_for_leaving_request(
            leaving_request=leaving_request,
            channel_id=settings.SLACK_SRE_CHANNEL_ID,
            message_content=f"Thank you for completing the "
            f"SRE leaving process for {leaver_name}",
        )
    except FailedToSendSlackMessage:
        raise FailedToSendSRECompleteMessage(
            "There is an issue sending a Slack message"
        )
