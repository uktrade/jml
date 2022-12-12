from typing import Optional

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse

from .base import LeavingRequestListing


class LeavingRequestListView(UserPassesTestMixin, LeavingRequestListing):
    template_name = "leaving/common/leaving_request_list.html"

    complete_field = "line_manager_complete"
    # These views will contain the task list for HR to complete/review what was done
    confirmation_view = "leaving-request-summary"
    summary_view = "leaving-request-summary"

    def test_func(self) -> Optional[bool]:
        return self.request.user.has_perm("leavers.select_leaver")


def empty_view(request, *args, **kwargs):
    return HttpResponse("")
