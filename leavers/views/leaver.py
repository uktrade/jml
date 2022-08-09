import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, cast

from django.forms import Form
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser, ServiceEmailAddress
from core.people_finder import get_people_finder_interface
from core.service_now import get_service_now_interface
from core.staff_search.views import StaffSearchView
from core.types import Address
from core.utils.helpers import bool_to_yes_no
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
)
from leavers import types
from leavers.forms import leaver as leaver_forms
from leavers.forms.leaver import ReturnOptions
from leavers.models import LeaverInformation, LeavingRequest
from leavers.progress_indicator import ProgressIndicator, StepDict
from leavers.utils.leaving_request import update_or_create_leaving_request
from leavers.workflow.utils import get_or_create_leaving_workflow
from user.models import User

MANAGER_SEARCH_PARAM = "manager_id"


class MyManagerSearchView(StaffSearchView):
    success_url = reverse_lazy("leaver-confirm-details")
    search_name = "manager"
    query_param_name = MANAGER_SEARCH_PARAM

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)
        try:
            leaver_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                email_user_id=user.sso_email_user_id,
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
    leaver_details: Optional[types.LeaverDetails] = None

    def get_leaver_activitystream_user(
        self, sso_email_user_id: str
    ) -> ActivityStreamStaffSSOUser:
        if not self.leaver_activitystream_user:
            try:
                self.leaver_activity_stream_user = (
                    ActivityStreamStaffSSOUser.objects.get(
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

    def get_leaver_details(self, sso_email_user_id: str) -> types.LeaverDetails:
        """
        Get the Leaver details from Index
        Raises an exception if Index doesn't have a record.
        """

        if self.leaver_details:
            return self.leaver_details

        staff_document = get_staff_document_from_staff_index(
            sso_email_user_id=sso_email_user_id
        )

        consolidated_staff_document = consolidate_staff_documents(
            staff_documents=[staff_document]
        )[0]
        self.leaver_details: types.LeaverDetails = {
            # Personal details
            "first_name": consolidated_staff_document["first_name"],
            "last_name": consolidated_staff_document["last_name"],
            "contact_email_address": consolidated_staff_document[
                "contact_email_address"
            ],
            # Professional details
            "job_title": consolidated_staff_document["job_title"],
            "directorate": "",
            "staff_id": consolidated_staff_document["staff_id"],
            # Misc.
            "photo": consolidated_staff_document["photo"],
        }
        return self.leaver_details

    def get_leaver_detail_updates(
        self, sso_email_user_id: str, requester: User
    ) -> types.LeaverDetailUpdates:
        """
        Get the stored updates for the Leaver.
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )
        leaver_info.refresh_from_db()
        updates: types.LeaverDetailUpdates = leaver_info.updates
        return updates

    def store_leaver_detail_updates(
        self,
        sso_email_user_id: str,
        requester: User,
        updates: types.LeaverDetailUpdates,
    ) -> None:
        """
        Store updates for the Leaver.
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )

        # Work out what information is new and only store that.
        existing_data = self.get_leaver_details(sso_email_user_id=sso_email_user_id)
        new_data: types.LeaverDetailUpdates = {}
        for key, value in updates.items():
            if key not in existing_data or existing_data.get(key) != value:
                new_data[key] = value  # type: ignore

        # Store the updates
        leaver_info.updates = new_data

        # Store the data against the leaver info
        leaver_info.leaver_first_name = updates.get("first_name", "")
        leaver_info.leaver_last_name = updates.get("last_name", "")
        leaver_info.personal_email = updates.get("contact_email_address", "")
        leaver_info.job_title = updates.get("job_title", "")
        leaver_info.directorate_id = updates.get("directorate", "")

        # Save the leaver info
        leaver_info.save(
            update_fields=[
                "updates",
                "leaver_first_name",
                "leaver_last_name",
                "personal_email",
                "job_title",
                "directorate_id",
                "staff_id",
            ]
        )

    def get_leaving_dates(
        self,
        sso_email_user_id: str,
        requester: User,
    ) -> Dict[str, Any]:
        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )
        leaver_info.refresh_from_db()

        last_day: Optional[date] = None
        if leaver_info.last_day:
            last_day = leaver_info.last_day.date()
        leaving_date: Optional[date] = None
        if leaver_info.leaving_date:
            leaving_date = leaver_info.leaving_date.date()

        return {
            "last_day": last_day,
            "leaving_date": leaving_date,
        }

    def get_leaver_extra_details(
        self,
        sso_email_user_id: str,
        requester: User,
    ) -> Dict[str, Any]:
        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )
        leaver_info.refresh_from_db()
        leaving_request: LeavingRequest = leaver_info.leaving_request

        # Convert yes/no to boolean values.
        has_locker = None
        if leaver_info.has_locker is not None:
            has_locker = bool_to_yes_no(leaver_info.has_locker)

        has_rosa_kit = None
        if leaving_request.is_rosa_user is not None:
            has_rosa_kit = bool_to_yes_no(leaving_request.is_rosa_user)

        has_gov_procurement_card = None
        if leaving_request.holds_government_procurement_card is not None:
            has_gov_procurement_card = bool_to_yes_no(
                leaving_request.holds_government_procurement_card
            )

        has_dse = None
        if leaver_info.has_dse is not None:
            has_dse = bool_to_yes_no(leaver_info.has_dse)

        return {
            "security_clearance": leaving_request.security_clearance,
            "date_of_birth": leaver_info.leaver_date_of_birth,
            "has_locker": has_locker,
            "has_rosa_kit": has_rosa_kit,
            "has_gov_procurement_card": has_gov_procurement_card,
            "has_dse": has_dse,
            "staff_type": leaving_request.staff_type,
            "contact_phone": leaver_info.contact_phone,
            "contact_address_line_1": leaver_info.contact_address_line_1,
            "contact_address_line_2": leaver_info.contact_address_line_2,
            "contact_address_city": leaver_info.contact_address_city,
            "contact_address_county": leaver_info.contact_address_county,
            "contact_address_postcode": leaver_info.contact_address_postcode,
        }

    def store_leaver_extra_details(
        self,
        sso_email_user_id: str,
        requester: User,
        date_of_birth: date,
        security_clearance: str,
        has_locker: bool,
        has_gov_procurement_card: bool,
        has_rosa_kit: bool,
        has_dse: bool,
        staff_type: str,
        contact_phone: str,
        contact_address_line_1: str,
        contact_address_line_2: str,
        contact_address_city: str,
        contact_address_county: str,
        contact_address_postcode: str,
    ) -> None:
        """
        Store Extra details for the Leaver.
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )

        leaver_info.leaving_request.security_clearance = security_clearance
        leaver_info.leaving_request.is_rosa_user = has_rosa_kit
        leaver_info.leaving_request.holds_government_procurement_card = (
            has_gov_procurement_card
        )
        leaver_info.leaving_request.staff_type = staff_type
        leaver_info.leaving_request.save(
            update_fields=[
                "security_clearance",
                "is_rosa_user",
                "holds_government_procurement_card",
                "staff_type",
            ]
        )

        leaver_info.leaver_date_of_birth = date_of_birth
        leaver_info.has_locker = has_locker
        leaver_info.has_dse = has_dse
        leaver_info.contact_phone = contact_phone
        leaver_info.contact_address_line_1 = contact_address_line_1
        leaver_info.contact_address_line_2 = contact_address_line_2
        leaver_info.contact_address_city = contact_address_city
        leaver_info.contact_address_county = contact_address_county
        leaver_info.contact_address_postcode = contact_address_postcode
        leaver_info.save(
            update_fields=[
                "leaver_date_of_birth",
                "has_locker",
                "has_dse",
                "contact_phone",
                "contact_address_line_1",
                "contact_address_line_2",
                "contact_address_city",
                "contact_address_county",
                "contact_address_postcode",
            ]
        )

    def get_leaver_details_with_updates(
        self, sso_email_user_id: str, requester: User
    ) -> types.LeaverDetails:
        leaver_details = self.get_leaver_details(sso_email_user_id=sso_email_user_id)
        leaver_details_updates = self.get_leaver_detail_updates(
            sso_email_user_id=sso_email_user_id, requester=requester
        )
        leaver_details.update(**leaver_details_updates)  # type: ignore
        return leaver_details

    def get_leaver_details_with_updates_for_display(
        self,
        sso_email_user_id: str,
        requester: User,
    ) -> types.LeaverDetails:
        leaver_details = self.get_leaver_details_with_updates(
            sso_email_user_id=sso_email_user_id, requester=requester
        )
        # Get data from Service Now /PS-IGNORE
        service_now_interface = get_service_now_interface()

        # Get the Directorate's Name from Service Now
        if leaver_details["directorate"]:
            service_now_directorate = service_now_interface.get_directorates(
                sys_id=leaver_details["directorate"]
            )
            if len(service_now_directorate) != 1:
                raise Exception("Issue finding directorate in Service Now")
            leaver_details["directorate"] = service_now_directorate[0]["name"]

        return leaver_details

    def store_leaving_dates(
        self,
        sso_email_user_id: str,
        requester: User,
        last_day: date,
        leaving_date: date,
    ) -> None:
        """
        Store the leaving date
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id,
            requester=requester,
        )

        last_day_datetime = datetime(last_day.year, last_day.month, last_day.day)
        leaving_date_datetime = datetime(
            leaving_date.year, leaving_date.month, leaving_date.day
        )

        leaver_info.last_day = timezone.make_aware(last_day_datetime)
        leaver_info.leaving_date = timezone.make_aware(leaving_date_datetime)
        leaver_info.save(
            update_fields=[
                "last_day",
                "leaving_date",
            ]
        )

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
        information_is_correct: bool,
        additional_information: str,
        cirrus_assets: List[types.CirrusAsset],
    ) -> None:
        """
        Store the Correction information
        """

        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=requester
        )

        leaver_info.cirrus_assets = cirrus_assets
        leaver_info.information_is_correct = information_is_correct
        leaver_info.additional_information = additional_information
        leaver_info.save(
            update_fields=[
                "cirrus_assets",
                "information_is_correct",
                "additional_information",
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


class LeaverProgressIndicator(ProgressIndicator):
    def __init__(self, current_step: str) -> None:
        super().__init__(current_step=current_step)
        self.steps: List[Tuple[str, str, str]] = [
            ("your_details", "Your details", "leaver-update-details"),
            (
                "cirrus_equipment",
                "Cirrus kit",
                "leaver-has-cirrus-equipment",
            ),
            (
                "display_screen_equipment",
                "IT equipment",
                "leaver-display-screen-equipment",
            ),
            ("confirmation", "Confirmation", "leaver-confirm-details"),
        ]

    def get_progress_steps(self, *args, **kwargs) -> List[StepDict]:
        """
        Build the list of progress steps
        """
        leaver_info: LeaverInformation = kwargs["leaver_info"]
        for step in self.steps:
            if not leaver_info.has_dse and step[0] == "display_screen_equipment":
                self.steps.remove(step)

        return super().get_progress_steps(*args, **kwargs)


class UpdateDetailsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/update_details.html"
    form_class = leaver_forms.LeaverUpdateForm
    success_url = reverse_lazy("leaver-has-cirrus-equipment")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("your_details")

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
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        initial = super().get_initial()
        initial.update(
            **self.get_leaver_details_with_updates(
                sso_email_user_id=sso_email_user_id, requester=user
            )
        )
        initial.update(
            **self.get_leaver_extra_details(
                sso_email_user_id=sso_email_user_id, requester=user
            )
        )
        initial.update(
            **self.get_leaving_dates(
                sso_email_user_id=sso_email_user_id, requester=user
            )
        )

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title=self.progress_indicator.get_current_step_label())
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        display_leaver_details = self.get_leaver_details_with_updates_for_display(
            sso_email_user_id=sso_email_user_id,
            requester=user,
        )
        leaver_first_name = display_leaver_details["first_name"]
        leaver_last_name = display_leaver_details["last_name"]
        context.update(leaver_name=f"{leaver_first_name} {leaver_last_name}")

        context.update(
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            )
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        updates: types.LeaverDetailUpdates = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "contact_email_address": form.cleaned_data["contact_email_address"],
            "job_title": form.cleaned_data["job_title"],
            "directorate": form.cleaned_data["directorate"],
        }

        self.store_leaver_detail_updates(
            sso_email_user_id=sso_email_user_id, requester=user, updates=updates
        )
        self.store_leaver_extra_details(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            date_of_birth=form.cleaned_data["date_of_birth"],
            security_clearance=form.cleaned_data["security_clearance"],
            has_locker=bool(form.cleaned_data["has_locker"] == "yes"),
            has_gov_procurement_card=bool(
                form.cleaned_data["has_gov_procurement_card"] == "yes"
            ),
            has_rosa_kit=bool(form.cleaned_data["has_rosa_kit"] == "yes"),
            has_dse=bool(form.cleaned_data["has_dse"] == "yes"),
            staff_type=form.cleaned_data["staff_type"],
            contact_phone=form.cleaned_data["contact_phone"],
            contact_address_line_1=form.cleaned_data["contact_address_line_1"],
            contact_address_line_2=form.cleaned_data["contact_address_line_2"],
            contact_address_city=form.cleaned_data["contact_address_city"],
            contact_address_county=form.cleaned_data["contact_address_county"],
            contact_address_postcode=form.cleaned_data["contact_address_postcode"],
        )
        self.store_leaving_dates(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            last_day=form.cleaned_data["last_day"],
            leaving_date=form.cleaned_data["leaving_date"],
        )
        return super().form_valid(form)


def get_cirrus_assets(request: HttpRequest) -> List[types.CirrusAsset]:
    user = cast(User, request.user)

    staff_sso_user = ActivityStreamStaffSSOUser.objects.get(
        email_user_id=user.sso_email_user_id
    )

    service_now_email: Optional[
        ServiceEmailAddress
    ] = ServiceEmailAddress.objects.filter(
        staff_sso_user=staff_sso_user,
    ).first()
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
                    email=service_now_email.service_now_email_address,
                )
            ]
    return request.session.get("cirrus_assets", [])


class HasCirrusEquipmentView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/cirrus/has_equipment.html"
    form_class = leaver_forms.HasCirrusKitForm
    success_url = reverse_lazy("leaver-cirrus-equipment")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("cirrus_equipment")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
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
        context.update(
            page_title=self.progress_indicator.get_current_step_label(),
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            ),
        )
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
        "correction_form": leaver_forms.CorrectionForm,
    }
    template_name = "leaving/leaver/cirrus/equipment.html"
    success_url = reverse_lazy("leaver-return-options")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("cirrus_equipment")

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

    def post_correction_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        user = cast(User, self.request.user)
        sso_email_user_id = cast(str, user.sso_email_user_id)

        form_data = form.cleaned_data

        # Store correction info and assets into the leaver details
        self.store_cirrus_kit_information(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            information_is_correct=bool(form_data["is_correct"] == "yes"),
            additional_information=form_data["whats_incorrect"],
            cirrus_assets=request.session.get("cirrus_assets", []),
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

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(page_title=self.progress_indicator.get_current_step_label())

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            context[form_name] = form_class()

        context.update(
            cirrus_assets=get_cirrus_assets(request=self.request),
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            ),
        )
        return context


class CirrusEquipmentReturnOptionsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/cirrus/equipment_options.html"
    form_class = leaver_forms.ReturnOptionForm
    success_url = reverse_lazy("leaver-return-information")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("cirrus_equipment")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if not self.leaver_info.cirrus_assets:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial["return_option"] = self.leaver_info.return_option
        return initial

    def form_valid(self, form):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        self.store_return_option(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            return_option=form.cleaned_data["return_option"],
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.progress_indicator.get_current_step_label(),
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            ),
        )
        return context


class CirrusEquipmentReturnInformationView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/cirrus/equipment_information.html"
    form_class = leaver_forms.ReturnInformationForm
    success_url = reverse_lazy("leaver-display-screen-equipment")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("cirrus_equipment")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        if not self.leaver_info.cirrus_assets:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial["personal_phone"] = (
            self.leaver_info.return_personal_phone or self.leaver_info.contact_phone
        )
        initial["contact_email"] = (
            self.leaver_info.return_contact_email or self.leaver_info.personal_email
        )
        initial["address_line_1"] = (
            self.leaver_info.return_address_line_1
            or self.leaver_info.contact_address_line_1
        )
        initial["address_line_2"] = (
            self.leaver_info.return_address_line_2
            or self.leaver_info.contact_address_line_2
        )
        initial["address_city"] = (
            self.leaver_info.return_address_city
            or self.leaver_info.contact_address_city
        )
        initial["address_county"] = (
            self.leaver_info.return_address_county
            or self.leaver_info.contact_address_county
        )
        initial["address_postcode"] = (
            self.leaver_info.return_address_postcode
            or self.leaver_info.contact_address_postcode
        )
        return initial

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        if self.leaver_info.return_option == ReturnOptions.OFFICE.value:
            kwargs.update(hide_address=True)

        return kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            page_title=self.progress_indicator.get_current_step_label(),
            return_option=self.leaver_info.return_option,
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            ),
        )
        return context

    def form_valid(self, form):
        user = cast(User, self.request.user)
        sso_email_user_id = cast(str, user.sso_email_user_id)
        leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=self.request.user
        )

        address: Optional[Address] = None
        if leaver_info.return_option == ReturnOptions.HOME.value:
            address: Address = {
                "line_1": form.cleaned_data["address_line_1"],
                "line_2": form.cleaned_data["address_line_2"],
                "town_or_city": form.cleaned_data["address_city"],
                "county": form.cleaned_data["address_county"],
                "postcode": form.cleaned_data["address_postcode"],
            }

        self.store_return_information(
            sso_email_user_id=sso_email_user_id,
            requester=user,
            personal_phone=form.cleaned_data["personal_phone"],
            contact_email=form.cleaned_data["contact_email"],
            address=address,
        )

        return super().form_valid(form)


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
    success_url = reverse_lazy("leaver-confirm-details")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("display_screen_equipment")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )

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
        context.update(page_title=self.progress_indicator.get_current_step_label())

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            context[form_name] = form_class()
        if "dse_assets" in self.request.session:
            context["dse_assets"] = self.request.session["dse_assets"]

        context.update(
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            )
        )
        return context


class ConfirmDetailsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/confirm_details.html"
    form_class = leaver_forms.LeaverConfirmationForm
    success_url = reverse_lazy("leaver-request-received")

    def __init__(self) -> None:
        super().__init__()
        self.progress_indicator = LeaverProgressIndicator("confirmation")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id
        self.leaver_info = self.get_leaver_information(
            sso_email_user_id=sso_email_user_id, requester=user
        )

        manager_id: Optional[str] = request.GET.get(MANAGER_SEARCH_PARAM, None)
        if manager_id:
            manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_uuid=manager_id,
            )

            try:
                manager = ActivityStreamStaffSSOUser.objects.get(
                    identifier=manager_staff_document.staff_sso_activity_stream_id,
                )
            except ActivityStreamStaffSSOUser.DoesNotExist:
                raise Exception(
                    "Unable to find manager in the Staff SSO ActivityStream."
                )

            if self.leaver_info.leaving_request.manager_activitystream_user != manager:
                self.leaver_info.leaving_request.manager_activitystream_user = manager
                self.leaver_info.leaving_request.save()
        return super().dispatch(request, *args, **kwargs)

    def get_manager(self) -> Optional[ConsolidatedStaffDocument]:
        manager: Optional[ConsolidatedStaffDocument] = None
        if self.leaver_info.leaving_request.manager_activitystream_user:
            sso_email_user_id = (
                self.leaver_info.leaving_request.manager_activitystream_user.email_user_id
            )
            manager_staff_document = get_staff_document_from_staff_index(
                sso_email_user_id=sso_email_user_id,
            )
            manager = cast(
                ConsolidatedStaffDocument,
                consolidate_staff_documents(
                    staff_documents=[manager_staff_document],
                )[0],
            )

        return manager

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        context.update(
            page_title=self.progress_indicator.get_current_step_label(),
            progress_steps=self.progress_indicator.get_progress_steps(
                leaver_info=self.leaver_info
            ),
            has_dse=self.leaver_info.has_dse,
            cirrus_assets=self.leaver_info.cirrus_assets,
            dse_assets=self.leaver_info.dse_assets,
            return_option=self.leaver_info.return_option,
            return_personal_phone=self.leaver_info.return_personal_phone,
            return_contact_email=self.leaver_info.return_contact_email,
            leaver_info=self.leaver_info,
            leaver_details=self.get_leaver_details_with_updates_for_display(
                sso_email_user_id=sso_email_user_id,
                requester=user,
            ),
        ),

        manager = self.get_manager()
        manager_search = reverse("leaver-manager-search")
        context.update(
            manager=manager,
            manager_search=manager_search,
        )

        # Build a list of errors to present to the user.
        errors: List[str] = []
        # Add an error message if the user hasn't selected a manager.
        if not manager:
            errors.append(
                mark_safe(
                    f"<a href='{manager_search}'>You need to inform us of your "
                    "line manager, please search for your manager below.</a>"
                )
            )

        context.update(errors=errors)
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Check we have all the required information before we continue.
        """
        user = cast(User, self.request.user)

        assert user.sso_email_user_id

        sso_email_user_id = user.sso_email_user_id

        # Check if a manager has been selected.
        if not self.get_manager():
            return self.form_invalid(form)

        leaving_request = self.get_leaving_request(
            sso_email_user_id=sso_email_user_id, requester=user
        )
        leaving_request.leaver_complete = timezone.now()
        leaving_request.save()

        # TODO: Send Leaver Thank you email

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
