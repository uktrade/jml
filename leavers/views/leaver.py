import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Type, cast

from django.contrib.auth.decorators import login_required
from django.forms import Form
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder import get_people_finder_interface
from core.service_now import get_service_now_interface
from core.service_now import types as service_now_types
from core.staff_search.forms import SearchForm
from core.staff_search.views import StaffSearchView
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    StaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
    search_staff_index,
)
from leavers import forms, types
from leavers.models import LeaverInformation, ReturnOption
from leavers.utils import update_or_create_leaving_request  # /PS-IGNORE
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
                email_address=user.email,
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find leaver in the Staff SSO ActivityStream.")

        self.exclude_staff_ids = [leaver_activitystream_user.identifier]
        return super().dispatch(request, *args, **kwargs)


class LeaverInformationMixin:
    people_finder_search = get_people_finder_interface()

    def get_leaver_information(self, email: str, requester: User) -> LeaverInformation:
        """
        Get the Leaver information stored in the DB
        Creates a new model if one doesn't exist.
        """

        try:
            leaver_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                email_address=email,
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            raise Exception("Unable to find leaver in the Staff SSO ActivityStream.")

        leaving_request = update_or_create_leaving_request(
            leaver=leaver_activitystream_user,
            user_requesting=requester,
        )

        try:
            leaver_info = LeaverInformation.objects.get(
                leaving_request=leaving_request, leaver_email=email
            )
        except LeaverInformation.DoesNotExist:
            leaver_info = LeaverInformation.objects.create(
                leaving_request=leaving_request,
                leaver_email=email,
                updates={},
            )
        return leaver_info

    def get_leaver_details(self, email: str) -> types.LeaverDetails:
        """
        Get the Leaver details from People Finder
        Raises an exception People Finder doesn't return a result.
        """

        staff_documents = search_staff_index(query=email)
        consolidated_staff_document: Optional[ConsolidatedStaffDocument] = None

        if len(staff_documents) == 0:
            raise Exception("Unable to find leaver in the Staff Index.")

        consolidated_staff_document = consolidate_staff_documents(
            staff_documents=[staff_documents[0]]
        )[0]
        leaver_details: types.LeaverDetails = {
            # Personal details
            "first_name": consolidated_staff_document["first_name"],
            "last_name": consolidated_staff_document["last_name"],
            "date_of_birth": datetime.strptime(
                consolidated_staff_document["date_of_birth"], "%d-%m-%Y"
            ).date(),
            "contact_email_address": consolidated_staff_document[
                "contact_email_address"
            ],
            "contact_phone": consolidated_staff_document["contact_phone"],
            "contact_address": consolidated_staff_document["contact_address"],
            # Professional details
            "grade": consolidated_staff_document["grade"],
            "job_title": consolidated_staff_document["job_title"],
            "department": consolidated_staff_document["department"],
            "directorate": consolidated_staff_document["directorate"],
            "email_address": consolidated_staff_document["email_address"],
            "staff_id": consolidated_staff_document["staff_id"],
            # Misc.
            "photo": consolidated_staff_document["photo"],
        }
        return leaver_details

    def get_leaver_detail_updates(
        self, email: str, requester: User
    ) -> types.LeaverDetailUpdates:
        """
        Get the stored updates for the Leaver.
        """

        leaver_info = self.get_leaver_information(
            email=email,
            requester=requester,
        )
        updates: types.LeaverDetailUpdates = leaver_info.updates
        return updates

    def store_leaver_detail_updates(
        self, email: str, requester: User, updates: types.LeaverDetailUpdates
    ):
        """
        Store updates for the Leaver.
        """

        leaver_info = self.get_leaver_information(
            email=email,
            requester=requester,
        )

        # Work out what information is new and only store that.
        existing_data = self.get_leaver_details(email=email)
        new_data: types.LeaverDetailUpdates = {}
        for key, value in updates.items():
            if key not in existing_data or existing_data.get(key) != value:
                new_data[key] = value  # type: ignore

        # Store the updates
        leaver_info.updates = new_data
        leaver_info.save(update_fields=["updates"])

    def get_leaver_details_with_updates(
        self, email: str, requester: User
    ) -> types.LeaverDetails:
        leaver_details = self.get_leaver_details(email=email)
        leaver_details_updates = self.get_leaver_detail_updates(
            email=email, requester=requester
        )
        leaver_details.update(**leaver_details_updates)  # type: ignore
        return leaver_details

    def get_leaver_details_with_updates_for_display(
        self,
        email: str,
        requester: User,
    ) -> types.LeaverDetails:
        leaver_details = self.get_leaver_details_with_updates(
            email=email, requester=requester
        )
        # Get data from Service Now /PS-IGNORE
        service_now_interface = get_service_now_interface()
        # Get the Department's Name from Service Now
        if leaver_details["department"]:
            service_now_departments = service_now_interface.get_departments(
                sys_id=leaver_details["department"]
            )
            if len(service_now_departments) != 1:
                raise Exception("Issue finding department in Service Now")
            leaver_details["department"] = service_now_departments[0]["name"]

        # Get the Directorate's Name from Service Now
        if leaver_details["directorate"]:
            service_now_directorate = service_now_interface.get_directorates(
                sys_id=leaver_details["directorate"]
            )
            if len(service_now_directorate) != 1:
                raise Exception("Issue finding directorate in Service Now")
            leaver_details["directorate"] = service_now_directorate[0]["name"]

        return leaver_details

    def store_leaving_date(self, email: str, requester: User, leaving_date: date):
        """
        Store the leaving date
        """

        leaver_info = self.get_leaver_information(
            email=email,
            requester=requester,
        )
        leaver_info.leaving_date = leaving_date
        leaver_info.save(update_fields=["leaving_date"])

    def store_correction_information(
        self,
        email: str,
        requester: User,
        information_is_correct: bool,
        additional_information: str,
    ):
        """
        Store the Correction information
        """

        leaver_info = self.get_leaver_information(email=email, requester=requester)
        leaver_info.information_is_correct = information_is_correct
        leaver_info.additional_information = additional_information
        leaver_info.save(
            update_fields=[
                "information_is_correct",
                "additional_information",
            ]
        )

    def store_return_option(
        self, email: str, requester: User, return_option: ReturnOption
    ):
        leaver_info = self.get_leaver_information(email=email, requester=requester)
        leaver_info.return_option = return_option
        leaver_info.save(update_fields=["return_option"])

    def store_return_information(
        self,
        email: str,
        requester: User,
        personal_phone: str,
        contact_email: str,
        address: Optional[service_now_types.Address],
    ):
        leaver_info = self.get_leaver_information(email=email, requester=requester)
        leaver_info.return_personal_phone = personal_phone
        leaver_info.return_contact_email = contact_email
        if address:
            leaver_info.return_address_building_and_street = address[
                "building_and_street"
            ]
            leaver_info.return_address_city = address["city"]
            leaver_info.return_address_county = address["county"]
            leaver_info.return_address_postcode = address["postcode"]
        leaver_info.save(
            update_fields=[
                "return_personal_phone",
                "return_contact_email",
                "return_address_building_and_street",
                "return_address_city",
                "return_address_county",
                "return_address_postcode",
            ]
        )

    def submit_to_service_now(
        self, email: str, requester: User, assets: List[service_now_types.AssetDetails]
    ):
        # Note: When this is called, make sure the assets have been cleared
        # from the Session.
        leaver_info = self.get_leaver_information(email=email, requester=requester)
        leaver_details = self.get_leaver_details_with_updates(
            email=email, requester=requester
        )
        service_now_interface = get_service_now_interface()
        service_now_interface.submit_leaver_request(
            leaver_info=leaver_info,
            leaver_details=leaver_details,
            assets=assets,
        )


class ConfirmDetailsView(LeaverInformationMixin, FormView):  # /PS-IGNORE
    template_name = "leaving/leaver/confirm_details.html"
    form_class = forms.LeaverConfirmationForm
    success_url = reverse_lazy("leaver-kit")

    def dispatch(self, request, *args, **kwargs):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        self.leaver_info = self.get_leaver_information(email=user_email, requester=user)

        manager_id: Optional[str] = request.GET.get(MANAGER_SEARCH_PARAM, None)
        if manager_id:
            manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_uuid=manager_id,
            )

            try:
                manager = ActivityStreamStaffSSOUser.objects.get(
                    identifier=manager_staff_document["staff_sso_activity_stream_id"],
                )
            except ActivityStreamStaffSSOUser.DoesNotExist:
                raise Exception(
                    "Unable to find manager in the Staff SSO ActivityStream."
                )

            if self.leaver_info.leaving_request.manager_activitystream_user != manager:
                self.leaver_info.leaving_request.manager_activitystream_user = manager
                self.leaver_info.leaving_request.save()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        # Get the Leaver details
        leaver_details = self.get_leaver_details_with_updates(
            email=user_email, requester=user
        )
        display_leaver_details = self.get_leaver_details_with_updates_for_display(
            email=user_email,
            requester=user,
        )
        context.update(leaver_details=display_leaver_details),

        manager: Optional[ConsolidatedStaffDocument] = None
        if self.leaver_info.leaving_request.manager_activitystream_user:
            manager_staff_document: StaffDocument = get_staff_document_from_staff_index(
                staff_id=self.leaver_info.leaving_request.manager_activitystream_user.identifier,
            )
            manager: ConsolidatedStaffDocument = consolidate_staff_documents(
                staff_documents=[manager_staff_document],
            )[0]
        manager_search = reverse("leaver-manager-search")
        context.update(
            manager=manager,
            manager_search=reverse("leaver-manager-search"),
            manager_search_form=SearchForm(),
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

        # Add an error message if the required details are missing
        if not forms.LeaverUpdateForm(data=leaver_details).is_valid():
            edit_path = reverse("leaver-update-details")
            errors.append(
                mark_safe(
                    f"<a href='{edit_path}'>There is missing information that "
                    "is required to continue, please edit the details on this "
                    "page.</a>"
                )
            )
        context.update(errors=errors)
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Check we have all the required information before we continue.
        """
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        # Store the leaving date
        self.store_leaving_date(
            email=user_email,
            requester=user,
            leaving_date=form.cleaned_data["last_day"],
        )

        # Get the person details with the updates.
        leaver_details = self.get_leaver_details_with_updates(
            email=user_email, requester=user
        )
        update_form = forms.LeaverUpdateForm(data=leaver_details)
        if update_form.is_valid():
            return super().form_valid(form)
        return self.form_invalid(form)


class UpdateDetailsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/update_details.html"
    form_class = forms.LeaverUpdateForm
    success_url = reverse_lazy("leaver-confirm-details")

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        self.initial = dict(
            self.get_leaver_details_with_updates(email=user_email, requester=user)
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        updates: types.LeaverDetailUpdates = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "contact_email_address": form.cleaned_data["contact_email_address"],
            "contact_phone": form.cleaned_data["contact_phone"],
            "contact_address": form.cleaned_data["contact_address"],
            "grade": form.cleaned_data["grade"],
            "job_title": form.cleaned_data["job_title"],
            "department": form.cleaned_data["department"],
            "directorate": form.cleaned_data["directorate"],
            "email_address": form.cleaned_data["email_address"],
            "staff_id": form.cleaned_data["staff_id"],
        }

        self.store_leaver_detail_updates(
            email=user_email, requester=user, updates=updates
        )
        return super().form_valid(form)


@login_required
def delete_kit(request: HttpRequest, kit_uuid: uuid.UUID):
    if "assets" in request.session:
        for asset in request.session["assets"]:
            if asset["uuid"] == str(kit_uuid):
                request.session["assets"].remove(asset)
                request.session.save()
                break
    return redirect("leaver-kit")


class KitView(LeaverInformationMixin, TemplateView):  # /PS-IGNORE
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": forms.AddAssetForm,
        "correction_form": forms.CorrectionForm,
    }
    template_name = "leaving/leaver/kit.html"
    success_url = reverse_lazy("leaver-return-options")

    def post_add_asset_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        session = request.session
        if "assets" not in session:
            session["assets"] = []

        # Add asset to session
        asset = {
            "uuid": str(uuid.uuid4()),
            "sys_id": None,
            "tag": None,
            "name": form.cleaned_data["asset_name"],
        }
        session["assets"].append(asset)
        session.save()

        # Redirect to the GET method
        return redirect("leaver-kit")

    def post_correction_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        form_data = form.cleaned_data

        # Store correction info and assets into the leaver details
        self.store_correction_information(
            email=user_email,
            requester=user,
            information_is_correct=bool(form_data["is_correct"] == "yes"),
            additional_information=form_data["whats_incorrect"],
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
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        if "assets" not in request.session:
            service_now_interface = get_service_now_interface()
            request.session["assets"] = [
                {
                    "uuid": str(uuid.uuid4()),
                    "sys_id": asset["sys_id"],
                    "tag": asset["tag"],
                    "name": asset["name"],
                }
                for asset in service_now_interface.get_assets_for_user(email=user_email)
            ]
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            context[form_name] = form_class()
        if "assets" in self.request.session:
            context["assets"] = self.request.session["assets"]
        return context


class EquipmentReturnOptionsView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/equipment_options.html"
    form_class = forms.ReturnOptionForm
    success_url = reverse_lazy("leaver-return-information")

    def form_valid(self, form):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        self.store_return_option(
            email=user_email,
            requester=user,
            return_option=form.cleaned_data["return_option"],
        )

        return super().form_valid(form)


class EquipmentReturnInformationView(LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/equipment_information.html"
    form_class = forms.ReturnInformationForm
    success_url = reverse_lazy("leaver-request-received")

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()

        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        leaver_info = self.get_leaver_information(email=user_email, requester=user)
        if leaver_info.return_option == ReturnOption.OFFICE:
            kwargs.update(hide_address=True)

        return kwargs

    def form_valid(self, form):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        leaver_info = self.get_leaver_information(
            email=user_email, requester=self.request.user
        )

        address: Optional[service_now_types.Address] = None
        if leaver_info.return_option == ReturnOption.HOME:
            address = {
                "building_and_street": form.cleaned_data["address_building"],
                "city": form.cleaned_data["address_city"],
                "county": form.cleaned_data["address_county"],
                "postcode": form.cleaned_data["address_postcode"],
            }

        self.store_return_information(
            email=user_email,
            requester=user,
            personal_phone=form.cleaned_data["personal_phone"],
            contact_email=form.cleaned_data["contact_email"],
            address=address,
        )

        return super().form_valid(form)


class RequestReceivedView(LeaverInformationMixin, TemplateView):
    template_name = "leaving/leaver/request_received.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        context = super().get_context_data(**kwargs)
        context.update(
            leaver_info=self.get_leaver_information(email=user_email, requester=user)
        )
        return context
