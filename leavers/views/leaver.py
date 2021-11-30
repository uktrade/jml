import uuid
from datetime import date
from typing import Any, Dict, List, Optional, Type, cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.service_now import get_service_now_interface
from core.service_now import types as service_now_types
from core.utils.people_finder import search_people_finder
from leavers import forms, types
from leavers.models import LeaverInformation, ReturnOption
from user.models import User


class LeaverInformationMixin:
    def get_leaver_information(self, email: str) -> LeaverInformation:
        """
        Get the Leaver information stored in the DB
        Creates a new model if one doesn't exist.
        """

        try:
            leaver_info = LeaverInformation.objects.get(leaver_email=email)
        except LeaverInformation.DoesNotExist:
            leaver_info = LeaverInformation.objects.create(
                leaver_email=email, updates={}
            )
        return leaver_info

    def get_leaver_details(self, email: str) -> types.LeaverDetails:
        """
        Get the Leaver details from People Finder
        Raises an exception People Finder doesn't return a result.
        """

        people_finder_results = search_people_finder(search_term=email)
        if len(people_finder_results) > 0:
            person = people_finder_results[0]

            job_title = ""
            directorate = ""
            if "roles" in person and len(person["roles"]) > 0:
                job_title = person["roles"][0]["job_title"]
                directorate = person["roles"][0]["team"]["name"]

            # TODO: Map values to the blank leaver details
            leaver_details: types.LeaverDetails = {
                # Personal details
                "first_name": person["first_name"],
                "last_name": person["last_name"],
                "date_of_birth": date(2021, 11, 25),
                "personal_email": "",
                "personal_phone": person["primary_phone_number"],
                "personal_address": "",
                # Professional details
                "grade": person["grade"],
                "job_title": job_title,
                "department": "",
                "directorate": directorate,
                "work_email": person["email"],
                "manager": "",
                "staff_id": "",
                # Misc.
                "photo": person["photo"],
            }
            return leaver_details
        raise Exception("Issue finding user in People Finder")

    def get_leaver_detail_updates(self, email: str) -> types.LeaverDetailUpdates:
        """
        Get the stored updates for the Leaver.
        """

        leaver_info = self.get_leaver_information(email=email)
        updates: types.LeaverDetailUpdates = leaver_info.updates
        return updates

    def store_leaver_detail_updates(
        self, email: str, updates: types.LeaverDetailUpdates
    ):
        """
        Store updates for the Leaver.
        """

        leaver_info = self.get_leaver_information(email=email)

        # Work out what information is new and only store that.
        existing_data = self.get_leaver_details(email=email)
        new_data: types.LeaverDetailUpdates = {}
        for key, value in updates.items():
            if key not in existing_data or existing_data.get(key) != value:
                new_data[key] = value  # type: ignore

        # Store the updates
        leaver_info.updates = new_data
        leaver_info.save(update_fields=["updates"])

    def get_leaver_details_with_updates(self, email: str) -> types.LeaverDetails:
        leaver_details = self.get_leaver_details(email=email)
        leaver_details_updates = self.get_leaver_detail_updates(email=email)
        leaver_details.update(**leaver_details_updates)  # type: ignore
        return leaver_details

    def store_leaving_date(self, email: str, leaving_date: date):
        """
        Store the leaving date
        """

        leaver_info = self.get_leaver_information(email=email)
        leaver_info.leaving_date = leaving_date
        leaver_info.save(update_fields=["leaving_date"])

    def store_correction_information(
        self,
        email: str,
        information_is_correct: bool,
        additional_information: str,
    ):
        """
        Store the Correction information
        """

        leaver_info = self.get_leaver_information(email=email)
        leaver_info.information_is_correct = information_is_correct
        leaver_info.additional_information = additional_information
        leaver_info.save(
            update_fields=[
                "information_is_correct",
                "additional_information",
            ]
        )

    def store_return_option(self, email: str, return_option: ReturnOption):
        leaver_info = self.get_leaver_information(email=email)
        leaver_info.return_option = return_option
        leaver_info.save(update_fields=["return_option"])

    def store_return_information(
        self, email, personal_phone: str, contact_email: str, address: Optional[str]
    ):
        leaver_info = self.get_leaver_information(email=email)
        leaver_info.return_personal_phone = personal_phone
        leaver_info.return_contact_email = contact_email
        if address:
            leaver_info.return_address = address
        leaver_info.save(
            update_fields=[
                "return_personal_phone",
                "return_contact_email",
                "return_address",
            ]
        )

    def submit_to_service_now(self):
        service_now_interface = get_service_now_interface()
        # TODO: Map form data to the expected format to submit to Service Now.
        leaving_request_data: service_now_types.LeaverRequestData = {
            "collection_address": {
                "building_and_street": "",
                "city": "",
                "county": "",
                "postcode": "",
            },
            "collection_telephone": "0123456789",
            "collection_email": "someone@example.com",
            "reason_for_leaving": "",
            "leaving_date": timezone.now().date(),
            "employee_email": "someone@example.com",
            "employee_name": "Joe Bloggs",
            "employee_department": "Example Department",
            "employee_directorate": "Example Directorate",
            "employee_staff_id": "Staff ID",
            "manager_name": "Jane Doe",
            "assets": [],
            "assets_confirmation": True,
            "assets_information": "",
        }
        service_now_interface.submit_leaver_request(request_data=leaving_request_data)


class ConfirmDetailsView(LoginRequiredMixin, LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/confirm_details.html"
    form_class = forms.LeaverConfirmationForm
    success_url = reverse_lazy("leaver-kit")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        # Get the Leaver details
        leaver_details = self.get_leaver_details_with_updates(email=user_email)
        context.update(leaver_details=leaver_details),
        # Build a list of errors to present to the user.
        errors: List[str] = []
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
            leaving_date=form.cleaned_data["last_day"],
        )

        # Get the person details with the updates.
        leaver_details = self.get_leaver_details_with_updates(email=user_email)
        if forms.LeaverUpdateForm(data=leaver_details).is_valid():
            return super().form_valid(form)
        return self.form_invalid(form)


class UpdateDetailsView(LoginRequiredMixin, LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/update_details.html"
    form_class = forms.LeaverUpdateForm
    success_url = reverse_lazy("leaver-confirm-details")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        self.initial = dict(self.get_leaver_details_with_updates(email=user_email))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)
        self.store_leaver_detail_updates(email=user_email, updates=form.cleaned_data)
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


class KitView(LoginRequiredMixin, LeaverInformationMixin, TemplateView):
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": forms.AddAssetForm,
        "correction_form": forms.CorrectionForm,
    }
    template_name = "leaving/leaver/kit.html"
    success_url = reverse_lazy("leaver-return-options")

    def post_add_asset_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        asset = {
            "uuid": str(uuid.uuid4()),
            "tag": None,
            "name": form.cleaned_data["asset_name"],
        }
        request.session["assets"].append(asset)
        request.session.save()
        # Redirect to the GET method
        return redirect("leaver-kit")

    def post_correction_form(self, request: HttpRequest, form: Form, *args, **kwargs):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        form_data = form.cleaned_data

        # Store correction info and assets into the leaver details
        self.store_correction_information(
            email=user_email,
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
        if "assets" not in request.session:
            service_now_interface = get_service_now_interface()
            request.session["assets"] = [
                {
                    "uuid": str(uuid.uuid4()),
                    "tag": asset["tag"],
                    "name": asset["name"],
                }
                for asset in service_now_interface.get_assets_for_user()
            ]
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add form instances to the context.
        for form_name, form_class in self.forms.items():
            context[form_name] = form_class()
        context["assets"] = self.request.session["assets"]

        return context


class EquipmentReturnOptions(LoginRequiredMixin, LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/equipment_options.html"
    form_class = forms.ReturnOptionForm
    success_url = reverse_lazy("leaver-return-informaation")

    def form_valid(self, form):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        self.store_return_option(
            email=user_email,
            return_option=form.cleaned_data["return_option"],
        )

        return super().form_valid(form)


class EquipmentReturnInformation(LoginRequiredMixin, LeaverInformationMixin, FormView):
    template_name = "leaving/leaver/equipment_information.html"
    form_class = forms.ReturnInformationForm
    success_url = reverse_lazy("leaver-request-received")

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()

        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        leaver_info = self.get_leaver_information(email=user_email)
        if leaver_info.return_option == ReturnOption.OFFICE:
            kwargs.update(hide_address=True)

        return kwargs

    def form_valid(self, form):
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        self.store_return_information(
            email=user_email,
            personal_phone=form.cleaned_data["personal_phone"],
            contact_email=form.cleaned_data["contact_email"],
            address=form.cleaned_data["address"],
        )

        return super().form_valid(form)


class RequestReceivedView(LoginRequiredMixin, LeaverInformationMixin, TemplateView):
    template_name = "leaving/leaver/request_received.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        user = cast(User, self.request.user)
        user_email = cast(str, user.email)

        context = super().get_context_data(**kwargs)
        context.update(leaver_info=self.get_leaver_information(email=user_email))
        return context
