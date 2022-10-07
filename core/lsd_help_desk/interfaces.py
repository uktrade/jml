import logging
from abc import ABC, abstractmethod

from django.conf import settings
from help_desk_client import get_help_desk_interface
from help_desk_client.interfaces import (
    HelpDeskComment,
    HelpDeskTicket,
    Priority,
    Status,
    TicketType,
)

from core.utils.helpers import DATE_FORMAT_STR
from leavers.models import LeavingRequest

logger = logging.getLogger(__name__)


class LSDHelpDeskBase(ABC):
    @abstractmethod
    def inform_lsd_team_of_leaver(self, leaving_request: LeavingRequest):
        raise NotImplementedError


class LSDHelpDeskStubbed(LSDHelpDeskBase):
    def inform_lsd_team_of_leaver(self, leaving_request: LeavingRequest):
        leaving_request.task_logs.create(
            task_name="LSD team informed of leaver via the help desk (stubbed)",
        )


class LSDHelpDesk(LSDHelpDeskBase):
    def __init__(self) -> None:
        super().__init__()
        help_desk_interface = get_help_desk_interface(settings.HELP_DESK_INTERFACE)
        self.help_desk = help_desk_interface(credentials=settings.HELP_DESK_CREDS)

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
        leaving_date_str = leaving_date.strftime(DATE_FORMAT_STR)

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

        user = self.help_desk.get_or_create_user()
        datahub_group = None
        for group in user.groups:
            if group.name == "Datahub":
                datahub_group = group
                break

        self.help_desk.create_ticket(
            HelpDeskTicket(
                subject=f"Notification of Leaver: {leaver_name}",
                comment=HelpDeskComment(
                    body=comment_body,
                ),
                priority=Priority.NORMAL,
                ticket_type=TicketType.TASK,
                status=Status.NEW,
                group_id=datahub_group.id,
            )
        )

        leaving_request.task_logs.create(
            task_name="LSD team informed of leaver via help desk",
        )
