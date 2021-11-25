from typing import Any, List, cast

from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.service_now import get_service_now_interface
from core.service_now import types as service_now_types
from core.utils.people_finder import search_people_finder
from leavers import forms, types
from leavers.models import LeaverUpdates


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

    def get_leaver_details(self, email: str) -> types.LeaverDetails:
        """
        Get the Leaver details from People Finder
        Raises an exception People Finder doesn't return a result.
        """

        people_finder_results = search_people_finder(search_term=email)
        if len(people_finder_results) > 0:
            person = people_finder_results[0]

            job_title = ""
            team_name = ""
            if "roles" in person and len(person["roles"]) > 0:
                job_title = person["roles"][0]["job_title"]
                team_name = person["roles"][0]["team"]["name"]

            # TODO: Map values to the blank leaver details
            leaver_details: types.LeaverDetails = {
                # Personal details
                "first_name": person["first_name"],
                "last_name": person["last_name"],
                "date_of_birth": timezone.now().date(),
                "personal_email": "",
                "personal_phone": person["primary_phone_number"],
                "personal_address": "",
                # Professional details
                "grade": person["grade"],
                "job_title": job_title,
                "directorate": "",
                "department": "",
                "team_name": team_name,
                "work_email": person["email"],
                "manager": "",
                # Misc.
                "photo": person["photo"],
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
        # TODO: Define a list of required keys
        required_keys: List[str] = []

        for key in required_keys:
            if key not in leaver_details:
                return False
            if not leaver_details.get(key):
                return False
        return True


class ConfirmDetailsView(LeaverDetailsMixin, FormView):
    template_name = "leaving/leaver/confirm_details.html"
    form_class = forms.LeaverConfirmationForm
    success_url = reverse_lazy("leaver-request-received")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: restrict view to only allow authenticated users.
        if self.request.user.is_authenticated:
            user_email = cast(str, self.request.user.email)
            # Add the Leaver details to the context
            context.update(
                leaver_details=self.get_leaver_details_with_updates(email=user_email),
            )
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Check we have all the required information before we continue.
        """
        # TODO: restrict view to only allow authenticated users.
        if self.request.user.is_authenticated:
            user_email = cast(str, self.request.user.email)
            # Get the person details with the updates.
            leaver_details = self.get_leaver_details_with_updates(email=user_email)
            if not self.has_required_leaver_details(leaver_details):
                # TODO: Add an error message to inform the user.
                return self.form_invalid(form)
        return super().form_valid(form)


class UpdateDetailsView(LeaverDetailsMixin, FormView):
    template_name = "leaving/leaver/update_details.html"
    form_class = forms.LeaverUpdateForm
    success_url = reverse_lazy("leaver-confirm-details")

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        # TODO: restrict view to only allow authenticated users.
        if self.request.user.is_authenticated:
            user_email = cast(str, self.request.user.email)
            self.initial = dict(self.get_leaver_details_with_updates(email=user_email))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        # TODO: restrict view to only allow authenticated users.
        if self.request.user.is_authenticated:
            user_email = cast(str, self.request.user.email)
            self.store_leaver_detail_updates(
                email=user_email, updates=form.cleaned_data
            )
        return super().form_valid(form)


class KitView(TemplateView):
    asset_form_class = forms.AddAssetForm
    correction_form_class = forms.CorrectionForm
    template_name = "leaving/leaver/kit.html"

    def post(self, request, *args, **kwargs):
        context = {}
        if "asset_name" in request.POST:
            form = self.asset_form_class(request.POST)

            if form.is_valid():
                asset: service_now_types.AssetDetails = {
                    "tag": None,
                    "name": form.cleaned_data["asset_name"],
                }
                request.session["assets"].append(asset)
                request.session.save()
            else:
                context["asset_form"] = form
        else:
            form = self.correction_form_class(request.POST)

            if form.is_valid():
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
                service_now_interface.submit_leaver_request(
                    request_data=leaving_request_data
                )
            else:
                context["correction_form"] = form

        return render(request, self.template_name, self.get_context_data(**context))

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        service_now_interface = get_service_now_interface()
        request.session["assets"] = service_now_interface.get_assets_for_user()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asset_form"] = self.asset_form_class()
        context["correction_form"] = self.correction_form_class()
        context["assets"] = self.request.session["assets"]

        return context


class RequestReceivedView(TemplateView):
    template_name = "leaving/leaver/request_received.html"
