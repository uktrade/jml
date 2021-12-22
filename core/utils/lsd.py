from django.conf import settings
from zenpy import Zenpy  # /PS-IGNORE
from zenpy.lib.api_objects import Ticket


def get_zendesk_client() -> Zenpy:
    creds = {
        "email": settings.LSD_ZENDESK_EMAIL,  # /PS-IGNORE
        "token": settings.LSD_ZENDESK_TOKEN,  # /PS-IGNORE
        "subdomain": settings.LSD_ZENDESK_SUBDOMAIN,
    }
    return Zenpy(**creds)


def inform_lsd_team_of_leaver(leaver_name: str, leaver_email: str) -> Ticket:
    client = get_zendesk_client()
    # Create a Zendesk Ticket /PS-IGNORE
    ticket: Ticket = client.tickets.create(
        subject=f"{leaver_name} has left DIT",
        comment=(  # /PS-IGNORE
            f"{leaver_name} has left DIT, please deactivate the "
            f"Gsuite account {leaver_email}."  # /PS-IGNORE
        ),
        priority="normal",
        type="task",
        status="new",
        requester=client.users.me,
    )
    return ticket
