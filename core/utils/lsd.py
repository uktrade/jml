import logging

from django.conf import settings
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket

from leavers.models import LeavingRequest

logger = logging.getLogger(__name__)


def get_zendesk_client() -> Zenpy:
    creds = {
        "email": settings.LSD_ZENDESK_EMAIL,
        "token": settings.LSD_ZENDESK_TOKEN,
        "subdomain": settings.LSD_ZENDESK_SUBDOMAIN,
    }
    return Zenpy(**creds)


def inform_lsd_team_of_leaver(leaving_request: LeavingRequest):
    leaver_name = leaving_request.get_leaver_name()
    if not leaver_name:
        raise Exception("No leaver name is set on the Leaving Request")

    leaver_email = leaving_request.get_leaver_email()
    if not leaver_email:
        raise Exception("No leaver email is set on the Leaving Request")

    leaving_date = leaving_request.get_leaving_date()
    if not leaving_date:
        raise Exception("No leaving date is set on the Leaving Request")
    leaving_date_str = leaving_date.strftime("%d/%m/%Y")

    if not settings.PROCESS_LEAVING_REQUEST:
        logger.warning(f"Creating zendesk ticket for LSD team regarding {leaver_name}")
        return None

    client = get_zendesk_client()
    # Create a Zendesk Ticket /PS-IGNORE
    client.tickets.create(
        Ticket(
            subject=f"Notification of Leaver: {leaver_name}",
            comment=(
                "We have been informed that the following person is "
                "leaving/has left the department.\n"
                f"Name: {leaver_name}\n"
                f"Email: {leaver_email}\n"
                f"Date of Leaving: {leaving_date_str}\n"
                "Please ensure that permissions are removed for this user "
                "(where appropriate. SSO, Datahub, Digital Worskspace, OKTA)."
            ),
            priority="normal",
            type="task",
            status="new",
            requester=client.users.me(),
        )
    )

    leaving_request.task_logs.create(
        task_name="LSD team informed of leaver via Zendesk",
    )
