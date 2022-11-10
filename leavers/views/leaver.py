import uuid
from typing import Any, Dict, List, Literal, Optional, Type, cast

from django.conf import settings
from django.forms import Form
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView, TemplateView
from django.views.generic.edit import FormView

from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)
from core.people_data import get_people_data_interface
from core.people_finder import get_people_finder_interface
from core.service_now import get_service_now_interface
from core.staff_search.views import StaffSearchView
from core.types import Address
from core.uksbs import get_uksbs_interface
from core.utils.helpers import bool_to_yes_no, yes_no_to_bool
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    consolidate_staff_documents,
    get_csd_for_activitystream_user,
    get_staff_document_from_staff_index,
)
from leavers import types
from leavers.forms import leaver as leaver_forms
from leavers.forms.leaver import ReturnOptions
from leavers.models import LeaverInformation, LeavingRequest
from leavers.types import LeavingReason, StaffType
from leavers.utils.leaving_request import update_or_create_leaving_request
from leavers.workflow.utils import get_or_create_leaving_workflow
from user.models import User

LINE_MANAGER_SEARCH_PARAM = "line_manager_uuid"


class MultiplePersonIdErrorView(TemplateView):
    template_name = "leaving/multiple_person_id_errors.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(JML_TEAM_CONTACT_EMAIL=settings.JML_TEAM_CONTACT_EMAIL)
        return context


class LeaversStartView(TemplateView):
    template_name = "leaving/start.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(start_url=reverse("why-are-you-leaving"))
        return context


class MyManagerSearchView(StaffSearchView):
    search_name = "manager"
    query_param_name = LINE_MANAGER_SEARCH_PARAM
    success_url = reverse_lazy("leaver-dates")

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)
        try:
            leaver_activitystream_user = (
                ActivityStreamStaffSSOUser.objects.active().get(
                    email_user_id=user.sso_email_user_id,
                )
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find leaver in the Staff SSO ActivityStream.")

        self.exclude_staff_ids = [leaver_activitystream_user.identifier]
        return super().dispatch(request, *args, **kwargs)


class LeaverInformationMixin:
    people_finder_search = get_people_finder_interface()

    leaver_activitystream_user: Optional[ActivityStreamStaffSSOUser] = None
    leaving_request: Optional[LeavingRequest] = None
    leaver_info: Optional[LeaverInformation] = None

    def get_leaver_activitystream_user(
        self, sso_email_user_id: str
    ) -> ActivityStreamStaffSSOUser:
        if not self.leaver_activitystream_user:
            try:
                self.leaver_activity_stream_user = (
                    ActivityStreamStaffSSOUser.objects.active().get(
                        email_user_id=sso_email_user_id,
                    )
                )
            except ActivityStreamStaffSSOUser.DoesNotExist:
                raise Exception(
                    f"Unable to find leaver '{sso_email_user_id}' in the Staff SSO ActivityStream."
                )
        return self.leaver_activity_stream_user

    def get_leaving_request(
        self, sso_email_user_id: str, requester: User
    ) -> LeavingRequest:
        """
        Get the Leaving Request for the Leaver
        """

        if self.leaving_request and self.leaving_request.user_requesting == requester:
            return self.leaving_request

        leaver_activity_stream_user = self.get_leaver_activitystream_user(
            sso_email_user_id=sso_email_user_id,
        )

        self.leaving_request = update_or_create_leaving_request(
            leaver=leaver_activity_stream_user,
            user_requesting=requester,
        )

        return self.leaving_request

    def get_leaver_information(
        self, sso_email_user_id: str, requester: User
    ) -> LeaverInformation:
        """
        Get the Leaver information stored in the DB
        Creates a new model if one doesn't exist.
        """
        if self.leaver_info:
            return self.leaver_info

        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )

        (
            self.leaver_info,
            _,
        ) = LeaverInformation.objects.prefetch_related().get_or_create(
            leaving_request=leaving_request,
            defaults={"updates": {}},
        )
        return self.leaver_info

    def store_display_screen_equipment(
        self,
        sso_email_user_id: str,
        requester: User,
        dse_assets: List[types.DisplayScreenEquipmentAsset],
    ) -> None:
        """
        Store DSE assets
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=requester
        )
        leaver_info.dse_assets = dse_assets
        leaver_info.save(update_fields=["dse_assets"])

    def store_cirrus_kit_information(
        self,
        sso_email_user_id: str,
        requester: User,
        cirrus_assets: List[types.CirrusAsset],
    ) -> None:
        """
        Store the Correction information
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=requester
        )

        leaver_info.cirrus_assets = cirrus_assets
        leaver_info.save(
            update_fields=[
                "cirrus_assets",
            ]
        )

        if not cirrus_assets:
            # clear any existing cirrus kit information if there is no kit.
            self.store_return_option(
                sso_email_user_id=sso_email_user_id,
                requester=requester,
                return_option=None,
            )
            self.store_return_information(
                sso_email_user_id=sso_email_user_id,
                requester=requester,
                personal_phone=None,
                contact_email=None,
                address=None,
            )

    def store_return_option(
        self, sso_email_user_id: str, requester: User, return_option: Optional[str]
    ) -> None:
        """
        Store the selected return option.

        return_option is a value from ReturnOptions.
        """
        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=requester
        )

        leaver_info.return_option = return_option
        leaver_info.save(update_fields=["return_option"])

    def store_return_information(
        self,
        sso_email_user_id: str,
        requester: User,
        personal_phone: Optional[str],
        contact_email: Optional[str],
        address: Optional[Address],
    ) -> None:
        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=requester
        )
        leaver_info.return_personal_phone = personal_phone
        leaver_info.return_contact_email = contact_email

        # Reset address fields
        leaver_info.return_address_line_1 = None
        leaver_info.return_address_line_2 = None
        leaver_info.return_address_city = None
        leaver_info.return_address_county = None
        leaver_info.return_address_postcode = None

        if address:
            leaver_info.return_address_line_1 = address["line_1"]
            leaver_info.return_address_line_2 = address["line_2"]
            leaver_info.return_address_city = address["town_or_city"]
            leaver_info.return_address_county = address["county"]
            leaver_info.return_address_postcode = address["postcode"]

        # Save leaver information
        leaver_info.save(
            update_fields=[
                "return_personal_phone",
                "return_contact_email",
                "return_address_line_1",
                "return_address_line_2",
                "return_address_city",
                "return_address_county",
                "return_address_postcode",
            ]
        )

    def create_workflow(self, sso_email_user_id: str, requester: User):
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=requester
        )
        get_or_create_leaving_workflow(
            leaving_request=leaving_request,
            executed_by=requester,
        )


class WhyAreYouLeavingView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/why_are_you_leaving.html"
    form_class = leaver_forms.WhyAreYouLeavingForm
    success_url = reverse_lazy("leaving-reason-unhandled")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation
    leaving_reason: Optional[LeavingReason] = None

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        reason: str = form.cleaned_data["reason"]

        if reason != "none_of_the_above":
            self.leaving_reason = LeavingReason(reason)

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="Why are you leaving DIT?")
        return context

    def get_success_url(self) -> str:
        reason_mapping = {
            LeavingReason.RESIGNATION: reverse_lazy("staff-type"),
            LeavingReason.RETIREMENT: reverse_lazy("leaving-reason-unhandled"),
            LeavingReason.TRANSFER: reverse_lazy("leaving-reason-unhandled"),
        }
        if self.leaving_reason in reason_mapping:
            return reason_mapping[self.leaving_reason]

        return super().get_success_url()


class UnhandledLeavingReasonView(LeaverInformationMixin, TemplateView):
    template_name = "leaving/leaver/unhandled_reason.html"

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="This service is unavailable")
        return context


class StaffTypeView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/staff_type.html"
    form_class = leaver_forms.StaffTypeForm
    success_url = reverse_lazy("employment-profile")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial.update(
            staff_type=self.leaving_request.staff_type,
        )

        return initial

    def form_valid(self, form) -> HttpResponse:
        staff_type = StaffType(form.cleaned_data["staff_type"])

        if staff_type == StaffType.FAST_STREAMERS:
            self.success_url = reverse_lazy("leaver-fast-streamer")
        else:
            self.leaving_request.staff_type = staff_type
            self.leaving_request.save(update_fields=["staff_type"])

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="How are you employed by DIT?")
        return context


class LeaverFastStreamerView(LeaverInformationMixin, TemplateView):
    template_name = "leaving/leaver/fast_streamer.html"

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="This service is unavailable")
        return context


class EmploymentProfileView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/employment_profile.html"
    form_class = leaver_forms.EmploymentProfileForm
    success_url = reverse_lazy("leaver-find-details")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial.update(
            first_name=self.leaver_info.leaver_first_name,
            last_name=self.leaver_info.leaver_last_name,
            date_of_birth=self.leaver_info.leaver_date_of_birth,
            job_title=self.leaver_info.job_title,
            security_clearance=self.leaving_request.security_clearance,
        )

        return initial

    def form_valid(self, form) -> HttpResponse:
        self.leaver_info.leaver_first_name = form.cleaned_data["first_name"]
        self.leaver_info.leaver_last_name = form.cleaned_data["last_name"]
        self.leaver_info.leaver_date_of_birth = form.cleaned_data["date_of_birth"]
        self.leaver_info.job_title = form.cleaned_data["job_title"]
        self.leaver_info.save(
            update_fields=[
                "leaver_first_name",
                "leaver_last_name",
                "leaver_date_of_birth",
                "job_title",
            ]
        )
        self.leaving_request.security_clearance = form.cleaned_data[
            "security_clearance"
        ]
        self.leaving_request.save(update_fields=["security_clearance"])

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="Your employment profile")
        return context


class LeaverFindDetailsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/leaver_find_details.html"
    form_class = leaver_forms.FindPersonIDForm
    success_url = reverse_lazy("leaver-dates")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))

        if self.has_person_id():
            self.set_default_line_manager()
            return redirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)

    def has_person_id(self) -> bool:
        leaver_activitystream_user = cast(
            Optional[ActivityStreamStaffSSOUser],
            self.leaving_request.leaver_activitystream_user,
        )
        if leaver_activitystream_user:
            leaver_person_id = leaver_activitystream_user.get_person_id()
            if leaver_person_id:
                return True
        return False

    def set_default_line_manager(self):
        leaver_activitystream_user = cast(
            Optional[ActivityStreamStaffSSOUser],
            self.leaving_request.leaver_activitystream_user,
        )

        if not leaver_activitystream_user:
            return None

        leaver_person_id = leaver_activitystream_user.get_person_id()
        uksbs_interface = get_uksbs_interface()
        leaver_hierarchy = uksbs_interface.get_user_hierarchy(
            person_id=leaver_person_id
        )
        leaver_managers = leaver_hierarchy.get("manager", [])
        if not leaver_managers:
            return None

        leaver_manager = leaver_managers[0]
        leaver_manager_email = leaver_manager.get("email_address")
        if not leaver_manager_email:
            return None

        activity_stream_user_emails = ActivityStreamStaffSSOUserEmail.objects.filter(
            email_address=leaver_manager_email
        )
        if activity_stream_user_emails.count() == 1:
            leaver_manager_activity_stream_user = (
                activity_stream_user_emails.first().staff_sso_user
            )
            self.leaving_request.manager_activitystream_user = (
                leaver_manager_activity_stream_user
            )
            self.leaving_request.save()

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title="Your personal email")
        return context

    def form_valid(self, form: Form) -> HttpResponse:
        assert self.leaving_request

        people_data_interface = get_people_data_interface()

        personal_email = form.cleaned_data["personal_email"]

        people_data_result = people_data_interface.get_people_data(
            email_address=personal_email
        )
        if people_data_result.person_id:
            self.leaving_request.leaver_activitystream_user.uksbs_person_id_override = (
                people_data_result.person_id
            )
            self.leaving_request.leaver_activitystream_user.save()
            self.set_default_line_manager()
        else:
            form.add_error(
                "personal_email",
                "We couldn't find details for this email address. Please try "
                "an alterate email address.",
            )
            return self.form_invalid(form)

        return super().form_valid(form)


class LeaverFindDetailsHelpView(LeaverInformationMixin, TemplateView):
    template_name = "leaving/leaver/leaver_find_details_help.html"

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if leaving_request and leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Please reach out to our support team",
        )
        return context


class RemoveLineManagerFromLeavingRequestView(LeaverInformationMixin, RedirectView):
    url = reverse_lazy("leaver-dates")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        self.leaving_request.manager_activitystream_user = None
        self.leaving_request.save(update_fields=["manager_activitystream_user"])

        return super().get(request, *args, **kwargs)


class LeaverDatesView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/dates.html"
    form_class = leaver_forms.LeaverDatesForm
    success_url = reverse_lazy("leaver-has-assets")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))

        self.line_manager: Optional[
            ActivityStreamStaffSSOUser
        ] = self.leaving_request.manager_activitystream_user
        self.line_manager_search_document: Optional[ConsolidatedStaffDocument] = None
        if self.line_manager:
            self.line_manager_search_document = get_csd_for_activitystream_user(
                activitystream_user=self.line_manager,
            )

        if LINE_MANAGER_SEARCH_PARAM in request.GET:
            self.line_manager_uuid = request.GET[LINE_MANAGER_SEARCH_PARAM]
            try:
                staff_document = get_staff_document_from_staff_index(
                    staff_uuid=self.line_manager_uuid
                )
            except Exception:
                pass
            else:
                self.line_manager_search_document = consolidate_staff_documents(
                    staff_documents=[staff_document]
                )[0]
                try:
                    self.line_manager = ActivityStreamStaffSSOUser.objects.active().get(
                        identifier=self.line_manager_search_document[
                            "staff_sso_activity_stream_id"
                        ],
                    )
                except ActivityStreamStaffSSOUser.DoesNotExist:
                    pass
                else:
                    if not self.leaving_request.manager_activitystream_user:
                        self.leaving_request.manager_activitystream_user = (
                            self.line_manager
                        )
                        self.leaving_request.save(
                            update_fields=["manager_activitystream_user"]
                        )

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial.update(
            leaving_date=self.leaver_info.leaving_date,
            last_day=self.leaver_info.last_day,
        )

        if self.line_manager_search_document:
            initial.update(
                leaver_manager=self.line_manager_search_document["uuid"],
            )

        return initial

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(request=self.request)
        return form_kwargs

    def form_valid(self, form) -> HttpResponse:
        self.leaver_info.leaving_date = form.cleaned_data["leaving_date"]
        self.leaver_info.last_day = form.cleaned_data["last_day"]
        self.leaver_info.save(
            update_fields=[
                "leaving_date",
                "last_day",
            ]
        )

        if not self.leaving_request.manager_activitystream_user:
            form.add_error(None, "You must select a line manager")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        manager_activitystream_user = cast(
            Optional[ActivityStreamStaffSSOUser],
            self.leaving_request.manager_activitystream_user,
        )
        context.update(
            page_title="Your last working day, leaving date and line manager",
            manager_search_url=reverse("leaver-manager-search"),
            leaver_manager=get_csd_for_activitystream_user(
                activitystream_user=manager_activitystream_user,
            ),
        )
        return context


class LeaverHasAssetsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/has_assets.html"
    form_class = leaver_forms.LeaverHasAssetsForm
    success_url = reverse_lazy("leaver-has-cirrus-equipment")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if leaving_request and leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial.update(
            has_gov_procurement_card=None,
            has_rosa_kit=None,
            has_dse=None,
        )
        holds_government_procurement_card = cast(
            Optional[bool], self.leaving_request.holds_government_procurement_card
        )
        if holds_government_procurement_card is not None:
            initial.update(
                has_gov_procurement_card=bool_to_yes_no(
                    holds_government_procurement_card
                ),
            )
        is_rosa_user = cast(Optional[bool], self.leaving_request.is_rosa_user)
        if is_rosa_user is not None:
            initial.update(
                has_gov_procurement_card=bool_to_yes_no(is_rosa_user),
            )
        has_dse = cast(Optional[bool], self.leaver_info.has_dse)
        if has_dse is not None:
            initial.update(
                has_gov_procurement_card=bool_to_yes_no(has_dse),
            )

        return initial

    def form_valid(self, form) -> HttpResponse:
        self.leaving_request.holds_government_procurement_card = yes_no_to_bool(
            form.cleaned_data["has_gov_procurement_card"]
        )
        self.leaving_request.is_rosa_user = yes_no_to_bool(
            form.cleaned_data["has_rosa_kit"]
        )
        self.leaving_request.save(
            update_fields=[
                "holds_government_procurement_card",
                "is_rosa_user",
            ]
        )
        self.leaver_info.has_dse = yes_no_to_bool(form.cleaned_data["has_dse"])
        self.leaver_info.save(
            update_fields=[
                "has_dse",
            ]
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="Return your pass and other assets")
        return context


def get_cirrus_assets(request: HttpRequest) -> List[types.CirrusAsset]:
    user = cast(User, request.user)

    staff_sso_user = ActivityStreamStaffSSOUser.objects.active().get(
        email_user_id=user.sso_email_user_id,
    )

    service_now_email: Optional[str] = staff_sso_user.service_now_email_address

    if service_now_email:
        if "cirrus_assets" not in request.session:
            service_now_interface = get_service_now_interface()
            request.session["cirrus_assets"] = [
                {
                    "uuid": str(uuid.uuid4()),
                    "sys_id": asset["sys_id"],
                    "tag": asset["tag"],
                    "name": asset["name"],
                }
                for asset in service_now_interface.get_assets_for_user(
                    email=service_now_email,
                )
            ]

    return request.session.get("cirrus_assets", [])


class HasCirrusEquipmentView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/cirrus/has_equipment.html"
    form_class = leaver_forms.HasCirrusKitForm
    success_url = reverse_lazy("leaver-cirrus-equipment")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if leaving_request and leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))

        user_assets = get_cirrus_assets(request=request)
        if not user_assets:
            return super().dispatch(request, *args, **kwargs)
        return redirect(self.success_url)

    def form_valid(self, form):
        has_cirrus_kit: Literal["yes", "no"] = form.cleaned_data["has_cirrus_kit"]

        if has_cirrus_kit == "no":
            self.success_url = reverse_lazy("leaver-display-screen-equipment")

        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="Return Cirrus kit")
        return context


def delete_cirrus_equipment(request: HttpRequest, kit_uuid: uuid.UUID):
    if "cirrus_assets" in request.session:
        for asset in request.session["cirrus_assets"]:
            if asset["uuid"] == str(kit_uuid):
                request.session["cirrus_assets"].remove(asset)
                request.session.save()
                break
    return redirect("leaver-cirrus-equipment")


class CirrusEquipmentView(LeaverInformationMixin, TemplateView):
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": leaver_forms.AddCirrusAssetForm,
        "cirrus_return_form": leaver_forms.CirrusReturnFormWithAssets,
        "cirrus_return_form_no_assets": leaver_forms.CirrusReturnFormNoAssets,
    }
    template_name = "leaving/leaver/cirrus/equipment.html"
    success_url = reverse_lazy("leaver-display-screen-equipment")

    def post_add_asset_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        session = request.session
        if "cirrus_assets" not in session:
            session["cirrus_assets"] = []

        # Add asset to session
        asset: types.CirrusAsset = {
            "uuid": str(uuid.uuid4()),
            "sys_id": None,
            "tag": None,
            "name": form.cleaned_data["asset_name"],
        }
        session["cirrus_assets"].append(asset)
        session.save()

        # Redirect to the GET method
        return redirect("leaver-cirrus-equipment")

    def post_cirrus_return_form_no_assets(
        self, request: HttpRequest, form: Form, *args, **kwargs
    ):
        user = cast(User, self.request.user)
        sso_email_user_id = cast(str, user.sso_email_user_id)

        # Store correction info and assets into the leaver details
        self.store_cirrus_kit_information(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            cirrus_assets=[],
        )
        return redirect(self.success_url)

    def post_cirrus_return_form(
        self, request: HttpRequest, form: Form, *args, **kwargs
    ):
        user = cast(User, self.request.user)
        sso_email_user_id = cast(str, user.sso_email_user_id)

        # Store correction info and assets into the leaver details
        self.store_cirrus_kit_information(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            cirrus_assets=request.session.get("cirrus_assets", []),
        )

        form_data = form.cleaned_data
        return_option = form.cleaned_data["return_option"]

        # Store return information
        self.store_return_option(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            return_option=return_option,
        )
        if return_option == ReturnOptions.OFFICE.value:
            self.store_return_information(
                sso_email_user_id=sso_email_user_id,
                requester=user,
                personal_phone=form.cleaned_data["office_personal_phone"],
                contact_email=form.cleaned_data["office_contact_email"],
                address=None,
            )
        elif return_option == ReturnOptions.HOME.value:
            return_address: Address = {
                "line_1": form_data["home_address_line_1"],
                "line_2": form_data["home_address_line_2"],
                "town_or_city": form_data["home_address_city"],
                "county": form_data["home_address_county"],
                "postcode": form_data["home_address_postcode"],
            }
            self.store_return_information(
                sso_email_user_id=sso_email_user_id,
                requester=user,
                personal_phone=form.cleaned_data["home_personal_phone"],
                contact_email=form.cleaned_data["home_contact_email"],
                address=return_address,
            )

        return redirect(self.success_url)

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)
        sso_email_user_id = cast(str, user.sso_email_user_id)
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if leaving_request and leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "form_name" in request.POST:
            form_name = request.POST["form_name"]
            if form_name in self.forms:
                form = self.forms[form_name](request.POST)
                if form.is_valid():
                    # Call the "post_{form_name}" method to handle the form POST logic.
                    return getattr(self, f"post_{form_name}")(
                        request, form, *args, **kwargs
                    )
                else:
                    context[form_name] = form
        return self.render_to_response(context)

    def get_initial_add_asset_form(self):
        return {}

    def get_initial_cirrus_return_form(self):
        return {
            "return_option": self.leaver_info.return_option,
            "office_personal_phone": self.leaver_info.return_personal_phone,
            "home_personal_phone": self.leaver_info.return_personal_phone,
            "office_contact_email": self.leaver_info.return_contact_email,
            "home_contact_email": self.leaver_info.return_contact_email,
            "home_address_line_1": self.leaver_info.return_address_line_1,
            "home_address_line_2": self.leaver_info.return_address_line_2,
            "home_address_city": self.leaver_info.return_address_city,
            "home_address_county": self.leaver_info.return_address_county,
            "home_address_postcode": self.leaver_info.return_address_postcode,
        }

    def get_initial_cirrus_return_form_no_assets(self):
        return {}

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title="Return Cirrus kit")

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            form_initial = getattr(self, f"get_initial_{form_name}")()
            context[form_name] = form_class(initial=form_initial)

        context.update(cirrus_assets=get_cirrus_assets(request=self.request))
        return context


def delete_dse_equipment(request: HttpRequest, kit_uuid: uuid.UUID):
    if "dse_assets" in request.session:
        for asset in request.session["dse_assets"]:
            if asset["uuid"] == str(kit_uuid):
                request.session["dse_assets"].remove(asset)
                request.session.save()
                break
    return redirect("leaver-display-screen-equipment")


class DisplayScreenEquipmentView(LeaverInformationMixin, TemplateView):
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": leaver_forms.AddDisplayScreenEquipmentAssetForm,
        "submission_form": leaver_forms.SubmissionForm,
    }
    template_name = "leaving/leaver/display_screen_equipment.html"
    success_url = reverse_lazy("leaver-contact-details")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if leaving_request and leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))

        # If the leaver doesn't have DSE, skip this step.
        if not self.leaver_info.has_dse:
            return redirect(self.success_url)

        return super().dispatch(request, *args, **kwargs)

    def post_add_asset_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        session = request.session
        if "dse_assets" not in session:
            session["dse_assets"] = []

        # Add asset to session
        asset: types.DisplayScreenEquipmentAsset = {
            "uuid": str(uuid.uuid4()),
            "name": form.cleaned_data["asset_name"],
        }
        session["dse_assets"].append(asset)
        session.save()

        # Redirect to the GET method
        return redirect("leaver-display-screen-equipment")

    def post_submission_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        # Store dse assets into the leaver details
        self.store_display_screen_equipment(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            dse_assets=request.session.get("dse_assets", []),
        )

        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "form_name" in request.POST:
            form_name = request.POST["form_name"]
            if form_name in self.forms:
                form = self.forms[form_name](request.POST)
                if form.is_valid():
                    # Call the "post_{form_name}" method to handle the form POST logic.
                    return getattr(self, f"post_{form_name}")(
                        request, form, *args, **kwargs
                    )
                else:
                    context[form_name] = form
        return self.render_to_response(context)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if "dse_assets" not in request.session:
            request.session["dse_assets"] = []
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title="Return DIT-owned equipment over £150")

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            context[form_name] = form_class()
        if "dse_assets" in self.request.session:
            context["dse_assets"] = self.request.session["dse_assets"]

        return context


class LeaverContactDetailsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/personal_contact_details.html"
    form_class = leaver_forms.LeaverContactDetailsForm
    success_url = reverse_lazy("leaver-confirm-details")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if leaving_request and leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        initial.update(
            contact_phone=self.leaver_info.contact_phone,
            contact_email_address=self.leaver_info.personal_email,
            contact_address_line_1=self.leaver_info.contact_address_line_1,
            contact_address_line_2=self.leaver_info.contact_address_line_2,
            contact_address_city=self.leaver_info.contact_address_city,
            contact_address_county=self.leaver_info.contact_address_county,
            contact_address_postcode=self.leaver_info.contact_address_postcode,
        )

        return initial

    def form_valid(self, form) -> HttpResponse:
        self.leaver_info.contact_phone = form.cleaned_data.get("contact_phone")
        self.leaver_info.personal_email = form.cleaned_data.get("contact_email_address")
        self.leaver_info.contact_address_line_1 = form.cleaned_data.get(
            "contact_address_line_1"
        )
        self.leaver_info.contact_address_line_2 = form.cleaned_data.get(
            "contact_address_line_2"
        )
        self.leaver_info.contact_address_city = form.cleaned_data.get(
            "contact_address_city"
        )
        self.leaver_info.contact_address_county = form.cleaned_data.get(
            "contact_address_county"
        )
        self.leaver_info.contact_address_postcode = form.cleaned_data.get(
            "contact_address_postcode"
        )
        self.leaver_info.save(
            update_fields=[
                "contact_phone",
                "personal_email",
                "contact_address_line_1",
                "contact_address_line_2",
                "contact_address_city",
                "contact_address_county",
                "contact_address_postcode",
            ]
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Personal contact details",
            has_dse=self.leaver_info.has_dse,
        )
        return context


class ConfirmDetailsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/confirm_details.html"
    form_class = leaver_forms.LeaverConfirmationForm
    success_url = reverse_lazy("leaver-request-received")

    leaving_request: LeavingRequest
    leaver_info: LeaverInformation

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if self.leaving_request and self.leaving_request.leaver_complete:
            return redirect(reverse("leaver-request-received"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            page_title="Check and confirm your answers",
            leaving_request=self.leaving_request,
            leaver_info=self.leaver_info,
            staff_type=types.StaffType(self.leaving_request.staff_type),
            security_clearance=types.SecurityClearance(
                self.leaving_request.security_clearance
            ),
            cirrus_assets=self.leaver_info.cirrus_assets,
            dse_assets=self.leaver_info.dse_assets,
            return_option=self.leaver_info.return_option,
            return_personal_phone=self.leaver_info.return_personal_phone,
            return_contact_email=self.leaver_info.return_contact_email,
        ),
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Check we have all the required information before we continue.
        """
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()

        # Create the workflow
        self.create_workflow(sso_email_user_id=sso_email_user_id, requester=user)

        return super().form_valid(form)


class RequestReceivedView(LeaverInformationMixin, TemplateView):
    template_name = "leaving/leaver/request_received.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Thank you",
            leaver_info=self.get_leaver_information(
                sso_email_user_id=sso_email_user_id, requester=user
            ),
            leaving_request=self.get_leaving_request(
                sso_email_user_id=sso_email_user_id, requester=user
            ),
        )
        return context
