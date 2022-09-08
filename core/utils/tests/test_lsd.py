from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone

import core.utils.lsd as lsd
from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from leavers.factories import LeavingRequestFactory
from user.test.factories import UserFactory


class FakeUser(object):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.email = kwargs.get("email")


class FakeTicket(object):
    def __init__(self, ticket_id, requester=None):
        self.id = ticket_id
        self.status = "open"
        self.description = "fakedescription"
        self.subject = "fakesubject"
        self.requester_id = 1234
        self.type = "task"
        self.requester = requester


class FakeTicketAudit(object):
    def __init__(self, ticket):
        self.ticket = ticket


class FakeUserResponse(object):
    def __init__(self, user_id):
        self.id = user_id


class FakeAPI(object):
    """Aid testing tickets without using Zendesk API directly. /PS-IGNORE"""

    class FakeUsers(object):
        def __init__(self, parent, me=None):
            self._me = me
            self._next_userid = 1
            self.parent = parent

        def me(self):
            return self._me

    class FakeTicketCRUD(object):
        def __init__(self, parent, ticket_audit=None):
            self.ticket_audit = ticket_audit
            self._next_ticket_id = 1
            self.parent = parent

        def create(self, ticket):
            """Pretend to create a zendesk ticket and return the canned
            result.
            """
            ticket.id = self._next_ticket_id
            ticket.created_at = datetime.now()
            self.parent._tickets[ticket.id] = ticket
            self._next_ticket_id += 1
            return FakeTicketAudit(ticket)

    def __init__(self, tickets=[], me=None, ticket_audit=None, users=[]):
        self.results = tickets
        self.users = self.FakeUsers(self, me=me)
        self._tickets: dict[int, FakeTicket] = dict(
            [(ticket.id, ticket) for ticket in tickets]
        )
        self.tickets = self.FakeTicketCRUD(self, ticket_audit)

        for ticket in tickets:
            self._tickets[ticket.id] = ticket


fake_user = FakeUser(
    id=1234,
    name="Jim Example",  # /PS-IGNORE
    email="test@example.com",  # /PS-IGNORE
)


@mock.patch(
    "core.utils.lsd.Zenpy",
    return_value=FakeAPI(users=[fake_user], me=FakeUserResponse(1234)),
)
class TestInformLSDTeamOfLeaver(TestCase):
    def setUp(self) -> None:
        leaver = UserFactory()
        manager = UserFactory()
        leaving_date = timezone.now()
        self.leaving_request = LeavingRequestFactory(
            leaver_complete=leaving_date,
            last_day=leaving_date,
            leaving_date=leaving_date,
            leaver_activitystream_user=ActivityStreamStaffSSOUserFactory(
                email_user_id=leaver.sso_email_user_id
            ),
            manager_activitystream_user=ActivityStreamStaffSSOUserFactory(
                email_user_id=manager.sso_email_user_id
            ),
        )

    def test_no_leaving_date(self, mock_zenpy_client: mock.Mock):
        self.leaving_request.leaving_date = None

        with self.assertRaises(Exception):
            lsd.inform_lsd_team_of_leaver(leaving_request=self.leaving_request)
            self.assertEqual(mock_zenpy_client.call_count, 0)

    def test_success(self, mock_zenpy_client: mock.Mock):

        lsd.inform_lsd_team_of_leaver(
            leaving_request=self.leaving_request,
        )

        self.assertEqual(mock_zenpy_client.call_count, 1)
