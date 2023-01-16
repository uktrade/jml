import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Type, cast

from django.forms import Form
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import resolve, reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView
from django.views.generic.edit import FormView

from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)
from core.people_data import get_people_data_interface
from core.service_now import get_service_now_interface
from core.staff_search.views import StaffSearchView
from core.types import Address
from core.uksbs import get_uksbs_interface
from core.uksbs.client import UKSBSPersonNotFound, UKSBSUnexpectedResponse
from core.utils.helpers import bool_to_yes_no, make_possessive, yes_no_to_bool
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    consolidate_staff_documents,
    get_csd_for_activitystream_user,
    get_sso_user_by_staff_document_uuid,
    get_staff_document_from_staff_index,
)
from core.views import BaseTemplateView
from leavers import types
from leavers.forms import leaver as leaver_forms
from leavers.forms.leaver import ReturnOptions
from leavers.models import LeaverInformation
from leavers.types import LeavingReason, StaffType
from leavers.utils.leaving_request import update_or_create_leaving_request
from leavers.views.base import LeavingRequestViewMixin
from leavers.workflow.utils import get_or_create_leaving_workflow
from user.models import User

LINE_MANAGER_SEARCH_PARAM = "line_manager_uuid"


class MultiplePersonIdErrorView(BaseTemplateView):
    template_name = "leaving/multiple_person_id_errors.html"


class LeaversStartView(BaseTemplateView):
    template_name = "leaving/start.html"
    extra_context = {"start_url": reverse_lazy("leaver-select-leaver")}


class LeaverSearchView(StaffSearchView):
    success_url = reverse_lazy("leaver-select-leaver")


class SelectLeaverView(FormView, BaseTemplateView):
    template_name = "leaving/leaver/select_leaver.html"
    form_class = leaver_forms.SelectLeaverForm

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)
        if not user.has_perm("leavers.select_leaver"):
            self.init_leaving_request(user.get_sso_user())

            return redirect(self.get_success_url())

        self.leaver_uuid = self.request.GET.get("staff_uuid")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(request=self.request)

        return form_kwargs

    def get_initial(self) -> dict[str, Any]:
        initial = {}

        if self.leaver_uuid:
            initial["leaver_uuid"] = self.leaver_uuid

        return super().get_initial() | initial

    def form_valid(self, form):
        leaver_uuid = form.cleaned_data["leaver_uuid"]

        leaver = get_sso_user_by_staff_document_uuid(leaver_uuid)

        self.init_leaving_request(leaver)

        return super().form_valid(form)

    def init_leaving_request(self, leaver: ActivityStreamStaffSSOUser) -> None:
        assert self.request.user.is_authenticated

        user = cast(User, self.request.user)

        # get or create a LeavingRequest object
        leaving_request = update_or_create_leaving_request(
            leaver=leaver, user_requesting=user
        )
        # get or create a LeavingInformation object
        LeaverInformation.objects.get_or_create(leaving_request=leaving_request)

        # we need to access this from the get_success_url method
        self.leaving_request = leaving_request

    def get_success_url(self) -> str:
        if not self.leaving_request.leaver_complete:
            return reverse(
                "leaver-checks",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            )
        if not self.leaving_request.line_manager_complete:
            return reverse(
                "line-manager-start",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            )
        raise Exception("Leaver and line manager are complete")


class LeaverShowViewConditions(Enum):
    LEAVING_REQUEST_COMPLETE = "leaving_request_complete"


class LeavingJourneyViewMixin(LeavingRequestViewMixin):
    JOURNEY = {
        "why-are-you-leaving": {
            "prev": reverse_lazy("start"),
            "next": "staff-type",
            "conditions": [],
            "view_name": "Leaving reason",
            "show_in_summary": True,
        },
        "staff-type": {
            "prev": "why-are-you-leaving",
            "next": "employment-profile",
            "conditions": [],
            "view_name": "Staff type",
            "show_in_summary": True,
        },
        "employment-profile": {
            "prev": "why-are-you-leaving",
            "next": "leaver-find-details",
            "conditions": [],
            "view_name": "Employment profile",
            "show_in_summary": True,
        },
        "leaver-find-details": {
            "prev": "employment-profile",
            "next": "leaver-dates",
            "conditions": [],
            "view_name": "Find leaver's details",
            "show_in_summary": False,
        },
        "leaver-dates": {
            "prev": "employment-profile",
            "next": "leaver-has-assets",
            "conditions": [],
            "view_name": "Dates",
            "show_in_summary": True,
        },
        "leaver-has-assets": {
            "prev": "leaver-dates",
            "next": "leaver-has-cirrus-equipment",
            "conditions": [],
            "view_name": "Leaver's assets",
            "show_in_summary": True,
        },
        "leaver-has-cirrus-equipment": {
            "prev": "leaver-has-assets",
            "next": "leaver-cirrus-equipment",
            "conditions": [],
            "view_name": "Leaver's Cirrus equipment?",
            "show_in_summary": True,
        },
        "leaver-cirrus-equipment": {
            "prev": "leaver-has-assets",
            "next": "leaver-display-screen-equipment",
            "conditions": [],
            "view_name": "Leaver's Cirrus equipment",
            "show_in_summary": False,
        },
        "leaver-display-screen-equipment": {
            "prev": "leaver-has-cirrus-equipment",
            "next": "leaver-contact-details",
            "conditions": [],
            "view_name": "Leaver's display screen equipment",
            "show_in_summary": True,
        },
        "leaver-contact-details": {
            "prev": "leaver-display-screen-equipment",
            "next": "leaver-confirm-details",
            "conditions": [],
            "view_name": "Leaver's contact details",
            "show_in_summary": True,
        },
        "leaver-confirm-details": {
            "prev": "leaver-contact-details",
            "next": "leaver-request-received",
            "conditions": [],
            "view_name": "Confirm leaver's details",
            "show_in_summary": True,
        },
        "leaver-request-received": {
            "prev": None,
            "next": None,
            "conditions": [LeaverShowViewConditions.LEAVING_REQUEST_COMPLETE],
            "view_name": "Leaver thank you",
            "show_in_summary": False,
        },
    }

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        current_url = resolve(request.path_info).url_name
        self.journey_dict = {}
        if current_url in self.JOURNEY:
            self.journey_dict = self.JOURNEY.get(current_url, {})
            self.initialise_journey()

    def initialise_journey(self) -> None:
        if self.journey_dict:
            prev = self.journey_dict.get("prev")
            if prev:
                if type(prev) == str:
                    self.back_link_viewname = prev
                elif type(prev) == Callable:
                    self.back_link_url = prev
            next = self.journey_dict.get("next")
            if next:
                if type(next) == str:
                    self.success_viewname = next
                elif type(next) == Callable:
                    self.success_url = next

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:

        multiple_person_id_response = self.check_multiple_person_ids(request=request)
        if multiple_person_id_response:
            return multiple_person_id_response

        if self.leaving_request:
            view_show_conditions = self.journey_dict.get("conditions", [])

            if self.leaving_request.leaver_complete:
                if (
                    LeaverShowViewConditions.LEAVING_REQUEST_COMPLETE
                    not in view_show_conditions
                ):
                    return redirect(
                        reverse(
                            "leaver-request-received",
                            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                        )
                    )
            elif (
                LeaverShowViewConditions.LEAVING_REQUEST_COMPLETE
                in view_show_conditions
            ):
                raise Http404

        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def get_success_url(self) -> str:
        if "save_and_close" in self.request.POST:
            return reverse(
                "leaving-request-summary",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            )
        return super().get_success_url()

    def check_multiple_person_ids(self, request: HttpRequest):
        SESSION_KEY = "multiple_person_ids_passed"
        person_id_error_page = reverse("leaver-multiple-person-ids-error")
        # The user has already been checked and verified.
        if SESSION_KEY in request.session:
            if not request.session[SESSION_KEY]:
                return redirect(person_id_error_page)

        user_emails = self.leaver_activitystream_user.sso_emails.all().values_list(
            "email_address", flat=True
        )

        people_data_interface = get_people_data_interface()
        multiple_person_id_emails = (
            people_data_interface.get_emails_with_multiple_person_ids()
        )

        # Check if any of the user's emails are a known multiple Person ID email.
        if any(email in multiple_person_id_emails for email in user_emails):
            request.session[SESSION_KEY] = False
            request.session.save()
            return redirect(person_id_error_page)

        request.session[SESSION_KEY] = True
        request.session.save()

    def get_cirrus_assets(self) -> List[types.CirrusAsset]:
        user = cast(User, self.request.user)
        session = self.get_session()

        staff_sso_user = ActivityStreamStaffSSOUser.objects.active().get(
            email_user_id=user.sso_email_user_id,
        )

        service_now_email: Optional[str] = staff_sso_user.service_now_email_address

        if service_now_email and not self.leaving_request.service_now_offline:
            if "cirrus_assets" not in session:
                service_now_interface = get_service_now_interface()
                session["cirrus_assets"] = [
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
                self.store_session(session)

        return session.get("cirrus_assets", [])

    def get_form_kwargs(self):
        if hasattr(super(), "get_form_kwargs"):
            kwargs = super().get_form_kwargs()
        else:
            kwargs = {}

        kwargs.update(
            request=self.request,
            leaving_request=self.leaving_request,
            user_is_leaver=self.user_is_leaver,
        )
        return kwargs

    def store_display_screen_equipment(
        self,
        dse_assets: List[types.DisplayScreenEquipmentAsset],
    ) -> None:
        """
        Store DSE assets
        """
        self.leaver_info.dse_assets = dse_assets
        self.leaver_info.save(update_fields=["dse_assets"])

    def store_cirrus_kit_information(
        self,
        cirrus_assets: List[types.CirrusAsset],
    ) -> None:
        """
        Store the Correction information
        """

        self.leaver_info.cirrus_assets = cirrus_assets
        self.leaver_info.save(
            update_fields=[
                "cirrus_assets",
            ]
        )

        if not cirrus_assets:
            # clear any existing cirrus kit information if there is no kit.
            self.store_return_option(
                return_option=None,
            )
            self.store_return_information(
                personal_phone=None,
                contact_email=None,
                address=None,
            )

    def store_return_option(self, return_option: Optional[str]) -> None:
        """
        Store the selected return option.

        return_option is a value from ReturnOptions.
        """

        self.leaver_info.return_option = return_option
        self.leaver_info.save(update_fields=["return_option"])

    def store_return_information(
        self,
        personal_phone: Optional[str],
        contact_email: Optional[str],
        address: Optional[Address],
    ) -> None:
        self.leaver_info.return_personal_phone = personal_phone
        self.leaver_info.return_contact_email = contact_email

        # Reset address fields
        self.leaver_info.return_address_line_1 = None
        self.leaver_info.return_address_line_2 = None
        self.leaver_info.return_address_city = None
        self.leaver_info.return_address_county = None
        self.leaver_info.return_address_postcode = None

        if address:
            self.leaver_info.return_address_line_1 = address["line_1"]
            self.leaver_info.return_address_line_2 = address["line_2"]
            self.leaver_info.return_address_city = address["town_or_city"]
            self.leaver_info.return_address_county = address["county"]
            self.leaver_info.return_address_postcode = address["postcode"]

        # Save leaver information
        self.leaver_info.save(
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

    def create_workflow(self, requester: User):
        get_or_create_leaving_workflow(
            leaving_request=self.leaving_request,
            executed_by=requester,
        )


class MyManagerSearchView(LeavingRequestViewMixin, StaffSearchView):
    search_name = "manager"
    query_param_name = LINE_MANAGER_SEARCH_PARAM

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.exclude_staff_ids = [self.leaving_request.leaver.identifier]

        return super().dispatch(request, *args, **kwargs)


class LeaverChecksView(LeavingRequestViewMixin, RedirectView):
    failure_url = reverse_lazy("unable-to-offboard")

    def get_redirect_url(self, *args, **kwargs):
        leaver_activitystream_user = self.leaving_request.leaver_activitystream_user

        person_id = leaver_activitystream_user.get_person_id()

        if not person_id:
            return self.failure_url

        uksbs_interface = get_uksbs_interface()
        try:
            uksbs_interface.get_user_hierarchy(person_id=person_id)
        except (UKSBSUnexpectedResponse, UKSBSPersonNotFound):
            return self.failure_url

        return reverse(
            "why-are-you-leaving",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )


class UnableToOffboardView(LeavingJourneyViewMixin, BaseTemplateView):
    template_name = "leaving/leaver/unable_to_offboard.html"
    extra_context = {"page_title": "You cannot use this service"}


class WhyAreYouLeavingView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/why_are_you_leaving.html"
    form_class = leaver_forms.WhyAreYouLeavingForm

    leaving_reason: Optional[LeavingReason] = None

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial["reason"] = self.leaving_request.reason_for_leaving
        return initial

    def form_valid(self, form) -> HttpResponse:
        reason: str = form.cleaned_data["reason"]

        if reason == "none_of_the_above":
            self.leaving_request.reason_for_leaving = None
            self.leaving_request.save(update_fields=["reason_for_leaving"])
        else:
            self.leaving_reason = LeavingReason(reason)
            self.leaving_request.reason_for_leaving = self.leaving_reason
            self.leaving_request.save(update_fields=["reason_for_leaving"])

        return super().form_valid(form)

    def get_success_url(self) -> str:
        if "save_and_close" in self.request.POST:
            return reverse(
                "leaving-request-summary",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            )

        reason_mapping = {
            LeavingReason.RESIGNATION: reverse_lazy(
                "staff-type",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            LeavingReason.RETIREMENT: reverse_lazy(
                "leaving-reason-unhandled",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            LeavingReason.TRANSFER: reverse_lazy(
                "staff-type",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            LeavingReason.END_OF_CONTRACT: reverse_lazy(
                "staff-type",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            LeavingReason.DISMISSAL: reverse_lazy(
                "staff-type",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            LeavingReason.DEATH_IN_SERVICE: reverse_lazy(
                "staff-type",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
        }
        if self.leaving_reason in reason_mapping:
            return reason_mapping[self.leaving_reason]

        return reverse(
            "leaving-reason-unhandled",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )

    def get_page_title(self):
        leaver_name = self.leaving_request.get_leaver_name()

        page_title = "What is your reason for leaving DIT?"
        if not self.user_is_leaver:
            page_title = f"Why is {leaver_name} leaving DIT?"

        return page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title=self.get_page_title())
        return context


class UnhandledLeavingReasonView(LeavingJourneyViewMixin, BaseTemplateView):
    template_name = "leaving/leaver/unhandled_reason.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page_title = "Sorry, we are unable to help offbaord you"
        if not self.user_is_leaver:
            page_title = "Sorry, we are unable to help offbaord the leaver"

        context.update(page_title=page_title)
        return context


class StaffTypeView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/staff_type.html"
    form_class = leaver_forms.StaffTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        page_title = "How are you employed by DIT?"
        if not self.user_is_leaver:
            page_title = f"How is {leaver_name} employed by DIT?"

        context.update(page_title=page_title)
        return context

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial.update(
            staff_type=self.leaving_request.staff_type,
        )

        return initial

    def form_valid(self, form) -> HttpResponse:
        assert self.leaving_request.reason_for_leaving

        leaving_reason_staff_type_mapping = {
            LeavingReason.RESIGNATION.value: {
                "staff_types": [StaffType.CIVIL_SERVANT],
                "error_message": "Only Civil Servants can resign.",
            },
            LeavingReason.RETIREMENT.value: {
                "staff_types": [],
                "error_message": "Only Civil Servants can retire.",
            },
            LeavingReason.END_OF_CONTRACT.value: {
                "staff_types": [StaffType.CONTRACTOR, StaffType.BENCH_CONTRACTOR],
                "error_message": (
                    "With the reason for leaving as "
                    f"'{LeavingReason.END_OF_CONTRACT.label}', the staff type must "
                    "be 'Contractor' or 'Bench contractor'."
                ),
            },
            LeavingReason.TRANSFER.value: {
                "staff_types": [StaffType.CIVIL_SERVANT],
                "error_message": (
                    "Only Civil Servants can transfer to another department."
                ),
            },
            LeavingReason.DISMISSAL.value: {
                "staff_types": [StaffType.CIVIL_SERVANT],
                "error_message": "Only Civil Servants can be dismissed.",
            },
            LeavingReason.DEATH_IN_SERVICE.value: {
                "staff_types": [StaffType.CIVIL_SERVANT],
                "error_message": (
                    f"Only select '{LeavingReason.DEATH_IN_SERVICE.label}' if "
                    "that status applies to a Civil Servant."
                ),
            },
        }

        staff_type = StaffType(form.cleaned_data["staff_type"])
        reason_for_leaving_mapping = leaving_reason_staff_type_mapping.get(
            self.leaving_request.reason_for_leaving, None
        )

        if staff_type == StaffType.FAST_STREAMERS:
            self.success_viewname = "leaver-fast-streamer"
            return super().form_valid(form)
        else:
            self.leaving_request.staff_type = staff_type
            self.leaving_request.save(update_fields=["staff_type"])

        if (
            reason_for_leaving_mapping
            and staff_type not in reason_for_leaving_mapping["staff_types"]
        ):
            form.add_error("staff_type", reason_for_leaving_mapping["error_message"])
            return self.form_invalid(form)

        return super().form_valid(form)


class LeaverFastStreamerView(LeavingJourneyViewMixin, BaseTemplateView):
    template_name = "leaving/leaver/fast_streamer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page_title = "You cannot use this service"
        if not self.user_is_leaver:
            page_title = "Fast Streamers cannot use this service"

        context.update(page_title=page_title)
        return context


class EmploymentProfileView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/employment_profile.html"
    form_class = leaver_forms.EmploymentProfileForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        page_title = "Your employment profile"
        if not self.user_is_leaver:
            page_title = f"{possessive_leaver_name} employment profile"

        context.update(page_title=page_title)
        return context

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


class LeaverFindDetailsView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/leaver_find_details.html"
    form_class = leaver_forms.FindPersonIDForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        page_title = "Your personal email address"
        if not self.user_is_leaver:
            page_title = f"{possessive_leaver_name} personal email address"

        context.update(page_title=page_title)
        return context

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
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

    def form_valid(self, form: Form) -> HttpResponse:
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
                "We cannot find your details. Try a different email address.",
            )
            return self.form_invalid(form)

        return super().form_valid(form)


class LeaverFindDetailsHelpView(LeavingJourneyViewMixin, BaseTemplateView):
    template_name = "leaving/leaver/leaver_find_details_help.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()

        page_title = "You cannot use this service"
        if not self.user_is_leaver:
            page_title = f"Cannot use this service for this {leaver_name}"

        context.update(page_title=page_title)
        return context


class RemoveLineManagerFromLeavingRequestView(LeavingJourneyViewMixin, RedirectView):
    pattern_name = "leaver-dates"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        self.leaving_request.manager_activitystream_user = None
        self.leaving_request.save(update_fields=["manager_activitystream_user"])

        return super().get(request, *args, **kwargs)


class LeaverDatesView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/dates.html"
    form_class = leaver_forms.LeaverDatesForm

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
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

    def form_valid(self, form) -> HttpResponse:
        self.leaver_info.leaving_date = form.cleaned_data["leaving_date"]
        self.leaver_info.last_day = form.cleaned_data["last_day"]
        self.leaver_info.save(
            update_fields=[
                "leaving_date",
                "last_day",
            ]
        )

        if (
            "save_and_close" not in form.data
            and not self.leaving_request.manager_activitystream_user
        ):
            form.add_error(None, "You must select a line manager")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        page_title = "Your last working day, leaving date and line manager"
        if not self.user_is_leaver:
            page_title = f"{possessive_leaver_name} last working day, leaving date and line manager"

        manager_activitystream_user = cast(
            Optional[ActivityStreamStaffSSOUser],
            self.leaving_request.manager_activitystream_user,
        )
        context.update(
            page_title=page_title,
            possessive_leaver_name=possessive_leaver_name,
            manager_search_url=reverse(
                "leaver-manager-search",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            ),
            leaver_manager=get_csd_for_activitystream_user(
                activitystream_user=manager_activitystream_user,
            ),
        )
        return context


class LeaverHasAssetsView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/has_assets.html"
    form_class = leaver_forms.LeaverHasAssetsForm

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
                has_rosa_kit=bool_to_yes_no(is_rosa_user),
            )
        has_dse = cast(Optional[bool], self.leaver_info.has_dse)
        if has_dse is not None:
            initial.update(
                has_dse=bool_to_yes_no(has_dse),
            )

        return initial

    def form_valid(self, form) -> HttpResponse:
        if form.cleaned_data["has_gov_procurement_card"]:
            self.leaving_request.holds_government_procurement_card = yes_no_to_bool(
                form.cleaned_data["has_gov_procurement_card"]
            )
        if form.cleaned_data["has_rosa_kit"]:
            self.leaving_request.is_rosa_user = yes_no_to_bool(
                form.cleaned_data["has_rosa_kit"]
            )
        self.leaving_request.save(
            update_fields=[
                "holds_government_procurement_card",
                "is_rosa_user",
            ]
        )
        if form.cleaned_data["has_dse"]:
            self.leaver_info.has_dse = yes_no_to_bool(form.cleaned_data["has_dse"])
            # Clear DSE assets
            if not self.leaver_info.has_dse:
                self.store_display_screen_equipment(dse_assets=[])

        self.leaver_info.save(
            update_fields=[
                "has_dse",
            ]
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page_title = "Return pass and other assets"
        if not self.user_is_leaver:
            page_title = "Other goverment assets"

        context.update(page_title=page_title)

        return context


class HasCirrusEquipmentView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/cirrus/has_equipment.html"
    form_class = leaver_forms.HasCirrusKitForm
    extra_context = {"page_title": "Return Cirrus kit"}

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        user_assets = self.get_cirrus_assets()

        if user_assets:
            return redirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.leaver_info.has_cirrus_kit is not None:
            initial.update(
                has_cirrus_kit=bool_to_yes_no(self.leaver_info.has_cirrus_kit),
            )
        return initial

    def form_valid(self, form):
        has_cirrus_kit: Literal["yes", "no"] = form.cleaned_data["has_cirrus_kit"]

        self.leaver_info.has_cirrus_kit = yes_no_to_bool(has_cirrus_kit)
        self.leaver_info.save(update_fields=["has_cirrus_kit"])

        if has_cirrus_kit == "no":
            self.success_viewname = "leaver-display-screen-equipment"

        return super().form_valid(form)


class DeleteCirrusEquipmentView(LeavingRequestViewMixin, RedirectView):
    pattern_name = "leaver-cirrus-equipment"

    def get_redirect_url(self, *args, **kwargs) -> Optional[str]:
        del kwargs["kit_uuid"]
        return super().get_redirect_url(*args, **kwargs)

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        kit_uuid: uuid.UUID = kwargs["kit_uuid"]

        session = self.get_session()
        if "cirrus_assets" in session:
            for asset in session["cirrus_assets"]:
                if asset["uuid"] == str(kit_uuid):
                    session["cirrus_assets"].remove(asset)
                    self.store_session(session)
                    break

        return super().get(request, *args, **kwargs)


class CirrusEquipmentView(LeavingJourneyViewMixin, BaseTemplateView):
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": leaver_forms.AddCirrusAssetForm,
        "cirrus_return_form": leaver_forms.CirrusReturnFormWithAssets,
        "cirrus_return_form_no_assets": leaver_forms.CirrusReturnFormNoAssets,
    }
    template_name = "leaving/leaver/cirrus/equipment.html"
    extra_context = {"page_title": "Return Cirrus kit"}

    def post_add_asset_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        session = self.get_session()
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
        self.store_session(session)

        # Redirect to the GET method
        return redirect(
            "leaver-cirrus-equipment",
            leaving_request_uuid=self.leaving_request.uuid,
        )

    def post_cirrus_return_form_no_assets(
        self, request: HttpRequest, form: Form, *args, **kwargs
    ):
        # Store correction info and assets into the leaver details
        self.store_cirrus_kit_information(
            cirrus_assets=[],
        )
        return redirect(self.get_success_url())

    def post_cirrus_return_form(
        self, request: HttpRequest, form: Form, *args, **kwargs
    ):
        session = self.get_session()

        # Store correction info and assets into the leaver details
        self.store_cirrus_kit_information(
            cirrus_assets=session.get("cirrus_assets", []),
        )

        form_data = form.cleaned_data
        return_option = form.cleaned_data["return_option"]

        # Store return information
        self.store_return_option(
            return_option=return_option,
        )
        if return_option == ReturnOptions.OFFICE.value:
            self.store_return_information(
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
                personal_phone=form.cleaned_data["home_personal_phone"],
                contact_email=form.cleaned_data["home_contact_email"],
                address=return_address,
            )

        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "form_name" in request.POST:
            form_name = request.POST["form_name"]
            if form_name in self.forms:
                form = self.forms[form_name](
                    data=request.POST, **self.get_form_kwargs()
                )
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

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            form_initial = getattr(self, f"get_initial_{form_name}")()
            context[form_name] = form_class(
                initial=form_initial, **self.get_form_kwargs()
            )

        context.update(cirrus_assets=self.get_cirrus_assets())

        return context


class DeleteDSEView(LeavingRequestViewMixin, RedirectView):
    pattern_name = "leaver-display-screen-equipment"

    def get_redirect_url(self, *args, **kwargs) -> Optional[str]:
        del kwargs["kit_uuid"]
        return super().get_redirect_url(*args, **kwargs)

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        kit_uuid: uuid.UUID = kwargs["kit_uuid"]

        session = self.get_session()
        if "dse_assets" in session:
            for asset in session["dse_assets"]:
                if asset["uuid"] == str(kit_uuid):
                    session["dse_assets"].remove(asset)
                    self.store_session(session)
                    break

        return super().get(request, *args, **kwargs)


class DisplayScreenEquipmentView(LeavingJourneyViewMixin, BaseTemplateView):
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": leaver_forms.AddDisplayScreenEquipmentAssetForm,
        "submission_form": leaver_forms.DisplayScreenEquipmentSubmissionForm,
    }
    template_name = "leaving/leaver/display_screen_equipment.html"
    extra_context = {"page_title": "Return DIT-owned equipment over £150"}

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not self.leaver_info.has_dse:
            return redirect(super().get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def post_add_asset_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        session = self.get_session()
        if "dse_assets" not in session:
            session["dse_assets"] = []

        # Add asset to session
        asset: types.DisplayScreenEquipmentAsset = {
            "uuid": str(uuid.uuid4()),
            "name": form.cleaned_data["asset_name"],
        }
        session["dse_assets"].append(asset)
        self.store_session(session)

        # Redirect to the GET method
        return redirect(
            "leaver-display-screen-equipment",
            leaving_request_uuid=self.leaving_request.uuid,
        )

    def post_submission_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        session = self.get_session()

        # Store dse assets into the leaver details
        self.store_display_screen_equipment(
            dse_assets=session.get("dse_assets", []),
        )

        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "form_name" in request.POST:
            form_name = request.POST["form_name"]
            if form_name in self.forms:
                form = self.forms[form_name](
                    data=request.POST, **self.get_form_kwargs()
                )
                if form.is_valid():
                    # Call the "post_{form_name}" method to handle the form POST logic.
                    return getattr(self, f"post_{form_name}")(
                        request, form, *args, **kwargs
                    )
                else:
                    context[form_name] = form
        return self.render_to_response(context)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        session = self.get_session()
        if "dse_assets" not in session:
            session["dse_assets"] = []
            self.store_session(session)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            context[form_name] = form_class(**self.get_form_kwargs())

        session = self.get_session()
        if "dse_assets" in session:
            context["dse_assets"] = session["dse_assets"]

        return context


class LeaverContactDetailsView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/personal_contact_details.html"
    form_class = leaver_forms.LeaverContactDetailsForm

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

        page_title = "Personal contact details"
        if not self.user_is_leaver:
            leaver_name = self.leaving_request.get_leaver_name()
            possessive_leaver_name = make_possessive(leaver_name)

            page_title = f"{possessive_leaver_name} personal contact details"

        context.update(
            page_title=page_title,
            has_dse=self.leaver_info.has_dse,
        )
        return context

    def get_back_link_url(self):
        if not self.leaver_info.has_dse:
            return reverse(
                "leaver-has-cirrus-equipment",
                kwargs={"leaving_request_uuid": self.leaving_request.uuid},
            )

        return reverse(
            "leaver-display-screen-equipment",
            kwargs={"leaving_request_uuid": self.leaving_request.uuid},
        )


class ConfirmDetailsView(LeavingJourneyViewMixin, BaseTemplateView, FormView):
    template_name = "leaving/leaver/confirm_details.html"
    form_class = leaver_forms.LeaverConfirmationForm
    extra_context = {"page_title": "Check and confirm your answers"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leaver_name = self.leaving_request.get_leaver_name()
        possessive_leaver_name = make_possessive(leaver_name)

        context.update(
            leaving_request=self.leaving_request,
            possessive_leaver_name=possessive_leaver_name,
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
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Check we have all the required information before we continue.
        """
        user = cast(User, self.request.user)

        # Mark the request as being completed by the leaver or someone else
        if not self.user_is_leaver:
            self.leaving_request.completed_by_leaver = False

        self.leaving_request.leaver_complete = timezone.now()
        self.leaving_request.save()

        # Create the workflow
        self.create_workflow(requester=user)

        return super().form_valid(form)


class RequestReceivedView(LeavingJourneyViewMixin, BaseTemplateView):
    template_name = "leaving/leaver/request_received.html"

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not self.user_is_leaver:
            return redirect(
                reverse(
                    "line-manager-start",
                    kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                )
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Thank you",
            leaver_info=self.leaver_info,
            leaving_request=self.leaving_request,
            reason_for_leaving=self.leaving_request.reason_for_leaving,
        )
        return context
