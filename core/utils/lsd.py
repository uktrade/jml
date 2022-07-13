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


def inform_lsd_team_of_leaver(leaver_name: str, leaver_email: str):
    if not settings.PROCESS_LEAVING_REQUEST:
        logger.warning(f"Creating zendesk ticket for LSD team regarding {leaver_name}")
        return None

    client = get_zendesk_client()
    # Create a Zendesk Ticket /PS-IGNORE
    client.tickets.create(
        subject=f"{leaver_name} has left DIT",
        comment=(
            f"{leaver_name} has left DIT, please deactivate the "
            f"Gsuite account {leaver_email}."
        ),
        priority="normal",
        type="task",
        status="new",
        requester=client.users.me,
    )
