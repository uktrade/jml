import logging

from django.conf import settings
from zenpy import Zenpy

logger = logging.getLogger(__name__)


def get_zendesk_client() -> Zenpy:
    creds = {
        "email": settings.LSD_ZENDESK_EMAIL,
        "token": settings.LSD_ZENDESK_TOKEN,
        "subdomain": settings.LSD_ZENDESK_SUBDOMAIN,
    }
    return Zenpy(**creds)


def inform_lsd_team_of_leaver(leaver_name: str, leaver_email: str, leaving_date: str):
    if not settings.PROCESS_LEAVING_REQUEST:
        logger.warning(f"Creating zendesk ticket for LSD team regarding {leaver_name}")
        return None

    client = get_zendesk_client()
    # Create a Zendesk Ticket /PS-IGNORE
    client.tickets.create(
        subject=f"Notification of Leaver: {leaver_name}",
        comment=(
            "We have been informed that the following person is leaving/has left the department.\n"
            f"Name: {leaver_name}\n"
            f"Email: {leaver_email}\n"
            f"Date of Leaving: {leaving_date}\n"
            "Please ensure that permissions are removed for this user (where appropriate. SSO, "
            "Datahub, Digital Worskspace, OKTA)."
        ),
        priority="normal",
        type="task",
        status="new",
        requester=client.users.me,
    )
