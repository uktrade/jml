from datetime import datetime


class MockZenpyUser(object):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.email = kwargs.get("email")


class MockZenpyTicket(object):
    def __init__(self, ticket_id, requester=None):
        self.id = ticket_id
        self.status = "open"
        self.description = "fakedescription"
        self.subject = "fakesubject"
        self.requester_id = 1234
        self.type = "task"
        self.requester = requester


class MockZenpyTicketAudit(object):
    def __init__(self, ticket):
        self.ticket = ticket


class MockZenpyUserResponse(object):
    def __init__(self, user_id):
        self.id = user_id


class MockZenpyAPI(object):
    """Aid testing tickets without using Zendesk API directly. /PS-IGNORE"""

    class MockZenpyUsers(object):
        def __init__(self, parent, me=None):
            self._me = me
            self._next_userid = 1
            self.parent = parent

        def me(self):
            return self._me

    class MockZenpyTicketCRUD(object):
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
            return MockZenpyTicketAudit(ticket)

    def __init__(self, tickets=[], me=None, ticket_audit=None, users=[]):
        self.results = tickets
        self.users = self.MockZenpyUsers(self, me=me)
        self._tickets: dict[int, MockZenpyTicket] = dict(
            [(ticket.id, ticket) for ticket in tickets]
        )
        self.tickets = self.MockZenpyTicketCRUD(self, ticket_audit)

        for ticket in tickets:
            self._tickets[ticket.id] = ticket
