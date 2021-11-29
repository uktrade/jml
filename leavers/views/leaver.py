import uuid
from datetime import date
from typing import Any, Dict, List, Type, cast

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
from leavers.models import LeaverUpdates
from user.models import User


class LeaverDetailsMixin:
    def get_leaver_detail_updates(self, email: str) -> types.LeaverDetailUpdates:
        """
        Get the stored updates for the Leaver.
        Return an empty dict if there are no updates.
        """
        # Get any stored updates from the DB
        try:
            leaver_updates = LeaverUpdates.objects.get(leaver_email=email)
        except LeaverUpdates.DoesNotExist:
            return {}

        updates: types.LeaverDetailUpdates = leaver_updates.updates
        return updates

    def store_leaver_detail_updates(
        self, email: str, updates: types.LeaverDetailUpdates
    ):
        """
        Store updates for the Leaver.
        """
        # Get any stored updates from the DB
        try:
            leaver_updates = LeaverUpdates.objects.get(leaver_email=email)
        except LeaverUpdates.DoesNotExist:
            leaver_updates = LeaverUpdates.objects.create(
                leaver_email=email, updates={}
            )

        # Work out what information is new and only store that.
        existing_data = self.get_leaver_details(email=email)
        new_data: types.LeaverDetailUpdates = {}
        for key, value in updates.items():
            if key not in existing_data or existing_data.get(key) != value:
                new_data[key] = value  # type: ignore

        # Store the updates
        leaver_updates.updates = new_data
        leaver_updates.save()

    def store_leaving_date(self, email: str, leaving_date: date):
        """
        Store the leaving date in the session.
        """
        try:
            leaver_updates = LeaverUpdates.objects.get(leaver_email=email)
        except LeaverUpdates.DoesNotExist:
            leaver_updates = LeaverUpdates.objects.create(
                leaver_email=email, updates={}
            )
        # Get the currently stored updates
        updates = leaver_updates.updates
        # Add the leaving date
        updates["leaving_date"] = str(leaving_date)
        # Store the updates
        leaver_updates.updates = updates
        leaver_updates.save()

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
                "leaving_date": None,
            }
            return leaver_details
        raise Exception("Issue finding user in People Finder")

    def get_leaver_details_with_updates(self, email: str) -> types.LeaverDetails:
        leaver_details = self.get_leaver_details(email=email)
        leaver_details_updates = self.get_leaver_detail_updates(email=email)
        leaver_details.update(**leaver_details_updates)  # type: ignore
        return leaver_details

    def has_required_leaver_details(self, leaver_details: types.LeaverDetails) -> bool:
        """
        Check if the leaver details are complete.
        """

        leaver_update_form = forms.LeaverUpdateForm(data=leaver_details)
        return leaver_update_form.is_valid()


class ConfirmDetailsView(LoginRequiredMixin, LeaverDetailsMixin, FormView):
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
        if not self.has_required_leaver_details(leaver_details=leaver_details):
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
        if self.has_required_leaver_details(leaver_details):
            return super().form_valid(form)
        return self.form_invalid(form)


class UpdateDetailsView(LoginRequiredMixin, LeaverDetailsMixin, FormView):
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


def delete_kit(request: HttpRequest, kit_uuid: uuid.UUID):
    if "assets" in request.session:
        for asset in request.session["assets"]:
            if asset["uuid"] == str(kit_uuid):
                request.session["assets"].remove(asset)
                request.session.save()
                break
    return redirect("leaver-kit")


class KitView(TemplateView):
    forms: Dict[str, Type[Form]] = {
        "add_asset_form": forms.AddAssetForm,
        "correction_form": forms.CorrectionForm,
    }
    template_name = "leaving/leaver/kit.html"
    success_url = reverse_lazy("leaver-request-received")

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


class RequestReceivedView(TemplateView):
    template_name = "leaving/leaver/request_received.html"
