from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.views.generic import FormView

from activity_stream.forms import ChoosePrimaryEmailForm
from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)

if TYPE_CHECKING:
    from user.models import User


class ChoosePrimaryEmailView(FormView):
    template_name = "activity_stream/choose_primary_email.html"
    form_class = ChoosePrimaryEmailForm

    def get_success_url(self) -> str:
        next: Optional[str] = None
        if "next" in self.request.GET:
            next = self.request.GET["next"]
        if "next" in self.request.POST:
            next = self.request.POST["next"]
        return next or "/"

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.activitystream_user: Optional[ActivityStreamStaffSSOUser] = None
        self.sso_emails: Optional[QuerySet[ActivityStreamStaffSSOUserEmail]] = None
        user = cast("User", self.request.user)
        try:
            self.activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                email_user_id=user.sso_email_user_id,
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            pass
        else:
            self.sso_emails = self.activitystream_user.sso_emails.all()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()

        if self.sso_emails:
            kwargs["email_addresses"] = [
                sso_email.email_address for sso_email in self.sso_emails
            ]

        return kwargs

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        if "next" in self.request.GET:
            initial["next"] = self.request.GET["next"]

        if self.activitystream_user:
            initial["email_address"] = self.activitystream_user.get_primary_email()

        return initial

    def form_valid(self, form) -> HttpResponse:
        assert self.activitystream_user
        assert self.sso_emails

        email_address = form.cleaned_data["email_address"]
        for sso_email in self.sso_emails:
            if sso_email.email_address == email_address:
                sso_email.is_primary = True
                sso_email.save()
                break

        return super().form_valid(form)
