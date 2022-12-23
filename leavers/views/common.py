from typing import TYPE_CHECKING, Optional, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy

from core.utils.helpers import make_possessive
from core.views import BaseTemplateView
from leavers.views.base import LeavingRequestListing, LeavingRequestViewMixin

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


class LeavingRequestListView(UserPassesTestMixin, LeavingRequestListing):
    template_name = "leaving/common/leaving_request_list.html"

    complete_field = "line_manager_complete"
    # These views will contain the task list for HR to complete/review what was done
    confirmation_view = "leaving-request-summary"
    summary_view = "leaving-request-summary"

    def test_func(self) -> Optional[bool]:
        user = cast(User, self.request.user)
        return user.has_perm("leavers.select_leaver")


class LeavingRequestView(BaseTemplateView, LeavingRequestViewMixin):
    template_name = "leaving/common/leaving_request.html"
    back_link_url = reverse_lazy("leaving-requests-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        context.update(page_title=f"{possessive_leaver_name} leaving request")

        return context
