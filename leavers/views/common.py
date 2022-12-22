from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse, reverse_lazy

from core.utils.helpers import make_possessive
from core.utils.staff_index import get_staff_document_from_staff_index
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

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(full_width=True)
        return form_kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            offboard_url=reverse("leaver-select-leaver"),
        )
        return context


class LeavingRequestView(
    UserPassesTestMixin, BaseTemplateView, LeavingRequestViewMixin
):
    template_name = "leaving/common/leaving_request.html"
    back_link_url = reverse_lazy("leaving-requests-list")

    def test_func(self) -> Optional[bool]:
        user = cast(User, self.request.user)
        return user.has_perm("leavers.select_leaver")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        staff_document = get_staff_document_from_staff_index(
            sso_email_user_id=self.leaving_request.leaver_activitystream_user.email_user_id,
        )

        context.update(
            page_title=f"{possessive_leaver_name} leaving request",
            leaving_request=self.leaving_request,
            continue_offboarding_link=reverse("leaver-select-leaver"),
            staff_uuid=staff_document.uuid,
        )

        return context
