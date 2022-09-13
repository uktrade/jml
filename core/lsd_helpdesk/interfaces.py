import logging
from abc import ABC, abstractmethod

from django.conf import settings
from helpdesk_client import get_helpdesk_interface
from helpdesk_client.interfaces import (
    HelpDeskComment,
    HelpDeskTicket,
    Priority,
    Status,
    TicketType,
)

from leavers.models import LeavingRequest

logger = logging.getLogger(__name__)
helpdesk_interface = get_helpdesk_interface(settings.LSD_HELP_DESK_INTERFACE)
helpdesk = helpdesk_interface(credentials=settings.LSD_HELP_DESK_CREDS)


class LSDHelpdeskBase(ABC):
    @abstractmethod
    def inform_lsd_team_of_leaver(self, leaving_request: LeavingRequest):
        raise NotImplementedError


class LSDHelpdeskStubbed(LSDHelpdeskBase):
    def inform_lsd_team_of_leaver(self, leaving_request: LeavingRequest):
        leaving_request.task_logs.create(
            task_name="LSD team informed of leaver via Helpdesk (stubbed)",
        )


class LSDHelpdesk(LSDHelpdeskBase):

    def inform_lsd_team_of_leaver(self, leaving_request: LeavingRequest):
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
            logger.warning(
                f"Creating zendesk ticket for LSD team regarding {leaver_name}"
            )
            return None

         # Create a helpdesk /PS-IGNORE
        comment_body = (
            "We have been informed that the following person is "
            "leaving/has left the department.\n"
            f"Name: {leaver_name}\n"
            f"Email: {leaver_email}\n"
            f"Date of Leaving: {leaving_date_str}\n"
            "Please ensure that permissions are removed for this user "
            "(where appropriate. SSO, Datahub, Digital Worskspace, OKTA)."
        )

        helpdesk.create_ticket(
            HelpDeskTicket(
                subject=f"Notification of Leaver: {leaver_name}",
                comment=HelpDeskComment(
                    body=comment_body,
                ),
                priority=Priority.NORMAL,
                ticket_type=TicketType.TASK,
                status=Status.NEW,
            )
        )

        leaving_request.task_logs.create(
            task_name="LSD team informed of leaver via Zendesk",
        )
